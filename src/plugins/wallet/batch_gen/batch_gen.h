#ifndef BATCH_WALLET_GEN_PLUGIN_H
#define BATCH_WALLET_GEN_PLUGIN_H

// CRITICAL: Disable OpenSSL type definitions BEFORE including any headers
// This prevents conflicts with CUDA kernel types (RIPEMD160_CTX, SHA256_CTX)
#ifndef OPENSSL_SKIP_HEADER
#define OPENSSL_SKIP_HEADER
#endif

#include <vector>
#include <string>
#include <memory>
#include <cstdint>
#include <ctime>

// Forward declarations for ECDSA module - using wallet::crypto namespace
namespace wallet {
namespace crypto {
class Secp256k1KeyGenerator;
class ECDSAPluginInterface;
}
}

namespace wallet_batch {

// Константы
const size_t DEFAULT_WALLET_COUNT = 1000;
const size_t MAX_WALLET_COUNT = 10000;

/**
 * @brief Структура данных одного кошелька
 */
struct WalletData {
    size_t index;
    std::vector<unsigned char> public_key;     // 65 байт
    std::vector<unsigned char> private_key;     // 279 байт
    std::string address;                         // Base58
    uint64_t timestamp;
    std::string entropy_source;
};

/**
 * @brief Запись для Berkeley DB
 */
struct WalletDBEntry {
    std::string key_type;
    std::vector<unsigned char> key_data;
    std::vector<unsigned char> value_data;
};

/**
 * @brief Коллекция кошельков
 */
class WalletCollection {
public:
    WalletCollection();
    ~WalletCollection();
    
    void addWallet(const WalletData& wallet);
    WalletData getWalletAt(size_t index) const;
    size_t size() const;
    void clear();
    
    const std::vector<WalletData>& getAll() const;
    std::vector<WalletDBEntry> toDBEntries() const;
    
private:
    std::vector<WalletData> wallets_;
    std::vector<std::string> addresses_set_;
};

/**
 * @brief Интерфейс плагина пакетной генерации кошельков
 */
class BatchWalletGeneratorInterface {
public:
    virtual ~BatchWalletGeneratorInterface() = default;
    
    /**
     * @brief Инициализация с snapshot энтропии
     * 
     * @param entropy_data Вектор данных энтропии (state[1043])
     * @return true при успехе
     */
    virtual bool initialize(const std::vector<unsigned char>& entropy_data) = 0;
    
    /**
     * @brief Генерация кошельков
     * 
     * @param count Количество кошельков
     * @param deterministic Использовать детерминистическую схему
     * @return Коллекция сгенерированных кошельков
     */
    virtual WalletCollection generateWallets(size_t count = 1000, 
                                              bool deterministic = true) = 0;
    
    /**
     * @brief Получение кошелька по индексу
     */
    virtual WalletData getWalletAtIndex(size_t index) const = 0;
    
    /**
     * @brief Экспорт в формат Berkeley DB
     */
    virtual std::vector<WalletDBEntry> exportToDBFormat() const = 0;
    
    /**
     * @brief Получение количества сгенерированных кошельков
     */
    virtual size_t getWalletCount() const = 0;
};

/**
 * @brief Реализация пакетного генератора кошельков
 */
class BatchWalletGenerator : public BatchWalletGeneratorInterface {
public:
    BatchWalletGenerator();
    ~BatchWalletGenerator() override;
    
    // START_METHOD_initialize
    // START_CONTRACT:
    // PURPOSE: Инициализация генератора с единым snapshot энтропии
    // INPUTS: const std::vector<unsigned char>& entropy_data
    // OUTPUTS: bool - результат инициализации
    // KEYWORDS: PATTERN(8): Initialization; DOMAIN(9): EntropySnapshot; TECH(7): RAND_seed
    // END_CONTRACT
    bool initialize(const std::vector<unsigned char>& entropy_data) override;
    
    // START_METHOD_generateWallets
    // START_CONTRACT:
    // PURPOSE: Генерация 1000 кошельков из единой энтропии
    // INPUTS: size_t count, bool deterministic
    // OUTPUTS: WalletCollection - коллекция кошельков
    // KEYWORDS: PATTERN(9): BatchGeneration; DOMAIN(9): WalletCollection; TECH(8): Deterministic
    // END_CONTRACT
    WalletCollection generateWallets(size_t count = 1000, 
                                     bool deterministic = true) override;
    
    // START_METHOD_getWalletAtIndex
    // START_CONTRACT:
    // PURPOSE: Получение конкретного кошелька по индексу
    // INPUTS: size_t index
    // OUTPUTS: WalletData - данные кошелька
    // KEYWORDS: PATTERN(7): IndexAccess; DOMAIN(8): WalletData; TECH(5): Lookup
    // END_CONTRACT
    WalletData getWalletAtIndex(size_t index) const override;
    
    // START_METHOD_exportToDBFormat
    // START_CONTRACT:
    // PURPOSE: Экспорт коллекции в формат для Berkeley DB
    // INPUTS: Нет
    // OUTPUTS: std::vector<WalletDBEntry> - вектор записей
    // KEYWORDS: PATTERN(8): DatabaseExport; DOMAIN(8): BerkeleyDB; TECH(7): Serialization
    // END_CONTRACT
    std::vector<WalletDBEntry> exportToDBFormat() const override;
    
    // START_METHOD_getWalletCount
    // START_CONTRACT:
    // PURPOSE: Получение количества сгенерированных кошельков
    // INPUTS: Нет
    // OUTPUTS: size_t - количество кошельков
    // KEYWORDS: PATTERN(5): Count; DOMAIN(6): Collection; TECH(4): Size
    // END_CONTRACT
    size_t getWalletCount() const override;

private:
    std::unique_ptr<wallet::crypto::Secp256k1KeyGenerator> key_generator_;
    WalletCollection wallets_;
    std::vector<unsigned char> initial_entropy_;
    bool is_initialized_;
    
    // Вспомогательные методы
    void injectEntropyFromKey(const std::vector<unsigned char>& pubkey);
    std::vector<unsigned char> deriveEntropy(const std::vector<unsigned char>& prev_pubkey, 
                                              const unsigned char* initial_entropy,
                                              size_t entropy_size);
};

/**
 * @brief Фабрика для создания экземпляров плагина
 */
class BatchWalletPluginFactory {
public:
    static std::unique_ptr<BatchWalletGeneratorInterface> create();
    static std::string getVersion();
};

} // namespace wallet_batch

#endif // BATCH_WALLET_GEN_PLUGIN_H
