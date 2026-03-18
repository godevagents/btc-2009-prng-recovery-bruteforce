// FILE: src/monitor_cpp/plugins/final_stats_plugin.cpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Реализация плагина финальной статистики
// SCOPE: Методы класса FinalStatsPlugin, обработка метрик, экспорт данных
// KEYWORDS: [DOMAIN(9): FinalStats; TECH(7): Export; TECH(6): C++17]
// END_MODULE_CONTRACT

#include "final_stats_plugin.hpp"
#include <algorithm>
#include <ctime>

//==============================================================================
// IMPLEMENTATION: FinalStatistics
//==============================================================================

// START_FUNCTION_FinalStatistics_IsAvailable
// START_CONTRACT:
// PURPOSE: Проверка доступности данных
// OUTPUTS: bool — true если есть данные
// END_CONTRACT
bool FinalStatistics::is_available() const {
    return iteration_count > 0 || match_count > 0 || wallet_count > 0;
}
// END_FUNCTION_FinalStatistics_IsAvailable

// START_FUNCTION_FinalStatistics_Reset
// START_CONTRACT:
// PURPOSE: Очистка всех данных
// OUTPUTS: Нет
// END_CONTRACT
void FinalStatistics::reset() {
    iteration_count = 0;
    match_count = 0;
    wallet_count = 0;
    runtime_seconds = 0.0;
    start_timestamp = 0.0;
    end_timestamp = 0.0;
    iterations_per_second = 0.0;
    wallets_per_second = 0.0;
    avg_iteration_time_ms = 0.0;
    list_path.clear();
    custom_metrics.clear();
}
// END_FUNCTION_FinalStatistics_Reset

// START_FUNCTION_FinalStatistics_ToPluginMetrics
// START_CONTRACT:
// PURPOSE: Преобразование в PluginMetrics для совместимости
// OUTPUTS: PluginMetrics словарь
// END_CONTRACT
PluginMetrics FinalStatistics::to_plugin_metrics() const {
    PluginMetrics result;
    result["iteration_count"] = static_cast<int64_t>(iteration_count);
    result["match_count"] = static_cast<int64_t>(match_count);
    result["wallet_count"] = static_cast<int64_t>(wallet_count);
    result["runtime_seconds"] = runtime_seconds;
    result["iterations_per_second"] = iterations_per_second;
    result["wallets_per_second"] = wallets_per_second;
    result["avg_iteration_time_ms"] = avg_iteration_time_ms;
    return result;
}
// END_FUNCTION_FinalStatistics_ToPluginMetrics

//==============================================================================
// IMPLEMENTATION: SessionHistory
//==============================================================================

// START_CONSTRUCTOR_SessionHistory
// START_CONTRACT:
// PURPOSE: Конструктор с параметрами
// INPUTS: id — ID сессии, statistics — статистика
// OUTPUTS: Созданный объект
// END_CONTRACT
SessionHistory::SessionHistory(uint32_t id, const FinalStatistics& statistics)
    : session_id(id), stats(statistics), timestamp(std::chrono::system_clock::now()) {}
// END_CONSTRUCTOR_SessionHistory

//==============================================================================
// IMPLEMENTATION: FinalStatsPlugin
//==============================================================================

// START_FUNCTION_FinalStatsPlugin_Constructor
// START_CONTRACT:
// PURPOSE: Конструктор плагина финальной статистики
// OUTPUTS: Инициализированный объект FinalStatsPlugin
// SIDE_EFFECTS: Создаёт логгер; инициализирует структуры данных
// TEST_CONDITIONS:
// - Объект должен быть готов к initialize()
// - История должна быть пустой
// END_CONTRACT
FinalStatsPlugin::FinalStatsPlugin()
    : m_info(PluginInfo(
        FINAL_STATS_PLUGIN_NAME,
        FINAL_STATS_PLUGIN_VERSION,
        "Final statistics plugin for wallet generation monitoring",
        "Wallet Generator Team"
    ))
    , m_logger("FinalStatsPlugin")
{
    m_logger.debug("FinalStatsPlugin constructed");
}
// END_FUNCTION_FinalStatsPlugin_Constructor

// START_FUNCTION_FinalStatsPlugin_Destructor
// START_CONTRACT:
// PURPOSE: Деструктор плагина
// SIDE_EFFECTS: Вызывает shutdown() для корректного завершения
// END_CONTRACT
FinalStatsPlugin::~FinalStatsPlugin() {
    if (m_state.load() != PluginState::STOPPED && 
        m_state.load() != PluginState::UNINITIALIZED) {
        shutdown();
    }
}
// END_FUNCTION_FinalStatsPlugin_Destructor

//==============================================================================
// IPlugin Implementation
//==============================================================================

// START_FUNCTION_Initialize
// START_CONTRACT:
// PURPOSE: Инициализация плагина
// SIDE_EFFECTS: Переводит плагин в состояние ACTIVE
// TEST_CONDITIONS: Плагин должен успешно инициализироваться
// END_CONTRACT
void FinalStatsPlugin::initialize() {
    m_logger.info("Initializing FinalStatsPlugin");
    m_state.store(PluginState::ACTIVE);
    m_logger.info("FinalStatsPlugin initialized successfully");
}
// END_FUNCTION_Initialize

// START_FUNCTION_Shutdown
// START_CONTRACT:
// PURPOSE: Завершение работы плагина
// SIDE_EFFECTS: Переводит плагин в состояние STOPPED
// END_CONTRACT
void FinalStatsPlugin::shutdown() {
    m_logger.info("FinalStatsPlugin shutdown complete");
    m_state.store(PluginState::STOPPED);
}
// END_FUNCTION_Shutdown

// START_FUNCTION_GetInfo
// START_CONTRACT:
// PURPOSE: Получение информации о плагине
// OUTPUTS: PluginInfo — структура с информацией о плагине
// END_CONTRACT
PluginInfo FinalStatsPlugin::get_info() const {
    return m_info;
}
// END_FUNCTION_GetInfo

// START_FUNCTION_GetState
// START_CONTRACT:
// PURPOSE: Получение состояния плагина
// OUTPUTS: PluginState — текущее состояние
// END_CONTRACT
PluginState FinalStatsPlugin::get_state() const {
    return m_state.load();
}
// END_FUNCTION_GetState

//==============================================================================
// Event Handlers
//==============================================================================

// START_FUNCTION_OnMetricsUpdate
// START_CONTRACT:
// PURPOSE: Обработка обновления метрик (заглушка для этого плагина)
// INPUTS: const PluginMetrics& metrics — метрики
// OUTPUTS: Нет
// KEYWORDS: [DOMAIN(6): Placeholder]
// END_CONTRACT
void FinalStatsPlugin::on_metrics_update(const PluginMetrics& metrics) {
    // Плагин финальной статистики не отслеживает метрики в реальном времени
    // Все метрики фиксируются при завершении в on_finish()
    m_logger.debug("on_metrics_update called - no action for final stats plugin");
}
// END_FUNCTION_OnMetricsUpdate

// START_FUNCTION_OnStart
// START_CONTRACT:
// PURPOSE: Обработчик запуска генератора кошельков
// INPUTS: const std::string& selected_list_path — путь к списку адресов
// SIDE_EFFECTS: Сброс статистики; установка флага мониторинга; запуск таймера
// END_CONTRACT
void FinalStatsPlugin::on_start(const std::string& selected_list_path) {
    m_logger.info("Starting final stats with list: " + selected_list_path);
    
    std::lock_guard<std::mutex> lock(m_data_mutex);
    m_final_stats.reset();
    m_final_stats.list_path = selected_list_path;
    m_start_time = std::chrono::steady_clock::now();
    m_is_complete = false;
    
    m_logger.info("Final stats session started");
}
// END_FUNCTION_OnStart

// START_FUNCTION_OnFinish
// START_CONTRACT:
// PURPOSE: Обработчик завершения генерации кошельков
// INPUTS: const PluginMetrics& final_metrics — финальные метрики
// SIDE_EFFECTS: Фиксация финальных метрик; вычисление производных показателей
// KEYWORDS: [DOMAIN(9): Finalization; CONCEPT(7): MetricsProcessing]
// END_CONTRACT
void FinalStatsPlugin::on_finish(const PluginMetrics& final_metrics) {
    m_logger.info("Generation finished - capturing final statistics");
    
    // START_BLOCK_CAPTURE_METRICS: [Фиксация метрик из словаря]
    std::lock_guard<std::mutex> lock(m_data_mutex);
    
    // Извлечение основных метрик
    m_final_stats.iteration_count = get_metric_value<int64_t>(final_metrics, "iteration_count", 0);
    m_final_stats.match_count = get_metric_value<int64_t>(final_metrics, "match_count", 0);
    m_final_stats.wallet_count = get_metric_value<int64_t>(final_metrics, "wallet_count", 0);
    
    // Извлечение custom metrics
    for (const auto& [key, value] : final_metrics) {
        if (key != "iteration_count" && key != "match_count" && 
            key != "wallet_count" && key != "runtime_seconds") {
            
        }
    }
    // END_BLOCK_CAPTURE_METRICS
    
    // START_BLOCK_CALCULATE_TIMING: [Вычисление временных метрик]
    if (m_start_time.has_value()) {
        auto now = std::chrono::steady_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(
            now - m_start_time.value()
        );
        m_final_stats.runtime_seconds = duration.count() / 1000.0;
        
        m_final_stats.end_timestamp = std::chrono::duration_cast<std::chrono::seconds>(
            now.time_since_epoch()
        ).count();
        m_final_stats.start_timestamp = std::chrono::duration_cast<std::chrono::seconds>(
            m_start_time.value().time_since_epoch()
        ).count();
    }
    // END_BLOCK_CALCULATE_TIMING
    
    // START_BLOCK_CALCULATE_DERIVED: [Вычисление производных показателей]
    calculate_derived_metrics();
    // END_BLOCK_CALCULATE_DERIVED
    
    m_is_complete = true;
    
    m_logger.info("[FinalStatsPlugin][ON_FINISH][Info] Финальная статистика: " +
                  std::to_string(m_final_stats.iteration_count) + " итераций, " +
                  std::to_string(m_final_stats.runtime_seconds) + " сек");
}
// END_FUNCTION_OnFinish

// START_FUNCTION_OnReset
// START_CONTRACT:
// PURPOSE: Обработчик сброса генератора
// SIDE_EFFECTS: Сброс внутреннего состояния
// END_CONTRACT
void FinalStatsPlugin::on_reset() {
    m_logger.info("Resetting final stats plugin");
    reset_stats();
}
// END_FUNCTION_OnReset

//==============================================================================
// Приватные методы
//==============================================================================

// START_FUNCTION_CalculateDerivedMetrics
// START_CONTRACT:
// PURPOSE: Вычисление производных показателей производительности
// OUTPUTS: Нет
// SIDE_EFFECTS: Обновляет поля iterations_per_second, wallets_per_second, avg_iteration_time_ms
// KEYWORDS: [DOMAIN(8): Performance; ALGORITHM(7): Calculation]
// END_CONTRACT
void FinalStatsPlugin::calculate_derived_metrics() {
    double runtime = m_final_stats.runtime_seconds;
    uint64_t iterations = m_final_stats.iteration_count;
    uint64_t wallets = m_final_stats.wallet_count;
    
    if (runtime > 0) {
        m_final_stats.iterations_per_second = static_cast<double>(iterations) / runtime;
        m_final_stats.wallets_per_second = static_cast<double>(wallets) / runtime;
    }
    
    if (iterations > 0 && runtime > 0) {
        m_final_stats.avg_iteration_time_ms = (runtime / static_cast<double>(iterations)) * 1000.0;
    }
}
// END_FUNCTION_CalculateDerivedMetrics

// START_FUNCTION_FormatTime
// START_CONTRACT:
// PURPOSE: Форматирование времени в читаемый вид
// INPUTS: double seconds — время в секундах
// OUTPUTS: std::string — отформатированная строка HH:MM:SS
// KEYWORDS: [CONCEPT(7): Formatting]
// END_CONTRACT
std::string FinalStatsPlugin::format_time(double seconds) const {
    int hours = static_cast<int>(seconds / 3600);
    int minutes = static_cast<int>((seconds - hours * 3600) / 60);
    int secs = static_cast<int>(seconds - hours * 3600 - minutes * 60);
    
    std::ostringstream oss;
    oss << std::setfill('0') << std::setw(2) << hours << ":"
        << std::setw(2) << minutes << ":" << std::setw(2) << secs;
    return oss.str();
}
// END_FUNCTION_FormatTime

//==============================================================================
// Методы получения данных
//==============================================================================

// START_FUNCTION_GetFinalMetrics
// START_CONTRACT:
// PURPOSE: Получение финальных метрик
// OUTPUTS: FinalStatistics — копия структуры с метриками
// END_CONTRACT
FinalStatistics FinalStatsPlugin::get_final_metrics() const {
    std::lock_guard<std::mutex> lock(m_data_mutex);
    return m_final_stats;
}
// END_FUNCTION_GetFinalMetrics

// START_FUNCTION_GetSummary
// START_CONTRACT:
// PURPOSE: Получение текстовой сводки
// OUTPUTS: std::string — форматированная строка сводки
// END_CONTRACT
std::string FinalStatsPlugin::get_summary() const {
    std::lock_guard<std::mutex> lock(m_data_mutex);
    
    if (!m_final_stats.is_available()) {
        return "Нет данных";
    }
    
    std::ostringstream oss;
    oss << "=================================================\n";
    oss << "ФИНАЛЬНАЯ СТАТИСТИКА\n";
    oss << "=================================================\n";
    oss << "Итераций: " << m_final_stats.iteration_count << "\n";
    oss << "Совпадений: " << m_final_stats.match_count << "\n";
    oss << "Кошельков: " << m_final_stats.wallet_count << "\n";
    oss << "Время работы: " << format_time(m_final_stats.runtime_seconds) << "\n";
    oss << "Итераций/сек: " << std::fixed << std::setprecision(2) 
       << m_final_stats.iterations_per_second << "\n";
    oss << "=================================================\n";
    
    return oss.str();
}
// END_FUNCTION_GetSummary

// START_FUNCTION_GetSessionHistory
// START_CONTRACT:
// PURPOSE: Получение истории сессий
// OUTPUTS: std::vector<SessionHistory> — вектор записей истории
// END_CONTRACT
std::vector<SessionHistory> FinalStatsPlugin::get_session_history() const {
    std::lock_guard<std::mutex> lock(m_data_mutex);
    return m_session_history;
}
// END_FUNCTION_GetSessionHistory

// START_FUNCTION_GetPerformanceAnalysis
// START_CONTRACT:
// PURPOSE: Получение анализа производительности
// OUTPUTS: PluginMetrics — словарь с показателями производительности
// END_CONTRACT
PluginMetrics FinalStatsPlugin::get_performance_analysis() const {
    std::lock_guard<std::mutex> lock(m_data_mutex);
    
    PluginMetrics analysis;
    
    if (!m_final_stats.is_available()) {
        analysis["available"] = false;
        return analysis;
    }
    
    analysis["available"] = true;
    analysis["iterations"] = static_cast<int64_t>(m_final_stats.iteration_count);
    analysis["runtime_seconds"] = m_final_stats.runtime_seconds;
    analysis["iter_per_sec"] = m_final_stats.iterations_per_second;
    
    // Оценка времени до успеха (предполагаем 1/1000000000 шанс на совпадение)
    double expected_iterations = 1000000000.0;
    double estimated_hours = 0.0;
    if (m_final_stats.iteration_count > 0 && m_final_stats.runtime_seconds > 0) {
        estimated_hours = (expected_iterations / m_final_stats.iteration_count) * 
                         (m_final_stats.runtime_seconds / 3600.0);
    }
    analysis["estimated_hours_to_match"] = estimated_hours;
    analysis["probability_per_iteration"] = 1.0 / expected_iterations;
    
    return analysis;
}
// END_FUNCTION_GetPerformanceAnalysis

// START_FUNCTION_IsComplete
// START_CONTRACT:
// PURPOSE: Проверка завершения
// OUTPUTS: bool — true если генерация завершена
// END_CONTRACT
bool FinalStatsPlugin::is_complete() const {
    return m_is_complete.load();
}
// END_FUNCTION_IsComplete

//==============================================================================
// Методы экспорта
//==============================================================================

// START_FUNCTION_ExportToJSON
// START_CONTRACT:
// PURPOSE: Экспорт статистики в JSON файл
// INPUTS: const std::string& file_path — путь к файлу
// OUTPUTS: bool — true при успехе
// SIDE_EFFECTS: Создаёт файл на диске
// KEYWORDS: [DOMAIN(7): Export; TECH(5): JSON]
// END_CONTRACT
bool FinalStatsPlugin::export_to_json(const std::string& file_path) {
    std::lock_guard<std::mutex> lock(m_data_mutex);
    
    try {
        std::ofstream file(file_path, std::ios::out | std::ios::binary);
        if (!file.is_open()) {
            m_logger.error("Failed to open file for JSON export: " + file_path);
            return false;
        }
        
        // Генерация JSON вручную (без внешних зависимостей)
        file << "{\n";
        file << "  \"iteration_count\": " << m_final_stats.iteration_count << ",\n";
        file << "  \"match_count\": " << m_final_stats.match_count << ",\n";
        file << "  \"wallet_count\": " << m_final_stats.wallet_count << ",\n";
        file << "  \"runtime_seconds\": " << std::fixed << std::setprecision(2) 
             << m_final_stats.runtime_seconds << ",\n";
        file << "  \"start_timestamp\": " << m_final_stats.start_timestamp << ",\n";
        file << "  \"end_timestamp\": " << m_final_stats.end_timestamp << ",\n";
        file << "  \"iterations_per_second\": " << m_final_stats.iterations_per_second << ",\n";
        file << "  \"wallets_per_second\": " << m_final_stats.wallets_per_second << ",\n";
        file << "  \"avg_iteration_time_ms\": " << m_final_stats.avg_iteration_time_ms << ",\n";
        file << "  \"list_path\": \"" << m_final_stats.list_path << "\"\n";
        file << "}\n";
        
        file.close();
        m_logger.info("Exported final stats to JSON: " + file_path);
        return true;
        
    } catch (const std::exception& e) {
        m_logger.error(std::string("JSON export exception: ") + e.what());
        return false;
    }
}
// END_FUNCTION_ExportToJSON

// START_FUNCTION_ExportToCSV
// START_CONTRACT:
// PURPOSE: Экспорт статистики в CSV файл (Excel совместимый)
// INPUTS: const std::string& file_path — путь к файлу
// OUTPUTS: bool — true при успехе
// SIDE_EFFECTS: Создаёт файл с UTF-8 BOM
// KEYWORDS: [DOMAIN(7): Export; TECH(5): CSV]
// END_CONTRACT
bool FinalStatsPlugin::export_to_csv(const std::string& file_path) {
    std::lock_guard<std::mutex> lock(m_data_mutex);
    
    try {
        std::ofstream file(file_path, std::ios::out | std::ios::binary);
        if (!file.is_open()) {
            m_logger.error("Failed to open file for CSV export: " + file_path);
            return false;
        }
        
        // UTF-8 BOM для Excel
        unsigned char bom[] = {0xEF, 0xBB, 0xBF};
        file.write(reinterpret_cast<const char*>(bom), 3);
        
        // Запись заголовков
        file << "Parameter,Value\n";
        
        // Запись данных
        file << "iteration_count," << m_final_stats.iteration_count << "\n";
        file << "match_count," << m_final_stats.match_count << "\n";
        file << "wallet_count," << m_final_stats.wallet_count << "\n";
        file << "runtime_seconds," << std::fixed << std::setprecision(2) 
             << m_final_stats.runtime_seconds << "\n";
        file << "iterations_per_second," << m_final_stats.iterations_per_second << "\n";
        file << "wallets_per_second," << m_final_stats.wallets_per_second << "\n";
        file << "avg_iteration_time_ms," << m_final_stats.avg_iteration_time_ms << "\n";
        file << "list_path," << m_final_stats.list_path << "\n";
        
        file.close();
        m_logger.info("Exported final stats to CSV: " + file_path);
        return true;
        
    } catch (const std::exception& e) {
        m_logger.error(std::string("CSV export exception: ") + e.what());
        return false;
    }
}
// END_FUNCTION_ExportToCSV

// START_FUNCTION_ExportToTXT
// START_CONTRACT:
// PURPOSE: Экспорт статистики в читаемый текстовый файл
// INPUTS: const std::string& file_path — путь к файлу
// OUTPUTS: std::string — путь к файлу или сообщение об ошибке
// SIDE_EFFECTS: Создаёт форматированный текстовый файл
// KEYWORDS: [DOMAIN(7): Export; TECH(5): TXT]
// END_CONTRACT
std::string FinalStatsPlugin::export_to_txt(const std::string& file_path) {
    std::lock_guard<std::mutex> lock(m_data_mutex);
    
    try {
        std::ofstream file(file_path, std::ios::out | std::ios::binary);
        if (!file.is_open()) {
            return "Error: Failed to open file";
        }
        
        // Запись данных
        file << "============================================================\n";
        file << "ФИНАЛЬНАЯ СТАТИСТИКА ГЕНЕРАТОРА КОШЕЛЬКОВ\n";
        file << "============================================================\n\n";
        
        // Время работы
        file << "ВРЕМЯ РАБОТЫ:\n";
        file << "  Общее время: " << format_time(m_final_stats.runtime_seconds) 
             << " (" << std::fixed << std::setprecision(2) << m_final_stats.runtime_seconds << " сек)\n\n";
        
        // Итерации
        file << "ИТЕРАЦИИ:\n";
        file << "  Всего итераций: " << m_final_stats.iteration_count << "\n\n";
        
        // Кошельки
        file << "КОШЕЛЬКИ:\n";
        file << "  Сгенерировано кошельков: " << m_final_stats.wallet_count << "\n\n";
        
        // Совпадения
        file << "СОВПАДЕНИЯ:\n";
        file << "  Найдено совпадений: " << m_final_stats.match_count << "\n\n";
        
        // Производительность
        file << "ПРОИЗВОДИТЕЛЬНОСТЬ:\n";
        file << "  Итераций в секунду: " << std::fixed << std::setprecision(2) 
             << m_final_stats.iterations_per_second << "\n";
        file << "  Кошельков в секунду: " << m_final_stats.wallets_per_second << "\n";
        file << "  Среднее время итерации: " << m_final_stats.avg_iteration_time_ms << " мс\n\n";
        
        // Список
        file << "ИСПОЛЬЗУЕМЫЙ СПИСОК:\n";
        file << "  " << m_final_stats.list_path << "\n\n";
        
        file << "============================================================\n";
        file << "КОНЕЦ ОТЧЁТА\n";
        file << "============================================================\n";
        
        file.close();
        m_logger.info("Exported final stats to TXT: " + file_path);
        return file_path;
        
    } catch (const std::exception& e) {
        m_logger.error(std::string("TXT export exception: ") + e.what());
        return std::string("Error exporting to TXT: ") + e.what();
    }
}
// END_FUNCTION_ExportToTXT

// START_FUNCTION_ExportToFile
// START_CONTRACT:
// PURPOSE: Универсальный экспорт
// INPUTS: ExportFormat format — формат, const std::string& file_path — путь
// OUTPUTS: bool — true при успехе
// END_CONTRACT
bool FinalStatsPlugin::export_to_file(ExportFormat format, const std::string& file_path) {
    switch (format) {
        case ExportFormat::JSON:
            return export_to_json(file_path);
        case ExportFormat::CSV:
            return export_to_csv(file_path);
        case ExportFormat::TXT:
            return export_to_txt(file_path).find("Error") == std::string::npos;
        case ExportFormat::MARKDOWN:
            // Для markdown используем txt с markdown форматированием
            return export_to_txt(file_path).find("Error") == std::string::npos;
        default:
            m_logger.error("Unknown export format");
            return false;
    }
}
// END_FUNCTION_ExportToFile

//==============================================================================
// Управление состоянием
//==============================================================================

// START_FUNCTION_ResetStats
// START_CONTRACT:
// PURPOSE: Сброс состояния
// OUTPUTS: Нет
// SIDE_EFFECTS: Очищает все данные
// END_CONTRACT
void FinalStatsPlugin::reset_stats() {
    std::lock_guard<std::mutex> lock(m_data_mutex);
    m_final_stats.reset();
    m_start_time = std::nullopt;
    m_is_complete = false;
    m_session_history.clear();
    m_session_counter = 0;
    m_logger.info("Final stats reset complete");
}
// END_FUNCTION_ResetStats

// START_FUNCTION_AddSession
// START_CONTRACT:
// PURPOSE: Добавление сессии в историю
// INPUTS: const FinalStatistics& session_stats — статистика сессии
// OUTPUTS: Нет
// END_CONTRACT
void FinalStatsPlugin::add_session(const FinalStatistics& session_stats) {
    std::lock_guard<std::mutex> lock(m_data_mutex);
    m_session_counter++;
    m_session_history.emplace_back(m_session_counter, session_stats);
    m_logger.debug("Session added to history: " + std::to_string(m_session_history.size()));
}
// END_FUNCTION_AddSession

// START_FUNCTION_GetTotalStatistics
// START_CONTRACT:
// PURPOSE: Получение общей статистики по всем сессиям
// OUTPUTS: FinalStatistics — агрегированная статистика
// END_CONTRACT
FinalStatistics FinalStatsPlugin::get_total_statistics() const {
    std::lock_guard<std::mutex> lock(m_data_mutex);
    
    FinalStatistics total;
    
    if (m_session_history.empty()) {
        return total;
    }
    
    for (const auto& session : m_session_history) {
        total.iteration_count += session.stats.iteration_count;
        total.match_count += session.stats.match_count;
        total.wallet_count += session.stats.wallet_count;
        total.runtime_seconds += session.stats.runtime_seconds;
    }
    
    // Вычисление средних значений
    size_t session_count = m_session_history.size();
    if (session_count > 0) {
        total.iterations_per_second = static_cast<double>(total.iteration_count) / total.runtime_seconds;
        total.wallets_per_second = static_cast<double>(total.wallet_count) / total.runtime_seconds;
    }
    
    return total;
}
// END_FUNCTION_GetTotalStatistics

//==============================================================================
// Template Implementation
//==============================================================================

// START_FUNCTION_GetMetricValue
// START_CONTRACT:
// PURPOSE: Извлечение метрики из PluginMetrics
// INPUTS: const PluginMetrics& metrics, const std::string& key, T default_value
// OUTPUTS: T — значение метрики или значение по умолчанию
// END_CONTRACT
template<typename T>
T FinalStatsPlugin::get_metric_value(
    const PluginMetrics& metrics, 
    const std::string& key, 
    T default_value
) const {
    auto it = metrics.find(key);
    if (it == metrics.end()) {
        return default_value;
    }
    
    const auto& value = it->second;
    
    if constexpr (std::is_same_v<T, int64_t>) {
        if (std::holds_alternative<int64_t>(value)) {
            return std::get<int64_t>(value);
        } else if (std::holds_alternative<int>(value)) {
            return static_cast<int64_t>(std::get<int>(value));
        } else if (std::holds_alternative<double>(value)) {
            return static_cast<int64_t>(std::get<double>(value));
        }
    } else if constexpr (std::is_same_v<T, double>) {
        if (std::holds_alternative<double>(value)) {
            return std::get<double>(value);
        } else if (std::holds_alternative<int64_t>(value)) {
            return static_cast<double>(std::get<int64_t>(value));
        } else if (std::holds_alternative<int>(value)) {
            return static_cast<double>(std::get<int>(value));
        }
    } else if constexpr (std::is_same_v<T, std::string>) {
        if (std::holds_alternative<std::string>(value)) {
            return std::get<std::string>(value);
        }
    }
    
    return default_value;
}
// END_FUNCTION_GetMetricValue
