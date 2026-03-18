// FILE: src/monitor/_cpp/src/final_stats_plugin.cpp
// VERSION: 2.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Реализация плагина финальной статистики на C++.
// SCOPE: Реализация методов FinalStatsPlugin, FinalStatistics, SessionEntry, PerformanceMetrics
// INPUT: Заголовочный файл final_stats_plugin.hpp
// OUTPUT: Скомпилированный объектный код
// KEYWORDS: [DOMAIN(9): Statistics; DOMAIN(8): PluginSystem; TECH(6): Implementation]
// END_MODULE_CONTRACT

#include "final_stats_plugin.hpp"
#include "plugin_base.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <pybind11/chrono.h>
#include <ctime>
#include <iomanip>
#include <fstream>
#include <sstream>
#include <cstdlib>

namespace py = pybind11;

// START_CONSTANTS_DEFINITION
// Статические константы класса FinalStatsPlugin
const std::string FinalStatsPlugin::VERSION = "1.0.0";
const std::string FinalStatsPlugin::AUTHOR = "Wallet Generator Team";
const std::string FinalStatsPlugin::DESCRIPTION = "Плагин финальной статистики";
const int32_t FinalStatsPlugin::DEFAULT_PRIORITY = 30;
// END_CONSTANTS_DEFINITION


// START_FINAL_STATISTICS_IMPLEMENTATION

// START_CONSTRUCTOR_FINAL_STATISTICS_DEFAULT
// START_CONTRACT:
// PURPOSE: Конструктор по умолчанию для FinalStatistics
// OUTPUTS: Объект с пустыми значениями
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
FinalStatistics::FinalStatistics()
    : iteration_count(0)
    , match_count(0)
    , wallet_count(0)
    , runtime_seconds(0.0)
    , iterations_per_second(0.0)
    , wallets_per_second(0.0)
    , avg_iteration_time_ms(0.0)
    , start_timestamp(0.0)
    , end_timestamp(0.0)
    , list_path("")
    , metadata(py::none())
{
}
// END_CONSTRUCTOR_FINAL_STATISTICS_DEFAULT


// START_CONSTRUCTOR_FINAL_STATISTICS_PARAMS
// START_CONTRACT:
// PURPOSE: Конструктор с параметрами для FinalStatistics
// INPUTS:
// - iterations: int32_t — количество итераций
// - matches: int32_t — количество совпадений
// - wallets: int32_t — количество кошельков
// - runtime: double — время работы
// OUTPUTS: Инициализированный объект FinalStatistics
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
FinalStatistics::FinalStatistics(int32_t iterations, int32_t matches, int32_t wallets, double runtime)
    : iteration_count(iterations)
    , match_count(matches)
    , wallet_count(wallets)
    , runtime_seconds(runtime)
    , iterations_per_second(0.0)
    , wallets_per_second(0.0)
    , avg_iteration_time_ms(0.0)
    , start_timestamp(0.0)
    , end_timestamp(0.0)
    , list_path("")
    , metadata(py::none())
{
    // Вычисление производных показателей
    if (runtime > 0) {
        iterations_per_second = static_cast<double>(iterations) / runtime;
        wallets_per_second = static_cast<double>(wallets) / runtime;
    }
    if (iterations > 0 && runtime > 0) {
        avg_iteration_time_ms = (runtime / static_cast<double>(iterations)) * 1000.0;
    }
}
// END_CONSTRUCTOR_FINAL_STATISTICS_PARAMS


// START_METHOD_FINAL_STATISTICS_FROM_PYTHON
// START_CONTRACT:
// PURPOSE: Создание FinalStatistics из Python объекта
// INPUTS:
// - obj: py::object — Python объект (dict)
// OUTPUTS: FinalStatistics — созданные метрики
// KEYWORDS: [PATTERN(7): Factory; CONCEPT(6): PythonBinding]
// END_CONTRACT
FinalStatistics FinalStatistics::from_python(py::dict dict) {
    FinalStatistics stats;

    try {
        if (dict.contains("iteration_count")) {
            stats.iteration_count = dict["iteration_count"].cast<int32_t>();
        }
        if (dict.contains("match_count")) {
            stats.match_count = dict["match_count"].cast<int32_t>();
        }
        if (dict.contains("wallet_count")) {
            stats.wallet_count = dict["wallet_count"].cast<int32_t>();
        }
        if (dict.contains("runtime_seconds")) {
            stats.runtime_seconds = dict["runtime_seconds"].cast<double>();
        }
        if (dict.contains("iterations_per_second")) {
            stats.iterations_per_second = dict["iterations_per_second"].cast<double>();
        }
        if (dict.contains("wallets_per_second")) {
            stats.wallets_per_second = dict["wallets_per_second"].cast<double>();
        }
        if (dict.contains("avg_iteration_time_ms")) {
            stats.avg_iteration_time_ms = dict["avg_iteration_time_ms"].cast<double>();
        }
        if (dict.contains("start_timestamp")) {
            stats.start_timestamp = dict["start_timestamp"].cast<double>();
        }
        if (dict.contains("end_timestamp")) {
            stats.end_timestamp = dict["end_timestamp"].cast<double>();
        }
        if (dict.contains("list_path")) {
            stats.list_path = dict["list_path"].cast<std::string>();
        }
        if (dict.contains("metadata")) {
            stats.metadata = dict["metadata"];
        }
    } catch (const py::error_already_set& e) {
        std::cerr << "[FinalStatistics][FROM_PYTHON][ExceptionCaught] Ошибка при извлечении атрибутов: " << e.what() << std::endl;
    }

    return stats;
}
// END_METHOD_FINAL_STATISTICS_FROM_PYTHON


// START_METHOD_FINAL_STATISTICS_TO_PYTHON
// START_CONTRACT:
// PURPOSE: Конвертация FinalStatistics в Python словарь
// OUTPUTS: py::dict — Python словарь
// KEYWORDS: [CONCEPT(6): Converter; DOMAIN(8): PythonBinding]
// END_CONTRACT
py::dict FinalStatistics::to_python() const {
    py::dict dict;
    dict["iteration_count"] = iteration_count;
    dict["match_count"] = match_count;
    dict["wallet_count"] = wallet_count;
    dict["runtime_seconds"] = runtime_seconds;
    dict["iterations_per_second"] = iterations_per_second;
    dict["wallets_per_second"] = wallets_per_second;
    dict["avg_iteration_time_ms"] = avg_iteration_time_ms;
    dict["start_timestamp"] = start_timestamp;
    dict["end_timestamp"] = end_timestamp;
    dict["list_path"] = list_path;
    dict["metadata"] = metadata;
    return dict;
}
// END_METHOD_FINAL_STATISTICS_TO_PYTHON


// START_METHOD_FINAL_STATISTICS_IS_VALID
// START_CONTRACT:
// PURPOSE: Проверка валидности данных
// OUTPUTS: bool — true если данные валидны
// KEYWORDS: [CONCEPT(7): Validation]
// END_CONTRACT
bool FinalStatistics::is_valid() const {
    return iteration_count > 0 || match_count > 0 || wallet_count > 0;
}
// END_METHOD_FINAL_STATISTICS_IS_VALID


// START_METHOD_FINAL_STATISTICS_GET_FORMATTED_RUNTIME
// START_CONTRACT:
// PURPOSE: Получение времени работы в читаемом формате
// OUTPUTS: std::string — отформатированное время (HH:MM:SS)
// KEYWORDS: [CONCEPT(6): Formatting]
// END_CONTRACT
std::string FinalStatistics::get_formatted_runtime() const {
    int hours = static_cast<int>(runtime_seconds / 3600);
    int minutes = static_cast<int>((runtime_seconds - hours * 3600) / 60);
    int seconds = static_cast<int>(runtime_seconds - hours * 3600 - minutes * 60);

    std::ostringstream oss;
    oss << std::setfill('0') << std::setw(2) << hours << ":"
        << std::setfill('0') << std::setw(2) << minutes << ":"
        << std::setfill('0') << std::setw(2) << seconds;
    return oss.str();
}
// END_METHOD_FINAL_STATISTICS_GET_FORMATTED_RUNTIME

// END_FINAL_STATISTICS_IMPLEMENTATION


// START_SESSION_ENTRY_IMPLEMENTATION

// START_CONSTRUCTOR_SESSION_ENTRY_DEFAULT
// START_CONTRACT:
// PURPOSE: Конструктор по умолчанию для SessionEntry
// OUTPUTS: Объект с пустыми значениями
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
SessionEntry::SessionEntry()
    : session_id(0)
    , iteration_count(0)
    , match_count(0)
    , wallet_count(0)
    , runtime_seconds(0.0)
    , start_timestamp(0.0)
    , end_timestamp(0.0)
    , metrics(py::none())
{
}
// END_CONSTRUCTOR_SESSION_ENTRY_DEFAULT


// START_CONSTRUCTOR_SESSION_ENTRY_PARAMS
// START_CONTRACT:
// PURPOSE: Конструктор с параметрами для SessionEntry
// INPUTS:
// - session_id: int32_t — идентификатор сессии
// - iterations: int32_t — количество итераций
// - matches: int32_t — количество совпадений
// - wallets: int32_t — количество кошельков
// - runtime: double — время работы
// - start_time: double — время начала
// OUTPUTS: Инициализированный объект SessionEntry
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
SessionEntry::SessionEntry(int32_t session_id, int32_t iterations, int32_t matches, int32_t wallets, double runtime, double start_time)
    : session_id(session_id)
    , iteration_count(iterations)
    , match_count(matches)
    , wallet_count(wallets)
    , runtime_seconds(runtime)
    , start_timestamp(start_time)
    , end_timestamp(start_time + runtime)
    , metrics(py::none())
{
}
// END_CONSTRUCTOR_SESSION_ENTRY_PARAMS


// START_METHOD_SESSION_ENTRY_FROM_PYTHON
// START_CONTRACT:
// PURPOSE: Создание SessionEntry из Python объекта
// INPUTS:
// - obj: py::object — Python объект (dict)
// OUTPUTS: SessionEntry — созданная запись
// KEYWORDS: [PATTERN(7): Factory; CONCEPT(6): PythonBinding]
// END_CONTRACT
SessionEntry SessionEntry::from_python(py::dict dict) {
    SessionEntry entry;

    try {
        if (dict.contains("session_id")) {
            entry.session_id = dict["session_id"].cast<int32_t>();
        }
        if (dict.contains("iteration_count")) {
            entry.iteration_count = dict["iteration_count"].cast<int32_t>();
        }
        if (dict.contains("match_count")) {
            entry.match_count = dict["match_count"].cast<int32_t>();
        }
        if (dict.contains("wallet_count")) {
            entry.wallet_count = dict["wallet_count"].cast<int32_t>();
        }
        if (dict.contains("runtime_seconds")) {
            entry.runtime_seconds = dict["runtime_seconds"].cast<double>();
        }
        if (dict.contains("start_timestamp")) {
            entry.start_timestamp = dict["start_timestamp"].cast<double>();
        }
        if (dict.contains("end_timestamp")) {
            entry.end_timestamp = dict["end_timestamp"].cast<double>();
        }
        if (dict.contains("metrics")) {
            entry.metrics = dict["metrics"];
        }
    } catch (const py::error_already_set& e) {
        std::cerr << "[SessionEntry][FROM_PYTHON][ExceptionCaught] Ошибка при извлечении атрибутов: " << e.what() << std::endl;
    }

    return entry;
}
// END_METHOD_SESSION_ENTRY_FROM_PYTHON


// START_METHOD_SESSION_ENTRY_TO_PYTHON
// START_CONTRACT:
// PURPOSE: Конвертация SessionEntry в Python словарь
// OUTPUTS: py::dict — Python словарь
// KEYWORDS: [CONCEPT(6): Converter; DOMAIN(8): PythonBinding]
// END_CONTRACT
py::dict SessionEntry::to_python() const {
    py::dict dict;
    dict["session_id"] = session_id;
    dict["iteration_count"] = iteration_count;
    dict["match_count"] = match_count;
    dict["wallet_count"] = wallet_count;
    dict["runtime_seconds"] = runtime_seconds;
    dict["start_timestamp"] = start_timestamp;
    dict["end_timestamp"] = end_timestamp;
    dict["metrics"] = metrics;
    return dict;
}
// END_METHOD_SESSION_ENTRY_TO_PYTHON

// END_SESSION_ENTRY_IMPLEMENTATION


// START_PERFORMANCE_METRICS_IMPLEMENTATION

// START_CONSTRUCTOR_PERFORMANCE_METRICS_DEFAULT
// START_CONTRACT:
// PURPOSE: Конструктор по умолчанию для PerformanceMetrics
// OUTPUTS: Объект с пустыми значениями
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
PerformanceMetrics::PerformanceMetrics()
    : iterations(0)
    , runtime_seconds(0.0)
    , iter_per_sec(0.0)
    , estimated_hours_to_match(0.0)
    , probability_per_iteration(0.0)
    , available(false)
{
}
// END_CONSTRUCTOR_PERFORMANCE_METRICS_DEFAULT


// START_CONSTRUCTOR_PERFORMANCE_METRICS_PARAMS
// START_CONTRACT:
// PURPOSE: Конструктор с параметрами для PerformanceMetrics
// INPUTS:
// - iterations: int32_t — количество итераций
// - runtime: double — время работы
// - iter_per_sec: double — итераций в секунду
// - estimated_hours: double — оценка времени до совпадения
// - probability: double — вероятность совпадения
// OUTPUTS: Инициализированный объект PerformanceMetrics
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
PerformanceMetrics::PerformanceMetrics(int32_t iterations, double runtime, double iter_per_sec, double estimated_hours, double probability)
    : iterations(iterations)
    , runtime_seconds(runtime)
    , iter_per_sec(iter_per_sec)
    , estimated_hours_to_match(estimated_hours)
    , probability_per_iteration(probability)
    , available(true)
{
}
// END_CONSTRUCTOR_PERFORMANCE_METRICS_PARAMS


// START_METHOD_PERFORMANCE_METRICS_TO_PYTHON
// START_CONTRACT:
// PURPOSE: Конвертация PerformanceMetrics в Python словарь
// OUTPUTS: py::dict — Python словарь
// KEYWORDS: [CONCEPT(6): Converter; DOMAIN(8): PythonBinding]
// END_CONTRACT
py::dict PerformanceMetrics::to_python() const {
    py::dict dict;
    dict["available"] = available;
    dict["iterations"] = iterations;
    dict["runtime_seconds"] = runtime_seconds;
    dict["iter_per_sec"] = iter_per_sec;
    dict["estimated_hours_to_match"] = estimated_hours_to_match;
    dict["probability_per_iteration"] = probability_per_iteration;
    return dict;
}
// END_METHOD_PERFORMANCE_METRICS_TO_PYTHON

// END_PERFORMANCE_METRICS_IMPLEMENTATION


// START_FINAL_STATS_PLUGIN_IMPLEMENTATION


// START_CONSTRUCTOR_FINAL_STATS_PLUGIN
// START_CONTRACT:
// PURPOSE: Конструктор плагина финальной статистики
// OUTPUTS: Инициализированный объект плагина
// KEYWORDS: [CONCEPT(5): Initialization; DOMAIN(7): PluginSetup]
// END_CONTRACT
FinalStatsPlugin::FinalStatsPlugin()
    : BaseMonitorPlugin("FinalStatsPlugin", 30)  // Приоритет 30
    , _gradio_components(py::none())
    , _final_metrics()
    , _start_time(0.0)
    , _end_time(0.0)
    , _is_complete(false)
    , _session_history()
    , _session_counter(0)
{
    // Инициализация истории сессий
    _session_history = std::deque<SessionEntry>();
    _session_history.shrink_to_fit();

    std::stringstream ss;
    ss << "[FinalStatsPlugin][INIT][ConditionCheck] Инициализирован плагин финальной статистики с приоритетом 30";
    log_info(ss.str());
}
// END_CONSTRUCTOR_FINAL_STATS_PLUGIN


// START_DESTRUCTOR_FINAL_STATS_PLUGIN
// START_CONTRACT:
// PURPOSE: Деструктор плагина финальной статистики
// OUTPUTS: Освобождение ресурсов
// KEYWORDS: [CONCEPT(8): Cleanup]
// END_CONTRACT
FinalStatsPlugin::~FinalStatsPlugin() {
    log_info("[FinalStatsPlugin][DESTRUCTOR][StepComplete] Плагин финальной статистики уничтожен");
}
// END_DESTRUCTOR_FINAL_STATS_PLUGIN


// START_METHOD_INITIALIZE
// START_CONTRACT:
// PURPOSE: Инициализация плагина и регистрация UI компонентов
// INPUTS:
// - app: py::object — ссылка на главное приложение
// OUTPUTS: void
// KEYWORDS: [DOMAIN(8): PluginSetup; CONCEPT(6): Registration]
// END_CONTRACT
void FinalStatsPlugin::initialize(py::object app) {
    _app = app;

    // Построение UI компонентов
    _gradio_components = _build_ui_components();

    // Регистрация UI компонентов в приложении
    if (!py::isinstance<py::none>(_app) && py::hasattr(_app, "register_ui_component")) {
        try {
            _app.attr("register_ui_component")(_gradio_components, "FinalStats");
        } catch (const py::error_already_set& e) {
            std::cerr << "[FinalStatsPlugin][INITIALIZE][ExceptionCaught] Ошибка при регистрации UI: " << e.what() << std::endl;
        }
    }

    std::stringstream ss;
    ss << "[FinalStatsPlugin][INITIALIZE][StepComplete] Плагин финальной статистики инициализирован";
    log_info(ss.str());
}
// END_METHOD_INITIALIZE


// START_METHOD_ON_METRIC_UPDATE
// START_CONTRACT:
// PURPOSE: Обработка обновления метрик (заглушка)
// INPUTS:
// - metrics: py::dict — словарь метрик
// OUTPUTS: void
// KEYWORDS: [DOMAIN(6): Placeholder]
// END_CONTRACT
void FinalStatsPlugin::on_metric_update(py::dict metrics) {
    // Заглушка - на этом этапе метрики не обновляются
    // Они фиксируются только при завершении
}
// END_METHOD_ON_METRIC_UPDATE


// START_METHOD_ON_SHUTDOWN
// START_CONTRACT:
// PURPOSE: Завершение работы плагина
// OUTPUTS: void
// KEYWORDS: [CONCEPT(8): Cleanup; DOMAIN(7): Shutdown]
// END_CONTRACT
void FinalStatsPlugin::on_shutdown() {
    _end_time = _get_current_time();

    std::stringstream ss;
    ss << "[FinalStatsPlugin][ON_SHUTDOWN][StepComplete] Плагин финальной статистики остановлен";
    log_info(ss.str());
}
// END_METHOD_ON_SHUTDOWN


// START_METHOD_GET_UI_COMPONENTS
// START_CONTRACT:
// PURPOSE: Получение UI компонентов плагина
// OUTPUTS: py::object — UI компоненты
// KEYWORDS: [PATTERN(6): UI; CONCEPT(5): Getter]
// END_CONTRACT
py::object FinalStatsPlugin::get_ui_components() {
    return _gradio_components;
}
// END_METHOD_GET_UI_COMPONENTS


// START_METHOD_UPDATE_UI
// START_CONTRACT:
// PURPOSE: Обновление UI компонентов значениями из финальных метрик
// OUTPUTS: py::object — словарь с обновлёнными значениями
// KEYWORDS: [DOMAIN(9): UIUpdate; TECH(7): Gradio]
// END_CONTRACT
py::object FinalStatsPlugin::update_ui() {
    py::dict updates;

    if (_final_metrics.iteration_count == 0 && _final_metrics.match_count == 0) {
        log_warning("[FinalStatsPlugin][UPDATE_UI][Warning] Нет финальных метрик для обновления UI");
        return updates;
    }

    // Получаем значения из метрик
    int32_t iterations = _final_metrics.iteration_count;
    int32_t matches = _final_metrics.match_count;
    int32_t wallets = _final_metrics.wallet_count;
    double runtime = _final_metrics.runtime_seconds;
    double iter_per_sec = _final_metrics.iterations_per_second;
    double wallets_per_sec = _final_metrics.wallets_per_second;
    double avg_iter_ms = _final_metrics.avg_iteration_time_ms;

    // Обновляем компоненты
    updates["total_iterations"] = iterations;
    updates["total_matches"] = matches;
    updates["total_wallets"] = wallets;
    updates["runtime"] = runtime;
    updates["runtime_formatted"] = _format_time(runtime);
    updates["avg_iteration_time"] = avg_iter_ms;
    updates["iterations_per_second"] = iter_per_sec;
    updates["wallets_per_second"] = wallets_per_sec;
    updates["detailed_stats"] = _final_metrics.to_python();

    std::stringstream ss;
    ss << "[FinalStatsPlugin][UPDATE_UI][StepComplete] UI обновлён: " << iterations << " итераций, " << runtime << " сек";
    log_info(ss.str());

    return updates;
}
// END_METHOD_UPDATE_UI


// START_METHOD_GET_FINAL_METRICS
// START_CONTRACT:
// PURPOSE: Получение финальных метрик
// OUTPUTS: py::dict — копия финальных метрик
// KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): Statistics]
// END_CONTRACT
py::dict FinalStatsPlugin::get_final_metrics() const {
    return _final_metrics.to_python();
}
// END_METHOD_GET_FINAL_METRICS


// START_METHOD_GET_SUMMARY
// START_CONTRACT:
// PURPOSE: Получение текстовой сводки
// OUTPUTS: std::string — текстовая сводка
// KEYWORDS: [CONCEPT(6): Summary; DOMAIN(8): Statistics]
// END_CONTRACT
std::string FinalStatsPlugin::get_summary() const {
    if (_final_metrics.iteration_count == 0 && _final_metrics.match_count == 0) {
        return "Нет данных";
    }

    std::stringstream ss;
    ss << "==================================================\n";
    ss << "ФИНАЛЬНАЯ СТАТИСТИКА\n";
    ss << "==================================================\n";
    ss << "Итераций: " << _final_metrics.iteration_count << "\n";
    ss << "Совпадений: " << _final_metrics.match_count << "\n";
    ss << "Кошельков: " << _final_metrics.wallet_count << "\n";
    ss << "Время работы: " << _format_time(_final_metrics.runtime_seconds) << "\n";
    ss << "Итераций/сек: " << _final_metrics.iterations_per_second << "\n";
    ss << "==================================================\n";

    return ss.str();
}
// END_METHOD_GET_SUMMARY


// START_METHOD_EXPORT_JSON
// START_CONTRACT:
// PURPOSE: Экспорт статистики в JSON файл
// INPUTS:
// - file_path: const std::string& — путь к файлу
// OUTPUTS: bool — успех/неудача
// KEYWORDS: [DOMAIN(7): Export; TECH(5): JSON]
// END_CONTRACT
bool FinalStatsPlugin::export_json(const std::string& file_path) const {
    try {
        std::ofstream file(file_path);
        if (!file.is_open()) {
            std::cerr << "[FinalStatsPlugin][EXPORT_JSON][Error] Не удалось открыть файл: " << file_path << std::endl;
            return false;
        }

        // Получаем Python словарь и записываем вручную
        py::dict data = _final_metrics.to_python();

        // Простая сериализация в JSON
        file << "{\n";
        file << "  \"iteration_count\": " << _final_metrics.iteration_count << ",\n";
        file << "  \"match_count\": " << _final_metrics.match_count << ",\n";
        file << "  \"wallet_count\": " << _final_metrics.wallet_count << ",\n";
        file << "  \"runtime_seconds\": " << std::fixed << std::setprecision(6) << _final_metrics.runtime_seconds << ",\n";
        file << "  \"iterations_per_second\": " << _final_metrics.iterations_per_second << ",\n";
        file << "  \"wallets_per_second\": " << _final_metrics.wallets_per_second << ",\n";
        file << "  \"avg_iteration_time_ms\": " << _final_metrics.avg_iteration_time_ms << ",\n";
        file << "  \"start_timestamp\": " << _final_metrics.start_timestamp << ",\n";
        file << "  \"end_timestamp\": " << _final_metrics.end_timestamp << ",\n";
        file << "  \"list_path\": \"" << _final_metrics.list_path << "\"\n";
        file << "}\n";

        file.close();

        std::stringstream ss;
        ss << "[FinalStatsPlugin][EXPORT_JSON][StepComplete] Экспорт в " << file_path;
        std::cout << ss.str() << std::endl;

        return true;
    } catch (const std::exception& e) {
        std::cerr << "[FinalStatsPlugin][EXPORT_JSON][ExceptionCaught] Ошибка при экспорте: " << e.what() << std::endl;
        return false;
    }
}
// END_METHOD_EXPORT_JSON


// START_METHOD_EXPORT_CSV
// START_CONTRACT:
// PURPOSE: Экспорт статистики в CSV файл
// INPUTS:
// - file_path: const std::string& — путь к файлу
// OUTPUTS: bool — успех/неудача
// KEYWORDS: [DOMAIN(7): Export; TECH(5): CSV]
// END_CONTRACT
bool FinalStatsPlugin::export_csv(const std::string& file_path) const {
    try {
        std::ofstream file(file_path);
        if (!file.is_open()) {
            std::cerr << "[FinalStatsPlugin][EXPORT_CSV][Error] Не удалось открыть файл: " << file_path << std::endl;
            return false;
        }

        // Запись заголовка
        file << "Параметр,Значение\n";

        // Запись данных
        file << "iteration_count," << _final_metrics.iteration_count << "\n";
        file << "match_count," << _final_metrics.match_count << "\n";
        file << "wallet_count," << _final_metrics.wallet_count << "\n";
        file << "runtime_seconds," << std::fixed << std::setprecision(6) << _final_metrics.runtime_seconds << "\n";
        file << "iterations_per_second," << _final_metrics.iterations_per_second << "\n";
        file << "wallets_per_second," << _final_metrics.wallets_per_second << "\n";
        file << "avg_iteration_time_ms," << _final_metrics.avg_iteration_time_ms << "\n";
        file << "list_path," << _final_metrics.list_path << "\n";

        file.close();

        std::stringstream ss;
        ss << "[FinalStatsPlugin][EXPORT_CSV][StepComplete] Экспорт в " << file_path;
        std::cout << ss.str() << std::endl;

        return true;
    } catch (const std::exception& e) {
        std::cerr << "[FinalStatsPlugin][EXPORT_CSV][ExceptionCaught] Ошибка при экспорте: " << e.what() << std::endl;
        return false;
    }
}
// END_METHOD_EXPORT_CSV


// START_METHOD_EXPORT_TXT
// START_CONTRACT:
// PURPOSE: Экспорт статистики в TXT файл (читаемый формат)
// INPUTS:
// - file_path: const std::string& — путь к файлу
// OUTPUTS: std::string — путь к файлу или сообщение об ошибке
// KEYWORDS: [DOMAIN(7): Export; TECH(5): TXT]
// END_CONTRACT
std::string FinalStatsPlugin::export_txt(const std::string& file_path) const {
    try {
        std::ofstream file(file_path);
        if (!file.is_open()) {
            std::string error_msg = "Не удалось открыть файл: " + file_path;
            std::cerr << "[FinalStatsPlugin][EXPORT_TXT][Error] " << error_msg << std::endl;
            return error_msg;
        }

        // Запись заголовка
        file << "============================================================\n";
        file << "ФИНАЛЬНАЯ СТАТИСТИКА ГЕНЕРАТОРА КОШЕЛЬКОВ\n";
        file << "============================================================\n\n";

        // Время работы
        file << "ВРЕМЯ РАБОТЫ:\n";
        file << "  Общее время: " << _format_time(_final_metrics.runtime_seconds);
        file << " (" << std::fixed << std::setprecision(2) << _final_metrics.runtime_seconds << " сек)\n\n";

        // Итерации
        file << "ИТЕРАЦИИ:\n";
        file << "  Всего итераций: " << _final_metrics.iteration_count << "\n\n";

        // Кошельки
        file << "КОШЕЛЬКИ:\n";
        file << "  Сгенерировано кошельков: " << _final_metrics.wallet_count << "\n\n";

        // Совпадения
        file << "СОВПАДЕНИЯ:\n";
        file << "  Найдено совпадений: " << _final_metrics.match_count << "\n\n";

        // Производительность
        file << "ПРОИЗВОДИТЕЛЬНОСТЬ:\n";
        file << "  Итераций в секунду: " << std::fixed << std::setprecision(2) << _final_metrics.iterations_per_second << "\n";
        file << "  Кошельков в секунду: " << _final_metrics.wallets_per_second << "\n";
        file << "  Среднее время итерации: " << std::fixed << std::setprecision(4) << _final_metrics.avg_iteration_time_ms << " мс\n\n";

        // Используемый LIST
        file << "ИСПОЛЬЗУЕМЫЙ СПИСОК:\n";
        file << "  " << _final_metrics.list_path << "\n\n";

        // Timestamp
        if (_final_metrics.end_timestamp > 0) {
            file << "ДАТА ЗАВЕРШЕНИЯ:\n";
            std::time_t time_val = static_cast<std::time_t>(_final_metrics.end_timestamp);
            std::tm* tm_val = std::localtime(&time_val);
            file << "  " << std::put_time(tm_val, "%Y-%m-%d %H:%M:%S") << "\n\n";
        }

        file << "============================================================\n";
        file << "КОНЕЦ ОТЧЁТА\n";
        file << "============================================================\n";

        file.close();

        std::stringstream ss;
        ss << "[FinalStatsPlugin][EXPORT_TXT][StepComplete] Экспорт в " << file_path;
        std::cout << ss.str() << std::endl;

        return file_path;
    } catch (const std::exception& e) {
        std::string error_msg = "Ошибка экспорта в TXT: " + std::string(e.what());
        std::cerr << "[FinalStatsPlugin][EXPORT_TXT][ExceptionCaught] " << error_msg << std::endl;
        return error_msg;
    }
}
// END_METHOD_EXPORT_TXT


// START_METHOD_GET_PERFORMANCE_ANALYSIS
// START_CONTRACT:
// PURPOSE: Получение анализа производительности
// OUTPUTS: py::dict — анализ производительности
// KEYWORDS: [DOMAIN(8): Performance; CONCEPT(7): Analysis]
// END_CONTRACT
py::dict FinalStatsPlugin::get_performance_analysis() const {
    py::dict analysis;

    if (_final_metrics.iteration_count == 0) {
        analysis["available"] = false;
        return analysis;
    }

    // Оценка времени до успеха
    // Предполагаем 1/1000000000 шанс на совпадение
    const int64_t expected_iterations = 1000000000;
    double estimated_time_hours = 0.0;

    if (_final_metrics.iteration_count > 0 && _final_metrics.runtime_seconds > 0) {
        estimated_time_hours = (static_cast<double>(expected_iterations) / _final_metrics.iteration_count) *
                               (_final_metrics.runtime_seconds / 3600.0);
    }

    analysis["available"] = true;
    analysis["iterations"] = _final_metrics.iteration_count;
    analysis["runtime_seconds"] = _final_metrics.runtime_seconds;
    analysis["iter_per_sec"] = _final_metrics.iterations_per_second;
    analysis["estimated_hours_to_match"] = estimated_time_hours;
    analysis["probability_per_iteration"] = 1.0 / static_cast<double>(expected_iterations);

    return analysis;
}
// END_METHOD_GET_PERFORMANCE_ANALYSIS


// START_METHOD_IS_COMPLETE
// START_CONTRACT:
// PURPOSE: Проверка завершения сбора статистики
// OUTPUTS: bool — True если статистика собрана
// KEYWORDS: [CONCEPT(5): Getter]
// END_CONTRACT
bool FinalStatsPlugin::is_complete() const {
    return _is_complete;
}
// END_METHOD_IS_COMPLETE


// START_METHOD_RESET
// START_CONTRACT:
// PURPOSE: Сброс статистики
// OUTPUTS: void
// SIDE_EFFECTS: Очищает все данные
// KEYWORDS: [CONCEPT(7): Reset]
// END_CONTRACT
void FinalStatsPlugin::reset() {
    _final_metrics = FinalStatistics();
    _start_time = 0.0;
    _end_time = 0.0;
    _is_complete = false;
    _session_history.clear();
    _session_counter = 0;

    log_info("[FinalStatsPlugin][RESET][StepComplete] Статистика сброшена");
}
// END_METHOD_RESET


// START_METHOD_ADD_SESSION
// START_CONTRACT:
// PURPOSE: Добавление сессии в историю
// INPUTS:
// - metrics: py::dict — метрики сессии
// OUTPUTS: void
// KEYWORDS: [CONCEPT(7): History]
// END_CONTRACT
void FinalStatsPlugin::add_session(py::dict metrics) {
    _session_counter++;

    SessionEntry entry;
    entry.session_id = _session_counter;

    if (metrics.contains("iteration_count")) {
        entry.iteration_count = metrics["iteration_count"].cast<int32_t>();
    }
    if (metrics.contains("match_count")) {
        entry.match_count = metrics["match_count"].cast<int32_t>();
    }
    if (metrics.contains("wallet_count")) {
        entry.wallet_count = metrics["wallet_count"].cast<int32_t>();
    }
    if (metrics.contains("runtime_seconds")) {
        entry.runtime_seconds = metrics["runtime_seconds"].cast<double>();
    }
    if (metrics.contains("start_timestamp")) {
        entry.start_timestamp = metrics["start_timestamp"].cast<double>();
    }

    entry.end_timestamp = entry.start_timestamp + entry.runtime_seconds;
    entry.metrics = metrics;

    _session_history.push_back(entry);

    std::stringstream ss;
    ss << "[FinalStatsPlugin][ADD_SESSION][StepComplete] Сессия добавлена: " << _session_history.size();
    log_debug(ss.str());
}
// END_METHOD_ADD_SESSION


// START_METHOD_GET_SESSION_HISTORY
// START_CONTRACT:
// PURPOSE: Получение истории сессий
// OUTPUTS: py::list — история сессий
// KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): SessionHistory]
// END_CONTRACT
py::list FinalStatsPlugin::get_session_history() const {
    py::list result;

    for (const auto& entry : _session_history) {
        result.append(entry.to_python());
    }

    return result;
}
// END_METHOD_GET_SESSION_HISTORY


// START_METHOD_GET_TOTAL_STATISTICS
// START_CONTRACT:
// PURPOSE: Получение общей статистики по всем сессиям
// OUTPUTS: py::dict — общая статистика
// KEYWORDS: [DOMAIN(8): Aggregation; CONCEPT(7): Statistics]
// END_CONTRACT
py::dict FinalStatsPlugin::get_total_statistics() const {
    py::dict stats;

    if (_session_history.empty()) {
        stats["available"] = false;
        return stats;
    }

    int32_t total_iterations = 0;
    int32_t total_matches = 0;
    int32_t total_wallets = 0;
    double total_runtime = 0.0;

    for (const auto& entry : _session_history) {
        total_iterations += entry.iteration_count;
        total_matches += entry.match_count;
        total_wallets += entry.wallet_count;
        total_runtime += entry.runtime_seconds;
    }

    stats["available"] = true;
    stats["session_count"] = static_cast<int32_t>(_session_history.size());
    stats["total_iterations"] = total_iterations;
    stats["total_matches"] = total_matches;
    stats["total_wallets"] = total_wallets;
    stats["total_runtime_seconds"] = total_runtime;
    stats["avg_iterations_per_session"] = static_cast<double>(total_iterations) / _session_history.size();

    return stats;
}
// END_METHOD_GET_TOTAL_STATISTICS


// START_METHOD_ON_START
// START_CONTRACT:
// PURPOSE: Обработчик запуска генератора
// INPUTS:
// - selected_list_path: const std::string& — путь к списку
// OUTPUTS: void
// KEYWORDS: [DOMAIN(8): EventHandler; CONCEPT(6): Startup]
// END_CONTRACT
void FinalStatsPlugin::on_start(const std::string& selected_list_path) {
    _start_time = _get_current_time();
    _is_complete = false;
    _final_metrics = FinalStatistics();
    _final_metrics.list_path = selected_list_path;
    _final_metrics.start_timestamp = _start_time;

    std::stringstream ss;
    ss << "[FinalStatsPlugin][ON_START][StepComplete] Начало сессии: " << selected_list_path;
    log_info(ss.str());
}
// END_METHOD_ON_START


// START_METHOD_ON_FINISH
// START_CONTRACT:
// PURPOSE: Обработчик завершения генерации
// INPUTS:
// - final_metrics: py::dict — финальные метрики
// OUTPUTS: void
// KEYWORDS: [DOMAIN(9): Finalization; CONCEPT(7): MetricsProcessing]
// END_CONTRACT
void FinalStatsPlugin::on_finish(py::dict final_metrics) {
    _end_time = _get_current_time();

    // Фиксация метрик
    _final_metrics = FinalStatistics::from_python(final_metrics);

    // Добавляем вычисляемые показатели
    _final_metrics.end_timestamp = _end_time;
    if (_start_time > 0) {
        _final_metrics.runtime_seconds = _end_time - _start_time;
    }

    // Вычисление производных показателей
    _calculate_runtime();

    _is_complete = true;

    std::stringstream ss;
    ss << "[FinalStatsPlugin][ON_FINISH][Info] Финальная статистика: "
       << _final_metrics.iteration_count << " итераций, "
       << _final_metrics.runtime_seconds << " сек";
    log_info(ss.str());
}
// END_METHOD_ON_FINISH


// START_METHOD_GET_NAME
// START_CONTRACT:
// PURPOSE: Получение имени плагина
// OUTPUTS: std::string — имя
// KEYWORDS: [CONCEPT(5): Getter]
// END_CONTRACT
std::string FinalStatsPlugin::get_name() const {
    return "FinalStatsPlugin";
}
// END_METHOD_GET_NAME


// START_METHOD_GET_PRIORITY
// START_CONTRACT:
// PURPOSE: Получение приоритета плагина
// OUTPUTS: int — приоритет
// KEYWORDS: [CONCEPT(5): Getter]
// END_CONTRACT
int FinalStatsPlugin::get_priority() const {
    return 30;
}
// END_METHOD_GET_PRIORITY


// START_METHOD_HEALTH_CHECK
// START_CONTRACT:
// PURPOSE: Проверка работоспособности
// OUTPUTS: bool — статус
// KEYWORDS: [CONCEPT(7): HealthCheck; DOMAIN(6): Diagnostics]
// END_CONTRACT
bool FinalStatsPlugin::health_check() const {
    return true;
}
// END_METHOD_HEALTH_CHECK


// START_METHOD_BUILD_UI_COMPONENTS
// START_CONTRACT:
// PURPOSE: Построение UI компонентов
// OUTPUTS: py::object — UI компоненты
// KEYWORDS: [DOMAIN(7): UI; CONCEPT(6): Builder]
// END_CONTRACT
py::object FinalStatsPlugin::_build_ui_components() {
    py::dict components;

    // Секция сводки
    components["summary_title"] = py::str(_generate_title_html("Сводка"));
    components["total_iterations"] = py::int_(0);
    components["total_matches"] = py::int_(0);
    components["total_wallets"] = py::int_(0);

    // Секция времени
    components["runtime"] = py::float_(0.0);
    components["runtime_formatted"] = py::str("00:00:00");
    components["avg_iteration_time"] = py::float_(0.0);

    // Секция производительности
    components["iterations_per_second"] = py::float_(0.0);
    components["wallets_per_second"] = py::float_(0.0);

    // Детали
    py::dict empty_stats;
    components["detailed_stats"] = empty_stats;

    // Кнопки экспорта
    components["export_json"] = py::str("Экспорт в JSON");
    components["export_csv"] = py::str("Экспорт в CSV");

    log_debug("[FinalStatsPlugin][BUILD_UI_COMPONENTS][StepComplete] UI компоненты созданы");

    return components;
}
// END_METHOD_BUILD_UI_COMPONENTS


// START_METHOD_ON_ENTER_STAGE
// START_CONTRACT:
// PURPOSE: Обработчик входа на этап
// OUTPUTS: void
// KEYWORDS: [CONCEPT(7): StageHandler]
// END_CONTRACT
void FinalStatsPlugin::_on_enter_stage() {
    log_info("[FinalStatsPlugin][ON_ENTER_STAGE][StepComplete] Вход на этап финальной статистики");
}
// END_METHOD_ON_ENTER_STAGE


// START_METHOD_FORMAT_TIME
// START_CONTRACT:
// PURPOSE: Форматирование времени в читаемый вид
// INPUTS:
// - seconds: double — время в секундах
// OUTPUTS: std::string — отформатированное время (HH:MM:SS)
// KEYWORDS: [CONCEPT(7): Formatting]
// END_CONTRACT
std::string FinalStatsPlugin::_format_time(double seconds) const {
    int hours = static_cast<int>(seconds / 3600);
    int minutes = static_cast<int>((seconds - hours * 3600) / 60);
    int secs = static_cast<int>(seconds - hours * 3600 - minutes * 60);

    std::ostringstream oss;
    oss << std::setfill('0') << std::setw(2) << hours << ":"
        << std::setfill('0') << std::setw(2) << minutes << ":"
        << std::setfill('0') << std::setw(2) << secs;
    return oss.str();
}
// END_METHOD_FORMAT_TIME


// START_METHOD_GENERATE_TITLE_HTML
// START_CONTRACT:
// PURPOSE: Генерация HTML заголовка секции
// INPUTS:
// - title: const std::string& — заголовок
// OUTPUTS: std::string — HTML строка
// KEYWORDS: [CONCEPT(6): HTML; TECH(5): Gradio]
// END_CONTRACT
std::string FinalStatsPlugin::_generate_title_html(const std::string& title) const {
    std::ostringstream oss;
    oss << "<div style=\"padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; margin: 10px 0;\">";
    oss << "<h2 style=\"margin: 0; color: white; text-align: center;\">" << title << "</h2>";
    oss << "</div>";
    return oss.str();
}
// END_METHOD_GENERATE_TITLE_HTML


// START_METHOD_CALCULATE_RUNTIME
// START_CONTRACT:
// PURPOSE: Вычисление времени работы и производных показателей
// OUTPUTS: void
// KEYWORDS: [DOMAIN(8): Calculation; CONCEPT(7): Metrics]
// END_CONTRACT
void FinalStatsPlugin::_calculate_runtime() {
    double runtime = _final_metrics.runtime_seconds;
    int32_t iterations = _final_metrics.iteration_count;
    int32_t wallets = _final_metrics.wallet_count;

    if (runtime > 0) {
        _final_metrics.iterations_per_second = static_cast<double>(iterations) / runtime;
        _final_metrics.wallets_per_second = static_cast<double>(wallets) / runtime;
    } else {
        _final_metrics.iterations_per_second = 0.0;
        _final_metrics.wallets_per_second = 0.0;
    }

    if (iterations > 0 && runtime > 0) {
        _final_metrics.avg_iteration_time_ms = (runtime / static_cast<double>(iterations)) * 1000.0;
    } else {
        _final_metrics.avg_iteration_time_ms = 0.0;
    }
}
// END_METHOD_CALCULATE_RUNTIME


// START_METHOD_GET_CURRENT_TIME
// START_CONTRACT:
// PURPOSE: Получение текущего времени
// OUTPUTS: double — Unix timestamp
// KEYWORDS: [CONCEPT(6): Timestamp]
// END_CONTRACT
double FinalStatsPlugin::_get_current_time() const {
    auto now = std::chrono::system_clock::now();
    auto duration = now.time_since_epoch();
    return std::chrono::duration<double>(duration).count();
}
// END_METHOD_GET_CURRENT_TIME

// END_FINAL_STATS_PLUGIN_IMPLEMENTATION
