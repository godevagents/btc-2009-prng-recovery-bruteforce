// FILE: src/monitor_cpp/integrations/log_parser.cpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Реализация C++ модуля log_parser - парсинг и мониторинг лог-файлов генератора кошельков.
// SCOPE: Парсинг, кэширование, метрики, поиск, фильтрация, агрегация
// INPUT: Путь к лог-файлу, строки логов
// OUTPUT: Классы: LogParser, ParsedEntry, LogMetrics, RegexPatterns, LogFilter, LogAggregator, LogWatcher
// KEYWORDS: [PATTERN(8): Parser; DOMAIN(9): LogParsing; CONCEPT(8): Incremental; TECH(7): FileIO; TECH(6): Threading]
// LINKS: [USES_API(7): spdlog]
// END_MODULE_CONTRACT

#include "log_parser.hpp"
#include <spdlog/spdlog.h>
#include <algorithm>
#include <cmath>
#include <ctime>
#include <sstream>
#include <iomanip>
#include <numeric>

namespace {
    // Локальный логгер для модуля
    auto logger = spdlog::get("log_parser");
}

//==============================================================================
// ParsedEntry Implementation
//==============================================================================

// START_METHOD_ParsedEntry_Constructor_Default
// START_CONTRACT:
// PURPOSE: Конструктор по умолчанию - инициализирует все поля
// OUTPUTS: Объект ParsedEntry с пустыми значениями
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
ParsedEntry::ParsedEntry() 
    : timestamp(0.0)
    , raw_line()
    , iteration_count(std::nullopt)
    , match_count(std::nullopt)
    , wallet_count(std::nullopt)
    , entropy_bits(std::nullopt)
    , stage(std::nullopt)
    , error(std::nullopt)
{}
// END_METHOD_ParsedEntry_Constructor_Default

// START_METHOD_ParsedEntry_Constructor_WithParams
// START_CONTRACT:
// PURPOSE: Конструктор с базовыми параметрами
// INPUTS: ts - timestamp, line - строка лога
// OUTPUTS: Объект ParsedEntry с заданными значениями
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
ParsedEntry::ParsedEntry(double ts, const std::string& line)
    : timestamp(ts)
    , raw_line(line)
    , iteration_count(std::nullopt)
    , match_count(std::nullopt)
    , wallet_count(std::nullopt)
    , entropy_bits(std::nullopt)
    , stage(std::nullopt)
    , error(std::nullopt)
{}
// END_METHOD_ParsedEntry_Constructor_WithParams

// START_METHOD_ParsedEntry_Constructor_Copy
// START_CONTRACT:
// PURPOSE: Конструктор копирования
// INPUTS: other - копируемый объект
// OUTPUTS: Копия объекта
// KEYWORDS: [CONCEPT(5): Copy]
// END_CONTRACT
ParsedEntry::ParsedEntry(const ParsedEntry& other)
    : timestamp(other.timestamp)
    , raw_line(other.raw_line)
    , iteration_count(other.iteration_count)
    , match_count(other.match_count)
    , wallet_count(other.wallet_count)
    , entropy_bits(other.entropy_bits)
    , stage(other.stage)
    , error(other.error)
{}
// END_METHOD_ParsedEntry_Constructor_Copy

// START_METHOD_ParsedEntry_OperatorAssign
// START_CONTRACT:
// PURPOSE: Оператор присваивания копирования
// INPUTS: other - копируемый объект
// OUTPUTS: Ссылка на текущий объект
// KEYWORDS: [CONCEPT(5): Assignment]
// END_CONTRACT
ParsedEntry& ParsedEntry::operator=(const ParsedEntry& other) {
    if (this != &other) {
        timestamp = other.timestamp;
        raw_line = other.raw_line;
        iteration_count = other.iteration_count;
        match_count = other.match_count;
        wallet_count = other.wallet_count;
        entropy_bits = other.entropy_bits;
        stage = other.stage;
        error = other.error;
    }
    return *this;
}
// END_METHOD_ParsedEntry_OperatorAssign

// START_METHOD_ParsedEntry_HasError
// START_CONTRACT:
// PURPOSE: Проверка наличия ошибки в записи
// OUTPUTS: true если есть ошибка
// KEYWORDS: [CONCEPT(5): Validation]
// END_CONTRACT
bool ParsedEntry::has_error() const {
    return error.has_value() && !error.value().empty();
}
// END_METHOD_ParsedEntry_HasError

// START_METHOD_ParsedEntry_HasIteration
// START_CONTRACT:
// PURPOSE: Проверка наличия итерации в записи
// OUTPUTS: true если есть итерация
// KEYWORDS: [CONCEPT(5): Validation]
// END_CONTRACT
bool ParsedEntry::has_iteration() const {
    return iteration_count.has_value();
}
// END_METHOD_ParsedEntry_HasIteration

// START_METHOD_ParsedEntry_IsEmpty
// START_CONTRACT:
// PURPOSE: Проверка пустоты записи (нет полезных данных)
// OUTPUTS: true если запись пустая
// KEYWORDS: [CONCEPT(5): Validation]
// END_CONTRACT
bool ParsedEntry::is_empty() const {
    return !iteration_count.has_value() 
        && !match_count.has_value()
        && !wallet_count.has_value()
        && !entropy_bits.has_value()
        && !stage.has_value()
        && !error.has_value();
}
// END_METHOD_ParsedEntry_IsEmpty

// START_METHOD_ParsedEntry_ToString
// START_CONTRACT:
// PURPOSE: Получение строкового представления записи
// OUTPUTS: Строковое представление
// KEYWORDS: [CONCEPT(5): StringRepresentation]
// END_CONTRACT
std::string ParsedEntry::to_string() const {
    std::ostringstream oss;
    oss << "ParsedEntry(timestamp=" << std::fixed << std::setprecision(3) << timestamp;
    oss << ", raw_line=\"" << raw_line << "\"";
    
    if (iteration_count.has_value()) {
        oss << ", iteration_count=" << iteration_count.value();
    }
    if (match_count.has_value()) {
        oss << ", match_count=" << match_count.value();
    }
    if (wallet_count.has_value()) {
        oss << ", wallet_count=" << wallet_count.value();
    }
    if (entropy_bits.has_value()) {
        oss << ", entropy_bits=" << entropy_bits.value();
    }
    if (stage.has_value()) {
        oss << ", stage=\"" << stage.value() << "\"";
    }
    if (error.has_value()) {
        oss << ", error=\"" << error.value() << "\"";
    }
    
    oss << ")";
    return oss.str();
}
// END_METHOD_ParsedEntry_ToString

//==============================================================================
// LogMetrics Implementation
//==============================================================================

// START_METHOD_LogMetrics_Constructor_Default
// START_CONTRACT:
// PURPOSE: Конструктор по умолчанию - инициализирует метрики нулями
// OUTPUTS: Объект LogMetrics с нулевыми значениями
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
LogMetrics::LogMetrics()
    : iteration_count(0)
    , match_count(0)
    , wallet_count(0)
    , entropy_bits(0.0)
    , stage("idle")
    , is_monitoring(false)
    , last_update_time(0.0)
    , error_count(0)
{}
// END_METHOD_LogMetrics_Constructor_Default

// START_METHOD_LogMetrics_Constructor_Copy
// START_CONTRACT:
// PURPOSE: Конструктор копирования
// INPUTS: other - копируемый объект
// OUTPUTS: Копия объекта
// KEYWORDS: [CONCEPT(5): Copy]
// END_CONTRACT
LogMetrics::LogMetrics(const LogMetrics& other)
    : iteration_count(other.iteration_count)
    , match_count(other.match_count)
    , wallet_count(other.wallet_count)
    , entropy_bits(other.entropy_bits)
    , stage(other.stage)
    , is_monitoring(other.is_monitoring)
    , last_update_time(other.last_update_time)
    , error_count(other.error_count)
{}
// END_METHOD_LogMetrics_Constructor_Copy

// START_METHOD_LogMetrics_Reset
// START_CONTRACT:
// PURPOSE: Сброс метрик к начальным значениям
// OUTPUTS: Нет
// KEYWORDS: [CONCEPT(5): Reset]
// END_CONTRACT
void LogMetrics::reset() {
    iteration_count = 0;
    match_count = 0;
    wallet_count = 0;
    entropy_bits = 0.0;
    stage = "idle";
    is_monitoring = false;
    last_update_time = static_cast<double>(std::time(nullptr));
    error_count = 0;
}
// END_METHOD_LogMetrics_Reset

// START_METHOD_LogMetrics_UpdateFromEntry
// START_CONTRACT:
// PURPOSE: Обновление метрик из записи лога
// INPUTS: entry - запись для извлечения метрик
// OUTPUTS: Нет
// KEYWORDS: [CONCEPT(6): Update; TECH(5): Parsing]
// END_CONTRACT
void LogMetrics::update_from_entry(const ParsedEntry& entry) {
    last_update_time = entry.timestamp;
    
    if (entry.iteration_count.has_value()) {
        iteration_count = entry.iteration_count.value();
        is_monitoring = true;
    }
    
    if (entry.match_count.has_value()) {
        match_count = entry.match_count.value();
    }
    
    if (entry.wallet_count.has_value()) {
        wallet_count = entry.wallet_count.value();
    }
    
    if (entry.entropy_bits.has_value()) {
        entropy_bits = entry.entropy_bits.value();
    }
    
    if (entry.stage.has_value()) {
        stage = entry.stage.value();
    }
    
    if (entry.error.has_value()) {
        error_count++;
    }
}
// END_METHOD_LogMetrics_UpdateFromEntry

// START_METHOD_LogMetrics_ToDict
// START_CONTRACT:
// PURPOSE: Конвертация метрик в словарь
// OUTPUTS: unordered_map с парами ключ-значение
// KEYWORDS: [CONCEPT(5): Conversion]
// END_CONTRACT
std::unordered_map<std::string, std::string> LogMetrics::to_dict() const {
    return {
        {"iteration_count", std::to_string(iteration_count)},
        {"match_count", std::to_string(match_count)},
        {"wallet_count", std::to_string(wallet_count)},
        {"entropy_bits", std::to_string(entropy_bits)},
        {"stage", stage},
        {"is_monitoring", is_monitoring ? "true" : "false"},
        {"last_update_time", std::to_string(last_update_time)},
        {"error_count", std::to_string(error_count)}
    };
}
// END_METHOD_LogMetrics_ToDict

// START_METHOD_LogMetrics_ToString
// START_CONTRACT:
// PURPOSE: Получение строкового представления
// OUTPUTS: Строковое представление
// KEYWORDS: [CONCEPT(5): StringRepresentation]
// END_CONTRACT
std::string LogMetrics::to_string() const {
    std::ostringstream oss;
    oss << "LogMetrics(iteration_count=" << iteration_count;
    oss << ", match_count=" << match_count;
    oss << ", wallet_count=" << wallet_count;
    oss << ", entropy_bits=" << std::fixed << std::setprecision(2) << entropy_bits;
    oss << ", stage=\"" << stage << "\"";
    oss << ", is_monitoring=" << (is_monitoring ? "true" : "false");
    oss << ", error_count=" << error_count;
    oss << ")";
    return oss.str();
}
// END_METHOD_LogMetrics_ToString

//==============================================================================
// RegexPatterns Implementation
//==============================================================================

// START_METHOD_RegexPatterns_Constructor
// START_CONTRACT:
// PURPOSE: Конструктор - компилирует все regex паттерны
// OUTPUTS: Объект с предкомпилированными паттернами
// KEYWORDS: [CONCEPT(6): Compilation; TECH(7): Regex]
// END_CONTRACT
RegexPatterns::RegexPatterns() 
    // Паттерн для поиска итерации: "Iteration: 12345"
    : pattern_iteration_(
        R"((\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}).*?(?:Iteration|iteration|ITERATION)[s]?\s*[:=]?\s*(\d+))",
        std::regex::icase
    )
    // Паттерн для поиска совпадений: "Match = 42"
    , pattern_match_(
        R"((\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}).*?(?:Match|match|MATCH)[s]?\s*[:=]?\s*(\d+))",
        std::regex::icase
    )
    // Паттерн для поиска кошельков: "Wallet: 1000"
    , pattern_wallet_(
        R"((\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}).*?(?:Wallet|wallet|WALLET)[s]?\s*[:=]?\s*(\d+))",
        std::regex::icase
    )
    // Паттерн для поиска энтропии: "Entropy: 256 bits"
    , pattern_entropy_(
        R"((\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}).*?(?:Entropy|entropy|ENTROPY)[s]?\s*[:=]?\s*(\d+\.?\d*)\s*(?:bits)?)",
        std::regex::icase
    )
    // Паттерн для поиска стадии: "Stage: SEARCH"
    , pattern_stage_(
        R"((\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}).*?(?:Stage|stage|STAGE)[s]?\s*[:=]?\s*(\w+))",
        std::regex::icase
    )
    // Паттерн для поиска ошибки: "Error: Connection failed"
    , pattern_error_(
        R"((\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}).*?(?:Error|ERROR|Exception|EXCEPTION)[:\s]+(.+))",
        std::regex::icase
    )
    // Паттерн для поиска прогресса: "Progress: 50.5%"
    , pattern_progress_(
        R"((\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}).*?Progress[:\s]+(\d+\.?\d*)%)",
        std::regex::icase
    )
    // Паттерн для поиска события совпадения: "MATCH: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
    , pattern_match_event_(
        R"((?:MATCH|FOUND|FOUND_MATCH)[s]?[:\s]+\"?([1A-HJ-NP-Za-km-z]{25,34})\"?)",
        std::regex::icase
    )
    // Паттерн для поиска адреса: "Address: 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
    , pattern_match_address_(
        R"((?:Address|address|ADDRESS)[s]?[:=]\s*\"?([1A-HJ-NP-Za-km-z]{25,34})\"?)",
        std::regex::icase
    )
    // Паттерн для поиска имени кошелька: "Wallet: my_wallet.dat"
    , pattern_match_wallet_(
        R"((?:Wallet|wallet|WALLET)[s]?[:=]\s*(\S+))",
        std::regex::icase
    )
    // Паттерн для поиска имени списка: "LIST: adr_list.txt"
    , pattern_match_list_(
        R"((?:LIST|List|list)[s]?[:=]\s*(\S+))",
        std::regex::icase
    )
{}
// END_METHOD_RegexPatterns_Constructor

RegexPatterns::~RegexPatterns() = default;

// START_METHOD_RegexPatterns_FindIteration
// START_CONTRACT:
// PURPOSE: Поиск номера итерации в строке
// INPUTS: line - строка для поиска
// OUTPUTS: optional с номером итерации или nullopt
// KEYWORDS: [CONCEPT(6): Parsing; TECH(7): Regex]
// END_CONTRACT
std::optional<int> RegexPatterns::find_iteration(const std::string& line) const {
    return extract_number<int>(line, pattern_iteration_);
}
// END_METHOD_RegexPatterns_FindIteration

// START_METHOD_RegexPatterns_FindMatch
// START_CONTRACT:
// PURPOSE: Поиск количества совпадений в строке
// INPUTS: line - строка для поиска
// OUTPUTS: optional с количеством совпадений или nullopt
// KEYWORDS: [CONCEPT(6): Parsing; TECH(7): Regex]
// END_CONTRACT
std::optional<int> RegexPatterns::find_match(const std::string& line) const {
    return extract_number<int>(line, pattern_match_);
}
// END_METHOD_RegexPatterns_FindMatch

// START_METHOD_RegexPatterns_FindWallet
// START_CONTRACT:
// PURPOSE: Поиск количества кошельков в строке
// INPUTS: line - строка для поиска
// OUTPUTS: optional с количеством кошельков или nullopt
// KEYWORDS: [CONCEPT(6): Parsing; TECH(7): Regex]
// END_CONTRACT
std::optional<int> RegexPatterns::find_wallet(const std::string& line) const {
    return extract_number<int>(line, pattern_wallet_);
}
// END_METHOD_RegexPatterns_FindWallet

// START_METHOD_RegexPatterns_FindEntropy
// START_CONTRACT:
// PURPOSE: Поиск бит энтропии в строке
// INPUTS: line - строка для поиска
// OUTPUTS: optional с битами энтропии или nullopt
// KEYWORDS: [CONCEPT(6): Parsing; TECH(7): Regex]
// END_CONTRACT
std::optional<double> RegexPatterns::find_entropy(const std::string& line) const {
    return extract_number<double>(line, pattern_entropy_);
}
// END_METHOD_RegexPatterns_FindEntropy

// START_METHOD_RegexPatterns_FindStage
// START_CONTRACT:
// PURPOSE: Поиск стадии выполнения в строке
// INPUTS: line - строка для поиска
// OUTPUTS: optional со стадией или nullopt
// KEYWORDS: [CONCEPT(6): Parsing; TECH(7): Regex]
// END_CONTRACT
std::optional<std::string> RegexPatterns::find_stage(const std::string& line) const {
    return extract_string(line, pattern_stage_);
}
// END_METHOD_RegexPatterns_FindStage

// START_METHOD_RegexPatterns_FindError
// START_CONTRACT:
// PURPOSE: Поиск сообщения об ошибке в строке
// INPUTS: line - строка для поиска
// OUTPUTS: optional с текстом ошибки или nullopt
// KEYWORDS: [CONCEPT(6): Parsing; TECH(7): Regex]
// END_CONTRACT
std::optional<std::string> RegexPatterns::find_error(const std::string& line) const {
    return extract_string(line, pattern_error_);
}
// END_METHOD_RegexPatterns_FindError

// START_METHOD_RegexPatterns_FindProgress
// START_CONTRACT:
// PURPOSE: Поиск процента прогресса в строке
// INPUTS: line - строка для поиска
// OUTPUTS: optional с процентом прогресса или nullopt
// KEYWORDS: [CONCEPT(6): Parsing; TECH(7): Regex]
// END_CONTRACT
std::optional<double> RegexPatterns::find_progress(const std::string& line) const {
    return extract_number<double>(line, pattern_progress_);
}
// END_METHOD_RegexPatterns_FindProgress

// START_METHOD_RegexPatterns_FindAddress
// START_CONTRACT:
// PURPOSE: Поиск адреса Bitcoin в строке
// INPUTS: line - строка для поиска
// OUTPUTS: optional с адресом или nullopt
// KEYWORDS: [CONCEPT(6): Parsing; TECH(7): Regex]
// END_CONTRACT
std::optional<std::string> RegexPatterns::find_address(const std::string& line) const {
    auto result = extract_string(line, pattern_match_event_);
    if (!result.has_value()) {
        result = extract_string(line, pattern_match_address_);
    }
    return result;
}
// END_METHOD_RegexPatterns_FindAddress

// START_METHOD_RegexPatterns_FindMatchData
// START_CONTRACT:
// PURPOSE: Поиск всех данных события совпадения
// INPUTS: line - строка для поиска
// OUTPUTS: Вектор строк с найденными данными
// KEYWORDS: [CONCEPT(6): Parsing; TECH(7): Regex]
// END_CONTRACT
std::vector<std::string> RegexPatterns::find_match_data(const std::string& line) const {
    std::vector<std::string> results;
    
    // Поиск адреса
    auto address = find_address(line);
    if (address.has_value()) {
        results.push_back("address:" + address.value());
    }
    
    // Поиск имени кошелька
    auto wallet = extract_string(line, pattern_match_wallet_);
    if (wallet.has_value()) {
        results.push_back("wallet:" + wallet.value());
    }
    
    // Поиск имени списка
    auto list = extract_string(line, pattern_match_list_);
    if (list.has_value()) {
        results.push_back("list:" + list.value());
    }
    
    return results;
}
// END_METHOD_RegexPatterns_FindMatchData

// START_METHOD_RegexPatterns_Search
// START_CONTRACT:
// PURPOSE: Универсальный поиск по произвольному паттерну
// INPUTS: line - строка для поиска; pattern - regex паттерн
// OUTPUTS: optional с первой группой или nullopt
// KEYWORDS: [CONCEPT(6): Search; TECH(7): Regex]
// END_CONTRACT
std::optional<std::string> RegexPatterns::search(
    const std::string& line, 
    const std::string& pattern
) const try {
    std::regex rgx(pattern, std::regex::icase);
    return extract_string(line, rgx);
} catch (const std::regex_error&) {
    return std::nullopt;
}
// END_METHOD_RegexPatterns_Search

// START_METHOD_RegexPatterns_GetPatternNames
// START_CONTRACT:
// PURPOSE: Получение списка всех доступных паттернов
// OUTPUTS: Вектор с названиями паттернов
// KEYWORDS: [CONCEPT(5): Enumeration]
// END_CONTRACT
std::vector<std::string> RegexPatterns::get_pattern_names() const {
    return {
        "iteration",
        "match",
        "wallet",
        "entropy",
        "stage",
        "error",
        "progress",
        "match_event",
        "match_address",
        "match_wallet",
        "match_list"
    };
}
// END_METHOD_RegexPatterns_GetPatternNames

// START_METHOD_RegexPatterns_ValidatePattern
// START_CONTRACT:
// PURPOSE: Валидация regex паттерна
// INPUTS: pattern - строка с регулярным выражением
// OUTPUTS: true если паттерн валиден
// KEYWORDS: [CONCEPT(6): Validation; TECH(7): Regex]
// END_CONTRACT
bool RegexPatterns::validate_pattern(const std::string& pattern) {
    try {
        std::regex test(pattern);
        return true;
    } catch (const std::regex_error&) {
        return false;
    }
}
// END_METHOD_RegexPatterns_ValidatePattern

// START_METHOD_RegexPatterns_ExtractString
// START_CONTRACT:
// PURPOSE: Вспомогательный метод для извлечения строки по паттерну
// INPUTS: line - строка для поиска; rgx - предкомпилированный паттерн
// OUTPUTS: optional с найденной строкой
// KEYWORDS: [CONCEPT(6): Extraction; TECH(7): Regex]
// END_CONTRACT
std::optional<std::string> RegexPatterns::extract_string(
    const std::string& line, 
    const std::regex& rgx
) const {
    std::smatch match;
    if (std::regex_search(line, match, rgx)) {
        if (match.size() >= 2) {
            return match[1].str();
        }
    }
    return std::nullopt;
}
// END_METHOD_RegexPatterns_ExtractString

// START_METHOD_RegexPatterns_ExtractNumber
// START_CONTRACT:
// PURPOSE: Вспомогательный метод для извлечения числа по паттерну
// INPUTS: line - строка для поиска; rgx - предкомпилированный паттерн
// OUTPUTS: optional с найденным числом
// KEYWORDS: [CONCEPT(6): Extraction; TECH(7): Regex]
// END_CONTRACT
template<typename T>
std::optional<T> RegexPatterns::extract_number(
    const std::string& line, 
    const std::regex& rgx
) const {
    std::smatch match;
    if (std::regex_search(line, match, rgx)) {
        if (match.size() >= 2) {
            try {
                if constexpr (std::is_same_v<T, int>) {
                    return std::stoi(match[1].str());
                } else if constexpr (std::is_same_v<T, double>) {
                    return std::stod(match[1].str());
                }
            } catch (const std::exception&) {
                return std::nullopt;
            }
        }
    }
    return std::nullopt;
}
// END_METHOD_RegexPatterns_ExtractNumber

// Явная инстанциация шаблона для известных типов
template std::optional<int> RegexPatterns::extract_number<int>(
    const std::string&, 
    const std::regex&
) const;

template std::optional<double> RegexPatterns::extract_number<double>(
    const std::string&, 
    const std::regex&
) const;

//==============================================================================
// LogParser Implementation
//==============================================================================

// START_METHOD_LogParser_Constructor
// START_CONTRACT:
// PURPOSE: Конструктор парсера - инициализирует все компоненты
// INPUTS: log_file_path - путь к файлу; max_cache_size - размер кэша
// OUTPUTS: Инициализированный объект LogParser
// KEYWORDS: [CONCEPT(6): Initialization; TECH(7): FileIO]
// END_CONTRACT
LogParser::LogParser(const std::string& log_file_path, size_t max_cache_size)
    : log_file_path_(log_file_path)
    , max_cache_size_(max_cache_size)
    , cached_entries_()
    , last_file_position_(0)
    , last_parse_time_(0.0)
    , is_monitoring_(false)
    , regex_patterns_(std::make_unique<RegexPatterns>())
    , current_metrics_()
{
    if (logger) {
        logger->info("LogParser initialized with file: {}, cache_size: {}", 
                     log_file_path, max_cache_size);
    }
}
// END_METHOD_LogParser_Constructor

LogParser::~LogParser() = default;

// START_METHOD_LogParser_ParseFile
// START_CONTRACT:
// PURPOSE: Полный парсинг лог-файла
// OUTPUTS: Вектор всех распарсенных записей
// SIDE_EFFECTS: Читает весь файл, обновляет кэш и метрики
// KEYWORDS: [CONCEPT(7): Parsing; TECH(7): FileIO]
// END_CONTRACT
std::vector<ParsedEntry> LogParser::parse_file() {
    std::vector<ParsedEntry> entries;
    
    std::ifstream file(log_file_path_);
    if (!file.is_open()) {
        if (logger) {
            logger->warn("Failed to open file: {}", log_file_path_);
        }
        return entries;
    }
    
    std::string line;
    while (std::getline(file, line)) {
        auto entry = parse_line(line);
        if (entry) {
            entries.push_back(*entry);
            update_metrics(*entry);
        }
    }
    
    // Обновление кэша (последние max_cache_size записей)
    size_t start_idx = 0;
    if (entries.size() > max_cache_size_) {
        start_idx = entries.size() - max_cache_size_;
    }
    
    {
        std::unique_lock lock(mutex_);
        cached_entries_.clear();
        for (size_t i = start_idx; i < entries.size(); ++i) {
            cached_entries_.push_back(entries[i]);
        }
        
        last_file_position_ = static_cast<size_t>(file.tellg());
        last_parse_time_ = static_cast<double>(std::time(nullptr));
    }
    
    if (logger) {
        logger->debug("Parsed {} entries from file", entries.size());
    }
    
    return entries;
}
// END_METHOD_LogParser_ParseFile

// START_METHOD_LogParser_ParseNewLines
// START_CONTRACT:
// PURPOSE: Парсинг только новых строк для real-time мониторинга
// OUTPUTS: Вектор новых записей
// SIDE_EFFECTS: Читает только новые строки, обновляет позицию в файле
// KEYWORDS: [CONCEPT(7): IncrementalParsing; TECH(7): FileIO]
// END_CONTRACT
std::vector<ParsedEntry> LogParser::parse_new_lines() {
    std::vector<ParsedEntry> new_entries;
    
    std::ifstream file(log_file_path_);
    if (!file.is_open()) {
        return new_entries;
    }
    
    // Получение размера файла
    file.seekg(0, std::ios::end);
    std::streamsize file_size = file.tellg();
    file.seekg(0, std::ios::beg);
    
    size_t last_pos = last_file_position_.load();
    
    // Проверка ротации файла
    if (last_pos > static_cast<size_t>(file_size)) {
        last_pos = 0;
        std::unique_lock lock(mutex_);
        cached_entries_.clear();
        current_metrics_.reset();
        last_file_position_.store(0);
    }
    
    // Переход к последней позиции
    file.seekg(static_cast<std::streamoff>(last_pos));
    
    std::string line;
    while (std::getline(file, line)) {
        auto entry = parse_line(line);
        if (entry) {
            new_entries.push_back(*entry);
            update_metrics(*entry);
            
            std::unique_lock lock(mutex_);
            // Добавление в кэш с ограничением размера
            if (cached_entries_.size() >= max_cache_size_) {
                cached_entries_.pop_front();
            }
            cached_entries_.push_back(*entry);
        }
    }
    
    last_file_position_ = static_cast<size_t>(file.tellg());
    last_parse_time_ = static_cast<double>(std::time(nullptr));
    
    if (logger && !new_entries.empty()) {
        logger->debug("Parsed {} new lines", new_entries.size());
    }
    
    return new_entries;
}
// END_METHOD_LogParser_ParseNewLines

// START_METHOD_LogParser_ParseNewLinesAsync
// START_CONTRACT:
// PURPOSE: Асинхронный парсинг новых строк
// OUTPUTS: Future с вектором новых записей
// KEYWORDS: [CONCEPT(7): Async; TECH(6): Threading]
// END_CONTRACT
std::future<std::vector<ParsedEntry>> LogParser::parse_new_lines_async() {
    return std::async(std::launch::async, [this]() {
        return this->parse_new_lines();
    });
}
// END_METHOD_LogParser_ParseNewLinesAsync

// START_METHOD_LogParser_ParseLine
// START_CONTRACT:
// PURPOSE: Парсинг одной строки лога
// INPUTS: line - строка для парсинга
// OUTPUTS: optional с распарсенной записью или nullopt
// KEYWORDS: [CONCEPT(7): Parsing; TECH(7): Regex]
// END_CONTRACT
std::optional<ParsedEntry> LogParser::parse_line(const std::string& line) {
    if (line.empty() || !line.find_first_not_of(" \t\r\n")) {
        return std::nullopt;
    }
    
    // Парсинг timestamp
    double timestamp = parse_timestamp(line);
    ParsedEntry entry(timestamp, line);
    
    // Извлечение метрик через regex паттерны
    entry.iteration_count = regex_patterns_->find_iteration(line);
    entry.match_count = regex_patterns_->find_match(line);
    entry.wallet_count = regex_patterns_->find_wallet(line);
    entry.entropy_bits = regex_patterns_->find_entropy(line);
    entry.stage = regex_patterns_->find_stage(line);
    entry.error = regex_patterns_->find_error(line);
    
    return entry;
}
// END_METHOD_LogParser_ParseLine

// START_METHOD_LogParser_GetCurrentMetrics
// START_CONTRACT:
// PURPOSE: Получение текущих метрик
// OUTPUTS: LogMetrics с текущими значениями
// KEYWORDS: [CONCEPT(5): Accessor]
// END_CONTRACT
LogMetrics LogParser::get_current_metrics() const {
    std::shared_lock lock(mutex_);
    return current_metrics_;
}
// END_METHOD_LogParser_GetCurrentMetrics

// START_METHOD_LogParser_Reset
// START_CONTRACT:
// PURPOSE: Сброс состояния парсера
// OUTPUTS: Нет
// KEYWORDS: [CONCEPT(5): Reset]
// END_CONTRACT
void LogParser::reset() {
    std::unique_lock lock(mutex_);
    cached_entries_.clear();
    last_file_position_ = 0;
    last_parse_time_ = 0.0;
    is_monitoring_ = false;
    current_metrics_.reset();
    
    if (logger) {
        logger->info("LogParser reset complete");
    }
}
// END_METHOD_LogParser_Reset

// START_METHOD_LogParser_GetCachedEntries
// START_CONTRACT:
// PURPOSE: Получение кэшированных записей
// OUTPUTS: Вектор кэшированных записей
// KEYWORDS: [CONCEPT(5): Accessor]
// END_CONTRACT
std::vector<ParsedEntry> LogParser::get_cached_entries() const {
    std::shared_lock lock(mutex_);
    return std::vector<ParsedEntry>(cached_entries_.begin(), cached_entries_.end());
}
// END_METHOD_LogParser_GetCachedEntries

// START_METHOD_LogParser_GetIterationRate
// START_CONTRACT:
// PURPOSE: Вычисление скорости итераций
// INPUTS: window_seconds - временное окно в секундах
// OUTPUTS: Скорость итераций в секунду
// KEYWORDS: [CONCEPT(7): RateCalculation; TECH(6): Statistics]
// END_CONTRACT
double LogParser::get_iteration_rate(int window_seconds) const {
    std::shared_lock lock(mutex_);
    
    if (cached_entries_.size() < 2) {
        return 0.0;
    }
    
    double current_time = static_cast<double>(std::time(nullptr));
    double window_start = current_time - window_seconds;
    
    // Фильтрация записей в окне
    const ParsedEntry* first = nullptr;
    const ParsedEntry* last = nullptr;
    
    for (const auto& entry : cached_entries_) {
        if (entry.timestamp >= window_start && entry.iteration_count.has_value()) {
            if (!first) first = &entry;
            last = &entry;
        }
    }
    
    if (!first || !last || first == last) {
        return 0.0;
    }
    
    double time_diff = last->timestamp - first->timestamp;
    if (time_diff <= 0) {
        return 0.0;
    }
    
    int iter_diff = last->iteration_count.value() - first->iteration_count.value();
    return std::max(0.0, static_cast<double>(iter_diff) / time_diff);
}
// END_METHOD_LogParser_GetIterationRate

// START_METHOD_LogParser_GetErrors
// START_CONTRACT:
// PURPOSE: Получение всех ошибок из кэша
// OUTPUTS: Вектор словарей с ошибками и timestamp
// KEYWORDS: [CONCEPT(6): ErrorHandling; TECH(5): Filtering]
// END_CONTRACT
std::vector<std::unordered_map<std::string, std::string>> LogParser::get_errors() const {
    std::shared_lock lock(mutex_);
    std::vector<std::unordered_map<std::string, std::string>> errors;
    
    for (const auto& entry : cached_entries_) {
        if (entry.error.has_value()) {
            errors.push_back({
                {"timestamp", std::to_string(entry.timestamp)},
                {"error", entry.error.value()}
            });
        }
    }
    
    return errors;
}
// END_METHOD_LogParser_GetErrors

// START_METHOD_LogParser_GetStages
// START_CONTRACT:
// PURPOSE: Получение статистики по стадиям
// OUTPUTS: Словарь стадия: количество
// KEYWORDS: [CONCEPT(6): Statistics; TECH(5): Aggregation]
// END_CONTRACT
std::unordered_map<std::string, int> LogParser::get_stages() const {
    std::shared_lock lock(mutex_);
    std::unordered_map<std::string, int> stages;
    
    for (const auto& entry : cached_entries_) {
        if (entry.stage.has_value()) {
            const std::string& stage = entry.stage.value();
            stages[stage]++;
        }
    }
    
    return stages;
}
// END_METHOD_LogParser_GetStages

// START_METHOD_LogParser_GetProgress
// START_CONTRACT:
// PURPOSE: Получение последнего значения прогресса
// OUTPUTS: optional с процентом прогресса
// KEYWORDS: [CONCEPT(5): Accessor]
// END_CONTRACT
std::optional<double> LogParser::get_progress() const {
    std::shared_lock lock(mutex_);
    
    for (auto it = cached_entries_.rbegin(); it != cached_entries_.rend(); ++it) {
        auto progress = regex_patterns_->find_progress(it->raw_line);
        if (progress.has_value()) {
            return progress;
        }
    }
    return std::nullopt;
}
// END_METHOD_LogParser_GetProgress

// START_METHOD_LogParser_SearchPatterns
// START_CONTRACT:
// PURPOSE: Поиск записей по регулярному выражению
// INPUTS: pattern - регулярное выражение
// OUTPUTS: Вектор найденных записей
// KEYWORDS: [CONCEPT(7): Search; TECH(7): Regex]
// END_CONTRACT
std::vector<ParsedEntry> LogParser::search_patterns(const std::string& pattern) const {
    std::shared_lock lock(mutex_);
    std::vector<ParsedEntry> results;
    
    try {
        std::regex rgx(pattern, std::regex::icase);
        
        for (const auto& entry : cached_entries_) {
            if (std::regex_search(entry.raw_line, rgx)) {
                results.push_back(entry);
            }
        }
    } catch (const std::regex_error&) {
        // Невалидный паттерн - возвращаем пустой результат
    }
    
    return results;
}
// END_METHOD_LogParser_SearchPatterns

// START_METHOD_LogParser_ParseMatchEvent
// START_CONTRACT:
// PURPOSE: Парсинг события совпадения
// INPUTS: log_line - строка лога для парсинга
// OUTPUTS: optional со словарём данных о совпадении
// KEYWORDS: [CONCEPT(7): EventParsing; TECH(7): Regex]
// END_CONTRACT
std::optional<std::unordered_map<std::string, std::string>> 
LogParser::parse_match_event(const std::string& log_line) const {
    if (log_line.empty()) {
        return std::nullopt;
    }
    
    // Проверка наличия паттерна совпадения
    auto address = regex_patterns_->find_address(log_line);
    if (!address.has_value()) {
        return std::nullopt;
    }
    
    std::unordered_map<std::string, std::string> result;
    result["timestamp"] = std::to_string(parse_timestamp(log_line));
    result["address"] = address.value();
    result["raw_line"] = log_line;
    
    // Извлечение дополнительных данных
    auto match_data = regex_patterns_->find_match_data(log_line);
    for (const auto& data : match_data) {
        auto colon_pos = data.find(':');
        if (colon_pos != std::string::npos) {
            std::string key = data.substr(0, colon_pos);
            std::string value = data.substr(colon_pos + 1);
            result[key] = value;
        }
    }
    
    return result;
}
// END_METHOD_LogParser_ParseMatchEvent

// START_METHOD_LogParser_SetLogFile
// START_CONTRACT:
// PURPOSE: Установка нового пути к лог-файлу
// INPUTS: log_file_path - новый путь к файлу
// OUTPUTS: true если файл существует
// SIDE_EFFECTS: Сбрасывает состояние парсера
// KEYWORDS: [CONCEPT(6): FileManagement]
// END_CONTRACT
bool LogParser::set_log_file(const std::string& log_file_path) {
    if (!file_exists()) {
        return false;
    }
    
    log_file_path_ = log_file_path;
    reset();
    return true;
}
// END_METHOD_LogParser_SetLogFile

// START_METHOD_LogParser_GetFileInfo
// START_CONTRACT:
// PURPOSE: Получение информации о файле
// OUTPUTS: Словарь с информацией о файле
// KEYWORDS: [CONCEPT(5): Accessor]
// END_CONTRACT
std::unordered_map<std::string, std::string> LogParser::get_file_info() const {
    std::shared_lock lock(mutex_);
    std::unordered_map<std::string, std::string> info;
    
    if (!file_exists()) {
        info["exists"] = "false";
        return info;
    }
    
    info["exists"] = "true";
    info["path"] = log_file_path_;
    info["size_bytes"] = std::to_string(get_file_size());
    info["size_mb"] = std::to_string(static_cast<double>(get_file_size()) / (1024.0 * 1024.0));
    info["cached_entries"] = std::to_string(cached_entries_.size());
    info["last_parse_time"] = std::to_string(last_parse_time_.load());
    
    return info;
}
// END_METHOD_LogParser_GetFileInfo

// START_METHOD_LogParser_IsMonitoring
// START_CONTRACT:
// PURPOSE: Проверка состояния мониторинга
// OUTPUTS: true если идёт мониторинг
// KEYWORDS: [CONCEPT(5): StateCheck]
// END_CONTRACT
bool LogParser::is_monitoring() const {
    return is_monitoring_.load();
}
// END_METHOD_LogParser_IsMonitoring

// START_METHOD_LogParser_GetCacheSize
// START_CONTRACT:
// PURPOSE: Получение количества кэшированных записей
// OUTPUTS: Размер кэша
// KEYWORDS: [CONCEPT(5): Accessor]
// END_CONTRACT
size_t LogParser::get_cache_size() const {
    std::shared_lock lock(mutex_);
    return cached_entries_.size();
}
// END_METHOD_LogParser_GetCacheSize

// START_METHOD_LogParser_HasNewData
// START_CONTRACT:
// PURPOSE: Проверка наличия новых данных
// OUTPUTS: true если есть новые данные
// KEYWORDS: [CONCEPT(5): StateCheck]
// END_CONTRACT
bool LogParser::has_new_data() const {
    if (!file_exists()) {
        return false;
    }
    
    std::streamsize current_size = get_file_size();
    return static_cast<size_t>(current_size) > last_file_position_.load();
}
// END_METHOD_LogParser_HasNewData

// START_METHOD_LogParser_UpdateMetrics
// START_CONTRACT:
// PURPOSE: Обновление метрик из записи
// INPUTS: entry - запись для извлечения метрик
// OUTPUTS: Нет
// KEYWORDS: [CONCEPT(6): Update]
// END_CONTRACT
void LogParser::update_metrics(const ParsedEntry& entry) {
    current_metrics_.update_from_entry(entry);
    
    if (current_metrics_.iteration_count > 0) {
        is_monitoring_ = true;
    }
}
// END_METHOD_LogParser_UpdateMetrics

// START_METHOD_LogParser_ParseTimestamp
// START_CONTRACT:
// PURPOSE: Парсинг timestamp из строки
// INPUTS: line - строка для извлечения timestamp
// OUTPUTS: Unix timestamp
// KEYWORDS: [CONCEPT(6): Parsing; TECH(7): Regex]
// END_CONTRACT
double LogParser::parse_timestamp(const std::string& line) const {
    // Формат: YYYY-MM-DD HH:MM:SS
    std::regex ts_pattern{4}-\d{2}-\d{2}\s(R"((\d+\d{2}:\d{2}:\d{2}))");
    std::smatch match;
    
    if (std::regex_search(line, match, ts_pattern)) {
        std::string ts_str = match[1].str();
        
        // Ручной парсинг для избежания locale проблем
        int year, month, day, hour, minute, second;
        if (sscanf(ts_str.c_str(), "%d-%d-%d %d:%d:%d", 
                   &year, &month, &day, &hour, &minute, &second) == 6) {
            
            // Конвертация в Unix timestamp
            struct std::tm tm_val = {};
            tm_val.tm_year = year - 1900;
            tm_val.tm_mon = month - 1;
            tm_val.tm_mday = day;
            tm_val.tm_hour = hour;
            tm_val.tm_min = minute;
            tm_val.tm_sec = second;
            
            return static_cast<double>(std::mktime(&tm_val));
        }
    }
    
    // Если timestamp не найден - возвращаем текущее время
    return static_cast<double>(std::time(nullptr));
}
// END_METHOD_LogParser_ParseTimestamp

// START_METHOD_LogParser_FileExists
// START_CONTRACT:
// PURPOSE: Проверка существования файла
// OUTPUTS: true если файл существует
// KEYWORDS: [CONCEPT(5): Validation]
// END_CONTRACT
bool LogParser::file_exists() const {
    struct stat buffer;
    return (stat(log_file_path_.c_str(), &buffer) == 0);
}
// END_METHOD_LogParser_FileExists

// START_METHOD_LogParser_GetFileSize
// START_CONTRACT:
// PURPOSE: Получение размера файла
// OUTPUTS: Размер файла в байтах
// KEYWORDS: [CONCEPT(5): Accessor]
// END_CONTRACT
std::streamsize LogParser::get_file_size() const {
    struct stat st;
    if (stat(log_file_path_.c_str(), &st) == 0) {
        return st.st_size;
    }
    return 0;
}
// END_METHOD_LogParser_GetFileSize

//==============================================================================
// LogFilter Implementation
//==============================================================================

// START_CONSTRUCTOR_LogFilter
// START_CONTRACT:
// PURPOSE: Конструктор фильтра
// OUTPUTS: Инициализированный объект
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
LogFilter::LogFilter() {}
// END_CONSTRUCTOR_LogFilter

// START_METHOD_LogFilter_SetMinLevel
// START_CONTRACT:
// PURPOSE: Установка фильтра по минимальному уровню
// INPUTS: level - минимальный уровень для отображения
// OUTPUTS: Нет
// KEYWORDS: [CONCEPT(5): Configuration]
// END_CONTRACT
void LogFilter::set_min_level(Level level) {
    min_level_ = level;
}
// END_METHOD_LogFilter_SetMinLevel

// START_METHOD_LogFilter_SetTimeRange
// START_CONTRACT:
// PURPOSE: Установка фильтра по временному диапазону
// INPUTS: start_time - начальное время; end_time - конечное время
// OUTPUTS: Нет
// KEYWORDS: [CONCEPT(5): Configuration]
// END_CONTRACT
void LogFilter::set_time_range(double start_time, double end_time) {
    time_range_ = std::make_pair(start_time, end_time);
}
// END_METHOD_LogFilter_SetTimeRange

// START_METHOD_LogFilter_SetPattern
// START_CONTRACT:
// PURPOSE: Установка фильтра по шаблону
// INPUTS: pattern - регулярное выражение
// OUTPUTS: Нет
// KEYWORDS: [CONCEPT(6): Configuration; TECH(7): Regex]
// END_CONTRACT
void LogFilter::set_pattern(const std::string& pattern) {
    try {
        pattern_ = std::regex(pattern, std::regex::icase);
    } catch (const std::regex_error&) {
        pattern_ = std::nullopt;
    }
}
// END_METHOD_LogFilter_SetPattern

// START_METHOD_LogFilter_SetStages
// START_CONTRACT:
// PURPOSE: Установка фильтра по стадиям
// INPUTS: stages - вектор стадий для включения
// OUTPUTS: Нет
// KEYWORDS: [CONCEPT(5): Configuration]
// END_CONTRACT
void LogFilter::set_stages(const std::vector<std::string>& stages) {
    stages_ = stages;
}
// END_METHOD_LogFilter_SetStages

// START_METHOD_LogFilter_Apply
// START_CONTRACT:
// PURPOSE: Применение фильтра к вектору записей
// INPUTS: entries - вектор записей для фильтрации
// OUTPUTS: Отфильтрованный вектор записей
// KEYWORDS: [CONCEPT(6): Filtering; TECH(5): Algorithm]
// END_CONTRACT
std::vector<ParsedEntry> LogFilter::apply(const std::vector<ParsedEntry>& entries) const {
    std::vector<ParsedEntry> result;
    
    for (const auto& entry : entries) {
        // Фильтр по времени
        if (time_range_.has_value()) {
            if (entry.timestamp < time_range_->first || entry.timestamp > time_range_->second) {
                continue;
            }
        }
        
        // Фильтр по шаблону
        if (pattern_.has_value()) {
            if (!std::regex_search(entry.raw_line, pattern_.value())) {
                continue;
            }
        }
        
        // Фильтр по стадиям
        if (stages_.has_value() && entry.stage.has_value()) {
            const std::string& stage = entry.stage.value();
            bool found = false;
            for (const auto& s : stages_.value()) {
                if (s == stage) {
                    found = true;
                    break;
                }
            }
            if (!found) {
                continue;
            }
        }
        
        result.push_back(entry);
    }
    
    return result;
}
// END_METHOD_LogFilter_Apply

// START_METHOD_LogFilter_Reset
// START_CONTRACT:
// PURPOSE: Сброс всех фильтров
// OUTPUTS: Нет
// KEYWORDS: [CONCEPT(5): Reset]
// END_CONTRACT
void LogFilter::reset() {
    min_level_ = std::nullopt;
    time_range_ = std::nullopt;
    pattern_ = std::nullopt;
    stages_ = std::nullopt;
}
// END_METHOD_LogFilter_Reset

//==============================================================================
// LogAggregator Implementation
//==============================================================================

// START_CONSTRUCTOR_LogAggregator
// START_CONTRACT:
// PURPOSE: Конструктор агрегатора
// INPUTS: max_history - максимальный размер истории
// OUTPUTS: Инициализированный объект
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
LogAggregator::LogAggregator(size_t max_history)
    : max_history_(max_history)
{}
// END_CONSTRUCTOR_LogAggregator

// START_METHOD_LogAggregator_AddEntry
// START_CONTRACT:
// PURPOSE: Добавление записи для агрегации
// INPUTS: entry - запись для добавления
// OUTPUTS: Нет
// KEYWORDS: [CONCEPT(5): Insertion]
// END_CONTRACT
void LogAggregator::add_entry(const ParsedEntry& entry) {
    if (entry.iteration_count.has_value()) {
        iterations_.push_back(static_cast<double>(entry.iteration_count.value()));
    }
    if (entry.match_count.has_value()) {
        matches_.push_back(static_cast<double>(entry.match_count.value()));
    }
    if (entry.wallet_count.has_value()) {
        wallets_.push_back(static_cast<double>(entry.wallet_count.value()));
    }
    timestamps_.push_back(entry.timestamp);
    if (entry.stage.has_value()) {
        stages_.push_back(entry.stage.value());
    }
    
    // Ограничение размера истории
    if (iterations_.size() > max_history_) {
        iterations_.erase(iterations_.begin());
    }
    if (matches_.size() > max_history_) {
        matches_.erase(matches_.begin());
    }
    if (wallets_.size() > max_history_) {
        wallets_.erase(wallets_.begin());
    }
    if (timestamps_.size() > max_history_) {
        timestamps_.erase(timestamps_.begin());
    }
    if (stages_.size() > max_history_) {
        stages_.erase(stages_.begin());
    }
}
// END_METHOD_LogAggregator_AddEntry

// START_METHOD_LogAggregator_Clear
// START_CONTRACT:
// PURPOSE: Очистка всех данных
// OUTPUTS: Нет
// KEYWORDS: [CONCEPT(5): Cleanup]
// END_CONTRACT
void LogAggregator::clear() {
    iterations_.clear();
    matches_.clear();
    wallets_.clear();
    timestamps_.clear();
    stages_.clear();
}
// END_METHOD_LogAggregator_Clear

// START_METHOD_LogAggregator_ComputeStatistics
// START_CONTRACT:
// PURPOSE: Вычисление статистики для вектора значений
// INPUTS: values - вектор значений
// OUTPUTS: Statistics структура
// KEYWORDS: [CONCEPT(7): Statistics; TECH(6): Algorithm]
// END_CONTRACT
LogAggregator::Statistics LogAggregator::compute_statistics(const std::vector<double>& values) const {
    Statistics stats{};
    
    if (values.empty()) {
        return stats;
    }
    
    stats.count = values.size();
    stats.min = *std::min_element(values.begin(), values.end());
    stats.max = *std::max_element(values.begin(), values.end());
    
    double sum = std::accumulate(values.begin(), values.end(), 0.0);
    stats.avg = sum / values.size();
    
    // Медиана
    std::vector<double> sorted = values;
    std::sort(sorted.begin(), sorted.end());
    size_t mid = sorted.size() / 2;
    if (sorted.size() % 2 == 0) {
        stats.median = (sorted[mid - 1] + sorted[mid]) / 2.0;
    } else {
        stats.median = sorted[mid];
    }
    
    // Стандартное отклонение
    double sq_sum = 0.0;
    for (const auto& v : values) {
        sq_sum += (v - stats.avg) * (v - stats.avg);
    }
    stats.stddev = std::sqrt(sq_sum / values.size());
    
    return stats;
}
// END_METHOD_LogAggregator_ComputeStatistics

// START_METHOD_LogAggregator_GetIterationStats
// START_CONTRACT:
// PURPOSE: Получение статистики по итерациям
// OUTPUTS: Statistics структура
// KEYWORDS: [CONCEPT(6): Accessor]
// END_CONTRACT
LogAggregator::Statistics LogAggregator::get_iteration_stats() const {
    return compute_statistics(iterations_);
}
// END_METHOD_LogAggregator_GetIterationStats

// START_METHOD_LogAggregator_GetMatchStats
// START_CONTRACT:
// PURPOSE: Получение статистики по совпадениям
// OUTPUTS: Statistics структура
// KEYWORDS: [CONCEPT(6): Accessor]
// END_CONTRACT
LogAggregator::Statistics LogAggregator::get_match_stats() const {
    return compute_statistics(matches_);
}
// END_METHOD_LogAggregator_GetMatchStats

// START_METHOD_LogAggregator_GetWalletStats
// START_CONTRACT:
// PURPOSE: Получение статистики по кошелькам
// OUTPUTS: Statistics структура
// KEYWORDS: [CONCEPT(6): Accessor]
// END_CONTRACT
LogAggregator::Statistics LogAggregator::get_wallet_stats() const {
    return compute_statistics(wallets_);
}
// END_METHOD_LogAggregator_GetWalletStats

// START_METHOD_LogAggregator_GetStageDistribution
// START_CONTRACT:
// PURPOSE: Получение частотного распределения стадий
// OUTPUTS: Словарь стадия: частота
// KEYWORDS: [CONCEPT(6): Distribution]
// END_CONTRACT
std::unordered_map<std::string, size_t> LogAggregator::get_stage_distribution() const {
    std::unordered_map<std::string, size_t> distribution;
    
    for (const auto& stage : stages_) {
        distribution[stage]++;
    }
    
    return distribution;
}
// END_METHOD_LogAggregator_GetStageDistribution

// START_METHOD_LogAggregator_GetTimeRange
// START_CONTRACT:
// PURPOSE: Получение временного диапазона данных
// OUTPUTS: optional с парой (начало, конец) Unix timestamp
// KEYWORDS: [CONCEPT(6): Accessor]
// END_CONTRACT
std::optional<std::pair<double, double>> LogAggregator::get_time_range() const {
    if (timestamps_.empty()) {
        return std::nullopt;
    }
    
    double min_ts = *std::min_element(timestamps_.begin(), timestamps_.end());
    double max_ts = *std::max_element(timestamps_.begin(), timestamps_.end());
    
    return std::make_pair(min_ts, max_ts);
}
// END_METHOD_LogAggregator_GetTimeRange

// START_METHOD_LogAggregator_GetTotalCount
// START_CONTRACT:
// PURPOSE: Получение общего количества записей
// OUTPUTS: Количество записей
// KEYWORDS: [CONCEPT(5): Accessor]
// END_CONTRACT
size_t LogAggregator::get_total_count() const {
    return timestamps_.size();
}
// END_METHOD_LogAggregator_GetTotalCount

//==============================================================================
// LogWatcher Implementation
//==============================================================================

// START_CONSTRUCTOR_LogWatcher
// START_CONTRACT:
// PURPOSE: Конструктор наблюдателя
// INPUTS: log_file_path - путь к файлу; parser - указатель на парсер
// OUTPUTS: Инициализированный объект
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
LogWatcher::LogWatcher(
    const std::string& log_file_path,
    std::shared_ptr<LogParser> parser
)
    : log_file_path_(log_file_path)
    , parser_(std::move(parser))
    , is_running_(false)
    , check_interval_(1.0)
    , last_known_size_(0)
{}
// END_CONSTRUCTOR_LogWatcher

// START_DESTRUCTOR_LogWatcher
// START_CONTRACT:
// PURPOSE: Деструктор - останавливает наблюдение
// KEYWORDS: [CONCEPT(5): Cleanup]
// END_CONTRACT
LogWatcher::~LogWatcher() {
    stop();
}
// END_DESTRUCTOR_LogWatcher

// START_METHOD_LogWatcher_SetCallback
// START_CONTRACT:
// PURPOSE: Установка callback функции
// INPUTS: callback - функция для вызова при новых данных
// OUTPUTS: Нет
// KEYWORDS: [CONCEPT(6): Callback]
// END_CONTRACT
void LogWatcher::set_callback(Callback callback) {
    callback_ = std::move(callback);
}
// END_METHOD_LogWatcher_SetCallback

// START_METHOD_LogWatcher_Start
// START_CONTRACT:
// PURPOSE: Запуск наблюдения
// INPUTS: interval - интервал проверки в секундах
// OUTPUTS: Нет
// KEYWORDS: [CONCEPT(6): Startup; TECH(6): Threading]
// END_CONTRACT
void LogWatcher::start(double interval) {
    if (is_running_.load()) {
        return;
    }
    
    check_interval_ = interval;
    is_running_ = true;
    
    // Получение начального размера файла
    struct stat st;
    if (stat(log_file_path_.c_str(), &st) == 0) {
        last_known_size_ = st.st_size;
    }
    
    watch_thread_ = std::thread(&LogWatcher::watch_loop, this);
    
    if (logger) {
        logger->info("LogWatcher started for: {}", log_file_path_);
    }
}
// END_METHOD_LogWatcher_Start

// START_METHOD_LogWatcher_Stop
// START_CONTRACT:
// PURPOSE: Остановка наблюдения
// OUTPUTS: Нет
// KEYWORDS: [CONCEPT(6): Shutdown; TECH(6): Threading]
// END_CONTRACT
void LogWatcher::stop() {
    if (!is_running_.load()) {
        return;
    }
    
    is_running_ = false;
    
    if (watch_thread_.joinable()) {
        watch_thread_.join();
    }
    
    if (logger) {
        logger->info("LogWatcher stopped");
    }
}
// END_METHOD_LogWatcher_Stop

// START_METHOD_LogWatcher_IsRunning
// START_CONTRACT:
// PURPOSE: Проверка состояния наблюдения
// OUTPUTS: true если активно
// KEYWORDS: [CONCEPT(5): StateCheck]
// END_CONTRACT
bool LogWatcher::is_running() const {
    return is_running_.load();
}
// END_METHOD_LogWatcher_IsRunning

// START_METHOD_LogWatcher_CheckForUpdates
// START_CONTRACT:
// PURPOSE: Ручная проверка на новые данные
// OUTPUTS: Вектор новых записей
// KEYWORDS: [CONCEPT(6): Check]
// END_CONTRACT
std::vector<ParsedEntry> LogWatcher::check_for_updates() {
    return parser_->parse_new_lines();
}
// END_METHOD_LogWatcher_CheckForUpdates

// START_METHOD_LogWatcher_WatchLoop
// START_CONTRACT:
// PURPOSE: Внутренний цикл наблюдения
// KEYWORDS: [CONCEPT(5): Loop; TECH(6): Threading]
// END_CONTRACT
void LogWatcher::watch_loop() {
    while (is_running_.load()) {
        // Проверка размера файла
        struct stat st;
        if (stat(log_file_path_.c_str(), &st) == 0) {
            size_t current_size = st.st_size;
            
            if (current_size > last_known_size_) {
                // Есть новые данные
                auto new_entries = parser_->parse_new_lines();
                
                if (!new_entries.empty() && callback_) {
                    callback_(new_entries);
                }
                
                last_known_size_ = current_size;
            } else if (current_size < last_known_size_) {
                // Файл был ротирован
                last_known_size_ = 0;
            }
        }
        
        // Ожидание до следующей проверки
        std::this_thread::sleep_for(std::chrono::duration<double>(check_interval_));
    }
}
// END_METHOD_LogWatcher_WatchLoop
