#include "wallet_tx.h"
#include <iostream>
#include <sstream>
#include <iomanip>
#include <algorithm>

namespace wallet_tx {

// START_FUNCTION_CTxIn_Constructor_Default
// START_CONTRACT:
// PURPOSE: Конструктор по умолчанию для CTxIn
// INPUTS: Нет
// OUTPUTS: Нет
// KEYWORDS: PATTERN(6): Constructor; DOMAIN(8): Transaction; TECH(5): Init
// END_CONTRACT
CTxIn::CTxIn() 
    : prevout_hash(32, 0), 
      prevout_n(0), 
      scriptSig() {
    // Инициализация нулями
}
// END_FUNCTION_CTxIn_Constructor_Default

// START_FUNCTION_CTxIn_Constructor_Params
// START_CONTRACT:
// PURPOSE: Конструктор с параметрами для CTxIn
// INPUTS:
// - const std::vector<unsigned char>& prev_hash - хэш предыдущей транзакции
// - uint32_t prev_n - индекс выхода
// OUTPUTS: Нет
// KEYWORDS: PATTERN(6): Constructor; DOMAIN(8): Transaction; TECH(5): Init
// END_CONTRACT
CTxIn::CTxIn(const std::vector<unsigned char>& prev_hash, uint32_t prev_n)
    : prevout_hash(prev_hash), 
      prevout_n(prev_n), 
      scriptSig() {
}
// END_FUNCTION_CTxIn_Constructor_Params

// START_FUNCTION_CTxIn_serialize
// START_CONTRACT:
// PURPOSE: Сериализация входа транзакции в бинарный формат
// INPUTS: Нет
// OUTPUTS: std::vector<unsigned char> - сериализованные данные
// KEYWORDS: PATTERN(8): Serialization; DOMAIN(9): Serialization; TECH(6): Binary
// END_CONTRACT
std::vector<unsigned char> CTxIn::serialize() const {
    std::vector<unsigned char> result;
    
    // prevout_hash - 32 байта
    result.insert(result.end(), prevout_hash.begin(), prevout_hash.end());
    
    // prevout_n - 4 байта little-endian
    result.push_back(static_cast<unsigned char>(prevout_n & 0xFF));
    result.push_back(static_cast<unsigned char>((prevout_n >> 8) & 0xFF));
    result.push_back(static_cast<unsigned char>((prevout_n >> 16) & 0xFF));
    result.push_back(static_cast<unsigned char>((prevout_n >> 24) & 0xFF));
    
    // scriptSig - varint length + data
    // Используем varint кодирование
    if (scriptSig.size() < 253) {
        result.push_back(static_cast<unsigned char>(scriptSig.size()));
    } else if (scriptSig.size() < 0x10000) {
        result.push_back(0xFD);
        result.push_back(static_cast<unsigned char>(scriptSig.size() & 0xFF));
        result.push_back(static_cast<unsigned char>((scriptSig.size() >> 8) & 0xFF));
    } else {
        result.push_back(0xFE);
        for (int i = 0; i < 4; ++i) {
            result.push_back(static_cast<unsigned char>((scriptSig.size() >> (i * 8)) & 0xFF));
        }
    }
    result.insert(result.end(), scriptSig.begin(), scriptSig.end());
    
    return result;
}
// END_FUNCTION_CTxIn_serialize

// START_FUNCTION_CTxIn_deserialize
// START_CONTRACT:
// PURPOSE: Десериализация входа транзакции из бинарного формата
// INPUTS:
// - const std::vector<unsigned char>& data - сериализованные данные
// - size_t& pos - позиция начала чтения (изменяется при чтении)
// OUTPUTS: bool - результат десериализации
// KEYWORDS: PATTERN(9): Deserialization; DOMAIN(9): Deserialization; TECH(6): Binary
// END_CONTRACT
bool CTxIn::deserialize(const std::vector<unsigned char>& data, size_t& pos) {
    if (pos + 36 > data.size()) { // 32 (hash) + 4 (n)
        return false;
    }
    
    // Читаем prevout_hash - 32 байта
    prevout_hash.assign(data.begin() + pos, data.begin() + pos + 32);
    pos += 32;
    
    // Читаем prevout_n - 4 байта little-endian
    prevout_n = static_cast<uint32_t>(data[pos]) |
                (static_cast<uint32_t>(data[pos + 1]) << 8) |
                (static_cast<uint32_t>(data[pos + 2]) << 16) |
                (static_cast<uint32_t>(data[pos + 3]) << 24);
    pos += 4;
    
    // Читаем длину scriptSig (varint)
    if (pos >= data.size()) {
        return false;
    }
    
    uint64_t script_len = 0;
    if (data[pos] < 253) {
        script_len = data[pos];
        pos++;
    } else if (data[pos] == 0xFD) {
        if (pos + 3 > data.size()) return false;
        script_len = static_cast<uint64_t>(data[pos + 1]) |
                     (static_cast<uint64_t>(data[pos + 2]) << 8);
        pos += 3;
    } else if (data[pos] == 0xFE) {
        if (pos + 5 > data.size()) return false;
        for (int i = 0; i < 4; ++i) {
            script_len |= static_cast<uint64_t>(data[pos + 1 + i]) << (i * 8);
        }
        pos += 5;
    } else {
        // 0xFF - 9 байт для length
        if (pos + 9 > data.size()) return false;
        for (int i = 0; i < 8; ++i) {
            script_len |= static_cast<uint64_t>(data[pos + 1 + i]) << (i * 8);
        }
        pos += 9;
    }
    
    // Читаем scriptSig
    if (pos + script_len > data.size()) {
        return false;
    }
    scriptSig.assign(data.begin() + pos, data.begin() + pos + script_len);
    pos += script_len;
    
    return true;
}
// END_FUNCTION_CTxIn_deserialize

// START_FUNCTION_CTxOut_Constructor_Default
// START_CONTRACT:
// PURPOSE: Конструктор по умолчанию для CTxOut
// INPUTS: Нет
// OUTPUTS: Нет
// KEYWORDS: PATTERN(6): Constructor; DOMAIN(8): Transaction; TECH(5): Init
// END_CONTRACT
CTxOut::CTxOut() 
    : nValue(0), 
      scriptPubKey() {
}
// END_FUNCTION_CTxOut_Constructor_Default

// START_FUNCTION_CTxOut_Constructor_Params
// START_CONTRACT:
// PURPOSE: Конструктор с параметрами для CTxOut
// INPUTS:
// - uint64_t value - сумма выхода
// - const std::vector<unsigned char>& script - скрипт
// OUTPUTS: Нет
// KEYWORDS: PATTERN(6): Constructor; DOMAIN(8): Transaction; TECH(5): Init
// END_CONTRACT
CTxOut::CTxOut(uint64_t value, const std::vector<unsigned char>& script)
    : nValue(value), 
      scriptPubKey(script) {
}
// END_FUNCTION_CTxOut_Constructor_Params

// START_FUNCTION_CTxOut_serialize
// START_CONTRACT:
// PURPOSE: Сериализация выхода транзакции в бинарный формат
// INPUTS: Нет
// OUTPUTS: std::vector<unsigned char> - сериализованные данные
// KEYWORDS: PATTERN(8): Serialization; DOMAIN(9): Serialization; TECH(6): Binary
// END_CONTRACT
std::vector<unsigned char> CTxOut::serialize() const {
    std::vector<unsigned char> result;
    
    // nValue - 8 байт little-endian
    for (int i = 0; i < 8; ++i) {
        result.push_back(static_cast<unsigned char>((nValue >> (i * 8)) & 0xFF));
    }
    
    // scriptPubKey - varint length + data
    if (scriptPubKey.size() < 253) {
        result.push_back(static_cast<unsigned char>(scriptPubKey.size()));
    } else if (scriptPubKey.size() < 0x10000) {
        result.push_back(0xFD);
        result.push_back(static_cast<unsigned char>(scriptPubKey.size() & 0xFF));
        result.push_back(static_cast<unsigned char>((scriptPubKey.size() >> 8) & 0xFF));
    } else {
        result.push_back(0xFE);
        for (int i = 0; i < 4; ++i) {
            result.push_back(static_cast<unsigned char>((scriptPubKey.size() >> (i * 8)) & 0xFF));
        }
    }
    result.insert(result.end(), scriptPubKey.begin(), scriptPubKey.end());
    
    return result;
}
// END_FUNCTION_CTxOut_serialize

// START_FUNCTION_CTxOut_deserialize
// START_CONTRACT:
// PURPOSE: Десериализация выхода транзакции из бинарного формата
// INPUTS:
// - const std::vector<unsigned char>& data - сериализованные данные
// - size_t& pos - позиция начала чтения (изменяется при чтении)
// OUTPUTS: bool - результат десериализации
// KEYWORDS: PATTERN(9): Deserialization; DOMAIN(9): Deserialization; TECH(6): Binary
// END_CONTRACT
bool CTxOut::deserialize(const std::vector<unsigned char>& data, size_t& pos) {
    if (pos + 8 > data.size()) { // 8 bytes for nValue
        return false;
    }
    
    // Читаем nValue - 8 байт little-endian
    nValue = 0;
    for (int i = 0; i < 8; ++i) {
        nValue |= static_cast<uint64_t>(data[pos + i]) << (i * 8);
    }
    pos += 8;
    
    // Читаем длину scriptPubKey (varint)
    if (pos >= data.size()) {
        return false;
    }
    
    uint64_t script_len = 0;
    if (data[pos] < 253) {
        script_len = data[pos];
        pos++;
    } else if (data[pos] == 0xFD) {
        if (pos + 3 > data.size()) return false;
        script_len = static_cast<uint64_t>(data[pos + 1]) |
                     (static_cast<uint64_t>(data[pos + 2]) << 8);
        pos += 3;
    } else if (data[pos] == 0xFE) {
        if (pos + 5 > data.size()) return false;
        for (int i = 0; i < 4; ++i) {
            script_len |= static_cast<uint64_t>(data[pos + 1 + i]) << (i * 8);
        }
        pos += 5;
    } else {
        // 0xFF - 9 байт для length
        if (pos + 9 > data.size()) return false;
        for (int i = 0; i < 8; ++i) {
            script_len |= static_cast<uint64_t>(data[pos + 1 + i]) << (i * 8);
        }
        pos += 9;
    }
    
    // Читаем scriptPubKey
    if (pos + script_len > data.size()) {
        return false;
    }
    scriptPubKey.assign(data.begin() + pos, data.begin() + pos + script_len);
    pos += script_len;
    
    return true;
}
// END_FUNCTION_CTxOut_deserialize

// START_FUNCTION_WalletTransaction_Constructor_Default
// START_CONTRACT:
// PURPOSE: Конструктор по умолчанию
// INPUTS: Нет
// OUTPUTS: Нет
// KEYWORDS: PATTERN(6): Constructor; DOMAIN(9): WalletTransaction; TECH(5): Init
// END_CONTRACT
WalletTransaction::WalletTransaction() 
    : txid_(32, 0),
      hash_(32, 0),
      version_(TX_VERSION),
      vin_(),
      vout_(),
      nLockTime_(0),
      nTimeReceived_(0),
      fFromMe_(false),
      fSpent_(false) {
    logToFile("[WalletTransaction] Конструктор по умолчанию вызван");
}
// END_FUNCTION_WalletTransaction_Constructor_Default

// START_FUNCTION_WalletTransaction_Constructor_Params
// START_CONTRACT:
// PURPOSE: Конструктор с параметрами
// INPUTS:
// - const std::vector<unsigned char>& txid - хэш транзакции (32 байта)
// - const std::vector<unsigned char>& hash - дубликат хэша (32 байта)
// - uint32_t version - версия транзакции
// - const std::vector<CTxIn>& vin - вектор входов
// - const std::vector<CTxOut>& vout - вектор выходов
// - uint32_t nLockTime - время блокировки
// OUTPUTS: Нет
// KEYWORDS: PATTERN(6): Constructor; DOMAIN(9): WalletTransaction; TECH(5): Init
// END_CONTRACT
WalletTransaction::WalletTransaction(const std::vector<unsigned char>& txid,
                                   const std::vector<unsigned char>& hash,
                                   uint32_t version,
                                   const std::vector<CTxIn>& vin,
                                   const std::vector<CTxOut>& vout,
                                   uint32_t nLockTime)
    : txid_(txid),
      hash_(hash),
      version_(version),
      vin_(vin),
      vout_(vout),
      nLockTime_(nLockTime),
      nTimeReceived_(static_cast<uint32_t>(time(nullptr))),
      fFromMe_(false),
      fSpent_(false) {
    std::ostringstream oss;
    oss << "[WalletTransaction] Конструктор с параметрами вызван. txid size: " << txid.size() 
        << ", hash size: " << hash.size() << ", vin: " << vin.size() << ", vout: " << vout.size();
    logToFile(oss.str());
}
// END_FUNCTION_WalletTransaction_Constructor_Params

// START_FUNCTION_WalletTransaction_Destructor
// START_CONTRACT:
// PURPOSE: Деструктор
// INPUTS: Нет
// OUTPUTS: Нет
// KEYWORDS: PATTERN(6): Destructor; DOMAIN(9): WalletTransaction; TECH(5): Cleanup
// END_CONTRACT
WalletTransaction::~WalletTransaction() {
    logToFile("[WalletTransaction] Деструктор вызван");
}
// END_FUNCTION_WalletTransaction_Destructor

// START_FUNCTION_setTxid
// START_CONTRACT:
// PURPOSE: Установка хэша транзакции (txid)
// INPUTS: const std::vector<unsigned char>& txid - хэш транзакции (32 байта)
// OUTPUTS: bool - результат установки
// KEYWORDS: PATTERN(6): TxIdSet; DOMAIN(8): Transaction; TECH(5): Setter
// END_CONTRACT
bool WalletTransaction::setTxid(const std::vector<unsigned char>& txid) {
    if (txid.size() != TX_ID_SIZE) {
        logToFile("[setTxid] ОШИБКА: Неверный размер txid");
        return false;
    }
    txid_ = txid;
    logToFile("[setTxid] txid установлен успешно");
    return true;
}
// END_FUNCTION_setTxid

// START_FUNCTION_setHash
// START_CONTRACT:
// PURPOSE: Установка дубликата хэша транзакции
// INPUTS: const std::vector<unsigned char>& hash - хэш (32 байта)
// OUTPUTS: bool - результат установки
// KEYWORDS: PATTERN(6): HashSet; DOMAIN(8): Transaction; TECH(5): Setter
// END_CONTRACT
bool WalletTransaction::setHash(const std::vector<unsigned char>& hash) {
    if (hash.size() != TX_HASH_SIZE) {
        logToFile("[setHash] ОШИБКА: Неверный размер hash");
        return false;
    }
    hash_ = hash;
    logToFile("[setHash] hash установлен успешно");
    return true;
}
// END_FUNCTION_setHash

// START_FUNCTION_setVersion
// START_CONTRACT:
// PURPOSE: Установка версии транзакции
// INPUTS: uint32_t version - версия транзакции
// OUTPUTS: void
// KEYWORDS: PATTERN(7): VersionSet; DOMAIN(8): Transaction; TECH(5): Setter
// END_CONTRACT
void WalletTransaction::setVersion(uint32_t version) {
    version_ = version;
    std::ostringstream oss;
    oss << "[setVersion] version установлен: " << version;
    logToFile(oss.str());
}
// END_FUNCTION_setVersion

// START_FUNCTION_setVin
// START_CONTRACT:
// PURPOSE: Установка входов транзакции
// INPUTS: const std::vector<CTxIn>& vin - вектор входов
// OUTPUTS: void
// KEYWORDS: PATTERN(6): VinSet; DOMAIN(8): Transaction; TECH(5): Setter
// END_CONTRACT
void WalletTransaction::setVin(const std::vector<CTxIn>& vin) {
    vin_ = vin;
    std::ostringstream oss;
    oss << "[setVin] vin установлен. Размер: " << vin.size();
    logToFile(oss.str());
}
// END_FUNCTION_setVin

// START_FUNCTION_setVout
// START_CONTRACT:
// PURPOSE: Установка выходов транзакции
// INPUTS: const std::vector<CTxOut>& vout - вектор выходов
// OUTPUTS: void
// KEYWORDS: PATTERN(7): VoutSet; DOMAIN(8): Transaction; TECH(5): Setter
// END_CONTRACT
void WalletTransaction::setVout(const std::vector<CTxOut>& vout) {
    vout_ = vout;
    std::ostringstream oss;
    oss << "[setVout] vout установлен. Размер: " << vout.size();
    logToFile(oss.str());
}
// END_FUNCTION_setVout

// START_FUNCTION_setNLockTime
// START_CONTRACT:
// PURPOSE: Установка времени блокировки
// INPUTS: uint32_t nLockTime - время блокировки
// OUTPUTS: void
// KEYWORDS: PATTERN(8): LockTimeSet; DOMAIN(8): Transaction; TECH(5): Setter
// END_CONTRACT
void WalletTransaction::setNLockTime(uint32_t nLockTime) {
    nLockTime_ = nLockTime;
    std::ostringstream oss;
    oss << "[setNLockTime] nLockTime установлен: " << nLockTime;
    logToFile(oss.str());
}
// END_FUNCTION_setNLockTime

// START_FUNCTION_setNTimeReceived
// START_CONTRACT:
// PURPOSE: Установка времени получения транзакции
// INPUTS: uint32_t nTimeReceived - время получения
// OUTPUTS: void
// KEYWORDS: PATTERN(9): TimeReceivedSet; DOMAIN(8): Transaction; TECH(5): Setter
// END_CONTRACT
void WalletTransaction::setNTimeReceived(uint32_t nTimeReceived) {
    nTimeReceived_ = nTimeReceived;
    std::ostringstream oss;
    oss << "[setNTimeReceived] nTimeReceived установлен: " << nTimeReceived;
    logToFile(oss.str());
}
// END_FUNCTION_setNTimeReceived

// START_FUNCTION_setFromMe
// START_CONTRACT:
// PURPOSE: Установка флага "от меня"
// INPUTS: bool fFromMe - флаг отправки от меня
// OUTPUTS: void
// KEYWORDS: PATTERN(7): FromMeSet; DOMAIN(8): Transaction; TECH(5): Setter
// END_CONTRACT
void WalletTransaction::setFromMe(bool fFromMe) {
    fFromMe_ = fFromMe;
    std::ostringstream oss;
    oss << "[setFromMe] fFromMe установлен: " << (fFromMe ? "true" : "false");
    logToFile(oss.str());
}
// END_FUNCTION_setFromMe

// START_FUNCTION_setSpent
// START_CONTRACT:
// PURPOSE: Установка флага "потрачено"
// INPUTS: bool fSpent - флаг потрачено
// OUTPUTS: void
// KEYWORDS: PATTERN(6): SpentSet; DOMAIN(8): Transaction; TECH(5): Setter
// END_CONTRACT
void WalletTransaction::setSpent(bool fSpent) {
    fSpent_ = fSpent;
    std::ostringstream oss;
    oss << "[setSpent] fSpent установлен: " << (fSpent ? "true" : "false");
    logToFile(oss.str());
}
// END_FUNCTION_setSpent

// START_FUNCTION_getTxid
// START_CONTRACT:
// PURPOSE: Получение хэша транзакции (txid)
// INPUTS: Нет
// OUTPUTS: std::vector<unsigned char> - хэш транзакции
// KEYWORDS: PATTERN(6): TxIdGet; DOMAIN(8): Transaction; TECH(5): Getter
// END_CONTRACT
std::vector<unsigned char> WalletTransaction::getTxid() const {
    return txid_;
}
// END_FUNCTION_getTxid

// START_FUNCTION_getHash
// START_CONTRACT:
// PURPOSE: Получение дубликата хэша транзакции
// INPUTS: Нет
// OUTPUTS: std::vector<unsigned char> - хэш транзакции
// KEYWORDS: PATTERN(6): HashGet; DOMAIN(8): Transaction; TECH(5): Getter
// END_CONTRACT
std::vector<unsigned char> WalletTransaction::getHash() const {
    return hash_;
}
// END_FUNCTION_getHash

// START_FUNCTION_getVersion
// START_CONTRACT:
// PURPOSE: Получение версии транзакции
// INPUTS: Нет
// OUTPUTS: uint32_t - версия транзакции
// KEYWORDS: PATTERN(7): VersionGet; DOMAIN(8): Transaction; TECH(5): Getter
// END_CONTRACT
uint32_t WalletTransaction::getVersion() const {
    return version_;
}
// END_FUNCTION_getVersion

// START_FUNCTION_getVin
// START_CONTRACT:
// PURPOSE: Получение входов транзакции
// INPUTS: Нет
// OUTPUTS: const std::vector<CTxIn>& - вектор входов
// KEYWORDS: PATTERN(6): VinGet; DOMAIN(8): Transaction; TECH(5): Getter
// END_CONTRACT
const std::vector<CTxIn>& WalletTransaction::getVin() const {
    return vin_;
}
// END_FUNCTION_getVin

// START_FUNCTION_getVout
// START_CONTRACT:
// PURPOSE: Получение выходов транзакции
// INPUTS: Нет
// OUTPUTS: const std::vector<CTxOut>& - вектор выходов
// KEYWORDS: PATTERN(7): VoutGet; DOMAIN(8): Transaction; TECH(5): Getter
// END_CONTRACT
const std::vector<CTxOut>& WalletTransaction::getVout() const {
    return vout_;
}
// END_FUNCTION_getVout

// START_FUNCTION_getNLockTime
// START_CONTRACT:
// PURPOSE: Получение времени блокировки
// INPUTS: Нет
// OUTPUTS: uint32_t - время блокировки
// KEYWORDS: PATTERN(8): LockTimeGet; DOMAIN(8): Transaction; TECH(5): Getter
// END_CONTRACT
uint32_t WalletTransaction::getNLockTime() const {
    return nLockTime_;
}
// END_FUNCTION_getNLockTime

// START_FUNCTION_getNTimeReceived
// START_CONTRACT:
// PURPOSE: Получения времени получения транзакции
// INPUTS: Нет
// OUTPUTS: uint32_t - время получения
// KEYWORDS: PATTERN(9): TimeReceivedGet; DOMAIN(8): Transaction; TECH(5): Getter
// END_CONTRACT
uint32_t WalletTransaction::getNTimeReceived() const {
    return nTimeReceived_;
}
// END_FUNCTION_getNTimeReceived

// START_FUNCTION_getFromMe
// START_CONTRACT:
// PURPOSE: Получение флага "от меня"
// INPUTS: Нет
// OUTPUTS: bool - флаг от меня
// KEYWORDS: PATTERN(7): FromMeGet; DOMAIN(8): Transaction; TECH(5): Getter
// END_CONTRACT
bool WalletTransaction::getFromMe() const {
    return fFromMe_;
}
// END_FUNCTION_getFromMe

// START_FUNCTION_getSpent
// START_CONTRACT:
// PURPOSE: Получение флага "потрачено"
// INPUTS: Нет
// OUTPUTS: bool - флаг потрачено
// KEYWORDS: PATTERN(6): SpentGet; DOMAIN(8): Transaction; TECH(5): Getter
// END_CONTRACT
bool WalletTransaction::getSpent() const {
    return fSpent_;
}
// END_FUNCTION_getSpent

// START_FUNCTION_serialize
// START_CONTRACT:
// PURPOSE: Сериализация транзакции в бинарный формат Berkeley DB
// INPUTS: Нет
// OUTPUTS: std::vector<unsigned char> - сериализованные данные
// KEYWORDS: PATTERN(8): Serialization; DOMAIN(9): Serialization; TECH(6): Binary
// END_CONTRACT
std::vector<unsigned char> WalletTransaction::serialize() const {
    std::vector<unsigned char> result;
    
    std::ostringstream oss;
    oss << "[serialize] Сериализация транзакции. vin: " << vin_.size() << ", vout: " << vout_.size();
    logToFile(oss.str());
    
    // txid - 32 байта
    result.insert(result.end(), txid_.begin(), txid_.end());
    
    // hash - 32 байта
    result.insert(result.end(), hash_.begin(), hash_.end());
    
    // version - 4 байта little-endian
    std::vector<unsigned char> version_bytes = serializeInt(version_);
    result.insert(result.end(), version_bytes.begin(), version_bytes.end());
    
    // vin - varint count + serialized inputs
    std::vector<unsigned char> vin_data;
    for (const auto& input : vin_) {
        std::vector<unsigned char> input_data = input.serialize();
        vin_data.insert(vin_data.end(), input_data.begin(), input_data.end());
    }
    std::vector<unsigned char> vin_len = encodeVarint(vin_.size());
    result.insert(result.end(), vin_len.begin(), vin_len.end());
    result.insert(result.end(), vin_data.begin(), vin_data.end());
    
    // vout - varint count + serialized outputs
    std::vector<unsigned char> vout_data;
    for (const auto& output : vout_) {
        std::vector<unsigned char> output_data = output.serialize();
        vout_data.insert(vout_data.end(), output_data.begin(), output_data.end());
    }
    std::vector<unsigned char> vout_len = encodeVarint(vout_.size());
    result.insert(result.end(), vout_len.begin(), vout_len.end());
    result.insert(result.end(), vout_data.begin(), vout_data.end());
    
    // nLockTime - 4 байта little-endian
    std::vector<unsigned char> locktime_bytes = serializeInt(nLockTime_);
    result.insert(result.end(), locktime_bytes.begin(), locktime_bytes.end());
    
    // nTimeReceived - 4 байта little-endian
    std::vector<unsigned char> time_received_bytes = serializeInt(nTimeReceived_);
    result.insert(result.end(), time_received_bytes.begin(), time_received_bytes.end());
    
    // fFromMe - 1 байт
    result.push_back(fFromMe_ ? 1 : 0);
    
    // fSpent - 1 байт
    result.push_back(fSpent_ ? 1 : 0);
    
    oss.str("");
    oss << "[serialize] Сериализация завершена. Размер данных: " << result.size() << " байт";
    logToFile(oss.str());
    
    return result;
}
// END_FUNCTION_serialize

// START_FUNCTION_deserialize
// START_CONTRACT:
// PURPOSE: Десериализация транзакции из бинарного формата Berkeley DB
// INPUTS: const std::vector<unsigned char>& data - сериализованные данные
// OUTPUTS: bool - результат десериализации
// KEYWORDS: PATTERN(9): Deserialization; DOMAIN(9): Deserialization; TECH(6): Binary
// END_CONTRACT
bool WalletTransaction::deserialize(const std::vector<unsigned char>& data) {
    logToFile("[deserialize] Начало десериализации транзакции");
    
    if (data.size() < 74) { // min: 32+32+4+1+1+4 (txid+hash+version+flags+locktime+timereceived)
        logToFile("[deserialize] ОШИБКА: Данные слишком малы");
        return false;
    }
    
    size_t pos = 0;
    
    // Читаем txid - 32 байта
    if (pos + 32 > data.size()) {
        logToFile("[deserialize] ОШИБКА: Недостаточно данных для txid");
        return false;
    }
    txid_.assign(data.begin() + pos, data.begin() + pos + 32);
    pos += 32;
    
    // Читаем hash - 32 байта
    if (pos + 32 > data.size()) {
        logToFile("[deserialize] ОШИБКА: Недостаточно данных для hash");
        return false;
    }
    hash_.assign(data.begin() + pos, data.begin() + pos + 32);
    pos += 32;
    
    // Читаем version - 4 байта
    version_ = deserializeInt(data, pos);
    
    // Читаем количество входов (vin) - varint
    uint64_t vin_count = decodeVarint(data, pos);
    
    // Читаем входы
    vin_.clear();
    for (uint64_t i = 0; i < vin_count; ++i) {
        CTxIn input;
        if (!input.deserialize(data, pos)) {
            std::ostringstream oss;
            oss << "[deserialize] ОШИБКА: Не удалось десериализовать вход " << i;
            logToFile(oss.str());
            return false;
        }
        vin_.push_back(input);
    }
    
    // Читаем количество выходов (vout) - varint
    uint64_t vout_count = decodeVarint(data, pos);
    
    // Читаем выходы
    vout_.clear();
    for (uint64_t i = 0; i < vout_count; ++i) {
        CTxOut output;
        if (!output.deserialize(data, pos)) {
            std::ostringstream oss;
            oss << "[deserialize] ОШИБКА: Не удалось десериализовать выход " << i;
            logToFile(oss.str());
            return false;
        }
        vout_.push_back(output);
    }
    
    // Читаем nLockTime - 4 байта
    nLockTime_ = deserializeInt(data, pos);
    
    // Читаем nTimeReceived - 4 байта
    nTimeReceived_ = deserializeInt(data, pos);
    
    // Читаем fFromMe - 1 байт
    if (pos >= data.size()) {
        logToFile("[deserialize] ОШИБКА: Недостаточно данных для fFromMe");
        return false;
    }
    fFromMe_ = (data[pos] != 0);
    pos++;
    
    // Читаем fSpent - 1 байт
    if (pos >= data.size()) {
        logToFile("[deserialize] ОШИБКА: Недостаточно данных для fSpent");
        return false;
    }
    fSpent_ = (data[pos] != 0);
    pos++;
    
    std::ostringstream oss;
    oss << "[deserialize] Десериализация завершена успешно. vin: " << vin_.size() << ", vout: " << vout_.size();
    logToFile(oss.str());
    
    return true;
}
// END_FUNCTION_deserialize

// START_FUNCTION_createKey
// START_CONTRACT:
// PURPOSE: Создание ключа записи для Berkeley DB
// INPUTS: Нет
// OUTPUTS: std::vector<unsigned char> - ключ записи (префикс "tx" + txid)
// KEYWORDS: PATTERN(7): KeyCreation; DOMAIN(9): KeyValueStore; TECH(5): DB
// END_CONTRACT
std::vector<unsigned char> WalletTransaction::createKey() const {
    std::vector<unsigned char> key;
    
    // Префикс "tx" (2 байта)
    key.push_back('t');
    key.push_back('x');
    
    // Добавляем txid (32 байта)
    key.insert(key.end(), txid_.begin(), txid_.end());
    
    logToFile("[createKey] Ключ транзакции создан");
    
    return key;
}
// END_FUNCTION_createKey

// START_FUNCTION_isValid
// START_CONTRACT:
// PURPOSE: Проверка валидности транзакции
// INPUTS: Нет
// OUTPUTS: bool - true если транзакция валидна
// KEYWORDS: PATTERN(7): Validation; DOMAIN(8): Transaction; TECH(5): Check
// END_CONTRACT
bool WalletTransaction::isValid() const {
    // Проверяем размер txid и hash
    if (txid_.size() != TX_ID_SIZE || hash_.size() != TX_HASH_SIZE) {
        logToFile("[isValid] ОШИБКА: Неверный размер txid или hash");
        return false;
    }
    
    // Проверяем версию
    if (version_ == 0) {
        logToFile("[isValid] ОШИБКА: Неверная версия");
        return false;
    }
    
    logToFile("[isValid] Транзакция валидна");
    return true;
}
// END_FUNCTION_isValid

// START_HELPER_encodeVarint
// START_CONTRACT:
// PURPOSE: Кодирование числа в формат Bitcoin Varint
// INPUTS: uint64_t value - число для кодирования
// OUTPUTS: std::vector<unsigned char> - закодированное значение
// KEYWORDS: PATTERN(8): VarintEncode; DOMAIN(7): Serialization; TECH(6): Bitcoin
// END_CONTRACT
std::vector<unsigned char> WalletTransaction::encodeVarint(uint64_t value) const {
    std::vector<unsigned char> result;
    
    while (value >= 0x80) {
        result.push_back(static_cast<unsigned char>((value & 0x7F) | 0x80));
        value >>= 7;
    }
    
    result.push_back(static_cast<unsigned char>(value & 0x7F));
    
    return result;
}
// END_HELPER_encodeVarint

// START_HELPER_decodeVarint
// START_CONTRACT:
// PURPOSE: Декодирование числа из формата Bitcoin Varint
// INPUTS: 
// - const std::vector<unsigned char>& data - закодированные данные
// - size_t& pos - позиция начала чтения (изменяется при чтении)
// OUTPUTS: uint64_t - декодированное значение
// KEYWORDS: PATTERN(8): VarintDecode; DOMAIN(7): Deserialization; TECH(6): Bitcoin
// END_CONTRACT
uint64_t WalletTransaction::decodeVarint(const std::vector<unsigned char>& data, size_t& pos) const {
    uint64_t result = 0;
    int shift = 0;
    
    while (pos < data.size()) {
        unsigned char byte = data[pos];
        pos++;
        
        result |= static_cast<uint64_t>(byte & 0x7F) << shift;
        
        if ((byte & 0x80) == 0) {
            break;
        }
        
        shift += 7;
        
        if (shift > 63) {
            break;
        }
    }
    
    return result;
}
// END_HELPER_decodeVarint

// START_HELPER_serializeInt
// START_CONTRACT:
// PURPOSE: Сериализация целого числа в little-endian формат
// INPUTS: uint32_t value - число для сериализации
// OUTPUTS: std::vector<unsigned char> - сериализованные данные (4 байта)
// KEYWORDS: PATTERN(7): IntSerialization; DOMAIN(6): Integer; TECH(5): LittleEndian
// END_CONTRACT
std::vector<unsigned char> WalletTransaction::serializeInt(uint32_t value) const {
    std::vector<unsigned char> result(4);
    result[0] = static_cast<unsigned char>(value & 0xFF);
    result[1] = static_cast<unsigned char>((value >> 8) & 0xFF);
    result[2] = static_cast<unsigned char>((value >> 16) & 0xFF);
    result[3] = static_cast<unsigned char>((value >> 24) & 0xFF);
    return result;
}
// END_HELPER_serializeInt

// START_HELPER_deserializeInt
// START_CONTRACT:
// PURPOSE: Десериализация целого числа из little-endian формата
// INPUTS: 
// - const std::vector<unsigned char>& data - сериализованные данные
// - size_t& pos - позиция начала чтения
// OUTPUTS: uint32_t - десериализованное значение
// KEYWORDS: PATTERN(8): IntDeserialization; DOMAIN(6): Integer; TECH(5): LittleEndian
// END_CONTRACT
uint32_t WalletTransaction::deserializeInt(const std::vector<unsigned char>& data, size_t& pos) const {
    if (pos + 4 > data.size()) {
        return 0;
    }
    
    uint32_t result = 0;
    result |= static_cast<uint32_t>(data[pos]);
    result |= static_cast<uint32_t>(data[pos + 1]) << 8;
    result |= static_cast<uint32_t>(data[pos + 2]) << 16;
    result |= static_cast<uint32_t>(data[pos + 3]) << 24;
    pos += 4;
    
    return result;
}
// END_HELPER_deserializeInt

// START_HELPER_serializeInt64
// START_CONTRACT:
// PURPOSE: Сериализация 64-битного целого числа в little-endian формат
// INPUTS: uint64_t value - число для сериализации
// OUTPUTS: std::vector<unsigned char> - сериализованные данные (8 байт)
// KEYWORDS: PATTERN(8): Int64Serialization; DOMAIN(6): Integer; TECH(5): LittleEndian
// END_CONTRACT
std::vector<unsigned char> WalletTransaction::serializeInt64(uint64_t value) const {
    std::vector<unsigned char> result(8);
    for (int i = 0; i < 8; ++i) {
        result[i] = static_cast<unsigned char>((value >> (i * 8)) & 0xFF);
    }
    return result;
}
// END_HELPER_serializeInt64

// START_HELPER_deserializeInt64
// START_CONTRACT:
// PURPOSE: Десериализация 64-битного целого числа из little-endian формата
// INPUTS: 
// - const std::vector<unsigned char>& data - сериализованные данные
// - size_t& pos - позиция начала чтения
// OUTPUTS: uint64_t - десериализованное значение
// KEYWORDS: PATTERN(9): Int64Deserialization; DOMAIN(6): Integer; TECH(5): LittleEndian
// END_CONTRACT
uint64_t WalletTransaction::deserializeInt64(const std::vector<unsigned char>& data, size_t& pos) const {
    if (pos + 8 > data.size()) {
        return 0;
    }
    
    uint64_t result = 0;
    for (int i = 0; i < 8; ++i) {
        result |= static_cast<uint64_t>(data[pos + i]) << (i * 8);
    }
    pos += 8;
    
    return result;
}
// END_HELPER_deserializeInt64

// START_HELPER_logToFile
// START_CONTRACT:
// PURPOSE: Логирование сообщений в файл
// INPUTS: const std::string& message - сообщение для логирования
// OUTPUTS: Нет
// KEYWORDS: PATTERN(5): Logging; DOMAIN(5): Debug; TECH(4): FileIO
// END_CONTRACT
void WalletTransaction::logToFile(const std::string& message) const {
    std::ofstream log_file(LOG_FILE, std::ios::app);
    if (log_file.is_open()) {
        std::time_t now = std::time(nullptr);
        char timestamp[64];
        std::strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", std::localtime(&now));
        log_file << "[" << timestamp << "] " << message << std::endl;
        log_file.close();
    }
}
// END_HELPER_logToFile

// START_FUNCTION_Factory_Create
// START_CONTRACT:
// PURPOSE: Фабричный метод создания экземпляра WalletTransaction
// INPUTS: Нет
// OUTPUTS: std::unique_ptr<WalletTransaction> - новый экземпляр
// KEYWORDS: PATTERN(7): FactoryMethod; DOMAIN(9): Creational; TECH(5): Factory
// END_CONTRACT
std::unique_ptr<WalletTransaction> WalletTransactionFactory::create() {
    return std::unique_ptr<WalletTransaction>(new WalletTransaction());
}
// END_FUNCTION_Factory_Create

// START_FUNCTION_Factory_GetVersion
// START_CONTRACT:
// PURPOSE: Получение версии модуля транзакций кошелька
// INPUTS: Нет
// OUTPUTS: std::string - версия
// KEYWORDS: PATTERN(6): VersionGet; DOMAIN(5): Metadata; TECH(4): Getter
// END_CONTRACT
std::string WalletTransactionFactory::getVersion() {
    return "1.0.0";
}
// END_FUNCTION_Factory_GetVersion

} // namespace wallet_tx
