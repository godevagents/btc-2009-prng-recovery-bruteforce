// FILE: src/monitor_cpp/plugins/final_stats_plugin.hpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Плагин финальной статистики для мониторинга генерации кошельков Bitcoin. Отображает итоговую сводку после завершения: итерации, совпадения, время работы, производительность.
// SCOPE: Этап 3 мониторинга, финальная статистика, экспорт данных в JSON/CSV/TXT
// INPUT: Финальные метрики от генератора (iteration_count, wallet_count, match_count)
// OUTPUT: Структуры данных для отображения, методы экспорта
// KEYWORDS: [DOMAIN(9): FinalStats; DOMAIN(8): Statistics; TECH(7): Plugin; CONCEPT(6): Export]
// LINKS: [EXTENDS(8): IPlugin; USES_API(7): plugin_base; USES_API(6): metrics]
// END_MODULE_CONTRACT

#ifndef FINAL_STATS_PLUGIN_HPP
#define FINAL_STATS_PLUGIN_HPP

//==============================================================================
// Plugin Base Headers
//==============================================================================
#include "plugin_base.hpp"

//==============================================================================
// Standard Library Headers
//==============================================================================
#include <string>
#include <vector>
#include <map>
#include <atomic>
#include <mutex>
#include <chrono>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <optional>

//==============================================================================
// Forward Declarations
//==============================================================================
class FinalStatsPlugin;

//==============================================================================
// Константы Модуля
//==============================================================================

/**
 * @brief Имя плагина
 */
constexpr const char* FINAL_STATS_PLUGIN_NAME = "final_stats";

/**
 * @brief Версия плагина
 */
constexpr const char* FINAL_STATS_PLUGIN_VERSION = "1.0.0";

/**
 * @brief Приоритет плагина (Этап 3 - финальная статистика)
 */
constexpr int FINAL_STATS_PLUGIN_PRIORITY = 30;

//==============================================================================
// ENUM: ExportFormat
//==============================================================================
/**
 * @enum ExportFormat
 * @brief Форматы экспорта данных
 */
enum class ExportFormat {
    JSON,      ///< JSON формат
    CSV,       ///< CSV формат (Excel совместимый)
    TXT,       ///< Текстовый читаемый формат
    MARKDOWN   ///< Markdown таблица
};

//==============================================================================
// STRUCT: FinalStatistics
//==============================================================================
/**
 * @struct FinalStatistics
 * @brief Структура для хранения финальной статистики генерации кошельков
 * 
 * CONTRACT:
 * PURPOSE: Хранение всех метрик завершённой генерации
 * ATTRIBUTES:
 * - iteration_count: uint64_t — общее количество итераций
 * - match_count: uint64_t — количество найденных совпадений
 * - wallet_count: uint64_t — количество сгенерированных кошельков
 * - runtime_seconds: double — время работы в секундах
 * - start_timestamp: double — timestamp начала
 * - end_timestamp: double — timestamp завершения
 * - iterations_per_second: double — скорость итераций
 * - wallets_per_second: double — скорость генерации кошельков
 * - avg_iteration_time_ms: double — среднее время итерации в мс
 * - list_path: std::string — путь к списку
 * - custom_metrics: std::map — дополнительные метрики
 * KEYWORDS: [DOMAIN(9): Statistics; DATA(8): Aggregate; CONCEPT(7): Metrics]
 */
struct FinalStatistics {
    // Основные счетчики
    uint64_t iteration_count = 0;
    uint64_t match_count = 0;
    uint64_t wallet_count = 0;
    
    // Временные метрики
    double runtime_seconds = 0.0;
    double start_timestamp = 0.0;
    double end_timestamp = 0.0;
    
    // Производительность
    double iterations_per_second = 0.0;
    double wallets_per_second = 0.0;
    double avg_iteration_time_ms = 0.0;
    
    // Дополнительная информация
    std::string list_path;
    std::map<std::string, std::string> custom_metrics;
    
    /**
     * @brief Конструктор по умолчанию
     */
    FinalStatistics() = default;
    
    /**
     * @brief Проверка доступности данных
     * @return true если есть какие-либо данные
     */
    bool is_available() const;
    
    /**
     * @brief Очистка всех данных
     */
    void reset();
    
    /**
     * @brief Преобразование в PluginMetrics для совместимости
     * @return PluginMetrics словарь
     */
    PluginMetrics to_plugin_metrics() const;
};

//==============================================================================
// STRUCT: SessionHistory
//==============================================================================
/**
 * @struct SessionHistory
 * @brief История сессий
 * 
 * CONTRACT:
 * PURPOSE: Хранение истории сессий для агрегации
 * ATTRIBUTES:
 * - session_id: uint32_t — ID сессии
 * - stats: FinalStatistics — статистика сессии
 * - timestamp: time_point — временная метка
 */
struct SessionHistory {
    uint32_t session_id = 0;
    FinalStatistics stats;
    std::chrono::system_clock::time_point timestamp;
    
    /**
     * @brief Конструктор по умолчанию
     */
    SessionHistory() = default;
    
    /**
     * @brief Конструктор с параметрами
     * @param id ID сессии
     * @param statistics статистика сессии
     */
    SessionHistory(uint32_t id, const FinalStatistics& statistics);
};

//==============================================================================
// CLASS: FinalStatsPlugin
//==============================================================================

/**
 * @class FinalStatsPlugin
 * @brief Плагин финальной статистики
 * 
 * CONTRACT:
 * PURPOSE: Плагин финальной статистики для отображения итоговой сводки после завершения генерации
 * ATTRIBUTES:
 * - m_info: PluginInfo — информация о плагине
 * - m_logger: PluginLogger — логгер плагина
 * - m_final_stats: FinalStatistics — финальная статистика
 * - m_start_time: optional<time_point> — время начала сессии
 * - m_is_complete: atomic<bool> — флаг завершения
 * - m_session_history: vector<SessionHistory> — история сессий
 * - m_data_mutex: mutex — мьютекс для thread-safety
 * 
 * METHODS:
 * - initialize(): инициализация плагина
 * - shutdown(): завершение работы
 * - on_start(path): начало сессии
 * - on_finish(metrics): завершение генерации
 * - on_reset(): сброс
 * - get_final_metrics(): получение метрик
 * - get_summary(): получение текстовой сводки
 * - export_json/csv/txt(): экспорт в различные форматы
 * - get_performance_analysis(): анализ производительности
 * 
 * KEYWORDS: [DOMAIN(9): FinalStats; PATTERN(7): Plugin; TECH(7): Export]
 * LINKS: [EXTENDS(8): IPlugin]
 */
class FinalStatsPlugin : public IPlugin {
public:
    //==========================================================================
    // Constructor / Destructor
    //==========================================================================
    
    /**
     * @brief Конструктор плагина финальной статистики
     * 
     * CONTRACT:
     * OUTPUTS: Инициализированный объект FinalStatsPlugin
     * SIDE_EFFECTS: Создаёт логгер; инициализирует структуры данных
     */
    FinalStatsPlugin();
    
    /**
     * @brief Деструктор плагина
     */
    virtual ~FinalStatsPlugin() override;
    
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
    
    //==========================================================================
    // Event Handlers
    //==========================================================================
    
    /**
     * @brief Обработка обновления метрик (заглушка - не используется на этом этапе)
     * 
     * CONTRACT:
     * INPUTS: const PluginMetrics& metrics — метрики
     * OUTPUTS: void
     */
    void on_metrics_update(const PluginMetrics& metrics) override;
    
    /**
     * @brief Обработчик запуска генератора кошельков
     * 
     * CONTRACT:
     * INPUTS: const std::string& selectedListPath — путь к списку
     * OUTPUTS: void
     * SIDE_EFFECTS: Сброс статистики; фиксация времени начала
     */
    void on_start(const std::string& selected_list_path) override;
    
    /**
     * @brief Обработчик завершения генерации кошельков
     * 
     * CONTRACT:
     * INPUTS: const PluginMetrics& finalMetrics — финальные метрики
     * OUTPUTS: void
     * SIDE_EFFECTS: Фиксация финальных метрик; вычисление производных показателей
     */
    void on_finish(const PluginMetrics& final_metrics) override;
    
    /**
     * @brief Обработчик сброса генератора
     * 
     * CONTRACT:
     * INPUTS: Нет
     * OUTPUTS: void
     * SIDE_EFFECTS: Сброс внутреннего состояния
     */
    void on_reset() override;
    
    //==========================================================================
    // Методы получения данных
    //==========================================================================
    
    /**
     * @brief Получить финальные метрики
     * 
     * CONTRACT:
     * OUTPUTS: FinalStatistics — структура с финальной статистикой
     */
    FinalStatistics get_final_metrics() const;
    
    /**
     * @brief Получить текстовую сводку
     * 
     * CONTRACT:
     * OUTPUTS: std::string — форматированная строка сводки
     */
    std::string get_summary() const;
    
    /**
     * @brief Получить историю сессий
     * 
     * CONTRACT:
     * OUTPUTS: std::vector<SessionHistory> — вектор записей истории
     */
    std::vector<SessionHistory> get_session_history() const;
    
    /**
     * @brief Получить анализ производительности
     * 
     * CONTRACT:
     * OUTPUTS: PluginMetrics — словарь с показателями производительности
     */
    PluginMetrics get_performance_analysis() const;
    
    /**
     * @brief Проверить завершение
     * 
     * CONTRACT:
     * OUTPUTS: bool — true если генерация завершена
     */
    bool is_complete() const;
    
    //==========================================================================
    // Методы экспорта
    //==========================================================================
    
    /**
     * @brief Экспорт в JSON файл
     * 
     * CONTRACT:
     * INPUTS: const std::string& file_path — путь к файлу
     * OUTPUTS: bool — true при успехе
     * SIDE_EFFECTS: Создаёт файл на диске
     */
    bool export_to_json(const std::string& file_path);
    
    /**
     * @brief Экспорт в CSV файл
     * 
     * CONTRACT:
     * INPUTS: const std::string& file_path — путь к файлу
     * OUTPUTS: bool — true при успехе
     * SIDE_EFFECTS: Создаёт UTF-8 BOM файл для Excel
     */
    bool export_to_csv(const std::string& file_path);
    
    /**
     * @brief Экспорт в TXT файл
     * 
     * CONTRACT:
     * INPUTS: const std::string& file_path — путь к файлу
     * OUTPUTS: std::string — путь к файлу или сообщение об ошибке
     * SIDE_EFFECTS: Создаёт форматированный текстовый файл
     */
    std::string export_to_txt(const std::string& file_path);
    
    /**
     * @brief Универсальный экспорт
     * 
     * CONTRACT:
     * INPUTS: ExportFormat format — формат, const std::string& file_path — путь
     * OUTPUTS: bool — true при успехе
     */
    bool export_to_file(ExportFormat format, const std::string& file_path);
    
    //==========================================================================
    // Управление состоянием
    //==========================================================================

    /**
     * @brief Сброс состояния
     * 
     * CONTRACT:
     * INPUTS: Нет
     * OUTPUTS: void
     * SIDE_EFFECTS: Очищает все данные
     */
    void reset_stats();
    
    /**
     * @brief Добавить сессию в историю
     * 
     * CONTRACT:
     * INPUTS: const FinalStatistics& session_stats — статистика сессии
     * OUTPUTS: void
     */
    void add_session(const FinalStatistics& session_stats);
    
    /**
     * @brief Получить общую статистику по всем сессиям
     * 
     * CONTRACT:
     * OUTPUTS: FinalStatistics — агрегированная статистика
     */
    FinalStatistics get_total_statistics() const;

private:
    //==========================================================================
    // Приватные методы
    //==========================================================================
    
    /**
     * @brief Вычисление производных метрик
     * 
     * CONTRACT:
     * INPUTS: Нет
     * OUTPUTS: void
     * SIDE_EFFECTS: Обновляет поля iterations_per_second, wallets_per_second, avg_iteration_time_ms
     */
    void calculate_derived_metrics();
    
    /**
     * @brief Форматирование времени
     * 
     * CONTRACT:
     * INPUTS: double seconds — время в секундах
     * OUTPUTS: std::string — отформатированная строка HH:MM:SS
     */
    std::string format_time(double seconds) const;
    
    /**
     * @brief Извлечение метрики из PluginMetrics
     * 
     * CONTRACT:
     * INPUTS: const PluginMetrics& metrics, const std::string& key, T default_value
     * OUTPUTS: T — значение метрики или значение по умолчанию
     */
    template<typename T>
    T get_metric_value(const PluginMetrics& metrics, const std::string& key, T default_value) const;
    
    //==========================================================================
    // Приватные атрибуты
    //==========================================================================
    PluginInfo m_info;                                      ///< Информация о плагине
    PluginLogger m_logger;                                   ///< Логгер плагина
    
    FinalStatistics m_final_stats;                           ///< Финальная статистика
    std::optional<std::chrono::steady_clock::time_point> m_start_time;  ///< Время начала
    std::atomic<bool> m_is_complete{false};                 ///< Флаг завершения
    
    std::vector<SessionHistory> m_session_history;            ///< История сессий
    mutable std::mutex m_data_mutex;                         ///< Мьютекс для thread-safety
    
    uint32_t m_session_counter = 0;                          ///< Счётчик сессий
};

//==============================================================================
// Типы указателей
//==============================================================================

/** @brief Тип умного указателя на плагин */
using FinalStatsPluginPtr = std::shared_ptr<FinalStatsPlugin>;

#endif // FINAL_STATS_PLUGIN_HPP
