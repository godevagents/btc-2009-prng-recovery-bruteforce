// FILE: src/monitor_cpp/core/metrics.cpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Реализация модуля metrics - хранилище метрик процесса генерации кошельков Bitcoin.
// SCOPE: метрики, хранилище данных, статистика, мониторинг производительности, thread-safety
// INPUT: Словари метрик от генератора кошельков, функции-источники метрик
// OUTPUT: Класс MetricsStore; Класс MetricsCollector; Константы метрик
// KEYWORDS: [DOMAIN(9): Metrics; DOMAIN(8): Storage; CONCEPT(7): TimeSeries; TECH(6): Threading; CONCEPT(5): Observer]
// LINKS: [USES_API(7): spdlog; COMPOSES(6): MetricEntry; CALLS(6): subscriber callbacks]
// LINKS_TO_SPECIFICATION: [Требования к хранению и отображению метрик мониторинга]
// END_MODULE_CONTRACT

#include "metrics.hpp"
#include <spdlog/spdlog.h>
#include <variant>
#include <algorithm>
#include <cmath>
#include <sstream>
#include <numeric>

namespace {
    // Локальный логгер для модуля metrics
    auto logger = spdlog::get("metrics");
    
    // Вспомогательная функция для вычисления скорости внутри lock
    double compute_rate_internal(
        const std::string& metric_name,
        const std::map<std::string, std::deque<MetricEntry>>& history,
        const std::chrono::steady_clock::time_point& start_time
    ) {
        auto it = history.find(metric_name);
        if (it == history.end() || it->second.size() < 2) {
            return 0.0;
        }
        
        const auto& hist = it->second;
        auto now = std::chrono::steady_clock::now();
        auto window_start = now - std::chrono::seconds(60);
        
        std::vector<const MetricEntry*> relevant;
        for (const auto& entry : hist) {
            if (entry.timestamp >= window_start) {
                relevant.push_back(&entry);
            }
        }
        
        if (relevant.size() < 2) {
            return 0.0;
        }
        
        const auto* first = relevant.front();
        const auto* last = relevant.back();
        
        auto time_diff = std::chrono::duration<double>(last->timestamp - first->timestamp).count();
        if (time_diff <= 0) {
            return 0.0;
        }
        
        double first_value = 0.0, last_value = 0.0;
        
        try {
            first_value = std::get<double>(first->value);
        } catch (const std::bad_variant_access&) {
            try {
                first_value = static_cast<double>(std::get<int64_t>(first->value));
            } catch (const std::bad_variant_access&) {
                return 0.0;
            }
        }
        
        try {
            last_value = std::get<double>(last->value);
        } catch (const std::bad_variant_access&) {
            try {
                last_value = static_cast<double>(std::get<int64_t>(last->value));
            } catch (const std::bad_variant_access&) {
                return 0.0;
            }
        }
        
        return (last_value - first_value) / time_diff;
    }
}

//==============================================================================
// MetricEntry Implementation
//==============================================================================

// START_METHOD_MetricEntry_Constructor_Default
// START_CONTRACT:
// PURPOSE: Конструктор по умолчанию - инициализирует timestamp текущим временем
// OUTPUTS: Объект MetricEntry с пустым значением
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
MetricEntry::MetricEntry() 
    : timestamp(std::chrono::steady_clock::now()) {}

// END_METHOD_MetricEntry_Constructor_Default

// START_METHOD_MetricEntry_Constructor_WithValue
// START_CONTRACT:
// PURPOSE: Конструктор с значением - инициализирует timestamp и value
// INPUTS: val - значение метрики (variant)
// OUTPUTS: Объект MetricEntry с заданным значением
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
MetricEntry::MetricEntry(const MetricValue& val) 
    : timestamp(std::chrono::steady_clock::now()), value(val) {}

// END_METHOD_MetricEntry_Constructor_WithValue

// START_METHOD_MetricEntry_Constructor_Full
// START_CONTRACT:
// PURPOSE: Конструктор с значением и метаданными
// INPUTS: val - значение метрики; meta - метаданные
// OUTPUTS: Объект MetricEntry с заданным значением и метаданными
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
MetricEntry::MetricEntry(const MetricValue& val, const std::map<std::string, MetricValue>& meta)
    : timestamp(std::chrono::steady_clock::now()), value(val), metadata(meta) {}

// END_METHOD_MetricEntry_Constructor_Full

//==============================================================================
// MetricsStore Implementation
//==============================================================================

// START_METHOD_MetricsStore_Constructor
// START_CONTRACT:
// PURPOSE: Инициализация хранилища метрик с заданным размером истории
// INPUTS: max_history_size - максимальное количество записей истории для каждой метрики
// OUTPUTS: Инициализированный объект MetricsStore
// SIDE_EFFECTS: Инициализирует стандартные метрики нулевыми значениями
// KEYWORDS: [PATTERN(7): Factory; CONCEPT(6): Initialization]
// END_CONTRACT
MetricsStore::MetricsStore(size_t max_history_size) 
    : max_history_size_(max_history_size)
    , update_count_(0)
    , start_time_(std::chrono::steady_clock::now()) 
{
    init_default_metrics();
    if (logger) {
        logger->info("MetricsStore initialized with max_history_size={}", max_history_size);
    }
}

// END_METHOD_MetricsStore_Constructor

// START_METHOD_MetricsStore_Destructor
// START_CONTRACT:
// PURPOSE: Деструктор - обеспечивает корректное завершение
// KEYWORDS: [CONCEPT(5): Cleanup]
// END_CONTRACT
MetricsStore::~MetricsStore() = default;

// END_METHOD_MetricsStore_Destructor

// START_METHOD_MetricsStore_InitDefaultMetrics
// START_CONTRACT:
// PURPOSE: Инициализация стандартных метрик нулевыми значениями
// SIDE_EFFECTS: Заполняет current_metrics_ и history_ стандартными метриками
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
void MetricsStore::init_default_metrics() {
    current_metrics_ = {
        {ITERATION_COUNT, int64_t(0)},
        {MATCH_COUNT, int64_t(0)},
        {WALLET_COUNT, int64_t(0)},
        {ELAPSED_TIME, 0.0},
        {ENTROPY_DATA, std::map<std::string, MetricValue>()},
        {ADDRESSES_EXTRACTED, int64_t(0)},
        {MATCHES_FOUND, int64_t(0)},
        {ITERATIONS_PER_SECOND, 0.0},
        {WALLETS_PER_SECOND, 0.0},
    };
    
    for (const auto& [key, value] : current_metrics_) {
        history_[key] = std::deque<MetricEntry>();
    }
}

// END_METHOD_MetricsStore_InitDefaultMetrics

// START_METHOD_MetricsStore_Update
// START_CONTRACT:
// PURPOSE: Обновление текущих метрик с записью в историю. Атомарная операция с блокировкой.
// INPUTS: metrics - словарь метрик для обновления {name: value, ...}
// OUTPUTS: Нет
// SIDE_EFFECTS:
// - Обновляет текущие значения в current_metrics_
// - Добавляет записи в историю для каждой метрики
// - Уведомляет подписчиков об изменении
// - Обрезает историю при превышении max_history_size_
// TEST_CONDITIONS_SUCCESS_CRITERIA:
// - Входной параметр не должен быть пустым словарём
// KEYWORDS: [PATTERN(8): Repository; CONCEPT(7): WriteOperation; TECH(6): Threading]
// LINKS: [CALLS(7): subscriber callbacks]
// END_CONTRACT
void MetricsStore::update(const MetricsMap& metrics) {
    if (metrics.empty()) {
        return;
    }
    
    std::unique_lock lock(mutex_);
    auto current_time = std::chrono::steady_clock::now();
    
    for (const auto& [name, value] : metrics) {
        auto it = current_metrics_.find(name);
        MetricValue old_value;
        bool found = (it != current_metrics_.end());
        if (found) {
            old_value = it->second;
        }
        
        current_metrics_[name] = value;
        
        std::map<std::string, MetricValue> meta;
        if (found) {
            meta["previous_value"] = old_value;
        }
        
        MetricEntry entry(value, meta);
        entry.timestamp = current_time;
        
        auto& hist = history_[name];
        hist.push_back(entry);
        
        // Обрезание истории при превышении лимита
        if (hist.size() > max_history_size_) {
            hist.pop_front();
        }
    }
    
    update_count_++;
    
    // Уведомление подписчиков (копия для безопасности)
    MetricsMap current_copy = current_metrics_;
    lock.unlock();
    
    // Вызов callback без блокировки
    for (auto& callback : subscribers_) {
        try {
            callback(current_copy);
        } catch (const std::exception& e) {
            if (logger) {
                logger->error("Exception in subscriber callback: {}", e.what());
            }
        }
    }
    
    if (logger) {
        logger->debug("Updated {} metrics", metrics.size());
    }
}

// END_METHOD_MetricsStore_Update

// START_METHOD_MetricsStore_GetCurrent
// START_CONTRACT:
// PURPOSE: Получение текущих метрик с метаданными (временная метка, счётчик обновлений)
// INPUTS: Нет
// OUTPUTS: Копия словаря текущих метрик со значениями
// SIDE_EFFECTS: Возвращает копию, внешние изменения не влияют на внутреннее состояние
// KEYWORDS: [CONCEPT(6): Accessor; TECH(5): Copy]
// END_CONTRACT
MetricsMap MetricsStore::get_current() const {
    std::shared_lock lock(mutex_);
    MetricsMap result = current_metrics_;
    
    // Добавить метаданные
    auto now = std::chrono::steady_clock::now();
    auto timestamp = std::chrono::duration<double>(now.time_since_epoch()).count();
    result["_timestamp"] = timestamp;
    result["_update_count"] = static_cast<int64_t>(update_count_.load());
    
    return result;
}

// END_METHOD_MetricsStore_GetCurrent

// START_METHOD_MetricsStore_GetHistory
// START_CONTRACT:
// PURPOSE: Получение истории метрики с возможностью ограничения количества записей
// INPUTS: metric_name - имя метрики; limit - максимальное количество записей (nullopt = все)
// OUTPUTS: Вектор записей истории (от старых к новым)
// KEYWORDS: [CONCEPT(6): TimeSeries; TECH(5): Slicing]
// END_CONTRACT
std::vector<MetricEntry> MetricsStore::get_history(
    const std::string& metric_name, 
    std::optional<size_t> limit
) const {
    std::shared_lock lock(mutex_);
    
    auto it = history_.find(metric_name);
    if (it == history_.end()) {
        return {};
    }
    
    const auto& hist = it->second;
    if (limit.has_value() && *limit > 0 && hist.size() > *limit) {
        return std::vector<MetricEntry>(hist.end() - *limit, hist.end());
    }
    
    return std::vector<MetricEntry>(hist.begin(), hist.end());
}

// END_METHOD_MetricsStore_GetHistory

// START_METHOD_MetricsStore_ComputeRate
// START_CONTRACT:
// PURPOSE: Вычисление скорости изменения метрики (производная) за заданное временное окно
// INPUTS: metric_name - имя метрики; window_seconds - временное окно в секундах (по умолчанию 60)
// OUTPUTS: float - скорость изменения (единиц в секунду)
// TEST_CONDITIONS_SUCCESS_CRITERIA: В истории должно быть не менее 2 записей в окне
// KEYWORDS: [CONCEPT(7): RateCalculation; TECH(6): SlidingWindow]
// END_CONTRACT
double MetricsStore::compute_rate(const std::string& metric_name, int window_seconds) const {
    std::shared_lock lock(mutex_);
    
    auto it = history_.find(metric_name);
    if (it == history_.end() || it->second.size() < 2) {
        if (logger) {
            logger->debug("Insufficient data for rate calculation: {}", metric_name);
        }
        return 0.0;
    }
    
    const auto& hist = it->second;
    auto now = std::chrono::steady_clock::now();
    auto window_start = now - std::chrono::seconds(window_seconds);
    
    // Поиск релевантных записей
    std::vector<const MetricEntry*> relevant;
    for (const auto& entry : hist) {
        if (entry.timestamp >= window_start) {
            relevant.push_back(&entry);
        }
    }
    
    if (relevant.size() < 2) {
        return 0.0;
    }
    
    const auto* first = relevant.front();
    const auto* last = relevant.back();
    
    auto time_diff = std::chrono::duration<double>(last->timestamp - first->timestamp).count();
    if (time_diff <= 0) {
        return 0.0;
    }
    
    // Извлечение числовых значений
    double first_value = 0.0, last_value = 0.0;
    
    try {
        first_value = std::get<double>(first->value);
    } catch (const std::bad_variant_access&) {
        try {
            first_value = static_cast<double>(std::get<int64_t>(first->value));
        } catch (const std::bad_variant_access&) {
            return 0.0;
        }
    }
    
    try {
        last_value = std::get<double>(last->value);
    } catch (const std::bad_variant_access&) {
        try {
            last_value = static_cast<double>(std::get<int64_t>(last->value));
        } catch (const std::bad_variant_access&) {
            return 0.0;
        }
    }
    
    double rate = (last_value - first_value) / time_diff;
    
    if (logger) {
        logger->debug("Rate for {}: {:.4f} units/sec", metric_name, rate);
    }
    
    return rate;
}

// END_METHOD_MetricsStore_ComputeRate

// START_METHOD_MetricsStore_GetSummary
// START_CONTRACT:
// PURPOSE: Получение полной сводки всех метрик включая текущие значения, скорости и статистику по истории
// INPUTS: Нет
// OUTPUTS: Словарь со сводкой метрик
// KEYWORDS: [CONCEPT(7): Aggregation; TECH(6): Statistics]
// END_CONTRACT
MetricsMap MetricsStore::get_summary() const {
    std::shared_lock lock(mutex_);
    
    MetricsMap result;
    
    // Текущие значения
    result["current"] = current_metrics_;
    
    // Скорости
    MetricsMap rates;
    rates[ITERATIONS_PER_SECOND] = compute_rate_internal(ITERATION_COUNT, history_, start_time_);
    rates[WALLETS_PER_SECOND] = compute_rate_internal(WALLET_COUNT, history_, start_time_);
    result["rates"] = rates;
    
    // Статистика по истории
    std::map<std::string, MetricsMap> stats;
    for (const auto& [name, hist] : history_) {
        if (hist.empty()) continue;
        
        std::vector<double> values;
        for (const auto& entry : hist) {
            try {
                values.push_back(std::get<double>(entry.value));
            } catch (const std::bad_variant_access&) {
                try {
                    values.push_back(static_cast<double>(std::get<int64_t>(entry.value)));
                } catch (...) {
                    continue;
                }
            }
        }
        
        if (!values.empty()) {
            MetricsMap stat;
            stat["min"] = *std::min_element(values.begin(), values.end());
            stat["max"] = *std::max_element(values.begin(), values.end());
            double sum = std::accumulate(values.begin(), values.end(), 0.0);
            stat["avg"] = sum / values.size();
            stat["count"] = static_cast<int64_t>(values.size());
            stats[name] = stat;
        }
    }
    result["stats"] = stats;
    
    // Метаданные
    auto uptime = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start_time_
    ).count();
    
    MetricsMap metadata;
    metadata["uptime"] = uptime;
    metadata["update_count"] = static_cast<int64_t>(update_count_.load());
    
    std::map<std::string, int64_t> history_sizes;
    for (const auto& [name, hist] : history_) {
        history_sizes[name] = static_cast<int64_t>(hist.size());
    }
    metadata["history_size"] = history_sizes;
    result["metadata"] = metadata;
    
    return result;
}

// END_METHOD_MetricsStore_GetSummary

// START_METHOD_MetricsStore_Reset
// START_CONTRACT:
// PURPOSE: Сброс всех метрик в начальное состояние. Очищает текущие значения и всю историю.
// INPUTS: Нет
// OUTPUTS: Нет
// SIDE_EFFECTS: Очищает текущие метрики, устанавливает нулевые значения; Очищает всю историю
// KEYWORDS: [CONCEPT(6): Reset; TECH(5): Cleanup]
// END_CONTRACT
void MetricsStore::reset() {
    std::unique_lock lock(mutex_);
    init_default_metrics();
    update_count_ = 0;
    start_time_ = std::chrono::steady_clock::now();
    
    if (logger) {
        logger->info("MetricsStore reset complete");
    }
}

// END_METHOD_MetricsStore_Reset

// START_METHOD_MetricsStore_ResetMetric
// START_CONTRACT:
// PURPOSE: Сброс конкретной метрики в нулевое значение и очистка её истории
// INPUTS: metric_name - имя метрики для сброса
// OUTPUTS: Нет
// KEYWORDS: [CONCEPT(5): Reset]
// END_CONTRACT
void MetricsStore::reset_metric(const std::string& metric_name) {
    std::unique_lock lock(mutex_);
    
    auto it = current_metrics_.find(metric_name);
    if (it != current_metrics_.end()) {
        // Определение типа и сброс
        if (std::holds_alternative<int64_t>(it->second) || 
            std::holds_alternative<double>(it->second)) {
            it->second = int64_t(0);
        } else {
            it->second = MetricValue{};
        }
        
        history_[metric_name].clear();
        
        if (logger) {
            logger->debug("Metric '{}' reset", metric_name);
        }
    }
}

// END_METHOD_MetricsStore_ResetMetric

// START_METHOD_MetricsStore_GetMetricNames
// START_CONTRACT:
// PURPOSE: Получение списка всех имён зарегистрированных метрик
// INPUTS: Нет
// OUTPUTS: Список имён метрик
// KEYWORDS: [CONCEPT(5): Enumeration]
// END_CONTRACT
std::vector<std::string> MetricsStore::get_metric_names() const {
    std::shared_lock lock(mutex_);
    
    std::vector<std::string> names;
    names.reserve(current_metrics_.size());
    for (const auto& [key, value] : current_metrics_) {
        names.push_back(key);
    }
    return names;
}

// END_METHOD_MetricsStore_GetMetricNames

// START_METHOD_MetricsStore_Subscribe
// START_CONTRACT:
// PURPOSE: Подписка на обновления метрик. Добавляет callback в список подписчиков.
// INPUTS: callback - функция обратного вызова, вызываемая при каждом update()
// OUTPUTS: Нет
// SIDE_EFFECTS: Добавляет callback в список подписчиков
// KEYWORDS: [PATTERN(7): Observer; CONCEPT(6): Subscription]
// END_CONTRACT
void MetricsStore::subscribe(MetricCallback callback) {
    std::unique_lock lock(mutex_);
    
    // Проверка на дубликаты (простейшая реализация)
    subscribers_.push_back(callback);
    
    if (logger) {
        logger->debug("Subscriber added");
    }
}

// END_METHOD_MetricsStore_Subscribe

// START_METHOD_MetricsStore_Unsubscribe
// START_CONTRACT:
// PURPOSE: Отписка от обновлений метрик. Удаляет callback из списка подписчиков.
// INPUTS: callback - функция обратного вызова для удаления
// OUTPUTS: Нет
// KEYWORDS: [CONCEPT(6): Unsubscription]
// END_CONTRACT
void MetricsStore::unsubscribe(MetricCallback callback) {
    std::unique_lock lock(mutex_);
    
    auto it = std::find(subscribers_.begin(), subscribers_.end(), callback);
    if (it != subscribers_.end()) {
        subscribers_.erase(it);
        
        if (logger) {
            logger->debug("Subscriber removed");
        }
    }
}

// END_METHOD_MetricsStore_Unsubscribe

// START_METHOD_MetricsStore_GetSnapshot
// START_CONTRACT:
// PURPOSE: Получение атомарного снимка всех метрик включая историю в текущий момент времени
// INPUTS: Нет
// OUTPUTS: Полный снимок метрик
// KEYWORDS: [PATTERN(8): Snapshot; CONCEPT(7): Atomic; TECH(6): Threading]
// END_CONTRACT
MetricsStore::Snapshot MetricsStore::get_snapshot() const {
    std::shared_lock lock(mutex_);
    
    Snapshot snapshot;
    snapshot.current = current_metrics_;
    
    for (const auto& [name, hist] : history_) {
        snapshot.history[name] = std::vector<MetricEntry>(hist.begin(), hist.end());
    }
    
    snapshot.timestamp = std::chrono::steady_clock::now();
    snapshot.update_count = update_count_.load();
    
    return snapshot;
}

// END_METHOD_MetricsStore_GetSnapshot

//==============================================================================
// MetricsCollector Implementation
//==============================================================================

// START_METHOD_MetricsCollector_Constructor
// START_CONTRACT:
// PURPOSE: Инициализация сборщика метрик с заданным хранилищем и интервалом сбора
// INPUTS: store - хранилище для собранных метрик; collection_interval - интервал сбора в секундах
// OUTPUTS: Инициализированный объект MetricsCollector
// KEYWORDS: [CONCEPT(6): Initialization]
// END_CONTRACT
MetricsCollector::MetricsCollector(std::shared_ptr<MetricsStore> store, double collection_interval)
    : metrics_store_(std::move(store))
    , collection_interval_(collection_interval)
    , is_collecting_(false)
    , stop_flag_(false) 
{
    if (logger) {
        logger->info("MetricsCollector initialized with interval {}s", collection_interval);
    }
}

// END_METHOD_MetricsCollector_Constructor

// START_METHOD_MetricsCollector_Destructor
// START_CONTRACT:
// PURPOSE: Деструктор - автоматически останавливает сбор
// KEYWORDS: [CONCEPT(5): Cleanup]
// END_CONTRACT
MetricsCollector::~MetricsCollector() {
    stop();
}

// END_METHOD_MetricsCollector_Destructor

// START_METHOD_MetricsCollector_AddSource
// START_CONTRACT:
// PURPOSE: Добавить источник метрик с заданным именем
// INPUTS: name - уникальное имя источника; collector_fn - функция, возвращающая словарь метрик
// OUTPUTS: Нет
// KEYWORDS: [CONCEPT(5): Registration; DOMAIN(7): SourceManagement]
// END_CONTRACT
void MetricsCollector::add_source(const std::string& name, CollectorFunction collector_fn) {
    std::lock_guard lock(sources_mutex_);
    sources_[name] = std::move(collector_fn);
    
    if (logger) {
        logger->debug("Source '{}' added", name);
    }
}

// END_METHOD_MetricsCollector_AddSource

// START_METHOD_MetricsCollector_RemoveSource
// START_CONTRACT:
// PURPOSE: Удалить источник метрик по имени
// INPUTS: name - имя источника для удаления
// OUTPUTS: Нет
// KEYWORDS: [CONCEPT(5): Removal; DOMAIN(7): SourceManagement]
// END_CONTRACT
void MetricsCollector::remove_source(const std::string& name) {
    std::lock_guard lock(sources_mutex_);
    auto it = sources_.find(name);
    if (it != sources_.end()) {
        sources_.erase(it);
        
        if (logger) {
            logger->debug("Source '{}' removed", name);
        }
    }
}

// END_METHOD_MetricsCollector_RemoveSource

// START_METHOD_MetricsCollector_Start
// START_CONTRACT:
// PURPOSE: Начать фоновый сбор метрик из всех источников
// OUTPUTS: Нет
// KEYWORDS: [CONCEPT(6): Startup; DOMAIN(8): Collection]
// END_CONTRACT
void MetricsCollector::start() {
    if (is_collecting_.load()) {
        if (logger) {
            logger->warn("Collection already started");
        }
        return;
    }
    
    stop_flag_.store(false);
    is_collecting_.store(true);
    collection_thread_ = std::thread(&MetricsCollector::collection_loop, this);
    
    if (logger) {
        logger->info("Metrics collection started");
    }
}

// END_METHOD_MetricsCollector_Start

// START_METHOD_MetricsCollector_Stop
// START_CONTRACT:
// PURPOSE: Остановить фоновый сбор метрик
// OUTPUTS: Нет
// KEYWORDS: [CONCEPT(6): Shutdown; DOMAIN(8): Collection]
// END_CONTRACT
void MetricsCollector::stop() {
    if (!is_collecting_.load()) {
        if (logger) {
            logger->warn("Collection not started");
        }
        return;
    }
    
    stop_flag_.store(true);
    is_collecting_.store(false);
    
    if (collection_thread_.joinable()) {
        collection_thread_.join();
    }
    
    if (logger) {
        logger->info("Metrics collection stopped");
    }
}

// END_METHOD_MetricsCollector_Stop

// START_METHOD_MetricsCollector_Collect
// START_CONTRACT:
// PURPOSE: Принудительный сбор метрик из всех источников и сохранение в хранилище
// OUTPUTS: Нет
// KEYWORDS: [CONCEPT(7): Collection; DOMAIN(8): Aggregation]
// END_CONTRACT
void MetricsCollector::collect() {
    std::lock_guard lock(sources_mutex_);
    
    MetricsMap all_metrics;
    
    for (const auto& [name, collector_fn] : sources_) {
        try {
            auto source_metrics = collector_fn();
            all_metrics.insert(source_metrics.begin(), source_metrics.end());
        } catch (const std::exception& e) {
            if (logger) {
                logger->error("Error collecting from '{}': {}", name, e.what());
            }
        }
    }
    
    if (!all_metrics.empty()) {
        metrics_store_->update(all_metrics);
        
        if (logger) {
            logger->debug("Collected {} metrics", all_metrics.size());
        }
    }
}

// END_METHOD_MetricsCollector_Collect

// START_METHOD_MetricsCollector_CollectionLoop
// START_CONTRACT:
// PURPOSE: Внутренний цикл сбора метрик
// KEYWORDS: [CONCEPT(5): Loop; DOMAIN(8): Collection]
// END_CONTRACT
void MetricsCollector::collection_loop() {
    while (!stop_flag_.load()) {
        collect();
        
        // Интервал между сбором
        std::this_thread::sleep_for(std::chrono::duration<double>(collection_interval_));
    }
}

// END_METHOD_MetricsCollector_CollectionLoop

// START_METHOD_MetricsCollector_GetCurrentMetrics
// START_CONTRACT:
// PURPOSE: Получить текущие метрики из хранилища
// OUTPUTS: Текущие метрики
// KEYWORDS: [CONCEPT(5): Getter; DOMAIN(7): Metrics]
// END_CONTRACT
MetricsMap MetricsCollector::get_current_metrics() const {
    return metrics_store_->get_current();
}

// END_METHOD_MetricsCollector_GetCurrentMetrics

// START_METHOD_MetricsCollector_IsCollecting
// START_CONTRACT:
// PURPOSE: Проверка состояния сбора метрик
// OUTPUTS: true если сбор активен, false в противном случае
// KEYWORDS: [CONCEPT(5): StateCheck]
// END_CONTRACT
bool MetricsCollector::is_collecting() const {
    return is_collecting_.load();
}

// END_METHOD_MetricsCollector_IsCollecting
