// FILE: src/monitor/_cpp/bindings/final_stats_plugin_bindings.cpp
// VERSION: 2.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Python bindings для плагина финальной статистики с использованием pybind11.
// Обеспечивает возможность наследования от C++ класса в Python через trampoline.
// SCOPE: Python bindings, trampoline класс, экспорт в Python
// INPUT: Заголовочный файл final_stats_plugin.hpp
// OUTPUT: Скомпилированный Python модуль
// KEYWORDS: [DOMAIN(9): Pybind11; DOMAIN(8): PythonBindings; TECH(7): Trampoline]
// END_MODULE_CONTRACT

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <pybind11/chrono.h>
#include "final_stats_plugin.hpp"
#include "plugin_base.hpp"

namespace py = pybind11;

// START_BINDINGS_EXPORT_FORMAT
void bind_export_format(py::module& m) {
    py::enum_<ExportFormat>(m, "ExportFormat")
        .value("JSON", ExportFormat::JSON)
        .value("CSV", ExportFormat::CSV)
        .value("TXT", ExportFormat::TXT)
        .value("MARKDOWN", ExportFormat::MARKDOWN)
        .export_values();
}
// END_BINDINGS_EXPORT_FORMAT


// START_BINDINGS_FINAL_STATISTICS
void bind_final_statistics(py::module& m) {
    py::class_<FinalStatistics>(m, "FinalStatistics")
        .def(py::init<>())
        .def(py::init<int32_t, int32_t, int32_t, double>(),
            py::arg("iterations"),
            py::arg("matches"),
            py::arg("wallets"),
            py::arg("runtime")
        )
        .def(py::init(&FinalStatistics::from_python))
        .def_readwrite("iteration_count", &FinalStatistics::iteration_count)
        .def_readwrite("match_count", &FinalStatistics::match_count)
        .def_readwrite("wallet_count", &FinalStatistics::wallet_count)
        .def_readwrite("runtime_seconds", &FinalStatistics::runtime_seconds)
        .def_readwrite("iterations_per_second", &FinalStatistics::iterations_per_second)
        .def_readwrite("wallets_per_second", &FinalStatistics::wallets_per_second)
        .def_readwrite("avg_iteration_time_ms", &FinalStatistics::avg_iteration_time_ms)
        .def_readwrite("start_timestamp", &FinalStatistics::start_timestamp)
        .def_readwrite("end_timestamp", &FinalStatistics::end_timestamp)
        .def_readwrite("list_path", &FinalStatistics::list_path)
        .def_readwrite("metadata", &FinalStatistics::metadata)
        .def("to_python", &FinalStatistics::to_python)
        .def("is_valid", &FinalStatistics::is_valid)
        .def("get_formatted_runtime", &FinalStatistics::get_formatted_runtime)
        .def("__repr__", [](const FinalStatistics& self) {
            return "<FinalStatistics(iterations=" + std::to_string(self.iteration_count) +
                   ", matches=" + std::to_string(self.match_count) +
                   ", wallets=" + std::to_string(self.wallet_count) + ")>";
        });
}
// END_BINDINGS_FINAL_STATISTICS


// START_BINDINGS_SESSION_ENTRY
void bind_session_entry(py::module& m) {
    py::class_<SessionEntry>(m, "SessionEntry")
        .def(py::init<>())
        .def(py::init<int32_t, int32_t, int32_t, int32_t, double, double>(),
            py::arg("session_id"),
            py::arg("iterations"),
            py::arg("matches"),
            py::arg("wallets"),
            py::arg("runtime"),
            py::arg("start_time")
        )
        .def(py::init(&SessionEntry::from_python))
        .def_readwrite("session_id", &SessionEntry::session_id)
        .def_readwrite("iteration_count", &SessionEntry::iteration_count)
        .def_readwrite("match_count", &SessionEntry::match_count)
        .def_readwrite("wallet_count", &SessionEntry::wallet_count)
        .def_readwrite("runtime_seconds", &SessionEntry::runtime_seconds)
        .def_readwrite("start_timestamp", &SessionEntry::start_timestamp)
        .def_readwrite("end_timestamp", &SessionEntry::end_timestamp)
        .def_readwrite("metrics", &SessionEntry::metrics)
        .def("to_python", &SessionEntry::to_python)
        .def("__repr__", [](const SessionEntry& self) {
            return "<SessionEntry(id=" + std::to_string(self.session_id) +
                   ", iterations=" + std::to_string(self.iteration_count) + ")>";
        });
}
// END_BINDINGS_SESSION_ENTRY


// START_BINDINGS_PERFORMANCE_METRICS
void bind_performance_metrics(py::module& m) {
    py::class_<PerformanceMetrics>(m, "PerformanceMetrics")
        .def(py::init<>())
        .def(py::init<int32_t, double, double, double, double>(),
            py::arg("iterations"),
            py::arg("runtime"),
            py::arg("iter_per_sec"),
            py::arg("estimated_hours"),
            py::arg("probability")
        )
        .def_readwrite("iterations", &PerformanceMetrics::iterations)
        .def_readwrite("runtime_seconds", &PerformanceMetrics::runtime_seconds)
        .def_readwrite("iter_per_sec", &PerformanceMetrics::iter_per_sec)
        .def_readwrite("estimated_hours_to_match", &PerformanceMetrics::estimated_hours_to_match)
        .def_readwrite("probability_per_iteration", &PerformanceMetrics::probability_per_iteration)
        .def_readwrite("available", &PerformanceMetrics::available)
        .def("to_python", &PerformanceMetrics::to_python);
}
// END_BINDINGS_PERFORMANCE_METRICS


// START_BINDINGS_FINAL_STATS_PLUGIN
void bind_final_stats_plugin(py::module& m) {
    // Основной класс (без trampoline)
    py::class_<FinalStatsPlugin, BaseMonitorPlugin>(m, "FinalStatsPlugin")
        .def(py::init<>())
        .def_static("get_version", []() { return FinalStatsPlugin::VERSION; })
        .def_static("get_author", []() { return FinalStatsPlugin::AUTHOR; })
        .def_static("get_description", []() { return FinalStatsPlugin::DESCRIPTION; })
        .def_readonly_static("VERSION", &FinalStatsPlugin::VERSION)
        .def_readonly_static("AUTHOR", &FinalStatsPlugin::AUTHOR)
        .def_readonly_static("DESCRIPTION", &FinalStatsPlugin::DESCRIPTION)
        .def_readonly_static("DEFAULT_PRIORITY", &FinalStatsPlugin::DEFAULT_PRIORITY)
        .def("initialize", &FinalStatsPlugin::initialize, py::arg("app"))
        .def("on_metric_update", &FinalStatsPlugin::on_metric_update, py::arg("metrics"))
        .def("on_shutdown", &FinalStatsPlugin::on_shutdown)
        .def("get_ui_components", &FinalStatsPlugin::get_ui_components)
        .def("update_ui", &FinalStatsPlugin::update_ui)
        .def("get_final_metrics", &FinalStatsPlugin::get_final_metrics)
        .def("get_summary", &FinalStatsPlugin::get_summary)
        .def("export_json", &FinalStatsPlugin::export_json, py::arg("file_path"))
        .def("export_csv", &FinalStatsPlugin::export_csv, py::arg("file_path"))
        .def("export_txt", &FinalStatsPlugin::export_txt, py::arg("file_path"))
        .def("get_performance_analysis", &FinalStatsPlugin::get_performance_analysis)
        .def("is_complete", &FinalStatsPlugin::is_complete)
        .def("reset", &FinalStatsPlugin::reset)
        .def("add_session", &FinalStatsPlugin::add_session, py::arg("metrics"))
        .def("get_session_history", &FinalStatsPlugin::get_session_history)
        .def("get_total_statistics", &FinalStatsPlugin::get_total_statistics)
        .def("on_start", &FinalStatsPlugin::on_start, py::arg("selected_list_path"))
        .def("on_finish", &FinalStatsPlugin::on_finish, py::arg("final_metrics"))
        .def("health_check", &FinalStatsPlugin::health_check)
        .def("__repr__", [](const FinalStatsPlugin& self) {
            return "<FinalStatsPlugin(priority=" + std::to_string(self.get_priority()) +
                   ", complete=" + (self.is_complete() ? "True" : "False") + ")>";
        });
}
// END_BINDINGS_FINAL_STATS_PLUGIN


// START_MODULE_DEFINITION
PYBIND11_MODULE(final_stats_plugin_cpp, m) {
    m.doc() = "C++ плагин финальной статистики с поддержкой наследования из Python";
    m.attr("__version__") = "2.0.0";

    bind_export_format(m);
    bind_final_statistics(m);
    bind_session_entry(m);
    bind_performance_metrics(m);
    bind_final_stats_plugin(m);
}
// END_MODULE_DEFINITION
