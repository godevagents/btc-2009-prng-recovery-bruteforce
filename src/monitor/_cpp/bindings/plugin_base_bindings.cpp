// FILE: src/monitor/_cpp/bindings/plugin_base_bindings.cpp
// VERSION: 1.0.2
// START_MODULE_CONTRACT:
// PURPOSE: Python bindings для базового класса плагина мониторинга с использованием pybind11.
// Обеспечивает возможность наследования от C++ класса в Python через trampoline.
// SCOPE: Python bindings, trampoline класс, экспорт в Python
// INPUT: Заголовочный файл plugin_base.hpp
// OUTPUT: Скомпилированный Python модуль
// KEYWORDS: [DOMAIN(9): Pybind11; DOMAIN(8): PythonBindings; TECH(7): Trampoline]
// END_MODULE_CONTRACT

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <pybind11/chrono.h>
#include "plugin_base.hpp"

namespace py = pybind11;

// START_BINDINGS_PLUGIN_METADATA
// START_CONTRACT:
// PURPOSE: Python bindings для структуры PluginMetadata
// KEYWORDS: [PATTERN(7): Pybind11; DOMAIN(8): PythonBindings]
// END_CONTRACT

void bind_plugin_metadata(py::module& m) {
    py::class_<PluginMetadata>(m, "PluginMetadata")
        .def(py::init<>())
        .def(py::init<
            const std::string&,
            const std::string&,
            const std::string&,
            const std::string&,
            const std::vector<std::string>&,
            const std::vector<std::string>&,
            const std::string&,
            const std::string&
        >(),
            py::arg("name"),
            py::arg("version"),
            py::arg("description"),
            py::arg("author"),
            py::arg("dependencies") = std::vector<std::string>{},
            py::arg("tags") = std::vector<std::string>{},
            py::arg("homepage") = "",
            py::arg("license") = ""
        )
        .def(py::init(&PluginMetadata::from_python))
        .def_readwrite("name", &PluginMetadata::name)
        .def_readwrite("version", &PluginMetadata::version)
        .def_readwrite("description", &PluginMetadata::description)
        .def_readwrite("author", &PluginMetadata::author)
        .def_readwrite("dependencies", &PluginMetadata::dependencies)
        .def_readwrite("tags", &PluginMetadata::tags)
        .def_readwrite("homepage", &PluginMetadata::homepage)
        .def_readwrite("license", &PluginMetadata::license)
        .def("__repr__", [](const PluginMetadata& self) {
            return "<PluginMetadata(name='" + self.name + 
                   "', version='" + self.version + 
                   "', description='" + self.description + "')>";
        })
        .def("__eq__", [](const PluginMetadata& self, const PluginMetadata& other) {
            return self.name == other.name && self.version == other.version;
        })
        .def("__hash__", [](const PluginMetadata& self) {
            return std::hash<std::string>()(self.name + self.version);
        });
}
// END_BINDINGS_PLUGIN_METADATA


// START_BINDINGS_MONITOR_APP_PROTOCOL
// START_CONTRACT:
// PURPOSE: Python bindings для класса MonitorAppProtocol
// KEYWORDS: [PATTERN(7): Pybind11; DOMAIN(8): PythonBindings]
// END_CONTRACT

void bind_monitor_app_protocol(py::module& m) {
    py::class_<MonitorAppProtocol>(m, "MonitorAppProtocol")
        .def(py::init<py::object>(), py::arg("app") = py::none())
        .def("register_ui_component", &MonitorAppProtocol::register_ui_component,
             py::arg("component"),
             py::arg("tab_name"))
        .def("log", &MonitorAppProtocol::log,
             py::arg("level"),
             py::arg("message"))
        .def("get_metrics_store", &MonitorAppProtocol::get_metrics_store);
}
// END_BINDINGS_MONITOR_APP_PROTOCOL


// START_BINDINGS_BASE_MONITOR_PLUGIN
// START_CONTRACT:
// PURPOSE: Python bindings для базового класса плагина мониторинга с trampoline
// KEYWORDS: [PATTERN(9): TrampolineClass; DOMAIN(9): Pybind11; TECH(7): PythonBindings]
// END_CONTRACT

void bind_base_monitor_plugin(py::module& m) {
    // Ключевой момент: порядок объявления классов ВАЖЕН!
    // Сначала объявляем trampoline как самостоятельный класс
    py::class_<BaseMonitorPluginTrampoline>(m, "BaseMonitorPluginTrampoline")
        .def(py::init<const std::string&, int>(),
             py::arg("name"),
             py::arg("priority") = 50)
        .def("initialize", &BaseMonitorPluginTrampoline::initialize,
             py::arg("app"))
        .def("on_metric_update", &BaseMonitorPluginTrampoline::on_metric_update,
             py::arg("metrics"))
        .def("on_shutdown", &BaseMonitorPluginTrampoline::on_shutdown)
        .def("get_ui_components", &BaseMonitorPluginTrampoline::get_ui_components)
        .def("get_metadata", &BaseMonitorPluginTrampoline::get_metadata)
        .def("on_start", &BaseMonitorPluginTrampoline::on_start,
             py::arg("selected_list_path"))
        .def("on_match_found", &BaseMonitorPluginTrampoline::on_match_found,
             py::arg("matches"),
             py::arg("iteration"))
        .def("on_finish", &BaseMonitorPluginTrampoline::on_finish,
             py::arg("final_metrics"))
        .def("on_reset", &BaseMonitorPluginTrampoline::on_reset)
        .def("enable", &BaseMonitorPluginTrampoline::enable)
        .def("disable", &BaseMonitorPluginTrampoline::disable)
        .def("is_enabled", &BaseMonitorPluginTrampoline::is_enabled)
        .def("health_check", &BaseMonitorPluginTrampoline::health_check)
        .def("get_name", &BaseMonitorPluginTrampoline::get_name)
        .def("get_priority", &BaseMonitorPluginTrampoline::get_priority)
        .def("set_priority", &BaseMonitorPluginTrampoline::set_priority,
             py::arg("priority"))
        .def_property("enabled", 
                      &BaseMonitorPluginTrampoline::get_enabled,
                      &BaseMonitorPluginTrampoline::set_enabled)
        .def("__lt__", [](const BaseMonitorPlugin& self, const BaseMonitorPlugin& other) {
            return self < other;
        })
        .def("__eq__", [](const BaseMonitorPlugin& self, const BaseMonitorPlugin& other) {
            return self == other;
        })
        .def("__hash__", [](const BaseMonitorPlugin& self) {
            return self.hash();
        });

    // Затем объявляем базовый класс с trampoline в качестве базы
    py::class_<BaseMonitorPlugin, BaseMonitorPluginTrampoline>(m, "BaseMonitorPlugin")
        .def(py::init<const std::string&, int>(),
             py::arg("name"),
             py::arg("priority") = 50)
        .def_static("get_version", []() { return BaseMonitorPlugin::VERSION; })
        .def_static("get_author", []() { return BaseMonitorPlugin::AUTHOR; })
        .def_static("get_description", []() { return BaseMonitorPlugin::DESCRIPTION; })
        .def_readonly_static("VERSION", &BaseMonitorPlugin::VERSION)
        .def_readonly_static("AUTHOR", &BaseMonitorPlugin::AUTHOR)
        .def_readonly_static("DESCRIPTION", &BaseMonitorPlugin::DESCRIPTION)
        .def("initialize", &BaseMonitorPlugin::initialize,
             py::arg("app"))
        .def("on_metric_update", &BaseMonitorPlugin::on_metric_update,
             py::arg("metrics"))
        .def("on_shutdown", &BaseMonitorPlugin::on_shutdown)
        .def("get_ui_components", &BaseMonitorPlugin::get_ui_components)
        .def("get_metadata", &BaseMonitorPlugin::get_metadata)
        .def("on_start", &BaseMonitorPlugin::on_start,
             py::arg("selected_list_path"))
        .def("on_match_found", &BaseMonitorPlugin::on_match_found,
             py::arg("matches"),
             py::arg("iteration"))
        .def("on_finish", &BaseMonitorPlugin::on_finish,
             py::arg("final_metrics"))
        .def("on_reset", &BaseMonitorPlugin::on_reset)
        .def("enable", &BaseMonitorPlugin::enable)
        .def("disable", &BaseMonitorPlugin::disable)
        .def("is_enabled", &BaseMonitorPlugin::is_enabled)
        .def("health_check", &BaseMonitorPlugin::health_check)
        .def("get_name", &BaseMonitorPlugin::get_name)
        .def("get_priority", &BaseMonitorPlugin::get_priority)
        .def("set_priority", &BaseMonitorPlugin::set_priority,
             py::arg("priority"))
        .def_property("name", 
                       &BaseMonitorPlugin::get_name, 
                       nullptr)
        .def_property("priority", 
                       &BaseMonitorPlugin::get_priority, 
                       &BaseMonitorPlugin::set_priority)
        .def_property("enabled", 
                      &BaseMonitorPlugin::get_enabled,
                      &BaseMonitorPlugin::set_enabled)
        .def("__lt__", [](const BaseMonitorPlugin& self, const BaseMonitorPlugin& other) {
            return self < other;
        })
        .def("__eq__", [](const BaseMonitorPlugin& self, const BaseMonitorPlugin& other) {
            return self == other;
        })
        .def("__hash__", [](const BaseMonitorPlugin& self) {
            return self.hash();
        })
        .def("__repr__", [](const BaseMonitorPlugin& self) {
            return "<BaseMonitorPlugin(name='" + self.get_name() + 
                   "', priority=" + std::to_string(self.get_priority()) + 
                   ", enabled=" + (self.is_enabled() ? "True" : "False") + ")>";
        });
}
// END_BINDINGS_BASE_MONITOR_PLUGIN


// START_MODULE_DEFINITION
// START_CONTRACT:
// PURPOSE: Определение Python модуля и точка входа для pybind11
// KEYWORDS: [PATTERN(7): Module; DOMAIN(8): Pybind11]
// END_CONTRACT

PYBIND11_MODULE(plugin_base_cpp, m) {
    m.doc() = "C++ базовый класс плагина мониторинга с поддержкой наследования из Python";
    
    // Версия модуля
    m.attr("__version__") = "1.0.0";
    
    // Привязки классов
    bind_plugin_metadata(m);
    bind_monitor_app_protocol(m);
    bind_base_monitor_plugin(m);
}
// END_MODULE_DEFINITION
