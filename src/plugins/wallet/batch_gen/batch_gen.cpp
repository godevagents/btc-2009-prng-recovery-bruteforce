#include "batch_gen.h"
#include "../../crypto/ecdsa_keys/ecdsa_keys.h"
#include <openssl/sha.h>
#include <openssl/rand.h>
#include <algorithm>
#include <stdexcept>
#include <cstring>

// Определение константы, если не определено
#ifndef SHA256_DIGEST_LENGTH
#define SHA256_DIGEST_LENGTH 32
#endif

namespace wallet_batch {

// Константы
static const size_t ENTROPY_POOL_SIZE = 1043;

// WalletCollection implementation
WalletCollection::WalletCollection() {}

WalletCollection::~WalletCollection() {}

void WalletCollection::addWallet(const WalletData& wallet) {
    wallets_.push_back(wallet);
    addresses_set_.push_back(wallet.address);
}

WalletData WalletCollection::getWalletAt(size_t index) const {
    if (index >= wallets_.size()) {
        throw std::out_of_range("Wallet index out of range");
    }
    return wallets_[index];
}

size_t WalletCollection::size() const {
    return wallets_.size();
}

void WalletCollection::clear() {
    wallets_.clear();
    addresses_set_.clear();
}

const std::vector<WalletData>& WalletCollection::getAll() const {
    return wallets_;
}

std::vector<WalletDBEntry> WalletCollection::toDBEntries() const {
    std::vector<WalletDBEntry> entries;
    
    // Добавить версию БД
    WalletDBEntry version_entry;
    version_entry.key_type = "version";
    // Сериализация версии (10500) - 4 байта little-endian
    version_entry.value_data = {0x74, 0x29, 0x00, 0x00};
    entries.push_back(version_entry);
    
    // Добавить defaultkey (первый ключ)
    if (!wallets_.empty()) {
        WalletDBEntry defaultkey_entry;
        defaultkey_entry.key_type = "defaultkey";
        defaultkey_entry.value_data = wallets_[0].public_key;
        entries.push_back(defaultkey_entry);
    }
    
    // Добавить все ключевые пары
    for (const auto& wallet : wallets_) {
        WalletDBEntry key_entry;
        key_entry.key_type = "key";
        key_entry.key_data = wallet.public_key;
        key_entry.value_data = wallet.private_key;
        entries.push_back(key_entry);
        
        // Добавить запись в адресную книгу
        WalletDBEntry name_entry;
        name_entry.key_type = "name";
        name_entry.key_data = std::vector<unsigned char>(wallet.address.begin(), wallet.address.end());
        name_entry.value_data = std::vector<unsigned char>(wallet.address.begin(), wallet.address.end());
        entries.push_back(name_entry);
    }
    
    return entries;
}

// BatchWalletGenerator implementation
BatchWalletGenerator::BatchWalletGenerator()
    : key_generator_(nullptr), is_initialized_(false) {
    key_generator_ = std::make_unique<wallet::crypto::Secp256k1KeyGenerator>();
}

BatchWalletGenerator::~BatchWalletGenerator() {}

// START_METHOD_initialize
// START_CONTRACT:
// PURPOSE: Инициализация генератора с единым snapshot энтропии
// INPUTS: const std::vector<unsigned char>& entropy_data
// OUTPUTS: bool - результат инициализации
// KEYWORDS: PATTERN(8): Initialization; DOMAIN(9): EntropySnapshot; TECH(7): RAND_seed
// END_CONTRACT
bool BatchWalletGenerator::initialize(const std::vector<unsigned char>& entropy_data) {
    if (entropy_data.empty()) {
        return false;
    }
    
    // Сохраняем начальную энтропию
    initial_entropy_ = entropy_data;
    
    // Инициализируем OpenSSL RAND_seed
    // RAND_seed() требуется для начальной инициализации (соответствует Bitcoin 0.1.0)
    RAND_seed(entropy_data.data(), entropy_data.size());
    
    is_initialized_ = true;
    return true;
}
// END_METHOD_initialize

// START_METHOD_generateWallets
// START_CONTRACT:
// PURPOSE: Генерация 1000 кошельков из единой энтропии
// INPUTS: size_t count, bool deterministic
// OUTPUTS: WalletCollection - коллекция кошельков
// KEYWORDS: PATTERN(9): BatchGeneration; DOMAIN(9): WalletCollection; TECH(8): Deterministic
// END_CONTRACT
WalletCollection BatchWalletGenerator::generateWallets(size_t count, bool deterministic) {
    if (!is_initialized_) {
        throw std::runtime_error("Generator not initialized. Call initialize() first.");
    }
    
    if (count == 0 || count > MAX_WALLET_COUNT) {
        throw std::invalid_argument("Invalid wallet count");
    }
    
    wallets_.clear();
    
    // Сохраняем текущее состояние RAND для детерминистического режима
    // Это позволяет генерировать одинаковые последовательности при повторных вызовах
    std::vector<unsigned char> entropy_pool;
    if (deterministic) {
        entropy_pool.resize(32);
        RAND_bytes(entropy_pool.data(), 32);
    }
    
    // Сбрасываем RAND к начальному состоянию после initialize()
    RAND_seed(initial_entropy_.data(), initial_entropy_.size());
    
    std::vector<unsigned char> previous_pubkey;
    uint64_t timestamp = static_cast<uint64_t>(std::time(nullptr));
    
    for (size_t i = 0; i < count; i++) {
        WalletData wallet;
        wallet.index = i;
        wallet.timestamp = timestamp;
        wallet.entropy_source = "snapshot";
        
        // Генерация ключа
        key_generator_->generateKey();
        
        // Получение ключей
        wallet.private_key = key_generator_->getPrivateKey();
        wallet.public_key = key_generator_->getPublicKey();
        wallet.address = key_generator_->getAddress();
        
        wallets_.addWallet(wallet);
        
        // Детерминистическая схема: добавляем хеш предыдущего ключа в пул
        if (deterministic && i > 0) {
            injectEntropyFromKey(wallet.public_key);
        }
    }
    
    return wallets_;
}
// END_METHOD_generateWallets

// START_METHOD_getWalletAtIndex
// START_CONTRACT:
// PURPOSE: Получение конкретного кошелька по индексу
// INPUTS: size_t index
// OUTPUTS: WalletData - данные кошелька
// KEYWORDS: PATTERN(7): IndexAccess; DOMAIN(8): WalletData; TECH(5): Lookup
// END_CONTRACT
WalletData BatchWalletGenerator::getWalletAtIndex(size_t index) const {
    return wallets_.getWalletAt(index);
}
// END_METHOD_getWalletAtIndex

// START_METHOD_exportToDBFormat
// START_CONTRACT:
// PURPOSE: Экспорт коллекции в формат для Berkeley DB
// INPUTS: Нет
// OUTPUTS: std::vector<WalletDBEntry> - вектор записей
// KEYWORDS: PATTERN(8): DatabaseExport; DOMAIN(8): BerkeleyDB; TECH(7): Serialization
// END_CONTRACT
std::vector<WalletDBEntry> BatchWalletGenerator::exportToDBFormat() const {
    return wallets_.toDBEntries();
}
// END_METHOD_exportToDBFormat

// START_METHOD_getWalletCount
// START_CONTRACT:
// PURPOSE: Получение количества сгенерированных кошельков
// INPUTS: Нет
// OUTPUTS: size_t - количество кошельков
// KEYWORDS: PATTERN(5): Count; DOMAIN(6): Collection; TECH(4): Size
// END_CONTRACT
size_t BatchWalletGenerator::getWalletCount() const {
    return wallets_.size();
}
// END_METHOD_getWalletCount

// START_METHOD_injectEntropyFromKey
// START_CONTRACT:
// PURPOSE: Добавление энтропии в пул на основе сгенерированного ключа
// INPUTS: const std::vector<unsigned char>& pubkey
// OUTPUTS: void
// KEYWORDS: PATTERN(7): EntropyInjection; DOMAIN(8): Deterministic; TECH(6): SHA256
// END_CONTRACT
void BatchWalletGenerator::injectEntropyFromKey(const std::vector<unsigned char>& pubkey) {
    // SHA256(public_key)
    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256(pubkey.data(), pubkey.size(), hash);
    
    // RAND_add с энтропией 0.5 (соответствует детерминистической схеме)
    RAND_add(hash, SHA256_DIGEST_LENGTH, 0.5);
}
// END_METHOD_injectEntropyFromKey

// START_METHOD_deriveEntropy
// START_CONTRACT:
// PURPOSE: Вычисление энтропии для следующего ключа
// INPUTS: const std::vector<unsigned char>& prev_pubkey, const unsigned char* initial_entropy, size_t entropy_size
// OUTPUTS: std::vector<unsigned char> - производная энтропия
// KEYWORDS: PATTERN(8): EntropyDerivation; DOMAIN(9): Deterministic; TECH(7): SHA256
// END_CONTRACT
std::vector<unsigned char> BatchWalletGenerator::deriveEntropy(
    const std::vector<unsigned char>& prev_pubkey,
    const unsigned char* initial_entropy,
    size_t entropy_size) {
    
    std::vector<unsigned char> combined;
    combined.reserve(prev_pubkey.size() + entropy_size);
    combined.insert(combined.end(), prev_pubkey.begin(), prev_pubkey.end());
    combined.insert(combined.end(), initial_entropy, initial_entropy + entropy_size);
    
    std::vector<unsigned char> result(SHA256_DIGEST_LENGTH);
    SHA256(combined.data(), combined.size(), result.data());
    
    return result;
}
// END_METHOD_deriveEntropy

// Фабрика
std::unique_ptr<BatchWalletGeneratorInterface> BatchWalletPluginFactory::create() {
    return std::make_unique<BatchWalletGenerator>();
}

std::string BatchWalletPluginFactory::getVersion() {
    return "1.0.0";
}

} // namespace wallet_batch
