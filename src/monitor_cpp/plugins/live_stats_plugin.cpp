// FILE: src/monitor_cpp/plugins/live_stats_plugin.cpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Реализация плагина live-мониторинга
// SCOPE: Методы класса LiveStatsPlugin, обработка метрик, вычисление статистики
// KEYWORDS: [DOMAIN(9): LiveMonitoring; TECH(8): RingBuffer; TECH(6): C++17]
// END_MODULE_CONTRACT

#include "live_stats_plugin.hpp"

//==============================================================================
// Конструктор и Деструктор
//==============================================================================

// START_FUNCTION_LiveStatsPlugin_Constructor
// START_CONTRACT:
// PURPOSE: Конструктор плагина live-мониторинга
// OUTPUTS: Инициализированный объект LiveStatsPlugin
// SIDE_EFFECTS: Создаёт хранилище истории метрик; инициализирует логгер
// TEST_CONDITIONS:
// - Объект должен быть готов к initialize()
// - История должна быть пустой
// END_CONTRACT
LiveStatsPlugin::LiveStatsPlugin()
    : m_name("live_stats")
    , m_info(PluginInfo(
        "live_stats",
        "1.0.0",
        "Live statistics plugin for monitoring wallet generation",
        "Wallet Generator Team"
    ))
    , m_logger("LiveStatsPlugin")
{
    m_logger.debug("LiveStatsPlugin constructed");
}
// END_FUNCTION_LiveStatsPlugin_Constructor

// START_FUNCTION_LiveStatsPlugin_Destructor
// START_CONTRACT:
// PURPOSE: Деструктор плагина
// SIDE_EFFECTS: Вызывает shutdown() для корректного завершения
// END_CONTRACT
LiveStatsPlugin::~LiveStatsPlugin() {
    if (m_state.load() != PluginState::STOPPED && 
        m_state.load() != PluginState::UNINITIALIZED) {
        shutdown();
    }
}
// END_FUNCTION_LiveStatsPlugin_Destructor

//==============================================================================
// IPlugin Implementation
//==============================================================================

// START_FUNCTION_Initialize
// START_CONTRACT:
// PURPOSE: Инициализация плагина и регистрация UI компонентов
// SIDE_EFFECTS: Сохраняет указатель на приложение; логирует инициализацию
// TEST_CONDITIONS: Плагин должен успешно инициализироваться
// END_CONTRACT
void LiveStatsPlugin::initialize() {
    m_logger.info("Initializing LiveStatsPlugin");
    m_state.store(PluginState::ACTIVE);
    m_logger.info("LiveStatsPlugin initialized successfully");
}
// END_FUNCTION_Initialize

// START_FUNCTION_Shutdown
// START_CONTRACT:
// PURPOSE: Завершение работы плагина
// SIDE_EFFECTS: Сбрасывает состояние мониторинга
// END_CONTRACT
void LiveStatsPlugin::shutdown() {
    m_is_monitoring = false;
    m_logger.info("LiveStatsPlugin shutdown complete");
    m_state.store(PluginState::STOPPED);
}
// END_FUNCTION_Shutdown

// START_FUNCTION_GetInfo
// START_CONTRACT:
// PURPOSE: Получение информации о плагине
// OUTPUTS: PluginInfo — структура с информацией о плагине
// END_CONTRACT
PluginInfo LiveStatsPlugin::get_info() const {
    return m_info;
}
// END_FUNCTION_GetInfo

// START_FUNCTION_GetState
// START_CONTRACT:
// PURPOSE: Получение состояния плагина
// OUTPUTS: PluginState — текущее состояние
// END_CONTRACT
PluginState LiveStatsPlugin::get_state() const {
    return m_state.load();
}
// END_FUNCTION_GetState

//==============================================================================
// Event Handlers
//==============================================================================

// START_FUNCTION_OnMetricsUpdate
// START_CONTRACT:
// PURPOSE: Обработка обновления метрик от генератора
// INPUTS: const PluginMetrics& metrics — словарь метрик
// SIDE_EFFECTS: Обновляет историю метрик; вычисляет дельты; обновляет UI
// TEST_CONDITIONS: Метод должен корректно обработать любые метрики
// END_CONTRACT
void LiveStatsPlugin::on_metrics_update(const PluginMetrics& metrics) {
    auto current_time = std::chrono::steady_clock::now();
    
    // START_BLOCK_EXTRACT_METRICS: [Извлечение метрик из словаря]
    int64_t iteration_count = 0;
    int64_t wallet_count = 0;
    int64_t match_count = 0;
    double entropy_bits = 0.0;
    
    // Извлечение iteration_count
    if (metrics.count("iteration_count")) {
        const auto& val = metrics.at("iteration_count");
        if (std::holds_alternative<int64_t>(val)) {
            iteration_count = std::get<int64_t>(val);
        } else if (std::holds_alternative<int>(val)) {
            iteration_count = static_cast<int64_t>(std::get<int>(val));
        } else if (std::holds_alternative<double>(val)) {
            iteration_count = static_cast<int64_t>(std::get<double>(val));
        }
    }
    
    // Извлечение wallet_count
    if (metrics.count("wallet_count")) {
        const auto& val = metrics.at("wallet_count");
        if (std::holds_alternative<int64_t>(val)) {
            wallet_count = std::get<int64_t>(val);
        } else if (std::holds_alternative<int>(val)) {
            wallet_count = static_cast<int64_t>(std::get<int>(val));
        } else if (std::holds_alternative<double>(val)) {
            wallet_count = static_cast<int64_t>(std::get<double>(val));
        }
    }
    
    // Извлечение match_count
    if (metrics.count("match_count")) {
        const auto& val = metrics.at("match_count");
        if (std::holds_alternative<int64_t>(val)) {
            match_count = std::get<int64_t>(val);
        } else if (std::holds_alternative<int>(val)) {
            match_count = static_cast<int64_t>(std::get<int>(val));
        } else if (std::holds_alternative<double>(val)) {
            match_count = static_cast<int64_t>(std::get<double>(val));
        }
    }
    
    // Извлечение entropy_data
    if (metrics.count("entropy_data")) {
        const auto& entropy_variant = metrics.at("entropy_data");
        if (std::holds_alternative<std::unordered_map<std::string, PluginAny>>(entropy_variant)) {
            const auto& ent_map = std::get<std::unordered_map<std::string, PluginAny>>(entropy_variant);
            if (ent_map.count("total_bits")) {
                const auto& bits = ent_map.at("total_bits");
                if (std::holds_alternative<double>(bits)) {
                    entropy_bits = std::get<double>(bits);
                } else if (std::holds_alternative<int64_t>(bits)) {
                    entropy_bits = static_cast<double>(std::get<int64_t>(bits));
                }
            }
        }
    }
    // END_BLOCK_EXTRACT_METRICS
    
    // START_BLOCK_CALCULATE_DELTAS: [Вычисление дельт]
    int64_t prev_iterations = m_last_iteration_count.load();
    int64_t prev_wallets = m_last_wallet_count.load();
    int64_t prev_matches = m_last_match_count.load();
    
    double iteration_delta = static_cast<double>(iteration_count - prev_iterations);
    double wallet_delta = static_cast<double>(wallet_count - prev_wallets);
    double match_delta = static_cast<double>(match_count - prev_matches);
    // END_BLOCK_CALCULATE_DELTAS
    
    // START_BLOCK_UPDATE_ATOMIC_COUNTERS: [Атомарное обновление счётчиков]
    m_last_iteration_count = iteration_count;
    m_last_wallet_count = wallet_count;
    m_last_match_count = match_count;
    // END_BLOCK_UPDATE_ATOMIC_COUNTERS
    
    // START_BLOCK_UPDATE_HISTORY: [Обновление истории метрик]
    m_last_update_time = std::chrono::duration<double>(
        current_time.time_since_epoch()
    ).count();
    
    {
        std::lock_guard<std::mutex> lock(m_data_mutex);
        MetricSnapshot snapshot(iteration_delta, wallet_delta, match_delta, entropy_bits);
        m_history.push(snapshot);
        
        if (entropy_bits > 0.0) {
            m_entropy_samples.push(entropy_bits);
        }
    }
    // END_BLOCK_UPDATE_HISTORY
    
    // START_BLOCK_CHECK_MONITORING_STATE: [Проверка состояния мониторинга]
    if (!m_is_monitoring.load() && iteration_count > 0) {
        m_is_monitoring = true;
        if (!m_start_timestamp.has_value()) {
            m_start_timestamp = current_time;
        }
    }
    // END_BLOCK_CHECK_MONITORING_STATE
    
    m_logger.debug("Metrics updated: iterations=" + std::to_string(iteration_count) +
                   ", wallets=" + std::to_string(wallet_count) +
                   ", matches=" + std::to_string(match_count));
}
// END_FUNCTION_OnMetricsUpdate

// START_FUNCTION_OnStart
// START_CONTRACT:
// PURPOSE: Обработчик запуска генератора кошельков
// INPUTS: const std::string& selectedListPath — путь к списку адресов
// SIDE_EFFECTS: Сброс статистики; установка флага мониторинга; запуск таймера
// END_CONTRACT
void LiveStatsPlugin::on_start(const std::string& selected_list_path) {
    m_logger.info("Starting monitoring with list: " + selected_list_path);
    resetStats();
    m_is_monitoring = true;
    m_start_timestamp = std::chrono::steady_clock::now();
    m_logger.info("Monitoring started");
}
// END_FUNCTION_OnStart

// START_FUNCTION_OnFinish
// START_CONTRACT:
// PURPOSE: Обработчик завершения генерации кошельков
// INPUTS: const PluginMetrics& finalMetrics — финальные метрики
// SIDE_EFFECTS: Обработка финальных метрик; обновление UI
// END_CONTRACT
void LiveStatsPlugin::on_finish(const PluginMetrics& final_metrics) {
    m_logger.info("Generation finished");
    on_metrics_update(final_metrics);
    m_is_monitoring = false;
}
// END_FUNCTION_OnFinish

// START_FUNCTION_OnReset
// START_CONTRACT:
// PURPOSE: Обработчик сброса генератора
// SIDE_EFFECTS: Сброс внутреннего состояния
// END_CONTRACT
void LiveStatsPlugin::on_reset() {
    m_logger.info("Resetting plugin state");
    resetStats();
}
// END_FUNCTION_OnReset

//==============================================================================
// Специфичные методы LiveStats
//==============================================================================

// START_FUNCTION_ResetStats
// START_CONTRACT:
// PURPOSE: Сброс статистики мониторинга
// SIDE_EFFECTS: Очищает историю метрик; сбрасывает счётчики
// END_CONTRACT
void LiveStatsPlugin::resetStats() {
    std::lock_guard<std::mutex> lock(m_data_mutex);
    m_history.clear();
    m_entropy_samples.clear();
    
    m_last_iteration_count = 0;
    m_last_wallet_count = 0;
    m_last_match_count = 0;
    m_last_update_time = 0.0;
    m_is_monitoring = false;
    m_start_timestamp = std::nullopt;
    
    m_logger.info("Stats reset complete");
}
// END_FUNCTION_ResetStats

// START_FUNCTION_GetCurrentStats
// START_CONTRACT:
// PURPOSE: Получение текущей статистики
// OUTPUTS: CurrentStats — структура с текущими значениями метрик
// SIDE_EFFECTS: Вычисление прошедшего времени и скоростей
// END_CONTRACT
CurrentStats LiveStatsPlugin::getCurrentStats() const {
    CurrentStats stats;
    
    stats.iterations = m_last_iteration_count.load();
    stats.wallets = m_last_wallet_count.load();
    stats.matches = m_last_match_count.load();
    stats.is_monitoring = m_is_monitoring.load();
    
    // Вычисление прошедшего времени
    stats.elapsed_time = calculateTimeElapsed();
    
    // Вычисление скоростей
    if (stats.elapsed_time > 0.0 && stats.iterations > 0) {
        stats.iter_per_sec = static_cast<double>(stats.iterations) / stats.elapsed_time;
        stats.wallets_per_sec = static_cast<double>(stats.wallets) / stats.elapsed_time;
    }
    
    return stats;
}
// END_FUNCTION_GetCurrentStats

// START_FUNCTION_CalculateTimeElapsed
// START_CONTRACT:
// PURPOSE: Вычисление прошедшего времени
// OUTPUTS: double — прошедшее время в секундах
// END_CONTRACT
double LiveStatsPlugin::calculateTimeElapsed() const {
    if (!m_start_timestamp.has_value()) {
        return 0.0;
    }
    
    auto now = std::chrono::steady_clock::now();
    auto elapsed = std::chrono::duration<double>(now - m_start_timestamp.value());
    return elapsed.count();
}
// END_FUNCTION_CalculateTimeElapsed

// START_FUNCTION_CalculateStatistics
// START_CONTRACT:
// PURPOSE: Вычисление статистических показателей
// OUTPUTS: Statistics — структура со всеми статистическими показателями
// SIDE_EFFECTS: Захватывает мьютекс для thread-safe доступа к данным
// END_CONTRACT
Statistics LiveStatsPlugin::calculateStatistics() const {
    Statistics stats;
    
    {
        std::lock_guard<std::mutex> lock(m_data_mutex);
        
        // START_BLOCK_ITERATIONS_STATS: [Вычисление статистики итераций]
        if (!m_history.empty()) {
            std::vector<double> iterations;
            iterations.reserve(m_history.size());
            for (const auto& snapshot : m_history) {
                iterations.push_back(snapshot.iteration_delta);
            }
            
            stats.iterations_min = *std::min_element(iterations.begin(), iterations.end());
            stats.iterations_max = *std::max_element(iterations.begin(), iterations.end());
            stats.iterations_mean = calculateMean(iterations);
            stats.iterations_std = calculateStd(iterations, stats.iterations_mean);
            stats.iterations_available = true;
        }
        // END_BLOCK_ITERATIONS_STATS
        
        // START_BLOCK_WALLETS_STATS: [Вычисление статистики кошельков]
        if (!m_history.empty()) {
            std::vector<double> wallets;
            wallets.reserve(m_history.size());
            for (const auto& snapshot : m_history) {
                wallets.push_back(snapshot.wallet_delta);
            }
            
            stats.wallets_min = *std::min_element(wallets.begin(), wallets.end());
            stats.wallets_max = *std::max_element(wallets.begin(), wallets.end());
            stats.wallets_mean = calculateMean(wallets);
            stats.wallets_std = calculateStd(wallets, stats.wallets_mean);
            stats.wallets_available = true;
        }
        // END_BLOCK_WALLETS_STATS
        
        // START_BLOCK_ENTROPY_STATS: [Вычисление статистики энтропии]
        if (!m_entropy_samples.empty()) {
            auto entropy = m_entropy_samples.toVector();
            stats.entropy_min = *std::min_element(entropy.begin(), entropy.end());
            stats.entropy_max = *std::max_element(entropy.begin(), entropy.end());
            stats.entropy_mean = calculateMean(entropy);
            stats.entropy_available = true;
        }
        // END_BLOCK_ENTROPY_STATS
    }
    
    return stats;
}
// END_FUNCTION_CalculateStatistics

// START_FUNCTION_CalculateMean
// START_CONTRACT:
// PURPOSE: Вычисление среднего значения вектора
// INPUTS: const std::vector<double>& values — вектор значений
// OUTPUTS: double — среднее значение
// TEST_CONDITIONS:
// - Пустой вектор возвращает 0.0
// - Вектор из одного элемента возвращает этот элемент
// END_CONTRACT
double LiveStatsPlugin::calculateMean(const std::vector<double>& values) const {
    if (values.empty()) {
        return 0.0;
    }
    
    double sum = 0.0;
    for (double v : values) {
        sum += v;
    }
    return sum / static_cast<double>(values.size());
}
// END_FUNCTION_CalculateMean

// START_FUNCTION_CalculateStd
// START_CONTRACT:
// PURPOSE: Вычисление стандартного отклонения
// INPUTS: const std::vector<double>& values, double mean
// OUTPUTS: double — стандартное отклонение
// TEST_CONDITIONS: Вектор менее 2 элементов возвращает 0.0
// END_CONTRACT
double LiveStatsPlugin::calculateStd(const std::vector<double>& values, double mean) const {
    if (values.size() < 2) {
        return 0.0;
    }
    
    double sq_sum = 0.0;
    for (double v : values) {
        double diff = v - mean;
        sq_sum += diff * diff;
    }
    return std::sqrt(sq_sum / static_cast<double>(values.size() - 1));
}
// END_FUNCTION_CalculateStd

// START_FUNCTION_GetIterationPlotData
// START_CONTRACT:
// PURPOSE: Получение данных для графика итераций
// OUTPUTS: std::pair<std::vector<double>, std::vector<double>> — пары (x, y)
// END_CONTRACT
std::pair<std::vector<double>, std::vector<double>> 
LiveStatsPlugin::getIterationPlotData() const {
    std::lock_guard<std::mutex> lock(m_data_mutex);
    
    std::vector<double> x_values;
    std::vector<double> y_values;
    
    size_t count = m_history.size();
    x_values.reserve(count);
    y_values.reserve(count);
    
    for (size_t i = 0; i < count; ++i) {
        x_values.push_back(static_cast<double>(i));
        y_values.push_back(m_history[i].iteration_delta);
    }
    
    return {x_values, y_values};
}
// END_FUNCTION_GetIterationPlotData

// START_FUNCTION_GetWalletPlotData
// START_CONTRACT:
// PURPOSE: Получение данных для графика кошельков
// OUTPUTS: std::pair<std::vector<double>, std::vector<double>> — пары (x, y)
// END_CONTRACT
std::pair<std::vector<double>, std::vector<double>> 
LiveStatsPlugin::getWalletPlotData() const {
    std::lock_guard<std::mutex> lock(m_data_mutex);
    
    std::vector<double> x_values;
    std::vector<double> y_values;
    
    size_t count = m_history.size();
    x_values.reserve(count);
    y_values.reserve(count);
    
    for (size_t i = 0; i < count; ++i) {
        x_values.push_back(static_cast<double>(i));
        y_values.push_back(m_history[i].wallet_delta);
    }
    
    return {x_values, y_values};
}
// END_FUNCTION_GetWalletPlotData

// START_FUNCTION_GetEntropySummary
// START_CONTRACT:
// PURPOSE: Получение сводки по энтропии
// OUTPUTS: std::unordered_map<std::string, PluginAny> — словарь с данными энтропии
// END_CONTRACT
std::unordered_map<std::string, PluginAny> LiveStatsPlugin::getEntropySummary() const {
    std::lock_guard<std::mutex> lock(m_data_mutex);
    
    std::unordered_map<std::string, PluginAny> summary;
    
    if (m_entropy_samples.empty()) {
        summary["available"] = false;
        return summary;
    }
    
    auto entropy = m_entropy_samples.toVector();
    
    summary["available"] = true;
    summary["samples"] = static_cast<int64_t>(entropy.size());
    summary["min_bits"] = *std::min_element(entropy.begin(), entropy.end());
    summary["max_bits"] = *std::max_element(entropy.begin(), entropy.end());
    summary["avg_bits"] = calculateMean(entropy);
    summary["current_bits"] = entropy.back();
    
    return summary;
}
// END_FUNCTION_GetEntropySummary

// START_FUNCTION_IsMonitoring
// START_CONTRACT:
// PURPOSE: Проверка состояния мониторинга
// OUTPUTS: bool — true если мониторинг активен
// END_CONTRACT
bool LiveStatsPlugin::isMonitoring() const {
    return m_is_monitoring.load();
}
// END_FUNCTION_IsMonitoring

// START_FUNCTION_GetPerformanceReport
// START_CONTRACT:
// PURPOSE: Получение текстового отчёта о производительности
// OUTPUTS: std::string — текстовый отчёт
// END_CONTRACT
std::string LiveStatsPlugin::getPerformanceReport() const {
    auto current_stats = getCurrentStats();
    auto detailed_stats = calculateStatistics();
    
    std::ostringstream report;
    report << "=================================================\n";
    report << "ОТЧЁТ О ПРОИЗВОДИТЕЛЬНОСТИ\n";
    report << "=================================================\n";
    report << "Итераций: " << current_stats.iterations << "\n";
    report << "Кошельков: " << current_stats.wallets << "\n";
    report << "Совпадений: " << current_stats.matches << "\n";
    report << "Прошло времени: " << current_stats.elapsed_time << " сек\n";
    report << "Скорость итераций: " << current_stats.iter_per_sec << " /сек\n";
    report << "Скорость кошельков: " << current_stats.wallets_per_sec << " /сек\n";
    report << "=================================================\n";
    
    if (detailed_stats.iterations_available) {
        report << "СТАТИСТИКА ИТЕРАЦИЙ:\n";
        report << "  Мин: " << detailed_stats.iterations_min << "\n";
        report << "  Макс: " << detailed_stats.iterations_max << "\n";
        report << "  Среднее: " << detailed_stats.iterations_mean << "\n";
        report << "  StdDev: " << detailed_stats.iterations_std << "\n";
    }
    
    return report.str();
}
// END_FUNCTION_GetPerformanceReport
