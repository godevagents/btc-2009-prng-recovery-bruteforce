// FILE: src/monitor_cpp/plugins/plugin_base.hpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Базовый интерфейс и классы для системы плагинов мониторинга.
// Определяет общий интерфейс, жизненный цикл и управление плагинами.
// SCOPE: Интерфейсы плагинов, система состояний, фабрика, менеджер
// INPUT: Нет (абстрактные интерфейсы)
// OUTPUT: Интерфейс IPlugin, Перечисления, Структуры данных, Классы
// KEYWORDS: [DOMAIN(9): PluginSystem; DOMAIN(8): Monitoring; CONCEPT(8): Interface; TECH(6): C++17]
// LINKS: [USES_API(7): pybind11; IMPLEMENTS(6): Observer]
// END_MODULE_CONTRACT

#ifndef PLUGIN_BASE_HPP
#define PLUGIN_BASE_HPP

//==============================================================================
// Standard Library Headers
//==============================================================================
#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <optional>
#include <unordered_map>
#include <variant>
#include <atomic>
#include <mutex>
#include <shared_mutex>
#include <chrono>
#include <functional>
#include <stdexcept>
#include <any>

//==============================================================================
// Forward Declarations
//==============================================================================
class IPlugin;
class PluginManager;

//==============================================================================
// Type Aliases
//==============================================================================
/**
 * @brief Универсальный тип для хранения значений (аналог Python Any)
 * 
 * Используется для совместимости с Python словарями метрик.
 * Поддерживает: int, double, string, bool, vector, dict
 */
using PluginAny = std::variant<
    int64_t, 
    double, 
    std::string, 
    bool, 
    std::vector<PluginAny>,
    std::unordered_map<std::string, PluginAny>
>;

/**
 * @brief Тип для хранения метрик плагина
 */
using PluginMetrics = std::unordered_map<std::string, PluginAny>;

/**
 * @brief Тип для хранения списка совпадений
 */
using MatchList = std::vector<std::unordered_map<std::string, PluginAny>>;

//==============================================================================
// PluginState - Перечисление состояний плагина
//==============================================================================
/**
 * @enum PluginState
 * @brief Перечисление состояний жизненного цикла плагина.
 * 
 * @details
 * Состояния:
 * - UNINITIALIZED: Плагин создан, но не инициализирован
 * - INITIALIZING: Плагин в процессе инициализации
 * - ACTIVE: Плагин полностью активен и обрабатывает события
 * - PAUSED: Плагин приостановлен (может быть возобновлен)
 * - STOPPED: Плагин остановлен (завершил работу)
 * - ERROR: Плагин в состоянии ошибки
 * 
 * @see IPlugin
 * @see BasePlugin
 */
enum class PluginState {
    UNINITIALIZED,  ///< Плагин создан, но не инициализирован
    INITIALIZING,   ///< Плагин в процессе инициализации
    ACTIVE,         ///< Плагин полностью активен
    PAUSED,         ///< Плагин приостановлен
    STOPPED,        ///< Плагин остановлен
    ERROR           ///< Плагин в состоянии ошибки
};

//==============================================================================
// PluginCapabilities - Возможности плагина
//==============================================================================
/**
 * @struct PluginCapabilities
 * @brief Структура возможностей плагина.
 * 
 * @details
 * Определяет, какие функции поддерживает плагин:
 * - supports_realtime: Поддержка реального времени
 * - supports_notifications: Поддержка уведомлений
 * - supports_export: Поддержка экспорта данных
 * 
 * @see PluginInfo
 * @see IPlugin
 */
struct PluginCapabilities {
    bool supports_realtime;      ///< Поддержка real-time обновлений
    bool supports_notifications; ///< Поддержка уведомлений
    bool supports_export;        ///< Поддержка экспорта данных
    
    /**
     * @brief Конструктор по умолчанию
     * @details Все возможности отключены по умолчанию
     */
    PluginCapabilities()
        : supports_realtime(false)
        , supports_notifications(false)
        , supports_export(false)
    {}
    
    /**
     * @brief Конструктор с параметрами
     * @param realtime Поддержка real-time
     * @param notifications Поддержка уведомлений
     * @param export_data Поддержка экспорта
     */
    PluginCapabilities(bool realtime, bool notifications, bool export_data)
        : supports_realtime(realtime)
        , supports_notifications(notifications)
        , supports_export(export_data)
    {}
};

//==============================================================================
// PluginInfo - Информация о плагине
//==============================================================================
/**
 * @struct PluginInfo
 * @brief Структура информации о плагине.
 * 
 * @details
 * Содержит метаданные плагина:
 * - name: Уникальное имя плагина
 * - version: Версия плагина
 * - description: Описание плагина
 * - author: Автор плагина
 * - capabilities: Возможности плагина
 * 
 * @see PluginCapabilities
 * @see IPlugin::get_info()
 */
struct PluginInfo {
    std::string name;            ///< Уникальное имя плагина
    std::string version;         ///< Версия плагина
    std::string description;     ///< Описание плагина
    std::string author;          ///< Автор плагина
    PluginCapabilities capabilities; ///< Возможности плагина
    
    /**
     * @brief Конструктор по умолчанию
     */
    PluginInfo()
        : name("")
        , version("1.0.0")
        , description("")
        , author("")
    {}
    
    /**
     * @brief Конструктор с основными параметрами
     * @param plugin_name Имя плагина
     * @param plugin_version Версия плагина
     * @param plugin_description Описание плагина
     * @param plugin_author Автор плагина
     */
    PluginInfo(
        const std::string& plugin_name,
        const std::string& plugin_version,
        const std::string& plugin_description,
        const std::string& plugin_author
    )
        : name(plugin_name)
        , version(plugin_version)
        , description(plugin_description)
        , author(plugin_author)
    {}
    
    /**
     * @brief Преобразование в строку для логирования
     * @return Строковое представление информации о плагине
     */
    std::string to_string() const;
};

//==============================================================================
// PluginConfig - Конфигурация плагина
//==============================================================================
/**
 * @struct PluginConfig
 * @brief Структура конфигурации плагина.
 * 
 * @details
 * Содержит параметры конфигурации плагина:
 * - enabled: Включен ли плагин
 * - priority: Приоритет плагина (меньше = выше приоритет)
 * - update_interval: Интервал обновления в секундах
 * - custom_config: Пользовательские параметры конфигурации
 * 
 * @see IPlugin
 * @see BasePlugin
 */
struct PluginConfig {
    bool enabled;                                    ///< Включен ли плагин
    int priority;                                   ///< Приоритет плагина
    double update_interval;                         ///< Интервал обновления (секунды)
    std::unordered_map<std::string, PluginAny> custom_config; ///< Пользовательская конфигурация
    
    /**
     * @brief Конструктор по умолчанию
     * @details Плагин включен, приоритет по умолчанию 50, интервал 1.0 сек
     */
    PluginConfig()
        : enabled(true)
        , priority(50)
        , update_interval(1.0)
    {}
    
    /**
     * @brief Конструктор с параметрами
     * @param is_enabled Включен ли плагин
     * @param plugin_priority Приоритет плагина
     * @param interval Интервал обновления
     */
    PluginConfig(bool is_enabled, int plugin_priority, double interval)
        : enabled(is_enabled)
        , priority(plugin_priority)
        , update_interval(interval)
    {}
};

//==============================================================================
// UpdateContext - Контекст обновления
//==============================================================================
/**
 * @struct UpdateContext
 * @brief Структура контекста обновления плагина.
 * 
 * @details
 * Содержит контекстную информацию при обновлении плагина:
 * - timestamp: Время обновления
 * - iteration: Номер итерации
 * - metrics: Текущие метрики
 * - matches: Список совпадений (если есть)
 * 
 * @see IPlugin::on_update()
 */
struct UpdateContext {
    std::chrono::steady_clock::time_point timestamp; ///< Время обновления
    int64_t iteration;                                ///< Номер итерации
    PluginMetrics metrics;                           ///< Текущие метрики
    std::optional<MatchList> matches;               ///< Список совпадений (опционально)
    
    /**
     * @brief Конструктор по умолчанию
     */
    UpdateContext()
        : timestamp(std::chrono::steady_clock::now())
        , iteration(0)
    {}
    
    /**
     * @brief Конструктор с метриками
     * @param iter Номер итерации
     * @param plugin_metrics Метрики плагина
     */
    UpdateContext(int64_t iter, const PluginMetrics& plugin_metrics)
        : timestamp(std::chrono::steady_clock::now())
        , iteration(iter)
        , metrics(plugin_metrics)
    {}
};

//==============================================================================
// IPlugin - Абстрактный интерфейс плагина
//==============================================================================
/**
 * @class IPlugin
 * @brief Абстрактный интерфейс для всех плагинов мониторинга.
 * 
 * @details
 * Определяет обязательный интерфейс, который должны реализовать все плагины.
 * Обеспечивает единый жизненный цикл плагинов в системе мониторинга.
 * 
 * Чисто виртуальные методы (должны быть реализованы):
 * - initialize(): Инициализация плагина
 * - shutdown(): Завершение работы плагина
 * - get_info(): Получение информации о плагине
 * - get_state(): Получение текущего состояния
 * 
 * Виртуальные методы (могут быть переопределены):
 * - on_update(): Обработка обновления
 * - on_metrics_update(): Обработка обновления метрик
 * - on_match_found(): Обработка найденных совпадений
 * - on_start(): Обработка запуска генератора
 * - on_finish(): Обработка завершения генерации
 * - on_reset(): Обработка сброса
 * 
 * @invariant Плагин всегда имеет валидное состояние после инициализации
 * @invariant Все операции должны быть thread-safe
 * 
 * @see BasePlugin
 * @see PluginManager
 * 
 * @example
 * @code
 * class MyPlugin : public IPlugin {
 * public:
 *     void initialize() override {
 *         // Инициализация плагина
 *     }
 *     
 *     void shutdown() override {
 *         // Завершение работы
 *     }
 *     
 *     PluginInfo get_info() const override {
 *         return PluginInfo("MyPlugin", "1.0.0", "Description", "Author");
 *     }
 *     
 *     PluginState get_state() const override {
 *         return m_state.load();
 *     }
 * };
 * @endcode
 */
class IPlugin {
public:
    //==============================================================================
    // Constructor / Destructor
    //==============================================================================
    /**
     * @brief Виртуальный деструктор
     * @details Обеспечивает корректное полиморфное удаление
     */
    virtual ~IPlugin() = default;

    //==============================================================================
    // Lifecycle Methods (Abstract - must implement)
    //==============================================================================
    
    /**
     * @brief Инициализация плагина
     * @details
     * Вызывается при инициализации плагина в системе мониторинга.
     * Плагин должен подготовить все необходимые ресурсы.
     * 
     * CONTRACT:
     * INPUTS: Нет
     * OUTPUTS: void
     * SIDE_EFFECTS: Инициализация внутреннего состояния; подготовка ресурсов
     * TEST_CONDITIONS_SUCCESS_CRITERIA: Плагин должен перейти в состояние INITIALIZING
     * 
     * @throw std::runtime_error при ошибке инициализации
     */
    virtual void initialize() = 0;
    
    /**
     * @brief Завершение работы плагина
     * @details
     * Вызывается при завершении работы системы мониторинга.
     * Плагин должен освободить все занятые ресурсы.
     * 
     * CONTRACT:
     * INPUTS: Нет
     * OUTPUTS: void
     * SIDE_EFFECTS: Освобождение ресурсов; сохранение состояния
     * TEST_CONDITIONS_SUCCESS_CRITERIA: Плагин должен перейти в состояние STOPPED
     */
    virtual void shutdown() = 0;
    
    /**
     * @brief Получение информации о плагине
     * @return PluginInfo Информация о плагине
     * 
     * CONTRACT:
     * OUTPUTS: PluginInfo - структура с информацией о плагине
     * TEST_CONDITIONS_SUCCESS_CRITERIA: Возвращает валидную структуру
     */
    virtual PluginInfo get_info() const = 0;
    
    /**
     * @brief Получение текущего состояния плагина
     * @return PluginState Текущее состояние плагина
     * 
     * CONTRACT:
     * OUTPUTS: PluginState - одно из значений перечисления
     * TEST_CONDITIONS_SUCCESS_CRITERIA: Всегда возвращает валидное состояние
     */
    virtual PluginState get_state() const = 0;

    //==============================================================================
    // Lifecycle Methods (Virtual - can override)
    //==============================================================================
    
    /**
     * @brief Обработка обновления
     * @param context Контекст обновления
     * @details
     * Вызывается при обновлении данных в системе мониторинга.
     * Основной метод обработки событий плагином.
     * 
     * CONTRACT:
     * INPUTS: const UpdateContext& context - контекст обновления
     * OUTPUTS: void
     * SIDE_EFFECTS: Обновление внутреннего состояния плагина
     * TEST_CONDITIONS_SUCCESS_CRITERIA: Метод должен корректно обработать контекст
     */
    virtual void on_update(const UpdateContext& context);
    
    /**
     * @brief Обработка обновления метрик
     * @param metrics Словарь метрик
     * @details
     * Вызывается при обновлении метрик от генератора кошельков.
     * 
     * CONTRACT:
     * INPUTS: const PluginMetrics& metrics - словарь метрик
     * OUTPUTS: void
     * SIDE_EFFECTS: Обновление внутреннего состояния
     * TEST_CONDITIONS_SUCCESS_CRITERIA: Метод должен корректно обработать метрики
     */
    virtual void on_metrics_update(const PluginMetrics& metrics);
    
    /**
     * @brief Обработка обнаружения совпадений
     * @param matches Список найденных совпадений
     * @param iteration Номер итерации
     * 
     * CONTRACT:
     * INPUTS: const MatchList& matches - список совпадений, int iteration - номер итерации
     * OUTPUTS: void
     * SIDE_EFFECTS: Обработка совпадений; возможно уведомление
     * TEST_CONDITIONS_SUCCESS_CRITERIA: Обработка должна корректно работать с пустым списком
     */
    virtual void on_match_found(const MatchList& matches, int iteration);
    
    /**
     * @brief Обработчик запуска генератора кошельков
     * @param selected_list_path Путь к выбранному списку адресов
     * 
     * CONTRACT:
     * INPUTS: const std::string& selectedListPath - путь к списку
     * OUTPUTS: void
     * SIDE_EFFECTS: Инициализация состояния для нового запуска
     * TEST_CONDITIONS_SUCCESS_CRITERIA: Состояние должно быть готово к новому запуску
     */
    virtual void on_start(const std::string& selected_list_path);
    
    /**
     * @brief Обработчик завершения генерации кошельков
     * @param final_metrics Финальные метрики генерации
     * 
     * CONTRACT:
     * INPUTS: const PluginMetrics& finalMetrics - финальные метрики
     * OUTPUTS: void
     * SIDE_EFFECTS: Генерация итоговой статистики
     * TEST_CONDITIONS_SUCCESS_CRITERIA: Финальные метрики должны быть обработаны
     */
    virtual void on_finish(const PluginMetrics& final_metrics);
    
    /**
     * @brief Обработчик сброса генератора
     * 
     * CONTRACT:
     * INPUTS: Нет
     * OUTPUTS: void
     * SIDE_EFFECTS: Сброс внутреннего состояния
     * TEST_CONDITIONS_SUCCESS_CRITERIA: Состояние должно быть сброшено в начальное
     */
    virtual void on_reset();

    //==============================================================================
    // Control Methods (Virtual - can override)
    //==============================================================================
    
    /**
     * @brief Запуск плагина
     * @details Переводит плагин в состояние ACTIVE
     * 
     * CONTRACT:
     * INPUTS: Нет
     * OUTPUTS: void
     * SIDE_EFFECTS: Изменение состояния на ACTIVE
     * TEST_CONDITIONS_SUCCESS_CRITERIA: Плагин переходит в состояние ACTIVE
     */
    virtual void start();
    
    /**
     * @brief Остановка плагина
     * @details Переводит плагин в состояние STOPPED
     * 
     * CONTRACT:
     * INPUTS: Нет
     * OUTPUTS: void
     * SIDE_EFFECTS: Изменение состояния на STOPPED
     * TEST_CONDITIONS_SUCCESS_CRITERIA: Плагин переходит в состояние STOPPED
     */
    virtual void stop();
    
    /**
     * @brief Приостановка плагина
     * @details Переводит плагин в состояние PAUSED
     * 
     * CONTRACT:
     * INPUTS: Нет
     * OUTPUTS: void
     * SIDE_EFFECTS: Изменение состояния на PAUSED
     * TEST_CONDITIONS_SUCCESS_CRITERIA: Плагин переходит в состояние PAUSED
     */
    virtual void pause();
    
    /**
     * @brief Возобновление работы плагина
     * @details Переводит плагин из состояния PAUSED в ACTIVE
     * 
     * CONTRACT:
     * INPUTS: Нет
     * OUTPUTS: void
     * SIDE_EFFECTS: Изменение состояния на ACTIVE
     * TEST_CONDITIONS_SUCCESS_CRITERIA: Плагин переходит в состояние ACTIVE
     */
    virtual void resume();

    //==============================================================================
    // Utility Methods (Virtual - can override)
    //==============================================================================
    
    /**
     * @brief Проверка работоспособности плагина
     * @return true если плагин работает корректно
     * 
     * CONTRACT:
     * OUTPUTS: bool - статус работоспособности
     * TEST_CONDITIONS_SUCCESS_CRITERIA: Возвращает true если плагин в рабочих состояниях
     */
    virtual bool health_check() const;
    
    /**
     * @brief Получение конфигурации плагина
     * @return PluginConfig Текущая конфигурация
     * 
     * CONTRACT:
     * OUTPUTS: PluginConfig - текущая конфигурация плагина
     * TEST_CONDITIONS_SUCCESS_CRITERIA: Возвращает копию конфигурации
     */
    virtual PluginConfig get_config() const;
    
    /**
     * @brief Установка конфигурации плагина
     * @param config Новая конфигурация
     * 
     * CONTRACT:
     * INPUTS: const PluginConfig& config - новая конфигурация
     * OUTPUTS: void
     * SIDE_EFFECTS: Изменение внутренней конфигурации
     * TEST_CONDITIONS_SUCCESS_CRITERIA: Конфигурация должна быть применена
     */
    virtual void set_config(const PluginConfig& config);

protected:
    //==============================================================================
    // Protected Members
    //==============================================================================
    
    /**
     * @brief Защищённый конструктор
     * @details Доступен только для наследников
     */
    IPlugin() = default;
    
    /**
     * @brief Атомарное состояние плагина
     */
    std::atomic<PluginState> m_state;
    
    /**
     * @brief Конфигурация плагина
     */
    PluginConfig m_config;
    
    /**
     * @brief Мьютекс для защиты доступа
     */
    mutable std::shared_mutex m_mutex;
};

//==============================================================================
// Type Definitions
//==============================================================================
/** @brief Умный указатель на плагин */
using PluginPtr = std::shared_ptr<IPlugin>;

/** @brief Слабый указатель на плагин */
using WeakPluginPtr = std::weak_ptr<IPlugin>;

/** @brief Функция-фабрика для создания плагинов */
using PluginFactory = std::function<PluginPtr()>;

//==============================================================================
// PluginLogger - Логгер для плагинов
//==============================================================================
/**
 * @class PluginLogger
 * @brief Класс для логирования событий плагинов.
 * 
 * @details
 * Обеспечивает централизованное логирование с записью в файл app.log.
 * Каждый плагин имеет свой экземпляр логгера с именем плагина.
 * 
 * @note Использует статический файл логов, открываемый в режиме добавления
 * 
 * @see IPlugin
 */
class PluginLogger {
public:
    //==============================================================================
    // Log Level
    //==============================================================================
    /**
     * @enum Level
     * @brief Уровни логирования
     */
    enum class Level {
        DEBUG,      ///< Отладочные сообщения
        INFO,       ///< Информационные сообщения
        WARNING,    ///< Предупреждения
        ERROR,      ///< Ошибки
        CRITICAL    ///< Критические ошибки
    };
    
    //==============================================================================
    // Constructor
    //==============================================================================
    /**
     * @brief Конструктор логгера
     * @param plugin_name Имя плагина для логирования
     */
    explicit PluginLogger(const std::string& plugin_name);
    
    //==============================================================================
    // Logging Methods
    //==============================================================================
    /**
     * @brief Логирование отладочного сообщения
     * @param message Сообщение для логирования
     */
    void debug(const std::string& message) const;
    
    /**
     * @brief Логирование информационного сообщения
     * @param message Сообщение для логирования
     */
    void info(const std::string& message) const;
    
    /**
     * @brief Логирование предупреждения
     * @param message Сообщение для логирования
     */
    void warning(const std::string& message) const;
    
    /**
     * @brief Логирование ошибки
     * @param message Сообщение для логирования
     */
    void error(const std::string& message) const;
    
    /**
     * @brief Логирование критической ошибки
     * @param message Сообщение для логирования
     */
    void critical(const std::string& message) const;
    
    /**
     * @brief Универсальный метод логирования
     * @param level Уровень логирования
     * @param message Сообщение для логирования
     */
    void log(Level level, const std::string& message) const;

private:
    //==============================================================================
    // Private Members
    //==============================================================================
    std::string m_plugin_name;  ///< Имя плагина
    
    //==============================================================================
    // Private Methods
    //==============================================================================
    /**
     * @brief Получение ссылки на файл логов
     * @return Ссылка на файл логов
     */
    static std::ofstream& get_log_file();
    
    /**
     * @brief Преобразование уровня в строку
     * @param level Уровень логирования
     * @return Строковое представление
     */
    static std::string level_to_string(Level level);
    
    /**
     * @brief Получение текущей временной метки
     * @return Временная метка в формате ISO
     */
    static std::string current_timestamp();
};

//==============================================================================
// Include fstream for ofstream
//==============================================================================
#include <fstream>

//==============================================================================
// BasePlugin - Базовая реализация плагина
//==============================================================================
/**
 * @class BasePlugin
 * @brief Базовая реализация плагина с общей функциональностью.
 * 
 * @details
 * Предоставляет базовую реализацию интерфейса IPlugin с:
 * - Управлением состоянием
 * - Логированием
 * - Конфигурацией
 * - Проверкой работоспособности
 * 
 * Наследники должны реализовать:
 * - initialize_impl(): Специфичная инициализация
 * - shutdown_impl(): Специфичное завершение
 * - on_update_impl(): Специфичная обработка обновлений
 * 
 * @see IPlugin
 * @see PluginLogger
 * 
 * @example
 * @code
 * class MyPlugin : public BasePlugin {
 * protected:
 *     void initialize_impl() override {
 *         // Инициализация
 *     }
 *     
 *     void shutdown_impl() override {
 *         // Завершение
 *     }
 *     
 *     void on_update_impl(const UpdateContext& context) override {
 *         // Обработка обновления
 *     }
 * };
 * @endcode
 */
class BasePlugin : public IPlugin {
public:
    //==============================================================================
    // Constructor / Destructor
    //==============================================================================
    /**
     * @brief Конструктор базового плагина
     * @param info Информация о плагине
     * @param config Конфигурация плагина
     */
    explicit BasePlugin(
        const PluginInfo& info,
        const PluginConfig& config = PluginConfig()
    );
    
    /**
     * @brief Виртуальный деструктор
     */
    virtual ~BasePlugin();

    //==============================================================================
    // IPlugin Implementation
    //==============================================================================
    void initialize() override;
    void shutdown() override;
    PluginInfo get_info() const override;
    PluginState get_state() const override;
    void on_update(const UpdateContext& context) override;
    void on_metrics_update(const PluginMetrics& metrics) override;
    void on_match_found(const MatchList& matches, int iteration) override;
    void on_start(const std::string& selected_list_path) override;
    void on_finish(const PluginMetrics& final_metrics) override;
    void on_reset() override;
    void start() override;
    void stop() override;
    void pause() override;
    void resume() override;
    bool health_check() const override;
    PluginConfig get_config() const override;
    void set_config(const PluginConfig& config) override;

protected:
    //==============================================================================
    // Abstract Methods (must implement)
    //==============================================================================
    /**
     * @brief Специфичная инициализация плагина
     * @details Вызывается из initialize() после базовой инициализации
     */
    virtual void initialize_impl() = 0;
    
    /**
     * @brief Специфичное завершение работы плагина
     * @details Вызывается из shutdown() перед базовым завершением
     */
    virtual void shutdown_impl() = 0;
    
    /**
     * @brief Специфичная обработка обновления
     * @param context Контекст обновления
     * @details Вызывается из on_update() после базовой обработки
     */
    virtual void on_update_impl(const UpdateContext& context) = 0;

    //==============================================================================
    // Protected Members
    //==============================================================================
    PluginInfo m_info;           ///< Информация о плагине
    PluginLogger m_logger;        ///< Логгер плагина
    
    /**
     * @brief Установка состояния плагина
     * @param state Новое состояние
     */
    void set_state(PluginState state);

private:
    //==============================================================================
    // Private Members
    //==============================================================================
    bool m_initialized;          ///< Флаг инициализации
};

//==============================================================================
// PluginManager - Менеджер плагинов
//==============================================================================
/**
 * @class PluginManager
 * @brief Класс для управления жизненным циклом всех плагинов.
 * 
 * @details
 * Обеспечивает:
 * - Регистрацию и удаление плагинов
 * - Управление жизненным циклом всех плагинов
 * - Dependency injection (установка внешних зависимостей)
 * - Thread-safe доступ к плагинам
 * 
 * Реализует паттерн Singleton для глобального доступа.
 * 
 * @invariant Все операции должны быть thread-safe
 * @invariant Плагины инициализируются в порядке приоритета
 * 
 * @see IPlugin
 * @see PluginFactory
 * 
 * @example
 * @code
 * PluginManager& manager = PluginManager::instance();
 * manager.register_plugin("my_plugin", []() {
 *     return std::make_shared<MyPlugin>();
 * });
 * manager.initialize_all();
 * manager.notify_all_metric_update(metrics);
 * @endcode
 */
class PluginManager {
public:
    //==============================================================================
    // Singleton
    //==============================================================================
    /**
     * @brief Получение единственного экземпляра менеджера
     * @return Ссылка на экземпляр менеджера
     */
    static PluginManager& instance();
    
    //==============================================================================
    // Plugin Registration
    //==============================================================================
    /**
     * @brief Регистрация плагина
     * @param plugin Умный указатель на плагин
     * @return true если плагин успешно зарегистрирован
     */
    bool register_plugin(PluginPtr plugin);
    
    /**
     * @brief Регистрация фабрики плагинов
     * @param plugin_name Имя плагина
     * @param factory Функция-фабрика для создания плагина
     * @return true если фабрика успешно зарегистрирована
     */
    bool register_factory(const std::string& plugin_name, PluginFactory factory);
    
    /**
     * @brief Удаление плагина по имени
     * @param plugin_name Имя плагина
     * @return true если плагин успешно удалён
     */
    bool unregister_plugin(const std::string& plugin_name);
    
    /**
     * @brief Получение плагина по имени
     * @param plugin_name Имя плагина
     * @return Умный указатель на плагин или nullptr
     */
    PluginPtr get_plugin(const std::string& plugin_name) const;
    
    /**
     * @brief Получение всех плагинов
     * @return Вектор указателей на плагины (отсортированных по приоритету)
     */
    std::vector<PluginPtr> get_all_plugins() const;
    
    /**
     * @brief Получение только включённых плагинов
     * @return Вектор указателей на плагины
     */
    std::vector<PluginPtr> get_enabled_plugins() const;
    
    /**
     * @brief Проверка наличия плагина
     * @param plugin_name Имя плагина
     * @return true если плагин зарегистрирован
     */
    bool has_plugin(const std::string& plugin_name) const;
    
    /**
     * @brief Получение количества плагинов
     * @return Количество зарегистрированных плагинов
     */
    size_t count() const;
    
    /**
     * @brief Очистка всех плагинов
     */
    void clear();

    //==============================================================================
    // Lifecycle Management
    //==============================================================================
    /**
     * @brief Инициализация всех зарегистрированных плагинов
     * @details Инициализирует плагины в порядке приоритета
     */
    void initialize_all();
    
    /**
     * @brief Завершение работы всех плагинов
     */
    void shutdown_all();
    
    /**
     * @brief Запуск всех плагинов
     */
    void start_all();
    
    /**
     * @brief Остановка всех плагинов
     */
    void stop_all();
    
    /**
     * @brief Приостановка всех плагинов
     */
    void pause_all();
    
    /**
     * @brief Возобновление всех плагинов
     */
    void resume_all();
    
    /**
     * @brief Сброс всех плагинов
     */
    void reset_all();

    //==============================================================================
    // Notification Methods
    //==============================================================================
    /**
     * @brief Уведомление всех плагинов об обновлении метрик
     * @param metrics Словарь метрик
     */
    void notify_all_metric_update(const PluginMetrics& metrics);
    
    /**
     * @brief Уведомление всех плагинов об обновлении
     * @param context Контекст обновления
     */
    void notify_all_update(const UpdateContext& context);
    
    /**
     * @brief Уведомление всех плагинов о запуске генератора
     * @param selected_list_path Путь к списку адресов
     */
    void notify_all_start(const std::string& selected_list_path);
    
    /**
     * @brief Уведомление всех плагинов о завершении генерации
     * @param final_metrics Финальные метрики
     */
    void notify_all_finish(const PluginMetrics& final_metrics);
    
    /**
     * @brief Уведомление всех плагинов о сбросе
     */
    void notify_all_reset();
    
    /**
     * @brief Уведомление всех плагинов о найденных совпадениях
     * @param matches Список совпадений
     * @param iteration Номер итерации
     */
    void notify_all_match_found(const MatchList& matches, int iteration);

    //==============================================================================
    // Dependency Injection
    //==============================================================================
    /**
     * @brief Установка хранилища метрик
     * @param metrics_store Умный указатель на хранилище метрик
     * @tparam T Тип хранилища метрик
     */
    template<typename T>
    void set_metrics_store(std::shared_ptr<T> metrics_store);
    
    /**
     * @brief Установка парсера логов
     * @param log_parser Умный указатель на парсер логов
     * @tparam T Тип парсера логов
     */
    template<typename T>
    void set_log_parser(std::shared_ptr<T> log_parser);

    //==============================================================================
    // Health Check
    //==============================================================================
    /**
     * @brief Проверка работоспособности всех плагинов
     * @return true если все плагины работают корректно
     */
    bool health_check_all() const;

private:
    //==============================================================================
    // Constructor / Destructor
    //==============================================================================
    PluginManager() = default;
    ~PluginManager() = default;
    
    //==============================================================================
    // Delete Copy/Move
    //==============================================================================
    PluginManager(const PluginManager&) = delete;
    PluginManager& operator=(const PluginManager&) = delete;
    PluginManager(PluginManager&&) = delete;
    PluginManager& operator=(PluginManager&&) = delete;

    //==============================================================================
    // Private Members
    //==============================================================================
    std::unordered_map<std::string, PluginPtr> m_plugins;           ///< Коллекция плагинов
    std::unordered_map<std::string, PluginFactory> m_factories;     ///< Фабрики плагинов
    mutable std::shared_mutex m_mutex;                              ///< Мьютекс для thread-safety
    
    //==============================================================================
    // Dependency Injection Pointers
    //==============================================================================
    std::any m_metrics_store;   ///< Хранилище метрик (any для универсальности)
    std::any m_log_parser;      ///< Парсер логов (any для универсальности)
};

//==============================================================================
// Template Implementations
//==============================================================================

// START_FUNCTION_PluginManager_set_metrics_store
// START_CONTRACT:
// PURPOSE: Установка хранилища метрик для dependency injection
// INPUTS: metrics_store - умный указатель на хранилище метрик
// OUTPUTS: void
// KEYWORDS: [CONCEPT(8): DependencyInjection; DOMAIN(7): Metrics]
// END_CONTRACT
template<typename T>
void PluginManager::set_metrics_store(std::shared_ptr<T> metrics_store) {
    std::unique_lock lock(m_mutex);
    m_metrics_store = metrics_store;
}
// END_FUNCTION_PluginManager_set_metrics_store

// START_FUNCTION_PluginManager_set_log_parser
// START_CONTRACT:
// PURPOSE: Установка парсера логов для dependency injection
// INPUTS: log_parser - умный указатель на парсер логов
// OUTPUTS: void
// KEYWORDS: [CONCEPT(8): DependencyInjection; DOMAIN(7): Logging]
// END_CONTRACT
template<typename T>
void PluginManager::set_log_parser(std::shared_ptr<T> log_parser) {
    std::unique_lock lock(m_mutex);
    m_log_parser = log_parser;
}
// END_FUNCTION_PluginManager_set_log_parser

//==============================================================================
// PriorityConverter - Конвертер приоритетов
//==============================================================================
/**
 * @class PriorityConverter
 * @brief Класс для преобразования приоритетов
 */
class PriorityConverter {
public:
    /**
     * @brief Преобразование строки в приоритет
     * @param str Строка с именем приоритета
     * @return Priority соответствующий приоритет
     */
    static int from_string(const std::string& str);
    
    /**
     * @brief Преобразование приоритета в строку
     * @param priority Числовое значение приоритета
     * @return Строковое представление
     */
    static std::string to_string(int priority);
};

#endif // PLUGIN_BASE_HPP
