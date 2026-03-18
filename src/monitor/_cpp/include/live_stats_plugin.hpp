// FILE: src/monitor/_cpp/include/live_stats_plugin.hpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Заголовочный файл плагина live-мониторинга процесса генерации кошельков на C++.
// Отображает метрики в реальном времени с графиками производительности.
// SCOPE: Live мониторинг, real-time метрики, графики производительности
// INPUT: Метрики от генератора в реальном времени
// OUTPUT: Класс LiveStatsPlugin, структуры данных для истории и статистики
// KEYWORDS: [DOMAIN(9): LiveMonitoring; DOMAIN(8): RealTime; TECH(8): Plugin; TECH(6): Pybind11]
// LINKS: [USES_API(8): plugin_base.hpp; USES_API(7): ring_buffer.hpp]
// END_MODULE_CONTRACT

#ifndef WALLET_MONITOR_LIVE_STATS_PLUGIN_HPP
#define WALLET_MONITOR_LIVE_STATS_PLUGIN_HPP

#include <string>
#include <vector>
#include <memory>
#include <chrono>
#include <sstream>
#include <iomanip>
#include <algorithm>
#include <cmath>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/chrono.h>
#include <pybind11/functional.h>

namespace py = pybind11;

// Включение заголовочного файла базового класса
#include "plugin_base.hpp"

// Включение шаблонного кольцевого буфера
#include "ring_buffer.hpp"

// START_CONSTANTS_LIVE_STATS
// START_CONTRACT:
// PURPOSE: Константы плагина live-мониторинга
// ATTRIBUTES:
// - kMaxHistoryPoints: Максимальное количество точек истории
// - kRefreshInterval: Интервал обновления в секундах
// KEYWORDS: [CONCEPT(7): Constants]
// END_CONTRACT

namespace wallet {
namespace monitor {
namespace live_stats {

const size_t kMaxHistoryPoints = 100;
const double kRefreshInterval = 1.0;

// START_STRUCT_THEME_COLORS
// START_CONTRACT:
// PURPOSE: Структура цветов темы для UI
// ATTRIBUTES:
// - primary: Основной цвет
// - success: Цвет успеха
// - warning: Цвет предупреждения
// - danger: Цвет опасности
// - info: Информационный цвет
// KEYWORDS: [DOMAIN(6): Theme; CONCEPT(6): Colors]
// END_CONTRACT

struct ThemeColors {
    std::string primary = "#2196F3";
    std::string success = "#4CAF50";
    std::string warning = "#FF9800";
    std::string danger = "#F44336";
    std::string info = "#00BCD4";
};
// END_STRUCT_THEME_COLORS

} // namespace live_stats
} // namespace monitor
} // namespace wallet

// START_STRUCT_METRIC_SNAPSHOT
// START_CONTRACT:
// PURPOSE: Структура снимка метрик для истории
// ATTRIBUTES:
// - iteration_count: Количество итераций
// - wallet_count: Количество кошельков
// - match_count: Количество совпадений
// - timestamp: Временная метка
// KEYWORDS: [DOMAIN(7): Metrics; CONCEPT(7): Snapshot]
// END_CONTRACT

struct MetricSnapshot {
    double iteration_delta;
    double wallet_delta;
    double match_delta;
    double timestamp;

    MetricSnapshot() : iteration_delta(0.0), wallet_delta(0.0), match_delta(0.0), timestamp(0.0) {}
    
    MetricSnapshot(double iter, double wallet, double match, double ts)
        : iteration_delta(iter), wallet_delta(wallet), match_delta(match), timestamp(ts) {}
};
// END_STRUCT_METRIC_SNAPSHOT


// START_STRUCT_STATISTICS
// START_CONTRACT:
// PURPOSE: Структура статистических показателей
// ATTRIBUTES:
// - min: Минимальное значение
// - max: Максимальное значение
// - mean: Среднее значение
// - std: Стандартное отклонение
// KEYWORDS: [DOMAIN(8): Statistics; CONCEPT(7): Analysis]
// END_CONTRACT

struct Statistics {
    double min;
    double max;
    double mean;
    double std;

    Statistics() : min(0.0), max(0.0), mean(0.0), std(0.0) {}

    Statistics(double min_val, double max_val, double mean_val, double std_val)
        : min(min_val), max(max_val), mean(mean_val), std(std_val) {}
};
// END_STRUCT_STATISTICS


// START_STRUCT_CURRENT_STATS
// START_CONTRACT:
// PURPOSE: Структура текущей статистики
// ATTRIBUTES:
// - iterations: Общее количество итераций
// - wallets: Общее количество кошельков
// - matches: Общее количество совпадений
// - elapsed_time: Прошедшее время в секундах
// - iter_per_sec: Итераций в секунду
// - wallets_per_sec: Кошельков в секунду
// - is_monitoring: Флаг активности мониторинга
// KEYWORDS: [DOMAIN(7): CurrentStats; CONCEPT(6): Metrics]
// END_CONTRACT

struct CurrentStats {
    int64_t iterations;
    int64_t wallets;
    int64_t matches;
    double elapsed_time;
    double iter_per_sec;
    double wallets_per_sec;
    bool is_monitoring;

    CurrentStats()
        : iterations(0), wallets(0), matches(0)
        , elapsed_time(0.0), iter_per_sec(0.0), wallets_per_sec(0.0)
        , is_monitoring(false) {}
};
// END_STRUCT_CURRENT_STATS


// START_CLASS_LIVE_STATS_PLUGIN
// START_CONTRACT:
// PURPOSE: Плагин live-мониторинга процесса генерации кошельков. Отображает метрики в реальном времени с графиками производительности.
// ATTRIBUTES:
// - VERSION: std::string — версия плагина
// - AUTHOR: std::string — автор плагина
// - DESCRIPTION: std::string — описание плагина
// - _history_iterations: RingBuffer<double, 100> — история итераций
// - _history_wallets: RingBuffer<double, 100> — история кошельков
// - _history_matches: RingBuffer<double, 100> — история совпадений
// - _history_timestamps: RingBuffer<double, 100> — история временных меток
// - _entropy_samples: RingBuffer<double, 100> — выборки энтропии
// - _is_monitoring: bool — флаг активности мониторинга
// - _start_timestamp: double — временная метка старта
// - _last_iteration_count: int64_t — последнее количество итераций
// - _last_wallet_count: int64_t — последнее количество кошельков
// - _last_match_count: int64_t — последнее количество совпадений
// - _last_update_time: double — время последнего обновления
// - _app: py::object — ссылка на приложение
// METHODS:
// - initialize: Инициализация плагина и регистрация UI
// - on_metric_update: Обработка метрик от генератора
// - on_shutdown: Остановка мониторинга
// - get_ui_components: Получение UI компонентов
// - reset_stats: Сброс статистики
// - get_current_stats: Получение текущей статистики
// - get_iteration_history: Получение истории итераций
// - get_wallet_history: Получение истории кошельков
// - get_plot_data: Получение данных для графика
// - calculate_statistics: Вычисление статистических показателей
// - get_performance_report: Получение текстового отчёта
// - get_entropy_summary: Получение сводки по энтропии
// - is_monitoring: Проверка состояния мониторинга
// KEYWORDS: [DOMAIN(9): LiveMonitoring; PATTERN(7): Plugin; TECH(8): RealTime]
// LINKS: [EXTENDS(8): BaseMonitorPlugin]
// END_CONTRACT

class LiveStatsPlugin : public BaseMonitorPlugin {
public:
    // Статические константы (аналог class attributes в Python)
    static const std::string VERSION;
    static const std::string AUTHOR;
    static const std::string DESCRIPTION;

    // START_CONSTRUCTOR_LIVE_STATS_PLUGIN
    // START_CONTRACT:
    // PURPOSE: Конструктор плагина live-мониторинга
    // OUTPUTS: Инициализированный объект LiveStatsPlugin
    // SIDE_EFFECTS: Создаёт хранилище истории метрик; инициализирует кольцевые буферы
    // KEYWORDS: [CONCEPT(5): Initialization]
    // END_CONTRACT
    LiveStatsPlugin();

    // Виртуальный деструктор
    virtual ~LiveStatsPlugin() = default;

    // START_METHOD_INITIALIZE
    // START_CONTRACT:
    // PURPOSE: Инициализация плагина и регистрация UI компонентов в главном приложении
    // INPUTS:
    // - app: py::object — ссылка на главное приложение мониторинга
    // OUTPUTS: void
    // SIDE_EFFECTS: Создаёт UI компоненты для отображения метрик; регистрирует плагин в главном приложении
    // KEYWORDS: [DOMAIN(8): PluginSetup; CONCEPT(6): Registration]
    // END_CONTRACT
    void initialize(py::object app) override;

    // START_METHOD_ON_METRIC_UPDATE
    // START_CONTRACT:
    // PURPOSE: Обработка обновления метрик от генератора
    // INPUTS:
    // - metrics: py::dict — словарь метрик
    // OUTPUTS: void
    // SIDE_EFFECTS: Обновляет историю метрик; вычисляет дельты; обновляет энтропию
    // KEYWORDS: [DOMAIN(9): MetricsProcessing; CONCEPT(7): EventHandler]
    // END_CONTRACT
    void on_metric_update(py::dict metrics) override;

    // START_METHOD_ON_SHUTDOWN
    // START_CONTRACT:
    // PURPOSE: Действия при завершении работы мониторинга
    // OUTPUTS: void
    // SIDE_EFFECTS: Сбрасывает состояние мониторинга
    // KEYWORDS: [CONCEPT(8): Cleanup]
    // END_CONTRACT
    void on_shutdown() override;

    // START_METHOD_GET_UI_COMPONENTS
    // START_CONTRACT:
    // PURPOSE: Получение UI компонентов плагина для отображения
    // OUTPUTS: py::object — словарь UI компонентов
    // KEYWORDS: [PATTERN(6): UI; CONCEPT(5): Getter]
    // END_CONTRACT
    py::object get_ui_components() override;

    // START_METHOD_RESET_STATS
    // START_CONTRACT:
    // PURPOSE: Сброс статистики мониторинга
    // OUTPUTS: void
    // SIDE_EFFECTS: Очищает историю метрик и сбрасывает счётчики
    // KEYWORDS: [CONCEPT(7): Reset]
    // END_CONTRACT
    void reset_stats();

    // START_METHOD_GET_CURRENT_STATS
    // START_CONTRACT:
    // PURPOSE: Получение текущей статистики
    // OUTPUTS: CurrentStats — структура текущей статистики
    // KEYWORDS: [CONCEPT(5): Getter]
    // END_CONTRACT
    CurrentStats get_current_stats() const;

    // START_METHOD_GET_CURRENT_STATS_PY
    // START_CONTRACT:
    // PURPOSE: Получение текущей статистики в виде Python словаря
    // OUTPUTS: py::dict — словарь текущей статистики
    // KEYWORDS: [CONCEPT(5): Getter; PATTERN(7): PythonBinding]
    // END_CONTRACT
    py::dict get_current_stats_py() const;

    // START_METHOD_GET_ITERATION_HISTORY
    // START_CONTRACT:
    // PURPOSE: Получение истории итераций
    // OUTPUTS: std::vector<double> — история итераций
    // KEYWORDS: [CONCEPT(5): Getter]
    // END_CONTRACT
    std::vector<double> get_iteration_history() const;

    // START_METHOD_GET_WALLET_HISTORY
    // START_CONTRACT:
    // PURPOSE: Получение истории кошельков
    // OUTPUTS: std::vector<double> — история кошельков
    // KEYWORDS: [CONCEPT(5): Getter]
    // END_CONTRACT
    std::vector<double> get_wallet_history() const;

    // START_METHOD_GET_MATCH_HISTORY
    // START_CONTRACT:
    // PURPOSE: Получения истории совпадений
    // OUTPUTS: std::vector<double> — история совпадений
    // KEYWORDS: [CONCEPT(5): Getter]
    // END_CONTRACT
    std::vector<double> get_match_history() const;

    // START_METHOD_GET_PLOT_DATA
    // START_CONTRACT:
    // PURPOSE: Преобразование истории в данные для графика
    // INPUTS:
    // - history: const std::vector<double>& — история значений
    // OUTPUTS: py::dict — словарь с ключами 'x' и 'y' для графика
    // KEYWORDS: [CONCEPT(7): ChartData]
    // END_CONTRACT
    py::dict get_plot_data(const std::vector<double>& history) const;

    // START_METHOD_GET_EMPTY_PLOT_DATA
    // START_CONTRACT:
    // PURPOSE: Получение пустых данных для графика
    // OUTPUTS: py::dict — пустые данные графика
    // KEYWORDS: [CONCEPT(6): ChartData]
    // END_CONTRACT
    py::dict get_empty_plot_data() const;

    // START_METHOD_CALCULATE_STATISTICS
    // START_CONTRACT:
    // PURPOSE: Вычисление статистических показателей
    // OUTPUTS: py::dict — словарь статистических показателей
    // KEYWORDS: [DOMAIN(8): Statistics; CONCEPT(7): Analysis]
    // END_CONTRACT
    py::dict calculate_statistics() const;

    // START_METHOD_GET_PERFORMANCE_REPORT
    // START_CONTRACT:
    // PURPOSE: Получение текстового отчёта о производительности
    // OUTPUTS: std::string — текстовый отчёт
    // KEYWORDS: [DOMAIN(7): Reporting; CONCEPT(6): Summary]
    // END_CONTRACT
    std::string get_performance_report() const;

    // START_METHOD_GET_ENTROPY_SUMMARY
    // START_CONTRACT:
    // PURPOSE: Получение сводки по энтропии
    // OUTPUTS: py::dict — словарь сводки по энтропии
    // KEYWORDS: [DOMAIN(6): Entropy; CONCEPT(6): Summary]
    // END_CONTRACT
    py::dict get_entropy_summary() const;

    // START_METHOD_IS_MONITORING
    // START_CONTRACT:
    // PURPOSE: Проверка состояния мониторинга
    // OUTPUTS: bool — True если мониторинг активен
    // KEYWORDS: [CONCEPT(5): Getter]
    // END_CONTRACT
    bool is_monitoring() const;

    // START_METHOD_GET_STATUS_HTML
    // START_CONTRACT:
    // PURPOSE: Генерация HTML статуса мониторинга
    // INPUTS:
    // - iteration_count: int64_t — текущий счётчик итераций
    // OUTPUTS: std::string — HTML статус
    // KEYWORDS: [CONCEPT(6): HTML]
    // END_CONTRACT
    std::string get_status_html(int64_t iteration_count = 0) const;

    // START_METHOD_ON_ENTER_STAGE
    // START_CONTRACT:
    // PURPOSE: Обработчик входа на этап live-мониторинга
    // OUTPUTS: void
    // SIDE_EFFECTS: Сбрасывает историю метрик
    // KEYWORDS: [CONCEPT(7): StageHandler]
    // END_CONTRACT
    void on_enter_stage();

    // START_METHOD_BUILD_UI_COMPONENTS
    // START_CONTRACT:
    // PURPOSE: Построение UI компонентов для отображения live-метрик (internal)
    // OUTPUTS: void
    // KEYWORDS: [DOMAIN(8): UIComponents; TECH(7): Gradio]
    // END_CONTRACT
    void build_ui_components();

protected:
    // История метрик (кольцевые буферы)
    RingBuffer<double, wallet::monitor::live_stats::kMaxHistoryPoints> _history_iterations;
    RingBuffer<double, wallet::monitor::live_stats::kMaxHistoryPoints> _history_wallets;
    RingBuffer<double, wallet::monitor::live_stats::kMaxHistoryPoints> _history_matches;
    RingBuffer<double, wallet::monitor::live_stats::kMaxHistoryPoints> _history_timestamps;
    
    // Выборки энтропии
    RingBuffer<double, 100> _entropy_samples;
    
    // Состояние мониторинга
    bool _is_monitoring;
    double _start_timestamp;
    double _last_update_time;
    
    // Счётчики
    int64_t _last_iteration_count;
    int64_t _last_wallet_count;
    int64_t _last_match_count;
    
    // UI компоненты (Python objects)
    py::object _gradio_components;
    
    // Тема цветов
    wallet::monitor::live_stats::ThemeColors _theme_colors;

private:
    // Вспомогательные методы
    double get_current_time() const;
    
    // Статистика
    Statistics calculate_stats(const std::vector<double>& data) const;
};
// END_CLASS_LIVE_STATS_PLUGIN


// START_CLASS_LIVE_STATS_PLUGIN_TRAMPOLINE
// START_CONTRACT:
// PURPOSE: Trampoline класс для обеспечения возможности наследования от C++ класса в Python.
// KEYWORDS: [PATTERN(9): TrampolineClass; DOMAIN(9): Pybind11; TECH(7): PythonBindings]
// END_CONTRACT

class LiveStatsPluginTrampoline : public LiveStatsPlugin {
public:
    using LiveStatsPlugin::LiveStatsPlugin;

    void initialize(py::object app) override {
        PYBIND11_OVERRIDE_PURE(
            void,
            LiveStatsPlugin,
            initialize,
            app
        );
    }

    void on_metric_update(py::dict metrics) override {
        PYBIND11_OVERRIDE_PURE(
            void,
            LiveStatsPlugin,
            on_metric_update,
            metrics
        );
    }

    void on_shutdown() override {
        PYBIND11_OVERRIDE_PURE(
            void,
            LiveStatsPlugin,
            on_shutdown
        );
    }

    py::object get_ui_components() override {
        PYBIND11_OVERRIDE(
            py::object,
            LiveStatsPlugin,
            get_ui_components
        );
    }
};
// END_CLASS_LIVE_STATS_PLUGIN_TRAMPOLINE


#endif // WALLET_MONITOR_LIVE_STATS_PLUGIN_HPP
