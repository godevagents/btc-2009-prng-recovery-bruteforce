// FILE: src/monitor_cpp/bindings/live_stats_plugin_bindings.cpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Python bindings для модуля live_stats_plugin с поддержкой создания плагинов на Python
// SCOPE: pybind11 bindings, Trampoline класс для Python плагинов
// KEYWORDS: [DOMAIN(9): PythonBindings; TECH(8): pybind11; CONCEPT(7): Trampoline]
// END_MODULE_CONTRACT

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/complex.h>
#include <pybind11/chrono.h>
#include <memory>

#include "plugins/live_stats_plugin.hpp"

namespace py = pybind11;

//==============================================================================
// TRAMPOLINE КЛАСС ДЛЯ LIVESTATSPLUGIN
//==============================================================================

/**
 * @brief Trampoline класс PyLiveStatsPlugin
 * 
 * CONTRACT:
 * PURPOSE: Позволяет наследоваться от LiveStatsPlugin в Python
 * PYBIND11_OVERRIDE используется для обработки вызовов виртуальных методов
 * из C++ в Python код
 */
class PyLiveStatsPlugin : public LiveStatsPlugin {
public:
    using LiveStatsPlugin::LiveStatsPlugin;
    
    // START_METHOD_INITIALIZE_TRAMPOLINE
    // PURPOSE: Инициализация плагина (trampoline для Python)
    // END_METHOD_INITIALIZE_TRAMPOLINE
    void initialize() override {
        PYBIND11_OVERRIDE(
            void,
            LiveStatsPlugin,
            initialize
        );
    }
    
    // START_METHOD_SHUTDOWN_TRAMPOLINE
    // PURPOSE: Завершение работы (trampoline для Python)
    // END_METHOD_SHUTDOWN_TRAMPOLINE
    void shutdown() override {
        PYBIND11_OVERRIDE(
            void,
            LiveStatsPlugin,
            shutdown
        );
    }
    
    // START_METHOD_GET_INFO_TRAMPOLINE
    // PURPOSE: Получение информации о плагине (trampoline для Python)
    // END_METHOD_GET_INFO_TRAMPOLINE
    PluginInfo get_info() const override {
        PYBIND11_OVERRIDE(
            PluginInfo,
            LiveStatsPlugin,
            get_info
        );
    }
    
    // START_METHOD_GET_STATE_TRAMPOLINE
    // PURPOSE: Получение состояния плагина (trampoline для Python)
    // END_METHOD_GET_STATE_TRAMPOLINE
    PluginState get_state() const override {
        PYBIND11_OVERRIDE(
            PluginState,
            LiveStatsPlugin,
            get_state
        );
    }
    
    // START_METHOD_ON_METRICS_UPDATE_TRAMPOLINE
    // PURPOSE: Обработка обновления метрик (trampoline для Python)
    // END_METHOD_ON_METRICS_UPDATE_TRAMPOLINE
    void on_metrics_update(const PluginMetrics& metrics) override {
        PYBIND11_OVERRIDE(
            void,
            LiveStatsPlugin,
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
            LiveStatsPlugin,
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
            LiveStatsPlugin,
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
            LiveStatsPlugin,
            on_reset
        );
    }
};

//==============================================================================
// ОПРЕДЕЛЕНИЕ PYTHON МОДУЛЯ
//==============================================================================

PYBIND11_MODULE(live_stats_plugin, m) {
    m.doc() = "C++ Live Stats Plugin for Bitcoin Wallet Generator Monitoring";
    
    //==========================================================================
    // КОНСТАНТЫ
    //==========================================================================
    
    m.attr("MAX_HISTORY_POINTS") = MAX_HISTORY_POINTS;
    m.attr("REFRESH_INTERVAL") = REFRESH_INTERVAL;
    
    //==========================================================================
    // СТРУКТУРЫ ДАННЫХ
    //==========================================================================
    
    // START_BINDING_METRIC_SNAPSHOT
    py::class_<MetricSnapshot>(m, "MetricSnapshot")
        .def(py::init<>())
        .def(py::init<double, double, double, double>(),
             py::arg("iteration_delta"), py::arg("wallet_delta"),
             py::arg("match_delta"), py::arg("entropy_bits"))
        .def_readwrite("iteration_delta", &MetricSnapshot::iteration_delta)
        .def_readwrite("wallet_delta", &MetricSnapshot::wallet_delta)
        .def_readwrite("match_delta", &MetricSnapshot::match_delta)
        .def_readwrite("entropy_bits", &MetricSnapshot::entropy_bits);
    // END_BINDING_METRIC_SNAPSHOT
    
    // START_BINDING_STATISTICS
    py::class_<Statistics>(m, "Statistics")
        .def(py::init<>())
        .def_readwrite("iterations_min", &Statistics::iterations_min)
        .def_readwrite("iterations_max", &Statistics::iterations_max)
        .def_readwrite("iterations_mean", &Statistics::iterations_mean)
        .def_readwrite("iterations_std", &Statistics::iterations_std)
        .def_readwrite("wallets_min", &Statistics::wallets_min)
        .def_readwrite("wallets_max", &Statistics::wallets_max)
        .def_readwrite("wallets_mean", &Statistics::wallets_mean)
        .def_readwrite("wallets_std", &Statistics::wallets_std)
        .def_readwrite("entropy_min", &Statistics::entropy_min)
        .def_readwrite("entropy_max", &Statistics::entropy_max)
        .def_readwrite("entropy_mean", &Statistics::entropy_mean)
        .def_readwrite("iterations_available", &Statistics::iterations_available)
        .def_readwrite("wallets_available", &Statistics::wallets_available)
        .def_readwrite("entropy_available", &Statistics::entropy_available);
    // END_BINDING_STATISTICS
    
    // START_BINDING_CURRENT_STATS
    py::class_<CurrentStats>(m, "CurrentStats")
        .def(py::init<>())
        .def_readwrite("iterations", &CurrentStats::iterations)
        .def_readwrite("wallets", &CurrentStats::wallets)
        .def_readwrite("matches", &CurrentStats::matches)
        .def_readwrite("elapsed_time", &CurrentStats::elapsed_time)
        .def_readwrite("iter_per_sec", &CurrentStats::iter_per_sec)
        .def_readwrite("wallets_per_sec", &CurrentStats::wallets_per_sec)
        .def_readwrite("is_monitoring", &CurrentStats::is_monitoring);
    // END_BINDING_CURRENT_STATS
    
    //==========================================================================
    // ENUMS
    //==========================================================================
    
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
    // КЛАСС LIVE_STATS PLUGIN
    //==========================================================================
    
    // START_BINDING_LIVE_STATS_PLUGIN
    py::class_<LiveStatsPlugin, PyLiveStatsPlugin>(m, "LiveStatsPlugin")
        .def(py::init<>())
        
        // Абстрактные методы IPlugin
        .def("initialize", &LiveStatsPlugin::initialize)
        .def("shutdown", &LiveStatsPlugin::shutdown)
        .def("get_info", &LiveStatsPlugin::get_info)
        .def("get_state", &LiveStatsPlugin::get_state)
        
        // Методы обратного вызова
        .def("on_metrics_update", &LiveStatsPlugin::on_metrics_update)
        .def("on_start", &LiveStatsPlugin::on_start)
        .def("on_finish", &LiveStatsPlugin::on_finish)
        .def("on_reset", &LiveStatsPlugin::on_reset)
        
        // Специфичные методы LiveStats
        .def("get_current_stats", &LiveStatsPlugin::getCurrentStats)
        .def("calculate_statistics", &LiveStatsPlugin::calculateStatistics)
        .def("reset_stats", &LiveStatsPlugin::resetStats)
        .def("get_iteration_plot_data", &LiveStatsPlugin::getIterationPlotData)
        .def("get_wallet_plot_data", &LiveStatsPlugin::getWalletPlotData)
        .def("get_entropy_summary", &LiveStatsPlugin::getEntropySummary)
        .def("is_monitoring", &LiveStatsPlugin::isMonitoring)
        .def("get_performance_report", &LiveStatsPlugin::getPerformanceReport);
    // END_BINDING_LIVE_STATS_PLUGIN
}
