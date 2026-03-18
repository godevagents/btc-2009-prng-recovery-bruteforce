/**
 * FILE: src/plugins/wallet/address_matcher/address_matcher.cpp
 * VERSION: 1.0.0
 * PURPOSE: Implementation of Bitcoin address list comparison using switch-mode algorithm.
 * LANGUAGE: C++11
 */

#include "address_matcher.h"
#include <openssl/ripemd.h>
#include <openssl/sha.h>
#include <iostream>
#include <stdexcept>
#include <cstring>
#include <fstream>
#include <sstream>

// =============================================================================
// LOGGING UTILITIES
// =============================================================================

inline void LogToAiState(const std::string& classifier, const std::string& func, 
                         const std::string& block, const std::string& op, 
                         const std::string& desc, const std::string& status) {
    std::string logLine = "[" + classifier + "][" + func + "][" + block + "][" + op + "] " + desc + " [" + status + "]";
    // Console output removed - logs only to file
    std::ofstream logFile("app.log", std::ios_base::app);
    if (logFile.is_open()) {
        logFile << logLine << std::endl;
    }
}

#define LOG_TRACE(classifier, func, block, op, desc, status) \
    LogToAiState(classifier, func, block, op, desc, status);

namespace address_matcher {

// =============================================================================
// PRIVATE HELPERS - BASE58 ENCODING/DECODING
// =============================================================================

namespace {

// Таблица для быстрого поиска индекса символа в Base58
// Base58 алфавит: "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
// Заполняем -1 для всех символов, затем устанавливаем правильные индексы
int8_t b58_digits[256] = {
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1
};

// Инициализация таблицы при первом вызове - устанавливаем правильные индексы
struct B58Init {
    B58Init() {
        // Base58 алфавит: "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        const char* alphabet = BASE58_ALPHABET;
        for (int i = 0; alphabet[i]; ++i) {
            b58_digits[(unsigned char)alphabet[i]] = i;
        }
    }
};

// Статическая инициализация
B58Init b58_init;

// =============================================================================
// HELPER: Base58Decode
// =============================================================================

bool base58_decode(const char* str, unsigned char* bytes, size_t max_len, size_t* out_len) {
    const char* FuncName = "base58_decode";
    LOG_TRACE("VarCheck", FuncName, "INPUT_PARAMS", "Params", 
              "Декодирование Base58 строки, длина: " + std::to_string(strlen(str)), "INFO");
    
    size_t len = strlen(str);
    size_t i, j;
    
    // Очистка выходного буфера
    memset(bytes, 0, max_len);
    
    // Декодирование
    for (i = 0; i < len; ++i) {
        int8_t digit = b58_digits[(unsigned char)str[i]];
        if (digit < 0) {
            LOG_TRACE("VarCheck", FuncName, "VALIDATE_DIGIT", "ConditionCheck", 
                      "Неверный символ в Base58 строке: " + std::string(1, str[i]), "FAIL");
            return false;
        }
        
        uint32_t carry = digit;
        for (j = max_len; j > 0; --j) {
            carry += (uint32_t)bytes[j - 1] * 58;
            bytes[j - 1] = (unsigned char)(carry & 0xff);
            carry >>= 8;
        }
        
        if (carry != 0) {
            LOG_TRACE("VarCheck", FuncName, "CHECK_CARRY", "ConditionCheck", 
                      "Перенос при декодировании", "FAIL");
            return false;
        }
    }
    
    *out_len = max_len;
    LOG_TRACE("TraceCheck", FuncName, "DECODE_COMPLETE", "ReturnData", 
              "Декодирование завершено, выходная длина: " + std::to_string(*out_len), "SUCCESS");
    return true;
}

// =============================================================================
// HELPER: Base58Encode
// =============================================================================

bool base58_encode(const unsigned char* bytes, size_t len, char* str, size_t max_len) {
    const char* FuncName = "base58_encode";
    LOG_TRACE("VarCheck", FuncName, "INPUT_PARAMS", "Params", 
              "Кодирование в Base58, длина входа: " + std::to_string(len), "INFO");
    
    unsigned char buffer[64];
    memset(buffer, 0, sizeof(buffer));
    
    size_t i, j;
    size_t zeros = 0;
    
    // Подсчет ведущих нулей
    for (i = 0; i < len && bytes[i] == 0; ++i) {
        ++zeros;
    }
    LOG_TRACE("VarCheck", FuncName, "COUNT_ZEROS", "ReturnData", 
              "Подсчитано ведущих нулей: " + std::to_string(zeros), "VALUE");
    
    // Кодирование
    size_t output_len = 0;
    for (; i < len; ++i) {
        uint32_t carry = bytes[i];
        for (j = sizeof(buffer) - 1; j > 0; --j) {
            carry += (uint32_t)buffer[j - 1] * 256;
            buffer[j - 1] = (unsigned char)(carry % 58);
            carry /= 58;
        }
    }
    
    // Пропуск ведущих нулей в буфере
    for (j = 0; j < sizeof(buffer) && buffer[j] == 0; ++j);
    
    // Запись результата
    if (zeros + (sizeof(buffer) - j) + 1 > max_len) {
        LOG_TRACE("CriticalError", FuncName, "CHECK_BUFFER", "ConditionCheck", 
                  "Буфер слишком мал для результата", "FAIL");
        return false;
    }
    
    memset(str, 0, max_len);
    
    // Запись ведущих нулей
    for (i = 0; i < zeros; ++i) {
        str[i] = '1';
    }
    
    // Запись остальных символов
    for (; j < sizeof(buffer); ++j) {
        str[i++] = BASE58_ALPHABET[buffer[j]];
    }
    
    str[i] = '\0';
    LOG_TRACE("TraceCheck", FuncName, "ENCODE_COMPLETE", "ReturnData", 
              "Кодирование завершено, длина результата: " + std::to_string(i), "SUCCESS");
    return true;
}

// =============================================================================
// HELPER: Check Bitcoin Address
// =============================================================================

bool verify_address_checksum(const unsigned char* bytes, size_t len) {
    const char* FuncName = "verify_address_checksum";
    LOG_TRACE("VarCheck", FuncName, "INPUT_PARAMS", "Params", 
              "Проверка контрольной суммы адреса, длина: " + std::to_string(len), "INFO");
    
    if (len != 25) {
        LOG_TRACE("VarCheck", FuncName, "CHECK_LENGTH", "ConditionCheck", 
                  "Неверная длина адреса: " + std::to_string(len) + " (ожидалось 25)", "FAIL");
        return false;
    }
    
    // Вычисление SHA256(SHA256(first 21 bytes))
    unsigned char hash1[SHA256_DIGEST_LENGTH];
    unsigned char hash2[SHA256_DIGEST_LENGTH];
    
    SHA256(bytes, 21, hash1);
    LOG_TRACE("CallExternal", FuncName, "FIRST_SHA256", "CallExternal", 
              "Вызов SHA256 для первых 21 байт", "ATTEMPT");
    
    SHA256(hash1, SHA256_DIGEST_LENGTH, hash2);
    LOG_TRACE("CallExternal", FuncName, "SECOND_SHA256", "CallExternal", 
              "Вызов SHA256 для хеша", "ATTEMPT");
    
    // Проверка контрольной суммы (первые 4 байта)
    bool checksum_valid = memcmp(bytes + 21, hash2, 4) == 0;
    LOG_TRACE("VarCheck", FuncName, "CHECK_CHECKSUM", "ConditionCheck", 
              "Контрольная сумма " + std::string(checksum_valid ? "верна" : "неверна"), 
              checksum_valid ? "SUCCESS" : "FAIL");
    
    return checksum_valid;
}

} // anonymous namespace

// =============================================================================
// ADDRESS MATCHER IMPLEMENTATION
// =============================================================================

// START_CONSTRUCTOR_ADDRESSMATCHER
AddressMatcher::AddressMatcher() {
    const char* FuncName = "AddressMatcher";
    LOG_TRACE("InitCheck", FuncName, "CONSTRUCTOR", "Start", 
              "Создание объекта AddressMatcher", "ATTEMPT");
    LOG_TRACE("InitCheck", FuncName, "CONSTRUCTOR", "Complete", 
              "Объект AddressMatcher создан", "SUCCESS");
}

// START_DESTRUCTOR_ADDRESSMATCHER
AddressMatcher::~AddressMatcher() {
    const char* FuncName = "~AddressMatcher";
    LOG_TRACE("InitCheck", FuncName, "DESTRUCTOR", "Start", 
              "Уничтожение объекта AddressMatcher", "ATTEMPT");
    LOG_TRACE("InitCheck", FuncName, "DESTRUCTOR", "Complete", 
              "Объект AddressMatcher уничтожен", "SUCCESS");
}

// START_METHOD_decodeBase58
// START_CONTRACT:
// PURPOSE: Декодирование Base58 строки в бинарный формат (25 байт)
// INPUTS: const std::string& address - адрес в формате Base58
// OUTPUTS: RawAddress - бинарное представление адреса
// KEYWORDS: [PATTERN(8): Base58Decode; TECH(7): Crypto; DOMAIN(8): AddressFormat]
// END_CONTRACT
RawAddress AddressMatcher::decodeBase58(const std::string& address) const {
    const char* FuncName = "decodeBase58";
    LOG_TRACE("VarCheck", FuncName, "INPUT_PARAMS", "Params", 
              "Декодирование адреса: " + address.substr(0, 10) + "...", "INFO");
    
    RawAddress result;
    
    // Валидация длины адреса
    if (address.length() < 26 || address.length() > 35) {
        LOG_TRACE("CriticalError", FuncName, "VALIDATE_LENGTH", "ExceptionCaught", 
                  "Неверная длина адреса: " + std::to_string(address.length()), "FAIL");
        throw std::invalid_argument("Invalid Bitcoin address length");
    }
    LOG_TRACE("VarCheck", FuncName, "VALIDATE_LENGTH", "ConditionCheck", 
              "Длина адреса корректна: " + std::to_string(address.length()), "SUCCESS");
    
    // Проверка первого символа (версия)
    if (address[0] != '1' && address[0] != '3') {
        LOG_TRACE("CriticalError", FuncName, "VALIDATE_VERSION", "ExceptionCaught", 
                  "Неверный первый символ (версия): " + std::string(1, address[0]), "FAIL");
        throw std::invalid_argument("Invalid Bitcoin address version");
    }
    LOG_TRACE("VarCheck", FuncName, "VALIDATE_VERSION", "ConditionCheck", 
              "Версия адреса корректна: " + std::string(1, address[0]), "SUCCESS");
    
    // Декодирование Base58
    unsigned char decoded[25];
    size_t out_len = 0;
    
    LOG_TRACE("CallExternal", FuncName, "BASE58_DECODE", "CallExternal", 
              "Вызов base58_decode", "ATTEMPT");
    
    if (!base58_decode(address.c_str(), decoded, 25, &out_len)) {
        LOG_TRACE("CriticalError", FuncName, "BASE58_DECODE", "ExceptionCaught", 
                  "Ошибка декодирования Base58", "FAIL");
        throw std::invalid_argument("Base58 decoding failed");
    }
    LOG_TRACE("TraceCheck", FuncName, "BASE58_DECODE", "StepComplete", 
              "Base58 декодирование успешно", "SUCCESS");
    
    // Проверка контрольной суммы
    if (!verify_address_checksum(decoded, out_len)) {
        throw std::invalid_argument("Address checksum verification failed");
    }
    
    // Копирование результата
    memcpy(result.data, decoded, RAW_ADDRESS_SIZE);
    
    LOG_TRACE("TraceCheck", FuncName, "DECODE_COMPLETE", "ReturnData", 
              "Декодирование завершено, размер: " + std::to_string(RAW_ADDRESS_SIZE) + " байт", "SUCCESS");
    
    return result;
}

// START_METHOD_encodeBase58
// START_CONTRACT:
// PURPOSE: Кодирование бинарного адреса в Base58 строку
// INPUTS: const RawAddress& raw - бинарное представление
// OUTPUTS: std::string - адрес в формате Base58
// KEYWORDS: [PATTERN(8): Base58Encode; TECH(7): Crypto; DOMAIN(8): AddressFormat]
// END_CONTRACT
std::string AddressMatcher::encodeBase58(const RawAddress& raw) const {
    const char* FuncName = "encodeBase58";
    LOG_TRACE("VarCheck", FuncName, "INPUT_PARAMS", "Params", 
              "Кодирование адреса в Base58, размер: " + std::to_string(RAW_ADDRESS_SIZE) + " байт", "INFO");
    
    char encoded[64];
    
    LOG_TRACE("CallExternal", FuncName, "BASE58_ENCODE", "CallExternal", 
              "Вызов base58_encode", "ATTEMPT");
    
    if (!base58_encode(raw.data, RAW_ADDRESS_SIZE, encoded, sizeof(encoded))) {
        LOG_TRACE("CriticalError", FuncName, "BASE58_ENCODE", "ExceptionCaught", 
                  "Ошибка кодирования Base58", "FAIL");
        throw std::runtime_error("Base58 encoding failed");
    }
    
    LOG_TRACE("TraceCheck", FuncName, "ENCODE_COMPLETE", "ReturnData", 
              "Кодирование завершено: " + std::string(encoded), "SUCCESS");
    
    return std::string(encoded);
}

// START_METHOD_loadAddressesFromFile
// START_CONTRACT:
// PURPOSE: Загрузка адресов из текстового файла
// INPUTS: const std::string& filepath - путь к файлу
// OUTPUTS: std::vector<std::string> - вектор адресов
// KEYWORDS: [PATTERN(7): FileIO; DOMAIN(8): AddressList; TECH(5): Parsing]
// END_CONTRACT
std::vector<std::string> AddressMatcher::loadAddressesFromFile(const std::string& filepath) const {
    const char* FuncName = "loadAddressesFromFile";
    LOG_TRACE("VarCheck", FuncName, "INPUT_PARAMS", "Params", 
              "Загрузка адресов из файла: " + filepath, "INFO");
    
    std::vector<std::string> addresses;
    
    LOG_TRACE("CallExternal", FuncName, "OPEN_FILE", "CallExternal", 
              "Открытие файла: " + filepath, "ATTEMPT");
    
    std::ifstream file(filepath);
    if (!file.is_open()) {
        LOG_TRACE("CriticalError", FuncName, "OPEN_FILE", "ExceptionCaught", 
                  "Не удалось открыть файл: " + filepath, "FAIL");
        throw std::runtime_error("Cannot open file: " + filepath);
    }
    LOG_TRACE("TraceCheck", FuncName, "OPEN_FILE", "StepComplete", 
              "Файл успешно открыт", "SUCCESS");
    
    std::string line;
    size_t line_count = 0;
    while (std::getline(file, line)) {
        line_count++;
        // Удаление пробелов и пустых строк
        line.erase(remove_if(line.begin(), line.end(), ::isspace), line.end());
        
        if (!line.empty()) {
            addresses.push_back(line);
        }
    }
    
    LOG_TRACE("TraceCheck", FuncName, "READ_COMPLETE", "ReturnData", 
              "Прочитано строк: " + std::to_string(line_count) + 
              ", адресов загружено: " + std::to_string(addresses.size()), "SUCCESS");
    
    return addresses;
}

// START_METHOD_convertToRaw
std::vector<RawAddress> AddressMatcher::convertToRaw(const std::vector<std::string>& addresses) const {
    const char* FuncName = "convertToRaw";
    LOG_TRACE("VarCheck", FuncName, "INPUT_PARAMS", "Params", 
              "Конвертация адресов в бинарный формат, количество: " + std::to_string(addresses.size()), "INFO");
    
    std::vector<RawAddress> result;
    result.reserve(addresses.size());
    
    size_t success_count = 0;
    size_t fail_count = 0;
    
    for (const auto& addr : addresses) {
        try {
            result.push_back(decodeBase58(addr));
            success_count++;
        } catch (const std::exception& e) {
            fail_count++;
            LOG_TRACE("VarCheck", FuncName, "DECODE_ERROR", "ExceptionCaught", 
                      "Ошибка декодирования адреса: " + addr.substr(0, 10) + "...", "FAIL");
        }
    }
    
    LOG_TRACE("TraceCheck", FuncName, "CONVERT_COMPLETE", "ReturnData", 
              "Конвертация завершена: успешно=" + std::to_string(success_count) + 
              ", ошибки=" + std::to_string(fail_count), "SUCCESS");
    
    return result;
}

// START_METHOD_convertToBase58
std::vector<std::string> AddressMatcher::convertToBase58(const std::vector<RawAddress>& raw_addresses) const {
    const char* FuncName = "convertToBase58";
    LOG_TRACE("VarCheck", FuncName, "INPUT_PARAMS", "Params", 
              "Конвертация бинарных адресов в Base58, количество: " + std::to_string(raw_addresses.size()), "INFO");
    
    std::vector<std::string> result;
    result.reserve(raw_addresses.size());
    
    for (const auto& raw : raw_addresses) {
        result.push_back(encodeBase58(raw));
    }
    
    LOG_TRACE("TraceCheck", FuncName, "CONVERT_COMPLETE", "ReturnData", 
              "Конвертация завершена, количество: " + std::to_string(result.size()), "SUCCESS");
    
    return result;
}

// START_METHOD_findIntersection
// START_CONTRACT:
// PURPOSE: Поиск пересечения между двумя списками адресов с переключением режимов
// INPUTS: const std::vector<std::string>& list1, const std::vector<std::string>& list2
// OUTPUTS: MatchResult - результат с совпадениями и статистикой
// KEYWORDS: [PATTERN(9): ListIntersection; DOMAIN(9): AddressMatching; TECH(8): HashSet]
// END_CONTRACT
MatchResult AddressMatcher::findIntersection(
    const std::vector<std::string>& list1,
    const std::vector<std::string>& list2
) const {
    const char* FuncName = "findIntersection";
    LOG_TRACE("VarCheck", FuncName, "INPUT_PARAMS", "Params", 
              "Поиск пересечения: list1=" + std::to_string(list1.size()) + 
              ", list2=" + std::to_string(list2.size()), "INFO");
    
    MatchResult result;
    
    // =============================================================================
    // ЭТАП 1: Подготовка данных (Конвертация Base58 -> Raw)
    // =============================================================================
    // START_BLOCK_CONVERT_LISTS: [Конвертация списков адресов в бинарный формат]
    LOG_TRACE("TraceCheck", FuncName, "CONVERT_LISTS", "Start", 
              "Конвертация списков адресов в бинарный формат", "ATTEMPT");
    
    std::vector<RawAddress> raw_list1 = convertToRaw(list1);
    std::vector<RawAddress> raw_list2 = convertToRaw(list2);
    
    LOG_TRACE("TraceCheck", FuncName, "CONVERT_LISTS", "StepComplete", 
              "Конвертация завершена: list1=" + std::to_string(raw_list1.size()) + 
              ", list2=" + std::to_string(raw_list2.size()), "SUCCESS");
    // END_BLOCK_CONVERT_LISTS
    
    // =============================================================================
    // ЭТАП 2: Выбор режима (Switch Mode)
    // =============================================================================
    // START_BLOCK_SWITCH_MODE: [Определение меньшего списка для хеш-таблицы]
    LOG_TRACE("TraceCheck", FuncName, "SWITCH_MODE", "Start", 
              "Определение режима (switch mode)", "ATTEMPT");
    
    bool list1_is_smaller = (raw_list1.size() < raw_list2.size());
    
    std::vector<RawAddress>& lookup_list = list1_is_smaller ? raw_list1 : raw_list2;
    std::vector<RawAddress>& query_list = list1_is_smaller ? raw_list2 : raw_list1;
    
    result.mode_used = list1_is_smaller ? 1 : 2;
    result.lookup_size = lookup_list.size();
    result.query_size = query_list.size();
    
    LOG_TRACE("VarCheck", FuncName, "SWITCH_MODE", "ReturnData", 
              "Выбран режим: " + std::to_string(result.mode_used) + 
              ", lookup_size=" + std::to_string(result.lookup_size) + 
              ", query_size=" + std::to_string(result.query_size), "SUCCESS");
    // END_BLOCK_SWITCH_MODE
    
    // =============================================================================
    // ЭТАП 3: Построение хеш-таблицы
    // =============================================================================
    // START_BLOCK_BUILD_HASHTABLE: [Построение хеш-таблицы из меньшего списка]
    LOG_TRACE("TraceCheck", FuncName, "BUILD_HASHTABLE", "Start", 
              "Построение хеш-таблицы", "ATTEMPT");
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    std::unordered_set<RawAddress> lookup_set;
    lookup_set.reserve(lookup_list.size() * 2);
    
    for (const auto& addr : lookup_list) {
        lookup_set.insert(addr);
    }
    
    LOG_TRACE("TraceCheck", FuncName, "BUILD_HASHTABLE", "StepComplete", 
              "Хеш-таблица построена, размер: " + std::to_string(lookup_set.size()), "SUCCESS");
    // END_BLOCK_BUILD_HASHTABLE
    
    // =============================================================================
    // ЭТАП 4: Поиск пересечений
    // =============================================================================
    // START_BLOCK_FIND_MATCHES: [Поиск совпадений в большем списке]
    LOG_TRACE("TraceCheck", FuncName, "FIND_MATCHES", "Start", 
              "Поиск совпадений", "ATTEMPT");
    
    for (const auto& addr : query_list) {
        if (lookup_set.find(addr) != lookup_set.end()) {
            result.matches.push_back(addr);
        }
    }
    
    LOG_TRACE("TraceCheck", FuncName, "FIND_MATCHES", "StepComplete", 
              "Найдено совпадений: " + std::to_string(result.matches.size()), "SUCCESS");
    // END_BLOCK_FIND_MATCHES
    
    // =============================================================================
    // ЭТАП 5: Завершение и возврат результата
    // =============================================================================
    // START_BLOCK_FINISH: [Завершение и измерение времени]
    auto end_time = std::chrono::high_resolution_clock::now();
    result.execution_time_ms = std::chrono::duration<double, std::milli>(end_time - start_time).count();
    
    LOG_TRACE("TraceCheck", FuncName, "FINISH", "ReturnData", 
              "Поиск пересечения завершен: совпадений=" + std::to_string(result.matches.size()) + 
              ", время=" + std::to_string(result.execution_time_ms) + "мс", "SUCCESS");
    // END_BLOCK_FINISH
    
    return result;
}

// START_METHOD_generateList1
// START_CONTRACT:
// PURPOSE: Генерация LIST_1 (1000 адресов) из единой энтропии
// INPUTS: const std::vector<unsigned char>& entropy_data - данные энтропии
// OUTPUTS: std::vector<std::string> - вектор адресов
// KEYWORDS: [PATTERN(8): AddressGeneration; DOMAIN(9): Deterministic; TECH(7): Entropy]
// END_CONTRACT
std::vector<std::string> AddressMatcher::generateList1(
    const std::vector<unsigned char>& entropy_data
) const {
    const char* FuncName = "generateList1";
    LOG_TRACE("VarCheck", FuncName, "INPUT_PARAMS", "Params", 
              "Генерация LIST_1, размер энтропии: " + std::to_string(entropy_data.size()) + 
              ", количество адресов: " + std::to_string(DEFAULT_LIST1_SIZE), "INFO");
    
    // Примечание: Эта функция требует интеграции с batch_gen модулем
    // Для простоты, здесь используется простая генерация на основе энтропии
    
    std::vector<std::string> addresses;
    addresses.reserve(DEFAULT_LIST1_SIZE);
    
    if (entropy_data.empty()) {
        LOG_TRACE("CriticalError", FuncName, "CHECK_ENTROPY", "ExceptionCaught", 
                  "Данные энтропии пусты", "FAIL");
        throw std::invalid_argument("Entropy data is empty");
    }
    
    LOG_TRACE("TraceCheck", FuncName, "GENERATE_ADDRESSES", "Start", 
              "Начало генерации адресов", "ATTEMPT");
    
    // Используем энтропию для генерации псевдоадресов (упрощенная версия)
    // В реальной реализации здесь будет вызов batch_gen
    for (size_t i = 0; i < DEFAULT_LIST1_SIZE; ++i) {
        // Создаем псевдоадрес на основе энтропии и индекса
        unsigned char addr_data[25] = {0};
        
        // Байт версии (0x00 для P2PKH)
        addr_data[0] = 0x00;
        
        // Копируем часть энтропии (с циклическим сдвигом)
        size_t entropy_offset = (i * 20) % entropy_data.size();
        for (size_t j = 0; j < 20; ++j) {
            addr_data[1 + j] = entropy_data[(entropy_offset + j) % entropy_data.size()];
        }
        
        // Вычисляем контрольную сумму: SHA256(SHA256(first 21 bytes))
        unsigned char checksum[SHA256_DIGEST_LENGTH];
        SHA256(addr_data, 21, checksum);
        SHA256(checksum, SHA256_DIGEST_LENGTH, checksum);  // Второй SHA256
        
        LOG_TRACE("CallExternal", FuncName, "SHA256", "CallExternal", 
                  "Вызов SHA256 (double) для адреса " + std::to_string(i), "ATTEMPT");
        
        // Копируем первые 4 байта контрольной суммы
        memcpy(addr_data + 21, checksum, 4);
        
        // Кодируем в Base58
        char encoded[64];
        if (base58_encode(addr_data, 25, encoded, sizeof(encoded))) {
            addresses.push_back(std::string(encoded));
        }
    }
    
    LOG_TRACE("TraceCheck", FuncName, "GENERATE_COMPLETE", "ReturnData", 
              "Генерация LIST_1 завершена, создано адресов: " + std::to_string(addresses.size()), "SUCCESS");
    
    return addresses;
}

// =============================================================================
// PLUGIN FACTORY
// =============================================================================

// START_METHOD_CREATE_FACTORY
std::unique_ptr<AddressMatcherInterface> AddressMatcherPluginFactory::create() {
    const char* FuncName = "AddressMatcherPluginFactory::create";
    LOG_TRACE("InitCheck", FuncName, "CREATE", "Start", 
              "Создание экземпляра AddressMatcher через фабрику", "ATTEMPT");
    
    auto result = std::make_unique<AddressMatcher>();
    
    LOG_TRACE("InitCheck", FuncName, "CREATE", "Complete", 
              "Экземпляр AddressMatcher создан через фабрику", "SUCCESS");
    
    return result;
}

// START_METHOD_GET_VERSION
std::string AddressMatcherPluginFactory::getVersion() {
    const char* FuncName = "AddressMatcherPluginFactory::getVersion";
    LOG_TRACE("VarCheck", FuncName, "GET_VERSION", "Params", 
              "Получение версии плагина AddressMatcher", "INFO");
    
    LOG_TRACE("TraceCheck", FuncName, "GET_VERSION", "ReturnData", 
              "Версия плагина: 1.0.0", "VALUE");
    
    return "1.0.0";
}

} // namespace address_matcher
