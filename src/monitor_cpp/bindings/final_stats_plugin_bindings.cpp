// FILE: src/monitor_cpp/bindings/final_stats_plugin_bindings.cpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Python bindings для модуля final_stats_plugin
// SCOPE: pybind11 bindings, Trampoline класс для Python плагинов
// KEYWORDS: [DOMAIN(9): PythonBindings; TECH(8): pybind11; CONCEPT(7): Trampoline]
// END_MODULE_CONTRACT

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/complex.h>
#include <pybind11/chrono.h>
#include <memory>

#include "plugins/final_stats_plugin.hpp"

namespace py = pybind11;

//==============================================================================
// TRAMPOLINE КЛАСС ДЛЯ FINALSTATSPLUGIN
//==============================================================================

/**
 * @brief Trampoline класс PyFinalStatsPlugin
 * 
 * CONTRACT:
 * PURPOSE: Позволяет наследоваться от FinalStatsPlugin в Python
 * PYBIND11_OVERRIDE используется для обработки вызовов виртуальных методов
 * из C++ в Python код
 */
class PyFinalStatsPlugin : public FinalStatsPlugin {
public:
    using FinalStatsPlugin::FinalStatsPlugin;
    
    // START_METHOD_INITIALIZE_TRAMPOLINE
    // PURPOSE: Инициализация плагина (trampoline для Python)
    // END_METHOD_INITIALIZE_TRAMPOLINE
    void initialize() override {
        PYBIND11_OVERRIDE(
            void,
            FinalStatsPlugin,
            initialize
        );
    }
    
    // START_METHOD_SHUTDOWN_TRAMPOLINE
    // PURPOSE: Завершение работы (trampoline для Python)
    // END_METHOD_SHUTDOWN_TRAMPOLINE
    void shutdown() override {
        PYBIND11_OVERRIDE(
            void,
            FinalStatsPlugin,
            shutdown
        );
    }
    
    // START_METHOD_GET_INFO_TRAMPOLINE
    // PURPOSE: Получение информации о плагине (trampoline для Python)
    // END_METHOD_GET_INFO_TRAMPOLINE
    PluginInfo get_info() const override {
        PYBIND11_OVERRIDE(
            PluginInfo,
            FinalStatsPlugin,
            get_info
        );
    }
    
    // START_METHOD_GET_STATE_TRAMPOLINE
    // PURPOSE: Получение состояния плагина (trampoline для Python)
    // END_METHOD_GET_STATE_TRAMPOLINE
    PluginState get_state() const override {
        PYBIND11_OVERRIDE(
            PluginState,
            FinalStatsPlugin,
            get_state
        );
    }
    
    // START_METHOD_ON_METRICS_UPDATE_TRAMPOLINE
    // PURPOSE: Обработка обновления метрик (trampoline для Python)
    // END_METHOD_ON_METRICS_UPDATE_TRAMPOLINE
    void on_metrics_update(const PluginMetrics& metrics) override {
        PYBIND11_OVERRIDE(
            void,
            FinalStatsPlugin,
            on_metrics_update,
            metrics
        );
    }
    
    // START_METHOD_ON_START_TRAMPOLINE
    // PURPOSE: Обработчик запуска (trampoline для Python)
    // END_METHOD_ON_START_TRAMPOLINE
    void on_start(const std::string& selected_list_path) override {
        PYBIND11_OVERRIDE(
            void,
            FinalStatsPlugin,
            on_start,
            selected_list_path
        );
    }
    
    // START_METHOD_ON_FINISH_TRAMPOLINE
    // PURPOSE: Обработчик завершения (trampoline для Python)
    // END_METHOD_ON_FINISH_TRAMPOLINE
    void on_finish(const PluginMetrics& final_metrics) override {
        PYBIND11_OVERRIDE(
            void,
            FinalStatsPlugin,
            on_finish,
            final_metrics
        );
    }
    
    // START_METHOD_ON_RESET_TRAMPOLINE
    // PURPOSE: Обработчик сброса (trampoline для Python)
    // END_METHOD_ON_RESET_TRAMPOLINE
    void on_reset() override {
        PYBIND11_OVERRIDE(
            void,
            FinalStatsPlugin,
            on_reset
        );
    }
};

//==============================================================================
// ОПРЕДЕЛЕНИЕ PYTHON МОДУЛЯ
//==============================================================================

PYBIND11_MODULE(final_stats_plugin, m) {
    m.doc() = "C++ Final Stats Plugin for Bitcoin Wallet Generator Monitoring";
    
    //==========================================================================
    // КОНСТАНТЫ
    //==========================================================================
    
    m.attr("PLUGIN_NAME") = FINAL_STATS_PLUGIN_NAME;
    m.attr("PLUGIN_VERSION") = FINAL_STATS_PLUGIN_VERSION;
    m.attr("PLUGIN_PRIORITY") = FINAL_STATS_PLUGIN_PRIORITY;
    
    //==========================================================================
    // ENUMS
    //==========================================================================
    
    // START_BINDING_EXPORT_FORMAT
    py::enum_<ExportFormat>(m, "ExportFormat")
        .value("JSON", ExportFormat::JSON, "JSON формат")
        .value("CSV", ExportFormat::CSV, "CSV формат (Excel совместимый)")
        .value("TXT", ExportFormat::TXT, "Текстовый читаемый формат")
        .value("MARKDOWN", ExportFormat::MARKDOWN, "Markdown таблица")
        .export_values();
    // END_BINDING_EXPORT_FORMAT
    
    // START_BINDING_PLUGIN_STATE
    py::enum_<PluginState>(m, "PluginState")
        .value("UNINITIALIZED", PluginState::UNINITIALIZED)
        .value("INITIALIZING", PluginState::INITIALIZING)
        .value("ACTIVE", PluginState::ACTIVE)
        .value("PAUSED", PluginState::PAUSED)
        .value("STOPPED", PluginState::STOPPED)
        .value("ERROR", PluginState::ERROR)
        .export_values();
    // END_BINDING_PLUGIN_STATE
    
    //==========================================================================
    // СТРУКТУРЫ ДАННЫХ
    //==========================================================================
    
    // START_BINDING_FINAL_STATISTICS
    py::class_<FinalStatistics>(m, "FinalStatistics")
        .def(py::init<>())
        .def_readwrite("iteration_count", &FinalStatistics::iteration_count,
            "Общее количество итераций")
        .def_readwrite("match_count", &FinalStatistics::match_count,
            "Количество найденных совпадений")
        .def_readwrite("wallet_count", &FinalStatistics::wallet_count,
            "Количество сгенерированных кошельков")
        .def_readwrite("runtime_seconds", &FinalStatistics::runtime_seconds,
            "Время работы в секундах")
        .def_readwrite("start_timestamp", &FinalStatistics::start_timestamp,
            "Timestamp начала")
        .def_readwrite("end_timestamp", &FinalStatistics::end_timestamp,
            "Timestamp завершения")
        .def_readwrite("iterations_per_second", &FinalStatistics::iterations_per_second,
            "Скорость итераций")
        .def_readwrite("wallets_per_second", &FinalStatistics::wallets_per_second,
            "Скорость генерации кошельков")
        .def_readwrite("avg_iteration_time_ms", &FinalStatistics::avg_iteration_time_ms,
            "Среднее время итерации в мс")
        .def_readwrite("list_path", &FinalStatistics::list_path,
            "Путь к используемому списку")
        .def_readwrite("custom_metrics", &FinalStatistics::custom_metrics,
            "Дополнительные метрики")
        .def("is_available", &FinalStatistics::is_available,
            "Проверить доступность данных")
        .def("reset", &FinalStatistics::reset,
            "Сбросить данные")
        .def("to_plugin_metrics", &FinalStatistics::to_plugin_metrics,
            "Преобразовать в PluginMetrics");
    // END_BINDING_FINAL_STATISTICS
    
    // START_BINDING_SESSION_HISTORY
    py::class_<SessionHistory>(m, "SessionHistory")
        .def(py::init<>())
        .def(py::init<uint32_t, const FinalStatistics&>(),
             py::arg("session_id"), py::arg("stats"))
        .def_readwrite("session_id", &SessionHistory::session_id,
            "ID сессии")
        .def_readwrite("stats", &SessionHistory::stats,
            "Статистика сессии")
        .def_readwrite("timestamp", &SessionHistory::timestamp,
            "Время сессии");
    // END_BINDING_SESSION_HISTORY
    
    //==========================================================================
    // КЛАСС FINAL_STATS PLUGIN
    //==========================================================================
    
    // START_BINDING_FINAL_STATS_PLUGIN
    py::class_<FinalStatsPlugin, PyFinalStatsPlugin>(m, "FinalStatsPlugin")
        .def(py::init<>())
        
        // Constants
        .def_readonly_static("PLUGIN_NAME", &FinalStatsPlugin::PLUGIN_NAME)
        .def_readonly_static("PLUGIN_VERSION", &FinalStatsPlugin::PLUGIN_VERSION)
        .def_readonly_static("PLUGIN_PRIORITY", &FinalStatsPlugin::PLUGIN_PRIORITY)
        
        // Абстрактные методы IPlugin
        .def("initialize", &FinalStatsPlugin::initialize)
        .def("shutdown", &FinalStatsPlugin::shutdown)
        .def("get_info", &FinalStatsPlugin::get_info)
        .def("get_state", &FinalStatsPlugin::get_state)
        
        // Методы обратного вызова
        .def("on_metrics_update", &FinalStatsPlugin::on_metrics_update)
        .def("on_start", &FinalStatsPlugin::on_start)
        .def("on_finish", &FinalStatsPlugin::on_finish)
        .def("on_reset", &FinalStatsPlugin::on_reset)
        
        // Специфичные методы FinalStats
        .def("get_final_metrics", &FinalStatsPlugin::get_final_metrics)
        .def("get_summary", &FinalStatsPlugin::get_summary)
        .def("get_session_history", &FinalStatsPlugin::get_session_history)
        .def("get_performance_analysis", &FinalStatsPlugin::get_performance_analysis)
        .def("is_complete", &FinalStatsPlugin::is_complete)
        
        // Экспорт
        .def("export_to_json", &FinalStatsPlugin::export_to_json)
        .def("export_to_csv", &FinalStatsPlugin::export_to_csv)
        .def("export_to_txt", &FinalStatsPlugin::export_to_txt)
        .def("export_to_file", &FinalStatsPlugin::export_to_file)
        
        // Управление состоянием
        .def("reset_stats", &FinalStatsPlugin::reset_stats)
        .def("add_session", &FinalStatsPlugin::add_session)
        .def("get_total_statistics", &FinalStatsPlugin::get_total_statistics);
    // END_BINDING_FINAL_STATS_PLUGIN
}
