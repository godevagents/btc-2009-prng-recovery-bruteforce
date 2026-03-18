// FILE: src/monitor/_cpp/include/plugin_base.hpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Заголовочный файл базового класса плагина мониторинга на C++.
// Определяет интерфейс и жизненный цикл плагинов для системы мониторинга генерации кошельков Bitcoin.
// SCOPE: Абстрактные классы, протоколы, структуры данных плагинов
// INPUT: Нет (заголовочный файл)
// OUTPUT: Классы PluginMetadata, MonitorAppProtocol, BaseMonitorPlugin
// KEYWORDS: [DOMAIN(9): Monitoring; DOMAIN(8): PluginSystem; CONCEPT(8): AbstractClass; TECH(6): Interface]
// LINKS: [USES_API(7): string; USES_API(6): vector; USES_API(5): memory]
// END_MODULE_CONTRACT

#ifndef WALLET_MONITOR_PLUGIN_BASE_HPP
#define WALLET_MONITOR_PLUGIN_BASE_HPP

#include <string>
#include <vector>
#include <memory>
#include <algorithm>
#include <iostream>
#include <sstream>
#include <functional>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/chrono.h>
#include <pybind11/functional.h>

namespace py = pybind11;

// START_STRUCT_PLUGIN_METADATA
// START_CONTRACT:
// PURPOSE: Структура для хранения метаданных плагина мониторинга
// ATTRIBUTES:
// - name: std::string — уникальное имя плагина
// - version: std::string — версия плагина
// - description: std::string — описание плагина
// - author: std::string — автор плагина
// - dependencies: std::vector<std::string> — зависимости плагина
// - tags: std::vector<std::string> — теги плагина
// - homepage: std::string — домашняя страница (может быть пустой)
// - license: std::string — лицензия (может быть пустой)
// KEYWORDS: [PATTERN(7): DataClass; DOMAIN(8): PluginMetadata; CONCEPT(6): Configuration]
// END_CONTRACT

struct PluginMetadata {
    std::string name;
    std::string version;
    std::string description;
    std::string author;
    std::vector<std::string> dependencies;
    std::vector<std::string> tags;
    std::string homepage;
    std::string license;

    // Конструктор по умолчанию
    PluginMetadata();

    // Конструктор с параметрами
    PluginMetadata(
        const std::string& name,
        const std::string& version,
        const std::string& description,
        const std::string& author,
        const std::vector<std::string>& dependencies = {},
        const std::vector<std::string>& tags = {},
        const std::string& homepage = "",
        const std::string& license = ""
    );

    // Конструктор для Python совместимости
    static PluginMetadata from_python(py::object obj);
};
// END_STRUCT_PLUGIN_METADATA


// START_CLASS_MONITOR_APP_PROTOCOL
// START_CONTRACT:
// PURPOSE: Протокол главного приложения мониторинга. Определяет минимальный интерфейс, необходимый плагинам для взаимодействия с приложением.
// ATTRIBUTES:
// - _app: py::object — ссылка на приложение
// METHODS:
// - register_ui_component: Регистрация UI компонента в указанной вкладке
// - log: Логирование сообщения
// - get_metrics_store: Получение хранилища метрик
// KEYWORDS: [PATTERN(7): Protocol; DOMAIN(8): Interface; CONCEPT(6): Contract]
// END_CONTRACT

class MonitorAppProtocol {
public:
    // START_CONSTRUCTOR_MONITOR_APP_PROTOCOL
    // START_CONTRACT:
    // PURPOSE: Конструктор протокола приложения
    // INPUTS:
    // - app: py::object — ссылка на главное приложение мониторинга
    // OUTPUTS: Инициализированный объект протокола
    // KEYWORDS: [CONCEPT(5): Initialization]
    // END_CONTRACT
    explicit MonitorAppProtocol(py::object app = py::none());

    // START_METHOD_REGISTER_UI_COMPONENT
    // START_CONTRACT:
    // PURPOSE: Регистрация UI компонента в указанной вкладке
    // INPUTS:
    // - component: py::object — UI компонент для регистрации
    // - tab_name: std::string — имя вкладки для размещения компонента
    // OUTPUTS: void
    // SIDE_EFFECTS: Вызывает метод register_ui_component у приложения
    // KEYWORDS: [DOMAIN(7): UI; CONCEPT(6): Registration]
    // END_CONTRACT
    void register_ui_component(py::object component, const std::string& tab_name);

    // START_METHOD_LOG
    // START_CONTRACT:
    // PURPOSE: Логирование сообщения с указанным уровнем
    // INPUTS:
    // - level: std::string — уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    // - message: std::string — текст сообщения
    // OUTPUTS: void
    // KEYWORDS: [CONCEPT(5): Logging]
    // END_CONTRACT
    void log(const std::string& level, const std::string& message);

    // START_METHOD_GET_METRICS_STORE
    // START_CONTRACT:
    // PURPOSE: Получение хранилища метрик от приложения
    // OUTPUTS: py::object — хранилище метрик или None
    // KEYWORDS: [DOMAIN(8): MetricsStore; CONCEPT(6): Getter]
    // END_CONTRACT
    py::object get_metrics_store();

    // Деструктор
    virtual ~MonitorAppProtocol() = default;

protected:
    py::object _app;  // Ссылка на приложение
};
// END_CLASS_MONITOR_APP_PROTOCOL


// START_CLASS_BASE_MONITOR_PLUGIN
// START_CONTRACT:
// PURPOSE: Базовый класс для всех плагинов системы мониторинга. Определяет общий интерфейс и жизненный цикл плагинов.
// ATTRIBUTES:
// - VERSION: std::string — версия плагина
// - AUTHOR: std::string — автор плагина
// - DESCRIPTION: std::string — описание плагина
// - _name: std::string — уникальное имя плагина
// - _priority: int — приоритет плагина (0 = highest, 100 = lowest)
// - _enabled: bool — флаг включения плагина
// - _app: py::object — ссылка на приложение
// METHODS:
// - initialize: Чистая виртуальная функция инициализации плагина
// - on_metric_update: Чистая виртуальная функция обработки метрик
// - on_shutdown: Чистая виртуальная функция завершения работы
// - get_ui_components: Виртуальная функция получения UI компонентов
// - on_start: Виртуальная функция обработки запуска
// - on_match_found: Виртуальная функция обработки совпадений
// - on_finish: Виртуальная функция обработки завершения
// - on_reset: Виртуальная функция обработки сброса
// - enable: Включение плагина
// - disable: Отключение плагина
// - is_enabled: Проверка состояния плагина
// - health_check: Проверка работоспособности
// KEYWORDS: [PATTERN(8): AbstractClass; DOMAIN(9): PluginSystem; TECH(6): Interface]
// LINKS: [IMPLEMENTS(8): MonitorAppProtocol]
// END_CONTRACT

class BaseMonitorPlugin {
public:
    // Статические константы (аналог class attributes в Python)
    static const std::string VERSION;
    static const std::string AUTHOR;
    static const std::string DESCRIPTION;

    // START_CONSTRUCTOR_BASE_MONITOR_PLUGIN
    // START_CONTRACT:
    // PURPOSE: Конструктор базового плагина с именем и приоритетом
    // INPUTS:
    // - name: const std::string& — уникальное имя плагина
    // - priority: int — приоритет плагина (0 = highest, 100 = lowest)
    // OUTPUTS: Инициализированный объект плагина
    // SIDE_EFFECTS: Создает внутреннее состояние плагина; устанавливает начальные значения атрибутов
    // KEYWORDS: [CONCEPT(5): Initialization; DOMAIN(7): PluginSetup]
    // END_CONTRACT
    BaseMonitorPlugin(const std::string& name, int priority = 50);

    // Виртуальный деструктор
    virtual ~BaseMonitorPlugin() = default;

    // START_METHOD_INITIALIZE
    // START_CONTRACT:
    // PURPOSE: Инициализация плагина и регистрация UI компонентов в главном приложении (чистая виртуальная функция)
    // INPUTS:
    // - app: py::object — ссылка на главное приложение мониторинга
    // OUTPUTS: void
    // SIDE_EFFECTS: Регистрирует UI компоненты плагина в приложении; может инициализировать внутреннее состояние плагина
    // KEYWORDS: [DOMAIN(8): PluginSetup; CONCEPT(6): Registration]
    // TEST_CONDITIONS_SUCCESS_CRITERIA: Плагин должен зарегистрировать свои компоненты в приложении
    // END_CONTRACT
    virtual void initialize(py::object app) = 0;

    // START_METHOD_ON_METRIC_UPDATE
    // START_CONTRACT:
    // PURPOSE: Обработка обновления метрик от генератора (чистая виртуальная функция)
    // INPUTS:
    // - metrics: py::dict — словарь текущих метрик
    // OUTPUTS: void
    // SIDE_EFFECTS: Может обновить внутреннее состояние плагина; может обновить UI компоненты
    // KEYWORDS: [DOMAIN(9): MetricsProcessing; CONCEPT(7): EventHandler]
    // END_CONTRACT
    virtual void on_metric_update(py::dict metrics) = 0;

    // START_METHOD_ON_SHUTDOWN
    // START_CONTRACT:
    // PURPOSE: Действия при завершении работы мониторинга (чистая виртуальная функция)
    // INPUTS: Нет
    // OUTPUTS: void
    // SIDE_EFFECTS: Освобождение ресурсов плагина; сохранение состояния (если необходимо); логирование завершения работы
    // KEYWORDS: [CONCEPT(8): Cleanup; DOMAIN(7): Shutdown]
    // END_CONTRACT
    virtual void on_shutdown() = 0;

    // START_METHOD_GET_UI_COMPONENTS
    // START_CONTRACT:
    // PURPOSE: Получение UI компонентов плагина для отображения
    // OUTPUTS: py::object — UI компоненты плагина или None
    // KEYWORDS: [PATTERN(6): UI; CONCEPT(5): Getter]
    // END_CONTRACT
    virtual py::object get_ui_components();

    // START_METHOD_GET_METADATA
    // START_CONTRACT:
    // PURPOSE: Получение метаданных плагина
    // OUTPUTS: PluginMetadata — метаданные плагина
    // KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): PluginMetadata]
    // END_CONTRACT
    virtual PluginMetadata get_metadata() const;

    // START_METHOD_ON_START
    // START_CONTRACT:
    // PURPOSE: Обработчик запуска генератора кошельков
    // INPUTS:
    // - selected_list_path: const std::string& — путь к выбранному списку адресов
    // OUTPUTS: void
    // SIDE_EFFECTS: Может инициализировать состояние для нового запуска
    // KEYWORDS: [DOMAIN(8): EventHandler; CONCEPT(6): Startup]
    // END_CONTRACT
    virtual void on_start(const std::string& selected_list_path);

    // START_METHOD_ON_MATCH_FOUND
    // START_CONTRACT:
    // PURPOSE: Обработчик обнаружения совпадений
    // INPUTS:
    // - matches: py::list — список найденных совпадений
    // - iteration: int — номер итерации, на которой найдены совпадения
    // OUTPUTS: void
    // SIDE_EFFECTS: Может отправить уведомление; может обновить UI
    // KEYWORDS: [DOMAIN(9): MatchHandler; CONCEPT(7): EventHandler]
    // END_CONTRACT
    virtual void on_match_found(py::list matches, int iteration);

    // START_METHOD_ON_FINISH
    // START_CONTRACT:
    // PURPOSE: Обработчик завершения генерации кошельков
    // INPUTS:
    // - final_metrics: py::dict — финальные метрики генерации
    // OUTPUTS: void
    // SIDE_EFFECTS: Может сгенерировать итоговую статистику; может обновить UI финальными данными
    // KEYWORDS: [DOMAIN(8): Finalization; CONCEPT(7): EventHandler]
    // END_CONTRACT
    virtual void on_finish(py::dict final_metrics);

    // START_METHOD_ON_RESET
    // START_CONTRACT:
    // PURPOSE: Обработчик сброса генератора. Вызывается при нажатии кнопки Reset для сброса плагина в начальное состояние.
    // INPUTS: Нет
    // OUTPUTS: void
    // SIDE_EFFECTS: Сбрасывает внутреннее состояние плагина; может очистить кэши и временные данные
    // KEYWORDS: [DOMAIN(7): ResetHandler; CONCEPT(7): EventHandler]
    // END_CONTRACT
    virtual void on_reset();

    // START_METHOD_ENABLE
    // START_CONTRACT:
    // PURPOSE: Включение плагина
    // OUTPUTS: void
    // SIDE_EFFECTS: Устанавливает флаг enabled = true; логирует событие включения
    // KEYWORDS: [CONCEPT(6): StateManagement]
    // END_CONTRACT
    virtual void enable();

    // START_METHOD_DISABLE
    // START_CONTRACT:
    // PURPOSE: Отключение плагина
    // OUTPUTS: void
    // SIDE_EFFECTS: Устанавливает флаг enabled = false; логирует событие отключения
    // KEYWORDS: [CONCEPT(6): StateManagement]
    // END_CONTRACT
    virtual void disable();

    // START_METHOD_IS_ENABLED
    // START_CONTRACT:
    // PURPOSE: Проверка состояния плагина
    // OUTPUTS: bool — true если плагин включён, false если выключен
    // KEYWORDS: [CONCEPT(5): Getter; DOMAIN(6): StateCheck]
    // END_CONTRACT
    virtual bool is_enabled() const;

    // START_METHOD_HEALTH_CHECK
    // START_CONTRACT:
    // PURPOSE: Проверка работоспособности плагина
    // OUTPUTS: bool — true если плагин работает корректно
    // KEYWORDS: [CONCEPT(7): HealthCheck; DOMAIN(6): Diagnostics]
    // END_CONTRACT
    virtual bool health_check() const;

    // START_METHOD_GET_NAME
    // START_CONTRACT:
    // PURPOSE: Получение имени плагина
    // OUTPUTS: std::string — имя плагина
    // KEYWORDS: [CONCEPT(5): Getter]
    // END_CONTRACT
    virtual std::string get_name() const;

    // START_METHOD_GET_PRIORITY
    // START_CONTRACT:
    // PURPOSE: Получение приоритета плагина
    // OUTPUTS: int — приоритет плагина
    // KEYWORDS: [CONCEPT(5): Getter]
    // END_CONTRACT
    virtual int get_priority() const;

    // START_METHOD_SET_PRIORITY
    // START_CONTRACT:
    // PURPOSE: Установка приоритета
    // INPUTS:
    // - priority: int — новый приоритет
    // OUTPUTS: void
    // KEYWORDS: [CONCEPT(6): Setter]
    // END_CONTRACT
    virtual void set_priority(int priority);

    // START_METHOD_GET_ENABLED
    // START_CONTRACT:
    // PURPOSE: Получение состояния enabled (геттер)
    // OUTPUTS: bool — состояние включения плагина
    // KEYWORDS: [CONCEPT(5): Getter]
    // END_CONTRACT
    virtual bool get_enabled() const;

    // START_METHOD_SET_ENABLED
    // START_CONTRACT:
    // PURPOSE: Установка состояния enabled (сеттер)
    // INPUTS:
    // - enabled: bool — новое состояние включения
    // OUTPUTS: void
    // KEYWORDS: [CONCEPT(6): Setter]
    // END_CONTRACT
    virtual void set_enabled(bool enabled);

    // Операторы сравнения
    // START_OPERATOR_LT
    // START_CONTRACT:
    // PURPOSE: Сравнение плагинов по приоритету (оператор <)
    // INPUTS:
    // - other: const BaseMonitorPlugin& — другой плагин для сравнения
    // OUTPUTS: bool — результат сравнения
    // KEYWORDS: [CONCEPT(8): Comparison; DOMAIN(6): Sorting]
    // END_CONTRACT
    bool operator<(const BaseMonitorPlugin& other) const;

    // START_OPERATOR_EQ
    // START_CONTRACT:
    // PURPOSE: Проверка равенства плагинов по имени
    // INPUTS:
    // - other: const BaseMonitorPlugin& — объект для сравнения
    // OUTPUTS: bool — результат сравнения
    // KEYWORDS: [CONCEPT(7): Equality; DOMAIN(5): Comparison]
    // END_CONTRACT
    bool operator==(const BaseMonitorPlugin& other) const;

    // START_METHOD_HASH
    // START_CONTRACT:
    // PURPOSE: Получение хэша плагина на основе имени
    // OUTPUTS: size_t — хэш плагина
    // KEYWORDS: [CONCEPT(6): Hashing]
    // END_CONTRACT
    virtual size_t hash() const;

protected:
    std::string _name;          // Имя плагина
    int _priority;              // Приоритет плагина
    bool _enabled;               // Флаг включения плагина
    py::object _app;            // Ссылка на приложение

    // Внутренний метод для логирования
    void log_debug(const std::string& message);
    void log_info(const std::string& message);
    void log_warning(const std::string& message);
    void log_error(const std::string& message);

    // Вспомогательный метод для получения временной метки
    static std::string get_timestamp();
};
// END_CLASS_BASE_MONITOR_PLUGIN


// START_CLASS_BASE_MONITOR_PLUGIN_TRAMPOLINE
// START_CONTRACT:
// PURPOSE: Trampoline класс (класс-заглушка) для обеспечения возможности наследования от C++ класса в Python.
// Позволяет переопределять чистые виртуальные методы в Python и вызывать их из C++.
// KEYWORDS: [PATTERN(9): TrampolineClass; DOMAIN(9): Pybind11; TECH(7): PythonBindings]
// END_CONTRACT

class BaseMonitorPluginTrampoline : public BaseMonitorPlugin {
public:
    // Конструктор trampoline
    using BaseMonitorPlugin::BaseMonitorPlugin;

    // START_METHOD_INITIALIZE_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода initialize - позволяет переопределить в Python
    // INPUTS:
    // - app: py::object — ссылка на главное приложение мониторинга
    // OUTPUTS: void
    // END_CONTRACT
    void initialize(py::object app) override {
        PYBIND11_OVERRIDE_PURE(
            void,                          // Return type
            BaseMonitorPlugin,             // Parent class
            initialize,                    // Method name
            app                            // Arguments
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
        PYBIND11_OVERRIDE_PURE(
            void,
            BaseMonitorPlugin,
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
        PYBIND11_OVERRIDE_PURE(
            void,
            BaseMonitorPlugin,
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
            BaseMonitorPlugin,
            get_ui_components
        );
    }

    // START_METHOD_ON_START_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода on_start - позволяет переопределить в Python
    // INPUTS:
    // - selected_list_path: const std::string& — путь к выбранному списку адресов
    // OUTPUTS: void
    // END_CONTRACT
    void on_start(const std::string& selected_list_path) override {
        PYBIND11_OVERRIDE(
            void,
            BaseMonitorPlugin,
            on_start,
            selected_list_path
        );
    }

    // START_METHOD_ON_MATCH_FOUND_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода on_match_found - позволяет переопределить в Python
    // INPUTS:
    // - matches: py::list — список найденных совпадений
    // - iteration: int — номер итерации
    // OUTPUTS: void
    // END_CONTRACT
    void on_match_found(py::list matches, int iteration) override {
        PYBIND11_OVERRIDE(
            void,
            BaseMonitorPlugin,
            on_match_found,
            matches,
            iteration
        );
    }

    // START_METHOD_ON_FINISH_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода on_finish - позволяет переопределить в Python
    // INPUTS:
    // - final_metrics: py::dict — финальные метрики генерации
    // OUTPUTS: void
    // END_CONTRACT
    void on_finish(py::dict final_metrics) override {
        PYBIND11_OVERRIDE(
            void,
            BaseMonitorPlugin,
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
            BaseMonitorPlugin,
            on_reset
        );
    }

    // START_METHOD_ENABLE_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода enable - позволяет переопределить в Python
    // OUTPUTS: void
    // END_CONTRACT
    void enable() override {
        PYBIND11_OVERRIDE(
            void,
            BaseMonitorPlugin,
            enable
        );
    }

    // START_METHOD_DISABLE_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода disable - позволяет переопределить в Python
    // OUTPUTS: void
    // END_CONTRACT
    void disable() override {
        PYBIND11_OVERRIDE(
            void,
            BaseMonitorPlugin,
            disable
        );
    }

    // START_METHOD_IS_ENABLED_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода is_enabled - позволяет переопределить в Python
    // OUTPUTS: bool
    // END_CONTRACT
    bool is_enabled() const override {
        PYBIND11_OVERRIDE(
            bool,
            BaseMonitorPlugin,
            is_enabled
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
            BaseMonitorPlugin,
            health_check
        );
    }

    // START_METHOD_GET_NAME_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода get_name - позволяет переопределить в Python
    // OUTPUTS: std::string
    // END_CONTRACT
    std::string get_name() const override {
        PYBIND11_OVERRIDE(
            std::string,
            BaseMonitorPlugin,
            get_name
        );
    }

    // START_METHOD_GET_PRIORITY_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода get_priority - позволяет переопределить в Python
    // OUTPUTS: int
    // END_CONTRACT
    int get_priority() const override {
        PYBIND11_OVERRIDE(
            int,
            BaseMonitorPlugin,
            get_priority
        );
    }

    // START_METHOD_SET_PRIORITY_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода set_priority - позволяет переопределить в Python
    // INPUTS:
    // - priority: int — новый приоритет
    // OUTPUTS: void
    // END_CONTRACT
    void set_priority(int priority) override {
        PYBIND11_OVERRIDE(
            void,
            BaseMonitorPlugin,
            set_priority,
            priority
        );
    }

    // START_METHOD_GET_ENABLED_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода get_enabled - позволяет переопределить в Python
    // OUTPUTS: bool
    // END_CONTRACT
    bool get_enabled() const override {
        PYBIND11_OVERRIDE(
            bool,
            BaseMonitorPlugin,
            get_enabled
        );
    }

    // START_METHOD_SET_ENABLED_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода set_enabled - позволяет переопределить в Python
    // INPUTS:
    // - enabled: bool — новое состояние
    // OUTPUTS: void
    // END_CONTRACT
    void set_enabled(bool enabled) override {
        PYBIND11_OVERRIDE(
            void,
            BaseMonitorPlugin,
            set_enabled,
            enabled
        );
    }

    // START_METHOD_HASH_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода hash - позволяет переопределить в Python
    // OUTPUTS: size_t
    // END_CONTRACT
    size_t hash() const override {
        PYBIND11_OVERRIDE(
            size_t,
            BaseMonitorPlugin,
            hash
        );
    }
};
// END_CLASS_BASE_MONITOR_PLUGIN_TRAMPOLINE


#endif // WALLET_MONITOR_PLUGIN_BASE_HPP
