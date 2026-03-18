#include "ecdsa_keys.h"
#include <cstring>
#include <openssl/err.h>

// Определение константы pszBase58
const char* wallet::crypto::pszBase58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";

namespace wallet {
namespace crypto {

// Константа размера пула энтропии OpenSSL
static const size_t ENTROPY_POOL_SIZE = 1043;

Secp256k1KeyGenerator::Secp256k1KeyGenerator()
    : pkey_(nullptr), fValid_(false) {
    // Инициализация OpenSSL кривой
    pkey_ = EC_KEY_new_by_curve_name(SECP256K1_NID);
    if (!pkey_) {
        throw key_error("Failed to create EC_KEY for secp256k1");
    }
}

Secp256k1KeyGenerator::~Secp256k1KeyGenerator() {
    if (pkey_) {
        EC_KEY_free(pkey_);
        pkey_ = nullptr;
    }
}

// START_FUNCTION_generateKey
// START_CONTRACT:
// PURPOSE: Генерация новой ключевой пары ECDSA на кривой secp256k1
// INPUTS: Нет
// OUTPUTS: bool - результат генерации (true при успехе)
// SIDE_EFFECTS: Создает новый EC_KEY, выделяет память
// TEST_CONDITIONS_SUCCESS_CRITERIA: Ключ генерируется без ошибок, является валидным
// KEYWORDS: PATTERN(8): KeyGeneration; DOMAIN(9): ECDSA; TECH(7): secp256k1
// LINKS: CALLS(8): EC_KEY_new; CALLS(7): EC_KEY_generate_key
// END_CONTRACT
bool Secp256k1KeyGenerator::generateKey() {
    // Проверка инициализации OpenSSL
    if (!pkey_) {
        pkey_ = EC_KEY_new_by_curve_name(SECP256K1_NID);
        if (!pkey_) {
            throw key_error("Failed to create EC_KEY for secp256k1");
        }
    }
    
    // Генерация ключа
    if (!EC_KEY_generate_key(pkey_)) {
        unsigned long err = ERR_get_error();
        char err_buf[256];
        ERR_error_string_n(err, err_buf, sizeof(err_buf));
        throw key_error(std::string("Failed to generate EC key: ") + err_buf);
    }
    
    fValid_ = true;
    return true;
}
// END_FUNCTION_generateKey

// START_FUNCTION_getPrivateKey
// START_CONTRACT:
// PURPOSE: Получение приватного ключа в DER-формате
// INPUTS: Нет
// OUTPUTS: std::vector<unsigned char> - DER-кодированный приватный ключ (279 байт)
// KEYWORDS: PATTERN(7): DEREncoding; DOMAIN(8): PrivateKey; TECH(6): OpenSSL
// END_CONTRACT
std::vector<unsigned char> Secp256k1KeyGenerator::getPrivateKey() const {
    if (!pkey_ || !fValid_) {
        throw key_error("Key is not valid");
    }
    
    // Определение размера ключа
    int priv_key_len = i2d_ECPrivateKey(pkey_, nullptr);
    if (priv_key_len <= 0) {
        throw key_error("Failed to get private key size");
    }
    
    // Выделение буфера
    std::vector<unsigned char> privKey(priv_key_len);
    unsigned char* p = privKey.data();
    
    // Кодирование в DER формат
    if (i2d_ECPrivateKey(pkey_, &p) != priv_key_len) {
        throw key_error("Failed to encode private key");
    }
    
    return privKey;
}
// END_FUNCTION_getPrivateKey

// START_FUNCTION_getPublicKey
// START_CONTRACT:
// PURPOSE: Получение публичного ключа в несжатом формате
// INPUTS: Нет
// OUTPUTS: std::vector<unsigned char> - публичный ключ (65 байт)
// KEYWORDS: PATTERN(7): PublicKey; DOMAIN(8): ECDSA; TECH(6): Uncompressed
// END_CONTRACT
std::vector<unsigned char> Secp256k1KeyGenerator::getPublicKey() const {
    if (!pkey_ || !fValid_) {
        throw key_error("Key is not valid");
    }
    
    // Получение публичного ключа
    const EC_POINT* pub_point = EC_KEY_get0_public_key(pkey_);
    if (!pub_point) {
        throw key_error("Failed to get public key point");
    }
    
    const EC_GROUP* group = EC_KEY_get0_group(pkey_);
    if (!group) {
        throw key_error("Failed to get EC group");
    }
    
    // Определение размера
    size_t pub_key_len = EC_POINT_point2oct(group, pub_point, 
                                            POINT_CONVERSION_UNCOMPRESSED, 
                                            nullptr, 0, nullptr);
    if (pub_key_len == 0) {
        throw key_error("Failed to get public key size");
    }
    
    // Выделение буфера и получение ключа
    std::vector<unsigned char> pubKey(pub_key_len);
    if (EC_POINT_point2oct(group, pub_point, 
                          POINT_CONVERSION_UNCOMPRESSED, 
                          pubKey.data(), pub_key_len, nullptr) != pub_key_len) {
        throw key_error("Failed to encode public key");
    }
    
    return pubKey;
}
// END_FUNCTION_getPublicKey

// START_FUNCTION_setPrivateKey
// START_CONTRACT:
// PURPOSE: Установка приватного ключа из DER-формата
// INPUTS: const std::vector<unsigned char>& vchPrivKey - DER-кодированный ключ
// OUTPUTS: bool - результат установки
// KEYWORDS: PATTERN(6): KeySet; DOMAIN(7): PrivateKey; TECH(5): DER
// END_CONTRACT
bool Secp256k1KeyGenerator::setPrivateKey(const std::vector<unsigned char>& vchPrivKey) {
    if (!pkey_) {
        pkey_ = EC_KEY_new_by_curve_name(SECP256K1_NID);
        if (!pkey_) {
            return false;
        }
    }
    
    const unsigned char* p = vchPrivKey.data();
    EC_KEY* loaded_key = d2i_ECPrivateKey(nullptr, &p, vchPrivKey.size());
    
    if (!loaded_key) {
        return false;
    }
    
    // Проверка ключа
    if (!EC_KEY_check_key(loaded_key)) {
        EC_KEY_free(loaded_key);
        return false;
    }
    
    // Замена текущего ключа
    EC_KEY_free(pkey_);
    pkey_ = loaded_key;
    fValid_ = true;
    
    return true;
}
// END_FUNCTION_setPrivateKey

// START_FUNCTION_setPublicKey
// START_CONTRACT:
// PURPOSE: Установка публичного ключа
// INPUTS: const std::vector<unsigned char>& vchPubKey - публичный ключ (65 байт)
// OUTPUTS: bool - результат установки
// KEYWORDS: PATTERN(6): KeySet; DOMAIN(7): PublicKey; TECH(5): ECDSA
// END_CONTRACT
bool Secp256k1KeyGenerator::setPublicKey(const std::vector<unsigned char>& vchPubKey) {
    if (!pkey_) {
        pkey_ = EC_KEY_new_by_curve_name(SECP256K1_NID);
        if (!pkey_) {
            return false;
        }
    }
    
    const EC_GROUP* group = EC_KEY_get0_group(pkey_);
    if (!group) {
        return false;
    }
    
    EC_POINT* point = EC_POINT_new(group);
    if (!point) {
        return false;
    }
    
    if (!EC_POINT_oct2point(group, point, vchPubKey.data(), vchPubKey.size(), nullptr)) {
        EC_POINT_free(point);
        return false;
    }
    
    if (!EC_KEY_set_public_key(pkey_, point)) {
        EC_POINT_free(point);
        return false;
    }
    
    EC_POINT_free(point);
    fValid_ = true;
    
    return true;
}
// END_FUNCTION_setPublicKey

// START_FUNCTION_addEntropy
// START_CONTRACT:
// PURPOSE: Добавление внешней энтропии в пул OpenSSL RAND
// INPUTS: const unsigned char* pEntropyData, size_t nEntropySize
// OUTPUTS: void
// KEYWORDS: PATTERN(7): EntropyInjection; DOMAIN(8): Randomness; TECH(6): OpenSSL
// END_CONTRACT
void Secp256k1KeyGenerator::addEntropy(const unsigned char* pEntropyData, size_t nEntropySize) {
    if (pEntropyData && nEntropySize > 0) {
        RAND_add(pEntropyData, nEntropySize, 0.0);
    }
}
// END_FUNCTION_addEntropy

// START_FUNCTION_getAddress
// START_CONTRACT:
// PURPOSE: Генерация Bitcoin адреса из публичного ключа
// INPUTS: Нет
// OUTPUTS: std::string - Base58Check адрес
// KEYWORDS: PATTERN(8): Base58Check; DOMAIN(9): BitcoinAddress; TECH(7): RIPEMD160
// END_CONTRACT
std::string Secp256k1KeyGenerator::getAddress() const {
    if (!pkey_ || !fValid_) {
        throw key_error("Key is not valid");
    }
    
    // Получение публичного ключа
    std::vector<unsigned char> pubkey = getPublicKey();
    
    // SHA256
    unsigned char hash1[SHA256_DIGEST_LENGTH];
    SHA256(pubkey.data(), pubkey.size(), hash1);
    
    // RIPEMD160
    std::vector<unsigned char> hash160(20);
    unsigned int hash160_len = 0;
    RIPEMD160(hash1, SHA256_DIGEST_LENGTH, hash160.data());
    
    // Добавление версии (0x00 для mainnet)
    std::vector<unsigned char> vchVersionedHash;
    vchVersionedHash.reserve(21);
    vchVersionedHash.push_back(0x00);  // Version byte
    vchVersionedHash.insert(vchVersionedHash.end(), hash160.begin(), hash160.end());
    
    // Контрольная сумма: SHA256(SHA256(version + hash160))
    unsigned char checksum[SHA256_DIGEST_LENGTH];
    SHA256(vchVersionedHash.data(), vchVersionedHash.size(), checksum);
    SHA256(checksum, SHA256_DIGEST_LENGTH, checksum);
    
    // Добавление первых 4 байт контрольной суммы
    vchVersionedHash.insert(vchVersionedHash.end(), checksum, checksum + 4);
    
    // Base58 кодирование
    return Base58Encode(vchVersionedHash);
}
// END_FUNCTION_getAddress

// START_FUNCTION_isValid
// START_CONTRACT:
// PURPOSE: Проверка валидности ключа
// INPUTS: Нет
// OUTPUTS: bool - true если ключ валиден
// KEYWORDS: PATTERN(6): Validation; DOMAIN(7): Key; TECH(5): Check
// END_CONTRACT
bool Secp256k1KeyGenerator::isValid() const {
    if (!pkey_ || !fValid_) {
        return false;
    }
    return EC_KEY_check_key(pkey_) == 1;
}
// END_FUNCTION_isValid

// START_FUNCTION_getEntropyPoolSize
// START_CONTRACT:
// PURPOSE: Получение размера пула энтропии OpenSSL
// INPUTS: Нет
// OUTPUTS: size_t - размер пула (1043 байта)
// KEYWORDS: PATTERN(5): EntropyPool; DOMAIN(6): OpenSSL; TECH(4): Size
// END_CONTRACT
size_t Secp256k1KeyGenerator::getEntropyPoolSize() const {
    return ENTROPY_POOL_SIZE;
}
// END_FUNCTION_getEntropyPoolSize

// START_FUNCTION_Hash160
// START_CONTRACT:
// PURPOSE: Вычисление RIPEMD160(SHA256(data))
// INPUTS: const std::vector<unsigned char>& vch - входные данные
// OUTPUTS: std::vector<unsigned char> - 20 байт хеш
// KEYWORDS: PATTERN(7): Hash160; DOMAIN(8): RIPEMD160; TECH(6): SHA256
// END_CONTRACT
std::vector<unsigned char> Secp256k1KeyGenerator::Hash160(const std::vector<unsigned char>& vch) const {
    unsigned char hash1[SHA256_DIGEST_LENGTH];
    SHA256(vch.data(), vch.size(), hash1);
    
    std::vector<unsigned char> hash160(20);
    RIPEMD160(hash1, SHA256_DIGEST_LENGTH, hash160.data());
    
    return hash160;
}
// END_FUNCTION_Hash160

// START_FUNCTION_Base58Encode
// START_CONTRACT:
// PURPOSE: Кодирование данных в Base58
// INPUTS: const std::vector<unsigned char>& vch - данные для кодирования
// OUTPUTS: std::string - Base58 строка
// KEYWORDS: PATTERN(7): Base58; DOMAIN(8): Encoding; TECH(6): Bitcoin
// END_CONTRACT
std::string Secp256k1KeyGenerator::Base58Encode(const std::vector<unsigned char>& vch) const {
    // Подсчет ведущих нулей
    size_t leading_zeros = 0;
    for (size_t i = 0; i < vch.size() && vch[i] == 0; i++) {
        leading_zeros++;
    }
    
    // Алгоритм Base58
    const int base58_digits_size = 58;
    int digits_len = (int)vch.size() * 138 / 100 + 1;
    std::vector<int> digits(digits_len, 0);
    
    for (size_t i = 0; i < vch.size(); i++) {
        int carry = vch[i];
        for (int j = digits_len - 1; j >= 0; j--) {
            carry += 256 * digits[j];
            digits[j] = carry % base58_digits_size;
            carry /= base58_digits_size;
        }
    }
    
    // Пропуск ведущих нулей
    std::string result;
    result.reserve(leading_zeros + digits_len);
    
    // Добавить ведущие нули
    for (size_t i = 0; i < leading_zeros; i++) {
        result.push_back(pszBase58[0]);
    }
    
    // Пропуск ведущих нулей в digits
    size_t digit_start = 0;
    for (size_t i = 0; i < (size_t)digits_len; i++) {
        if (digits[i] != 0) {
            digit_start = i;
            break;
        }
    }
    
    // Конвертация в строку
    for (size_t i = digit_start; i < (size_t)digits_len; i++) {
        result.push_back(pszBase58[digits[i]]);
    }
    
    return result;
}
// END_FUNCTION_Base58Encode

// START_FUNCTION_Base58Decode
// START_CONTRACT:
// PURPOSE: Декодирование Base58 строки
// INPUTS: const std::string& str - Base58 строка
// OUTPUTS: std::vector<unsigned char> - декодированные данные
// KEYWORDS: PATTERN(7): Base58; DOMAIN(8): Decoding; TECH(6): Bitcoin
// END_CONTRACT
std::vector<unsigned char> Secp256k1KeyGenerator::Base58Decode(const std::string& str) const {
    // Создание таблицы для быстрого поиска
    int digits_size = (int)str.size();
    std::vector<int> digits(digits_size);
    
    for (int i = 0; i < digits_size; i++) {
        char c = str[i];
        const char* p = strchr(pszBase58, c);
        if (!p) {
            throw key_error(std::string("Invalid Base58 character: ") + c);
        }
        digits[i] = p - pszBase58;
    }
    
    // Алгоритм декодирования
    int result_size = digits_size;
    std::vector<unsigned char> result(result_size, 0);
    
    for (int i = 0; i < digits_size; i++) {
        int carry = digits[i];
        for (int j = result_size - 1; j >= 0; j--) {
            carry += 58 * result[j];
            result[j] = carry & 0xff;
            carry >>= 8;
        }
    }
    
    // Удаление ведущих нулей
    size_t leading_zeros = 0;
    for (size_t i = 0; i < result.size() && result[i] == 0; i++) {
        leading_zeros++;
    }
    
    // Проверка на ведущие нули в исходной строке
    for (size_t i = 0; i < str.size() && str[i] == pszBase58[0]; i++) {
        leading_zeros++;
    }
    
    return result;
}
// END_FUNCTION_Base58Decode

// Фабрика
std::unique_ptr<ECDSAPluginInterface> ECDSAKeyPluginFactory::create() {
    return std::make_unique<Secp256k1KeyGenerator>();
}

std::string ECDSAKeyPluginFactory::getVersion() {
    return "1.0.0";
}

} // namespace crypto
} // namespace wallet
