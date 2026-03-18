// FILE: src/monitor/_cpp/bindings/match_notifier_plugin_bindings.cpp
// VERSION: 2.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Python bindings для плагина уведомлений о совпадениях с использованием pybind11.
// Обеспечивает возможность наследования от C++ класса в Python через trampoline.
// SCOPE: Python bindings, trampoline класс, экспорт в Python
// INPUT: Заголовочный файл match_notifier_plugin.hpp
// OUTPUT: Скомпилированный Python модуль
// KEYWORDS: [DOMAIN(9): Pybind11; DOMAIN(8): PythonBindings; TECH(7): Trampoline]
// END_MODULE_CONTRACT

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <pybind11/chrono.h>
#include "match_notifier_plugin.hpp"
#include "plugin_base.hpp"

namespace py = pybind11;

// START_BINDINGS_MATCH_SEVERITY
void bind_match_severity(py::module& m) {
    py::enum_<MatchSeverity>(m, "MatchSeverity")
        .value("INFO", MatchSeverity::INFO)
        .value("SUCCESS", MatchSeverity::SUCCESS)
        .value("WARNING", MatchSeverity::WARNING)
        .value("CRITICAL", MatchSeverity::CRITICAL)
        .export_values();
}
// END_BINDINGS_MATCH_SEVERITY


// START_BINDINGS_NOTIFICATION_TYPE
void bind_notification_type(py::module& m) {
    py::enum_<NotificationType>(m, "NotificationType")
        .value("DESKTOP", NotificationType::DESKTOP)
        .value("SOUND", NotificationType::SOUND)
        .value("LOG", NotificationType::LOG)
        .value("UI", NotificationType::UI)
        .export_values();
}
// END_BINDINGS_NOTIFICATION_TYPE


// START_BINDINGS_MATCH_ENTRY
void bind_match_entry(py::module& m) {
    py::class_<MatchEntry>(m, "MatchEntry")
        .def(py::init<>())
        .def(py::init<
            const std::string&,
            const std::string&,
            double,
            int32_t,
            MatchSeverity
        >(),
            py::arg("address"),
            py::arg("private_key"),
            py::arg("balance"),
            py::arg("iteration"),
            py::arg("severity") = MatchSeverity::INFO
        )
        .def(py::init(&MatchEntry::from_python))
        .def_readwrite("address", &MatchEntry::address)
        .def_readwrite("private_key", &MatchEntry::private_key)
        .def_readwrite("balance", &MatchEntry::balance)
        .def_readwrite("iteration", &MatchEntry::iteration)
        .def_readwrite("timestamp", &MatchEntry::timestamp)
        .def_readwrite("severity", &MatchEntry::severity)
        .def_readwrite("message", &MatchEntry::message)
        .def("to_python", &MatchEntry::to_python)
        .def("get_severity_string", &MatchEntry::get_severity_string)
        .def("get_formatted_time", &MatchEntry::get_formatted_time)
        .def("__repr__", [](const MatchEntry& self) {
            return "<MatchEntry(address='" + self.address +
                   "', balance=" + std::to_string(self.balance) +
                   ", iteration=" + std::to_string(self.iteration) + ")>";
        });
}
// END_BINDINGS_MATCH_ENTRY


// START_BINDINGS_NOTIFICATION_SETTINGS
void bind_notification_settings(py::module& m) {
    py::class_<NotificationSettings>(m, "NotificationSettings")
        .def(py::init<>())
        .def(py::init<
            bool,
            bool,
            bool,
            bool,
            double
        >(),
            py::arg("desktop"),
            py::arg("sound"),
            py::arg("log"),
            py::arg("ui"),
            py::arg("cooldown") = 5.0
        )
        .def(py::init(&NotificationSettings::from_python))
        .def_readwrite("enable_desktop", &NotificationSettings::enable_desktop)
        .def_readwrite("enable_sound", &NotificationSettings::enable_sound)
        .def_readwrite("enable_log", &NotificationSettings::enable_log)
        .def_readwrite("enable_ui", &NotificationSettings::enable_ui)
        .def_readwrite("cooldown", &NotificationSettings::cooldown)
        .def("to_python", &NotificationSettings::to_python)
        .def("is_any_enabled", &NotificationSettings::is_any_enabled);
}
// END_BINDINGS_NOTIFICATION_SETTINGS


// START_BINDINGS_MATCH_NOTIFIER_PLUGIN
void bind_match_notifier_plugin(py::module& m) {
    // Основной класс (без trampoline)
    py::class_<MatchNotifierPlugin, BaseMonitorPlugin>(m, "MatchNotifierPlugin")
        .def(py::init<>())
        .def_static("get_version", []() { return MatchNotifierPlugin::VERSION; })
        .def_static("get_author", []() { return MatchNotifierPlugin::AUTHOR; })
        .def_static("get_description", []() { return MatchNotifierPlugin::DESCRIPTION; })
        .def_readonly_static("VERSION", &MatchNotifierPlugin::VERSION)
        .def_readonly_static("AUTHOR", &MatchNotifierPlugin::AUTHOR)
        .def_readonly_static("DESCRIPTION", &MatchNotifierPlugin::DESCRIPTION)
        .def_readonly_static("MAX_MATCH_HISTORY", &MatchNotifierPlugin::MAX_MATCH_HISTORY)
        .def_readonly_static("NOTIFICATION_COOLDOWN", &MatchNotifierPlugin::NOTIFICATION_COOLDOWN)
        .def("initialize", &MatchNotifierPlugin::initialize, py::arg("app"))
        .def("on_metric_update", &MatchNotifierPlugin::on_metric_update, py::arg("metrics"))
        .def("on_shutdown", &MatchNotifierPlugin::on_shutdown)
        .def("get_ui_components", &MatchNotifierPlugin::get_ui_components)
        .def("reset_notifications", &MatchNotifierPlugin::reset_notifications)
        .def("get_match_history", &MatchNotifierPlugin::get_match_history)
        .def("get_total_matches", &MatchNotifierPlugin::get_total_matches)
        .def("get_latest_match", &MatchNotifierPlugin::get_latest_match)
        .def("set_notification_settings", &MatchNotifierPlugin::set_notification_settings, py::arg("settings"))
        .def("get_notification_settings", &MatchNotifierPlugin::get_notification_settings)
        .def("register_match_callback", &MatchNotifierPlugin::register_match_callback, py::arg("callback"))
        .def("unregister_match_callback", &MatchNotifierPlugin::unregister_match_callback, py::arg("callback"))
        .def("on_match_event", &MatchNotifierPlugin::on_match_event, py::arg("match_data"))
        .def("get_notification_summary", &MatchNotifierPlugin::get_notification_summary)
        .def("export_matches", &MatchNotifierPlugin::export_matches, py::arg("file_path"))
        .def("on_start", &MatchNotifierPlugin::on_start, py::arg("selected_list_path"))
        .def("on_match_found", &MatchNotifierPlugin::on_match_found, py::arg("matches"), py::arg("iteration"))
        .def("on_finish", &MatchNotifierPlugin::on_finish, py::arg("final_metrics"))
        .def("on_reset", &MatchNotifierPlugin::on_reset)
        .def("health_check", &MatchNotifierPlugin::health_check)
        .def("get_name", &MatchNotifierPlugin::get_name)
        .def("get_priority", &MatchNotifierPlugin::get_priority)
        .def("__repr__", [](const MatchNotifierPlugin& self) {
            return "<MatchNotifierPlugin(total_matches=" + std::to_string(self.get_total_matches()) +
                   ", priority=" + std::to_string(self.get_priority()) + ")>";
        });
}
// END_BINDINGS_MATCH_NOTIFIER_PLUGIN


// START_MODULE_DEFINITION
PYBIND11_MODULE(match_notifier_plugin_cpp, m) {
    m.doc() = "C++ плагин уведомлений о совпадениях с поддержкой наследования из Python";
    m.attr("__version__") = "2.0.0";

    bind_match_severity(m);
    bind_notification_type(m);
    bind_match_entry(m);
    bind_notification_settings(m);
    bind_match_notifier_plugin(m);
}
// END_MODULE_DEFINITION
