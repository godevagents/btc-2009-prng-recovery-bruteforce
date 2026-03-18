// FILE: src/monitor/_cpp/bindings/live_stats_plugin_bindings.cpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Python bindings для плагина live-мониторинга с использованием pybind11.
// SCOPE: Python bindings, trampoline класс, экспорт в Python
// INPUT: Заголовочный файл live_stats_plugin.hpp
// OUTPUT: Скомпилированный Python модуль
// KEYWORDS: [DOMAIN(9): Pybind11; DOMAIN(8): PythonBindings; TECH(7): LiveMonitoring]
// END_MODULE_CONTRACT

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/chrono.h>
#include "live_stats_plugin.hpp"

namespace py = pybind11;

// START_BINDINGS_METRIC_SNAPSHOT
// START_CONTRACT:
// PURPOSE: Python bindings для структуры MetricSnapshot
// KEYWORDS: [PATTERN(7): Pybind11; DOMAIN(8): PythonBindings]
// END_CONTRACT

void bind_metric_snapshot(py::module& m) {
    py::class_<MetricSnapshot>(m, "MetricSnapshot")
        .def(py::init<>())
        .def(py::init<double, double, double, double>(),
             py::arg("iteration_delta"),
             py::arg("wallet_delta"),
             py::arg("match_delta"),
             py::arg("timestamp"))
        .def_readwrite("iteration_delta", &MetricSnapshot::iteration_delta)
        .def_readwrite("wallet_delta", &MetricSnapshot::wallet_delta)
        .def_readwrite("match_delta", &MetricSnapshot::match_delta)
        .def_readwrite("timestamp", &MetricSnapshot::timestamp)
        .def("__repr__", [](const MetricSnapshot& self) {
            return "<MetricSnapshot(iter=" + std::to_string(self.iteration_delta) + 
                   ", wallet=" + std::to_string(self.wallet_delta) + 
                   ", match=" + std::to_string(self.match_delta) + ")>";
        });
}
// END_BINDINGS_METRIC_SNAPSHOT


// START_BINDINGS_STATISTICS
// START_CONTRACT:
// PURPOSE: Python bindings для структуры Statistics
// KEYWORDS: [PATTERN(7): Pybind11; DOMAIN(8): PythonBindings]
// END_CONTRACT

void bind_statistics(py::module& m) {
    py::class_<Statistics>(m, "Statistics")
        .def(py::init<>())
        .def(py::init<double, double, double, double>(),
             py::arg("min"),
             py::arg("max"),
             py::arg("mean"),
             py::arg("std"))
        .def_readwrite("min", &Statistics::min)
        .def_readwrite("max", &Statistics::max)
        .def_readwrite("mean", &Statistics::mean)
        .def_readwrite("std", &Statistics::std)
        .def("__repr__", [](const Statistics& self) {
            return "<Statistics(min=" + std::to_string(self.min) + 
                   ", max=" + std::to_string(self.max) + 
                   ", mean=" + std::to_string(self.mean) + 
                   ", std=" + std::to_string(self.std) + ")>";
        });
}
// END_BINDINGS_STATISTICS


// START_BINDINGS_CURRENT_STATS
// START_CONTRACT:
// PURPOSE: Python bindings для структуры CurrentStats
// KEYWORDS: [PATTERN(7): Pybind11; DOMAIN(8): PythonBindings]
// END_CONTRACT

void bind_current_stats(py::module& m) {
    py::class_<CurrentStats>(m, "CurrentStats")
        .def(py::init<>())
        .def_readwrite("iterations", &CurrentStats::iterations)
        .def_readwrite("wallets", &CurrentStats::wallets)
        .def_readwrite("matches", &CurrentStats::matches)
        .def_readwrite("elapsed_time", &CurrentStats::elapsed_time)
        .def_readwrite("iter_per_sec", &CurrentStats::iter_per_sec)
        .def_readwrite("wallets_per_sec", &CurrentStats::wallets_per_sec)
        .def_readwrite("is_monitoring", &CurrentStats::is_monitoring)
        .def("__repr__", [](const CurrentStats& self) {
            return "<CurrentStats(iterations=" + std::to_string(self.iterations) + 
                   ", wallets=" + std::to_string(self.wallets) + 
                   ", monitoring=" + (self.is_monitoring ? "True" : "False") + ")>";
        });
}
// END_BINDINGS_CURRENT_STATS


// START_BINDINGS_LIVE_STATS_PLUGIN
// START_CONTRACT:
// PURPOSE: Python bindings для плагина live-мониторинга с trampoline
// KEYWORDS: [PATTERN(9): TrampolineClass; DOMAIN(9): Pybind11; TECH(7): PythonBindings]
// END_CONTRACT

void bind_live_stats_plugin(py::module& m) {
    // Основной класс (без trampoline, просто привязываем напрямую)
    py::class_<LiveStatsPlugin>(m, "LiveStatsPlugin")
        .def(py::init<>())
        .def_static("get_version", []() { return LiveStatsPlugin::VERSION; })
        .def_static("get_author", []() { return LiveStatsPlugin::AUTHOR; })
        .def_static("get_description", []() { return LiveStatsPlugin::DESCRIPTION; })
        .def_readonly_static("VERSION", &LiveStatsPlugin::VERSION)
        .def_readonly_static("AUTHOR", &LiveStatsPlugin::AUTHOR)
        .def_readonly_static("DESCRIPTION", &LiveStatsPlugin::DESCRIPTION)
        .def_readonly_static("MAX_HISTORY_POINTS", &wallet::monitor::live_stats::kMaxHistoryPoints)
        .def_readonly_static("REFRESH_INTERVAL", &wallet::monitor::live_stats::kRefreshInterval)
        .def("initialize", &LiveStatsPlugin::initialize,
             py::arg("app"))
        .def("on_metric_update", &LiveStatsPlugin::on_metric_update,
             py::arg("metrics"))
        .def("on_shutdown", &LiveStatsPlugin::on_shutdown)
        .def("get_ui_components", &LiveStatsPlugin::get_ui_components)
        .def("reset_stats", &LiveStatsPlugin::reset_stats)
        .def("get_current_stats", &LiveStatsPlugin::get_current_stats_py)
        .def("get_iteration_history", &LiveStatsPlugin::get_iteration_history)
        .def("get_wallet_history", &LiveStatsPlugin::get_wallet_history)
        .def("get_match_history", &LiveStatsPlugin::get_match_history)
        .def("get_plot_data", &LiveStatsPlugin::get_plot_data,
             py::arg("history"))
        .def("get_empty_plot_data", &LiveStatsPlugin::get_empty_plot_data)
        .def("calculate_statistics", &LiveStatsPlugin::calculate_statistics)
        .def("get_performance_report", &LiveStatsPlugin::get_performance_report)
        .def("get_entropy_summary", &LiveStatsPlugin::get_entropy_summary)
        .def("is_monitoring", &LiveStatsPlugin::is_monitoring)
        .def("get_status_html", &LiveStatsPlugin::get_status_html,
             py::arg("iteration_count") = 0)
        .def("on_enter_stage", &LiveStatsPlugin::on_enter_stage)
        .def("__repr__", [](const LiveStatsPlugin& self) {
            return "<LiveStatsPlugin(version='" + LiveStatsPlugin::VERSION + 
                   "', monitoring=" + (self.is_monitoring() ? "True" : "False") + ")>";
        });
}
// END_BINDINGS_LIVE_STATS_PLUGIN


// START_MODULE_DEFINITION
// START_CONTRACT:
// PURPOSE: Определение Python модуля и точка входа для pybind11
// KEYWORDS: [PATTERN(7): Module; DOMAIN(8): Pybind11]
// END_CONTRACT

PYBIND11_MODULE(live_stats_plugin_cpp, m) {
    m.doc() = "C++ плагин live-мониторинга метрик генерации кошельков";
    
    // Версия модуля
    m.attr("__version__") = "1.0.0";
    
    // Привязки структур данных
    bind_metric_snapshot(m);
    bind_statistics(m);
    bind_current_stats(m);
    
    // Привязки класса плагина
    bind_live_stats_plugin(m);
}
// END_MODULE_DEFINITION
