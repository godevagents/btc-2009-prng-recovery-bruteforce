#ifndef WALLET_SETTINGS_H
#define WALLET_SETTINGS_H

#include <vector>
#include <string>
#include <cstdint>
#include <optional>
#include <sstream>
#include <iomanip>
#include <ctime>
#include <fstream>
#include <memory>

namespace wallet_settings {

// Константы для логирования
static const std::string LOG_FILE = "wallet_settings.log";

// Константы формата настроек Bitcoin 0.1.0
static const int DEFAULT_MIN_VERSION = 100;
static const int64_t DEFAULT_TRANSACTION_FEE = 50;
static const int DEFAULT_LIMIT_PROCESS_BLOCK = 100;
static const bool DEFAULT_GENERATE_BITCOINS = false;
static const bool DEFAULT_MINIMIZE_TO_TRAY = false;
static const bool DEFAULT_USE_SSL = false;
static const int DEFAULT_PROCESS_ACTIONS = 0;

// Имена настроек для Berkeley DB
static const std::string SETTING_MIN_VERSION = "minVersion";
static const std::string SETTING_N_TRANSACTION_FEE = "nTransactionFee";
static const std::string SETTING_N_LIMIT_PROCESS_BLOCK = "nLimitProcessBlock";
static const std::string SETTING_F_GENERATE_BITCOINS = "fGenerateBitcoins";
static const std::string SETTING_F_MINIMIZE_TO_TRAY = "fMinimizeToTray";
static const std::string SETTING_F_USE_SSL = "fUseSSL";
static const std::string SETTING_N_PROCESS_ACTIONS = "nProcessActions";

/**
 * @brief Класс настроек кошелька (CWalletSettings)
 * 
 * Реализует структуру настроек кошелька в формате Bitcoin 0.1.0.
 * Включает все поля, необходимые для записи в Berkeley DB.
 */
class WalletSettings {
public:
    /**
     * @brief Конструктор по умолчанию
     */
    WalletSettings();
    
    /**
     * @brief Деструктор
     */
    ~WalletSettings();
    
    // START_METHOD_setMinVersion
    // START_CONTRACT:
    // PURPOSE: Установка минимальной версии кошелька
    // INPUTS: int minVersion - минимальная версия
    // OUTPUTS: void
    // KEYWORDS: PATTERN(8): VersionSet; DOMAIN(8): Settings; TECH(5): Setter
    // END_CONTRACT
    void setMinVersion(int minVersion);
    
    // START_METHOD_setNTransactionFee
    // START_CONTRACT:
    // PURPOSE: Установка комиссии за транзакцию
    // INPUTS: int64_t fee - комиссия в сатоши
    // OUTPUTS: void
    // KEYWORDS: PATTERN(8): FeeSet; DOMAIN(8): Transaction; TECH(5): Setter
    // END_CONTRACT
    void setNTransactionFee(int64_t fee);
    
    // START_METHOD_setNLimitProcessBlock
    // START_CONTRACT:
    // PURPOSE: Установка лимита обработки блоков
    // INPUTS: int limit - лимит блоков
    // OUTPUTS: void
    // KEYWORDS: PATTERN(9): LimitSet; DOMAIN(7): Process; TECH(5): Setter
    // END_CONTRACT
    void setNLimitProcessBlock(int limit);
    
    // START_METHOD_setFGenerateBitcoins
    // START_CONTRACT:
    // PURPOSE: Установка флага генерации биткоинов
    // INPUTS: bool generate - флаг генерации
    // OUTPUTS: void
    // KEYWORDS: PATTERN(9): GenerateSet; DOMAIN(7): Mining; TECH(5): Setter
    // END_CONTRACT
    void setFGenerateBitcoins(bool generate);
    
    // START_METHOD_setFMinimizeToTray
    // START_CONTRACT:
    // PURPOSE: Установка флага минимизации в трей
    // INPUTS: bool minimize - флаг минимизации
    // OUTPUTS: void
    // KEYWORDS: PATTERN(9): MinimizeSet; DOMAIN(6): UI; TECH(5): Setter
    // END_CONTRACT
    void setFMinimizeToTray(bool minimize);
    
    // START_METHOD_setFUseSSL
    // START_CONTRACT:
    // PURPOSE: Установка флага использования SSL
    // INPUTS: bool useSSL - флаг SSL
    // OUTPUTS: void
    // KEYWORDS: PATTERN(7): SSLSet; DOMAIN(7): Network; TECH(5): Setter
    // END_CONTRACT
    void setFUseSSL(bool useSSL);
    
    // START_METHOD_setNProcessActions
    // START_CONTRACT:
    // PURPOSE: Установка количества действий
    // INPUTS: int actions - количество действий
    // OUTPUTS: void
    // KEYWORDS: PATTERN(8): ActionsSet; DOMAIN(7): Process; TECH(5): Setter
    // END_CONTRACT
    void setNProcessActions(int actions);
    
    // START_METHOD_getMinVersion
    // START_CONTRACT:
    // PURPOSE: Получение минимальной версии кошелька
    // INPUTS: Нет
    // OUTPUTS: int - минимальная версия
    // KEYWORDS: PATTERN(8): VersionGet; DOMAIN(8): Settings; TECH(5): Getter
    // END_CONTRACT
    int getMinVersion() const;
    
    // START_METHOD_getNTransactionFee
    // START_CONTRACT:
    // PURPOSE: Получение комиссии за транзакцию
    // INPUTS: Нет
    // OUTPUTS: int64_t - комиссия в сатоши
    // KEYWORDS: PATTERN(8): FeeGet; DOMAIN(8): Transaction; TECH(5): Getter
    // END_CONTRACT
    int64_t getNTransactionFee() const;
    
    // START_METHOD_getNLimitProcessBlock
    // START_CONTRACT:
    // PURPOSE: Получение лимита обработки блоков
    // INPUTS: Нет
    // OUTPUTS: int - лимит блоков
    // KEYWORDS: PATTERN(9): LimitGet; DOMAIN(7): Process; TECH(5): Getter
    // END_CONTRACT
    int getNLimitProcessBlock() const;
    
    // START_METHOD_getFGenerateBitcoins
    // START_CONTRACT:
    // PURPOSE: Получение флага генерации биткоинов
    // INPUTS: Нет
    // OUTPUTS: bool - флаг генерации
    // KEYWORDS: PATTERN(9): GenerateGet; DOMAIN(7): Mining; TECH(5): Getter
    // END_CONTRACT
    bool getFGenerateBitcoins() const;
    
    // START_METHOD_getFMinimizeToTray
    // START_CONTRACT:
    // PURPOSE: Получение флага минимизации в трей
    // INPUTS: Нет
    // OUTPUTS: bool - флаг минимизации
    // KEYWORDS: PATTERN(9): MinimizeGet; DOMAIN(6): UI; TECH(5): Getter
    // END_CONTRACT
    bool getFMinimizeToTray() const;
    
    // START_METHOD_getFUseSSL
    // START_CONTRACT:
    // PURPOSE: Получение флага использования SSL
    // INPUTS: Нет
    // OUTPUTS: bool - флаг SSL
    // KEYWORDS: PATTERN(7): SSLGet; DOMAIN(7): Network; TECH(5): Getter
    // END_CONTRACT
    bool getFUseSSL() const;
    
    // START_METHOD_getNProcessActions
    // START_CONTRACT:
    // PURPOSE: Получение количества действий
    // INPUTS: Нет
    // OUTPUTS: int - количество действий
    // KEYWORDS: PATTERN(8): ActionsGet; DOMAIN(7): Process; TECH(5): Getter
    // END_CONTRACT
    int getNProcessActions() const;
    
    // START_METHOD_serialize
    // START_CONTRACT:
    // PURPOSE: Сериализация настроек в бинарный формат Berkeley DB
    // INPUTS: const std::string& settingName - имя настройки
    // OUTPUTS: std::vector<unsigned char> - сериализованные данные
    // KEYWORDS: PATTERN(8): Serialization; DOMAIN(9): Serialization; TECH(6): Binary
    // END_CONTRACT
    std::vector<unsigned char> serialize(const std::string& settingName) const;
    
    // START_METHOD_deserialize
    // START_CONTRACT:
    // PURPOSE: Десериализация настройки из бинарного формата Berkeley DB
    // INPUTS: 
    // - const std::string& settingName - имя настройки
    // - const std::vector<unsigned char>& data - сериализованные данные
    // OUTPUTS: bool - результат десериализации
    // KEYWORDS: PATTERN(9): Deserialization; DOMAIN(9): Deserialization; TECH(6): Binary
    // END_CONTRACT
    bool deserialize(const std::string& settingName, const std::vector<unsigned char>& data);
    
    // START_METHOD_createKey
    // START_CONTRACT:
    // PURPOSE: Создание ключа записи для Berkeley DB
    // INPUTS: const std::string& settingName - имя настройки
    // OUTPUTS: std::vector<unsigned char> - ключ записи (префикс "setting" + имя настройки)
    // KEYWORDS: PATTERN(7): KeyCreation; DOMAIN(9): KeyValueStore; TECH(5): DB
    // END_CONTRACT
    std::vector<unsigned char> createKey(const std::string& settingName) const;
    
    // START_METHOD_isValid
    // START_CONTRACT:
    // PURPOSE: Проверка валидности настроек
    // INPUTS: Нет
    // OUTPUTS: bool - true если настройки валидны
    // KEYWORDS: PATTERN(7): Validation; DOMAIN(8): Settings; TECH(5): Check
    // END_CONTRACT
    bool isValid() const;
    
    // START_METHOD_getAllSettings
    // START_CONTRACT:
    // PURPOSE: Получение всех настроек в виде карты
    // INPUTS: Нет
    // OUTPUTS: std::vector<std::pair<std::string, std::vector<unsigned char>>> - вектор пар (имя, значение)
    // KEYWORDS: PATTERN(8): SettingsGet; DOMAIN(8): Settings; TECH(5): Getter
    // END_CONTRACT
    std::vector<std::pair<std::string, std::vector<unsigned char>>> getAllSettings() const;

private:
    // Минимальная версия кошелька - 4 байта
    int minVersion_;
    
    // Комиссия за транзакцию - 8 байт
    int64_t nTransactionFee_;
    
    // Лимит обработки блоков - 4 байта
    int nLimitProcessBlock_;
    
    // Флаг генерации биткоинов - 1 байт
    bool fGenerateBitcoins_;
    
    // Флаг минимизации в трей - 1 байт
    bool fMinimizeToTray_;
    
    // Флаг использования SSL - 1 байт
    bool fUseSSL_;
    
    // Количество действий - 4 байта
    int nProcessActions_;
    
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
    // INPUTS: int value - число для сериализации
    // OUTPUTS: std::vector<unsigned char> - сериализованные данные (4 байта)
    // KEYWORDS: PATTERN(7): IntSerialization; DOMAIN(6): Integer; TECH(5): LittleEndian
    // END_CONTRACT
    std::vector<unsigned char> serializeInt(int value) const;
    
    // START_HELPER_deserializeInt
    // START_CONTRACT:
    // PURPOSE: Десериализация целого числа из little-endian формата
    // INPUTS: 
    // - const std::vector<unsigned char>& data - сериализованные данные
    // - size_t& pos - позиция начала чтения
    // OUTPUTS: int - десериализованное значение
    // KEYWORDS: PATTERN(8): IntDeserialization; DOMAIN(6): Integer; TECH(5): LittleEndian
    // END_CONTRACT
    int deserializeInt(const std::vector<unsigned char>& data, size_t& pos) const;
    
    // START_HELPER_serializeInt64
    // START_CONTRACT:
    // PURPOSE: Сериализация 64-битного целого числа в little-endian формат
    // INPUTS: int64_t value - число для сериализации
    // OUTPUTS: std::vector<unsigned char> - сериализованные данные (8 байт)
    // KEYWORDS: PATTERN(8): Int64Serialization; DOMAIN(6): Integer; TECH(5): LittleEndian
    // END_CONTRACT
    std::vector<unsigned char> serializeInt64(int64_t value) const;
    
    // START_HELPER_deserializeInt64
    // START_CONTRACT:
    // PURPOSE: Десериализация 64-битного целого числа из little-endian формата
    // INPUTS: 
    // - const std::vector<unsigned char>& data - сериализованные данные
    // - size_t& pos - позиция начала чтения
    // OUTPUTS: int64_t - десериализованное значение
    // KEYWORDS: PATTERN(9): Int64Deserialization; DOMAIN(6): Integer; TECH(5): LittleEndian
    // END_CONTRACT
    int64_t deserializeInt64(const std::vector<unsigned char>& data, size_t& pos) const;
    
    // START_HELPER_serializeBool
    // START_CONTRACT:
    // PURPOSE: Сериализация булева значения
    // INPUTS: bool value - значение для сериализации
    // OUTPUTS: std::vector<unsigned char> - сериализованные данные (1 байт)
    // KEYWORDS: PATTERN(7): BoolSerialization; DOMAIN(6): Boolean; TECH(5): Binary
    // END_CONTRACT
    std::vector<unsigned char> serializeBool(bool value) const;
    
    // START_HELPER_deserializeBool
    // START_CONTRACT:
    // PURPOSE: Десериализация булева значения
    // INPUTS: 
    // - const std::vector<unsigned char>& data - сериализованные данные
    // - size_t& pos - позиция начала чтения
    // OUTPUTS: bool - десериализованное значение
    // KEYWORDS: PATTERN(8): BoolDeserialization; DOMAIN(6): Boolean; TECH(5): Binary
    // END_CONTRACT
    bool deserializeBool(const std::vector<unsigned char>& data, size_t& pos) const;
    
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
 * @brief Фабрика для создания экземпляров WalletSettings
 */
class WalletSettingsFactory {
public:
    static std::unique_ptr<WalletSettings> create();
    static std::string getVersion();
};

} // namespace wallet_settings

#endif // WALLET_SETTINGS_H
