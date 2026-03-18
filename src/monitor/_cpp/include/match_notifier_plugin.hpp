// FILE: src/monitor/_cpp/include/match_notifier_plugin.hpp
// VERSION: 2.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Заголовочный файл плагина уведомлений о совпадениях на C++.
// Обеспечивает real-time уведомления при обнаружении совпадений с адресами из списка.
// SCOPE: Классы плагина, структуры данных, интерфейсы уведомлений
// INPUT: Заголовочный файл plugin_base.hpp
// OUTPUT: Класс MatchNotifierPlugin, структура MatchEntry, перечисления
// KEYWORDS: [DOMAIN(9): Notifications; DOMAIN(8): PluginSystem; CONCEPT(8): EventDriven; TECH(6): DesktopNotify]
// LINKS: [INHERITS_FROM(9): plugin_base.hpp; USES_API(7): pybind11]
// END_MODULE_CONTRACT

#ifndef WALLET_MONITOR_MATCH_NOTIFIER_PLUGIN_HPP
#define WALLET_MONITOR_MATCH_NOTIFIER_PLUGIN_HPP

#include <string>
#include <vector>
#include <memory>
#include <algorithm>
#include <iostream>
#include <sstream>
#include <functional>
#include <deque>
#include <map>
#include <chrono>
#include <thread>
#include <atomic>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/chrono.h>
#include <pybind11/functional.h>

// Включение заголовочного файла базового класса
#include "plugin_base.hpp"

// START_ENUM_MATCH_SEVERITY
// START_CONTRACT:
// PURPOSE: Перечисление уровней серьёзности совпадений
// ATTRIBUTES:
// - INFO: Информационное совпадение
// - SUCCESS: Успешное совпадение (баланс найден)
// - WARNING: Предупреждение (аномальная активность)
// - CRITICAL: Критическое совпадение (высокий баланс)
// KEYWORDS: [PATTERN(6): Enum; DOMAIN(7): Severity; CONCEPT(5): Priority]
// END_CONTRACT

enum class MatchSeverity {
    INFO = 0,
    SUCCESS = 1,
    WARNING = 2,
    CRITICAL = 3
};
// END_ENUM_MATCH_SEVERITY


// START_ENUM_NOTIFICATION_TYPE
// START_CONTRACT:
// PURPOSE: Перечисление типов уведомлений
// ATTRIBUTES:
// - DESKTOP: Уведомление на рабочий стол
// - SOUND: Звуковое уведомление
// - LOG: Запись в лог файл
// - UI: Уведомление в пользовательском интерфейсе
// KEYWORDS: [PATTERN(6): Enum; DOMAIN(8): Notification; CONCEPT(5): Types]
// END_CONTRACT

enum class NotificationType {
    DESKTOP = 0,
    SOUND = 1,
    LOG = 2,
    UI = 3
};
// END_ENUM_NOTIFICATION_TYPE


// START_STRUCT_MATCH_ENTRY
// START_CONTRACT:
// PURPOSE: Структура для хранения данных о найденном совпадении
// ATTRIBUTES:
// - address: std::string — найденный адрес
// - private_key: std::string — приватный ключ (если доступен)
// - balance: double — баланс адреса
// - iteration: int32_t — номер итерации, на которой найдено совпадение
// - timestamp: double — время обнаружения (Unix timestamp)
// - severity: MatchSeverity — уровень серьёзности
// - message: std::string — сообщение о совпадении
// KEYWORDS: [PATTERN(7): DataClass; DOMAIN(9): MatchData; CONCEPT(6): Storage]
// END_CONTRACT

struct MatchEntry {
    std::string address;
    std::string private_key;
    double balance;
    int32_t iteration;
    double timestamp;
    MatchSeverity severity;
    std::string message;

    // Конструктор по умолчанию
    MatchEntry();

    // Конструктор с параметрами
    MatchEntry(
        const std::string& address,
        const std::string& private_key,
        double balance,
        int32_t iteration,
        MatchSeverity severity = MatchSeverity::INFO
    );

    // Конструктор для Python совместимости
    static MatchEntry from_python(py::object obj);

    // Конвертация в Python словарь
    py::dict to_python() const;

    // Получение строкового представления серьёзности
    std::string get_severity_string() const;

    // Получение времени в читаемом формате
    std::string get_formatted_time() const;
};
// END_STRUCT_MATCH_ENTRY


// START_STRUCT_NOTIFICATION_SETTINGS
// START_CONTRACT:
// PURPOSE: Структура настроек уведомлений
// ATTRIBUTES:
// - enable_desktop: bool — включены ли desktop уведомления
// - enable_sound: bool — включены ли звуковые уведомления
// - enable_log: bool — включена ли запись в лог
// - enable_ui: bool — включены ли UI уведомления
// - cooldown: double — кулдаун между уведомлениями в секундах
// KEYWORDS: [PATTERN(7): DataClass; DOMAIN(8): Notification; CONCEPT(6): Configuration]
// END_CONTRACT

struct NotificationSettings {
    bool enable_desktop;
    bool enable_sound;
    bool enable_log;
    bool enable_ui;
    double cooldown;

    // Конструктор по умолчанию
    NotificationSettings();

    // Конструктор с параметрами
    NotificationSettings(
        bool desktop,
        bool sound,
        bool log,
        bool ui,
        double cooldown = 5.0
    );

    // Конструктор из Python словаря
    static NotificationSettings from_python(py::dict dict);

    // Конвертация в Python словарь
    py::dict to_python() const;

    // Проверка, включены ли вообще уведомления
    bool is_any_enabled() const;
};
// END_STRUCT_NOTIFICATION_SETTINGS


// START_CLASS_MATCH_NOTIFIER_PLUGIN
// START_CONTRACT:
// PURPOSE: Класс плагина уведомлений о совпадениях. Обеспечивает real-time уведомления при обнаружении совпадений с адресами из списка в процессе генерации кошельков Bitcoin.
// ATTRIBUTES:
// - VERSION: std::string — версия плагина
// - AUTHOR: std::string — автор плагина
// - DESCRIPTION: std::string — описание плагина
// - _match_history: std::deque<MatchEntry> — история совпадений (maxlen=50)
// - _total_matches: int32_t — общее количество совпадений
// - _notification_settings: NotificationSettings — настройки уведомлений
// - _match_callbacks: std::vector<py::object> — callbacks для совпадений
// - _last_notification_time: double — время последнего уведомления
// - _notification_cooldown: double — кулдаун уведомлений (5.0 сек)
// - _is_monitoring: bool — флаг мониторинга
// - _gradio_components: py::object — UI компоненты
// METHODS:
// - initialize: Инициализация плагина и регистрация UI
// - on_metric_update: Обработка обновления метрик
// - on_shutdown: Завершение работы плагина
// - get_ui_components: Получение UI компонентов
// - reset_notifications: Сброс уведомлений
// - get_match_history: Получение истории совпадений
// - get_total_matches: Получение общего количества совпадений
// - get_latest_match: Получение последнего совпадения
// - set_notification_settings: Установка настроек уведомлений
// - get_notification_settings: Получение настроек уведомлений
// - register_match_callback: Регистрация callback
// - unregister_match_callback: Удаление callback
// - on_match_event: Обработчик события совпадения
// - get_notification_summary: Получение текстовой сводки
// - export_matches: Экспорт совпадений в файл
// KEYWORDS: [PATTERN(7): PluginClass; DOMAIN(9): NotificationSystem; TECH(6): DesktopNotify]
// LINKS: [INHERITS_FROM(9): BaseMonitorPlugin]
// END_CONTRACT

class MatchNotifierPlugin : public BaseMonitorPlugin {
public:
    // Статические константы (аналог class attributes в Python)
    static const std::string VERSION;
    static const std::string AUTHOR;
    static const std::string DESCRIPTION;
    static const int32_t MAX_MATCH_HISTORY;
    static const double NOTIFICATION_COOLDOWN;

    // START_CONSTRUCTOR_MATCH_NOTIFIER_PLUGIN
    // START_CONTRACT:
    // PURPOSE: Конструктор плагина уведомлений о совпадениях
    // OUTPUTS: Инициализированный объект плагина
    // SIDE_EFFECTS: Создает внутреннее состояние плагина; инициализирует историю совпадений; настраивает параметры уведомлений
    // KEYWORDS: [CONCEPT(5): Initialization; DOMAIN(7): PluginSetup]
    // END_CONTRACT
    MatchNotifierPlugin();

    // Виртуальный деструктор
    virtual ~MatchNotifierPlugin() override;

    // START_METHOD_INITIALIZE
    // START_CONTRACT:
    // PURPOSE: Инициализация плагина и регистрация UI компонентов в главном приложении
    // INPUTS:
    // - app: py::object — ссылка на главное приложение мониторинга
    // OUTPUTS: void
    // SIDE_EFFECTS: Регистрирует UI компоненты плагина в приложении; инициализирует подписку на метрики
    // KEYWORDS: [DOMAIN(8): PluginSetup; CONCEPT(6): Registration]
    // TEST_CONDITIONS_SUCCESS_CRITERIA: Плагин должен зарегистрировать свои компоненты в приложении
    // END_CONTRACT
    virtual void initialize(py::object app) override;

    // START_METHOD_ON_METRIC_UPDATE
    // START_CONTRACT:
    // PURPOSE: Обработка обновления метрик от генератора. Проверяет наличие новых совпадений и отправляет уведомления.
    // INPUTS:
    // - metrics: py::dict — словарь текущих метрик
    // OUTPUTS: void
    // SIDE_EFFECTS: Обновляет внутреннее состояние; проверяет наличие совпадений; отправляет уведомления
    // KEYWORDS: [DOMAIN(9): MetricsProcessing; CONCEPT(7): EventHandler]
    // END_CONTRACT
    virtual void on_metric_update(py::dict metrics) override;

    // START_METHOD_ON_SHUTDOWN
    // START_CONTRACT:
    // PURPOSE: Действия при завершении работы мониторинга
    // INPUTS: Нет
    // OUTPUTS: void
    // SIDE_EFFECTS: Освобождение ресурсов плагина; сохранение состояния (если необходимо); логирование завершения работы
    // KEYWORDS: [CONCEPT(8): Cleanup; DOMAIN(7): Shutdown]
    // END_CONTRACT
    virtual void on_shutdown() override;

    // START_METHOD_GET_UI_COMPONENTS
    // START_CONTRACT:
    // PURPOSE: Получение UI компонентов плагина для отображения в Gradio интерфейсе
    // OUTPUTS: py::object — словарь UI компонентов или None
    // KEYWORDS: [PATTERN(6): UI; CONCEPT(5): Getter]
    // END_CONTRACT
    virtual py::object get_ui_components() override;

    // START_METHOD_RESET_NOTIFICATIONS
    // START_CONTRACT:
    // PURPOSE: Сброс всех уведомлений и истории совпадений
    // OUTPUTS: void
    // SIDE_EFFECTS: Очищает историю совпадений; сбрасывает счётчик; сбрасывает время последнего уведомления
    // KEYWORDS: [CONCEPT(6): Reset; DOMAIN(7): Notification]
    // END_CONTRACT
    virtual void reset_notifications();

    // START_METHOD_GET_MATCH_HISTORY
    // START_CONTRACT:
    // PURPOSE: Получение истории совпадений
    // OUTPUTS: py::list — список всех совпадений
    // KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): MatchHistory]
    // END_CONTRACT
    virtual py::list get_match_history() const;

    // START_METHOD_GET_TOTAL_MATCHES
    // START_CONTRACT:
    // PURPOSE: Получение общего количества найденных совпадений
    // OUTPUTS: int32_t — общее количество совпадений
    // KEYWORDS: [CONCEPT(5): Getter; DOMAIN(7): Counter]
    // END_CONTRACT
    virtual int32_t get_total_matches() const;

    // START_METHOD_GET_LATEST_MATCH
    // START_CONTRACT:
    // PURPOSE: Получение последнего найденного совпадения
    // OUTPUTS: py::object — последнее совпадение или None
    // KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): MatchData]
    // END_CONTRACT
    virtual py::object get_latest_match() const;

    // START_METHOD_SET_NOTIFICATION_SETTINGS
    // START_CONTRACT:
    // PURPOSE: Установка настроек уведомлений
    // INPUTS:
    // - settings: py::dict — словарь настроек уведомлений
    // OUTPUTS: void
    // SIDE_EFFECTS: Обновляет настройки уведомлений плагина
    // KEYWORDS: [CONCEPT(6): Setter; DOMAIN(8): Configuration]
    // END_CONTRACT
    virtual void set_notification_settings(py::dict settings);

    // START_METHOD_GET_NOTIFICATION_SETTINGS
    // START_CONTRACT:
    // PURPOSE: Получение текущих настроек уведомлений
    // OUTPUTS: py::dict — словарь настроек уведомлений
    // KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): Configuration]
    // END_CONTRACT
    virtual py::dict get_notification_settings() const;

    // START_METHOD_REGISTER_MATCH_CALLBACK
    // START_CONTRACT:
    // PURPOSE: Регистрация callback функции для обработки совпадений
    // INPUTS:
    // - callback: py::object — Python функция callback
    // OUTPUTS: void
    // SIDE_EFFECTS: Добавляет callback в список обработчиков
    // KEYWORDS: [CONCEPT(7): Callback; DOMAIN(8): EventHandler]
    // END_CONTRACT
    virtual void register_match_callback(py::object callback);

    // START_METHOD_UNREGISTER_MATCH_CALLBACK
    // START_CONTRACT:
    // PURPOSE: Удаление callback функции из списка обработчиков
    // INPUTS:
    // - callback: py::object — Python функция callback для удаления
    // OUTPUTS: void
    // SIDE_EFFECTS: Удаляет callback из списка обработчиков
    // KEYWORDS: [CONCEPT(7): Callback; DOMAIN(8): EventHandler]
    // END_CONTRACT
    virtual void unregister_match_callback(py::object callback);

    // START_METHOD_ON_MATCH_EVENT
    // START_CONTRACT:
    // PURPOSE: Обработчик события совпадения. Вызывается при обнаружении нового совпадения.
    // INPUTS:
    // - match_data: py::dict — данные о совпадении
    // OUTPUTS: void
    // SIDE_EFFECTS: Добавляет совпадение в историю; вызывает callbacks; отправляет уведомления
    // KEYWORDS: [DOMAIN(9): MatchHandler; CONCEPT(7): EventHandler]
    // END_CONTRACT
    virtual void on_match_event(py::dict match_data);

    // START_METHOD_GET_NOTIFICATION_SUMMARY
    // START_CONTRACT:
    // PURPOSE: Получение текстовой сводки о всех уведомлениях
    // OUTPUTS: std::string — текстовая сводка
    // KEYWORDS: [CONCEPT(6): Summary; DOMAIN(7): Notification]
    // END_CONTRACT
    virtual std::string get_notification_summary() const;

    // START_METHOD_EXPORT_MATCHES
    // START_CONTRACT:
    // PURPOSE: Экспорт истории совпадений в файл
    // INPUTS:
    // - file_path: const std::string& — путь к файлу для экспорта
    // OUTPUTS: bool — true если экспорт успешен, false в противном случае
    // KEYWORDS: [CONCEPT(6): Export; DOMAIN(8): FileIO]
    // END_CONTRACT
    virtual bool export_matches(const std::string& file_path) const;

    // START_METHOD_ON_START
    // START_CONTRACT:
    // PURPOSE: Обработчик запуска генератора кошельков
    // INPUTS:
    // - selected_list_path: const std::string& — путь к выбранному списку адресов
    // OUTPUTS: void
    // SIDE_EFFECTS: Сбрасывает историю при новом запуске
    // KEYWORDS: [DOMAIN(8): EventHandler; CONCEPT(6): Startup]
    // END_CONTRACT
    virtual void on_start(const std::string& selected_list_path) override;

    // START_METHOD_ON_MATCH_FOUND
    // START_CONTRACT:
    // PURPOSE: Обработчик обнаружения совпадений
    // INPUTS:
    // - matches: py::list — список найденных совпадений
    // - iteration: int — номер итерации, на которой найдены совпадения
    // OUTPUTS: void
    // SIDE_EFFECTS: Обрабатывает найденные совпадения; отправляет уведомления
    // KEYWORDS: [DOMAIN(9): MatchHandler; CONCEPT(7): EventHandler]
    // END_CONTRACT
    virtual void on_match_found(py::list matches, int iteration) override;

    // START_METHOD_ON_FINISH
    // START_CONTRACT:
    // PURPOSE: Обработчик завершения генерации кошельков
    // INPUTS:
    // - final_metrics: py::dict — финальные метрики генерации
    // OUTPUTS: void
    // SIDE_EFFECTS: Генерирует итоговую статистику; обновляет UI
    // KEYWORDS: [DOMAIN(8): Finalization; CONCEPT(7): EventHandler]
    // END_CONTRACT
    virtual void on_finish(py::dict final_metrics) override;

    // START_METHOD_ON_RESET
    // START_CONTRACT:
    // PURPOSE: Обработчик сброса генератора. Вызывается при нажатии кнопки Reset.
    // INPUTS: Нет
    // OUTPUTS: void
    // SIDE_EFFECTS: Сбрасывает внутреннее состояние плагина; очищает кэши
    // KEYWORDS: [DOMAIN(7): ResetHandler; CONCEPT(7): EventHandler]
    // END_CONTRACT
    virtual void on_reset() override;

    // START_METHOD_GET_NAME
    // START_CONTRACT:
    // PURPOSE: Получение имени плагина
    // OUTPUTS: std::string — имя плагина
    // KEYWORDS: [CONCEPT(5): Getter]
    // END_CONTRACT
    virtual std::string get_name() const override;

    // START_METHOD_GET_PRIORITY
    // START_CONTRACT:
    // PURPOSE: Получение приоритета плагина
    // OUTPUTS: int — приоритет плагина
    // KEYWORDS: [CONCEPT(5): Getter]
    // END_CONTRACT
    virtual int get_priority() const override;

    // START_METHOD_HEALTH_CHECK
    // START_CONTRACT:
    // PURPOSE: Проверка работоспособности плагина
    // OUTPUTS: bool — true если плагин работает корректно
    // KEYWORDS: [CONCEPT(7): HealthCheck; DOMAIN(6): Diagnostics]
    // END_CONTRACT
    virtual bool health_check() const override;

protected:
    // История совпадений (аналог Deque с maxlen=50)
    std::deque<MatchEntry> _match_history;

    // Общее количество совпадений
    int32_t _total_matches;

    // Настройки уведомлений
    NotificationSettings _notification_settings;

    // Callbacks для совпадений
    std::vector<py::object> _match_callbacks;

    // Время последнего уведомления
    double _last_notification_time;

    // Кулдаун уведомлений
    double _notification_cooldown;

    // Флаг мониторинга
    std::atomic<bool> _is_monitoring;

    // UI компоненты (Gradio)
    py::object _gradio_components;

    // Внутренние методы

    // START_METHOD_BUILD_UI_COMPONENTS
    // START_CONTRACT:
    // PURPOSE: Построение UI компонентов плагина для Gradio интерфейса
    // OUTPUTS: py::object — словарь UI компонентов
    // KEYWORDS: [DOMAIN(7): UI; CONCEPT(6): Builder]
    // END_CONTRACT
    py::object _build_ui_components();

    // START_METHOD_ADD_MATCH
    // START_CONTRACT:
    // PURPOSE: Добавление совпадения в историю
    // INPUTS:
    // - match_data: const MatchEntry& — данные о совпадении
    // OUTPUTS: void
    // SIDE_EFFECTS: Добавляет совпадение в историю; обновляет счётчик
    // KEYWORDS: [CONCEPT(6): Storage; DOMAIN(8): MatchHistory]
    // END_CONTRACT
    void _add_match(const MatchEntry& match_data);

    // START_METHOD_SEND_NOTIFICATIONS
    // START_CONTRACT:
    // PURPOSE: Отправка уведомлений о совпадении
    // INPUTS:
    // - match_data: const MatchEntry& — данные о совпадении
    // OUTPUTS: void
    // SIDE_EFFECTS: Отправляет уведомления всех включённых типов
    // KEYWORDS: [DOMAIN(9): Notification; CONCEPT(7): Dispatcher]
    // END_CONTRACT
    void _send_notifications(const MatchEntry& match_data);

    // START_METHOD_SEND_DESKTOP_NOTIFICATION
    // START_CONTRACT:
    // PURPOSE: Отправка desktop уведомления через notify-send или dunstify
    // INPUTS:
    // - title: const std::string& — заголовок уведомления
    // - message: const std::string& — текст уведомления
    // OUTPUTS: void
    // SIDE_EFFECTS: Запускает внешний процесс для отправки уведомления
    // KEYWORDS: [DOMAIN(8): DesktopNotify; CONCEPT(7): ExternalCall]
    // END_CONTRACT
    void _send_desktop_notification(const std::string& title, const std::string& message);

    // START_METHOD_DETERMINE_SEVERITY
    // START_CONTRACT:
    // PURPOSE: Определение уровня серьёзности совпадения на основе итерации и баланса
    // INPUTS:
    // - iteration: int32_t — номер итерации
    // - balance: double — баланс адреса
    // OUTPUTS: MatchSeverity — определённый уровень серьёзности
    // KEYWORDS: [CONCEPT(7): Severity; DOMAIN(7): DecisionTree]
    // END_CONTRACT
    MatchSeverity _determine_severity(int32_t iteration, double balance) const;

    // START_METHOD_CHECK_NOTIFICATION_COOLDOWN
    // START_CONTRACT:
    // PURPOSE: Проверка, можно ли отправить уведомление (кулдаун)
    // OUTPUTS: bool — true если уведомление можно отправить
    // KEYWORDS: [CONCEPT(6): Cooldown; DOMAIN(8): RateLimit]
    // END_CONTRACT
    bool _check_notification_cooldown() const;

    // START_METHOD_UPDATE_LAST_NOTIFICATION_TIME
    // START_CONTRACT:
    // PURPOSE: Обновление времени последнего уведомления
    // OUTPUTS: void
    // KEYWORDS: [CONCEPT(6): Timestamp]
    // END_CONTRACT
    void _update_last_notification_time();

    // START_METHOD_INVOKE_CALLBACKS
    // START_CONTRACT:
    // PURPOSE: Вызов всех зарегистрированных callbacks с данными совпадения
    // INPUTS:
    // - match_data: const MatchEntry& — данные о совпадении
    // OUTPUTS: void
    // KEYWORDS: [CONCEPT(7): Callback; DOMAIN(8): EventHandler]
    // END_CONTRACT
    void _invoke_callbacks(const MatchEntry& match_data);

    // START_METHOD_GET_EMPTY_NOTIFICATION_HTML
    // START_CONTRACT:
    // PURPOSE: Получение HTML для пустого состояния (нет уведомлений)
    // OUTPUTS: std::string — HTML код
    // KEYWORDS: [PATTERN(6): HTML; DOMAIN(7): UI]
    // END_CONTRACT
    std::string _get_empty_notification_html() const;

    // START_METHOD_LOG_NOTIFICATION
    // START_CONTRACT:
    // PURPOSE: Логирование уведомления в файл
    // INPUTS:
    // - match_data: const MatchEntry& — данные о совпадении
    // OUTPUTS: void
    // KEYWORDS: [CONCEPT(6): Logging; DOMAIN(7): FileIO]
    // END_CONTRACT
    void _log_notification(const MatchEntry& match_data) const;

    // Метод для получения текущего времени
    double _get_current_time() const;

    // Метод для проверки наличия совпадений в метриках (mock/реальные данные)
    bool _check_for_matches_in_metrics(py::dict metrics, py::list& out_matches);

    // Метод для генерации mock данных (для тестирования)
    MatchEntry _generate_mock_match(int32_t iteration);
};
// END_CLASS_MATCH_NOTIFIER_PLUGIN


// START_CLASS_MATCH_NOTIFIER_PLUGIN_TRAMPOLINE
// START_CONTRACT:
// PURPOSE: Trampoline класс для обеспечения возможности наследования от C++ класса MatchNotifierPlugin в Python.
// Позволяет переопределять методы в Python и вызывать их из C++.
// KEYWORDS: [PATTERN(9): TrampolineClass; DOMAIN(9): Pybind11; TECH(7): PythonBindings]
// END_CONTRACT

class MatchNotifierPluginTrampoline : public MatchNotifierPlugin {
public:
    // Конструктор trampoline
    using MatchNotifierPlugin::MatchNotifierPlugin;

    // START_METHOD_INITIALIZE_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода initialize - позволяет переопределить в Python
    // INPUTS:
    // - app: py::object — ссылка на главное приложение мониторинга
    // OUTPUTS: void
    // END_CONTRACT
    void initialize(py::object app) override {
        PYBIND11_OVERRIDE(
            void,
            MatchNotifierPlugin,
            initialize,
            app
        );
    }

    // START_METHOD_ON_METRIC_UPDATE_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода on_metric_update - позволяет переопределить в Python
    // INPUTS:
    // - metrics: py::dict — словарь текущих метрик
    // OUTPUTS: void
    // END_CONTRACT
    void on_metric_update(py::dict metrics) override {
        PYBIND11_OVERRIDE(
            void,
            MatchNotifierPlugin,
            on_metric_update,
            metrics
        );
    }

    // START_METHOD_ON_SHUTDOWN_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода on_shutdown - позволяет переопределить в Python
    // OUTPUTS: void
    // END_CONTRACT
    void on_shutdown() override {
        PYBIND11_OVERRIDE(
            void,
            MatchNotifierPlugin,
            on_shutdown
        );
    }

    // START_METHOD_GET_UI_COMPONENTS_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода get_ui_components - позволяет переопределить в Python
    // OUTPUTS: py::object
    // END_CONTRACT
    py::object get_ui_components() override {
        PYBIND11_OVERRIDE(
            py::object,
            MatchNotifierPlugin,
            get_ui_components
        );
    }

    // START_METHOD_RESET_NOTIFICATIONS_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода reset_notifications - позволяет переопределить в Python
    // OUTPUTS: void
    // END_CONTRACT
    void reset_notifications() override {
        PYBIND11_OVERRIDE(
            void,
            MatchNotifierPlugin,
            reset_notifications
        );
    }

    // START_METHOD_GET_MATCH_HISTORY_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода get_match_history - позволяет переопределить в Python
    // OUTPUTS: py::list
    // END_CONTRACT
    py::list get_match_history() const override {
        PYBIND11_OVERRIDE(
            py::list,
            MatchNotifierPlugin,
            get_match_history
        );
    }

    // START_METHOD_GET_TOTAL_MATCHES_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода get_total_matches - позволяет переопределить в Python
    // OUTPUTS: int32_t
    // END_CONTRACT
    int32_t get_total_matches() const override {
        PYBIND11_OVERRIDE(
            int32_t,
            MatchNotifierPlugin,
            get_total_matches
        );
    }

    // START_METHOD_GET_LATEST_MATCH_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода get_latest_match - позволяет переопределить в Python
    // OUTPUTS: py::object
    // END_CONTRACT
    py::object get_latest_match() const override {
        PYBIND11_OVERRIDE(
            py::object,
            MatchNotifierPlugin,
            get_latest_match
        );
    }

    // START_METHOD_SET_NOTIFICATION_SETTINGS_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода set_notification_settings - позволяет переопределить в Python
    // INPUTS:
    // - settings: py::dict — словарь настроек
    // OUTPUTS: void
    // END_CONTRACT
    void set_notification_settings(py::dict settings) override {
        PYBIND11_OVERRIDE(
            void,
            MatchNotifierPlugin,
            set_notification_settings,
            settings
        );
    }

    // START_METHOD_GET_NOTIFICATION_SETTINGS_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода get_notification_settings - позволяет переопределить в Python
    // OUTPUTS: py::dict
    // END_CONTRACT
    py::dict get_notification_settings() const override {
        PYBIND11_OVERRIDE(
            py::dict,
            MatchNotifierPlugin,
            get_notification_settings
        );
    }

    // START_METHOD_REGISTER_MATCH_CALLBACK_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода register_match_callback - позволяет переопределить в Python
    // INPUTS:
    // - callback: py::object — callback функция
    // OUTPUTS: void
    // END_CONTRACT
    void register_match_callback(py::object callback) override {
        PYBIND11_OVERRIDE(
            void,
            MatchNotifierPlugin,
            register_match_callback,
            callback
        );
    }

    // START_METHOD_UNREGISTER_MATCH_CALLBACK_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода unregister_match_callback - позволяет переопределить в Python
    // INPUTS:
    // - callback: py::object — callback функция
    // OUTPUTS: void
    // END_CONTRACT
    void unregister_match_callback(py::object callback) override {
        PYBIND11_OVERRIDE(
            void,
            MatchNotifierPlugin,
            unregister_match_callback,
            callback
        );
    }

    // START_METHOD_ON_MATCH_EVENT_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода on_match_event - позволяет переопределить в Python
    // INPUTS:
    // - match_data: py::dict — данные о совпадении
    // OUTPUTS: void
    // END_CONTRACT
    void on_match_event(py::dict match_data) override {
        PYBIND11_OVERRIDE(
            void,
            MatchNotifierPlugin,
            on_match_event,
            match_data
        );
    }

    // START_METHOD_GET_NOTIFICATION_SUMMARY_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода get_notification_summary - позволяет переопределить в Python
    // OUTPUTS: std::string
    // END_CONTRACT
    std::string get_notification_summary() const override {
        PYBIND11_OVERRIDE(
            std::string,
            MatchNotifierPlugin,
            get_notification_summary
        );
    }

    // START_METHOD_EXPORT_MATCHES_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода export_matches - позволяет переопределить в Python
    // INPUTS:
    // - file_path: const std::string& — путь к файлу
    // OUTPUTS: bool
    // END_CONTRACT
    bool export_matches(const std::string& file_path) const override {
        PYBIND11_OVERRIDE(
            bool,
            MatchNotifierPlugin,
            export_matches,
            file_path
        );
    }

    // START_METHOD_ON_START_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода on_start - позволяет переопределить в Python
    // INPUTS:
    // - selected_list_path: const std::string& — путь к списку
    // OUTPUTS: void
    // END_CONTRACT
    void on_start(const std::string& selected_list_path) override {
        PYBIND11_OVERRIDE(
            void,
            MatchNotifierPlugin,
            on_start,
            selected_list_path
        );
    }

    // START_METHOD_ON_MATCH_FOUND_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода on_match_found - позволяет переопределить в Python
    // INPUTS:
    // - matches: py::list — список совпадений
    // - iteration: int — номер итерации
    // OUTPUTS: void
    // END_CONTRACT
    void on_match_found(py::list matches, int iteration) override {
        PYBIND11_OVERRIDE(
            void,
            MatchNotifierPlugin,
            on_match_found,
            matches,
            iteration
        );
    }

    // START_METHOD_ON_FINISH_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода on_finish - позволяет переопределить в Python
    // INPUTS:
    // - final_metrics: py::dict — финальные метрики
    // OUTPUTS: void
    // END_CONTRACT
    void on_finish(py::dict final_metrics) override {
        PYBIND11_OVERRIDE(
            void,
            MatchNotifierPlugin,
            on_finish,
            final_metrics
        );
    }

    // START_METHOD_ON_RESET_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода on_reset - позволяет переопределить в Python
    // OUTPUTS: void
    // END_CONTRACT
    void on_reset() override {
        PYBIND11_OVERRIDE(
            void,
            MatchNotifierPlugin,
            on_reset
        );
    }

    // START_METHOD_HEALTH_CHECK_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода health_check - позволяет переопределить в Python
    // OUTPUTS: bool
    // END_CONTRACT
    bool health_check() const override {
        PYBIND11_OVERRIDE(
            bool,
            MatchNotifierPlugin,
            health_check
        );
    }
};
// END_CLASS_MATCH_NOTIFIER_PLUGIN_TRAMPOLINE


#endif // WALLET_MONITOR_MATCH_NOTIFIER_PLUGIN_HPP
