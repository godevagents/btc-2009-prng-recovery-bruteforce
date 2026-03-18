#include "wallet_settings.h"
#include <iostream>
#include <sstream>
#include <iomanip>
#include <ctime>

namespace wallet_settings {

// START_FUNCTION_WalletSettings_Constructor
// START_CONTRACT:
// PURPOSE: Конструктор по умолчанию, инициализирует настройки значениями по умолчанию
// INPUTS: Нет
// OUTPUTS: Нет
// KEYWORDS: PATTERN(6): Constructor; DOMAIN(8): Settings; TECH(5): Init
// END_CONTRACT
WalletSettings::WalletSettings()
    : minVersion_(DEFAULT_MIN_VERSION),
      nTransactionFee_(DEFAULT_TRANSACTION_FEE),
      nLimitProcessBlock_(DEFAULT_LIMIT_PROCESS_BLOCK),
      fGenerateBitcoins_(DEFAULT_GENERATE_BITCOINS),
      fMinimizeToTray_(DEFAULT_MINIMIZE_TO_TRAY),
      fUseSSL_(DEFAULT_USE_SSL),
      nProcessActions_(DEFAULT_PROCESS_ACTIONS) {
    logToFile("[WalletSettings] Конструктор вызван с параметрами по умолчанию");
    std::ostringstream oss;
    oss << "[WalletSettings] minVersion=" << minVersion_ 
        << ", nTransactionFee=" << nTransactionFee_
        << ", nLimitProcessBlock=" << nLimitProcessBlock_
        << ", fGenerateBitcoins=" << fGenerateBitcoins_
        << ", fMinimizeToTray=" << fMinimizeToTray_
        << ", fUseSSL=" << fUseSSL_
        << ", nProcessActions=" << nProcessActions_;
    logToFile(oss.str());
}
// END_FUNCTION_WalletSettings_Constructor

// START_FUNCTION_WalletSettings_Destructor
// START_CONTRACT:
// PURPOSE: Деструктор
// INPUTS: Нет
// OUTPUTS: Нет
// KEYWORDS: PATTERN(6): Destructor; DOMAIN(8): Settings; TECH(5): Cleanup
// END_CONTRACT
WalletSettings::~WalletSettings() {
    logToFile("[WalletSettings] Деструктор вызван");
}
// END_FUNCTION_WalletSettings_Destructor

// START_FUNCTION_setMinVersion
// START_CONTRACT:
// PURPOSE: Установка минимальной версии кошелька
// INPUTS: int minVersion - минимальная версия
// OUTPUTS: void
// KEYWORDS: PATTERN(8): VersionSet; DOMAIN(8): Settings; TECH(5): Setter
// END_CONTRACT
void WalletSettings::setMinVersion(int minVersion) {
    std::ostringstream oss;
    oss << "[setMinVersion] Установка minVersion: " << minVersion;
    logToFile(oss.str());
    minVersion_ = minVersion;
}
// END_FUNCTION_setMinVersion

// START_FUNCTION_setNTransactionFee
// START_CONTRACT:
// PURPOSE: Установка комиссии за транзакцию
// INPUTS: int64_t fee - комиссия в сатоши
// OUTPUTS: void
// KEYWORDS: PATTERN(8): FeeSet; DOMAIN(8): Transaction; TECH(5): Setter
// END_CONTRACT
void WalletSettings::setNTransactionFee(int64_t fee) {
    std::ostringstream oss;
    oss << "[setNTransactionFee] Установка nTransactionFee: " << fee;
    logToFile(oss.str());
    nTransactionFee_ = fee;
}
// END_FUNCTION_setNTransactionFee

// START_FUNCTION_setNLimitProcessBlock
// START_CONTRACT:
// PURPOSE: Установка лимита обработки блоков
// INPUTS: int limit - лимит блоков
// OUTPUTS: void
// KEYWORDS: PATTERN(9): LimitSet; DOMAIN(7): Process; TECH(5): Setter
// END_CONTRACT
void WalletSettings::setNLimitProcessBlock(int limit) {
    std::ostringstream oss;
    oss << "[setNLimitProcessBlock] Установка nLimitProcessBlock: " << limit;
    logToFile(oss.str());
    nLimitProcessBlock_ = limit;
}
// END_FUNCTION_setNLimitProcessBlock

// START_FUNCTION_setFGenerateBitcoins
// START_CONTRACT:
// PURPOSE: Установка флага генерации биткоинов
// INPUTS: bool generate - флаг генерации
// OUTPUTS: void
// KEYWORDS: PATTERN(9): GenerateSet; DOMAIN(7): Mining; TECH(5): Setter
// END_CONTRACT
void WalletSettings::setFGenerateBitcoins(bool generate) {
    std::ostringstream oss;
    oss << "[setFGenerateBitcoins] Установка fGenerateBitcoins: " << (generate ? "true" : "false");
    logToFile(oss.str());
    fGenerateBitcoins_ = generate;
}
// END_FUNCTION_setFGenerateBitcoins

// START_FUNCTION_setFMinimizeToTray
// START_CONTRACT:
// PURPOSE: Установка флага минимизации в трей
// INPUTS: bool minimize - флаг минимизации
// OUTPUTS: void
// KEYWORDS: PATTERN(9): MinimizeSet; DOMAIN(6): UI; TECH(5): Setter
// END_CONTRACT
void WalletSettings::setFMinimizeToTray(bool minimize) {
    std::ostringstream oss;
    oss << "[setFMinimizeToTray] Установка fMinimizeToTray: " << (minimize ? "true" : "false");
    logToFile(oss.str());
    fMinimizeToTray_ = minimize;
}
// END_FUNCTION_setFMinimizeToTray

// START_FUNCTION_setFUseSSL
// START_CONTRACT:
// PURPOSE: Установка флага использования SSL
// INPUTS: bool useSSL - флаг SSL
// OUTPUTS: void
// KEYWORDS: PATTERN(7): SSLSet; DOMAIN(7): Network; TECH(5): Setter
// END_CONTRACT
void WalletSettings::setFUseSSL(bool useSSL) {
    std::ostringstream oss;
    oss << "[setFUseSSL] Установка fUseSSL: " << (useSSL ? "true" : "false");
    logToFile(oss.str());
    fUseSSL_ = useSSL;
}
// END_FUNCTION_setFUseSSL

// START_FUNCTION_setNProcessActions
// START_CONTRACT:
// PURPOSE: Установка количества действий
// INPUTS: int actions - количество действий
// OUTPUTS: void
// KEYWORDS: PATTERN(8): ActionsSet; DOMAIN(7): Process; TECH(5): Setter
// END_CONTRACT
void WalletSettings::setNProcessActions(int actions) {
    std::ostringstream oss;
    oss << "[setNProcessActions] Установка nProcessActions: " << actions;
    logToFile(oss.str());
    nProcessActions_ = actions;
}
// END_FUNCTION_setNProcessActions

// START_FUNCTION_getMinVersion
// START_CONTRACT:
// PURPOSE: Получение минимальной версии кошелька
// INPUTS: Нет
// OUTPUTS: int - минимальная версия
// KEYWORDS: PATTERN(8): VersionGet; DOMAIN(8): Settings; TECH(5): Getter
// END_CONTRACT
int WalletSettings::getMinVersion() const {
    logToFile("[getMinVersion] Получение minVersion");
    return minVersion_;
}
// END_FUNCTION_getMinVersion

// START_FUNCTION_getNTransactionFee
// START_CONTRACT:
// PURPOSE: Получение комиссии за транзакцию
// INPUTS: Нет
// OUTPUTS: int64_t - комиссия в сатоши
// KEYWORDS: PATTERN(8): FeeGet; DOMAIN(8): Transaction; TECH(5): Getter
// END_CONTRACT
int64_t WalletSettings::getNTransactionFee() const {
    logToFile("[getNTransactionFee] Получение nTransactionFee");
    return nTransactionFee_;
}
// END_FUNCTION_getNTransactionFee

// START_FUNCTION_getNLimitProcessBlock
// START_CONTRACT:
// PURPOSE: Получение лимита обработки блоков
// INPUTS: Нет
// OUTPUTS: int - лимит блоков
// KEYWORDS: PATTERN(9): LimitGet; DOMAIN(7): Process; TECH(5): Getter
// END_CONTRACT
int WalletSettings::getNLimitProcessBlock() const {
    logToFile("[getNLimitProcessBlock] Получение nLimitProcessBlock");
    return nLimitProcessBlock_;
}
// END_FUNCTION_getNLimitProcessBlock

// START_FUNCTION_getFGenerateBitcoins
// START_CONTRACT:
// PURPOSE: Получение флага генерации биткоинов
// INPUTS: Нет
// OUTPUTS: bool - флаг генерации
// KEYWORDS: PATTERN(9): GenerateGet; DOMAIN(7): Mining; TECH(5): Getter
// END_CONTRACT
bool WalletSettings::getFGenerateBitcoins() const {
    logToFile("[getFGenerateBitcoins] Получение fGenerateBitcoins");
    return fGenerateBitcoins_;
}
// END_FUNCTION_getFGenerateBitcoins

// START_FUNCTION_getFMinimizeToTray
// START_CONTRACT:
// PURPOSE: Получение флага минимизации в трей
// INPUTS: Нет
// OUTPUTS: bool - флаг минимизации
// KEYWORDS: PATTERN(9): MinimizeGet; DOMAIN(6): UI; TECH(5): Getter
// END_CONTRACT
bool WalletSettings::getFMinimizeToTray() const {
    logToFile("[getFMinimizeToTray] Получение fMinimizeToTray");
    return fMinimizeToTray_;
}
// END_FUNCTION_getFMinimizeToTray

// START_FUNCTION_getFUseSSL
// START_CONTRACT:
// PURPOSE: Получение флага использования SSL
// INPUTS: Нет
// OUTPUTS: bool - флаг SSL
// KEYWORDS: PATTERN(7): SSLGet; DOMAIN(7): Network; TECH(5): Getter
// END_CONTRACT
bool WalletSettings::getFUseSSL() const {
    logToFile("[getFUseSSL] Получение fUseSSL");
    return fUseSSL_;
}
// END_FUNCTION_getFUseSSL

// START_FUNCTION_getNProcessActions
// START_CONTRACT:
// PURPOSE: Получение количества действий
// INPUTS: Нет
// OUTPUTS: int - количество действий
// KEYWORDS: PATTERN(8): ActionsGet; DOMAIN(7): Process; TECH(5): Getter
// END_CONTRACT
int WalletSettings::getNProcessActions() const {
    logToFile("[getNProcessActions] Получение nProcessActions");
    return nProcessActions_;
}
// END_FUNCTION_getNProcessActions

// START_FUNCTION_serialize
// START_CONTRACT:
// PURPOSE: Сериализация настройки в бинарный формат Berkeley DB
// INPUTS: const std::string& settingName - имя настройки
// OUTPUTS: std::vector<unsigned char> - сериализованные данные
// KEYWORDS: PATTERN(8): Serialization; DOMAIN(9): Serialization; TECH(6): Binary
// END_CONTRACT
std::vector<unsigned char> WalletSettings::serialize(const std::string& settingName) const {
    std::ostringstream oss;
    oss << "[serialize] Сериализация настройки: " << settingName;
    logToFile(oss.str());
    
    std::vector<unsigned char> result;
    
    if (settingName == SETTING_MIN_VERSION) {
        result = serializeInt(minVersion_);
    } else if (settingName == SETTING_N_TRANSACTION_FEE) {
        result = serializeInt64(nTransactionFee_);
    } else if (settingName == SETTING_N_LIMIT_PROCESS_BLOCK) {
        result = serializeInt(nLimitProcessBlock_);
    } else if (settingName == SETTING_F_GENERATE_BITCOINS) {
        result = serializeBool(fGenerateBitcoins_);
    } else if (settingName == SETTING_F_MINIMIZE_TO_TRAY) {
        result = serializeBool(fMinimizeToTray_);
    } else if (settingName == SETTING_F_USE_SSL) {
        result = serializeBool(fUseSSL_);
    } else if (settingName == SETTING_N_PROCESS_ACTIONS) {
        result = serializeInt(nProcessActions_);
    } else {
        logToFile("[serialize] ОШИБКА: Неизвестное имя настройки");
    }
    
    oss.str("");
    oss << "[serialize] Размер сериализованных данных: " << result.size() << " байт";
    logToFile(oss.str());
    
    return result;
}
// END_FUNCTION_serialize

// START_FUNCTION_deserialize
// START_CONTRACT:
// PURPOSE: Десериализация настройки из бинарного формата Berkeley DB
// INPUTS: 
// - const std::string& settingName - имя настройки
// - const std::vector<unsigned char>& data - сериализованные данные
// OUTPUTS: bool - результат десериализации
// KEYWORDS: PATTERN(9): Deserialization; DOMAIN(9): Deserialization; TECH(6): Binary
// END_CONTRACT
bool WalletSettings::deserialize(const std::string& settingName, const std::vector<unsigned char>& data) {
    std::ostringstream oss;
    oss << "[deserialize] Десериализация настройки: " << settingName << " (размер: " << data.size() << " байт)";
    logToFile(oss.str());
    
    if (data.empty()) {
        logToFile("[deserialize] ОШИБКА: Пустые данные");
        return false;
    }
    
    size_t pos = 0;
    bool success = true;
    
    if (settingName == SETTING_MIN_VERSION) {
        minVersion_ = deserializeInt(data, pos);
    } else if (settingName == SETTING_N_TRANSACTION_FEE) {
        nTransactionFee_ = deserializeInt64(data, pos);
    } else if (settingName == SETTING_N_LIMIT_PROCESS_BLOCK) {
        nLimitProcessBlock_ = deserializeInt(data, pos);
    } else if (settingName == SETTING_F_GENERATE_BITCOINS) {
        fGenerateBitcoins_ = deserializeBool(data, pos);
    } else if (settingName == SETTING_F_MINIMIZE_TO_TRAY) {
        fMinimizeToTray_ = deserializeBool(data, pos);
    } else if (settingName == SETTING_F_USE_SSL) {
        fUseSSL_ = deserializeBool(data, pos);
    } else if (settingName == SETTING_N_PROCESS_ACTIONS) {
        nProcessActions_ = deserializeInt(data, pos);
    } else {
        logToFile("[deserialize] ОШИБКА: Неизвестное имя настройки");
        success = false;
    }
    
    oss.str("");
    oss << "[deserialize] Результат десериализации: " << (success ? "SUCCESS" : "FAIL");
    logToFile(oss.str());
    
    return success;
}
// END_FUNCTION_deserialize

// START_FUNCTION_createKey
// START_CONTRACT:
// PURPOSE: Создание ключа записи для Berkeley DB
// INPUTS: const std::string& settingName - имя настройки
// OUTPUTS: std::vector<unsigned char> - ключ записи (префикс "setting" + имя настройки)
// KEYWORDS: PATTERN(7): KeyCreation; DOMAIN(9): KeyValueStore; TECH(5): DB
// END_CONTRACT
std::vector<unsigned char> WalletSettings::createKey(const std::string& settingName) const {
    std::ostringstream oss;
    oss << "[createKey] Создание ключа для настройки: " << settingName;
    logToFile(oss.str());
    
    std::vector<unsigned char> key;
    
    // Добавляем префикс "setting"
    std::string prefix = "setting";
    key.insert(key.end(), prefix.begin(), prefix.end());
    
    // Добавляем имя настройки
    key.insert(key.end(), settingName.begin(), settingName.end());
    
    oss.str("");
    oss << "[createKey] Ключ создан, размер: " << key.size() << " байт";
    logToFile(oss.str());
    
    return key;
}
// END_FUNCTION_createKey

// START_FUNCTION_isValid
// START_CONTRACT:
// PURPOSE: Проверка валидности настроек
// INPUTS: Нет
// OUTPUTS: bool - true если настройки валидны
// KEYWORDS: PATTERN(7): Validation; DOMAIN(8): Settings; TECH(5): Check
// END_CONTRACT
bool WalletSettings::isValid() const {
    logToFile("[isValid] Проверка валидности настроек");
    
    // Проверяем базовые ограничения
    if (minVersion_ < 0) {
        logToFile("[isValid] ОШИБКА: minVersion не может быть отрицательным");
        return false;
    }
    
    if (nTransactionFee_ < 0) {
        logToFile("[isValid] ОШИБКА: nTransactionFee не может быть отрицательным");
        return false;
    }
    
    if (nLimitProcessBlock_ < 0) {
        logToFile("[isValid] ОШИБКА: nLimitProcessBlock не может быть отрицательным");
        return false;
    }
    
    logToFile("[isValid] Настройки валидны");
    return true;
}
// END_FUNCTION_isValid

// START_FUNCTION_getAllSettings
// START_CONTRACT:
// PURPOSE: Получение всех настроек в виде карты
// INPUTS: Нет
// OUTPUTS: std::vector<std::pair<std::string, std::vector<unsigned char>>> - вектор пар (имя, значение)
// KEYWORDS: PATTERN(8): SettingsGet; DOMAIN(8): Settings; TECH(5): Getter
// END_CONTRACT
std::vector<std::pair<std::string, std::vector<unsigned char>>> WalletSettings::getAllSettings() const {
    logToFile("[getAllSettings] Получение всех настроек");
    
    std::vector<std::pair<std::string, std::vector<unsigned char>>> settings;
    
    settings.push_back({SETTING_MIN_VERSION, serialize(SETTING_MIN_VERSION)});
    settings.push_back({SETTING_N_TRANSACTION_FEE, serialize(SETTING_N_TRANSACTION_FEE)});
    settings.push_back({SETTING_N_LIMIT_PROCESS_BLOCK, serialize(SETTING_N_LIMIT_PROCESS_BLOCK)});
    settings.push_back({SETTING_F_GENERATE_BITCOINS, serialize(SETTING_F_GENERATE_BITCOINS)});
    settings.push_back({SETTING_F_MINIMIZE_TO_TRAY, serialize(SETTING_F_MINIMIZE_TO_TRAY)});
    settings.push_back({SETTING_F_USE_SSL, serialize(SETTING_F_USE_SSL)});
    settings.push_back({SETTING_N_PROCESS_ACTIONS, serialize(SETTING_N_PROCESS_ACTIONS)});
    
    std::ostringstream oss;
    oss << "[getAllSettings] Всего настроек: " << settings.size();
    logToFile(oss.str());
    
    return settings;
}
// END_FUNCTION_getAllSettings

// START_HELPER_encodeVarint
// START_CONTRACT:
// PURPOSE: Кодирование числа в формат Bitcoin Varint
// INPUTS: uint64_t value - число для кодирования
// OUTPUTS: std::vector<unsigned char> - закодированное значение
// KEYWORDS: PATTERN(8): VarintEncode; DOMAIN(7): Serialization; TECH(6): Bitcoin
// END_CONTRACT
std::vector<unsigned char> WalletSettings::encodeVarint(uint64_t value) const {
    std::vector<unsigned char> result;
    
    // Varint кодирование для Bitcoin
    // 0-127: 1 байт
    // 128-16383: 2 байта
    // 16384-2097151: 3 байта
    // и т.д.
    
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
uint64_t WalletSettings::decodeVarint(const std::vector<unsigned char>& data, size_t& pos) const {
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
// INPUTS: int value - число для сериализации
// OUTPUTS: std::vector<unsigned char> - сериализованные данные (4 байта)
// KEYWORDS: PATTERN(7): IntSerialization; DOMAIN(6): Integer; TECH(5): LittleEndian
// END_CONTRACT
std::vector<unsigned char> WalletSettings::serializeInt(int value) const {
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
// OUTPUTS: int - десериализованное значение
// KEYWORDS: PATTERN(8): IntDeserialization; DOMAIN(6): Integer; TECH(5): LittleEndian
// END_CONTRACT
int WalletSettings::deserializeInt(const std::vector<unsigned char>& data, size_t& pos) const {
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
// END_HELPER_deserializeInt

// START_HELPER_serializeInt64
// START_CONTRACT:
// PURPOSE: Сериализация 64-битного целого числа в little-endian формат
// INPUTS: int64_t value - число для сериализации
// OUTPUTS: std::vector<unsigned char> - сериализованные данные (8 байт)
// KEYWORDS: PATTERN(8): Int64Serialization; DOMAIN(6): Integer; TECH(5): LittleEndian
// END_CONTRACT
std::vector<unsigned char> WalletSettings::serializeInt64(int64_t value) const {
    std::vector<unsigned char> result(8);
    result[0] = static_cast<unsigned char>(value & 0xFF);
    result[1] = static_cast<unsigned char>((value >> 8) & 0xFF);
    result[2] = static_cast<unsigned char>((value >> 16) & 0xFF);
    result[3] = static_cast<unsigned char>((value >> 24) & 0xFF);
    result[4] = static_cast<unsigned char>((value >> 32) & 0xFF);
    result[5] = static_cast<unsigned char>((value >> 40) & 0xFF);
    result[6] = static_cast<unsigned char>((value >> 48) & 0xFF);
    result[7] = static_cast<unsigned char>((value >> 56) & 0xFF);
    return result;
}
// END_HELPER_serializeInt64

// START_HELPER_deserializeInt64
// START_CONTRACT:
// PURPOSE: Десериализация 64-битного целого числа из little-endian формата
// INPUTS: 
// - const std::vector<unsigned char>& data - сериализованные данные
// - size_t& pos - позиция начала чтения
// OUTPUTS: int64_t - десериализованное значение
// KEYWORDS: PATTERN(9): Int64Deserialization; DOMAIN(6): Integer; TECH(5): LittleEndian
// END_CONTRACT
int64_t WalletSettings::deserializeInt64(const std::vector<unsigned char>& data, size_t& pos) const {
    if (pos + 8 > data.size()) {
        return 0;
    }
    
    int64_t result = 0;
    result |= static_cast<int64_t>(data[pos]);
    result |= static_cast<int64_t>(data[pos + 1]) << 8;
    result |= static_cast<int64_t>(data[pos + 2]) << 16;
    result |= static_cast<int64_t>(data[pos + 3]) << 24;
    result |= static_cast<int64_t>(data[pos + 4]) << 32;
    result |= static_cast<int64_t>(data[pos + 5]) << 40;
    result |= static_cast<int64_t>(data[pos + 6]) << 48;
    result |= static_cast<int64_t>(data[pos + 7]) << 56;
    pos += 8;
    
    return result;
}
// END_HELPER_deserializeInt64

// START_HELPER_serializeBool
// START_CONTRACT:
// PURPOSE: Сериализация булева значения
// INPUTS: bool value - значение для сериализации
// OUTPUTS: std::vector<unsigned char> - сериализованные данные (1 байт)
// KEYWORDS: PATTERN(7): BoolSerialization; DOMAIN(6): Boolean; TECH(5): Binary
// END_CONTRACT
std::vector<unsigned char> WalletSettings::serializeBool(bool value) const {
    std::vector<unsigned char> result(1);
    result[0] = value ? 1 : 0;
    return result;
}
// END_HELPER_serializeBool

// START_HELPER_deserializeBool
// START_CONTRACT:
// PURPOSE: Десериализация булева значения
// INPUTS: 
// - const std::vector<unsigned char>& data - сериализованные данные
// - size_t& pos - позиция начала чтения
// OUTPUTS: bool - десериализованное значение
// KEYWORDS: PATTERN(8): BoolDeserialization; DOMAIN(6): Boolean; TECH(5): Binary
// END_CONTRACT
bool WalletSettings::deserializeBool(const std::vector<unsigned char>& data, size_t& pos) const {
    if (pos >= data.size()) {
        return false;
    }
    
    bool result = (data[pos] != 0);
    pos += 1;
    
    return result;
}
// END_HELPER_deserializeBool

// START_HELPER_logToFile
// START_CONTRACT:
// PURPOSE: Логирование сообщений в файл
// INPUTS: const std::string& message - сообщение для логирования
// OUTPUTS: Нет
// KEYWORDS: PATTERN(5): Logging; DOMAIN(5): Debug; TECH(4): FileIO
// END_CONTRACT
void WalletSettings::logToFile(const std::string& message) const {
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
// PURPOSE: Фабричный метод создания экземпляра WalletSettings
// INPUTS: Нет
// OUTPUTS: std::unique_ptr<WalletSettings> - новый экземпляр
// KEYWORDS: PATTERN(7): FactoryMethod; DOMAIN(9): Creational; TECH(5): Factory
// END_CONTRACT
std::unique_ptr<WalletSettings> WalletSettingsFactory::create() {
    return std::make_unique<WalletSettings>();
}
// END_FUNCTION_Factory_Create

// START_FUNCTION_Factory_GetVersion
// START_CONTRACT:
// PURPOSE: Получение версии класса WalletSettings
// INPUTS: Нет
// OUTPUTS: std::string - версия
// KEYWORDS: PATTERN(6): VersionGet; DOMAIN(5): Metadata; TECH(4): Getter
// END_CONTRACT
std::string WalletSettingsFactory::getVersion() {
    return "1.0.0";
}
// END_FUNCTION_Factory_GetVersion

} // namespace wallet_settings
