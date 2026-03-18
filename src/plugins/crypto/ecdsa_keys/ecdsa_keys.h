#ifndef ECDSA_KEYS_PLUGIN_H
#define ECDSA_KEYS_PLUGIN_H

// CRITICAL: Disable OpenSSL type definitions BEFORE including any OpenSSL headers
// This prevents conflicts with CUDA kernel types in hybrid CUDA/CPU modules
#ifndef OPENSSL_SKIP_HEADER
#define OPENSSL_SKIP_HEADER
#endif

#include <vector>
#include <string>
#include <memory>
#include <stdexcept>
#include <openssl/ec.h>
#include <openssl/ecdsa.h>
#include <openssl/obj_mac.h>
#include <openssl/ripemd.h>
#include <openssl/sha.h>
#include <openssl/rand.h>
#include <openssl/bio.h>
#include <openssl/buffer.h>

namespace wallet {
namespace crypto {

// Константы из референса Bitcoin 0.1.0
const unsigned int PRIVATE_KEY_SIZE = 279;  // DER-encoded
const unsigned int PUBLIC_KEY_SIZE  = 65;   // Несжатый формат
const unsigned int SIGNATURE_SIZE   = 72;   // DER-encoded ECDSA

// NID кривой secp256k1 (избегаем конфликта с макросом OpenSSL)
static const int SECP256K1_NID = 714;

// База Base58 (без 0, O, I, l)
extern const char* pszBase58;

/**
 * @brief Исключение для ошибок криптографии
 */
class key_error : public std::runtime_error {
public:
    explicit key_error(const std::string& msg) : std::runtime_error(msg) {}
};

/**
 * @brief Интерфейс плагина генерации ECDSA ключей
 * 
 * Критерий 0: Модуль-плагинная архитектура
 * Все плагины проекта должны реализовывать этот интерфейс
 */
class ECDSAPluginInterface {
public:
    virtual ~ECDSAPluginInterface() = default;
    
    /**
     * @brief Генерация новой ключевой пары ECDSA
     * 
     * Использует кривую secp256k1 (NID_secp256k1)
     * Соответствует оригинальному CKey::MakeNewKey() из Bitcoin 0.1.0
     * 
     * @return true если ключ успешно сгенерирован
     * @throw key_error при ошибке генерации
     */
    virtual bool generateKey() = 0;
    
    /**
     * @brief Получение приватного ключа в DER-формате
     * 
     * Формат: 30 <len> 02 01 <privkey_len> 04 <privkey> 30 <pubkey_len> 04 <pubkey_x> 04 <pubkey_y>
     * Размер: 279 байт (PRIVATE_KEY_SIZE)
     * 
     * @return Вектор байт с DER-кодированным приватным ключом
     */
    virtual std::vector<unsigned char> getPrivateKey() const = 0;
    
    /**
     * @brief Получение публичного ключа
     * 
     * Формат: 0x04 + X (32 байта) + Y (32 байта) = 65 байт
     * Несжатый формат (uncompressed)
     * 
     * @return Вектор байт с публичным ключом
     */
    virtual std::vector<unsigned char> getPublicKey() const = 0;
    
    /**
     * @brief Установка приватного ключа из DER-формата
     * 
     * @param vchPrivKey DER-кодированный приватный ключ
     * @return true при успешной установке
     */
    virtual bool setPrivateKey(const std::vector<unsigned char>& vchPrivKey) = 0;
    
    /**
     * @brief Установка публичного ключа
     * 
     * @param vchPubKey Публичный ключ (65 байт)
     * @return true при успешной установке
     */
    virtual bool setPublicKey(const std::vector<unsigned char>& vchPubKey) = 0;
    
    /**
     * @brief Добавление энтропии в OpenSSL пул
     * 
     * Используется для передачи собранной энтропии в OpenSSL RNG
     * Соответствует оригинальному RandAddSeed() из Bitcoin 0.1.0
     * 
     * @param pEntropyData Указатель на данные энтропии
     * @param nEntropySize Размер данных энтропии в байтах
     */
    virtual void addEntropy(const unsigned char* pEntropyData, size_t nEntropySize) = 0;
    
    /**
     * @brief Получение адреса из публичного ключа (Base58Check)
     * 
     * Алгоритм: Base58Check(0x00 + RIPEMD160(SHA256(PubKey)))
     * 
     * @return Строковое представление адреса Bitcoin
     */
    virtual std::string getAddress() const = 0;
    
    /**
     * @brief Проверка валидности ключа
     * 
     * @return true если ключ валиден
     */
    virtual bool isValid() const = 0;
    
    /**
     * @brief Получение константы пула энтропии OpenSSL
     * 
     * @return Размер состояния пула (1043 байта для OpenSSL RAND_poll)
     */
    virtual size_t getEntropyPoolSize() const = 0;
};

/**
 * @brief Реализация генератора ключей secp256k1
 */
class Secp256k1KeyGenerator : public ECDSAPluginInterface {
public:
    Secp256k1KeyGenerator();
    ~Secp256k1KeyGenerator() override;
    
    bool generateKey() override;
    std::vector<unsigned char> getPrivateKey() const override;
    std::vector<unsigned char> getPublicKey() const override;
    bool setPrivateKey(const std::vector<unsigned char>& vchPrivKey) override;
    bool setPublicKey(const std::vector<unsigned char>& vchPubKey) override;
    void addEntropy(const unsigned char* pEntropyData, size_t nEntropySize) override;
    std::string getAddress() const override;
    bool isValid() const override;
    size_t getEntropyPoolSize() const override;

private:
    EC_KEY* pkey_;
    bool fValid_;
    
    // Вспомогательные методы
    std::vector<unsigned char> Hash160(const std::vector<unsigned char>& vch) const;
    std::string Base58Encode(const std::vector<unsigned char>& vch) const;
    std::vector<unsigned char> Base58Decode(const std::string& str) const;
};

/**
 * @brief Фабрика для создания экземпляров плагина
 */
class ECDSAKeyPluginFactory {
public:
    /**
     * @brief Создание нового экземпляра плагина
     * 
     * @return Уникальный указатель на плагин
     */
    static std::unique_ptr<ECDSAPluginInterface> create();
    
    /**
     * @brief Получение версии плагина
     * 
     * @return Версия в формате "major.minor.patch"
     */
    static std::string getVersion();
};

} // namespace crypto
} // namespace wallet

#endif // ECDSA_KEYS_PLUGIN_H
