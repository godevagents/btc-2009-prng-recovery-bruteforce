// FILE: src/monitor_cpp/core/metrics.hpp
// VERSION: 1.0.0
#ifndef METRICS_HPP
#define METRICS_HPP

//==============================================================================
// Standard Library Headers
//==============================================================================
#include <chrono>
#include <deque>
#include <functional>
#include <map>
#include <memory>
#include <mutex>
#include <shared_mutex>
#include <string>
#include <thread>
#include <atomic>
#include <variant>
#include <vector>
#include <optional>
#include <algorithm>
#include <cmath>
#include <sstream>

//==============================================================================
// Forward Declarations
//==============================================================================
class MetricsStore;
class MetricsCollector;

//==============================================================================
// Type Aliases
//==============================================================================
using MetricValue = std::variant<int64_t, double, std::string, std::map<std::string, MetricValue>>;
using MetricsMap = std::map<std::string, MetricValue>;
using MetricCallback = std::function<void(const MetricsMap&)>;
using CollectorFunction = std::function<MetricsMap()>;

//==============================================================================
// MetricType - Перечисление типов метрик
//==============================================================================
/**
 * @class MetricType
 * @brief Перечисление типов метрик для классификации данных мониторинга.
 * 
 * @details
 * Типы метрик:
 * - COUNTER: счётчик (монотонно возрастающее значение)
 * - GAUGE: значение может увеличиваться и уменьшаться
 * - RATE: скорость изменения (производная метрика)
 * - TIMESTAMP: временная метка
 * 
 * @note Используется для типизации метрик и определения способа их обработки.
 * 
 * @see MetricsStore
 * @see MetricEntry
 */
enum class MetricType {
    COUNTER,     ///< Счётчик - монотонно возрастающее значение
    GAUGE,       ///< Gauge - значение может увеличиваться и уменьшаться
    RATE,        ///< Rate - скорость изменения (производная метрика)
    TIMESTAMP    ///< Timestamp - временная метка
};

//==============================================================================
// MetricEntry - Запись истории метрики
//==============================================================================
/**
 * @struct MetricEntry
 * @brief Структура данных для записи истории метрики с временной меткой и метаданными.
 * 
 * @details
 * Представляет собой одну запись в истории изменения метрики.
 * Содержит timestamp записи, значение метрики и дополнительные метаданные.
 * 
 * @attribute timestamp Время записи (steady_clock time_point)
 * @attribute value Значение метрики (variant поддерживает int64_t, double, string, nested dict)
 * @attribute metadata Дополнительные метаданные (например, previous_value)
 * 
 * @invariant timestamp всегда валиден и представляет время в прошлом или настоящем
 * @invariant value не может быть пустым (должен содержать одно из значений variant)
 * 
 * @see MetricsStore
 * @see MetricType
 */
struct MetricEntry {
    /** @brief Время записи */
    std::chrono::steady_clock::time_point timestamp;
    
    /** @brief Значение метрики (поддерживает int64_t, double, string, nested dict) */
    MetricValue value;
    
    /** @brief Дополнительные метаданные (previous_value и др.) */
    std::map<std::string, MetricValue> metadata;
    
    /**
     * @brief Конструктор по умолчанию
     * @details Инициализирует timestamp текущим временем, value - пустым
     */
    MetricEntry();
    
    /**
     * @brief Конструктор с значением
     * @param val Значение метрики
     */
    MetricEntry(const MetricValue& val);
    
    /**
     * @brief Конструктор с значением и метаданными
     * @param val Значение метрики
     * @param meta Метаданные записи
     */
    MetricEntry(const MetricValue& val, const std::map<std::string, MetricValue>& meta);
};

//==============================================================================
// MetricsStore - Центральное хранилище метрик
//==============================================================================
/**
 * @class MetricsStore
 * @brief Центральное хранилище метрик процесса генерации кошельков Bitcoin.
 * 
 * @details
 * Управляет текущими значениями метрик, полной историей изменений
 * и вычислением производных показателей (скорости, статистика).
 * Обеспечивает thread-safe доступ и механизм подписки на обновления.
 * 
 * @attribute max_history_size_ Максимальный размер истории для каждой метрики
 * @attribute mutex_ Блокировка для thread-safety (shared_mutex)
 * @attribute current_metrics_ Текущие значения метрик
 * @attribute history_ История метрик (deque для эффективного push/pop)
 * @attribute subscribers_ Список подписчиков на обновления
 * @attribute update_count_ Счётчик обновлений (atomic)
 * @attribute start_time_ Время старта хранилища
 * 
 * @invariant max_history_size_ > 0
 * @invariant current_metrics_ всегда содержит стандартные метрики после инициализации
 * @invariant history_ содержит записи только для метрик из current_metrics_
 * 
 * @note Использует shared_mutex для оптимального множественного чтения
 * @note Подписчики вызываются синхронно при update(), ошибки логируются
 * 
 * @see MetricEntry
 * @see MetricsCollector
 * @see MetricCallback
 * 
 * @example
 * @code
 * auto store = std::make_shared<MetricsStore>(10000);
 * store->update({{"iteration_count", int64_t(1000)}});
 * auto current = store->get_current();
 * auto history = store->get_history("iteration_count", 100);
 * double rate = store->compute_rate("iteration_count", 60);
 * @endcode
 */
class MetricsStore {
public:
    //==============================================================================
    // Constants - Стандартные имена метрик
    //==============================================================================
    /** @brief Количество итераций */
    static constexpr const char* ITERATION_COUNT = "iteration_count";
    /** @brief Количество совпадений */
    static constexpr const char* MATCH_COUNT = "match_count";
    /** @brief Количество кошельков */
    static constexpr const char* WALLET_COUNT = "wallet_count";
    /** @brief Прошедшее время */
    static constexpr const char* ELAPSED_TIME = "elapsed_time";
    /** @brief Данные энтропии */
    static constexpr const char* ENTROPY_DATA = "entropy_data";
    /** @brief Извлечённые адреса */
    static constexpr const char* ADDRESSES_EXTRACTED = "addresses_extracted";
    /** @brief Найденные совпадения */
    static constexpr const char* MATCHES_FOUND = "matches_found";
    /** @brief Итераций в секунду */
    static constexpr const char* ITERATIONS_PER_SECOND = "iterations_per_second";
    /** @brief Кошельков в секунду */
    static constexpr const char* WALLETS_PER_SECOND = "wallets_per_second";

    //==============================================================================
    // Public Types
    //==============================================================================
    /**
     * @struct Snapshot
     * @brief Атомарный снимок всех метрик в текущий момент времени.
     */
    struct Snapshot {
        MetricsMap current;                                              ///< Текущие значения
        std::map<std::string, std::vector<MetricEntry>> history;       ///< История всех метрик
        std::chrono::steady_clock::time_point timestamp;               ///< Время снимка
        uint64_t update_count;                                          ///< Счётчик обновлений
    };

    //==============================================================================
    // Constructors / Destructor
    //==============================================================================
    /**
     * @brief Конструктор хранилища метрик
     * @param max_history_size Максимальное количество записей истории для каждой метрики
     * @details Инициализирует стандартные метрики нулевыми значениями
     */
    explicit MetricsStore(size_t max_history_size = 10000);
    
    /** @brief Деструктор - обеспечивает корректное завершение */
    ~MetricsStore();

    //==============================================================================
    // Main Operations - Основные операции
    //==============================================================================
    /**
     * @brief Обновление текущих метрик с записью в историю
     * @param metrics Словарь метрик для обновления {name: value, ...}
     * @details
     * - Атомарная операция с эксклюзивной блокировкой
     * - Обновляет текущие значения в current_metrics_
     * - Добавляет записи в историю для каждой метрики
     * - Уведомляет подписчиков об изменении
     * - Обрезает историю при превышении max_history_size_
     * 
     * @throw Никаких исключений (errors логируются)
     */
    void update(const MetricsMap& metrics);
    
    /**
     * @brief Получение текущих метрик с метаданными
     * @return Копия словаря текущих метрик со значениями
     * @details
     * - Возвращает копию, внешние изменения не влияют на внутреннее состояние
     * - Добавляет _timestamp (текущее время) и _update_count
     * - Использует shared lock для множественного чтения
     */
    MetricsMap get_current() const;
    
    /**
     * @brief Получение истории метрики
     * @param metric_name Имя метрики для получения истории
     * @param limit Максимальное количество записей (nullopt = все)
     * @return Вектор записей истории (от старых к новым)
     * @details Использует shared lock
     */
    std::vector<MetricEntry> get_history(
        const std::string& metric_name,
        std::optional<size_t> limit = std::nullopt
    ) const;

    //==============================================================================
    // Computations - Вычисления
    //==============================================================================
    /**
     * @brief Вычисление скорости изменения метрики
     * @param metric_name Имя метрики для вычисления скорости
     * @param window_seconds Временное окно в секундах (по умолчанию 60)
     * @return Скорость изменения (единиц в секунду)
     * @details
     * - В истории должно быть не менее 2 записей в окне
     * - Фильтрует записи в пределах window_seconds
     * - Вычисляет rate = (last_value - first_value) / time_diff
     * - Возвращает 0.0 при недостаточных данных
     */
    double compute_rate(const std::string& metric_name, int window_seconds = 60) const;

    //==============================================================================
    // Summary - Сводка
    //==============================================================================
    /**
     * @brief Получение полной сводки всех метрик
     * @return Словарь со сводкой метрик
     * @details Включает:
     * - current: текущие значения
     * - rates: скорости (iterations_per_second, wallets_per_second)
     * - stats: статистика по истории (min, max, avg, count)
     * - metadata: uptime, update_count, history_size
     */
    MetricsMap get_summary() const;

    //==============================================================================
    // Management - Управление метриками
    //==============================================================================
    /** @brief Сброс всех метрик в начальное состояние */
    void reset();
    
    /**
     * @brief Сброс конкретной метрики
     * @param metric_name Имя метрики для сброса
     */
    void reset_metric(const std::string& metric_name);
    
    /**
     * @brief Получение списка всех имён зарегистрированных метрик
     * @return Вектор имён метрик
     */
    std::vector<std::string> get_metric_names() const;

    //==============================================================================
    // Subscription - Подписка на обновления
    //==============================================================================
    /**
     * @brief Подписка на обновления метрик
     * @param callback Функция обратного вызова (вызывается при каждом update)
     * @details
     * - Добавляет callback в список подписчиков
     * - Callback получает копию текущих метрик
     * - Ошибки в callback логируются, но не прерывают обновление
     */
    void subscribe(MetricCallback callback);
    
    /**
     * @brief Отписка от обновлений метрик
     * @param callback Функция обратного вызова для удаления
     */
    void unsubscribe(MetricCallback callback);

    //==============================================================================
    // Snapshot - Атомарный снимок
    //==============================================================================
    /**
     * @brief Получение атомарного снимка всех метрик
     * @return Snapshot с полным состоянием хранилища
     * @details
     * - Атомарная операция (единый lock на всё)
     * - Возвращает копию текущих метрик и всей истории
     */
    Snapshot get_snapshot() const;

private:
    //==============================================================================
    // Private Methods
    //==============================================================================
    /** @brief Инициализация стандартных метрик нулевыми значениями */
    void init_default_metrics();

    //==============================================================================
    // Private Members
    //==============================================================================
    size_t max_history_size_;                                           ///< Макс. размер истории
    mutable std::shared_mutex mutex_;                                   ///< Блокировка thread-safety
    MetricsMap current_metrics_;                                         ///< Текущие значения
    std::map<std::string, std::deque<MetricEntry>> history_;            ///< История метрик
    std::vector<MetricCallback> subscribers_;                           ///< Подписчики
    std::atomic<uint64_t> update_count_;                                 ///< Счётчик обновлений
    std::chrono::steady_clock::time_point start_time_;                  ///< Время старта
};

//==============================================================================
// MetricsCollector - Сборщик метрик
//==============================================================================
/**
 * @class MetricsCollector
 * @brief Класс для сбора метрик из различных источников с фонвым потоком.
 * 
 * @details
 * Управляет источниками метрик, запускает и останавливает сбор,
 * обеспечивает интеграцию с MetricsStore.
 * 
 * @attribute metrics_store_ Ссылка на хранилище метрик
 * @attribute sources_ Источники метрик (имя -> функция сбора)
 * @attribute collection_interval_ Интервал сбора метрик в секундах
 * @attribute is_collecting_ Флаг активности сбора (atomic)
 * @attribute collection_thread_ Поток сбора метрик
 * @attribute stop_flag_ Флаг остановки (atomic)
 * @attribute sources_mutex_ Mutex для защиты sources_
 * 
 * @invariant metrics_store_ всегда валиден (shared_ptr)
 * @invariant collection_interval_ > 0
 * 
 * @note Деструктор автоматически останавливает сбор (RAII)
 * @note Источники вызываются в порядке добавления
 * @note Ошибки в источниках логируются, но не останавливают сбор
 * 
 * @see MetricsStore
 * @see CollectorFunction
 * 
 * @example
 * @code
 * auto store = std::make_shared<MetricsStore>();
 * auto collector = std::make_shared<MetricsCollector>(store, 1.0);
 * collector->add_source("system", []() {
 *     return MetricsMap{{"cpu", 45.2}};
 * });
 * collector->start();
 * // ... работа ...
 * collector->stop();
 * @endcode
 */
class MetricsCollector {
public:
    //==============================================================================
    // Constructors / Destructor
    //==============================================================================
    /**
     * @brief Конструктор сборщика метрик
     * @param store Хранилище для собранных метрик
     * @param collection_interval Интервал сбора в секундах (по умолчанию 1.0)
     */
    explicit MetricsCollector(
        std::shared_ptr<MetricsStore> store,
        double collection_interval = 1.0
    );
    
    /** @brief Деструктор - автоматически останавливает сбор */
    ~MetricsCollector();

    //==============================================================================
    // Source Management - Управление источниками
    //==============================================================================
    /**
     * @brief Добавить источник метрик
     * @param name Уникальное имя источника
     * @param collector_fn Функция, возвращающая словарь метрик
     * @details
     * - Перезаписывает существующий источник с тем же именем
     * - Функция должна возвращать MetricsMap
     */
    void add_source(const std::string& name, CollectorFunction collector_fn);
    
    /**
     * @brief Удалить источник метрик
     * @param name Имя источника для удаления
     */
    void remove_source(const std::string& name);

    //==============================================================================
    // Collection Control - Управление сбором
    //==============================================================================
    /** @brief Начать фоновый сбор метрик */
    void start();
    
    /** @brief Остановить фоновый сбор метрик */
    void stop();
    
    /**
     * @brief Принудительный сбор метрик
     * @details
     * - Собирает метрики со всех источников
     * - Обновляет хранилище собранными данными
     * - Ошибки в источниках логируются
     */
    void collect();

    //==============================================================================
    // Accessors - Получение данных
    //==============================================================================
    /** @brief Получить текущие метрики из хранилища */
    MetricsMap get_current_metrics() const;
    
    /** @brief Проверка состояния сбора метрик */
    bool is_collecting() const;

private:
    //==============================================================================
    // Private Methods
    //==============================================================================
    /** @brief Внутренний цикл сбора метрик */
    void collection_loop();

    //==============================================================================
    // Private Members
    //==============================================================================
    std::shared_ptr<MetricsStore> metrics_store_;                       ///< Хранилище метрик
    std::map<std::string, CollectorFunction> sources_;                 ///< Источники метрик
    double collection_interval_;                                         ///< Интервал сбора
    std::atomic<bool> is_collecting_;                                   ///< Флаг активности
    std::thread collection_thread_;                                      ///< Поток сбора
    std::atomic<bool> stop_flag_;                                        ///< Флаг остановки
    mutable std::mutex sources_mutex_;                                   ///< Mutex для sources_
};

#endif // METRICS_HPP
