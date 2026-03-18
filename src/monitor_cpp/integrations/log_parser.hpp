// FILE: src/monitor_cpp/integrations/log_parser.hpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: C++ модуль для парсинга и мониторинга лог-файлов генератора кошельков.
// Обеспечивает полный и инкрементальный парсинг логов, извлечение метрик,
// кэширование записей и поиск по паттернам. Оптимизирован для real-time мониторинга.
// SCOPE: Парсинг, кэширование, метрики, поиск, фильтрация
// INPUT: Путь к лог-файлу
// OUTPUT: Классы: LogParser, LogEntry, LogWatcher, LogFilter, LogAggregator
// KEYWORDS: [PATTERN(8): Parser; DOMAIN(9): LogParsing; CONCEPT(8): Incremental; TECH(7): FileIO; TECH(6): Threading]
// LINKS: [USES_API(7): spdlog; COMPOSES(8): ParsedEntry; COMPOSES(7): LogMetrics; COMPOSES(7): RegexPatterns]
// END_MODULE_CONTRACT

#ifndef LOG_PARSER_HPP
#define LOG_PARSER_HPP

//==============================================================================
// Standard Library Headers
//==============================================================================
#include <string>
#include <vector>
#include <deque>
#include <optional>
#include <regex>
#include <unordered_map>
#include <fstream>
#include <memory>
#include <mutex>
#include <shared_mutex>
#include <atomic>
#include <future>
#include <functional>
#include <chrono>
#include <sys/stat.h>

//==============================================================================
// Forward Declarations
//==============================================================================
class RegexPatterns;
class ParsedEntry;
class LogMetrics;

//==============================================================================
// ParsedEntry - Структура записи лога
//==============================================================================
/**
 * @struct ParsedEntry
 * @brief Структура для хранения одной записи лога.
 * 
 * Аналог Python dataclass LogEntry. Содержит timestamp, оригинальную строку
 * и опциональные поля для метрик (итерации, совпадения, кошельки, энтропия, стадия, ошибка).
 * 
 * @var timestamp Unix timestamp записи
 * @var raw_line Оригинальная строка лога
 * @var iteration_count Количество итераций (опционально)
 * @var match_count Количество совпадений (опционально)
 * @var wallet_count Количество кошельков (опционально)
 * @var entropy_bits Биты энтропии (опционально)
 * @var stage Текущая стадия выполнения (опционально)
 * @var error Сообщение об ошибке (опционально)
 */
struct ParsedEntry {
    // =========================================================================
    // PUBLIC ATTRIBUTES
    // =========================================================================
    
    /** Unix timestamp записи */
    double timestamp;
    
    /** Оригинальная строка лога */
    std::string raw_line;
    
    /** Количество итераций */
    std::optional<int> iteration_count;
    
    /** Количество совпадений */
    std::optional<int> match_count;
    
    /** Количество кошельков */
    std::optional<int> wallet_count;
    
    /** Биты энтропии */
    std::optional<double> entropy_bits;
    
    /** Текущая стадия выполнения */
    std::optional<std::string> stage;
    
    /** Сообщение об ошибке */
    std::optional<std::string> error;
    
    // =========================================================================
    // CONSTRUCTORS
    // =========================================================================
    
    /**
     * @brief Конструктор по умолчанию
     */
    ParsedEntry();
    
    /**
     * @brief Конструктор с базовыми параметрами
     * @param ts Unix timestamp
     * @param line Оригинальная строка лога
     */
    ParsedEntry(double ts, const std::string& line);
    
    /**
     * @brief Конструктор копирования
     */
    ParsedEntry(const ParsedEntry& other);
    
    /**
     * @brief Оператор присваивания копирования
     */
    ParsedEntry& operator=(const ParsedEntry& other);
    
    // =========================================================================
    // PUBLIC METHODS
    // =========================================================================
    
    /**
     * @brief Проверка, содержит ли запись ошибку
     * @return true если есть поле error
     */
    bool has_error() const;
    
    /**
     * @brief Проверка, содержит ли запись метрики итерации
     * @return true если есть поле iteration_count
     */
    bool has_iteration() const;
    
    /**
     * @brief Проверка, пустая ли запись (нет полезных данных)
     * @return true если запись не содержит значимых данных
     */
    bool is_empty() const;
    
    /**
     * @brief Получение строкового представления записи
     * @return Строковое представление для отладки
     */
    std::string to_string() const;
};

//==============================================================================
// LogMetrics - Структура метрик
//==============================================================================
/**
 * @struct LogMetrics
 * @brief Структура для хранения агрегированных метрик из логов.
 * 
 * Содержит текущие значения всех отслеживаемых метрик генератора кошельков:
 * итерации, совпадения, кошельки, энтропия, стадия.
 * 
 * @var iteration_count Текущее количество итераций
 * @var match_count Текущее количество совпадений
 * @var wallet_count Текущее количество кошельков
 * @var entropy_bits Текущее значение энтропии
 * @var stage Текущая стадия выполнения
 * @var is_monitoring Флаг активности мониторинга
 * @var last_update_time Время последнего обновления метрик
 * @var error_count Количество ошибок в логе
 */
struct LogMetrics {
    // =========================================================================
    // PUBLIC ATTRIBUTES
    // =========================================================================
    
    /** Текущее количество итераций */
    int iteration_count;
    
    /** Текущее количество совпадений */
    int match_count;
    
    /** Текущее количество кошельков */
    int wallet_count;
    
    /** Текущее значение энтропии */
    double entropy_bits;
    
    /** Текущая стадия выполнения */
    std::string stage;
    
    /** Флаг активности мониторинга */
    bool is_monitoring;
    
    /** Время последнего обновления метрик */
    double last_update_time;
    
    /** Количество ошибок в логе */
    int error_count;
    
    // =========================================================================
    // CONSTRUCTORS
    // =========================================================================
    
    /**
     * @brief Конструктор по умолчанию
     */
    LogMetrics();
    
    /**
     * @brief Конструктор копирования
     */
    LogMetrics(const LogMetrics& other);
    
    // =========================================================================
    // PUBLIC METHODS
    // =========================================================================
    
    /**
     * @brief Сброс метрик к начальным значениям
     */
    void reset();
    
    /**
     * @brief Обновление метрик из записи лога
     * @param entry Запись лога для извлечения метрик
     */
    void update_from_entry(const ParsedEntry& entry);
    
    /**
     * @brief Получение метрик в виде словаря
     * @return unordered_map с парами ключ-значение
     */
    std::unordered_map<std::string, std::string> to_dict() const;
    
    /**
     * @brief Получение строкового представления
     * @return Строковое представление для отладки
     */
    std::string to_string() const;
};

//==============================================================================
// RegexPatterns - Класс управления regex паттернами
//==============================================================================
/**
 * @class RegexPatterns
 * @brief Класс для управления предкомпилированными regex паттернами.
 * 
 * Инкапсулирует все regex паттерны для парсинга логов генератора кошельков.
 * Паттерны компилируются один раз при создании объекта для оптимизации производительности.
 */
class RegexPatterns {
public:
    // =========================================================================
    // CONSTRUCTORS
    // =========================================================================
    
    /**
     * @brief Конструктор по умолчанию - компилирует все паттерны
     */
    RegexPatterns();
    
    /**
     * @brief Деструктор
     */
    ~RegexPatterns();
    
    /**
     * @brief Конструктор копирования (удалён)
     */
    RegexPatterns(const RegexPatterns&) = delete;
    
    /**
     * @brief Оператор присваивания (удалён)
     */
    RegexPatterns& operator=(const RegexPatterns&) = delete;
    
    // =========================================================================
    // PUBLIC METHODS - PATTERN MATCHING
    // =========================================================================
    
    /**
     * @brief Поиск номера итерации в строке
     * @param line Строка для поиска
     * @return optional с номером итерации или nullopt
     */
    std::optional<int> find_iteration(const std::string& line) const;
    
    /**
     * @brief Поиск количества совпадений в строке
     * @param line Строка для поиска
     * @return optional с количеством совпадений или nullopt
     */
    std::optional<int> find_match(const std::string& line) const;
    
    /**
     * @brief Поиск количества кошельков в строке
     * @param line Строка для поиска
     * @return optional с количеством кошельков или nullopt
     */
    std::optional<int> find_wallet(const std::string& line) const;
    
    /**
     * @brief Поиск бит энтропии в строке
     * @param line Строка для поиска
     * @return optional с битами энтропии или nullopt
     */
    std::optional<double> find_entropy(const std::string& line) const;
    
    /**
     * @brief Поиск стадии выполнения в строке
     * @param line Строка для поиска
     * @return optional со стадией или nullopt
     */
    std::optional<std::string> find_stage(const std::string& line) const;
    
    /**
     * @brief Поиск сообщения об ошибке в строке
     * @param line Строка для поиска
     * @return optional с текстом ошибки или nullopt
     */
    std::optional<std::string> find_error(const std::string& line) const;
    
    /**
     * @brief Поиск процента прогресса в строке
     * @param line Строка для поиска
     * @return optional с процентом прогресса или nullopt
     */
    std::optional<double> find_progress(const std::string& line) const;
    
    /**
     * @brief Поиск адреса Bitcoin в строке
     * @param line Строка для поиска
     * @return optional с адресом или nullopt
     */
    std::optional<std::string> find_address(const std::string& line) const;
    
    /**
     * @brief Поиск всех данных события совпадения
     * @param line Строка для поиска
     * @return Вектор строк с найденными данными
     */
    std::vector<std::string> find_match_data(const std::string& line) const;
    
    // =========================================================================
    // PUBLIC METHODS - UTILITY
    // =========================================================================
    
    /**
     * @brief Универсальный поиск по произвольному паттерну
     * @param line Строка для поиска
     * @param pattern Регулярное выражение
     * @return optional с первой группой или nullopt
     */
    std::optional<std::string> search(const std::string& line, const std::string& pattern) const;
    
    /**
     * @brief Получение списка всех доступных паттернов
     * @return Вектор с названиями паттернов
     */
    std::vector<std::string> get_pattern_names() const;
    
    /**
     * @brief Валидация regex паттерна
     * @param pattern Строка с регулярным выражением
     * @return true если паттерн валиден
     */
    static bool validate_pattern(const std::string& pattern);
    
private:
    // =========================================================================
    // PRIVATE ATTRIBUTES - COMPILED REGEX PATTERNS
    // =========================================================================
    
    /** Паттерн для поиска итерации */
    std::regex pattern_iteration_;
    
    /** Паттерн для поиска совпадений */
    std::regex pattern_match_;
    
    /** Паттерн для поиска кошельков */
    std::regex pattern_wallet_;
    
    /** Паттерн для поиска энтропии */
    std::regex pattern_entropy_;
    
    /** Паттерн для поиска стадии */
    std::regex pattern_stage_;
    
    /** Паттерн для поиска ошибки */
    std::regex pattern_error_;
    
    /** Паттерн для поиска прогресса */
    std::regex pattern_progress_;
    
    /** Паттерн для поиска события совпадения */
    std::regex pattern_match_event_;
    
    /** Паттерн для поиска адреса */
    std::regex pattern_match_address_;
    
    /** Паттерн для поиска имени кошелька */
    std::regex pattern_match_wallet_;
    
    /** Паттерн для поиска имени списка */
    std::regex pattern_match_list_;
    
    // =========================================================================
    // PRIVATE METHODS
    // =========================================================================
    
    /**
     * @brief Вспомогательный метод для извлечения строки по паттерну
     * @param line Строка для поиска
     * @param rgx Предкомпилированный паттерн
     * @return optional с найденной строкой
     */
    std::optional<std::string> extract_string(
        const std::string& line, 
        const std::regex& rgx
    ) const;
    
    /**
     * @brief Вспомогательный метод для извлечения числа по паттерну
     * @tparam T Тип числа (int или double)
     * @param line Строка для поиска
     * @param rgx Предкомпилированный паттерн
     * @return optional с найденным числом
     */
    template<typename T>
    std::optional<T> extract_number(
        const std::string& line, 
        const std::regex& rgx
    ) const;
};

//==============================================================================
// LogParser - Основной класс парсера
//==============================================================================
/**
 * @class LogParser
 * @brief Парсер лог-файлов генератора кошельков.
 * 
 * Основной класс для парсинга логов генератора кошельков. Обеспечивает:
 * - Полный парсинг файла (parse_file)
 * - Инкрементальный парсинг для real-time мониторинга (parse_new_lines)
 * - Извлечение метрик (итерации, совпадения, кошельки, энтропия, стадия)
 * - Кэширование последних записей
 * - Поиск по регулярным выражениям
 * - Вычисление статистики (скорость итераций, ошибки, стадии)
 * 
 * @var log_file_path_ Путь к лог-файлу
 * @var max_cache_size_ Максимальный размер кэша
 * @var cached_entries_ Кэш записей (deque для эффективного добавления/удаления)
 * @var last_file_position_ Позиция в файле для инкрементального чтения
 * @var last_parse_time_ Время последнего парсинга
 * @var is_monitoring_ Флаг активности мониторинга
 * @var regex_patterns_ Предкомпилированные regex паттерны
 * @var current_metrics_ Текущие метрики
 * @var mutex_ Мьютекс для thread-safety
 */
class LogParser {
public:
    // =========================================================================
    // CONSTRUCTORS
    // =========================================================================
    
    /**
     * @brief Конструктор парсера
     * @param log_file_path Путь к лог-файлу (по умолчанию: logs/infinite_loop.log)
     * @param max_cache_size Максимальный размер кэша (по умолчанию: 1000)
     * 
     * @note Инициализирует regex паттерны при создании объекта
     */
    explicit LogParser(
        const std::string& log_file_path = "logs/infinite_loop.log",
        size_t max_cache_size = 1000
    );
    
    /**
     * @brief Деструктор
     */
    ~LogParser();
    
    // =========================================================================
    // PUBLIC METHODS - PARSING
    // =========================================================================
    
    /**
     * @brief Полный парсинг лог-файла
     * @return Вектор всех распарсенных записей
     * 
     * Читает весь файл и извлекает все записи. Обновляет внутренний кэш
     * и метрики. Подходит для начальной загрузки при старте мониторинга.
     * 
     * @side_effects Читает весь файл, обновляет кэш и метрики
     */
    std::vector<ParsedEntry> parse_file();
    
    /**
     * @brief Парсинг только новых строк
     * @return Вектор новых записей
     * 
     * Читает только строки, добавленные после последнего вызова.
     * Поддерживает ротацию файлов. Оптимизирован для real-time мониторинга.
     * 
     * @side_effects Читает только новые строки, обновляет позицию в файле
     */
    std::vector<ParsedEntry> parse_new_lines();
    
    /**
     * @brief Асинхронный парсинг новых строк
     * @return Future с вектором новых записей
     */
    std::future<std::vector<ParsedEntry>> parse_new_lines_async();
    
    /**
     * @brief Парсинг одной строки
     * @param line Строка для парсинга
     * @return optional с распарсенной записью или nullopt
     */
    std::optional<ParsedEntry> parse_line(const std::string& line);
    
    // =========================================================================
    // PUBLIC METHODS - METRICS
    // =========================================================================
    
    /**
     * @brief Получение текущих метрик
     * @return LogMetrics с текущими значениями
     */
    LogMetrics get_current_metrics() const;
    
    /**
     * @brief Сброс состояния парсера
     * 
     * Очищает кэш, сбрасывает метрики и позицию в файле.
     * Используется при смене файла или перезапуске мониторинга.
     */
    void reset();
    
    // =========================================================================
    // PUBLIC METHODS - CACHE
    // =========================================================================
    
    /**
     * @brief Получение кэшированных записей
     * @return Вектор кэшированных записей
     * 
     * @note Возвращает копию для безопасности
     */
    std::vector<ParsedEntry> get_cached_entries() const;
    
    // =========================================================================
    // PUBLIC METHODS - ANALYTICS
    // =========================================================================
    
    /**
     * @brief Вычисление скорости итераций
     * @param window_seconds Временное окно в секундах (по умолчанию: 60)
     * @return Скорость итераций в секунду
     */
    double get_iteration_rate(int window_seconds = 60) const;
    
    /**
     * @brief Получение всех ошибок из кэша
     * @return Вектор словарей с ошибками и timestamp
     */
    std::vector<std::unordered_map<std::string, std::string>> get_errors() const;
    
    /**
     * @brief Получение статистики по стадиям
     * @return Словарь стадия: количество
     */
    std::unordered_map<std::string, int> get_stages() const;
    
    /**
     * @brief Получение последнего значения прогресса
     * @return optional с процентом прогресса
     */
    std::optional<double> get_progress() const;
    
    // =========================================================================
    // PUBLIC METHODS - SEARCH
    // =========================================================================
    
    /**
     * @brief Поиск записей по регулярному выражению
     * @param pattern Регулярное выражение
     * @return Вектор найденных записей
     */
    std::vector<ParsedEntry> search_patterns(const std::string& pattern) const;
    
    // =========================================================================
    // PUBLIC METHODS - MATCH EVENTS
    // =========================================================================
    
    /**
     * @brief Парсинг события совпадения
     * @param log_line Строка лога для парсинга
     * @return optional со словарём данных о совпадении
     * 
     * Извлекает адрес, имя кошелька, имя списка из строки лога.
     */
    std::optional<std::unordered_map<std::string, std::string>> 
    parse_match_event(const std::string& log_line) const;
    
    // =========================================================================
    // PUBLIC METHODS - FILE MANAGEMENT
    // =========================================================================
    
    /**
     * @brief Установка нового пути к лог-файлу
     * @param log_file_path Новый путь к файлу
     * @return true если файл существует
     * 
     * @side_effects Сбрасывает состояние парсера
     */
    bool set_log_file(const std::string& log_file_path);
    
    /**
     * @brief Получение информации о файле
     * @return Словарь с информацией о файле
     */
    std::unordered_map<std::string, std::string> get_file_info() const;
    
    /**
     * @brief Проверка состояния мониторинга
     * @return true если идёт мониторинг
     */
    bool is_monitoring() const;
    
    // =========================================================================
    // PUBLIC METHODS - UTILITY
    // =========================================================================
    
    /**
     * @brief Получение количества кэшированных записей
     * @return Размер кэша
     */
    size_t get_cache_size() const;
    
    /**
     * @brief Проверка наличия новых данных
     * @return true если есть новые данные
     */
    bool has_new_data() const;

private:
    // =========================================================================
    // PRIVATE ATTRIBUTES
    // =========================================================================
    
    /** Путь к лог-файлу */
    std::string log_file_path_;
    
    /** Максимальный размер кэша */
    size_t max_cache_size_;
    
    /** Кэш записей (deque для O(1) добавления/удаления) */
    std::deque<ParsedEntry> cached_entries_;
    
    /** Позиция в файле для инкрементального чтения */
    std::atomic<size_t> last_file_position_;
    
    /** Время последнего парсинга */
    std::atomic<double> last_parse_time_;
    
    /** Флаг активности мониторинга */
    std::atomic<bool> is_monitoring_;
    
    /** Уникальный указатель на regex паттерны */
    std::unique_ptr<RegexPatterns> regex_patterns_;
    
    /** Текущие метрики */
    LogMetrics current_metrics_;
    
    /** Мьютекс для thread-safety */
    mutable std::shared_mutex mutex_;
    
    // =========================================================================
    // PRIVATE METHODS
    // =========================================================================
    
    /**
     * @brief Обновление метрик из записи
     * @param entry Запись для извлечения метрик
     */
    void update_metrics(const ParsedEntry& entry);
    
    /**
     * @brief Парсинг timestamp из строки
     * @param line Строка для извлечения timestamp
     * @return Unix timestamp
     */
    double parse_timestamp(const std::string& line) const;
    
    /**
     * @brief Проверка существования файла
     * @return true если файл существует
     */
    bool file_exists() const;
    
    /**
     * @brief Получение размера файла
     * @return Размер файла в байтах
     */
    std::streamsize get_file_size() const;
};

//==============================================================================
// LogFilter - Класс фильтрации записей
//==============================================================================
/**
 * @class LogFilter
 * @brief Класс для фильтрации записей лога по различным критериям.
 * 
 * Обеспечивает фильтрацию по уровню логирования, времени, шаблону и стадии.
 */
class LogFilter {
public:
    // =========================================================================
    // Types
    // =========================================================================
    
    enum class Level {
        DEBUG,
        INFO,
        WARNING,
        ERROR,
        CRITICAL
    };
    
    // =========================================================================
    // Constructors
    // =========================================================================
    
    /**
     * @brief Конструктор по умолчанию
     */
    LogFilter();
    
    // =========================================================================
    // Public Methods
    // =========================================================================
    
    /**
     * @brief Установка фильтра по минимальному уровню
     * @param level Минимальный уровень для отображения
     */
    void set_min_level(Level level);
    
    /**
     * @brief Установка фильтра по временному диапазону
     * @param start_time Начальное время (Unix timestamp)
     * @param end_time Конечное время (Unix timestamp)
     */
    void set_time_range(double start_time, double end_time);
    
    /**
     * @brief Установка фильтра по шаблону
     * @param pattern Регулярное выражение
     */
    void set_pattern(const std::string& pattern);
    
    /**
     * @brief Установка фильтра по стадиям
     * @param stages Вектор стадий для включения
     */
    void set_stages(const std::vector<std::string>& stages);
    
    /**
     * @brief Применение фильтра к вектору записей
     * @param entries Вектор записей для фильтрации
     * @return Отфильтрованный вектор записей
     */
    std::vector<ParsedEntry> apply(const std::vector<ParsedEntry>& entries) const;
    
    /**
     * @brief Сброс всех фильтров
     */
    void reset();
    
private:
    // =========================================================================
    // Private Attributes
    // =========================================================================
    
    std::optional<Level> min_level_;
    std::optional<std::pair<double, double>> time_range_;
    std::optional<std::regex> pattern_;
    std::optional<std::vector<std::string>> stages_;
};

//==============================================================================
// LogAggregator - Класс агрегации данных
//==============================================================================
/**
 * @class LogAggregator
 * @brief Класс для агрегации и статистической обработки данных из логов.
 * 
 * Обеспечивает вычисление различных статистик: минимум, максимум, среднее,
 * медиана, перцентили, тренды и т.д.
 */
class LogAggregator {
public:
    // =========================================================================
    // Types
    // =========================================================================
    
    struct Statistics {
        double min;
        double max;
        double avg;
        double median;
        double stddev;
        size_t count;
    };
    
    // =========================================================================
    // Constructors
    // =========================================================================
    
    /**
     * @brief Конструктор агрегатора
     * @param max_history Максимальный размер истории для агрегации
     */
    explicit LogAggregator(size_t max_history = 10000);
    
    // =========================================================================
    // Public Methods
    // =========================================================================
    
    /**
     * @brief Добавление записи для агрегации
     * @param entry Запись для добавления
     */
    void add_entry(const ParsedEntry& entry);
    
    /**
     * @brief Очистка всех данных
     */
    void clear();
    
    /**
     * @brief Получение статистики по итерациям
     * @return Statistics структура
     */
    Statistics get_iteration_stats() const;
    
    /**
     * @brief Получение статистики по совпадениям
     * @return Statistics структура
     */
    Statistics get_match_stats() const;
    
    /**
     * @brief Получение статистики по кошелькам
     * @return Statistics структура
     */
    Statistics get_wallet_stats() const;
    
    /**
     * @brief Получение частотного распределения стадий
     * @return Словарь стадия: частота
     */
    std::unordered_map<std::string, size_t> get_stage_distribution() const;
    
    /**
     * @brief Получение временного диапазона данных
     * @return Пара (начало, конец) Unix timestamp
     */
    std::optional<std::pair<double, double>> get_time_range() const;
    
    /**
     * @brief Получение общего количества записей
     * @return Количество записей
     */
    size_t get_total_count() const;
    
private:
    // =========================================================================
    // Private Methods
    // =========================================================================
    
    /**
     * @brief Вычисление статистики для вектора значений
     * @param values Вектор значений
     * @return Statistics структура
     */
    Statistics compute_statistics(const std::vector<double>& values) const;
    
    // =========================================================================
    // Private Attributes
    // =========================================================================
    
    size_t max_history_;
    std::vector<double> iterations_;
    std::vector<double> matches_;
    std::vector<double> wallets_;
    std::vector<double> timestamps_;
    std::vector<std::string> stages_;
};

//==============================================================================
// LogWatcher - Класс наблюдателя за файлом
//==============================================================================
/**
 * @class LogWatcher
 * @brief Класс для отслеживания изменений в лог-файле.
 * 
 * Обеспечивает автоматическое обнаружение новых данных и уведомление
 * через callback функцию.
 */
class LogWatcher {
public:
    // =========================================================================
    // Types
    // =========================================================================
    
    using Callback = std::function<void(const std::vector<ParsedEntry>&)>;
    
    // =========================================================================
    // Constructors
    // =========================================================================
    
    /**
     * @brief Конструктор наблюдателя
     * @param log_file_path Путь к файлу для наблюдения
     * @param parser Указатель на парсер
     */
    explicit LogWatcher(
        const std::string& log_file_path,
        std::shared_ptr<LogParser> parser
    );
    
    /**
     * @brief Деструктор
     */
    ~LogWatcher();
    
    // =========================================================================
    // Public Methods
    // =========================================================================
    
    /**
     * @brief Установка callback функции
     * @param callback Функция для вызова при новых данных
     */
    void set_callback(Callback callback);
    
    /**
     * @brief Запуск наблюдения
     * @param interval Интервал проверки в секундах
     */
    void start(double interval = 1.0);
    
    /**
     * @brief Остановка наблюдения
     */
    void stop();
    
    /**
     * @brief Проверка состояния наблюдения
     * @return true если активно
     */
    bool is_running() const;
    
    /**
     * @brief Ручная проверка на новые данные
     * @return Вектор новых записей
     */
    std::vector<ParsedEntry> check_for_updates();

private:
    // =========================================================================
    // Private Methods
    // =========================================================================
    
    /**
     * @brief Внутренний цикл наблюдения
     */
    void watch_loop();
    
    // =========================================================================
    // Private Attributes
    // =========================================================================
    
    std::string log_file_path_;
    std::shared_ptr<LogParser> parser_;
    Callback callback_;
    std::atomic<bool> is_running_;
    std::thread watch_thread_;
    double check_interval_;
    size_t last_known_size_;
};

#endif // LOG_PARSER_HPP
