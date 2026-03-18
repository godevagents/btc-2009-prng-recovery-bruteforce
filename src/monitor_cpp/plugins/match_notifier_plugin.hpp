// FILE: src/monitor_cpp/plugins/match_notifier_plugin.hpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Плагин уведомлений о найденных совпадениях для мониторинга генерации кошельков Bitcoin.
// Обеспечивает real-time уведомления при обнаружении совпадений с адресами из списка.
// SCOPE: Уведомления, история совпадений, desktop-уведомления, фильтрация
// INPUT: Метрики от генератора, события совпадений
// OUTPUT: Методы для работы с историей, экспорт, callback система
// KEYWORDS: [DOMAIN(9): Notifications; DOMAIN(8): RealTime; TECH(7): Plugin; CONCEPT(6): DesktopNotify]
// LINKS: [EXTENDS(8): IPlugin; USES_API(7): plugin_base]
// END_MODULE_CONTRACT

#ifndef MATCH_NOTIFIER_PLUGIN_HPP
#define MATCH_NOTIFIER_PLUGIN_HPP

//==============================================================================
// Plugin Base Headers
//==============================================================================
#include "plugin_base.hpp"

//==============================================================================
// Standard Library Headers
//==============================================================================
#include <string>
#include <vector>
#include <deque>
#include <functional>
#include <chrono>
#include <memory>
#include <optional>
#include <unordered_map>
#include <mutex>
#include <atomic>
#include <variant>

//==============================================================================
// Forward Declarations
//==============================================================================
class MatchNotifierPlugin;

//==============================================================================
// Константы Модуля
//==============================================================================

/**
 * @brief Имя плагина
 */
constexpr const char* MATCH_NOTIFIER_PLUGIN_NAME = "match_notifier";

/**
 * @brief Версия плагина
 */
constexpr const char* MATCH_NOTIFIER_PLUGIN_VERSION = "1.0.0";

/**
 * @brief Приоритет плагина (Этап 1 - уведомления)
 */
constexpr int MATCH_NOTIFIER_PLUGIN_PRIORITY = 20;

/**
 * @brief Максимальный размер истории совпадений (ring buffer)
 */
constexpr size_t MAX_MATCH_HISTORY = 50;

//==============================================================================
// ENUM: NotificationChannel
//==============================================================================
/**
 * @enum NotificationChannel
 * @brief Каналы уведомлений
 */
enum class NotificationChannel {
    CONSOLE,  ///< Консольный вывод
    FILE,     ///< Запись в файл
    DESKTOP,  ///< Desktop уведомление (notify-send)
    EMAIL     ///< Email уведомление (заглушка)
};

//==============================================================================
// ENUM: NotificationPriority
//==============================================================================
/**
 * @enum NotificationPriority
 * @brief Приоритет уведомлений
 */
enum class NotificationPriority {
    LOW,      ///< Низкий приоритет
    NORMAL,   ///< Обычный приоритет
    HIGH,     ///< Высокий приоритет
    CRITICAL  ///< Критический приоритет
};

//==============================================================================
// STRUCT: MatchInfo
//==============================================================================
/**
 * @struct MatchInfo
 * @brief Структура для хранения информации о найденном совпадении
 * 
 * CONTRACT:
 * PURPOSE: Хранение данных о найденном совпадении адреса
 * ATTRIBUTES:
 * - timestamp: время обнаружения совпадения
 * - iteration: номер итерации генерации
 * - match_number: порядковый номер совпадения
 * - address: найденный адрес Bitcoin
 * - private_key: приватный ключ (опционально)
 * - wallet_name: имя кошелька
 * - list_name: имя списка адресов
 * - priority: приоритет уведомления
 * KEYWORDS: [DOMAIN(9): MatchData; CONCEPT(8): DataStructure]
 */
struct MatchInfo {
    // Время обнаружения совпадения
    std::chrono::system_clock::time_point timestamp;
    
    // Номер итерации генерации
    int64_t iteration;
    
    // Порядковый номер совпадения
    int64_t match_number;
    
    // Найденный адрес Bitcoin
    std::string address;
    
    // Приватный ключ (опционально)
    std::optional<std::string> private_key;
    
    // Имя кошелька
    std::string wallet_name;
    
    // Имя списка адресов
    std::string list_name;
    
    // Приоритет уведомления
    NotificationPriority priority;
    
    /**
     * @brief Конструктор по умолчанию
     */
    MatchInfo();
    
    /**
     * @brief Конструктор с основными параметрами
     * @param iter номер итерации
     * @param match_num номер совпадения
     * @param addr адрес
     */
    MatchInfo(int64_t iter, int64_t match_num, const std::string& addr);
    
    /**
     * @brief Сериализация в JSON строку
     * @return JSON строка
     */
    std::string to_json() const;
    
    /**
     * @brief Строковое представление
     * @return читаемое представление
     */
    std::string to_string() const;
    
    /**
     * @brief Получение timestamp в читаемом формате ISO
     * @return timestamp в формате ISO 8601
     */
    std::string get_timestamp_string() const;
};

//==============================================================================
// STRUCT: MatchNotifierConfig
//==============================================================================
/**
 * @struct MatchNotifierConfig
 * @brief Структура конфигурации уведомлений плагина
 * 
 * CONTRACT:
 * PURPOSE: Хранение конфигурации уведомлений
 * ATTRIBUTES:
 * - desktop_enabled: включены ли desktop-уведомления
 * - sound_enabled: включены ли звуковые уведомления
 * - log_enabled: включено ли логирование уведомлений
 * - ui_enabled: включены ли UI уведомления
 * - cooldown_seconds: интервал кулдауна между уведомлениями
 * - min_priority: минимальный приоритет для уведомлений
 * - enabled_channels: список включённых каналов
 * KEYWORDS: [DOMAIN(8): Configuration; CONCEPT(7): Settings]
 */
struct MatchNotifierConfig {
    // Включены ли desktop-уведомления
    bool desktop_enabled;
    
    // Включены ли звуковые уведомления
    bool sound_enabled;
    
    // Включено ли логирование уведомлений
    bool log_enabled;
    
    // Включены ли UI уведомления
    bool ui_enabled;
    
    // Интервал кулдауна между уведомлениями (секунды)
    double cooldown_seconds;
    
    // Минимальный приоритет для уведомлений
    NotificationPriority min_priority;
    
    // Список включённых каналов
    std::vector<NotificationChannel> enabled_channels;
    
    /**
     * @brief Конструктор по умолчанию
     */
    MatchNotifierConfig();
    
    /**
     * @brief Конструктор с параметрами
     * @param desktop включены ли desktop уведомления
     * @param sound включены ли звуковые уведомления
     * @param log включено ли логирование
     * @param ui включены ли UI уведомления
     * @param cooldown кулдаун в секундах
     */
    MatchNotifierConfig(bool desktop, bool sound, bool log, bool ui, double cooldown = 5.0);
    
    /**
     * @brief Проверка включён ли хотя бы один тип уведомлений
     * @return true если хотя бы один тип включён
     */
    bool is_any_enabled() const;
    
    /**
     * @brief Сброс к значениям по умолчанию
     */
    void reset();
    
    /**
     * @brief Строковое представление конфигурации
     * @return читаемое представление
     */
    std::string to_string() const;
};

//==============================================================================
// STRUCT: MatchHistoryEntry
//==============================================================================
/**
 * @struct MatchHistoryEntry
 * @brief Запись в истории совпадений
 * 
 * CONTRACT:
 * PURPOSE: Хранение записи истории для агрегации
 * ATTRIBUTES:
 * - entry_id: ID записи
 * - match: информация о совпадении
 * - notification_sent: отправлено ли уведомление
 * - timestamp: время записи
 */
struct MatchHistoryEntry {
    uint64_t entry_id;
    MatchInfo match;
    bool notification_sent;
    std::chrono::system_clock::time_point timestamp;
    
    /**
     * @brief Конструктор по умолчанию
     */
    MatchHistoryEntry();
    
    /**
     * @brief Конструктор с параметрами
     * @param id ID записи
     * @param info информация о совпадении
     */
    MatchHistoryEntry(uint64_t id, const MatchInfo& info);
};

//==============================================================================
// CLASS: MatchNotifierPlugin
//==============================================================================

/**
 * @class MatchNotifierPlugin
 * @brief Плагин уведомлений о найденных совпадениях
 * 
 * CONTRACT:
 * PURPOSE: Обеспечивает real-time уведомления при обнаружении совпадений
 * ATTRIBUTES:
 * - m_info: PluginInfo — информация о плагине
 * - m_logger: PluginLogger — логгер плагина
 * - m_match_history: deque<MatchHistoryEntry> — история совпадений (ring buffer)
 * - m_total_matches: atomic<int64_t> — общее количество совпадений
 * - m_config: MatchNotifierConfig — конфигурация уведомлений
 * - m_last_notification_time: time_point — время последнего уведомления
 * - m_match_callbacks: vector<function> — callback функции
 * - m_data_mutex: mutex — мьютекс для thread-safety
 * 
 * METHODS:
 * - initialize(): инициализация плагина
 * - shutdown(): завершение работы
 * - on_metrics_update(metrics): обработка метрик
 * - on_match_found(matches, iteration): обработка совпадений
 * - on_start(path): начало сессии
 * - on_finish(metrics): завершение
 * - on_reset(): сброс
 * - get_match_history(): получение истории
 * - get_latest_match(): получение последнего совпадения
 * - get_total_matches(): получение общего количества
 * - export_matches(file_path): экспорт в JSON
 * - register_match_callback(): регистрация callback
 * - get_notification_config(): получение конфигурации
 * - set_notification_config(): установка конфигурации
 * 
 * KEYWORDS: [DOMAIN(9): Notifications; PATTERN(7): Plugin; TECH(7): RealTime]
 * LINKS: [EXTENDS(8): IPlugin]
 */
class MatchNotifierPlugin : public IPlugin {
public:
    //==========================================================================
    // Type Definitions
    //==========================================================================
    
    /** @brief Тип callback функции для уведомления о совпадениях */
    using MatchCallback = std::function<void(const MatchInfo&)>;
    
    //==========================================================================
    // Constructor / Destructor
    //==========================================================================
    
    /**
     * @brief Конструктор плагина уведомлений
     * 
     * CONTRACT:
     * OUTPUTS: Инициализированный объект MatchNotifierPlugin
     * SIDE_EFFECTS: Создаёт логгер; инициализирует структуры данных
     */
    MatchNotifierPlugin();
    
    /**
     * @brief Деструктор плагина
     */
    virtual ~MatchNotifierPlugin() override;
    
    //==========================================================================
    // IPlugin Implementation
    //==========================================================================
    
    /**
     * @brief Инициализация плагина
     * 
     * CONTRACT:
     * INPUTS: Нет
     * OUTPUTS: void
     * SIDE_EFFECTS: Переводит плагин в состояние ACTIVE
     */
    void initialize() override;
    
    /**
     * @brief Завершение работы плагина
     * 
     * CONTRACT:
     * INPUTS: Нет
     * OUTPUTS: void
     * SIDE_EFFECTS: Переводит плагин в состояние STOPPED
     */
    void shutdown() override;
    
    /**
     * @brief Получение информации о плагине
     * 
     * CONTRACT:
     * OUTPUTS: PluginInfo — информация о плагине
     */
    PluginInfo get_info() const override;
    
    /**
     * @brief Получение состояния плагина
     * 
     * CONTRACT:
     * OUTPUTS: PluginState — текущее состояние
     */
    PluginState get_state() const override;
    
    /**
     * @brief Обработка обновления метрик
     * 
     * CONTRACT:
     * INPUTS: const PluginMetrics& metrics — метрики
     * OUTPUTS: void
     */
    void on_metrics_update(const PluginMetrics& metrics) override;
    
    /**
     * @brief Обработка обнаружения совпадений
     * 
     * CONTRACT:
     * INPUTS: const MatchList& matches — список совпадений, int iteration — итерация
     * OUTPUTS: void
     * SIDE_EFFECTS: Добавление в историю; отправка уведомлений; вызов callbacks
     */
    void on_match_found(const MatchList& matches, int iteration) override;
    
    /**
     * @brief Обработчик запуска генератора
     * 
     * CONTRACT:
     * INPUTS: const std::string& selected_list_path — путь к списку
     * OUTPUTS: void
     */
    void on_start(const std::string& selected_list_path) override;
    
    /**
     * @brief Обработчик завершения генерации
     * 
     * CONTRACT:
     * INPUTS: const PluginMetrics& final_metrics — финальные метрики
     * OUTPUTS: void
     */
    void on_finish(const PluginMetrics& final_metrics) override;
    
    /**
     * @brief Обработчик сброса
     * 
     * CONTRACT:
     * INPUTS: Нет
     * OUTPUTS: void
     */
    void on_reset() override;
    
    //==========================================================================
    // Методы получения данных
    //==========================================================================
    
    /**
     * @brief Получение полной истории совпадений
     * 
     * CONTRACT:
     * OUTPUTS: std::vector<MatchHistoryEntry> — вектор всех записей
     */
    std::vector<MatchHistoryEntry> get_match_history() const;
    
    /**
     * @brief Получение последнего найденного совпадения
     * 
     * CONTRACT:
     * OUTPUTS: std::optional<MatchHistoryEntry> — последнее совпадение или nullopt
     */
    std::optional<MatchHistoryEntry> get_latest_match() const;
    
    /**
     * @brief Получение общего количества найденных совпадений
     * 
     * CONTRACT:
     * OUTPUTS: int64_t — общее количество совпадений
     */
    int64_t get_total_matches() const;
    
    /**
     * @brief Проверка активности мониторинга
     * 
     * CONTRACT:
     * OUTPUTS: bool — true если мониторинг активен
     */
    bool is_monitoring() const;
    
    //==========================================================================
    // Методы экспорта
    //==========================================================================
    
    /**
     * @brief Экспорт истории совпадений в JSON файл
     * 
     * CONTRACT:
     * INPUTS: const std::string& file_path — путь к файлу
     * OUTPUTS: bool — успешность экспорта
     * SIDE_EFFECTS: Создаёт файл на диске
     */
    bool export_matches(const std::string& file_path) const;
    
    //==========================================================================
    // Управление уведомлениями
    //==========================================================================
    
    /**
     * @brief Сброс истории совпадений и счётчиков
     * 
     * CONTRACT:
     * INPUTS: Нет
     * OUTPUTS: void
     * SIDE_EFFECTS: Очищает историю; сбрасывает счётчики
     */
    void reset_notifications();
    
    /**
     * @brief Получение текущей конфигурации уведомлений
     * 
     * CONTRACT:
     * OUTPUTS: const MatchNotifierConfig& — конфигурация
     */
    const MatchNotifierConfig& get_notification_config() const;
    
    /**
     * @brief Установка новой конфигурации уведомлений
     * 
     * CONTRACT:
     * INPUTS: const MatchNotifierConfig& config — новая конфигурация
     * OUTPUTS: void
     */
    void set_notification_config(const MatchNotifierConfig& config);
    
    /**
     * @brief Получение текстовой сводки о состоянии уведомлений
     * 
     * CONTRACT:
     * OUTPUTS: std::string — форматированная сводка
     */
    std::string get_notification_summary() const;
    
    /**
     * @brief Регистрация callback функции для уведомления о совпадениях
     * 
     * CONTRACT:
     * INPUTS: MatchCallback callback — функция обратного вызова
     * OUTPUTS: void
     */
    void register_match_callback(MatchCallback callback);
    
    //==========================================================================
    // Отправка уведомлений
    //==========================================================================
    
    /**
     * @brief Отправка уведомления о совпадении
     * 
     * CONTRACT:
     * INPUTS: const MatchInfo& match_info — информация о совпадении
     * OUTPUTS: bool — успешность отправки
     */
    bool send_notification(const MatchInfo& match_info);
    
    /**
     * @brief Логирование совпадения
     * 
     * CONTRACT:
     * INPUTS: const MatchInfo& match_info — информация о совпадении
     * OUTPUTS: void
     */
    void log_match(const MatchInfo& match_info);

private:
    //==========================================================================
    // Приватные методы
    //==========================================================================
    
    /**
     * @brief Добавление совпадения в историю
     * 
     * CONTRACT:
     * INPUTS: const MatchInfo& match_info — информация о совпадении
     * OUTPUTS: void
     * SIDE_EFFECTS: Добавляет в ring buffer; вызывает send_notifications; вызывает callbacks
     */
    void add_match(const MatchInfo& match_info);
    
    /**
     * @brief Отправка уведомлений через все каналы
     * 
     * CONTRACT:
     * INPUTS: const MatchInfo& match_info — информация о совпадении
     * OUTPUTS: void
     */
    void send_notifications(const MatchInfo& match_info);
    
    /**
     * @brief Проверка возможности отправки уведомления (кулдаун)
     * 
     * CONTRACT:
     * OUTPUTS: bool — true если можно отправлять уведомление
     */
    bool should_process_notification() const;
    
    /**
     * @brief Определение приоритета на основе итерации
     * 
     * CONTRACT:
     * INPUTS: int64_t iteration — номер итерации
     * OUTPUTS: NotificationPriority — определённый приоритет
     */
    NotificationPriority determine_priority(int64_t iteration) const;
    
    /**
     * @brief Генерация тестовой записи совпадения
     * 
     * CONTRACT:
     * INPUTS: int64_t iteration — номер итерации
     * OUTPUTS: MatchInfo — сгенерированная запись
     */
    MatchInfo generate_match_info(int64_t iteration, int64_t match_number) const;
    
    //==========================================================================
    // Приватные атрибуты
    //==========================================================================
    PluginInfo m_info;                                           ///< Информация о плагине
    PluginLogger m_logger;                                        ///< Логгер плагина
    
    std::deque<MatchHistoryEntry> m_match_history;                ///< История совпадений (ring buffer)
    std::atomic<int64_t> m_total_matches{0};                     ///< Общее количество совпадений
    std::atomic<bool> m_is_monitoring{false};                    ///< Флаг активности мониторинга
    
    MatchNotifierConfig m_config;                                ///< Конфигурация уведомлений
    std::chrono::system_clock::time_point m_last_notification_time;  ///< Время последнего уведомления
    
    std::vector<MatchCallback> m_match_callbacks;                ///< Callback функции
    mutable std::mutex m_data_mutex;                             ///< Мьютекс для thread-safety
    
    uint64_t m_entry_counter = 0;                                ///< Счётчик записей
    std::string m_current_list_path;                            ///< Текущий путь к списку
};

//==============================================================================
// Inline Helper Functions
//==============================================================================

/**
 * @brief Определение уровня серьёзности на основе номера итерации (free function)
 * 
 * CONTRACT:
 * INPUTS: int64_t iteration — номер итерации генерации
 * OUTPUTS: NotificationPriority — уровень приоритета
 * - iteration < 1000: LOW
 * - iteration < 10000: NORMAL
 * - iteration < 100000: HIGH
 * - iteration >= 100000: CRITICAL
 * KEYWORDS: [DOMAIN(8): Priority; CONCEPT(7): Classification]
 */
inline NotificationPriority determine_priority_level(int64_t iteration) {
    if (iteration < 1000) return NotificationPriority::LOW;
    if (iteration < 10000) return NotificationPriority::NORMAL;
    if (iteration < 100000) return NotificationPriority::HIGH;
    return NotificationPriority::CRITICAL;
}

//==============================================================================
// Type Definitions
//==============================================================================

/** @brief Тип умного указателя на плагин */
using MatchNotifierPluginPtr = std::shared_ptr<MatchNotifierPlugin>;

#endif // MATCH_NOTIFIER_PLUGIN_HPP
