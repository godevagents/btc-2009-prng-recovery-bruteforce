// FILE: src/monitor_cpp/plugins/live_stats_plugin.hpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Плагин live-мониторинга процесса генерации кошельков Bitcoin. Отображает метрики в реальном времени: итерации, кошельки, совпадения, время работы, энтропия, графики производительности.
// SCOPE: Этап 2 мониторинга, real-time метрики, графики производительности, система ring buffer для истории
// INPUT: Метрики от генератора в реальном времени (iteration_count, wallet_count, match_count, entropy_data)
// OUTPUT: Текущая статистика (CurrentStats), детальная статистика (Statistics), данные для графиков
// KEYWORDS: [DOMAIN(9): LiveMonitoring; DOMAIN(8): RealTime; DOMAIN(7): Statistics; TECH(8): RingBuffer; TECH(6): C++17]
// LINKS: [EXTENDS(8): IPlugin; USES_API(7): plugin_base; USES_API(6): metrics]
// END_MODULE_CONTRACT

#ifndef LIVE_STATS_PLUGIN_HPP
#define LIVE_STATS_PLUGIN_HPP

//==============================================================================
// Plugin Base Headers
//==============================================================================
#include "plugin_base.hpp"

//==============================================================================
// Standard Library Headers
//==============================================================================
#include <string>
#include <vector>
#include <array>
#include <atomic>
#include <mutex>
#include <chrono>
#include <cmath>
#include <optional>
#include <sstream>
#include <algorithm>
#include <map>

//==============================================================================
// Forward Declarations
//==============================================================================
class LiveStatsPlugin;

//==============================================================================
// Константы Модуля
//==============================================================================

/**
 * @brief Максимальное количество точек истории метрик
 * 
 * Соответствует Python константе MAX_HISTORY_POINTS = 100
 * Ограничивает размер истории для отображения графиков производительности
 */
constexpr size_t MAX_HISTORY_POINTS = 100;

/**
 * @brief Интервал обновления мониторинга в секундах
 * 
 * Соответствует Python константе REFRESH_INTERVAL = 1.0
 */
constexpr double REFRESH_INTERVAL = 1.0;

//==============================================================================
// RingBuffer Template - Кольцевой буфер фиксированного размера
//==============================================================================

/**
 * @brief Шаблонный класс RingBuffer - кольцевой буфер фиксированного размера
 * 
 * CONTRACT:
 * PURPOSE: Хранение последних N элементов с эффективным использованием памяти
 * TYPE_PARAMS:
 * - T: тип хранимых элементов
 * - MaxSize: максимальный размер буфера
 * 
 * METHODS:
 * - push(value): добавление элемента (автоматически удаляет старые при переполнении)
 * - clear(): очистка буфера
 * - size(): получение текущего размера
 * - capacity(): получение максимального размера
 * - empty(): проверка на пустоту
 * - full(): проверка на заполненность
 * - begin()/end(): итераторы для диапазонного for
 * - operator[](index): доступ по индексу
 * - toVector(): преобразование в std::vector
 */
template<typename T, size_t MaxSize>
class RingBuffer {
public:
    /**
     * @brief Конструктор по умолчанию
     */
    RingBuffer() : m_head(0), m_count(0) {}
    
    /**
     * @brief Добавление элемента в буфер
     * 
     * CONTRACT:
     * INPUTS: const T& value — добавляемый элемент
     * OUTPUTS: Нет
     * SIDE_EFFECTS: При переполнении автоматически удаляется самый старый элемент
     */
    void push(const T& value) {
        m_data[m_head] = value;
        m_head = (m_head + 1) % MaxSize;
        if (m_count < MaxSize) {
            m_count++;
        }
    }
    
    /**
     * @brief Очистка буфера
     * 
     * CONTRACT:
     * OUTPUTS: Нет
     * SIDE_EFFECTS: Сброс указателей head и count
     */
    void clear() {
        m_head = 0;
        m_count = 0;
    }
    
    /**
     * @brief Получение текущего размера
     * 
     * CONTRACT:
     * OUTPUTS: size_t — количество элементов в буфере
     */
    size_t size() const { return m_count; }
    
    /**
     * @brief Получение максимального размера
     * 
     * CONTRACT:
     * OUTPUTS: size_t — максимальная ёмкость буфера
     */
    size_t capacity() const { return MaxSize; }
    
    /**
     * @brief Проверка на пустоту
     * 
     * CONTRACT:
     * OUTPUTS: bool — true если буфер пуст
     */
    bool empty() const { return m_count == 0; }
    
    /**
     * @brief Проверка на заполненность
     * 
     * CONTRACT:
     * OUTPUTS: bool — true если буфер полон
     */
    bool full() const { return m_count == MaxSize; }
    
    //==========================================================================
    // Итераторы
    //==========================================================================
    
    /**
     * @brief Класс итератора для RingBuffer
     */
    class Iterator {
    public:
        Iterator(const RingBuffer* buffer, size_t index) 
            : m_buffer(buffer), m_index(index) {}
        
        const T& operator*() const { return m_buffer->m_data[m_index]; }
        Iterator& operator++() { 
            m_index = (m_index + 1) % MaxSize; 
            return *this; 
        }
        bool operator!=(const Iterator& other) const { 
            return m_index != other.m_index; 
        }
        
    private:
        const RingBuffer* m_buffer;
        size_t m_index;
    };
    
    /**
     * @brief Получение итератора на начало
     */
    Iterator begin() const {
        if (m_count == 0) return end();
        size_t start = (m_head + MaxSize - m_count) % MaxSize;
        return Iterator(this, start);
    }
    
    /**
     * @brief Получение итератора на конец
     */
    Iterator end() const {
        return Iterator(this, m_head);
    }
    
    //==========================================================================
    // Доступ по индексу
    //==========================================================================
    
    /**
     * @brief Доступ по индексу (от oldest к newest)
     * 
     * CONTRACT:
     * INPUTS: size_t index — индекс (0 - самый старый)
     * OUTPUTS: const T& — ссылка на элемент
     * TEST_CONDITIONS: index должен быть меньше size()
     */
    const T& operator[](size_t index) const {
        size_t start = (m_head + MaxSize - m_count) % MaxSize;
        return m_data[(start + index) % MaxSize];
    }
    
    /**
     * @brief Преобразование в std::vector
     * 
     * CONTRACT:
     * OUTPUTS: std::vector<T> — вектор всех элементов
     */
    std::vector<T> toVector() const {
        std::vector<T> result;
        result.reserve(m_count);
        for (const auto& item : *this) {
            result.push_back(item);
        }
        return result;
    }

private:
    std::array<T, MaxSize> m_data;  // Предвыделенный массив
    size_t m_head;                   // Указатель на голову
    size_t m_count;                  // Текущее количество элементов
};

//==============================================================================
// СТРУКТУРЫ ДАННЫХ
//==============================================================================

/**
 * @brief Структура MetricSnapshot - хранит одну точку данных метрик
 * 
 * Используется для хранения одной записи в истории метрик.
 * Содержит дельты (изменения) значений между обновлениями и временную метку.
 * 
 * CONTRACT:
 * PURPOSE: Хранение одной точки данных метрик для истории
 * ATTRIBUTES:
 * - iteration_delta: double — изменение количества итераций
 * - wallet_delta: double — изменение количества кошельков
 * - match_delta: double — изменение количества совпадений
 * - entropy_bits: double — значение энтропии в битах
 * - timestamp: std::chrono::steady_clock::time_point — временная метка
 */
struct MetricSnapshot {
    double iteration_delta;    // Изменение количества итераций
    double wallet_delta;       // Изменение количества кошельков
    double match_delta;        // Изменение количества совпадений
    double entropy_bits;       // Значение энтропии в битах
    std::chrono::steady_clock::time_point timestamp;  // Временная метка
    
    /**
     * @brief Конструктор по умолчанию
     * 
     * CONTRACT:
     * OUTPUTS: Объект с нулевыми значениями и текущей временной меткой
     */
    MetricSnapshot() 
        : iteration_delta(0.0)
        , wallet_delta(0.0)
        , match_delta(0.0)
        , entropy_bits(0.0)
        , timestamp(std::chrono::steady_clock::now())
    {}
    
    /**
     * @brief Конструктор с параметрами
     * 
     * CONTRACT:
     * INPUTS: 
     * - iter: изменение итераций
     * - wallet: изменение кошельков
     * - match: изменение совпадений
     * - entropy: значение энтропии
     * OUTPUTS: Объект с заданными значениями
     */
    MetricSnapshot(double iter, double wallet, double match, double entropy)
        : iteration_delta(iter)
        , wallet_delta(wallet)
        , match_delta(match)
        , entropy_bits(entropy)
        , timestamp(std::chrono::steady_clock::now())
    {}
};

/**
 * @brief Структура Statistics - результаты вычисления статистики
 * 
 * CONTRACT:
 * PURPOSE: Хранение статистических показателей метрик
 * ATTRIBUTES:
 * - iterations_*: статистика итераций (min, max, mean, std)
 * - wallets_*: статистика кошельков (min, max, mean, std)
 * - entropy_*: статистика энтропии (min, max, mean)
 * - *_available: флаги доступности данных
 */
struct Statistics {
    // Статистика итераций
    double iterations_min;
    double iterations_max;
    double iterations_mean;
    double iterations_std;
    
    // Статистика кошельков
    double wallets_min;
    double wallets_max;
    double wallets_mean;
    double wallets_std;
    
    // Статистика энтропии (без std - по аналогии с Python)
    double entropy_min;
    double entropy_max;
    double entropy_mean;
    
    // Флаги доступности
    bool iterations_available;
    bool wallets_available;
    bool entropy_available;
    
    /**
     * @brief Конструктор по умолчанию
     */
    Statistics()
        : iterations_min(0.0), iterations_max(0.0), iterations_mean(0.0), iterations_std(0.0)
        , wallets_min(0.0), wallets_max(0.0), wallets_mean(0.0), wallets_std(0.0)
        , entropy_min(0.0), entropy_max(0.0), entropy_mean(0.0)
        , iterations_available(false), wallets_available(false), entropy_available(false)
    {}
};

/**
 * @brief Структура CurrentStats - текущая статистика мониторинга
 * 
 * CONTRACT:
 * PURPOSE: Хранение текущих значений метрик для отображения в UI
 * ATTRIBUTES:
 * - iterations: общее количество итераций
 * - wallets: общее количество кошельков
 * - matches: общее количество совпадений
 * - elapsed_time: прошедшее время в секундах
 * - iter_per_sec: скорость итераций в секунду
 * - wallets_per_sec: скорость кошельков в секунду
 * - is_monitoring: флаг активности мониторинга
 */
struct CurrentStats {
    int64_t iterations;
    int64_t wallets;
    int64_t matches;
    double elapsed_time;
    double iter_per_sec;
    double wallets_per_sec;
    bool is_monitoring;
    
    /**
     * @brief Конструктор по умолчанию
     */
    CurrentStats()
        : iterations(0), wallets(0), matches(0)
        , elapsed_time(0.0), iter_per_sec(0.0), wallets_per_sec(0.0)
        , is_monitoring(false)
    {}
};

//==============================================================================
// КЛАСС LIVE_STATS_PLUGIN
//==============================================================================

/**
 * @brief Класс LiveStatsPlugin - плагин live-мониторинга
 * 
 * CONTRACT:
 * PURPOSE: Плагин live-мониторинга процесса генерации кошельков Bitcoin
 * ATTRIBUTES:
 * - m_name: имя плагина
 * - m_priority: приоритет плагина (20 - соответствует Python)
 * - m_enabled: флаг включения плагина
 * - m_logger: логгер плагина
 * - m_app: указатель на приложение
 * - m_last_iteration_count: атомарный счётчик итераций
 * - m_last_wallet_count: атомарный счётчик кошельков
 * - m_last_match_count: атомарный счётчик совпадений
 * - m_is_monitoring: атомарный флаг мониторинга
 * - m_start_timestamp: время начала мониторинга
 * - m_history_: кольцевые буферы истории
 * - m_data_mutex: мьютекс для thread-safe доступа
 * 
 * METHODS:
 * - initialize(): инициализация плагина и регистрация UI
 * - on_metrics_update(metrics): обработка обновления метрик
 * - on_start(path): обработка запуска генерации
 * - on_finish(metrics): обработка завершения генерации
 * - shutdown(): завершение работы
 * - get_current_stats(): получение текущей статистики
 * - calculate_statistics(): вычисление детальной статистики
 * - reset_stats(): сброс статистики
 * - get_iteration_plot_data(): получение данных для графика итераций
 * - get_wallet_plot_data(): получение данных для графика кошельков
 * - get_entropy_summary(): получение сводки по энтропии
 * - is_monitoring(): проверка состояния мониторинга
 * - get_performance_report(): получение текстового отчёта
 * 
 * KEYWORDS: [DOMAIN(9): LiveMonitoring; PATTERN(7): Plugin; TECH(8): RingBuffer]
 * LINKS: [EXTENDS(8): IPlugin]
 */
class LiveStatsPlugin : public IPlugin {
public:
    //==========================================================================
    // Constructor / Destructor
    //==========================================================================
    
    /**
     * @brief Конструктор плагина live-мониторинга
     * 
     * CONTRACT:
     * OUTPUTS: Инициализированный объект LiveStatsPlugin
     * SIDE_EFFECTS: Создаёт хранилище истории метрик; инициализирует логгер
     * TEST_CONDITIONS: Объект должен быть готов к инициализации
     */
    LiveStatsPlugin();
    
    /**
     * @brief Деструктор плагина
     * 
     * CONTRACT:
     * SIDE_EFFECTS: Вызывает shutdown() для корректного завершения
     */
    virtual ~LiveStatsPlugin() override;
    
    //==========================================================================
    // IPlugin Implementation
    //==========================================================================
    
    /**
     * @brief Инициализация плагина
     * 
     * CONTRACT:
     * INPUTS: Нет
     * OUTPUTS: void
     * SIDE_EFFECTS: Регистрация UI компонентов; инициализация внутреннего состояния
     * TEST_CONDITIONS: Плагин должен успешно инициализироваться
     */
    void initialize() override;
    
    /**
     * @brief Завершение работы плагина
     * 
     * CONTRACT:
     * INPUTS: Нет
     * OUTPUTS: void
     * SIDE_EFFECTS: Сброс состояния мониторинга; освобождение ресурсов
     * TEST_CONDITIONS: Все ресурсы должны быть освобождены
     */
    void shutdown() override;
    
    /**
     * @brief Получение информации о плагине
     * 
     * CONTRACT:
     * OUTPUTS: PluginInfo — информация о плагине
     */
    PluginInfo get_info() const override;
    
    /**
     * @brief Получение состояния плагина
     * 
     * CONTRACT:
     * OUTPUTS: PluginState — текущее состояние плагина
     */
    PluginState get_state() const override;
    
    //==========================================================================
    // Event Handlers
    //==========================================================================
    
    /**
     * @brief Обработка обновления метрик
     * 
     * CONTRACT:
     * INPUTS: const PluginMetrics& metrics — словарь метрик
     * OUTPUTS: void
     * SIDE_EFFECTS: Обновление истории метрик; вычисление дельт; обновление временных меток
     * TEST_CONDITIONS: Метод должен корректно обработать любые метрики
     */
    void on_metrics_update(const PluginMetrics& metrics) override;
    
    /**
     * @brief Обработчик запуска генератора кошельков
     * 
     * CONTRACT:
     * INPUTS: const std::string& selectedListPath — путь к списку адресов
     * OUTPUTS: void
     * SIDE_EFFECTS: Сброс статистики; установка флага мониторинга; запуск таймера
     */
    void on_start(const std::string& selected_list_path) override;
    
    /**
     * @brief Обработчик завершения генерации кошельков
     * 
     * CONTRACT:
     * INPUTS: const PluginMetrics& finalMetrics — финальные метрики
     * OUTPUTS: void
     * SIDE_EFFECTS: Обработка финальных метрик; обновление UI
     */
    void on_finish(const PluginMetrics& final_metrics) override;
    
    /**
     * @brief Обработчик сброса генератора
     * 
     * CONTRACT:
     * INPUTS: Нет
     * OUTPUTS: void
     * SIDE_EFFECTS: Сброс внутреннего состояния; очистка истории
     */
    void on_reset() override;
    
    //==========================================================================
    // Специфичные методы плагина LiveStats
    //==========================================================================
    
    /**
     * @brief Получение текущей статистики
     * 
     * CONTRACT:
     * OUTPUTS: CurrentStats — структура с текущими значениями метрик
     * SIDE_EFFECTS: Вычисление прошедшего времени и скоростей
     */
    CurrentStats getCurrentStats() const;
    
    /**
     * @brief Вычисление статистических показателей
     * 
     * CONTRACT:
     * OUTPUTS: Statistics — структура с min, max, mean, std для метрик
     * SIDE_EFFECTS: Захватывает мьютекс для thread-safe доступа к данным
     */
    Statistics calculateStatistics() const;
    
    /**
     * @brief Сброс статистики мониторинга
     * 
     * CONTRACT:
     * OUTPUTS: void
     * SIDE_EFFECTS: Очищает историю метрик; сбрасывает счётчики
     */
    void resetStats();
    
    /**
     * @brief Получение данных для графика итераций
     * 
     * CONTRACT:
     * OUTPUTS: std::pair<std::vector<double>, std::vector<double>> — пары (x, y) для графика
     */
    std::pair<std::vector<double>, std::vector<double>> getIterationPlotData() const;
    
    /**
     * @brief Получение данных для графика кошельков
     * 
     * CONTRACT:
     * OUTPUTS: std::pair<std::vector<double>, std::vector<double>> — пары (x, y) для графика
     */
    std::pair<std::vector<double>, std::vector<double>> getWalletPlotData() const;
    
    /**
     * @brief Получение сводки по энтропии
     * 
     * CONTRACT:
     * OUTPUTS: std::unordered_map<std::string, PluginAny> — словарь с данными энтропии
     */
    std::unordered_map<std::string, PluginAny> getEntropySummary() const;
    
    /**
     * @brief Проверка состояния мониторинга
     * 
     * CONTRACT:
     * OUTPUTS: bool — true если мониторинг активен
     */
    bool isMonitoring() const;
    
    /**
     * @brief Получение текстового отчёта о производительности
     * 
     * CONTRACT:
     * OUTPUTS: std::string — текстовый отчёт о производительности
     */
    std::string getPerformanceReport() const;

private:
    //==========================================================================
    // Вспомогательные методы
    //==========================================================================
    
    /**
     * @brief Вычисление среднего значения
     * 
     * CONTRACT:
     * INPUTS: values — вектор double значений
     * OUTPUTS: Среднее значение (double)
     */
    double calculateMean(const std::vector<double>& values) const;
    
    /**
     * @brief Вычисление стандартного отклонения
     * 
     * CONTRACT:
     * INPUTS: values — вектор double значений, mean — среднее значение
     * OUTPUTS: Стандартное отклонение (double)
     */
    double calculateStd(const std::vector<double>& values, double mean) const;
    
    /**
     * @brief Вычисление прошедшего времени
     * 
     * CONTRACT:
     * OUTPUTS: Прошедшее время в секундах (double)
     */
    double calculateTimeElapsed() const;
    
    /**
     * @brief Извлечение значения метрики из PluginMetrics
     * 
     * CONTRACT:
     * INPUTS: metrics — словарь метрик, key — имя метрики
     * OUTPUTS: Значение метрики или default_value если не найдено
     */
    template<typename T>
    T getMetricValue(const PluginMetrics& metrics, const std::string& key, T default_value) const;
    
    //==========================================================================
    // Атрибуты плагина
    //==========================================================================
    
    std::string m_name;           // Имя плагина
    PluginInfo m_info;            // Информация о плагине
    PluginLogger m_logger;        // Логгер
    
    // Атомарные счётчики для thread-safe обновлений
    std::atomic<int64_t> m_last_iteration_count{0};
    std::atomic<int64_t> m_last_wallet_count{0};
    std::atomic<int64_t> m_last_match_count{0};
    std::atomic<bool> m_is_monitoring{false};
    std::atomic<double> m_last_update_time{0.0};
    
    // Временная метка начала мониторинга
    std::optional<std::chrono::steady_clock::time_point> m_start_timestamp;
    
    // История метрик (ring buffer)
    RingBuffer<MetricSnapshot, MAX_HISTORY_POINTS> m_history;
    RingBuffer<double, MAX_HISTORY_POINTS> m_entropy_samples;
    
    // Мьютекс для защиты доступа к данным
    mutable std::mutex m_data_mutex;
};

//==============================================================================
// Типы указателей
//==============================================================================

/** @brief Тип умного указателя на плагин */
using LiveStatsPluginPtr = std::shared_ptr<LiveStatsPlugin>;

#endif // LIVE_STATS_PLUGIN_HPP
