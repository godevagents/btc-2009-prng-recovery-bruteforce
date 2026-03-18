#ifndef WALLET_CRYPTO_BLOWFISH_H
#define WALLET_CRYPTO_BLOWFISH_H

#include <string>
#include <vector>
#include <memory>
#include <optional>

namespace wallet_crypto {

// Константы для размеров
static const size_t SALT_SIZE = 8;                    // Размер соли в байтах
static const size_t MASTER_KEY_SIZE = 32;             // Размер мастер-ключа в байтах
static const size_t IV_SIZE = 16;                     // Размер IV в байтах
static const size_t DERIVED_KEY_SIZE = 48;            // Размер результата EVP_BytesToKey (32 key + 16 IV)
static const size_t CHECKSUM_SIZE = 4;                // Размер контрольной суммы (первые 4 байта SHA1)

// Константы для формата mkey
static const int MKEY_VERSION = 1;                    // Версия формата мастер-ключа
static const int MKEY_DERIVATION_METHOD = 0;          // Метод деривации (0 = EVP_BytesToKey)
static const int MKEY_ID = 1;                         // ID мастер-ключа

// Типы записей кошелька
static const std::string RECORD_TYPE_CKEY = "ckey";  // Зашифрованный приватный ключ
static const std::string RECORD_TYPE_MKEY = "mkey";   // Мастер-ключ

/**
 * @brief Класс для криптографических операций кошелька Bitcoin
 * 
 * Реализует шифрование приватных ключей с использованием Blowfish ECB,
 * соответствующее формату Bitcoin (EVP_BytesToKey с SHA1)
 */
class WalletCrypto {
public:
    /**
     * @brief Конструктор по умолчанию
     */
    WalletCrypto();
    
    /**
     * @brief Деструктор
     */
    ~WalletCrypto();
    
    // START_METHOD_DeriveKey
    // START_CONTRACT:
    // PURPOSE: Получение мастер-ключа из пароля с использованием EVP_BytesToKey
    // INPUTS:
    // - const std::string& password - пароль пользователя
    // - const std::vector<unsigned char>& salt - соль (8 байт)
    // OUTPUTS: std::vector<unsigned char> - результат (48 байт: 32 ключ + 16 IV)
    // KEYWORDS: PATTERN(8): KeyDerivation; DOMAIN(9): Cryptography; TECH(7): EVP_BytesToKey
    // END_CONTRACT
    static std::vector<unsigned char> DeriveKey(const std::string& password,
                                                 const std::vector<unsigned char>& salt);
    
    // START_METHOD_GenerateSalt
    // START_CONTRACT:
    // PURPOSE: Генерация случайной соли для шифрования
    // INPUTS: Нет
    // OUTPUTS: std::vector<unsigned char> - случайная соль (8 байт)
    // KEYWORDS: PATTERN(7): SaltGeneration; DOMAIN(9): Cryptography; TECH(5): Random
    // END_CONTRACT
    static std::vector<unsigned char> GenerateSalt();
    
    // START_METHOD_EncryptPrivateKey
    // START_CONTRACT:
    // PURPOSE: Шифрование приватного ключа с использованием Blowfish ECB
    // INPUTS:
    // - const std::vector<unsigned char>& private_key - приватный ключ в DER формате
    // - const std::vector<unsigned char>& master_key - мастер-ключ (48 байт)
    // OUTPUTS: std::vector<unsigned char> - зашифрованный ключ
    // KEYWORDS: PATTERN(9): PrivateKeyEncryption; DOMAIN(9): Cryptography; TECH(8): BlowfishECB
    // END_CONTRACT
    static std::vector<unsigned char> EncryptPrivateKey(const std::vector<unsigned char>& private_key,
                                                         const std::vector<unsigned char>& master_key);
    
    // START_METHOD_DecryptPrivateKey
    // START_CONTRACT:
    // PURPOSE: Дешифрование приватного ключа с использованием Blowfish ECB
    // INPUTS:
    // - const std::vector<unsigned char>& encrypted_key - зашифрованный ключ
    // - const std::vector<unsigned char>& master_key - мастер-ключ (48 байт)
    // OUTPUTS: std::optional<std::vector<unsigned char>> - расшифрованный ключ или пустое значение при ошибке
    // KEYWORDS: PATTERN(9): PrivateKeyDecryption; DOMAIN(9): Cryptography; TECH(8): BlowfishECB
    // END_CONTRACT
    static std::optional<std::vector<unsigned char>> DecryptPrivateKey(const std::vector<unsigned char>& encrypted_key,
                                                                         const std::vector<unsigned char>& master_key);
    
    // START_METHOD_ComputeChecksum
    // START_CONTRACT:
    // PURPOSE: Вычисление контрольной суммы зашифрованного ключа
    // INPUTS:
    // - const std::vector<unsigned char>& encrypted_key - зашифрованный ключ
    // OUTPUTS: std::vector<unsigned char> - контрольная сумма (4 байта - первые байты SHA1)
    // KEYWORDS: PATTERN(9): ChecksumCompute; DOMAIN(9): Integrity; TECH(6): SHA1
    // END_CONTRACT
    static std::vector<unsigned char> ComputeChecksum(const std::vector<unsigned char>& encrypted_key);
    
    // START_METHOD_VerifyPassword
    // START_CONTRACT:
    // PURPOSE: Проверка корректности пароля по контрольной сумме
    // INPUTS:
    // - const std::vector<unsigned char>& encrypted_key - зашифрованный ключ
    // - const std::vector<unsigned char>& master_key - мастер-ключ
    // - const std::vector<unsigned char>& checksum - ожидаемая контрольная сумма
    // OUTPUTS: bool - true если пароль корректен
    // KEYWORDS: PATTERN(8): PasswordVerify; DOMAIN(9): Authentication; TECH(6): Validation
    // END_CONTRACT
    static bool VerifyPassword(const std::vector<unsigned char>& encrypted_key,
                               const std::vector<unsigned char>& master_key,
                               const std::vector<unsigned char>& checksum);
    
    // START_METHOD_CreateCKey
    // START_CONTRACT:
    // PURPOSE: Создание записи ckey (encrypted key) для Berkeley DB
    // INPUTS:
    // - const std::vector<unsigned char>& private_key - приватный ключ в DER формате
    // - const std::string& password - пароль для шифрования
    // OUTPUTS: std::vector<unsigned char> - сериализованная запись ckey
    // KEYWORDS: PATTERN(7): CKeyCreate; DOMAIN(9): WalletStorage; TECH(7): Serialization
    // END_CONTRACT
    static std::vector<unsigned char> CreateCKey(const std::vector<unsigned char>& private_key,
                                                   const std::string& password);
    
    // START_METHOD_CreateMKey
    // START_CONTRACT:
    // PURPOSE: Создание записи mkey (master key) для Berkeley DB
    // INPUTS:
    // - const std::string& password - пароль для генерации мастер-ключа
    // OUTPUTS: std::vector<unsigned char> - сериализованная запись mkey
    // KEYWORDS: PATTERN(7): MKeyCreate; DOMAIN(9): WalletStorage; TECH(7): Serialization
    // END_CONTRACT
    static std::vector<unsigned char> CreateMKey(const std::string& password);
    
    // START_METHOD_EncryptData
    // START_CONTRACT:
    // PURPOSE: Универсальное шифрование данных с использованием Blowfish ECB
    // INPUTS:
    // - const std::vector<unsigned char>& data - данные для шифрования
    // - const std::vector<unsigned char>& key - ключ шифрования
    // OUTPUTS: std::vector<unsigned char> - зашифрованные данные
    // KEYWORDS: PATTERN(8): DataEncryption; DOMAIN(9): Cryptography; TECH(8): BlowfishECB
    // END_CONTRACT
    static std::vector<unsigned char> EncryptData(const std::vector<unsigned char>& data,
                                                    const std::vector<unsigned char>& key);
    
    // START_METHOD_DecryptData
    // START_CONTRACT:
    // PURPOSE: Универсальное дешифрование данных с использованием Blowfish ECB
    // INPUTS:
    // - const std::vector<unsigned char>& encrypted_data - зашифрованные данные
    // - const std::vector<unsigned char>& key - ключ шифрования
    // OUTPUTS: std::optional<std::vector<unsigned char>> - расшифрованные данные или пустое значение при ошибке
    // KEYWORDS: PATTERN(8): DataDecryption; DOMAIN(9): Cryptography; TECH(8): BlowfishECB
    // END_CONTRACT
    static std::optional<std::vector<unsigned char>> DecryptData(const std::vector<unsigned char>& encrypted_data,
                                                                  const std::vector<unsigned char>& key);

private:
    // Константы для логирования
    static const std::string LOG_FILE;
    
    // Вспомогательные методы
    // START_HELPER_logToFile
    // START_CONTRACT:
    // PURPOSE: Логирование сообщений в файл
    // INPUTS: const std::string& message - сообщение для логирования
    // OUTPUTS: Нет
    // KEYWORDS: PATTERN(5): Logging; DOMAIN(5): Debug; TECH(4): FileIO
    // END_CONTRACT
    static void logToFile(const std::string& message);
    
    // START_HELPER_serializeInt
    // START_CONTRACT:
    // PURPOSE: Сериализация целого числа в little-endian формат
    // INPUTS: int value - число для сериализации
    // OUTPUTS: std::vector<unsigned char> - сериализованные данные (4 байта)
    // KEYWORDS: PATTERN(7): IntSerialization; DOMAIN(6): Integer; TECH(5): LittleEndian
    // END_CONTRACT
    static std::vector<unsigned char> serializeInt(int value);
    
    // START_HELPER_computeSha1
    // START_CONTRACT:
    // PURPOSE: Вычисление SHA1 хеша
    // INPUTS: const std::vector<unsigned char>& data - входные данные
    // OUTPUTS: std::vector<unsigned char> - SHA1 хеш (20 байт)
    // KEYWORDS: PATTERN(6): SHA1Hash; DOMAIN(9): Cryptography; TECH(5): Hash
    // END_CONTRACT
    static std::vector<unsigned char> computeSha1(const std::vector<unsigned char>& data);
    
    // START_HELPER_bytesToHex
    // START_CONTRACT:
    // PURPOSE: Преобразование байтов в hex строку
    // INPUTS: const std::vector<unsigned char>& bytes - входные байты
    // OUTPUTS: std::string - hex строка
    // KEYWORDS: PATTERN(6): HexEncode; DOMAIN(6): Format; TECH(5): String
    // END_CONTRACT
    static std::string bytesToHex(const std::vector<unsigned char>& bytes);
    
    // START_HELPER_addPadding
    // START_CONTRACT:
    // PURPOSE: Добавление PKCS#5 padding
    // INPUTS: const std::vector<unsigned char>& data - данные, size_t block_size - размер блока
    // OUTPUTS: std::vector<unsigned char> - данные с padding
    // KEYWORDS: PATTERN(7): PaddingAdd; DOMAIN(9): Cryptography; TECH(6): PKCS5
    // END_CONTRACT
    static std::vector<unsigned char> AddPadding(const std::vector<unsigned char>& data, size_t block_size);
    
    // START_HELPER_removePadding
    // START_CONTRACT:
    // PURPOSE: Удаление PKCS#5 padding
    // INPUTS: const std::vector<unsigned char>& data - данные с padding, size_t block_size - размер блока
    // OUTPUTS: std::vector<unsigned char> - данные без padding
    // KEYWORDS: PATTERN(8): PaddingRemove; DOMAIN(9): Cryptography; TECH(6): PKCS5
    // END_CONTRACT
    static std::vector<unsigned char> RemovePadding(const std::vector<unsigned char>& data, size_t block_size);
};

/**
 * @brief Фабрика для создания экземпляров WalletCrypto
 */
class WalletCryptoFactory {
public:
    static std::unique_ptr<WalletCrypto> create();
    static std::string getVersion();
};

} // namespace wallet_crypto

#endif // WALLET_CRYPTO_BLOWFISH_H
