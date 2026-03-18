// FILE: src/monitor_cpp/bindings/match_notifier_plugin_bindings.cpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Python bindings для модуля match_notifier_plugin
// SCOPE: pybind11 bindings, Trampoline класс для Python плагинов
// KEYWORDS: [DOMAIN(9): PythonBindings; TECH(8): pybind11; CONCEPT(7): Trampoline]
// END_MODULE_CONTRACT

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/complex.h>
#include <pybind11/chrono.h>
#include <memory>

#include "plugins/match_notifier_plugin.hpp"

namespace py = pybind11;

//==============================================================================
// TRAMPOLINE КЛАСС ДЛЯ MATCHNOTIFIERPLUGIN
//==============================================================================

/**
 * @brief Trampoline класс PyMatchNotifierPlugin
 * 
 * CONTRACT:
 * PURPOSE: Позволяет наследоваться от MatchNotifierPlugin в Python
 * PYBIND11_OVERRIDE используется для обработки вызовов виртуальных методов
 * из C++ в Python код
 */
class PyMatchNotifierPlugin : public MatchNotifierPlugin {
public:
    using MatchNotifierPlugin::MatchNotifierPlugin;
    
    // START_METHOD_INITIALIZE_TRAMPOLINE
    // PURPOSE: Инициализация плагина (trampoline для Python)
    // END_METHOD_INITIALIZE_TRAMPOLINE
    void initialize() override {
        PYBIND11_OVERRIDE(
            void,
            MatchNotifierPlugin,
            initialize
        );
    }
    
    // START_METHOD_SHUTDOWN_TRAMPOLINE
    // PURPOSE: Завершение работы (trampoline для Python)
    // END_METHOD_SHUTDOWN_TRAMPOLINE
    void shutdown() override {
        PYBIND11_OVERRIDE(
            void,
            MatchNotifierPlugin,
            shutdown
        );
    }
    
    // START_METHOD_GET_INFO_TRAMPOLINE
    // PURPOSE: Получение информации о плагине (trampoline для Python)
    // END_METHOD_GET_INFO_TRAMPOLINE
    PluginInfo get_info() const override {
        PYBIND11_OVERRIDE(
            PluginInfo,
            MatchNotifierPlugin,
            get_info
        );
    }
    
    // START_METHOD_GET_STATE_TRAMPOLINE
    // PURPOSE: Получение состояния плагина (trampoline для Python)
    // END_METHOD_GET_STATE_TRAMPOLINE
    PluginState get_state() const override {
        PYBIND11_OVERRIDE(
            PluginState,
            MatchNotifierPlugin,
            get_state
        );
    }
    
    // START_METHOD_ON_METRICS_UPDATE_TRAMPOLINE
    // PURPOSE: Обработка обновления метрик (trampoline для Python)
    // END_METHOD_ON_METRICS_UPDATE_TRAMPOLINE
    void on_metrics_update(const PluginMetrics& metrics) override {
        PYBIND11_OVERRIDE(
            void,
            MatchNotifierPlugin,
            on_metrics_update,
            metrics
        );
    }
    
    // START_METHOD_ON_MATCH_FOUND_TRAMPOLINE
    // PURPOSE: Обработка совпадений (trampoline для Python)
    // END_METHOD_ON_MATCH_FOUND_TRAMPOLINE
    void on_match_found(const MatchList& matches, int iteration) override {
        PYBIND11_OVERRIDE(
            void,
            MatchNotifierPlugin,
            on_match_found,
            matches,
            iteration
        );
    }
    
    // START_METHOD_ON_START_TRAMPOLINE
    // PURPOSE: Обработчик запуска (trampoline для Python)
    // END_METHOD_ON_START_TRAMPOLINE
    void on_start(const std::string& selected_list_path) override {
        PYBIND11_OVERRIDE(
            void,
            MatchNotifierPlugin,
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
            MatchNotifierPlugin,
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
            MatchNotifierPlugin,
            on_reset
        );
    }
};

//==============================================================================
// HELPER FUNCTIONS
//==============================================================================

// START_HELPER_MATCH_INFO_TO_DICT
// START_CONTRACT:
// PURPOSE: Конвертация MatchInfo в Python dict
// INPUTS: info — структура MatchInfo
// OUTPUTS: py::dict — Python словарь
// KEYWORDS: [CONCEPT(7): Conversion]
// END_CONTRACT
py::dict match_info_to_dict(const MatchInfo& info) {
    py::dict dict;
    
    // Конвертируем timestamp в микросекунды
    dict["timestamp"] = std::chrono::duration_cast<std::chrono::microseconds>(
        info.timestamp.time_since_epoch()).count();
    dict["iteration"] = info.iteration;
    dict["match_number"] = info.match_number;
    dict["address"] = info.address;
    dict["wallet_name"] = info.wallet_name;
    dict["list_name"] = info.list_name;
    dict["priority"] = static_cast<int>(info.priority);
    
    if (info.private_key.has_value()) {
        dict["private_key"] = info.private_key.value();
    } else {
        dict["private_key"] = py::none();
    }
    
    return dict;
}

// START_HELPER_MATCH_HISTORY_ENTRY_TO_DICT
// START_CONTRACT:
// PURPOSE: Конвертация MatchHistoryEntry в Python dict
// INPUTS: entry — структура MatchHistoryEntry
// OUTPUTS: py::dict — Python словарь
// KEYWORDS: [CONCEPT(7): Conversion]
// END_CONTRACT
py::dict match_history_entry_to_dict(const MatchHistoryEntry& entry) {
    py::dict dict;
    dict["entry_id"] = entry.entry_id;
    dict["match"] = match_info_to_dict(entry.match);
    dict["notification_sent"] = entry.notification_sent;
    dict["timestamp"] = std::chrono::duration_cast<std::chrono::microseconds>(
        entry.timestamp.time_since_epoch()).count();
    return dict;
}

//==============================================================================
// ОПРЕДЕЛЕНИЕ PYTHON МОДУЛЯ
//==============================================================================

PYBIND11_MODULE(match_notifier_plugin, m) {
    m.doc() = "C++ Match Notifier Plugin for Bitcoin Wallet Generator Monitoring";
    
    //==========================================================================
    // КОНСТАНТЫ
    //==========================================================================
    
    m.attr("PLUGIN_NAME") = MATCH_NOTIFIER_PLUGIN_NAME;
    m.attr("PLUGIN_VERSION") = MATCH_NOTIFIER_PLUGIN_VERSION;
    m.attr("PLUGIN_PRIORITY") = MATCH_NOTIFIER_PLUGIN_PRIORITY;
    m.attr("MAX_MATCH_HISTORY") = MAX_MATCH_HISTORY;
    
    //==========================================================================
    // ENUMS
    //==========================================================================
    
    // START_BINDING_NOTIFICATION_CHANNEL
    py::enum_<NotificationChannel>(m, "NotificationChannel")
        .value("CONSOLE", NotificationChannel::CONSOLE, "Консольный вывод")
        .value("FILE", NotificationChannel::FILE, "Запись в файл")
        .value("DESKTOP", NotificationChannel::DESKTOP, "Desktop уведомление")
        .value("EMAIL", NotificationChannel::EMAIL, "Email уведомление")
        .export_values();
    // END_BINDING_NOTIFICATION_CHANNEL
    
    // START_BINDING_NOTIFICATION_PRIORITY
    py::enum_<NotificationPriority>(m, "NotificationPriority")
        .value("LOW", NotificationPriority::LOW, "Низкий приоритет")
        .value("NORMAL", NotificationPriority::NORMAL, "Обычный приоритет")
        .value("HIGH", NotificationPriority::HIGH, "Высокий приоритет")
        .value("CRITICAL", NotificationPriority::CRITICAL, "Критический приоритет")
        .export_values();
    // END_BINDING_NOTIFICATION_PRIORITY
    
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
    
    // START_BINDING_MATCH_INFO
    py::class_<MatchInfo>(m, "MatchInfo")
        .def(py::init<>())
        .def(py::init<int64_t, int64_t, const std::string&>(),
             py::arg("iteration"), 
             py::arg("match_number"), 
             py::arg("address"))
        .def_readwrite("timestamp", &MatchInfo::timestamp)
        .def_readwrite("iteration", &MatchInfo::iteration)
        .def_readwrite("match_number", &MatchInfo::match_number)
        .def_readwrite("address", &MatchInfo::address)
        .def_readwrite("private_key", &MatchInfo::private_key)
        .def_readwrite("wallet_name", &MatchInfo::wallet_name)
        .def_readwrite("list_name", &MatchInfo::list_name)
        .def_readwrite("priority", &MatchInfo::priority)
        .def("to_json", &MatchInfo::to_json)
        .def("to_dict", &match_info_to_dict)
        .def("to_string", &MatchInfo::to_string)
        .def("__repr__", &MatchInfo::to_string)
        .def_static("determine_priority", &determine_priority_level, py::arg("iteration"));
    // END_BINDING_MATCH_INFO
    
    // START_BINDING_MATCH_NOTIFIER_CONFIG
    py::class_<MatchNotifierConfig>(m, "MatchNotifierConfig")
        .def(py::init<>())
        .def(py::init<bool, bool, bool, bool, double>(),
             py::arg("desktop"),
             py::arg("sound"),
             py::arg("log"),
             py::arg("ui"),
             py::arg("cooldown") = 5.0)
        .def_readwrite("desktop_enabled", &MatchNotifierConfig::desktop_enabled)
        .def_readwrite("sound_enabled", &MatchNotifierConfig::sound_enabled)
        .def_readwrite("log_enabled", &MatchNotifierConfig::log_enabled)
        .def_readwrite("ui_enabled", &MatchNotifierConfig::ui_enabled)
        .def_readwrite("cooldown_seconds", &MatchNotifierConfig::cooldown_seconds)
        .def_readwrite("min_priority", &MatchNotifierConfig::min_priority)
        .def_readwrite("enabled_channels", &MatchNotifierConfig::enabled_channels)
        .def("is_any_enabled", &MatchNotifierConfig::is_any_enabled)
        .def("reset", &MatchNotifierConfig::reset)
        .def("__repr__", &MatchNotifierConfig::to_string);
    // END_BINDING_MATCH_NOTIFIER_CONFIG
    
    // START_BINDING_MATCH_HISTORY_ENTRY
    py::class_<MatchHistoryEntry>(m, "MatchHistoryEntry")
        .def(py::init<>())
        .def(py::init<uint64_t, const MatchInfo&>(),
             py::arg("entry_id"), py::arg("match"))
        .def_readwrite("entry_id", &MatchHistoryEntry::entry_id)
        .def_readwrite("match", &MatchHistoryEntry::match)
        .def_readwrite("notification_sent", &MatchHistoryEntry::notification_sent)
        .def_readwrite("timestamp", &MatchHistoryEntry::timestamp)
        .def("to_dict", &match_history_entry_to_dict);
    // END_BINDING_MATCH_HISTORY_ENTRY
    
    //==========================================================================
    // КЛАСС MATCH_NOTIFIER PLUGIN
    //==========================================================================
    
    // START_BINDING_MATCH_NOTIFIER_PLUGIN
    py::class_<MatchNotifierPlugin, PyMatchNotifierPlugin>(m, "MatchNotifierPlugin")
        .def(py::init<>())
        
        // Constants
        .def_readonly_static("PLUGIN_NAME", &MatchNotifierPlugin::PLUGIN_NAME)
        .def_readonly_static("PLUGIN_VERSION", &MatchNotifierPlugin::PLUGIN_VERSION)
        .def_readonly_static("PLUGIN_PRIORITY", &MatchNotifierPlugin::PLUGIN_PRIORITY)
        
        // Абстрактные методы IPlugin
        .def("initialize", &MatchNotifierPlugin::initialize)
        .def("shutdown", &MatchNotifierPlugin::shutdown)
        .def("get_info", &MatchNotifierPlugin::get_info)
        .def("get_state", &MatchNotifierPlugin::get_state)
        
        // Методы обратного вызова
        .def("on_metrics_update", &MatchNotifierPlugin::on_metrics_update)
        .def("on_match_found", &MatchNotifierPlugin::on_match_found)
        .def("on_start", &MatchNotifierPlugin::on_start)
        .def("on_finish", &MatchNotifierPlugin::on_finish)
        .def("on_reset", &MatchNotifierPlugin::on_reset)
        
        // Методы плагина
        .def("get_match_history", [](const MatchNotifierPlugin& self) {
            py::list history;
            for (const auto& entry : self.get_match_history()) {
                history.append(match_history_entry_to_dict(entry));
            }
            return history;
        })
        .def("get_latest_match", [](const MatchNotifierPlugin& self) -> py::object {
            auto latest = self.get_latest_match();
            if (latest.has_value()) {
                return py::cast(match_history_entry_to_dict(latest.value()));
            }
            return py::none();
        })
        .def("get_total_matches", &MatchNotifierPlugin::get_total_matches)
        .def("is_monitoring", &MatchNotifierPlugin::is_monitoring)
        
        // Управление уведомлениями
        .def("reset_notifications", &MatchNotifierPlugin::reset_notifications)
        .def("export_matches", &MatchNotifierPlugin::export_matches)
        .def("get_notification_config", &MatchNotifierPlugin::get_notification_config)
        .def("set_notification_config", &MatchNotifierPlugin::set_notification_config)
        .def("get_notification_summary", &MatchNotifierPlugin::get_notification_summary)
        .def("send_notification", &MatchNotifierPlugin::send_notification)
        .def("log_match", &MatchNotifierPlugin::log_match)
        
        // Callback система
        .def("register_match_callback", [](MatchNotifierPlugin& self, py::function callback) {
            self.register_match_callback([callback](const MatchInfo& info) {
                callback(match_info_to_dict(info));
            });
        })
        
        // Properties
        .def_property_readonly("name", [](const MatchNotifierPlugin& self) {
            return self.get_info().name;
        })
        .def_property_readonly("total_matches", &MatchNotifierPlugin::get_total_matches)
        .def_property_readonly("is_monitoring", &MatchNotifierPlugin::is_monitoring);
    // END_BINDING_MATCH_NOTIFIER_PLUGIN
}
// END_PYTHON_MODULE
