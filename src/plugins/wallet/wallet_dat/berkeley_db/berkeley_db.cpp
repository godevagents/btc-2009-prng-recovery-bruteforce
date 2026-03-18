#include "berkeley_db.h"
#include <iostream>
#include <sstream>
#include <iomanip>
#include <ctime>
#include <sys/stat.h>
#include <algorithm>

namespace berkeley_db {

// Константы для логирования
static const std::string LOG_FILE = "berkeley_db.log";

// START_FUNCTION_BerkeleyDBWriter_Constructor
// START_CONTRACT:
// PURPOSE: Конструктор по умолчанию, инициализирует все внутренние состояния
// INPUTS: Нет
// OUTPUTS: Нет
// KEYWORDS: PATTERN(6): Constructor; DOMAIN(9): BerkeleyDB; TECH(5): Init
// END_CONTRACT
BerkeleyDBWriter::BerkeleyDBWriter()
    : file_stream_(nullptr),
      db_path_(""),
      flags_(0),
      is_open_(false),
      is_dirty_(false) {
    logToFile("[BerkeleyDBWriter] Конструктор вызван");
}
// END_FUNCTION_BerkeleyDBWriter_Constructor

// START_FUNCTION_BerkeleyDBWriter_Destructor
// START_CONTRACT:
// PURPOSE: Деструктор, закрывает базу данных если она открыта
// INPUTS: Нет
// OUTPUTS: Нет
// KEYWORDS: PATTERN(6): Destructor; DOMAIN(9): BerkeleyDB; TECH(5): Cleanup
// END_CONTRACT
BerkeleyDBWriter::~BerkeleyDBWriter() {
    if (is_open_) {
        close();
    }
    logToFile("[BerkeleyDBWriter] Деструктор вызван");
}
// END_FUNCTION_BerkeleyDBWriter_Destructor

// START_FUNCTION_open
// START_CONTRACT:
// PURPOSE: Открытие базы данных Berkeley DB
// INPUTS:
// - const std::string& path - путь к файлу базы данных
// - int flags - флаги открытия (комбинация OpenFlags)
// OUTPUTS: bool - результат открытия
// KEYWORDS: PATTERN(8): DatabaseOpen; DOMAIN(9): BerkeleyDB; TECH(7): FileIO
// END_CONTRACT
bool BerkeleyDBWriter::open(const std::string& path, int flags) {
    std::ostringstream oss;
    oss << "[open] Открытие базы данных: " << path << " с флагами: " << flags;
    logToFile(oss.str());
    
    if (path.empty()) {
        logToFile("[open] ОШИБКА: Путь к базе данных пуст");
        return false;
    }
    
    db_path_ = path;
    flags_ = flags;
    
    // Определяем режим открытия файла
    std::ios_base::openmode mode = std::ios::binary;
    
    bool create_new = (flags & static_cast<int>(OpenFlags::CREATE)) != 0;
    bool read_only = (flags & static_cast<int>(OpenFlags::READ_ONLY)) != 0;
    bool truncate = (flags & static_cast<int>(OpenFlags::TRUNCATE)) != 0;
    
    if (read_only) {
        mode |= std::ios::in;
    } else {
        mode |= std::ios::in | std::ios::out;
    }
    
    if (truncate || (create_new && !read_only)) {
        mode |= std::ios::trunc;
    }
    
    // Проверяем существование файла если открываем только для чтения
    if (read_only) {
        struct stat info;
        if (stat(path.c_str(), &info) != 0) {
            oss.str("");
            oss << "[open] ОШИБКА: Файл не существует: " << path;
            logToFile(oss.str());
            return false;
        }
    }
    
    // Открываем файл
    file_stream_ = std::make_unique<std::fstream>(path, mode);
    
    if (!file_stream_->is_open()) {
        oss.str("");
        oss << "[open] ОШИБКА: Не удалось открыть файл: " << path;
        logToFile(oss.str());
        return false;
    }
    
    // Если файл не пустой и не truncаем, читаем существующие записи
    if (!truncate && file_stream_->tellg() > 0) {
        file_stream_->seekg(0, std::ios::beg);
        if (!readRecordsFromFile()) {
            logToFile("[open] ПРЕДУПРЕЖДЕНИЕ: Не удалось прочитать существующие записи");
            records_.clear();
        }
    }
    
    is_open_ = true;
    is_dirty_ = false;
    
    oss.str("");
    oss << "[open] База данных успешно открыта. Записей в памяти: " << records_.size();
    logToFile(oss.str());
    
    return true;
}
// END_FUNCTION_open

// START_FUNCTION_put
// START_CONTRACT:
// PURPOSE: Запись записи в базу данных
// INPUTS:
// - const std::vector<unsigned char>& key - ключ записи
// - const std::vector<unsigned char>& value - значение записи
// OUTPUTS: DbResult - результат операции
// KEYWORDS: PATTERN(7): RecordWrite; DOMAIN(9): KeyValueStore; TECH(6): Serialization
// END_CONTRACT
DbResult BerkeleyDBWriter::put(const std::vector<unsigned char>& key, const std::vector<unsigned char>& value) {
    std::ostringstream oss;
    oss << "[put] Запись ключа размером: " << key.size() << " байт, значение: " << value.size() << " байт";
    logToFile(oss.str());
    
    if (!is_open_) {
        logToFile("[put] ОШИБКА: База данных не открыта");
        return DbResult::ERROR;
    }
    
    if (key.empty()) {
        logToFile("[put] ОШИБКА: Ключ пуст");
        return DbResult::ERROR;
    }
    
    bool key_exists = records_.find(key) != records_.end();
    
    // Записываем в map (B-Tree эмуляция через отсортированный map)
    records_[key] = value;
    is_dirty_ = true;
    
    // Если открыт поток, записываем сразу в файл
    if (file_stream_ && !(flags_ & static_cast<int>(OpenFlags::READ_ONLY))) {
        if (!writeRecordsToFile()) {
            logToFile("[put] ОШИБКА: Не удалось записать в файл");
            return DbResult::ERROR;
        }
    }
    
    return key_exists ? DbResult::KEY_EXIST : DbResult::SUCCESS;
}
// END_FUNCTION_put

// START_FUNCTION_get
// START_CONTRACT:
// PURPOSE: Чтение записи из базы данных
// INPUTS:
// - const std::vector<unsigned char>& key - ключ записи
// OUTPUTS: std::optional<std::vector<unsigned char>> - значение или пустое если не найдено
// KEYWORDS: PATTERN(7): RecordRead; DOMAIN(9): KeyValueStore; TECH(7): Deserialization
// END_CONTRACT
std::optional<std::vector<unsigned char>> BerkeleyDBWriter::get(const std::vector<unsigned char>& key) {
    std::ostringstream oss;
    oss << "[get] Чтение ключа размером: " << key.size() << " байт";
    logToFile(oss.str());
    
    if (!is_open_) {
        logToFile("[get] ОШИБКА: База данных не открыта");
        return std::nullopt;
    }
    
    auto it = records_.find(key);
    
    if (it == records_.end()) {
        logToFile("[get] Ключ не найден");
        return std::nullopt;
    }
    
    logToFile("[get] Ключ найден");
    return it->second;
}
// END_FUNCTION_get

// START_FUNCTION_del
// START_CONTRACT:
// PURPOSE: Удаление записи из базы данных
// INPUTS:
// - const std::vector<unsigned char>& key - ключ записи
// OUTPUTS: DbResult - результат операции
// KEYWORDS: PATTERN(7): RecordDelete; DOMAIN(9): KeyValueStore; TECH(5): Removal
// END_CONTRACT
DbResult BerkeleyDBWriter::del(const std::vector<unsigned char>& key) {
    std::ostringstream oss;
    oss << "[del] Удаление ключа размером: " << key.size() << " байт";
    logToFile(oss.str());
    
    if (!is_open_) {
        logToFile("[del] ОШИБКА: База данных не открыта");
        return DbResult::ERROR;
    }
    
    auto it = records_.find(key);
    
    if (it == records_.end()) {
        logToFile("[del] Ключ не найден");
        return DbResult::NOT_FOUND;
    }
    
    records_.erase(it);
    is_dirty_ = true;
    
    // Перезаписываем файл
    if (file_stream_ && !(flags_ & static_cast<int>(OpenFlags::READ_ONLY))) {
        if (!writeRecordsToFile()) {
            logToFile("[del] ОШИБКА: Не удалось записать в файл");
            return DbResult::ERROR;
        }
    }
    
    logToFile("[del] Ключ успешно удален");
    return DbResult::SUCCESS;
}
// END_FUNCTION_del

// START_FUNCTION_close
// START_CONTRACT:
// PURPOSE: Закрытие базы данных и освобождение ресурсов
// INPUTS: Нет
// OUTPUTS: bool - результат закрытия
// KEYWORDS: PATTERN(6): DatabaseClose; DOMAIN(7): Cleanup; TECH(5): Resource
// END_CONTRACT
bool BerkeleyDBWriter::close() {
    logToFile("[close] Закрытие базы данных");
    
    if (!is_open_) {
        logToFile("[close] База данных уже закрыта");
        return true;
    }
    
    // Записываем все изменения в файл если есть права на запись
    if (is_dirty_ && file_stream_ && !(flags_ & static_cast<int>(OpenFlags::READ_ONLY))) {
        if (!writeRecordsToFile()) {
            logToFile("[close] ОШИБКА: Не удалось записать изменения в файл");
        }
        file_stream_->flush();
    }
    
    // Закрываем файл
    if (file_stream_) {
        if (file_stream_->is_open()) {
            file_stream_->close();
        }
        file_stream_.reset();
    }
    
    // Очищаем карту записей
    records_.clear();
    
    is_open_ = false;
    is_dirty_ = false;
    
    logToFile("[close] База данных закрыта");
    return true;
}
// END_FUNCTION_close

// START_FUNCTION_writeVersion
// START_CONTRACT:
// PURPOSE: Запись версии базы данных
// INPUTS: int version - номер версии
// OUTPUTS: bool - результат записи
// KEYWORDS: PATTERN(7): VersionWrite; DOMAIN(8): Metadata; TECH(6): Serialization
// END_CONTRACT
bool BerkeleyDBWriter::writeVersion(int version) {
    std::ostringstream oss;
    oss << "[writeVersion] Запись версии: " << version;
    logToFile(oss.str());
    
    // Сериализуем строку "version"
    std::vector<unsigned char> key_data;
    std::string version_key = "version";
    key_data.insert(key_data.end(), version_key.begin(), version_key.end());
    
    // Сериализуем значение версии
    std::vector<unsigned char> value_data = serializeInt(version);
    
    DbResult result = put(key_data, value_data);
    
    if (result == DbResult::ERROR) {
        logToFile("[writeVersion] ОШИБКА записи версии");
        return false;
    }
    
    logToFile("[writeVersion] Версия успешно записана");
    return true;
}
// END_FUNCTION_writeVersion

// START_FUNCTION_writeDefaultKey
// START_CONTRACT:
// PURPOSE: Запись ключа по умолчанию
// INPUTS: const std::vector<unsigned char>& pubkey - публичный ключ
// OUTPUTS: bool - результат записи
// KEYWORDS: PATTERN(8): DefaultKeyWrite; DOMAIN(8): Bitcoin; TECH(6): KeyStorage
// END_CONTRACT
bool BerkeleyDBWriter::writeDefaultKey(const std::vector<unsigned char>& pubkey) {
    std::ostringstream oss;
    oss << "[writeDefaultKey] Запись default key размером: " << pubkey.size() << " байт";
    logToFile(oss.str());
    
    // Сериализуем строку "defaultkey"
    std::vector<unsigned char> key_data;
    std::string defaultkey_str = "defaultkey";
    key_data.insert(key_data.end(), defaultkey_str.begin(), defaultkey_str.end());
    
    DbResult result = put(key_data, pubkey);
    
    if (result == DbResult::ERROR) {
        logToFile("[writeDefaultKey] ОШИБКА записи default key");
        return false;
    }
    
    logToFile("[writeDefaultKey] Default key успешно записан");
    return true;
}
// END_FUNCTION_writeDefaultKey

// START_FUNCTION_writeKeyPair
// START_CONTRACT:
// PURPOSE: Запись ключевой пары (публичный/приватный ключ)
// INPUTS:
// - const std::vector<unsigned char>& pubkey - публичный ключ
// - const std::vector<unsigned char>& privkey - приватный ключ
// OUTPUTS: bool - результат записи
// KEYWORDS: PATTERN(7): KeyPairWrite; DOMAIN(8): PrivateKey; TECH(6): ECDSA
// END_CONTRACT
bool BerkeleyDBWriter::writeKeyPair(const std::vector<unsigned char>& pubkey, 
                                     const std::vector<unsigned char>& privkey) {
    std::ostringstream oss;
    oss << "[writeKeyPair] Запись ключевой пары. Pubkey: " << pubkey.size() 
       << " байт, Privkey: " << privkey.size() << " байт";
    logToFile(oss.str());
    
    // Формат ключа: "key" + pubkey
    std::vector<unsigned char> key_data;
    std::string key_str = "key";
    key_data.insert(key_data.end(), key_str.begin(), key_str.end());
    key_data.insert(key_data.end(), pubkey.begin(), pubkey.end());
    
    DbResult result = put(key_data, privkey);
    
    if (result == DbResult::ERROR) {
        logToFile("[writeKeyPair] ОШИБКА записи ключевой пары");
        return false;
    }
    
    logToFile("[writeKeyPair] Ключевая пара успешно записана");
    return true;
}
// END_FUNCTION_writeKeyPair

// START_FUNCTION_writeTx
// START_CONTRACT:
// PURPOSE: Запись транзакции кошелька
// INPUTS:
// - const std::vector<unsigned char>& txHash - хэш транзакции
// - const std::vector<unsigned char>& txData - данные транзакции
// OUTPUTS: bool - результат записи
// KEYWORDS: PATTERN(6): TxWrite; DOMAIN(8): Transaction; TECH(5): DB
// END_CONTRACT
bool BerkeleyDBWriter::writeTx(const std::vector<unsigned char>& txHash, 
                                const std::vector<unsigned char>& txData) {
    std::ostringstream oss;
    oss << "[writeTx] Запись транзакции. Hash: " << txHash.size() 
       << " байт, Data: " << txData.size() << " байт";
    logToFile(oss.str());
    
    // Формат ключа: "tx" + txHash
    std::vector<unsigned char> key_data;
    std::string tx_str = "tx";
    key_data.insert(key_data.end(), tx_str.begin(), tx_str.end());
    key_data.insert(key_data.end(), txHash.begin(), txHash.end());
    
    DbResult result = put(key_data, txData);
    
    if (result == DbResult::ERROR) {
        logToFile("[writeTx] ОШИБКА записи транзакции");
        return false;
    }
    
    logToFile("[writeTx] Транзакция успешно записана");
    return true;
}
// END_FUNCTION_writeTx

// START_FUNCTION_writeSetting
// START_CONTRACT:
// PURPOSE: Запись настройки кошелька
// INPUTS:
// - const std::string& settingKey - имя настройки
// - const std::vector<unsigned char>& value - значение настройки
// OUTPUTS: bool - результат записи
// KEYWORDS: PATTERN(7): SettingWrite; DOMAIN(7): Config; TECH(5): DB
// END_CONTRACT
bool BerkeleyDBWriter::writeSetting(const std::string& settingKey, 
                                     const std::vector<unsigned char>& value) {
    std::ostringstream oss;
    oss << "[writeSetting] Запись настройки: " << settingKey << " (размер: " << value.size() << " байт)";
    logToFile(oss.str());
    
    // Формат ключа: "setting" + settingKey
    std::vector<unsigned char> key_data;
    std::string setting_str = "setting";
    key_data.insert(key_data.end(), setting_str.begin(), setting_str.end());
    key_data.insert(key_data.end(), settingKey.begin(), settingKey.end());
    
    DbResult result = put(key_data, value);
    
    if (result == DbResult::ERROR) {
        logToFile("[writeSetting] ОШИБКА записи настройки");
        return false;
    }
    
    logToFile("[writeSetting] Настройка успешно записана");
    return true;
}
// END_FUNCTION_writeSetting

// START_FUNCTION_writeName
// START_CONTRACT:
// PURPOSE: Запись адресной книги (имя/адрес)
// INPUTS:
// - const std::string& address - Bitcoin адрес
// - const std::string& name - имя
// OUTPUTS: bool - результат записи
// KEYWORDS: PATTERN(8): AddressBookWrite; DOMAIN(7): Contacts; TECH(5): DB
// END_CONTRACT
bool BerkeleyDBWriter::writeName(const std::string& address, const std::string& name) {
    std::ostringstream oss;
    oss << "[writeName] Запись адресной книги. Адрес: " << address << ", Имя: " << name;
    logToFile(oss.str());
    
    // Формат ключа: "name" + address
    std::vector<unsigned char> key_data;
    std::string name_str = "name";
    key_data.insert(key_data.end(), name_str.begin(), name_str.end());
    key_data.insert(key_data.end(), address.begin(), address.end());
    
    // Сериализуем значение (имя)
    std::vector<unsigned char> value_data;
    value_data.insert(value_data.end(), name.begin(), name.end());
    
    DbResult result = put(key_data, value_data);
    
    if (result == DbResult::ERROR) {
        logToFile("[writeName] ОШИБКА записи адресной книги");
        return false;
    }
    
    logToFile("[writeName] Адресная книга успешно записана");
    return true;
}
// END_FUNCTION_writeName

// START_FUNCTION_exists
// START_CONTRACT:
// PURPOSE: Проверка существования ключа
// INPUTS: const std::vector<unsigned char>& key - ключ записи
// OUTPUTS: bool - true если ключ существует
// KEYWORDS: PATTERN(7): KeyExists; DOMAIN(9): KeyValueStore; TECH(5): Check
// END_CONTRACT
bool BerkeleyDBWriter::exists(const std::vector<unsigned char>& key) {
    if (!is_open_) {
        return false;
    }
    return records_.find(key) != records_.end();
}
// END_FUNCTION_exists

// START_FUNCTION_flush
// START_CONTRACT:
// PURPOSE: Принудительная запись данных на диск
// INPUTS: Нет
// OUTPUTS: bool - результат операции
// KEYWORDS: PATTERN(6): DataFlush; DOMAIN(7): Persistence; TECH(5): Sync
// END_CONTRACT
bool BerkeleyDBWriter::flush() {
    logToFile("[flush] Сброс данных на диск");
    
    if (!is_open_ || !file_stream_) {
        logToFile("[flush] ОШИБКА: База данных не открыта");
        return false;
    }
    
    if (records_.empty()) {
        logToFile("[flush] Записей нет, создаем пустой файл");
        // Создаем пустой файл
        std::vector<unsigned char> empty_data;
        // Пишем пустой B-Tree заголовок
        empty_data.insert(empty_data.end(), {0x00, 0x00, 0x00, 0x00}); // magic
        empty_data.insert(empty_data.end(), {0x00, 0x00, 0x00, 0x00}); // version
        // Записываем количество записей = 0
        std::vector<unsigned char> count_bytes = serializeInt(0);
        empty_data.insert(empty_data.end(), count_bytes.begin(), count_bytes.end());
        
        file_stream_->seekp(0, std::ios::beg);
        file_stream_->write(reinterpret_cast<const char*>(empty_data.data()), empty_data.size());
        file_stream_->flush();
        
        is_dirty_ = false;
        return true;
    }
    
    if (!writeRecordsToFile()) {
        logToFile("[flush] ОШИБКА записи данных");
        return false;
    }
    
    file_stream_->flush();
    is_dirty_ = false;
    
    logToFile("[flush] Данные успешно сброшены на диск");
    return true;
}
// END_FUNCTION_flush

// START_FUNCTION_getFileSize
// START_CONTRACT:
// PURPOSE: Получение размера файла базы данных
// INPUTS: Нет
// OUTPUTS: size_t - размер файла в байтах
// KEYWORDS: PATTERN(6): FileSize; DOMAIN(6): Metadata; TECH(4): Getter
// END_CONTRACT
size_t BerkeleyDBWriter::getFileSize() const {
    if (!file_stream_ || !file_stream_->is_open()) {
        return 0;
    }
    
    auto current_pos = file_stream_->tellg();
    file_stream_->seekg(0, std::ios::end);
    auto size = file_stream_->tellg();
    file_stream_->seekg(current_pos);
    
    return static_cast<size_t>(size);
}
// END_FUNCTION_getFileSize

// START_FUNCTION_isOpen
// START_CONTRACT:
// PURPOSE: Проверка состояния базы данных
// INPUTS: Нет
// OUTPUTS: bool - true если база данных открыта
// KEYWORDS: PATTERN(5): StateCheck; DOMAIN(5): Status; TECH(4): Getter
// END_CONTRACT
bool BerkeleyDBWriter::isOpen() const {
    return is_open_;
}

// START_METHOD_getAllRecords
// START_CONTRACT:
// PURPOSE: Получение всех записей из базы данных
// INPUTS: Нет
// OUTPUTS: std::map<std::vector<unsigned char>, std::vector<unsigned char>> - все записи (ключ-значение)
// KEYWORDS: PATTERN(9): GetAllRecords; DOMAIN(9): KeyValueStore; TECH(6): Retrieval
// END_CONTRACT
std::map<std::vector<unsigned char>, std::vector<unsigned char>, std::less<>> BerkeleyDBWriter::getAllRecords() {
    std::map<std::vector<unsigned char>, std::vector<unsigned char>, std::less<>> result;
    
    // Если база данных не открыта, возвращаем пустой результат
    if (!is_open_) {
        logToFile("[getAllRecords] Database is not open, returning empty result");
        return result;
    }
    
    // Если записей нет в памяти, пробуем прочитать из файла
    if (records_.empty()) {
        logToFile("[getAllRecords] No records in memory, reading from file");
        if (!readRecordsFromFile()) {
            logToFile("[getAllRecords] Failed to read records from file");
            return result;
        }
    }
    
    // Возвращаем все записи
    return records_;
}
// END_FUNCTION_isOpen

// START_FUNCTION_serializeRecord
// START_CONTRACT:
// PURPOSE: Сериализация записи в бинарный формат Berkeley DB
// INPUTS: const Record& record - запись для сериализации
// OUTPUTS: std::vector<unsigned char> - сериализованные данные
// KEYWORDS: PATTERN(8): RecordSerialization; DOMAIN(7): Serialization; TECH(6): Binary
// END_CONTRACT
std::vector<unsigned char> BerkeleyDBWriter::serializeRecord(const Record& record) const {
    std::vector<unsigned char> result;
    
    // Формат: varint(key_len) + key_data + varint(value_len) + value_data
    
    // Ключ
    std::vector<unsigned char> key_len = encodeVarint(record.key.size());
    result.insert(result.end(), key_len.begin(), key_len.end());
    result.insert(result.end(), record.key.begin(), record.key.end());
    
    // Значение
    std::vector<unsigned char> value_len = encodeVarint(record.value.size());
    result.insert(result.end(), value_len.begin(), value_len.end());
    result.insert(result.end(), record.value.begin(), record.value.end());
    
    return result;
}
// END_FUNCTION_serializeRecord

// START_FUNCTION_deserializeRecord
// START_CONTRACT:
// PURPOSE: Десериализация записи из бинарного формата Berkeley DB
// INPUTS: const std::vector<unsigned char>& data - сериализованные данные
// OUTPUTS: Record - десериализованная запись
// KEYWORDS: PATTERN(8): RecordDeserialization; DOMAIN(7): Deserialization; TECH(6): Binary
// END_CONTRACT
BerkeleyDBWriter::Record BerkeleyDBWriter::deserializeRecord(const std::vector<unsigned char>& data) const {
    Record record;
    
    if (data.empty()) {
        return record;
    }
    
    size_t pos = 0;
    
    // Читаем длину ключа
    uint64_t key_len = decodeVarint(data, pos);
    
    if (pos + key_len > data.size()) {
        logToFile("[deserializeRecord] ОШИБКА: Недостаточно данных для ключа");
        return record;
    }
    
    // Читаем ключ
    record.key.assign(data.begin() + pos, data.begin() + pos + key_len);
    pos += key_len;
    
    // Читаем длину значения
    if (pos >= data.size()) {
        logToFile("[deserializeRecord] ОШИБКА: Недостаточно данных для длины значения");
        return record;
    }
    
    uint64_t value_len = decodeVarint(data, pos);
    
    if (pos + value_len > data.size()) {
        logToFile("[deserializeRecord] ОШИБКА: Недостаточно данных для значения");
        return record;
    }
    
    // Читаем значение
    record.value.assign(data.begin() + pos, data.begin() + pos + value_len);
    
    return record;
}
// END_FUNCTION_deserializeRecord

// START_FUNCTION_encodeVarint
// START_CONTRACT:
// PURPOSE: Кодирование числа в формат Bitcoin Varint
// INPUTS: uint64_t value - число для кодирования
// OUTPUTS: std::vector<unsigned char> - закодированное значение
// KEYWORDS: PATTERN(8): VarintEncode; DOMAIN(7): Serialization; TECH(6): Bitcoin
// END_CONTRACT
std::vector<unsigned char> BerkeleyDBWriter::encodeVarint(uint64_t value) const {
    std::vector<unsigned char> result;
    
    // Varint кодирование для Bitcoin
    // 0-127: 1 байт
    // 128-16383: 2 байта
    // 16384-2097151: 3 байта
    // и т.д.
    
    while (value >= 0x80) {
        // Записываем байт с установленным старшим битом (continue bit)
        result.push_back(static_cast<unsigned char>((value & 0x7F) | 0x80));
        value >>= 7;
    }
    
    // Записываем последний байт без continue bit
    result.push_back(static_cast<unsigned char>(value & 0x7F));
    
    return result;
}
// END_FUNCTION_encodeVarint

// START_FUNCTION_decodeVarint
// START_CONTRACT:
// PURPOSE: Декодирование числа из формата Bitcoin Varint
// INPUTS: 
// - const std::vector<unsigned char>& data - закодированные данные
// - size_t& pos - позиция начала чтения (изменяется при чтении)
// OUTPUTS: uint64_t - декодированное значение
// KEYWORDS: PATTERN(8): VarintDecode; DOMAIN(7): Deserialization; TECH(6): Bitcoin
// END_CONTRACT
uint64_t BerkeleyDBWriter::decodeVarint(const std::vector<unsigned char>& data, size_t& pos) const {
    uint64_t result = 0;
    int shift = 0;
    
    while (pos < data.size()) {
        unsigned char byte = data[pos];
        pos++;
        
        result |= static_cast<uint64_t>(byte & 0x7F) << shift;
        
        // Если старший бит не установлен, это последний байт
        if ((byte & 0x80) == 0) {
            break;
        }
        
        shift += 7;
        
        // Защита от бесконечного цикла
        if (shift > 63) {
            break;
        }
    }
    
    return result;
}
// END_FUNCTION_decodeVarint

// START_FUNCTION_serializeInt
// START_CONTRACT:
// PURPOSE: Сериализация целого числа в little-endian формат
// INPUTS: int value - число для сериализации
// OUTPUTS: std::vector<unsigned char> - сериализованные данные (4 байта)
// KEYWORDS: PATTERN(7): IntSerialization; DOMAIN(6): Integer; TECH(5): LittleEndian
// END_CONTRACT
std::vector<unsigned char> BerkeleyDBWriter::serializeInt(int value) const {
    std::vector<unsigned char> result(4);
    result[0] = static_cast<unsigned char>(value & 0xFF);
    result[1] = static_cast<unsigned char>((value >> 8) & 0xFF);
    result[2] = static_cast<unsigned char>((value >> 16) & 0xFF);
    result[3] = static_cast<unsigned char>((value >> 24) & 0xFF);
    return result;
}
// END_FUNCTION_serializeInt

// START_FUNCTION_deserializeInt
// START_CONTRACT:
// PURPOSE: Десериализация целого числа из little-endian формата
// INPUTS: 
// - const std::vector<unsigned char>& data - сериализованные данные
// - size_t& pos - позиция начала чтения (изменяется при чтении)
// OUTPUTS: int - десериализованное значение
// KEYWORDS: PATTERN(8): IntDeserialization; DOMAIN(6): Integer; TECH(5): LittleEndian
// END_CONTRACT
int BerkeleyDBWriter::deserializeInt(const std::vector<unsigned char>& data, size_t& pos) const {
    if (pos + 4 > data.size()) {
        return 0;
    }
    
    int result = 0;
    result |= static_cast<int>(data[pos]);
    result |= static_cast<int>(data[pos + 1]) << 8;
    result |= static_cast<int>(data[pos + 2]) << 16;
    result |= static_cast<int>(data[pos + 3]) << 24;
    pos += 4;
    
    return result;
}
// END_FUNCTION_deserializeInt

// START_FUNCTION_serializeString
// START_CONTRACT:
// PURPOSE: Сериализация строки с varint префиксом длины
// INPUTS: const std::string& str - строка для сериализации
// OUTPUTS: std::vector<unsigned char> - сериализованные данные
// KEYWORDS: PATTERN(7): StringSerialization; DOMAIN(6): String; TECH(5): VarInt
// END_CONTRACT
std::vector<unsigned char> BerkeleyDBWriter::serializeString(const std::string& str) const {
    std::vector<unsigned char> result;
    // Добавляем varint длину
    std::vector<unsigned char> len_prefix = encodeVarint(str.size());
    result.insert(result.end(), len_prefix.begin(), len_prefix.end());
    // Добавляем данные
    result.insert(result.end(), str.begin(), str.end());
    return result;
}
// END_FUNCTION_serializeString

// START_FUNCTION_writeRecordsToFile
// START_CONTRACT:
// PURPOSE: Запись всех записей в файл в формате BDB B-Tree
// INPUTS: Нет
// OUTPUTS: bool - результат записи
// KEYWORDS: PATTERN(8): BTreeWrite; DOMAIN(9): IndexStructure; TECH(6): FileIO
// END_CONTRACT
bool BerkeleyDBWriter::writeRecordsToFile() {
    if (!file_stream_ || !file_stream_->is_open()) {
        logToFile("[writeRecordsToFile] ОШИБКА: Файл не открыт");
        return false;
    }
    
    std::ostringstream oss;
    oss << "[writeRecordsToFile] Запись " << records_.size() << " записей в файл (формат BDB)";
    logToFile(oss.str());
    
    // Используем новый формат BDB страниц
    return writeBTreePages();
}
// END_FUNCTION_writeRecordsToFile

// START_FUNCTION_writeBTreePages
// START_CONTRACT:
// PURPOSE: Запись данных в формате B-Tree страниц Berkeley DB
// INPUTS: Нет
// OUTPUTS: bool - результат записи
// KEYWORDS: PATTERN(8): BTreePageWrite; DOMAIN(9): BerkeleyDB; TECH(6): FileIO
// END_CONTRACT
bool BerkeleyDBWriter::writeBTreePages() {
    if (!file_stream_ || !file_stream_->is_open()) {
        logToFile("[writeBTreePages] ОШИБКА: Файл не открыт");
        return false;
    }
    
    std::ostringstream oss;
    oss << "[writeBTreePages] Запись " << records_.size() << " записей в формате BDB страниц";
    logToFile(oss.str());
    
    // Создаем бинарные данные
    std::vector<unsigned char> file_data;
    
    // Если записей нет, создаем пустой файл с метастраницей
    if (records_.empty()) {
        // Создаем метастраницу с корнем = 0 (нет данных)
        std::vector<unsigned char> meta_page = createBTreeMetaPage(0);
        file_data.insert(file_data.end(), meta_page.begin(), meta_page.end());
        
        // Записываем в файл
        file_stream_->seekp(0, std::ios::beg);
        file_stream_->write(reinterpret_cast<const char*>(file_data.data()), file_data.size());
        
        oss.str("");
        oss << "[writeBTreePages] Успешно записано " << file_data.size() << " байт (пустая БД)";
        logToFile(oss.str());
        
        return true;
    }
    
    // Создаем вектор записей из map
    std::vector<Record> record_vec;
    for (const auto& pair : records_) {
        Record rec;
        rec.key = pair.first;
        rec.value = pair.second;
        record_vec.push_back(rec);
    }
    
    // Создаем leaf страницу с данными
    std::vector<unsigned char> leaf_page = createLeafPage(record_vec);
    
    // Корневая страница - это leaf страница (номер 1)
    uint32_t root_page_num = 1;
    
    // Создаем метастраницу
    std::vector<unsigned char> meta_page = createBTreeMetaPage(root_page_num);
    
    // Собираем файл: метастраница + leaf страница
    file_data.insert(file_data.end(), meta_page.begin(), meta_page.end());
    file_data.insert(file_data.end(), leaf_page.begin(), leaf_page.end());
    
    // Записываем в файл
    file_stream_->seekp(0, std::ios::beg);
    file_stream_->write(reinterpret_cast<const char*>(file_data.data()), file_data.size());
    
    oss.str("");
    oss << "[writeBTreePages] Успешно записано " << file_data.size() << " байт";
    logToFile(oss.str());
    
    return true;
}
// END_FUNCTION_writeBTreePages

// START_FUNCTION_createBTreeMetaPage
// START_CONTRACT:
// PURPOSE: Создание метастраницы B-Tree Berkeley DB
// INPUTS: uint32_t rootPageNum - номер корневой страницы
// OUTPUTS: std::vector<unsigned char> - данные метастраницы
// KEYWORDS: PATTERN(7): MetaPageCreate; DOMAIN(9): BerkeleyDB; TECH(5): Format
// END_CONTRACT
std::vector<unsigned char> BerkeleyDBWriter::createBTreeMetaPage(uint32_t rootPageNum) const {
    std::vector<unsigned char> page(BDB_PAGE_SIZE, 0);
    
    // Смещение 0: magic number (4 байта, little-endian) - 0x00053161
    page[0] = 0x61;
    page[1] = 0x31;
    page[2] = 0x05;
    page[3] = 0x00;
    
    // Смещение 4: version (2 байта, little-endian) - 9
    page[4] = 0x09;
    page[5] = 0x00;
    
    // Смещение 6: page type (1 байт) - 0x0d = meta page
    page[6] = 0x0d;
    
    // Смещение 7: unused (1 байт)
    page[7] = 0x00;
    
    // Смещение 8: root page number (4 байта, little-endian)
    page[8] = static_cast<unsigned char>(rootPageNum & 0xFF);
    page[9] = static_cast<unsigned char>((rootPageNum >> 8) & 0xFF);
    page[10] = static_cast<unsigned char>((rootPageNum >> 16) & 0xFF);
    page[11] = static_cast<unsigned char>((rootPageNum >> 24) & 0xFF);
    
    // Смещение 12: free page list (4 байта) - 0 (нет свободных страниц)
    page[12] = 0x00;
    page[13] = 0x00;
    page[14] = 0x00;
    page[15] = 0x00;
    
    // Смещение 16: last page number (4 байта)
    uint32_t last_pgno = rootPageNum > 0 ? rootPageNum : 0;
    page[16] = static_cast<unsigned char>(last_pgno & 0xFF);
    page[17] = static_cast<unsigned char>((last_pgno >> 8) & 0xFF);
    page[18] = static_cast<unsigned char>((last_pgno >> 16) & 0xFF);
    page[19] = static_cast<unsigned char>((last_pgno >> 24) & 0xFF);
    
    // Смещение 20: free space offset (4 байта) - 1088 (начало данных в meta page)
    uint32_t hf_offset = 1088;
    page[20] = static_cast<unsigned char>(hf_offset & 0xFF);
    page[21] = static_cast<unsigned char>((hf_offset >> 8) & 0xFF);
    page[22] = static_cast<unsigned char>((hf_offset >> 16) & 0xFF);
    page[23] = static_cast<unsigned char>((hf_offset >> 24) & 0xFF);
    
    // Смещение 24-27: pattern (4 байта) - 0
    page[24] = 0x00;
    page[25] = 0x00;
    page[26] = 0x00;
    page[27] = 0x00;
    
    // Заполняем остаток страницы нулями (уже инициализировано)
    
    logToFile("[createBTreeMetaPage] Метастраница создана, root=" + std::to_string(rootPageNum));
    
    return page;
}
// END_FUNCTION_createBTreeMetaPage

// START_FUNCTION_createLeafPage
// START_CONTRACT:
// PURPOSE: Создание leaf страницы B-Tree с записями
// INPUTS: const std::vector<Record>& records - вектор записей
// OUTPUTS: std::vector<unsigned char> - данные leaf страницы
// KEYWORDS: PATTERN(7): LeafPageCreate; DOMAIN(9): BerkeleyDB; TECH(5): Format
// END_CONTRACT
std::vector<unsigned char> BerkeleyDBWriter::createLeafPage(const std::vector<Record>& records) const {
    // Начнем с базового размера страницы
    std::vector<unsigned char> page;
    page.reserve(BDB_PAGE_SIZE);
    
    // Создаем заголовок leaf страницы (28 байт)
    // Смещение 0-3: magic number
    page.push_back(0x61);
    page.push_back(0x31);
    page.push_back(0x05);
    page.push_back(0x00);
    
    // Смещение 4-5: version = 9
    page.push_back(0x09);
    page.push_back(0x00);
    
    // Смещение 6: page type = 0x0a (leaf)
    page.push_back(BDB_PAGE_TYPE_LEAF);
    
    // Смещение 7: свободное пространство (будет обновлено)
    uint8_t freespace_off_pos = 7;
    page.push_back(0x00); // placeholder
    
    // Смещение 8-11: количество записей
    uint32_t entry_count = static_cast<uint32_t>(records.size());
    page.push_back(static_cast<unsigned char>(entry_count & 0xFF));
    page.push_back(static_cast<unsigned char>((entry_count >> 8) & 0xFF));
    page.push_back(static_cast<unsigned char>((entry_count >> 16) & 0xFF));
    page.push_back(static_cast<unsigned char>((entry_count >> 24) & 0xFF));
    
    // Смещение 12-15: hf_offset (смещение до первой записи, пока 0)
    uint32_t hf_offset_pos = 12;
    page.push_back(0x00);
    page.push_back(0x00);
    page.push_back(0x00);
    page.push_back(0x00);
    
    // Смещение 16-19: level (0 для leaf)
    page.push_back(0x00);
    page.push_back(0x00);
    page.push_back(0x00);
    page.push_back(0x00);
    
    // Смещение 20-23: leaf_ptr (0)
    page.push_back(0x00);
    page.push_back(0x00);
    page.push_back(0x00);
    page.push_back(0x00);
    
    // Смещение 24-27: зарезервировано
    page.push_back(0x00);
    page.push_back(0x00);
    page.push_back(0x00);
    page.push_back(0x00);
    
    // Теперь сериализуем все записи
    // Каждая запись: key_len (varint) + key + value_len (varint) + value
    std::vector<std::vector<unsigned char>> serialized_records;
    size_t total_data_size = 0;
    
    for (const auto& rec : records) {
        std::vector<unsigned char> serialized = serializeKeyValue(rec.key, rec.value);
        serialized_records.push_back(serialized);
        total_data_size += serialized.size();
    }
    
    // Вычисляем свободное пространство
    // Page size - header(28) - data_size
    uint32_t freespace_offset = BDB_PAGE_SIZE - static_cast<uint32_t>(total_data_size);
    
    // Обновляем freespace_off в заголовке
    page[freespace_off_pos] = static_cast<unsigned char>(freespace_offset & 0xFF);
    
    // Обновляем hf_offset (смещение первой записи)
    uint32_t hf_offset = 28; // После заголовка
    page[hf_offset_pos] = static_cast<unsigned char>(hf_offset & 0xFF);
    page[hf_offset_pos + 1] = static_cast<unsigned char>((hf_offset >> 8) & 0xFF);
    page[hf_offset_pos + 2] = static_cast<unsigned char>((hf_offset >> 16) & 0xFF);
    page[hf_offset_pos + 3] = static_cast<unsigned char>((hf_offset >> 24) & 0xFF);
    
    // Добавляем все сериализованные записи
    for (const auto& serialized : serialized_records) {
        page.insert(page.end(), serialized.begin(), serialized.end());
    }
    
    // Дополняем до размера страницы нулями
    while (page.size() < BDB_PAGE_SIZE) {
        page.push_back(0x00);
    }
    
    std::ostringstream oss;
    oss << "[createLeafPage] Leaf страница создана, записей: " << records.size() 
        << ", размер данных: " << total_data_size;
    logToFile(oss.str());
    
    return page;
}
// END_FUNCTION_createLeafPage

// START_FUNCTION_encodeCompactSize
// START_CONTRACT:
// PURPOSE: Кодирование размера в формате CompactSize (CDataStream SER_DISK)
// INPUTS: uint64_t size - размер для кодирования
// OUTPUTS: std::vector<unsigned char> - закодированные данные
// KEYWORDS: PATTERN(9): CompactSize; DOMAIN(7): Serialization; TECH(5): Format
// END_CONTRACT
std::vector<unsigned char> BerkeleyDBWriter::encodeCompactSize(uint64_t size) const {
    std::vector<unsigned char> result;
    
    if (size < 253) {
        // 1 байт: само значение
        result.push_back(static_cast<unsigned char>(size));
    } else if (size <= 0xFFFF) {
        // 3 байта: 0xFD + 2 байта размер (little-endian)
        result.push_back(0xFD);
        result.push_back(static_cast<unsigned char>(size & 0xFF));
        result.push_back(static_cast<unsigned char>((size >> 8) & 0xFF));
    } else if (size <= 0xFFFFFFFF) {
        // 5 байт: 0xFE + 4 байта размер (little-endian)
        result.push_back(0xFE);
        result.push_back(static_cast<unsigned char>(size & 0xFF));
        result.push_back(static_cast<unsigned char>((size >> 8) & 0xFF));
        result.push_back(static_cast<unsigned char>((size >> 16) & 0xFF));
        result.push_back(static_cast<unsigned char>((size >> 24) & 0xFF));
    } else {
        // 9 байт: 0xFF + 8 байт размер (little-endian)
        result.push_back(0xFF);
        for (int i = 0; i < 8; i++) {
            result.push_back(static_cast<unsigned char>((size >> (i * 8)) & 0xFF));
        }
    }
    
    return result;
}
// END_FUNCTION_encodeCompactSize

// START_FUNCTION_serializeKeyValue
// START_CONTRACT:
// PURPOSE: Сериализация ключа/значения в CDataStream формат (SER_DISK)
// INPUTS: 
// - const std::vector<unsigned char>& key - ключ
// - const std::vector<unsigned char>& value - значение
// OUTPUTS: std::vector<unsigned char> - сериализованные данные
// KEYWORDS: PATTERN(8): CDataStream; DOMAIN(7): Serialization; TECH(6): Bitcoin
// END_CONTRACT
std::vector<unsigned char> BerkeleyDBWriter::serializeKeyValue(const std::vector<unsigned char>& key,
                                                              const std::vector<unsigned char>& value) const {
    std::vector<unsigned char> result;
    
    // CompactSize(key_len) + key_data
    std::vector<unsigned char> key_len = encodeCompactSize(key.size());
    result.insert(result.end(), key_len.begin(), key_len.end());
    result.insert(result.end(), key.begin(), key.end());
    
    // CompactSize(value_len) + value_data
    std::vector<unsigned char> value_len = encodeCompactSize(value.size());
    result.insert(result.end(), value_len.begin(), value_len.end());
    result.insert(result.end(), value.begin(), value.end());
    
    return result;
}
// END_FUNCTION_serializeKeyValue

// START_FUNCTION_readRecordsFromFile
// START_CONTRACT:
// PURPOSE: Чтение всех записей из файла (поддержка старого BTRE и нового BDB форматов)
// INPUTS: Нет
// OUTPUTS: bool - результат чтения
// KEYWORDS: PATTERN(8): BTreeRead; DOMAIN(9): IndexStructure; TECH(6): FileIO
// END_CONTRACT
bool BerkeleyDBWriter::readRecordsFromFile() {
    if (!file_stream_ || !file_stream_->is_open()) {
        logToFile("[readRecordsFromFile] ОШИБКА: Файл не открыт");
        return false;
    }
    
    logToFile("[readRecordsFromFile] Чтение записей из файла");
    
    // Читаем весь файл в память
    file_stream_->seekg(0, std::ios::end);
    std::streamsize file_size = file_stream_->tellg();
    file_stream_->seekg(0, std::ios::beg);
    
    if (file_size <= 0) {
        logToFile("[readRecordsFromFile] Файл пуст");
        return true;
    }
    
    std::vector<unsigned char> file_data(static_cast<size_t>(file_size));
    file_stream_->read(reinterpret_cast<char*>(file_data.data()), file_size);
    
    if (file_stream_->fail()) {
        logToFile("[readRecordsFromFile] ОШИБКА чтения файла");
        return false;
    }
    
    // Проверяем формат файла
    if (file_size >= 4) {
        // Проверяем BDB магическое число (0x00053161 = 0x61 0x31 0x05 0x00)
        bool is_bdb_format = (file_data[0] == 0x61 && file_data[1] == 0x31 && 
                             file_data[2] == 0x05 && file_data[3] == 0x00);
        
        // Проверяем старый формат BTRE
        bool is_btre_format = (file_data[0] == 0x42 && file_data[1] == 0x54 && 
                             file_data[2] == 0x52 && file_data[3] == 0x45);
        
        if (is_bdb_format) {
            logToFile("[readRecordsFromFile] Определен формат: Berkeley DB B-Tree");
            return readBDBFormat(file_data);
        } else if (is_btre_format) {
            logToFile("[readRecordsFromFile] Определен формат: BTRE (старый)");
            return readBTREFormat(file_data);
        } else {
            // Неизвестный формат - пробуем читать как поток записей
            logToFile("[readRecordsFromFile] Неизвестный формат, пробуем как поток записей");
            return readRawFormat(file_data);
        }
    }
    
    logToFile("[readRecordsFromFile] Файл слишком мал для определения формата");
    return false;
}
// END_FUNCTION_readRecordsFromFile

// START_HELPER_readBDBFormat
// START_CONTRACT:
// PURPOSE: Чтение данных из формата Berkeley DB B-Tree
// INPUTS: const std::vector<unsigned char>& file_data - данные файла
// OUTPUTS: bool - результат чтения
// KEYWORDS: PATTERN(8): BDBFormatRead; DOMAIN(9): BerkeleyDB; TECH(6): FileIO
// END_CONTRACT
bool BerkeleyDBWriter::readBDBFormat(const std::vector<unsigned char>& file_data) {
    if (file_data.size() < BDB_PAGE_SIZE) {
        logToFile("[readBDBFormat] ОШИБКА: Файл слишком мал для BDB");
        return false;
    }
    
    // Читаем meta page (страница 0)
    uint32_t root_page = file_data[8] | (file_data[9] << 8) | (file_data[10] << 16) | (file_data[11] << 24);
    
    std::ostringstream oss;
    oss << "[readBDBFormat] Root page: " << root_page << ", file size: " << file_data.size();
    logToFile(oss.str());
    
    // Если root = 0, база данных пустая
    if (root_page == 0) {
        records_.clear();
        logToFile("[readBDBFormat] База данных пустая");
        return true;
    }
    
    // Читаем leaf страницу (страница 1)
    if (file_data.size() < BDB_PAGE_SIZE * 2) {
        logToFile("[readBDBFormat] ОШИБКА: Файл слишком мал для leaf страницы");
        return false;
    }
    
    // Leaf страница начинается со смещения BDB_PAGE_SIZE
    size_t leaf_offset = BDB_PAGE_SIZE;
    
    // Проверяем, что это leaf страница
    if (file_data[leaf_offset + 6] != BDB_PAGE_TYPE_LEAF) {
        logToFile("[readBDBFormat] ОШИБКА: Неверный тип страницы");
        return false;
    }
    
    // Читаем количество записей (смещение 8)
    uint32_t entry_count = file_data[leaf_offset + 8] | 
                          (file_data[leaf_offset + 9] << 8) | 
                          (file_data[leaf_offset + 10] << 16) | 
                          (file_data[leaf_offset + 11] << 24);
    
    oss.str("");
    oss << "[readBDBFormat] Количество записей: " << entry_count;
    logToFile(oss.str());
    
    // Читаем записи из leaf страницы
    // Смещение данных: после заголовка страницы (28 байт)
    size_t data_offset = leaf_offset + 28;
    
    records_.clear();
    size_t pos = data_offset;
    
    for (uint32_t i = 0; i < entry_count && pos < file_data.size(); i++) {
        // Читаем длину ключа (CompactSize)
        if (pos >= file_data.size()) break;
        
        uint64_t key_len = decodeCompactSize(file_data, pos);
        
        if (pos + key_len > file_data.size()) break;
        
        // Читаем ключ
        std::vector<unsigned char> key(file_data.begin() + pos, file_data.begin() + pos + key_len);
        pos += key_len;
        
        // Читаем длину значения (CompactSize)
        if (pos >= file_data.size()) break;
        
        uint64_t value_len = decodeCompactSize(file_data, pos);
        
        if (pos + value_len > file_data.size()) break;
        
        // Читаем значение
        std::vector<unsigned char> value(file_data.begin() + pos, file_data.begin() + pos + value_len);
        pos += value_len;
        
        // Добавляем в map
        records_[key] = value;
    }
    
    oss.str("");
    oss << "[readBDBFormat] Успешно прочитано " << records_.size() << " записей";
    logToFile(oss.str());
    
    return true;
}
// END_HELPER_readBDBFormat

// START_HELPER_readBTREFormat
// START_CONTRACT:
// PURPOSE: Чтение данных из старого формата BTRE
// INPUTS: const std::vector<unsigned char>& file_data - данные файла
// OUTPUTS: bool - результат чтения
// KEYWORDS: PATTERN(8): BTREFormatRead; DOMAIN(9): BerkeleyDB; TECH(6): FileIO
// END_CONTRACT
bool BerkeleyDBWriter::readBTREFormat(const std::vector<unsigned char>& file_data) {
    size_t pos = 4; // пропускаем магическое число "BTRE"
    
    // Читаем версию
    int version = deserializeInt(file_data, pos);
    
    std::ostringstream oss;
    oss << "[readBTREFormat] Версия формата: " << version;
    logToFile(oss.str());
    
    // Читаем количество записей
    if (pos + 4 > file_data.size()) {
        logToFile("[readBTREFormat] ОШИБКА: Недостаточно данных для количества записей");
        return false;
    }
    
    int record_count = deserializeInt(file_data, pos);
    
    oss.str("");
    oss << "[readBTREFormat] Количество записей: " << record_count;
    logToFile(oss.str());
    
    // Читаем записи
    records_.clear();
    for (int i = 0; i < record_count; ++i) {
        if (pos >= file_data.size()) break;
        
        uint64_t key_len = decodeVarint(file_data, pos);
        
        if (pos + key_len > file_data.size()) break;
        
        std::vector<unsigned char> key(file_data.begin() + pos, file_data.begin() + pos + key_len);
        pos += key_len;
        
        if (pos >= file_data.size()) break;
        
        uint64_t value_len = decodeVarint(file_data, pos);
        
        if (pos + value_len > file_data.size()) break;
        
        std::vector<unsigned char> value(file_data.begin() + pos, file_data.begin() + pos + value_len);
        pos += value_len;
        
        records_[key] = value;
    }
    
    oss.str("");
    oss << "[readBTREFormat] Успешно прочитано " << records_.size() << " записей";
    logToFile(oss.str());
    
    return true;
}
// END_HELPER_readBTREFormat

// START_HELPER_readRawFormat
// START_CONTRACT:
// PURPOSE: Чтение данных из сырого потока записей
// INPUTS: const std::vector<unsigned char>& file_data - данные файла
// OUTPUTS: bool - результат чтения
// KEYWORDS: PATTERN(8): RawFormatRead; DOMAIN(7): Serialization; TECH(6): Stream
// END_CONTRACT
bool BerkeleyDBWriter::readRawFormat(const std::vector<unsigned char>& file_data) {
    logToFile("[readRawFormat] Чтение в сыром формате Berkeley DB");
    
    records_.clear();
    
    size_t pos = 0;
    
    while (pos < file_data.size()) {
        // Читаем длину ключа (CompactSize)
        if (pos >= file_data.size()) break;
        
        uint64_t key_len = decodeCompactSize(file_data, pos);
        
        if (key_len > 10000 || pos + key_len > file_data.size()) {
            logToFile("[readRawFormat] ОШИБКА: Слишком большая длина ключа");
            break;
        }
        
        // Читаем ключ
        std::vector<unsigned char> key(file_data.begin() + pos, file_data.begin() + pos + key_len);
        pos += key_len;
        
        // Читаем длину значения
        if (pos >= file_data.size()) break;
        
        uint64_t value_len = decodeCompactSize(file_data, pos);
        
        if (value_len > 1000000 || pos + value_len > file_data.size()) {
            logToFile("[readRawFormat] ОШИБКА: Слишком большая длина значения");
            break;
        }
        
        // Читаем значение
        std::vector<unsigned char> value(file_data.begin() + pos, file_data.begin() + pos + value_len);
        pos += value_len;
        
        records_[key] = value;
    }
    
    std::ostringstream oss;
    oss << "[readRawFormat] Успешно прочитано " << records_.size() << " записей";
    logToFile(oss.str());
    
    return true;
}
// END_HELPER_readRawFormat

// START_HELPER_decodeCompactSize
// START_CONTRACT:
// PURPOSE: Декодирование CompactSize из вектора байт
// INPUTS: 
// - const std::vector<unsigned char>& data - данные
// - size_t& pos - позиция чтения (изменяется)
// OUTPUTS: uint64_t - декодированное значение
// KEYWORDS: PATTERN(9): CompactSizeDecode; DOMAIN(7): Deserialization; TECH(5): Format
// END_CONTRACT
uint64_t BerkeleyDBWriter::decodeCompactSize(const std::vector<unsigned char>& data, size_t& pos) const {
    if (pos >= data.size()) {
        return 0;
    }
    
    unsigned char first = data[pos];
    pos++;
    
    if (first < 253) {
        return first;
    } else if (first == 253) {
        // 2 байта little-endian
        if (pos + 2 > data.size()) return 0;
        uint64_t val = data[pos] | (data[pos + 1] << 8);
        pos += 2;
        return val;
    } else if (first == 254) {
        // 4 байта little-endian
        if (pos + 4 > data.size()) return 0;
        uint64_t val = data[pos] | 
                      (data[pos + 1] << 8) | 
                      (data[pos + 2] << 16) | 
                      (data[pos + 3] << 24);
        pos += 4;
        return val;
    } else {
        // 8 байт little-endian
        if (pos + 8 > data.size()) return 0;
        uint64_t val = 0;
        for (int i = 0; i < 8; i++) {
            val |= (static_cast<uint64_t>(data[pos + i]) << (i * 8));
        }
        pos += 8;
        return val;
    }
}
// END_HELPER_decodeCompactSize

// START_HELPER_decodeVarintFromStream
// START_CONTRACT:
// PURPOSE: Декодирование varint из потока
// INPUTS: std::fstream& stream - поток для чтения
// OUTPUTS: uint64_t - декодированное значение
// KEYWORDS: PATTERN(8): VarintDecode; DOMAIN(7): Deserialization; TECH(6): Stream
// END_CONTRACT
uint64_t BerkeleyDBWriter::decodeVarintFromStream(std::fstream& stream) const {
    uint64_t result = 0;
    int shift = 0;
    
    while (true) {
        unsigned char byte;
        if (!stream.read(reinterpret_cast<char*>(&byte), 1)) {
            return 0;
        }
        
        result |= static_cast<uint64_t>(byte & 0x7F) << shift;
        
        // Если старший бит не установлен, это последний байт
        if ((byte & 0x80) == 0) {
            break;
        }
        
        shift += 7;
        
        // Защита от бесконечного цикла
        if (shift > 63) {
            return 0;
        }
    }
    
    return result;
}

// START_FUNCTION_logToFile
// START_CONTRACT:
// PURPOSE: Логирование сообщений в файл
// INPUTS: const std::string& message - сообщение для логирования
// OUTPUTS: Нет
// KEYWORDS: PATTERN(5): Logging; DOMAIN(5): Debug; TECH(4): FileIO
// END_CONTRACT
void BerkeleyDBWriter::logToFile(const std::string& message) const {
    std::ofstream log_file(LOG_FILE, std::ios::app);
    if (log_file.is_open()) {
        // Добавляем timestamp
        std::time_t now = std::time(nullptr);
        char timestamp[64];
        std::strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", std::localtime(&now));
        log_file << "[" << timestamp << "] " << message << std::endl;
        log_file.close();
    }
}
// END_FUNCTION_logToFile

// START_FUNCTION_Factory_Create
// START_CONTRACT:
// PURPOSE: Фабричный метод создания экземпляра BerkeleyDBWriter
// INPUTS: Нет
// OUTPUTS: std::unique_ptr<BerkeleyDBWriter> - новый экземпляр
// KEYWORDS: PATTERN(7): FactoryMethod; DOMAIN(9): Creational; TECH(5): Factory
// END_CONTRACT
std::unique_ptr<BerkeleyDBWriter> BerkeleyDBWriterFactory::create() {
    return std::make_unique<BerkeleyDBWriter>();
}
// END_FUNCTION_Factory_Create

// START_FUNCTION_Factory_GetVersion
// START_CONTRACT:
// PURPOSE: Получение версии эмулятора Berkeley DB
// INPUTS: Нет
// OUTPUTS: std::string - версия
// KEYWORDS: PATTERN(6): VersionGet; DOMAIN(5): Metadata; TECH(4): Getter
// END_CONTRACT
std::string BerkeleyDBWriterFactory::getVersion() {
    return "1.0.0";
}
// END_FUNCTION_Factory_GetVersion

} // namespace berkeley_db
