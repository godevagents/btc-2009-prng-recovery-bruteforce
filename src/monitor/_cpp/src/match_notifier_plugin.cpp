// FILE: src/monitor/_cpp/src/match_notifier_plugin.cpp
// VERSION: 2.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Реализация плагина уведомлений о совпадениях на C++.
// SCOPE: Реализация методов MatchNotifierPlugin, MatchEntry, NotificationSettings
// INPUT: Заголовочный файл match_notifier_plugin.hpp
// OUTPUT: Скомпилированный объектный код
// KEYWORDS: [DOMAIN(9): Notifications; DOMAIN(8): PluginSystem; TECH(6): Implementation]
// END_MODULE_CONTRACT

#include "match_notifier_plugin.hpp"
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
// Статические константы класса MatchNotifierPlugin
const std::string MatchNotifierPlugin::VERSION = "1.0.0";
const std::string MatchNotifierPlugin::AUTHOR = "Wallet Generator Team";
const std::string MatchNotifierPlugin::DESCRIPTION = "Плагин уведомлений о совпадениях";
const int32_t MatchNotifierPlugin::MAX_MATCH_HISTORY = 50;
const double MatchNotifierPlugin::NOTIFICATION_COOLDOWN = 5.0;
// END_CONSTANTS_DEFINITION


// START_MATCH_ENTRY_IMPLEMENTATION

// START_CONSTRUCTOR_MATCH_ENTRY_DEFAULT
// START_CONTRACT:
// PURPOSE: Конструктор по умолчанию для MatchEntry
// OUTPUTS: Объект с пустыми значениями
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
MatchEntry::MatchEntry()
    : address("")
    , private_key("")
    , balance(0.0)
    , iteration(0)
    , timestamp(0.0)
    , severity(MatchSeverity::INFO)
    , message("")
{
}
// END_CONSTRUCTOR_MATCH_ENTRY_DEFAULT


// START_CONSTRUCTOR_MATCH_ENTRY_PARAMS
// START_CONTRACT:
// PURPOSE: Конструктор с параметрами для MatchEntry
// INPUTS:
// - address: const std::string& — найденный адрес
// - private_key: const std::string& — приватный ключ
// - balance: double — баланс адреса
// - iteration: int32_t — номер итерации
// - severity: MatchSeverity — уровень серьёзности
// OUTPUTS: Инициализированный объект MatchEntry
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
MatchEntry::MatchEntry(
    const std::string& address,
    const std::string& private_key,
    double balance,
    int32_t iteration,
    MatchSeverity severity)
    : address(address)
    , private_key(private_key)
    , balance(balance)
    , iteration(iteration)
    , timestamp(std::time(nullptr))
    , severity(severity)
    , message("")
{
}
// END_CONSTRUCTOR_MATCH_ENTRY_PARAMS


// START_METHOD_MATCH_ENTRY_FROM_PYTHON
// START_CONTRACT:
// PURPOSE: Создание MatchEntry из Python объекта
// INPUTS:
// - obj: py::object — Python объект (dict)
// OUTPUTS: MatchEntry — созданная запись
// KEYWORDS: [PATTERN(7): Factory; CONCEPT(6): PythonBinding]
// END_CONTRACT
MatchEntry MatchEntry::from_python(py::object obj) {
    MatchEntry entry;

    try {
        if (py::hasattr(obj, "address")) {
            entry.address = obj.attr("address").cast<std::string>();
        }
        if (py::hasattr(obj, "private_key")) {
            entry.private_key = obj.attr("private_key").cast<std::string>();
        }
        if (py::hasattr(obj, "balance")) {
            entry.balance = obj.attr("balance").cast<double>();
        }
        if (py::hasattr(obj, "iteration")) {
            entry.iteration = obj.attr("iteration").cast<int32_t>();
        }
        if (py::hasattr(obj, "timestamp")) {
            entry.timestamp = obj.attr("timestamp").cast<double>();
        }
        if (py::hasattr(obj, "severity")) {
            std::string severity_str = obj.attr("severity").cast<std::string>();
            if (severity_str == "info") entry.severity = MatchSeverity::INFO;
            else if (severity_str == "success") entry.severity = MatchSeverity::SUCCESS;
            else if (severity_str == "warning") entry.severity = MatchSeverity::WARNING;
            else if (severity_str == "critical") entry.severity = MatchSeverity::CRITICAL;
        }
        if (py::hasattr(obj, "message")) {
            entry.message = obj.attr("message").cast<std::string>();
        }
    } catch (const py::error_already_set& e) {
        std::cerr << "[MatchEntry][FROM_PYTHON][ExceptionCaught] Ошибка при извлечении атрибутов: " << e.what() << std::endl;
    }

    return entry;
}
// END_METHOD_MATCH_ENTRY_FROM_PYTHON


// START_METHOD_MATCH_ENTRY_TO_PYTHON
// START_CONTRACT:
// PURPOSE: Конвертация MatchEntry в Python словарь
// OUTPUTS: py::dict — Python словарь
// KEYWORDS: [CONCEPT(6): Converter; DOMAIN(8): PythonBinding]
// END_CONTRACT
py::dict MatchEntry::to_python() const {
    py::dict dict;
    dict["address"] = address;
    dict["private_key"] = private_key;
    dict["balance"] = balance;
    dict["iteration"] = iteration;
    dict["timestamp"] = timestamp;
    dict["severity"] = get_severity_string();
    dict["message"] = message;
    return dict;
}
// END_METHOD_MATCH_ENTRY_TO_PYTHON


// START_METHOD_MATCH_ENTRY_GET_SEVERITY_STRING
// START_CONTRACT:
// PURPOSE: Получение строкового представления серьёзности
// OUTPUTS: std::string — строка серьёзности
// KEYWORDS: [CONCEPT(6): Converter]
// END_CONTRACT
std::string MatchEntry::get_severity_string() const {
    switch (severity) {
        case MatchSeverity::INFO: return "info";
        case MatchSeverity::SUCCESS: return "success";
        case MatchSeverity::WARNING: return "warning";
        case MatchSeverity::CRITICAL: return "critical";
        default: return "info";
    }
}
// END_METHOD_MATCH_ENTRY_GET_SEVERITY_STRING


// START_METHOD_MATCH_ENTRY_GET_FORMATTED_TIME
// START_CONTRACT:
// PURPOSE: Получение времени в читаемом формате
// OUTPUTS: std::string — отформатированное время
// KEYWORDS: [CONCEPT(6): Timestamp; DOMAIN(5): Format]
// END_CONTRACT
std::string MatchEntry::get_formatted_time() const {
    if (timestamp == 0.0) {
        return "Unknown";
    }

    std::time_t time_val = static_cast<std::time_t>(timestamp);
    std::tm* tm_val = std::localtime(&time_val);

    std::ostringstream oss;
    oss << std::put_time(tm_val, "%Y-%m-%d %H:%M:%S");
    return oss.str();
}
// END_METHOD_MATCH_ENTRY_GET_FORMATTED_TIME

// END_MATCH_ENTRY_IMPLEMENTATION


// START_NOTIFICATION_SETTINGS_IMPLEMENTATION

// START_CONSTRUCTOR_NOTIFICATION_SETTINGS_DEFAULT
// START_CONTRACT:
// PURPOSE: Конструктор по умолчанию для NotificationSettings
// OUTPUTS: Объект с настройками по умолчанию
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
NotificationSettings::NotificationSettings()
    : enable_desktop(true)
    , enable_sound(false)
    , enable_log(true)
    , enable_ui(true)
    , cooldown(5.0)
{
}
// END_CONSTRUCTOR_NOTIFICATION_SETTINGS_DEFAULT


// START_CONSTRUCTOR_NOTIFICATION_SETTINGS_PARAMS
// START_CONTRACT:
// PURPOSE: Конструктор с параметрами для NotificationSettings
// INPUTS:
// - desktop: bool — включены ли desktop уведомления
// - sound: bool — включены ли звуковые уведомления
// - log: bool — включена ли запись в лог
// - ui: bool — включены ли UI уведомления
// - cooldown: double — кулдаун
// OUTPUTS: Инициализированный объект NotificationSettings
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
NotificationSettings::NotificationSettings(
    bool desktop,
    bool sound,
    bool log,
    bool ui,
    double cooldown)
    : enable_desktop(desktop)
    , enable_sound(sound)
    , enable_log(log)
    , enable_ui(ui)
    , cooldown(cooldown)
{
}
// END_CONSTRUCTOR_NOTIFICATION_SETTINGS_PARAMS


// START_METHOD_NOTIFICATION_SETTINGS_FROM_PYTHON
// START_CONTRACT:
// PURPOSE: Создание NotificationSettings из Python словаря
// INPUTS:
// - dict: py::dict — Python словарь настроек
// OUTPUTS: NotificationSettings — созданные настройки
// KEYWORDS: [PATTERN(7): Factory; CONCEPT(6): PythonBinding]
// END_CONTRACT
NotificationSettings NotificationSettings::from_python(py::dict dict) {
    NotificationSettings settings;

    try {
        if (dict.contains("desktop") || dict.contains("enable_desktop")) {
            if (dict.contains("desktop")) {
                settings.enable_desktop = dict["desktop"].cast<bool>();
            } else {
                settings.enable_desktop = dict["enable_desktop"].cast<bool>();
            }
        }
        if (dict.contains("sound") || dict.contains("enable_sound")) {
            if (dict.contains("sound")) {
                settings.enable_sound = dict["sound"].cast<bool>();
            } else {
                settings.enable_sound = dict["enable_sound"].cast<bool>();
            }
        }
        if (dict.contains("log") || dict.contains("enable_log")) {
            if (dict.contains("log")) {
                settings.enable_log = dict["log"].cast<bool>();
            } else {
                settings.enable_log = dict["enable_log"].cast<bool>();
            }
        }
        if (dict.contains("ui") || dict.contains("enable_ui")) {
            if (dict.contains("ui")) {
                settings.enable_ui = dict["ui"].cast<bool>();
            } else {
                settings.enable_ui = dict["enable_ui"].cast<bool>();
            }
        }
        if (dict.contains("cooldown")) {
            settings.cooldown = dict["cooldown"].cast<double>();
        }
    } catch (const py::error_already_set& e) {
        std::cerr << "[NotificationSettings][FROM_PYTHON][ExceptionCaught] Ошибка при извлечении атрибутов: " << e.what() << std::endl;
    }

    return settings;
}
// END_METHOD_NOTIFICATION_SETTINGS_FROM_PYTHON


// START_METHOD_NOTIFICATION_SETTINGS_TO_PYTHON
// START_CONTRACT:
// PURPOSE: Конвертация NotificationSettings в Python словарь
// OUTPUTS: py::dict — Python словарь
// KEYWORDS: [CONCEPT(6): Converter; DOMAIN(8): PythonBinding]
// END_CONTRACT
py::dict NotificationSettings::to_python() const {
    py::dict dict;
    dict["enable_desktop"] = enable_desktop;
    dict["enable_sound"] = enable_sound;
    dict["enable_log"] = enable_log;
    dict["enable_ui"] = enable_ui;
    dict["cooldown"] = cooldown;
    return dict;
}
// END_METHOD_NOTIFICATION_SETTINGS_TO_PYTHON


// START_METHOD_NOTIFICATION_SETTINGS_IS_ANY_ENABLED
// START_CONTRACT:
// PURPOSE: Проверка, включены ли вообще уведомления
// OUTPUTS: bool — true если хотя бы один тип уведомлений включён
// KEYWORDS: [CONCEPT(7): Validation]
// END_CONTRACT
bool NotificationSettings::is_any_enabled() const {
    return enable_desktop || enable_sound || enable_log || enable_ui;
}
// END_METHOD_NOTIFICATION_SETTINGS_IS_ANY_ENABLED

// END_NOTIFICATION_SETTINGS_IMPLEMENTATION


// START_MATCH_NOTIFIER_PLUGIN_IMPLEMENTATION


// START_CONSTRUCTOR_MATCH_NOTIFIER_PLUGIN
// START_CONTRACT:
// PURPOSE: Конструктор плагина уведомлений о совпадениях
// OUTPUTS: Инициализированный объект плагина
// KEYWORDS: [CONCEPT(5): Initialization; DOMAIN(7): PluginSetup]
// END_CONTRACT
MatchNotifierPlugin::MatchNotifierPlugin()
    : BaseMonitorPlugin("MatchNotifierPlugin", 25)  // Приоритет 25
    , _match_history()
    , _total_matches(0)
    , _notification_settings()
    , _match_callbacks()
    , _last_notification_time(0.0)
    , _notification_cooldown(5.0)
    , _is_monitoring(false)
    , _gradio_components(py::none())
{
    // Установка максимального размера истории
    _match_history = std::deque<MatchEntry>();
    _match_history.shrink_to_fit();

    std::stringstream ss;
    ss << "[MatchNotifierPlugin][INIT][ConditionCheck] Инициализирован плагин уведомлений о совпадениях с приоритетом 25";
    log_info(ss.str());
}
// END_CONSTRUCTOR_MATCH_NOTIFIER_PLUGIN


// START_DESTRUCTOR_MATCH_NOTIFIER_PLUGIN
// START_CONTRACT:
// PURPOSE: Деструктор плагина уведомлений
// OUTPUTS: Освобождение ресурсов
// KEYWORDS: [CONCEPT(8): Cleanup]
// END_CONTRACT
MatchNotifierPlugin::~MatchNotifierPlugin() {
    _is_monitoring = false;
    log_info("[MatchNotifierPlugin][DESTRUCTOR][StepComplete] Плагин уведомлений уничтожен");
}
// END_DESTRUCTOR_MATCH_NOTIFIER_PLUGIN


// START_METHOD_INITIALIZE
// START_CONTRACT:
// PURPOSE: Инициализация плагина и регистрация UI компонентов
// INPUTS:
// - app: py::object — ссылка на главное приложение
// OUTPUTS: void
// KEYWORDS: [DOMAIN(8): PluginSetup; CONCEPT(6): Registration]
// END_CONTRACT
void MatchNotifierPlugin::initialize(py::object app) {
    _app = app;
    _is_monitoring = true;
    _last_notification_time = 0.0;

    // Построение UI компонентов
    _gradio_components = _build_ui_components();

    // Регистрация UI компонентов в приложении
    if (!py::isinstance<py::none>(_app) && py::hasattr(_app, "register_ui_component")) {
        try {
            _app.attr("register_ui_component")(_gradio_components, "Notifications");
        } catch (const py::error_already_set& e) {
            std::cerr << "[MatchNotifierPlugin][INITIALIZE][ExceptionCaught] Ошибка при регистрации UI: " << e.what() << std::endl;
        }
    }

    std::stringstream ss;
    ss << "[MatchNotifierPlugin][INITIALIZE][StepComplete] Плагин уведомлений инициализирован";
    log_info(ss.str());
}
// END_METHOD_INITIALIZE


// START_METHOD_ON_METRIC_UPDATE
// START_CONTRACT:
// PURPOSE: Обработка обновления метрик
// INPUTS:
// - metrics: py::dict — словарь метрик
// OUTPUTS: void
// KEYWORDS: [DOMAIN(9): MetricsProcessing; CONCEPT(7): EventHandler]
// END_CONTRACT
void MatchNotifierPlugin::on_metric_update(py::dict metrics) {
    py::list matches;

    // Проверка наличия совпадений в метриках
    if (_check_for_matches_in_metrics(metrics, matches)) {
        // Обработка найденных совпадений
        int32_t iteration = 0;
        if (metrics.contains("iteration")) {
            iteration = metrics["iteration"].cast<int32_t>();
        }

        on_match_found(matches, iteration);
    }
}
// END_METHOD_ON_METRIC_UPDATE


// START_METHOD_ON_SHUTDOWN
// START_CONTRACT:
// PURPOSE: Завершение работы плагина
// OUTPUTS: void
// KEYWORDS: [CONCEPT(8): Cleanup; DOMAIN(7): Shutdown]
// END_CONTRACT
void MatchNotifierPlugin::on_shutdown() {
    _is_monitoring = false;

    // Экспорт истории перед завершением (опционально)
    // export_matches("matches_before_shutdown.json");

    std::stringstream ss;
    ss << "[MatchNotifierPlugin][ON_SHUTDOWN][StepComplete] Плагин уведомлений завершил работу. Всего совпадений: " << _total_matches;
    log_info(ss.str());
}
// END_METHOD_ON_SHUTDOWN


// START_METHOD_GET_UI_COMPONENTS
// START_CONTRACT:
// PURPOSE: Получение UI компонентов плагина
// OUTPUTS: py::object — UI компоненты
// KEYWORDS: [PATTERN(6): UI; CONCEPT(5): Getter]
// END_CONTRACT
py::object MatchNotifierPlugin::get_ui_components() {
    return _gradio_components;
}
// END_METHOD_GET_UI_COMPONENTS


// START_METHOD_RESET_NOTIFICATIONS
// START_CONTRACT:
// PURPOSE: Сброс всех уведомлений и истории
// OUTPUTS: void
// KEYWORDS: [CONCEPT(6): Reset; DOMAIN(7): Notification]
// END_CONTRACT
void MatchNotifierPlugin::reset_notifications() {
    _match_history.clear();
    _total_matches = 0;
    _last_notification_time = 0.0;

    std::stringstream ss;
    ss << "[MatchNotifierPlugin][RESET_NOTIFICATIONS][StepComplete] История уведомлений сброшена";
    log_info(ss.str());
}
// END_METHOD_RESET_NOTIFICATIONS


// START_METHOD_GET_MATCH_HISTORY
// START_CONTRACT:
// PURPOSE: Получение истории совпадений
// OUTPUTS: py::list — список совпадений
// KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): MatchHistory]
// END_CONTRACT
py::list MatchNotifierPlugin::get_match_history() const {
    py::list result;

    for (const auto& entry : _match_history) {
        result.append(entry.to_python());
    }

    return result;
}
// END_METHOD_GET_MATCH_HISTORY


// START_METHOD_GET_TOTAL_MATCHES
// START_CONTRACT:
// PURPOSE: Получение общего количества совпадений
// OUTPUTS: int32_t — количество совпадений
// KEYWORDS: [CONCEPT(5): Getter; DOMAIN(7): Counter]
// END_CONTRACT
int32_t MatchNotifierPlugin::get_total_matches() const {
    return _total_matches;
}
// END_METHOD_GET_TOTAL_MATCHES


// START_METHOD_GET_LATEST_MATCH
// START_CONTRACT:
// PURPOSE: Получение последнего совпадения
// OUTPUTS: py::object — последнее совпадение или None
// KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): MatchData]
// END_CONTRACT
py::object MatchNotifierPlugin::get_latest_match() const {
    if (_match_history.empty()) {
        return py::none();
    }

    return _match_history.back().to_python();
}
// END_METHOD_GET_LATEST_MATCH


// START_METHOD_SET_NOTIFICATION_SETTINGS
// START_CONTRACT:
// PURPOSE: Установка настроек уведомлений
// INPUTS:
// - settings: py::dict — словарь настроек
// OUTPUTS: void
// KEYWORDS: [CONCEPT(6): Setter; DOMAIN(8): Configuration]
// END_CONTRACT
void MatchNotifierPlugin::set_notification_settings(py::dict settings) {
    _notification_settings = NotificationSettings::from_python(settings);

    std::stringstream ss;
    ss << "[MatchNotifierPlugin][SET_NOTIFICATION_SETTINGS][StepComplete] Настройки обновлены: desktop="
       << _notification_settings.enable_desktop << ", sound=" << _notification_settings.enable_sound
       << ", log=" << _notification_settings.enable_log << ", ui=" << _notification_settings.enable_ui;
    log_info(ss.str());
}
// END_METHOD_SET_NOTIFICATION_SETTINGS


// START_METHOD_GET_NOTIFICATION_SETTINGS
// START_CONTRACT:
// PURPOSE: Получение настроек уведомлений
// OUTPUTS: py::dict — словарь настроек
// KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): Configuration]
// END_CONTRACT
py::dict MatchNotifierPlugin::get_notification_settings() const {
    return _notification_settings.to_python();
}
// END_METHOD_GET_NOTIFICATION_SETTINGS


// START_METHOD_REGISTER_MATCH_CALLBACK
// START_CONTRACT:
// PURPOSE: Регистрация callback функции
// INPUTS:
// - callback: py::object — Python функция
// OUTPUTS: void
// KEYWORDS: [CONCEPT(7): Callback; DOMAIN(8): EventHandler]
// END_CONTRACT
void MatchNotifierPlugin::register_match_callback(py::object callback) {
    if (py::isinstance<py::function>(callback)) {
        _match_callbacks.push_back(callback);

        std::stringstream ss;
        ss << "[MatchNotifierPlugin][REGISTER_MATCH_CALLBACK][StepComplete] Зарегистрирован callback";
        log_info(ss.str());
    } else {
        std::cerr << "[MatchNotifierPlugin][REGISTER_MATCH_CALLBACK][Warning] Переданный объект не является функцией" << std::endl;
    }
}
// END_METHOD_REGISTER_MATCH_CALLBACK


// START_METHOD_UNREGISTER_MATCH_CALLBACK
// START_CONTRACT:
// PURPOSE: Удаление callback функции
// INPUTS:
// - callback: py::object — Python функция
// OUTPUTS: void
// KEYWORDS: [CONCEPT(7): Callback; DOMAIN(8): EventHandler]
// END_CONTRACT
void MatchNotifierPlugin::unregister_match_callback(py::object callback) {
    auto it = std::find(_match_callbacks.begin(), _match_callbacks.end(), callback);
    if (it != _match_callbacks.end()) {
        _match_callbacks.erase(it);

        std::stringstream ss;
        ss << "[MatchNotifierPlugin][UNREGISTER_MATCH_CALLBACK][StepComplete] Удалён callback";
        log_info(ss.str());
    }
}
// END_METHOD_UNREGISTER_MATCH_CALLBACK


// START_METHOD_ON_MATCH_EVENT
// START_CONTRACT:
// PURPOSE: Обработчик события совпадения
// INPUTS:
// - match_data: py::dict — данные о совпадении
// OUTPUTS: void
// KEYWORDS: [DOMAIN(9): MatchHandler; CONCEPT(7): EventHandler]
// END_CONTRACT
void MatchNotifierPlugin::on_match_event(py::dict match_data) {
    // Создание MatchEntry из словаря
    MatchEntry entry = MatchEntry::from_python(match_data);

    // Добавление в историю
    _add_match(entry);

    // Вызов callbacks
    _invoke_callbacks(entry);

    // Отправка уведомлений
    if (_check_notification_cooldown()) {
        _send_notifications(entry);
        _update_last_notification_time();
    }
}
// END_METHOD_ON_MATCH_EVENT


// START_METHOD_GET_NOTIFICATION_SUMMARY
// START_CONTRACT:
// PURPOSE: Получение текстовой сводки
// OUTPUTS: std::string — сводка
// KEYWORDS: [CONCEPT(6): Summary; DOMAIN(7): Notification]
// END_CONTRACT
std::string MatchNotifierPlugin::get_notification_summary() const {
    std::stringstream ss;
    ss << "=== Сводка уведомлений ===\n";
    ss << "Всего совпадений: " << _total_matches << "\n";
    ss << "История совпадений: " << _match_history.size() << " / " << MAX_MATCH_HISTORY << "\n";
    ss << "Типы уведомлений:\n";
    ss << "  - Desktop: " << (_notification_settings.enable_desktop ? "ВКЛ" : "ВЫКЛ") << "\n";
    ss << "  - Sound: " << (_notification_settings.enable_sound ? "ВКЛ" : "ВЫКЛ") << "\n";
    ss << "  - Log: " << (_notification_settings.enable_log ? "ВКЛ" : "ВЫКЛ") << "\n";
    ss << "  - UI: " << (_notification_settings.enable_ui ? "ВКЛ" : "ВЫКЛ") << "\n";
    ss << "Кулдаун: " << _notification_settings.cooldown << " сек.\n";

    if (!_match_history.empty()) {
        ss << "\nПоследнее совпадение:\n";
        const auto& last = _match_history.back();
        ss << "  Адрес: " << last.address << "\n";
        ss << "  Баланс: " << last.balance << "\n";
        ss << "  Итерация: " << last.iteration << "\n";
        ss << "  Время: " << last.get_formatted_time() << "\n";
    }

    return ss.str();
}
// END_METHOD_GET_NOTIFICATION_SUMMARY


// START_METHOD_EXPORT_MATCHES
// START_CONTRACT:
// PURPOSE: Экспорт совпадений в файл
// INPUTS:
// - file_path: const std::string& — путь к файлу
// OUTPUTS: bool — успех/неудача
// KEYWORDS: [CONCEPT(6): Export; DOMAIN(8): FileIO]
// END_CONTRACT
bool MatchNotifierPlugin::export_matches(const std::string& file_path) const {
    try {
        std::ofstream file(file_path);
        if (!file.is_open()) {
            std::cerr << "[MatchNotifierPlugin][EXPORT_MATCHES][Error] Не удалось открыть файл: " << file_path << std::endl;
            return false;
        }

        file << "{\n";
        file << "  \"total_matches\": " << _total_matches << ",\n";
        file << "  \"match_count\": " << _match_history.size() << ",\n";
        file << "  \"matches\": [\n";

        for (size_t i = 0; i < _match_history.size(); ++i) {
            const auto& entry = _match_history[i];
            file << "    {\n";
            file << "      \"address\": \"" << entry.address << "\",\n";
            file << "      \"private_key\": \"" << entry.private_key << "\",\n";
            file << "      \"balance\": " << entry.balance << ",\n";
            file << "      \"iteration\": " << entry.iteration << ",\n";
            file << "      \"timestamp\": " << entry.timestamp << ",\n";
            file << "      \"severity\": \"" << entry.get_severity_string() << "\",\n";
            file << "      \"message\": \"" << entry.message << "\"\n";
            file << "    }";
            if (i < _match_history.size() - 1) {
                file << ",";
            }
            file << "\n";
        }

        file << "  ]\n";
        file << "}\n";

        file.close();

        std::stringstream ss;
        ss << "[MatchNotifierPlugin][EXPORT_MATCHES][StepComplete] Экспортировано " << _match_history.size() << " совпадений в файл " << file_path;
        std::cout << ss.str() << std::endl;

        return true;
    } catch (const std::exception& e) {
        std::cerr << "[MatchNotifierPlugin][EXPORT_MATCHES][ExceptionCaught] Ошибка при экспорте: " << e.what() << std::endl;
        return false;
    }
}
// END_METHOD_EXPORT_MATCHES


// START_METHOD_ON_START
// START_CONTRACT:
// PURPOSE: Обработчик запуска генератора
// INPUTS:
// - selected_list_path: const std::string& — путь к списку
// OUTPUTS: void
// KEYWORDS: [DOMAIN(8): EventHandler; CONCEPT(6): Startup]
// END_CONTRACT
void MatchNotifierPlugin::on_start(const std::string& selected_list_path) {
    _is_monitoring = true;

    std::stringstream ss;
    ss << "[MatchNotifierPlugin][ON_START][StepComplete] Плагин уведомлений запущен с списком: " << selected_list_path;
    log_info(ss.str());
}
// END_METHOD_ON_START


// START_METHOD_ON_MATCH_FOUND
// START_CONTRACT:
// PURPOSE: Обработчик обнаружения совпадений
// INPUTS:
// - matches: py::list — список совпадений
// - iteration: int — номер итерации
// OUTPUTS: void
// KEYWORDS: [DOMAIN(9): MatchHandler; CONCEPT(7): EventHandler]
// END_CONTRACT
void MatchNotifierPlugin::on_match_found(py::list matches, int iteration) {
    size_t match_count = py::len(matches);

    std::stringstream ss;
    ss << "[MatchNotifierPlugin][ON_MATCH_FOUND][Info] Найдено " << match_count << " совпадений на итерации " << iteration;
    log_info(ss.str());

    for (size_t i = 0; i < match_count; ++i) {
        py::dict match_dict = matches[i].cast<py::dict>();
        on_match_event(match_dict);
    }
}
// END_METHOD_ON_MATCH_FOUND


// START_METHOD_ON_FINISH
// START_CONTRACT:
// PURPOSE: Обработчик завершения генерации
// INPUTS:
// - final_metrics: py::dict — финальные метрики
// OUTPUTS: void
// KEYWORDS: [DOMAIN(8): Finalization; CONCEPT(7): EventHandler]
// END_CONTRACT
void MatchNotifierPlugin::on_finish(py::dict final_metrics) {
    _is_monitoring = false;

    std::stringstream ss;
    ss << "[MatchNotifierPlugin][ON_FINISH][StepComplete] Генерация завершена. Всего найдено совпадений: " << _total_matches;
    log_info(ss.str());
}
// END_METHOD_ON_FINISH


// START_METHOD_ON_RESET
// START_CONTRACT:
// PURPOSE: Обработчик сброса
// OUTPUTS: void
// KEYWORDS: [DOMAIN(7): ResetHandler; CONCEPT(7): EventHandler]
// END_CONTRACT
void MatchNotifierPlugin::on_reset() {
    reset_notifications();
    _is_monitoring = false;

    std::stringstream ss;
    ss << "[MatchNotifierPlugin][ON_RESET][StepComplete] Плагин уведомлений сброшен";
    log_info(ss.str());
}
// END_METHOD_ON_RESET


// START_METHOD_GET_NAME
// START_CONTRACT:
// PURPOSE: Получение имени плагина
// OUTPUTS: std::string — имя
// KEYWORDS: [CONCEPT(5): Getter]
// END_CONTRACT
std::string MatchNotifierPlugin::get_name() const {
    return "MatchNotifierPlugin";
}
// END_METHOD_GET_NAME


// START_METHOD_GET_PRIORITY
// START_CONTRACT:
// PURPOSE: Получения приоритета плагина
// OUTPUTS: int — приоритет
// KEYWORDS: [CONCEPT(5): Getter]
// END_CONTRACT
int MatchNotifierPlugin::get_priority() const {
    return 25;
}
// END_METHOD_GET_PRIORITY


// START_METHOD_HEALTH_CHECK
// START_CONTRACT:
// PURPOSE: Проверка работоспособности
// OUTPUTS: bool — статус
// KEYWORDS: [CONCEPT(7): HealthCheck; DOMAIN(6): Diagnostics]
// END_CONTRACT
bool MatchNotifierPlugin::health_check() const {
    return _notification_settings.is_any_enabled() || !_match_callbacks.empty();
}
// END_METHOD_HEALTH_CHECK


// START_METHOD_BUILD_UI_COMPONENTS
// START_CONTRACT:
// PURPOSE: Построение UI компонентов
// OUTPUTS: py::object — UI компоненты
// KEYWORDS: [DOMAIN(7): UI; CONCEPT(6): Builder]
// END_CONTRACT
py::object MatchNotifierPlugin::_build_ui_components() {
    // Создание простого HTML для отображения уведомлений
    py::dict components;

    // Основной контейнер уведомлений
    std::string html = _get_empty_notification_html();
    components["notification_area"] = py::str(html);

    // Сводка уведомлений
    std::string summary = get_notification_summary();
    components["summary"] = py::str(summary);

    // Статистика
    py::dict stats;
    stats["total_matches"] = _total_matches;
    stats["history_size"] = static_cast<int32_t>(_match_history.size());
    components["stats"] = stats;

    return components;
}
// END_METHOD_BUILD_UI_COMPONENTS


// START_METHOD_ADD_MATCH
// START_CONTRACT:
// PURPOSE: Добавление совпадения в историю
// INPUTS:
// - match_data: const MatchEntry& — данные о совпадении
// OUTPUTS: void
// KEYWORDS: [CONCEPT(6): Storage; DOMAIN(8): MatchHistory]
// END_CONTRACT
void MatchNotifierPlugin::_add_match(const MatchEntry& match_data) {
    // Добавление в начало deque
    _match_history.push_front(match_data);

    // Ограничение размера истории
    while (_match_history.size() > MAX_MATCH_HISTORY) {
        _match_history.pop_back();
    }

    // Увеличение счётчика
    _total_matches++;

    std::stringstream ss;
    ss << "[MatchNotifierPlugin][ADD_MATCH][StepComplete] Добавлено совпадение. Всего: " << _total_matches;
    log_debug(ss.str());
}
// END_METHOD_ADD_MATCH


// START_METHOD_SEND_NOTIFICATIONS
// START_CONTRACT:
// PURPOSE: Отправка уведомлений
// INPUTS:
// - match_data: const MatchEntry& — данные о совпадении
// OUTPUTS: void
// KEYWORDS: [DOMAIN(9): Notification; CONCEPT(7): Dispatcher]
// END_CONTRACT
void MatchNotifierPlugin::_send_notifications(const MatchEntry& match_data) {
    // Desktop уведомление
    if (_notification_settings.enable_desktop) {
        std::stringstream title;
        title << "Совпадение найдено! (#" << _total_matches << ")";

        std::stringstream message;
        message << "Адрес: " << match_data.address << "\n";
        message << "Баланс: " << match_data.balance << " BTC\n";
        message << "Итерация: " << match_data.iteration;

        _send_desktop_notification(title.str(), message.str());
    }

    // Логирование
    if (_notification_settings.enable_log) {
        _log_notification(match_data);
    }

    // UI уведомление (через app callback)
    if (_notification_settings.enable_ui && !py::isinstance<py::none>(_app)) {
        try {
            if (py::hasattr(_app, "notify")) {
                _app.attr("notify")(match_data.to_python());
            }
        } catch (const py::error_already_set& e) {
            std::cerr << "[MatchNotifierPlugin][SEND_NOTIFICATIONS][ExceptionCaught] Ошибка UI уведомления: " << e.what() << std::endl;
        }
    }
}
// END_METHOD_SEND_NOTIFICATIONS


// START_METHOD_SEND_DESKTOP_NOTIFICATION
// START_CONTRACT:
// PURPOSE: Отправка desktop уведомления
// INPUTS:
// - title: const std::string& — заголовок
// - message: const std::string& — сообщение
// OUTPUTS: void
// KEYWORDS: [DOMAIN(8): DesktopNotify; CONCEPT(7): ExternalCall]
// END_CONTRACT
void MatchNotifierPlugin::_send_desktop_notification(const std::string& title, const std::string& message) {
    // Пробуем использовать notify-send
    std::string command = "notify-send \"" + title + "\" \"" + message + "\"";

    int result = std::system(command.c_str());

    if (result != 0) {
        // Пробуем dunstify (Dunst - демон уведомлений)
        command = "dunstify \"" + title + "\" \"" + message + "\"";
        result = std::system(command.c_str());

        if (result != 0) {
            std::cerr << "[MatchNotifierPlugin][SEND_DESKTOP_NOTIFICATION][Warning] Не удалось отправить desktop уведомление (notify-send и dunstify недоступны)" << std::endl;
        }
    }
}
// END_METHOD_SEND_DESKTOP_NOTIFICATION


// START_METHOD_DETERMINE_SEVERITY
// START_CONTRACT:
// PURPOSE: Определение серьёзности
// INPUTS:
// - iteration: int32_t — итерация
// - balance: double — баланс
// OUTPUTS: MatchSeverity
// KEYWORDS: [CONCEPT(7): Severity; DOMAIN(7): DecisionTree]
// END_CONTRACT
MatchSeverity MatchNotifierPlugin::_determine_severity(int32_t iteration, double balance) const {
    if (balance >= 100.0) {
        return MatchSeverity::CRITICAL;
    } else if (balance >= 10.0) {
        return MatchSeverity::WARNING;
    } else if (balance >= 1.0) {
        return MatchSeverity::SUCCESS;
    } else {
        return MatchSeverity::INFO;
    }
}
// END_METHOD_DETERMINE_SEVERITY


// START_METHOD_CHECK_NOTIFICATION_COOLDOWN
// START_CONTRACT:
// PURPOSE: Проверка кулдауна
// OUTPUTS: bool — можно ли отправить
// KEYWORDS: [CONCEPT(6): Cooldown; DOMAIN(8): RateLimit]
// END_CONTRACT
bool MatchNotifierPlugin::_check_notification_cooldown() const {
    double current_time = _get_current_time();
    return (current_time - _last_notification_time) >= _notification_settings.cooldown;
}
// END_METHOD_CHECK_NOTIFICATION_COOLDOWN


// START_METHOD_UPDATE_LAST_NOTIFICATION_TIME
// START_CONTRACT:
// PURPOSE: Обновление времени уведомления
// OUTPUTS: void
// KEYWORDS: [CONCEPT(6): Timestamp]
// END_CONTRACT
void MatchNotifierPlugin::_update_last_notification_time() {
    _last_notification_time = _get_current_time();
}
// END_METHOD_UPDATE_LAST_NOTIFICATION_TIME


// START_METHOD_INVOKE_CALLBACKS
// START_CONTRACT:
// PURPOSE: Вызов callbacks
// INPUTS:
// - match_data: const MatchEntry& — данные
// OUTPUTS: void
// KEYWORDS: [CONCEPT(7): Callback; DOMAIN(8): EventHandler]
// END_CONTRACT
void MatchNotifierPlugin::_invoke_callbacks(const MatchEntry& match_data) {
    for (const auto& callback : _match_callbacks) {
        try {
            callback(match_data.to_python());
        } catch (const py::error_already_set& e) {
            std::cerr << "[MatchNotifierPlugin][INVOKE_CALLBACKS][ExceptionCaught] Ошибка при вызове callback: " << e.what() << std::endl;
        }
    }
}
// END_METHOD_INVOKE_CALLBACKS


// START_METHOD_GET_EMPTY_NOTIFICATION_HTML
// START_CONTRACT:
// PURPOSE: Получение пустого HTML
// OUTPUTS: std::string — HTML
// KEYWORDS: [PATTERN(6): HTML; DOMAIN(7): UI]
// END_CONTRACT
std::string MatchNotifierPlugin::_get_empty_notification_html() const {
    return R"(
<div style="padding: 20px; background: #f5f5f5; border-radius: 8px; text-align: center;">
    <h3 style="color: #666;">📭 Нет уведомлений</h3>
    <p style="color: #999;">Совпадения будут отображаться здесь</p>
</div>
)";
}
// END_METHOD_GET_EMPTY_NOTIFICATION_HTML


// START_METHOD_LOG_NOTIFICATION
// START_CONTRACT:
// PURPOSE: Логирование уведомления
// INPUTS:
// - match_data: const MatchEntry& — данные
// OUTPUTS: void
// KEYWORDS: [CONCEPT(6): Logging; DOMAIN(7): FileIO]
// END_CONTRACT
void MatchNotifierPlugin::_log_notification(const MatchEntry& match_data) const {
    std::stringstream ss;
    ss << "[NOTIFICATION] " << match_data.get_formatted_time()
       << " | Address: " << match_data.address
       << " | Balance: " << match_data.balance
       << " BTC | Iteration: " << match_data.iteration
       << " | Severity: " << match_data.get_severity_string();

    std::cout << ss.str() << std::endl;
}
// END_METHOD_LOG_NOTIFICATION


// START_METHOD_GET_CURRENT_TIME
// START_CONTRACT:
// PURPOSE: Получение текущего времени
// OUTPUTS: double — Unix timestamp
// KEYWORDS: [CONCEPT(6): Timestamp]
// END_CONTRACT
double MatchNotifierPlugin::_get_current_time() const {
    auto now = std::chrono::system_clock::now();
    auto duration = now.time_since_epoch();
    return std::chrono::duration<double>(duration).count();
}
// END_METHOD_GET_CURRENT_TIME


// START_METHOD_CHECK_FOR_MATCHES_IN_METRICS
// START_CONTRACT:
// PURPOSE: Проверка метрик на наличие совпадений
// INPUTS:
// - metrics: py::dict — метрики
// - out_matches: py::list& — выходной список совпадений
// OUTPUTS: bool — есть ли совпадения
// KEYWORDS: [CONCEPT(7): Metrics; DOMAIN(8): MatchDetection]
// END_CONTRACT
bool MatchNotifierPlugin::_check_for_matches_in_metrics(py::dict metrics, py::list& out_matches) {
    // Проверяем, есть ли ключ matches в метриках
    if (metrics.contains("matches")) {
        try {
            py::object matches_obj = metrics["matches"];
            if (py::isinstance<py::list>(matches_obj)) {
                out_matches = matches_obj.cast<py::list>();
                return py::len(out_matches) > 0;
            }
        } catch (const py::error_already_set& e) {
            std::cerr << "[MatchNotifierPlugin][CHECK_FOR_MATCHES][ExceptionCaught] Ошибка при извлечении совпадений: " << e.what() << std::endl;
        }
    }

    return false;
}
// END_METHOD_CHECK_FOR_MATCHES_IN_METRICS


// START_METHOD_GENERATE_MOCK_MATCH
// START_CONTRACT:
// PURPOSE: Генерация mock данных для тестирования
// INPUTS:
// - iteration: int32_t — номер итерации
// OUTPUTS: MatchEntry — сгенерированные данные
// KEYWORDS: [PATTERN(6): Mock; DOMAIN(7): Testing]
// END_CONTRACT
MatchEntry MatchNotifierPlugin::_generate_mock_match(int32_t iteration) {
    // Генерация случайного адреса (mock)
    std::string mock_address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa";  // Genesis block address
    std::string mock_private_key = "KwDiBf89QgGbjEhKnhXJuH7LrciVrZi3qYjgd9M7rFU73sVHnoWn";  // Mock private key

    // Случайный баланс для демонстрации
    double mock_balance = (rand() % 1000) / 100.0;

    // Определение серьёзности
    MatchSeverity severity = _determine_severity(iteration, mock_balance);

    return MatchEntry(mock_address, mock_private_key, mock_balance, iteration, severity);
}
// END_METHOD_GENERATE_MOCK_MATCH

// END_MATCH_NOTIFIER_PLUGIN_IMPLEMENTATION
