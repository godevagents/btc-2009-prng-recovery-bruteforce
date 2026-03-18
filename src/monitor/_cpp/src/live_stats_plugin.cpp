// FILE: src/monitor/_cpp/src/live_stats_plugin.cpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Реализация плагина live-мониторинга процесса генерации кошельков на C++.
// SCOPE: Реализация методов LiveStatsPlugin, статистические вычисления
// INPUT: Заголовочный файл live_stats_plugin.hpp
// OUTPUT: Скомпилированный объектный код
// KEYWORDS: [DOMAIN(9): LiveMonitoring; DOMAIN(8): PluginSystem; TECH(6): Implementation]
// END_MODULE_CONTRACT

#include "live_stats_plugin.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/chrono.h>

namespace py = pybind11;

// ============================================================================
// ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ЛОГИРОВАНИЯ (объявлены до использования)
// ============================================================================

static std::string _get_timestamp() {
    auto now = std::time(nullptr);
    auto tm = *std::localtime(&now);
    std::ostringstream oss;
    oss << std::put_time(&tm, "%Y-%m-%d %H:%M:%S");
    return oss.str();
}

inline void log_debug(const std::string& message) {
    std::cout << _get_timestamp() << " [DEBUG] " << message << std::endl;
}

inline void log_info(const std::string& message) {
    std::cout << _get_timestamp() << " [INFO] " << message << std::endl;
}

inline void log_error(const std::string& message) {
    std::cout << _get_timestamp() << " [ERROR] " << message << std::endl;
}

// ============================================================================
// START_CONSTANTS_DEFINITION
// Статические константы класса LiveStatsPlugin
const std::string LiveStatsPlugin::VERSION = "1.0.0";
const std::string LiveStatsPlugin::AUTHOR = "Wallet Generator Team";
const std::string LiveStatsPlugin::DESCRIPTION = "Плагин live-мониторинга метрик генерации";
// END_CONSTANTS_DEFINITION


// START_CONSTRUCTOR_LIVE_STATS_PLUGIN
// START_CONTRACT:
// PURPOSE: Конструктор плагина live-мониторинга
// OUTPUTS: Инициализированный объект LiveStatsPlugin
// SIDE_EFFECTS: Создаёт хранилище истории метрик; инициализирует кольцевые буферы
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
LiveStatsPlugin::LiveStatsPlugin()
    : BaseMonitorPlugin("live_stats", 20)  // priority = 20
    , _is_monitoring(false)
    , _start_timestamp(0.0)
    , _last_update_time(0.0)
    , _last_iteration_count(0)
    , _last_wallet_count(0)
    , _last_match_count(0)
{
    log_debug("[LiveStatsPlugin][INIT][ConditionCheck] Инициализирован плагин live-мониторинга");
}
// END_CONSTRUCTOR_LIVE_STATS_PLUGIN


// START_METHOD_INITIALIZE
// START_CONTRACT:
// PURPOSE: Инициализация плагина и регистрация UI компонентов в главном приложении
// INPUTS:
// - app: py::object — ссылка на главное приложение мониторинга
// OUTPUTS: void
// SIDE_EFFECTS: Создаёт UI компоненты для отображения метрик; регистрирует плагин в главном приложении
// KEYWORDS: [DOMAIN(8): PluginSetup; CONCEPT(6): Registration]
// END_CONTRACT
void LiveStatsPlugin::initialize(py::object app) {
    _app = app;
    
    // Построение UI компонентов
    build_ui_components();
    
    // Регистрация в приложении
    if (py::hasattr(app, "register_stage")) {
        try {
            app.attr("register_stage")(
                "live_monitoring",
                "Live мониторинг",
                get_priority(),
                _gradio_components,
                py::none()
            );
        } catch (const py::error_already_set& e) {
            log_error("[LiveStatsPlugin][INITIALIZE][ExceptionCaught] Ошибка при регистрации stage: " + std::string(e.what()));
        }
    }
    
    log_info("[LiveStatsPlugin][INITIALIZE][StepComplete] Плагин live-мониторинга инициализирован");
}
// END_METHOD_INITIALIZE


// START_METHOD_BUILD_UI_COMPONENTS
// START_CONTRACT:
// PURPOSE: Построение UI компонентов для отображения live-метрик
// OUTPUTS: void
// SIDE_EFFECTS: Создаёт Gradio-компоненты для метрик и графиков
// KEYWORDS: [DOMAIN(8): UIComponents; TECH(7): Gradio]
// END_CONTRACT
void LiveStatsPlugin::build_ui_components() {
    // Создание Python словаря для компонентов
    _gradio_components = py::dict();
    
    // Импорт gradio
    py::object gr = py::module_::import("gradio");
    
    // Основные компоненты статистики
    _gradio_components["iteration_count"] = gr.attr("Number")(
        py::arg("label") = "Итерации",
        py::arg("value") = 0,
        py::arg("interactive") = false
    );
    
    _gradio_components["wallet_count"] = gr.attr("Number")(
        py::arg("label") = "Кошельки",
        py::arg("value") = 0,
        py::arg("interactive") = false
    );
    
    _gradio_components["match_count"] = gr.attr("Number")(
        py::arg("label") = "Совпадения",
        py::arg("value") = 0,
        py::arg("interactive") = false
    );
    
    // Компоненты времени
    _gradio_components["elapsed_time"] = gr.attr("Number")(
        py::arg("label") = "Прошло времени (сек)",
        py::arg("value") = 0,
        py::arg("interactive") = false
    );
    
    _gradio_components["iter_per_sec"] = gr.attr("Number")(
        py::arg("label") = "Итераций/сек",
        py::arg("value") = 0,
        py::arg("interactive") = false
    );
    
    _gradio_components["wallets_per_sec"] = gr.attr("Number")(
        py::arg("label") = "Кошельков/сек",
        py::arg("value") = 0,
        py::arg("interactive") = false
    );
    
    // Компонент энтропии
    _gradio_components["entropy_display"] = gr.attr("JSON")(
        py::arg("label") = "Энтропия",
        py::arg("value") = py::dict()
    );
    
    // Графики производительности
    py::dict empty_plot = get_empty_plot_data();
    
    _gradio_components["iterations_chart"] = gr.attr("LinePlot")(
        py::arg("value") = empty_plot,
        py::arg("label") = "Итерации за последние 100 итераций",
        py::arg("x") = "x",
        py::arg("y") = "y",
        py::arg("height") = 200
    );
    
    _gradio_components["wallets_chart"] = gr.attr("LinePlot")(
        py::arg("value") = empty_plot,
        py::arg("label") = "Кошельки за последние 100 итераций",
        py::arg("x") = "x",
        py::arg("y") = "y",
        py::arg("height") = 200
    );
    
    // Статус
    _gradio_components["status"] = gr.attr("HTML")(
        py::arg("value") = get_status_html(0),
        py::arg("label") = "Статус"
    );
    
    log_debug("[LiveStatsPlugin][BUILD_UI_COMPONENTS][StepComplete] UI компоненты созданы");
}
// END_METHOD_BUILD_UI_COMPONENTS


// START_METHOD_ON_METRIC_UPDATE
// START_CONTRACT:
// PURPOSE: Обработка обновления метрик от генератора
// INPUTS:
// - metrics: py::dict — словарь метрик
// OUTPUTS: void
// SIDE_EFFECTS: Обновляет историю метрик; вычисляет дельты; обновляет энтропию
// KEYWORDS: [DOMAIN(9): MetricsProcessing; CONCEPT(7): EventHandler]
// END_CONTRACT
void LiveStatsPlugin::on_metric_update(py::dict metrics) {
    double current_time = get_current_time();
    
    // START_BLOCK_EXTRACT_METRICS: [Извлечение метрик из словаря]
    int64_t iteration_count = 0;
    int64_t wallet_count = 0;
    int64_t match_count = 0;
    py::dict entropy_data;
    
    try {
        if (metrics.contains("iteration_count")) {
            iteration_count = metrics["iteration_count"].cast<int64_t>();
        }
        if (metrics.contains("wallet_count")) {
            wallet_count = metrics["wallet_count"].cast<int64_t>();
        }
        if (metrics.contains("match_count")) {
            match_count = metrics["match_count"].cast<int64_t>();
        }
        if (metrics.contains("entropy_data")) {
            entropy_data = metrics["entropy_data"].cast<py::dict>();
        }
    } catch (const py::error_already_set& e) {
        log_error("[LiveStatsPlugin][ON_METRIC_UPDATE][ExceptionCaught] Ошибка при извлечении метрик: " + std::string(e.what()));
        return;
    }
    // END_BLOCK_EXTRACT_METRICS
    
    // START_BLOCK_UPDATE_HISTORY: [Обновление истории метрик]
    _history_timestamps.push(current_time);
    
    // Вычисление дельт (скорость)
    double iteration_delta = static_cast<double>(iteration_count - _last_iteration_count);
    double wallet_delta = static_cast<double>(wallet_count - _last_wallet_count);
    double match_delta = static_cast<double>(match_count - _last_match_count);
    
    _history_iterations.push(iteration_delta);
    _history_wallets.push(wallet_delta);
    _history_matches.push(match_delta);
    
    _last_iteration_count = iteration_count;
    _last_wallet_count = wallet_count;
    _last_match_count = match_count;
    // END_BLOCK_UPDATE_HISTORY
    
    // START_BLOCK_ENTROPY_SAMPLING: [Сэмплирование энтропии]
    if (!entropy_data.empty()) {
        try {
            if (entropy_data.contains("total_bits")) {
                double entropy_value = entropy_data["total_bits"].cast<double>();
                if (entropy_value > 0) {
                    _entropy_samples.push(entropy_value);
                }
            }
        } catch (const py::error_already_set& e) {
            log_error("[LiveStatsPlugin][ON_METRIC_UPDATE][ExceptionCaught] Ошибка при извлечении энтропии: " + std::string(e.what()));
        }
    }
    // END_BLOCK_ENTROPY_SAMPLING
    
    // START_BLOCK_CHECK_MONITORING_STATE: [Проверка состояния мониторинга]
    if (!_is_monitoring && iteration_count > 0) {
        _is_monitoring = true;
        if (_start_timestamp == 0.0) {
            _start_timestamp = current_time;
        }
    }
    // END_BLOCK_CHECK_MONITORING_STATE
    
    _last_update_time = current_time;
    
    // Логирование отладочной информации
    std::stringstream ss;
    ss << "[LiveStatsPlugin][ON_METRIC_UPDATE][Info] Итераций: " << iteration_count 
       << ", Кошельков: " << wallet_count << ", Совпадений: " << match_count;
    log_debug(ss.str());
}
// END_METHOD_ON_METRIC_UPDATE


// START_METHOD_ON_SHUTDOWN
// START_CONTRACT:
// PURPOSE: Действия при завершении работы мониторинга
// OUTPUTS: void
// SIDE_EFFECTS: Сбрасывает состояние мониторинга
// KEYWORDS: [CONCEPT(8): Cleanup]
// END_CONTRACT
void LiveStatsPlugin::on_shutdown() {
    _is_monitoring = false;
    log_info("[LiveStatsPlugin][ON_SHUTDOWN][StepComplete] Плагин live-мониторинга остановлен");
}
// END_METHOD_ON_SHUTDOWN


// START_METHOD_GET_UI_COMPONENTS
// START_CONTRACT:
// PURPOSE: Получение UI компонентов плагина для отображения
// OUTPUTS: py::object — словарь UI компонентов
// KEYWORDS: [PATTERN(6): UI; CONCEPT(5): Getter]
// END_CONTRACT
py::object LiveStatsPlugin::get_ui_components() {
    return _gradio_components;
}
// END_METHOD_GET_UI_COMPONENTS


// START_METHOD_RESET_STATS
// START_CONTRACT:
// PURPOSE: Сброс статистики мониторинга
// OUTPUTS: void
// SIDE_EFFECTS: Очищает историю метрик и сбрасывает счётчики
// KEYWORDS: [CONCEPT(7): Reset]
// END_CONTRACT
void LiveStatsPlugin::reset_stats() {
    _history_iterations.clear();
    _history_wallets.clear();
    _history_matches.clear();
    _history_timestamps.clear();
    _entropy_samples.clear();
    
    _is_monitoring = false;
    _start_timestamp = 0.0;
    _last_update_time = 0.0;
    _last_iteration_count = 0;
    _last_wallet_count = 0;
    _last_match_count = 0;
    
    log_info("[LiveStatsPlugin][RESET_STATS][StepComplete] Статистика сброшена");
}
// END_METHOD_RESET_STATS


// START_METHOD_GET_CURRENT_STATS
// START_CONTRACT:
// PURPOSE: Получение текущей статистики
// OUTPUTS: CurrentStats — структура текущей статистики
// KEYWORDS: [CONCEPT(5): Getter]
// END_CONTRACT
CurrentStats LiveStatsPlugin::get_current_stats() const {
    CurrentStats stats;
    
    stats.iterations = _last_iteration_count;
    stats.wallets = _last_wallet_count;
    stats.matches = _last_match_count;
    stats.is_monitoring = _is_monitoring;
    
    double elapsed = 0.0;
    if (_start_timestamp > 0.0) {
        elapsed = get_current_time() - _start_timestamp;
    }
    stats.elapsed_time = elapsed;
    
    if (elapsed > 0.0 && _last_iteration_count > 0) {
        stats.iter_per_sec = static_cast<double>(_last_iteration_count) / elapsed;
        stats.wallets_per_sec = static_cast<double>(_last_wallet_count) / elapsed;
    }
    
    return stats;
}
// END_METHOD_GET_CURRENT_STATS


// START_METHOD_GET_CURRENT_STATS_PY
// START_CONTRACT:
// PURPOSE: Получение текущей статистики в виде Python словаря
// OUTPUTS: py::dict — словарь текущей статистики
// KEYWORDS: [CONCEPT(5): Getter; PATTERN(7): PythonBinding]
// END_CONTRACT
py::dict LiveStatsPlugin::get_current_stats_py() const {
    CurrentStats stats = get_current_stats();
    
    py::dict result;
    result["iterations"] = stats.iterations;
    result["wallets"] = stats.wallets;
    result["matches"] = stats.matches;
    result["elapsed_time"] = stats.elapsed_time;
    result["iter_per_sec"] = stats.iter_per_sec;
    result["wallets_per_sec"] = stats.wallets_per_sec;
    result["is_monitoring"] = stats.is_monitoring;
    
    return result;
}
// END_METHOD_GET_CURRENT_STATS_PY


// START_METHOD_GET_ITERATION_HISTORY
// START_CONTRACT:
// PURPOSE: Получение истории итераций
// OUTPUTS: std::vector<double> — история итераций
// KEYWORDS: [CONCEPT(5): Getter]
// END_CONTRACT
std::vector<double> LiveStatsPlugin::get_iteration_history() const {
    return _history_iterations.get_all();
}
// END_METHOD_GET_ITERATION_HISTORY


// START_METHOD_GET_WALLET_HISTORY
// START_CONTRACT:
// PURPOSE: Получение истории кошельков
// OUTPUTS: std::vector<double> — история кошельков
// KEYWORDS: [CONCEPT(5): Getter]
// END_CONTRACT
std::vector<double> LiveStatsPlugin::get_wallet_history() const {
    return _history_wallets.get_all();
}
// END_METHOD_GET_WALLET_HISTORY


// START_METHOD_GET_MATCH_HISTORY
// START_CONTRACT:
// PURPOSE: Получения истории совпадений
// OUTPUTS: std::vector<double> — история совпадений
// KEYWORDS: [CONCEPT(5): Getter]
// END_CONTRACT
std::vector<double> LiveStatsPlugin::get_match_history() const {
    return _history_matches.get_all();
}
// END_METHOD_GET_MATCH_HISTORY


// START_METHOD_GET_PLOT_DATA
// START_CONTRACT:
// PURPOSE: Преобразование истории в данные для графика
// INPUTS:
// - history: const std::vector<double>& — история значений
// OUTPUTS: py::dict — словарь с ключами 'x' и 'y' для графика
// KEYWORDS: [CONCEPT(7): ChartData]
// END_CONTRACT
py::dict LiveStatsPlugin::get_plot_data(const std::vector<double>& history) const {
    if (history.empty()) {
        return get_empty_plot_data();
    }
    
    py::list x_values;
    py::list y_values;
    
    for (size_t i = 0; i < history.size(); ++i) {
        x_values.append(static_cast<int>(i));
        y_values.append(history[i]);
    }
    
    py::dict result;
    result["x"] = x_values;
    result["y"] = y_values;
    
    return result;
}
// END_METHOD_GET_PLOT_DATA


// START_METHOD_GET_EMPTY_PLOT_DATA
// START_CONTRACT:
// PURPOSE: Получение пустых данных для графика
// OUTPUTS: py::dict — пустые данные графика
// KEYWORDS: [CONCEPT(6): ChartData]
// END_CONTRACT
py::dict LiveStatsPlugin::get_empty_plot_data() const {
    py::dict result;
    result["x"] = py::list();
    result["y"] = py::list();
    return result;
}
// END_METHOD_GET_EMPTY_PLOT_DATA


// START_METHOD_GET_STATUS_HTML
// START_CONTRACT:
// PURPOSE: Генерация HTML статуса мониторинга
// INPUTS:
// - iteration_count: int64_t — текущий счётчик итераций
// OUTPUTS: std::string — HTML статус
// KEYWORDS: [CONCEPT(6): HTML]
// END_CONTRACT
std::string LiveStatsPlugin::get_status_html(int64_t iteration_count) const {
    std::string status_color = _is_monitoring ? _theme_colors.success : _theme_colors.warning;
    std::string status_text = _is_monitoring ? "Мониторинг активен" : "Ожидание запуска";
    
    std::ostringstream oss;
    oss << "<div style=\"padding: 10px; background: " << status_color << "20; border-radius: 8px; border: 2px solid " << status_color << ";\">";
    oss << "<h3 style=\"margin: 0; color: " << status_color << ";\">" << status_text << "</h3>";
    oss << "<p style=\"margin: 5px 0; color: #212121;\">Итераций: <strong style=\"color: #212121;\">" << iteration_count << "</strong></p>";
    oss << "</div>";
    
    return oss.str();
}
// END_METHOD_GET_STATUS_HTML


// START_METHOD_ON_ENTER_STAGE
// START_CONTRACT:
// PURPOSE: Обработчик входа на этап live-мониторинга
// OUTPUTS: void
// SIDE_EFFECTS: Сбрасывает историю метрик
// KEYWORDS: [CONCEPT(7): StageHandler]
// END_CONTRACT
void LiveStatsPlugin::on_enter_stage() {
    log_info("[LiveStatsPlugin][ON_ENTER_STAGE][StepComplete] Вход на этап live-мониторинга");
    reset_stats();
}
// END_METHOD_ON_ENTER_STAGE


// START_METHOD_CALCULATE_STATISTICS
// START_CONTRACT:
// PURPOSE: Вычисление статистических показателей
// OUTPUTS: py::dict — словарь статистических показателей
// KEYWORDS: [DOMAIN(8): Statistics; CONCEPT(7): Analysis]
// END_CONTRACT
py::dict LiveStatsPlugin::calculate_statistics() const {
    py::dict stats;
    
    // Статистика итераций
    std::vector<double> iterations_data = _history_iterations.get_all();
    if (!iterations_data.empty()) {
        Statistics iter_stats = calculate_stats(iterations_data);
        py::dict iter_dict;
        iter_dict["min"] = iter_stats.min;
        iter_dict["max"] = iter_stats.max;
        iter_dict["mean"] = iter_stats.mean;
        iter_dict["std"] = iter_stats.std;
        stats["iterations"] = iter_dict;
    }
    
    // Статистика кошельков
    std::vector<double> wallets_data = _history_wallets.get_all();
    if (!wallets_data.empty()) {
        Statistics wallet_stats = calculate_stats(wallets_data);
        py::dict wallet_dict;
        wallet_dict["min"] = wallet_stats.min;
        wallet_dict["max"] = wallet_stats.max;
        wallet_dict["mean"] = wallet_stats.mean;
        wallet_dict["std"] = wallet_stats.std;
        stats["wallets"] = wallet_dict;
    }
    
    // Статистика энтропии
    std::vector<double> entropy_data = _entropy_samples.get_all();
    if (!entropy_data.empty()) {
        Statistics entropy_stats = calculate_stats(entropy_data);
        py::dict entropy_dict;
        entropy_dict["min"] = entropy_stats.min;
        entropy_dict["max"] = entropy_stats.max;
        entropy_dict["mean"] = entropy_stats.mean;
        stats["entropy"] = entropy_dict;
    }
    
    return stats;
}
// END_METHOD_CALCULATE_STATISTICS


// START_METHOD_GET_PERFORMANCE_REPORT
// START_CONTRACT:
// PURPOSE: Получение текстового отчёта о производительности
// OUTPUTS: std::string — текстовый отчёт
// KEYWORDS: [DOMAIN(7): Reporting; CONCEPT(6): Summary]
// END_CONTRACT
std::string LiveStatsPlugin::get_performance_report() const {
    CurrentStats stats = get_current_stats();
    py::dict detailed_stats = calculate_statistics();
    
    std::ostringstream oss;
    oss << "==================================================\n";
    oss << "ОТЧЁТ О ПРОИЗВОДИТЕЛЬНОСТИ\n";
    oss << "==================================================\n";
    oss << "Итераций: " << stats.iterations << "\n";
    oss << "Кошельков: " << stats.wallets << "\n";
    oss << "Совпадений: " << stats.matches << "\n";
    oss << "Прошло времени: " << stats.elapsed_time << " сек\n";
    oss << "Скорость итераций: " << stats.iter_per_sec << " /сек\n";
    oss << "Скорость кошельков: " << stats.wallets_per_sec << " /сек\n";
    oss << "==================================================\n";
    
    // Добавление детальной статистики
    if (detailed_stats.contains("iterations")) {
        py::dict iter_stats = detailed_stats["iterations"].cast<py::dict>();
        oss << "СТАТИСТИКА ИТЕРАЦИЙ:\n";
        oss << "  Мин: " << iter_stats["min"].cast<double>() << "\n";
        oss << "  Макс: " << iter_stats["max"].cast<double>() << "\n";
        oss << "  Среднее: " << iter_stats["mean"].cast<double>() << "\n";
        oss << "  StdDev: " << iter_stats["std"].cast<double>() << "\n";
    }
    
    return oss.str();
}
// END_METHOD_GET_PERFORMANCE_REPORT


// START_METHOD_GET_ENTROPY_SUMMARY
// START_CONTRACT:
// PURPOSE: Получение сводки по энтропии
// OUTPUTS: py::dict — словарь сводки по энтропии
// KEYWORDS: [DOMAIN(6): Entropy; CONCEPT(6): Summary]
// END_CONTRACT
py::dict LiveStatsPlugin::get_entropy_summary() const {
    if (_entropy_samples.is_empty()) {
        py::dict result;
        result["available"] = false;
        return result;
    }
    
    std::vector<double> entropy_data = _entropy_samples.get_all();
    Statistics stats = calculate_stats(entropy_data);
    
    py::dict result;
    result["available"] = true;
    result["samples"] = static_cast<int>(_entropy_samples.size());
    result["min_bits"] = stats.min;
    result["max_bits"] = stats.max;
    result["avg_bits"] = stats.mean;
    
    // Текущее значение - последний элемент
    if (!_entropy_samples.is_empty()) {
        const double* last_ptr = _entropy_samples.last();
        if (last_ptr != nullptr) {
            result["current_bits"] = *last_ptr;
        }
    }
    
    return result;
}
// END_METHOD_GET_ENTROPY_SUMMARY


// START_METHOD_IS_MONITORING
// START_CONTRACT:
// PURPOSE: Проверка состояния мониторинга
// OUTPUTS: bool — True если мониторинг активен
// KEYWORDS: [CONCEPT(5): Getter]
// END_CONTRACT
bool LiveStatsPlugin::is_monitoring() const {
    return _is_monitoring;
}
// END_METHOD_IS_MONITORING


// START_HELPER_GET_CURRENT_TIME
// START_CONTRACT:
// PURPOSE: Получение текущего времени в секундах (UNIX timestamp)
// OUTPUTS: double — текущее время
// KEYWORDS: [CONCEPT(6): Timestamp]
// END_CONTRACT
double LiveStatsPlugin::get_current_time() const {
    auto now = std::chrono::system_clock::now();
    auto duration = now.time_since_epoch();
    return std::chrono::duration<double>(duration).count();
}
// END_HELPER_GET_CURRENT_TIME


// START_HELPER_CALCULATE_STATS
// START_CONTRACT:
// PURPOSE: Вычисление статистики для вектора данных
// INPUTS:
// - data: const std::vector<double>& — вектор данных
// OUTPUTS: Statistics — структура со статистическими показателями
// KEYWORDS: [DOMAIN(8): Statistics; CONCEPT(7): Analysis]
// END_CONTRACT
Statistics LiveStatsPlugin::calculate_stats(const std::vector<double>& data) const {
    Statistics stats;
    
    if (data.empty()) {
        return stats;
    }
    
    // Min и Max
    stats.min = *std::min_element(data.begin(), data.end());
    stats.max = *std::max_element(data.begin(), data.end());
    
    // Mean
    double sum = 0.0;
    for (double val : data) {
        sum += val;
    }
    stats.mean = sum / static_cast<double>(data.size());
    
    // Standard deviation
    double sq_sum = 0.0;
    for (double val : data) {
        double diff = val - stats.mean;
        sq_sum += diff * diff;
    }
    stats.std = std::sqrt(sq_sum / static_cast<double>(data.size()));
    
    return stats;
}
// END_HELPER_CALCULATE_STATS
