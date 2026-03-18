#ifndef WALLET_TX_H
#define WALLET_TX_H

#include <vector>
#include <string>
#include <cstdint>
#include <optional>
#include <sstream>
#include <iomanip>
#include <ctime>
#include <fstream>

namespace wallet_tx {

// Константы для логирования
static const std::string LOG_FILE = "wallet_tx.log";

// Константы формата транзакции Bitcoin 0.1.0
static const int TX_VERSION = 1;
static const size_t TX_HASH_SIZE = 32;
static const size_t TX_ID_SIZE = 32;

/**
 * @brief Структура входа транзакции (CTxIn)
 * 
 * Представляет вход транзакции, который ссылается на выход предыдущей транзакции.
 */
struct CTxIn {
    // Хэш предыдущей транзакции (32 байта)
    std::vector<unsigned char> prevout_hash;
    
    // Индекс выхода в предыдущей транзакции (4 байта)
    uint32_t prevout_n;
    
    // Скрипт подписи (вектор байтов)
    std::vector<unsigned char> scriptSig;
    
    // Конструктор по умолчанию
    CTxIn();
    
    // Конструктор с параметрами
    CTxIn(const std::vector<unsigned char>& prev_hash, uint32_t prev_n);
    
    // Сериализация в бинарный формат
    std::vector<unsigned char> serialize() const;
    
    // Десериализация из бинарного формата
    bool deserialize(const std::vector<unsigned char>& data, size_t& pos);
};

/**
 * @brief Структура выхода транзакции (CTxOut)
 * 
 * Представляет выход транзакции с суммой и скриптом.
 */
struct CTxOut {
    // Сумма выхода (8 байт - uint64_t)
    uint64_t nValue;
    
    // Скрипт (вектор байтов)
    std::vector<unsigned char> scriptPubKey;
    
    // Конструктор по умолчанию
    CTxOut();
    
    // Конструктор с параметрами
    CTxOut(uint64_t value, const std::vector<unsigned char>& script);
    
    // Сериализация в бинарный формат
    std::vector<unsigned char> serialize() const;
    
    // Десериализация из бинарного формата
    bool deserialize(const std::vector<unsigned char>& data, size_t& pos);
};

/**
 * @brief Класс транзакции кошелька (CWalletTx)
 * 
 * Реализует структуру транзакции кошелька в формате Bitcoin 0.1.0.
 * Включает все поля, необходимые для записи в Berkeley DB.
 */
class WalletTransaction {
public:
    /**
     * @brief Конструктор по умолчанию
     */
    WalletTransaction();
    
    /**
     * @brief Конструктор с параметрами
     * @param txid - хэш транзакции (32 байта)
     * @param hash - дубликат хэша (32 байта)
     * @param version - версия транзакции
     * @param vin - вектор входов транзакции
     * @param vout - вектор выходов транзакции
     * @param nLockTime - время блокировки
     */
    WalletTransaction(const std::vector<unsigned char>& txid,
                     const std::vector<unsigned char>& hash,
                     uint32_t version,
                     const std::vector<CTxIn>& vin,
                     const std::vector<CTxOut>& vout,
                     uint32_t nLockTime);
    
    /**
     * @brief Деструктор
     */
    ~WalletTransaction();
    
    // START_METHOD_setTxid
    // START_CONTRACT:
    // PURPOSE: Установка хэша транзакции (txid)
    // INPUTS: const std::vector<unsigned char>& txid - хэш транзакции (32 байта)
    // OUTPUTS: bool - результат установки
    // KEYWORDS: PATTERN(6): TxIdSet; DOMAIN(8): Transaction; TECH(5): Setter
    // END_CONTRACT
    bool setTxid(const std::vector<unsigned char>& txid);
    
    // START_METHOD_setHash
    // START_CONTRACT:
    // PURPOSE: Установка дубликата хэша транзакции
    // INPUTS: const std::vector<unsigned char>& hash - хэш (32 байта)
    // OUTPUTS: bool - результат установки
    // KEYWORDS: PATTERN(6): HashSet; DOMAIN(8): Transaction; TECH(5): Setter
    // END_CONTRACT
    bool setHash(const std::vector<unsigned char>& hash);
    
    // START_METHOD_setVersion
    // START_CONTRACT:
    // PURPOSE: Установка версии транзакции
    // INPUTS: uint32_t version - версия транзакции
    // OUTPUTS: void
    // KEYWORDS: PATTERN(7): VersionSet; DOMAIN(8): Transaction; TECH(5): Setter
    // END_CONTRACT
    void setVersion(uint32_t version);
    
    // START_METHOD_setVin
    // START_CONTRACT:
    // PURPOSE: Установка входов транзакции
    // INPUTS: const std::vector<CTxIn>& vin - вектор входов
    // OUTPUTS: void
    // KEYWORDS: PATTERN(6): VinSet; DOMAIN(8): Transaction; TECH(5): Setter
    // END_CONTRACT
    void setVin(const std::vector<CTxIn>& vin);
    
    // START_METHOD_setVout
    // START_CONTRACT:
    // PURPOSE: Установка выходов транзакции
    // INPUTS: const std::vector<CTxOut>& vout - вектор выходов
    // OUTPUTS: void
    // KEYWORDS: PATTERN(7): VoutSet; DOMAIN(8): Transaction; TECH(5): Setter
    // END_CONTRACT
    void setVout(const std::vector<CTxOut>& vout);
    
    // START_METHOD_setNLockTime
    // START_CONTRACT:
    // PURPOSE: Установка времени блокировки
    // INPUTS: uint32_t nLockTime - время блокировки
    // OUTPUTS: void
    // KEYWORDS: PATTERN(8): LockTimeSet; DOMAIN(8): Transaction; TECH(5): Setter
    // END_CONTRACT
    void setNLockTime(uint32_t nLockTime);
    
    // START_METHOD_setNTimeReceived
    // START_CONTRACT:
    // PURPOSE: Установка времени получения транзакции
    // INPUTS: uint32_t nTimeReceived - время получения
    // OUTPUTS: void
    // KEYWORDS: PATTERN(9): TimeReceivedSet; DOMAIN(8): Transaction; TECH(5): Setter
    // END_CONTRACT
    void setNTimeReceived(uint32_t nTimeReceived);
    
    // START_METHOD_setFromMe
    // START_CONTRACT:
    // PURPOSE: Установка флага "от меня"
    // INPUTS: bool fFromMe - флаг отправки от меня
    // OUTPUTS: void
    // KEYWORDS: PATTERN(7): FromMeSet; DOMAIN(8): Transaction; TECH(5): Setter
    // END_CONTRACT
    void setFromMe(bool fFromMe);
    
    // START_METHOD_setSpent
    // START_CONTRACT:
    // PURPOSE: Установка флага "потрачено"
    // INPUTS: bool fSpent - флаг потрачено
    // OUTPUTS: void
    // KEYWORDS: PATTERN(6): SpentSet; DOMAIN(8): Transaction; TECH(5): Setter
    // END_CONTRACT
    void setSpent(bool fSpent);
    
    // START_METHOD_getTxid
    // START_CONTRACT:
    // PURPOSE: Получение хэша транзакции (txid)
    // INPUTS: Нет
    // OUTPUTS: std::vector<unsigned char> - хэш транзакции
    // KEYWORDS: PATTERN(6): TxIdGet; DOMAIN(8): Transaction; TECH(5): Getter
    // END_CONTRACT
    std::vector<unsigned char> getTxid() const;
    
    // START_METHOD_getHash
    // START_CONTRACT:
    // PURPOSE: Получение дубликата хэша транзакции
    // INPUTS: Нет
    // OUTPUTS: std::vector<unsigned char> - хэш транзакции
    // KEYWORDS: PATTERN(6): HashGet; DOMAIN(8): Transaction; TECH(5): Getter
    // END_CONTRACT
    std::vector<unsigned char> getHash() const;
    
    // START_METHOD_getVersion
    // START_CONTRACT:
    // PURPOSE: Получение версии транзакции
    // INPUTS: Нет
    // OUTPUTS: uint32_t - версия транзакции
    // KEYWORDS: PATTERN(7): VersionGet; DOMAIN(8): Transaction; TECH(5): Getter
    // END_CONTRACT
    uint32_t getVersion() const;
    
    // START_METHOD_getVin
    // START_CONTRACT:
    // PURPOSE: Получение входов транзакции
    // INPUTS: Нет
    // OUTPUTS: const std::vector<CTxIn>& - вектор входов
    // KEYWORDS: PATTERN(6): VinGet; DOMAIN(8): Transaction; TECH(5): Getter
    // END_CONTRACT
    const std::vector<CTxIn>& getVin() const;
    
    // START_METHOD_getVout
    // START_CONTRACT:
    // PURPOSE: Получение выходов транзакции
    // INPUTS: Нет
    // OUTPUTS: const std::vector<CTxOut>& - вектор выходов
    // KEYWORDS: PATTERN(7): VoutGet; DOMAIN(8): Transaction; TECH(5): Getter
    // END_CONTRACT
    const std::vector<CTxOut>& getVout() const;
    
    // START_METHOD_getNLockTime
    // START_CONTRACT:
    // PURPOSE: Получение времени блокировки
    // INPUTS: Нет
    // OUTPUTS: uint32_t - время блокировки
    // KEYWORDS: PATTERN(8): LockTimeGet; DOMAIN(8): Transaction; TECH(5): Getter
    // END_CONTRACT
    uint32_t getNLockTime() const;
    
    // START_METHOD_getNTimeReceived
    // START_CONTRACT:
    // PURPOSE: Получения времени получения транзакции
    // INPUTS: Нет
    // OUTPUTS: uint32_t - время получения
    // KEYWORDS: PATTERN(9): TimeReceivedGet; DOMAIN(8): Transaction; TECH(5): Getter
    // END_CONTRACT
    uint32_t getNTimeReceived() const;
    
    // START_METHOD_getFromMe
    // START_CONTRACT:
    // PURPOSE: Получение флага "от меня"
    // INPUTS: Нет
    // OUTPUTS: bool - флаг от меня
    // KEYWORDS: PATTERN(7): FromMeGet; DOMAIN(8): Transaction; TECH(5): Getter
    // END_CONTRACT
    bool getFromMe() const;
    
    // START_METHOD_getSpent
    // START_CONTRACT:
    // PURPOSE: Получение флага "потрачено"
    // INPUTS: Нет
    // OUTPUTS: bool - флаг потрачено
    // KEYWORDS: PATTERN(6): SpentGet; DOMAIN(8): Transaction; TECH(5): Getter
    // END_CONTRACT
    bool getSpent() const;
    
    // START_METHOD_serialize
    // START_CONTRACT:
    // PURPOSE: Сериализация транзакции в бинарный формат Berkeley DB
    // INPUTS: Нет
    // OUTPUTS: std::vector<unsigned char> - сериализованные данные
    // KEYWORDS: PATTERN(8): Serialization; DOMAIN(9): Serialization; TECH(6): Binary
    // END_CONTRACT
    std::vector<unsigned char> serialize() const;
    
    // START_METHOD_deserialize
    // START_CONTRACT:
    // PURPOSE: Десериализация транзакции из бинарного формата Berkeley DB
    // INPUTS: const std::vector<unsigned char>& data - сериализованные данные
    // OUTPUTS: bool - результат десериализации
    // KEYWORDS: PATTERN(9): Deserialization; DOMAIN(9): Deserialization; TECH(6): Binary
    // END_CONTRACT
    bool deserialize(const std::vector<unsigned char>& data);
    
    // START_METHOD_createKey
    // START_CONTRACT:
    // PURPOSE: Создание ключа записи для Berkeley DB
    // INPUTS: Нет
    // OUTPUTS: std::vector<unsigned char> - ключ записи (префикс "tx" + txid)
    // KEYWORDS: PATTERN(7): KeyCreation; DOMAIN(9): KeyValueStore; TECH(5): DB
    // END_CONTRACT
    std::vector<unsigned char> createKey() const;
    
    // START_METHOD_isValid
    // START_CONTRACT:
    // PURPOSE: Проверка валидности транзакции
    // INPUTS: Нет
    // OUTPUTS: bool - true если транзакция валидна
    // KEYWORDS: PATTERN(7): Validation; DOMAIN(8): Transaction; TECH(5): Check
    // END_CONTRACT
    bool isValid() const;

private:
    // Хэш транзакции (txid) - 32 байта
    std::vector<unsigned char> txid_;
    
    // Дубликат хэша - 32 байта
    std::vector<unsigned char> hash_;
    
    // Версия транзакции - 4 байта
    uint32_t version_;
    
    // Вектор входов транзакции
    std::vector<CTxIn> vin_;
    
    // Вектор выходов транзакции
    std::vector<CTxOut> vout_;
    
    // Время блокировки - 4 байта
    uint32_t nLockTime_;
    
    // Время получения - 4 байта
    uint32_t nTimeReceived_;
    
    // Флаг "от меня" - 1 байт
    bool fFromMe_;
    
    // Флаг "потрачено" - 1 байт
    bool fSpent_;
    
    // Вспомогательные методы для сериализации
    // START_HELPER_encodeVarint
    // START_CONTRACT:
    // PURPOSE: Кодирование числа в формат Bitcoin Varint
    // INPUTS: uint64_t value - число для кодирования
    // OUTPUTS: std::vector<unsigned char> - закодированное значение
    // KEYWORDS: PATTERN(8): VarintEncode; DOMAIN(7): Serialization; TECH(6): Bitcoin
    // END_CONTRACT
    std::vector<unsigned char> encodeVarint(uint64_t value) const;
    
    // START_HELPER_decodeVarint
    // START_CONTRACT:
    // PURPOSE: Декодирование числа из формата Bitcoin Varint
    // INPUTS: 
    // - const std::vector<unsigned char>& data - закодированные данные
    // - size_t& pos - позиция начала чтения (изменяется при чтении)
    // OUTPUTS: uint64_t - декодированное значение
    // KEYWORDS: PATTERN(8): VarintDecode; DOMAIN(7): Deserialization; TECH(6): Bitcoin
    // END_CONTRACT
    uint64_t decodeVarint(const std::vector<unsigned char>& data, size_t& pos) const;
    
    // START_HELPER_serializeInt
    // START_CONTRACT:
    // PURPOSE: Сериализация целого числа в little-endian формат
    // INPUTS: uint32_t value - число для сериализации
    // OUTPUTS: std::vector<unsigned char> - сериализованные данные (4 байта)
    // KEYWORDS: PATTERN(7): IntSerialization; DOMAIN(6): Integer; TECH(5): LittleEndian
    // END_CONTRACT
    std::vector<unsigned char> serializeInt(uint32_t value) const;
    
    // START_HELPER_deserializeInt
    // START_CONTRACT:
    // PURPOSE: Десериализация целого числа из little-endian формата
    // INPUTS: 
    // - const std::vector<unsigned char>& data - сериализованные данные
    // - size_t& pos - позиция начала чтения
    // OUTPUTS: uint32_t - десериализованное значение
    // KEYWORDS: PATTERN(8): IntDeserialization; DOMAIN(6): Integer; TECH(5): LittleEndian
    // END_CONTRACT
    uint32_t deserializeInt(const std::vector<unsigned char>& data, size_t& pos) const;
    
    // START_HELPER_serializeInt64
    // START_CONTRACT:
    // PURPOSE: Сериализация 64-битного целого числа в little-endian формат
    // INPUTS: uint64_t value - число для сериализации
    // OUTPUTS: std::vector<unsigned char> - сериализованные данные (8 байт)
    // KEYWORDS: PATTERN(8): Int64Serialization; DOMAIN(6): Integer; TECH(5): LittleEndian
    // END_CONTRACT
    std::vector<unsigned char> serializeInt64(uint64_t value) const;
    
    // START_HELPER_deserializeInt64
    // START_CONTRACT:
    // PURPOSE: Десериализация 64-битного целого числа из little-endian формата
    // INPUTS: 
    // - const std::vector<unsigned char>& data - сериализованные данные
    // - size_t& pos - позиция начала чтения
    // OUTPUTS: uint64_t - десериализованное значение
    // KEYWORDS: PATTERN(9): Int64Deserialization; DOMAIN(6): Integer; TECH(5): LittleEndian
    // END_CONTRACT
    uint64_t deserializeInt64(const std::vector<unsigned char>& data, size_t& pos) const;
    
    // START_HELPER_logToFile
    // START_CONTRACT:
    // PURPOSE: Логирование сообщений в файл
    // INPUTS: const std::string& message - сообщение для логирования
    // OUTPUTS: Нет
    // KEYWORDS: PATTERN(5): Logging; DOMAIN(5): Debug; TECH(4): FileIO
    // END_CONTRACT
    void logToFile(const std::string& message) const;
};

/**
 * @brief Фабрика для создания экземпляров WalletTransaction
 */
class WalletTransactionFactory {
public:
    static std::unique_ptr<WalletTransaction> create();
    static std::string getVersion();
};

} // namespace wallet_tx

#endif // WALLET_TX_H
