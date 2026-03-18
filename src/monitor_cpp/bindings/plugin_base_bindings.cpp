// FILE: src/monitor_cpp/bindings/plugin_base_bindings.cpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Python bindings для модуля plugin_base через pybind11.
// Обеспечивает доступ к C++ классам плагинов из Python.
// SCOPE: Python интеграция, pybind11 bindings
// KEYWORDS: [TECH(9): pybind11; DOMAIN(8): PythonBindings; CONCEPT(7): Interop]
// END_MODULE_CONTRACT

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <pybind11/chrono.h>
#include <memory>
#include <string>
#include <vector>
#include "../plugins/plugin_base.hpp"

namespace py = pybind11;
using namespace pybind11::literals;

//==============================================================================
// Helper Functions for Bindings
//==============================================================================

// START_FUNCTION_bind_plugin_state
// START_CONTRACT:
// PURPOSE: Создание Python bindings для PluginState
// INPUTS: m - pybind11 модуль
// OUTPUTS: none
// KEYWORDS: [TECH(8): pybind11; CONCEPT(6): Binding]
// END_CONTRACT
void bind_plugin_state(py::module& m) {
    py::enum_<PluginState>(m, "PluginState")
        .value("UNINITIALIZED", PluginState::UNINITIALIZED)
        .value("INITIALIZING", PluginState::INITIALIZING)
        .value("ACTIVE", PluginState::ACTIVE)
        .value("PAUSED", PluginState::PAUSED)
        .value("STOPPED", PluginState::STOPPED)
        .value("ERROR", PluginState::ERROR)
        .export_values();
}
// END_FUNCTION_bind_plugin_state

// START_FUNCTION_bind_plugin_capabilities
// START_CONTRACT:
// PURPOSE: Создание Python bindings для PluginCapabilities
// INPUTS: m - pybind11 модуль
// OUTPUTS: none
// KEYWORDS: [TECH(8): pybind11; CONCEPT(6): Binding]
// END_CONTRACT
void bind_plugin_capabilities(py::module& m) {
    py::class_<PluginCapabilities>(m, "PluginCapabilities")
        .def(py::init<>(), "Default constructor")
        .def(py::init<bool, bool, bool>(),
             py::arg("supports_realtime"),
             py::arg("supports_notifications"),
             py::arg("supports_export"),
             "Constructor with all capabilities")
        .def_readwrite("supports_realtime", &PluginCapabilities::supports_realtime)
        .def_readwrite("supports_notifications", &PluginCapabilities::supports_notifications)
        .def_readwrite("supports_export", &PluginCapabilities::supports_export);
}
// END_FUNCTION_bind_plugin_capabilities

// START_FUNCTION_bind_plugin_info
// START_CONTRACT:
// PURPOSE: Создание Python bindings для PluginInfo
// INPUTS: m - pybind11 модуль
// OUTPUTS: none
// KEYWORDS: [TECH(8): pybind11; CONCEPT(6): Binding]
// END_CONTRACT
void bind_plugin_info(py::module& m) {
    py::class_<PluginInfo>(m, "PluginInfo")
        .def(py::init<>(), "Default constructor")
        .def(py::init<const std::string&, const std::string&,
                      const std::string&, const std::string&>(),
             py::arg("name"),
             py::arg("version"),
             py::arg("description"),
             py::arg("author"),
             "Constructor with required parameters")
        .def_readwrite("name", &PluginInfo::name)
        .def_readwrite("version", &PluginInfo::version)
        .def_readwrite("description", &PluginInfo::description)
        .def_readwrite("author", &PluginInfo::author)
        .def_readwrite("capabilities", &PluginInfo::capabilities)
        .def("__repr__", &PluginInfo::to_string);
}
// END_FUNCTION_bind_plugin_info

// START_FUNCTION_bind_plugin_config
// START_CONTRACT:
// PURPOSE: Создание Python bindings для PluginConfig
// INPUTS: m - pybind11 модуль
// OUTPUTS: none
// KEYWORDS: [TECH(8): pybind11; CONCEPT(6): Binding]
// END_CONTRACT
void bind_plugin_config(py::module& m) {
    py::class_<PluginConfig>(m, "PluginConfig")
        .def(py::init<>(), "Default constructor")
        .def(py::init<bool, int, double>(),
             py::arg("enabled"),
             py::arg("priority"),
             py::arg("update_interval"),
             "Constructor with all parameters")
        .def_readwrite("enabled", &PluginConfig::enabled)
        .def_readwrite("priority", &PluginConfig::priority)
        .def_readwrite("update_interval", &PluginConfig::update_interval)
        .def_readwrite("custom_config", &PluginConfig::custom_config);
}
// END_FUNCTION_bind_plugin_config

// START_FUNCTION_bind_update_context
// START_CONTRACT:
// PURPOSE: Создание Python bindings для UpdateContext
// INPUTS: m - pybind11 модуль
// OUTPUTS: none
// KEYWORDS: [TECH(8): pybind11; CONCEPT(6): Binding]
// END_CONTRACT
void bind_update_context(py::module& m) {
    py::class_<UpdateContext>(m, "UpdateContext")
        .def(py::init<>(), "Default constructor")
        .def(py::init<int64_t, const PluginMetrics&>(),
             py::arg("iteration"),
             py::arg("metrics"),
             "Constructor with iteration and metrics")
        .def_readwrite("timestamp", &UpdateContext::timestamp)
        .def_readwrite("iteration", &UpdateContext::iteration)
        .def_readwrite("metrics", &UpdateContext::metrics)
        .def_readwrite("matches", &UpdateContext::matches);
}
// END_FUNCTION_bind_update_context

// START_FUNCTION_bind_plugin_logger
// START_CONTRACT:
// PURPOSE: Создание Python bindings для PluginLogger
// INPUTS: m - pybind11 модуль
// OUTPUTS: none
// KEYWORDS: [TECH(8): pybind11; CONCEPT(6): Binding]
// END_CONTRACT
void bind_plugin_logger(py::module& m) {
    py::enum_<PluginLogger::Level>(m, "LogLevel")
        .value("DEBUG", PluginLogger::Level::DEBUG)
        .value("INFO", PluginLogger::Level::INFO)
        .value("WARNING", PluginLogger::Level::WARNING)
        .value("ERROR", PluginLogger::Level::ERROR)
        .value("CRITICAL", PluginLogger::Level::CRITICAL)
        .export_values();
    
    py::class_<PluginLogger>(m, "PluginLogger")
        .def(py::init<const std::string&>(),
             py::arg("plugin_name"),
             "Create logger for plugin")
        .def("debug", &PluginLogger::debug,
             "Log debug message")
        .def("info", &PluginLogger::info,
             "Log info message")
        .def("warning", &PluginLogger::warning,
             "Log warning message")
        .def("error", &PluginLogger::error,
             "Log error message")
        .def("critical", &PluginLogger::critical,
             "Log critical message")
        .def("log", &PluginLogger::log,
             "Log message with level",
             py::arg("level"),
             py::arg("message"));
}
// END_FUNCTION_bind_plugin_logger

//==============================================================================
// Trampoline Class for IPlugin
//==============================================================================

// START_CLASS_PyPlugin
// START_CONTRACT:
// PURPOSE: Trampoline класс для поддержки Python плагинов
// KEYWORDS: [TECH(8): pybind11; CONCEPT(7): Trampoline]
// END_CONTRACT
class PyPlugin : public IPlugin {
public:
    using IPlugin::IPlugin;
    
    //==============================================================================
    // Lifecycle (Abstract - must implement)
    //==============================================================================
    void initialize() override {
        PYBIND11_OVERRIDE_PURE(
            void,
            IPlugin,
            initialize
        );
    }
    
    void shutdown() override {
        PYBIND11_OVERRIDE_PURE(
            void,
            IPlugin,
            shutdown
        );
    }
    
    PluginInfo get_info() const override {
        PYBIND11_OVERRIDE_PURE(
            PluginInfo,
            IPlugin,
            get_info
        );
    }
    
    PluginState get_state() const override {
        PYBIND11_OVERRIDE_PURE(
            PluginState,
            IPlugin,
            get_state
        );
    }
    
    //==============================================================================
    // Virtual Methods (can override)
    //==============================================================================
    void on_update(const UpdateContext& context) override {
        PYBIND11_OVERRIDE(
            void,
            IPlugin,
            on_update,
            context
        );
    }
    
    void on_metrics_update(const PluginMetrics& metrics) override {
        PYBIND11_OVERRIDE(
            void,
            IPlugin,
            on_metrics_update,
            metrics
        );
    }
    
    void on_match_found(const MatchList& matches, int iteration) override {
        PYBIND11_OVERRIDE(
            void,
            IPlugin,
            on_match_found,
            matches,
            iteration
        );
    }
    
    void on_start(const std::string& selected_list_path) override {
        PYBIND11_OVERRIDE(
            void,
            IPlugin,
            on_start,
            selected_list_path
        );
    }
    
    void on_finish(const PluginMetrics& final_metrics) override {
        PYBIND11_OVERRIDE(
            void,
            IPlugin,
            on_finish,
            final_metrics
        );
    }
    
    void on_reset() override {
        PYBIND11_OVERRIDE(
            void,
            IPlugin,
            on_reset
        );
    }
    
    void start() override {
        PYBIND11_OVERRIDE(
            void,
            IPlugin,
            start
        );
    }
    
    void stop() override {
        PYBIND11_OVERRIDE(
            void,
            IPlugin,
            stop
        );
    }
    
    void pause() override {
        PYBIND11_OVERRIDE(
            void,
            IPlugin,
            pause
        );
    }
    
    void resume() override {
        PYBIND11_OVERRIDE(
            void,
            IPlugin,
            resume
        );
    }
    
    bool health_check() const override {
        PYBIND11_OVERRIDE(
            bool,
            IPlugin,
            health_check
        );
    }
    
    PluginConfig get_config() const override {
        PYBIND11_OVERRIDE(
            PluginConfig,
            IPlugin,
            get_config
        );
    }
    
    void set_config(const PluginConfig& config) override {
        PYBIND11_OVERRIDE(
            void,
            IPlugin,
            set_config,
            config
        );
    }
};
// END_CLASS_PyPlugin

// START_FUNCTION_bind_i_plugin
// START_CONTRACT:
// PURPOSE: Создание Python bindings для IPlugin
// INPUTS: m - pybind11 модуль
// OUTPUTS: none
// KEYWORDS: [TECH(8): pybind11; CONCEPT(6): Binding]
// END_CONTRACT
void bind_i_plugin(py::module& m) {
    py::class_<IPlugin, PyPlugin>(m, "IPlugin")
        .def(py::init<>())
        
        // Lifecycle
        .def("initialize", &IPlugin::initialize,
             "Initialize the plugin")
        .def("shutdown", &IPlugin::shutdown,
             "Shutdown the plugin")
        .def("get_info", &IPlugin::get_info,
             "Get plugin information")
        .def("get_state", &IPlugin::get_state,
             "Get plugin state")
        
        // Events
        .def("on_update", &IPlugin::on_update,
             "Handle update event",
             py::arg("context"))
        .def("on_metrics_update", &IPlugin::on_metrics_update,
             "Handle metrics update",
             py::arg("metrics"))
        .def("on_match_found", &IPlugin::on_match_found,
             "Handle match found",
             py::arg("matches"),
             py::arg("iteration"))
        .def("on_start", &IPlugin::on_start,
             "Handle generator start",
             py::arg("selected_list_path"))
        .def("on_finish", &IPlugin::on_finish,
             "Handle generator finish",
             py::arg("final_metrics"))
        .def("on_reset", &IPlugin::on_reset,
             "Handle reset")
        
        // Control
        .def("start", &IPlugin::start,
             "Start the plugin")
        .def("stop", &IPlugin::stop,
             "Stop the plugin")
        .def("pause", &IPlugin::pause,
             "Pause the plugin")
        .def("resume", &IPlugin::resume,
             "Resume the plugin")
        
        // Utility
        .def("health_check", &IPlugin::health_check,
             "Check plugin health")
        .def("get_config", &IPlugin::get_config,
             "Get plugin config")
        .def("set_config", &IPlugin::set_config,
             "Set plugin config",
             py::arg("config"));
}
// END_FUNCTION_bind_i_plugin

//==============================================================================
// BasePlugin Binding
//==============================================================================

// START_CLASS_PyBasePlugin
// START_CONTRACT:
// PURPOSE: Trampoline класс для BasePlugin
// KEYWORDS: [TECH(8): pybind11; CONCEPT(7): Trampoline]
// END_CONTRACT
class PyBasePlugin : public BasePlugin {
public:
    using BasePlugin::BasePlugin;
    
    void initialize_impl() override {
        PYBIND11_OVERRIDE_PURE(
            void,
            BasePlugin,
            initialize_impl
        );
    }
    
    void shutdown_impl() override {
        PYBIND11_OVERRIDE_PURE(
            void,
            BasePlugin,
            shutdown_impl
        );
    }
    
    void on_update_impl(const UpdateContext& context) override {
        PYBIND11_OVERRIDE_PURE(
            void,
            BasePlugin,
            on_update_impl,
            context
        );
    }
};
// END_CLASS_PyBasePlugin

// START_FUNCTION_bind_base_plugin
// START_CONTRACT:
// PURPOSE: Создание Python bindings для BasePlugin
// INPUTS: m - pybind11 модуль
// OUTPUTS: none
// KEYWORDS: [TECH(8): pybind11; CONCEPT(6): Binding]
// END_CONTRACT
void bind_base_plugin(py::module& m) {
    py::class_<BasePlugin, PyBasePlugin>(m, "BasePlugin")
        .def(py::init<const PluginInfo&, const PluginConfig&>(),
             py::arg("info"),
             py::arg("config") = PluginConfig(),
             "Construct BasePlugin with info and config")
        
        // Override lifecycle methods
        .def("initialize", &BasePlugin::initialize,
             "Initialize the plugin")
        .def("shutdown", &BasePlugin::shutdown,
             "Shutdown the plugin")
        
        // Info and state
        .def("get_info", &BasePlugin::get_info,
             "Get plugin information")
        .def("get_state", &BasePlugin::get_state,
             "Get plugin state")
        
        // Events
        .def("on_update", &BasePlugin::on_update,
             "Handle update event",
             py::arg("context"))
        .def("on_metrics_update", &BasePlugin::on_metrics_update,
             "Handle metrics update",
             py::arg("metrics"))
        .def("on_match_found", &BasePlugin::on_match_found,
             "Handle match found",
             py::arg("matches"),
             py::arg("iteration"))
        .def("on_start", &BasePlugin::on_start,
             "Handle generator start",
             py::arg("selected_list_path"))
        .def("on_finish", &BasePlugin::on_finish,
             "Handle generator finish",
             py::arg("final_metrics"))
        .def("on_reset", &BasePlugin::on_reset,
             "Handle reset")
        
        // Control
        .def("start", &BasePlugin::start,
             "Start the plugin")
        .def("stop", &BasePlugin::stop,
             "Stop the plugin")
        .def("pause", &BasePlugin::pause,
             "Pause the plugin")
        .def("resume", &BasePlugin::resume,
             "Resume the plugin")
        
        // Utility
        .def("health_check", &BasePlugin::health_check,
             "Check plugin health")
        .def("get_config", &BasePlugin::get_config,
             "Get plugin config")
        .def("set_config", &BasePlugin::set_config,
             "Set plugin config",
             py::arg("config"));
}
// END_FUNCTION_bind_base_plugin

//==============================================================================
// PluginManager Binding
//==============================================================================

// START_FUNCTION_bind_plugin_manager
// START_CONTRACT:
// PURPOSE: Создание Python bindings для PluginManager
// INPUTS: m - pybind11 модуль
// OUTPUTS: none
// KEYWORDS: [TECH(8): pybind11; CONCEPT(6): Binding]
// END_CONTRACT
void bind_plugin_manager(py::module& m) {
    py::class_<PluginManager>(m, "PluginManager")
        .def_static("instance", &PluginManager::instance,
                    "Get singleton instance")
        
        // Registration
        .def("register_plugin", &PluginManager::register_plugin,
             "Register a plugin",
             py::arg("plugin"))
        .def("register_factory", &PluginManager::register_factory,
             "Register a plugin factory",
             py::arg("plugin_name"),
             py::arg("factory"))
        .def("unregister_plugin", &PluginManager::unregister_plugin,
             "Unregister a plugin",
             py::arg("plugin_name"))
        .def("get_plugin", &PluginManager::get_plugin,
             "Get plugin by name",
             py::arg("plugin_name"))
        .def("get_all_plugins", &PluginManager::get_all_plugins,
             "Get all plugins")
        .def("get_enabled_plugins", &PluginManager::get_enabled_plugins,
             "Get enabled plugins")
        .def("has_plugin", &PluginManager::has_plugin,
             "Check if plugin exists",
             py::arg("plugin_name"))
        .def("count", &PluginManager::count,
             "Get plugin count")
        .def("clear", &PluginManager::clear,
             "Clear all plugins")
        
        // Lifecycle
        .def("initialize_all", &PluginManager::initialize_all,
             "Initialize all plugins")
        .def("shutdown_all", &PluginManager::shutdown_all,
             "Shutdown all plugins")
        .def("start_all", &PluginManager::start_all,
             "Start all plugins")
        .def("stop_all", &PluginManager::stop_all,
             "Stop all plugins")
        .def("pause_all", &PluginManager::pause_all,
             "Pause all plugins")
        .def("resume_all", &PluginManager::resume_all,
             "Resume all plugins")
        .def("reset_all", &PluginManager::reset_all,
             "Reset all plugins")
        
        // Notifications
        .def("notify_all_metric_update", &PluginManager::notify_all_metric_update,
             "Notify all plugins of metric update",
             py::arg("metrics"))
        .def("notify_all_update", &PluginManager::notify_all_update,
             "Notify all plugins of update",
             py::arg("context"))
        .def("notify_all_start", &PluginManager::notify_all_start,
             "Notify all plugins of generator start",
             py::arg("selected_list_path"))
        .def("notify_all_finish", &PluginManager::notify_all_finish,
             "Notify all plugins of generator finish",
             py::arg("final_metrics"))
        .def("notify_all_reset", &PluginManager::notify_all_reset,
             "Notify all plugins of reset")
        .def("notify_all_match_found", &PluginManager::notify_all_match_found,
             "Notify all plugins of match found",
             py::arg("matches"),
             py::arg("iteration"))
        
        // Health
        .def("health_check_all", &PluginManager::health_check_all,
             "Check health of all plugins");
}
// END_FUNCTION_bind_plugin_manager

//==============================================================================
// Priority Converter Binding
//==============================================================================

// START_FUNCTION_bind_priority_converter
// START_CONTRACT:
// PURPOSE: Создание Python bindings для PriorityConverter
// INPUTS: m - pybind11 модуль
// OUTPUTS: none
// KEYWORDS: [TECH(8): pybind11; CONCEPT(6): Binding]
// END_CONTRACT
void bind_priority_converter(py::module& m) {
    m.def("priority_from_string", &PriorityConverter::from_string,
          "Convert string to priority",
          py::arg("priority_str"));
    
    m.def("priority_to_string", &PriorityConverter::to_string,
          "Convert priority to string",
          py::arg("priority"));
}

//==============================================================================
// Module Definition
//==============================================================================

// START_FUNCTION_PYBIND11_MODULE
// START_CONTRACT:
// PURPOSE: Определение Python extension module
// KEYWORDS: [TECH(9): pybind11; CONCEPT(7): Module]
// END_CONTRACT
PYBIND11_MODULE(plugin_base_cpp, m) {
    m.doc() = "C++ Plugin Base module for Bitcoin Wallet Generator Monitoring";
    m.attr("__version__") = "1.0.0";
    
    // Bind enums and structs
    bind_plugin_state(m);
    bind_plugin_capabilities(m);
    bind_plugin_info(m);
    bind_plugin_config(m);
    bind_update_context(m);
    bind_plugin_logger(m);
    bind_priority_converter(m);
    
    // Bind interfaces
    bind_i_plugin(m);
    bind_base_plugin(m);
    
    // Bind manager
    bind_plugin_manager(m);
    
    // Module-level functions
    m.def("create_plugin_info",
          [](const std::string& name,
             const std::string& version,
             const std::string& description,
             const std::string& author,
             bool realtime = false,
             bool notifications = false,
             bool export_data = false) {
              PluginInfo info(name, version, description, author);
              info.capabilities = PluginCapabilities(realtime, notifications, export_data);
              return info;
          },
          py::arg("name"),
          py::arg("version"),
          py::arg("description"),
          py::arg("author"),
          py::arg("supports_realtime") = false,
          py::arg("supports_notifications") = false,
          py::arg("supports_export") = false,
          "Create PluginInfo with capabilities");
    
    m.def("create_plugin_config",
          [](bool enabled, int priority, double update_interval) {
              return PluginConfig(enabled, priority, update_interval);
          },
          py::arg("enabled") = true,
          py::arg("priority") = 50,
          py::arg("update_interval") = 1.0,
          "Create PluginConfig");
}

// END_FUNCTION_PYBIND11_MODULE
