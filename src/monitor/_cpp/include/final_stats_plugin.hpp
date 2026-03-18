// FILE: src/monitor/_cpp/include/final_stats_plugin.hpp
// VERSION: 2.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Заголовочный файл плагина финальной статистики на C++.
// Обеспечивает отображение итоговой сводки после завершения генерации кошельков:
// общее количество итераций, совпадений, время работы, среднее время итерации.
// SCOPE: Классы плагина, структуры данных, интерфейсы экспорта
// INPUT: Заголовочный файл plugin_base.hpp
// OUTPUT: Класс FinalStatsPlugin, структуры данных, перечисления
// KEYWORDS: [DOMAIN(9): Statistics; DOMAIN(8): PluginSystem; CONCEPT(8): Finalization; TECH(7): ExportData]
// LINKS: [INHERITS_FROM(9): plugin_base.hpp; USES_API(7): pybind11]
// END_MODULE_CONTRACT

#ifndef WALLET_MONITOR_FINAL_STATS_PLUGIN_HPP
#define WALLET_MONITOR_FINAL_STATS_PLUGIN_HPP

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
#include <fstream>
#include <iomanip>

// pybind11
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <pybind11/chrono.h>

// Включение заголовочного файла базового класса
#include "plugin_base.hpp"

// START_ENUM_EXPORT_FORMAT
// START_CONTRACT:
// PURPOSE: Перечисление форматов экспорта отчётов
// ATTRIBUTES:
// - JSON: Экспорт в формате JSON
// - CSV: Экспорт в формате CSV (Comma Separated Values)
// - TXT: Экспорт в текстовом формате (читаемый человеком)
// - MARKDOWN: Экспорт в формате Markdown
// KEYWORDS: [PATTERN(6): Enum; DOMAIN(8): Export; CONCEPT(5): Format]
// END_CONTRACT

enum class ExportFormat {
    JSON = 0,
    CSV = 1,
    TXT = 2,
    MARKDOWN = 3
};
// END_ENUM_EXPORT_FORMAT


// START_STRUCT_FINAL_STATISTICS
// START_CONTRACT:
// PURPOSE: Структура для хранения финальных метрик генерации
// ATTRIBUTES:
// - iteration_count: int32_t — общее количество итераций
// - match_count: int32_t — количество совпадений
// - wallet_count: int32_t — количество сгенерированных кошельков
// - runtime_seconds: double — время работы в секундах
// - iterations_per_second: double — итераций в секунду
// - wallets_per_second: double — кошельков в секунду
// - avg_iteration_time_ms: double — среднее время итерации в миллисекундах
// - start_timestamp: double — время начала (Unix timestamp)
// - end_timestamp: double — время завершения (Unix timestamp)
// - list_path: std::string — путь к используемому списку
// - metadata: py::object — дополнительные метаданные
// KEYWORDS: [PATTERN(7): DataClass; DOMAIN(9): Statistics; CONCEPT(6): Storage]
// END_CONTRACT

struct FinalStatistics {
    int32_t iteration_count;
    int32_t match_count;
    int32_t wallet_count;
    double runtime_seconds;
    double iterations_per_second;
    double wallets_per_second;
    double avg_iteration_time_ms;
    double start_timestamp;
    double end_timestamp;
    std::string list_path;
    py::object metadata;

    // Конструктор по умолчанию
    FinalStatistics();

    // Конструктор с параметрами
    FinalStatistics(
        int32_t iterations,
        int32_t matches,
        int32_t wallets,
        double runtime
    );

    // Конструктор из Python словаря
    static FinalStatistics from_python(py::dict dict);

    // Конвертация в Python словарь
    py::dict to_python() const;

    // Проверка валидности данных
    bool is_valid() const;

    // Получение времени работы в читаемом формате
    std::string get_formatted_runtime() const;
};
// END_STRUCT_FINAL_STATISTICS


// START_STRUCT_SESSION_ENTRY
// START_CONTRACT:
// PURPOSE: Структура для хранения данных о сессии
// ATTRIBUTES:
// - session_id: int32_t — идентификатор сессии
// - iteration_count: int32_t — количество итераций в сессии
// - match_count: int32_t — количество совпадений в сессии
// - runtime_seconds: double — время работы сессии
// - start_timestamp: double — время начала сессии
// - end_timestamp: double — время завершения сессии
// - metrics: py::object — полные метрики сессии
// KEYWORDS: [PATTERN(7): DataClass; DOMAIN(8): SessionData; CONCEPT(6): Storage]
// END_CONTRACT

struct SessionEntry {
    int32_t session_id;
    int32_t iteration_count;
    int32_t match_count;
    int32_t wallet_count;
    double runtime_seconds;
    double start_timestamp;
    double end_timestamp;
    py::object metrics;

    // Конструктор по умолчанию
    SessionEntry();

    // Конструктор с параметрами
    SessionEntry(
        int32_t session_id,
        int32_t iterations,
        int32_t matches,
        int32_t wallets,
        double runtime,
        double start_time
    );

    // Конструктор из Python словаря
    static SessionEntry from_python(py::dict dict);

    // Конвертация в Python словарь
    py::dict to_python() const;
};
// END_STRUCT_SESSION_ENTRY


// START_STRUCT_PERFORMANCE_METRICS
// START_CONTRACT:
// PURPOSE: Структура для хранения метрик производительности
// ATTRIBUTES:
// - iterations: int32_t — общее количество итераций
// - runtime_seconds: double — время работы в секундах
// - iter_per_sec: double — итераций в секунду
// - estimated_hours_to_match: double — оценка времени до совпадения
// - probability_per_iteration: double — вероятность совпадения на итерации
// KEYWORDS: [PATTERN(7): DataClass; DOMAIN(8): Performance; CONCEPT(6): Metrics]
// END_CONTRACT

struct PerformanceMetrics {
    int32_t iterations;
    double runtime_seconds;
    double iter_per_sec;
    double estimated_hours_to_match;
    double probability_per_iteration;
    bool available;

    // Конструктор по умолчанию
    PerformanceMetrics();

    // Конструктор с параметрами
    PerformanceMetrics(
        int32_t iterations,
        double runtime,
        double iter_per_sec,
        double estimated_hours,
        double probability
    );

    // Конвертация в Python словарь
    py::dict to_python() const;
};
// END_STRUCT_PERFORMANCE_METRICS


// START_CLASS_FINAL_STATS_PLUGIN
// START_CONTRACT:
// PURPOSE: Класс плагина финальной статистики. Обеспечивает отображение итоговой сводки после завершения генерации кошельков Bitcoin.
// ATTRIBUTES:
// - VERSION: std::string — версия плагина
// - AUTHOR: std::string — автор плагина
// - DESCRIPTION: std::string — описание плагина
// - _gradio_components: py::object — UI компоненты для Gradio
// - _final_metrics: FinalStatistics — финальные метрики
// - _start_time: double — время начала генерации
// - _end_time: double — время завершения генерации
// - _is_complete: bool — флаг завершения
// - _session_history: std::deque<SessionEntry> — история сессий
// METHODS:
// - initialize: Инициализация плагина и регистрация UI
// - on_metric_update: Обработка обновления метрик (заглушка)
// - on_shutdown: Завершение работы плагина
// - get_ui_components: Получение UI компонентов
// - update_ui: Обновление UI компонентов
// - get_final_metrics: Получение финальных метрик
// - get_summary: Получение текстовой сводки
// - export_json: Экспорт в JSON
// - export_csv: Экспорт в CSV
// - export_txt: Экспорт в TXT
// - get_performance_analysis: Получение анализа производительности
// - is_complete: Проверка завершения
// - reset: Сброс статистики
// - add_session: Добавление сессии в историю
// - get_session_history: Получение истории сессий
// - get_total_statistics: Получение общей статистики
// KEYWORDS: [PATTERN(7): PluginClass; DOMAIN(9): StatisticsSystem; TECH(7): Gradio]
// LINKS: [INHERITS_FROM(9): BaseMonitorPlugin]
// END_CONTRACT

class FinalStatsPlugin : public BaseMonitorPlugin {
public:
    // Статические константы (аналог class attributes в Python)
    static const std::string VERSION;
    static const std::string AUTHOR;
    static const std::string DESCRIPTION;
    static const int32_t DEFAULT_PRIORITY;

    // START_CONSTRUCTOR_FINAL_STATS_PLUGIN
    // START_CONTRACT:
    // PURPOSE: Конструктор плагина финальной статистики
    // OUTPUTS: Инициализированный объект плагина
    // SIDE_EFFECTS: Создает внутреннее состояние плагина; инициализирует историю сессий
    // KEYWORDS: [CONCEPT(5): Initialization; DOMAIN(7): PluginSetup]
    // END_CONTRACT
    FinalStatsPlugin();

    // Виртуальный деструктор
    virtual ~FinalStatsPlugin() override;

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
    // PURPOSE: Обработка обновления метрик от генератора (заглушка, не используется)
    // INPUTS:
    // - metrics: py::dict — словарь текущих метрик
    // OUTPUTS: void
    // SIDE_EFFECTS: Никаких действий (заглушка)
    // KEYWORDS: [DOMAIN(6): Placeholder; CONCEPT(7): EventHandler]
    // END_CONTRACT
    virtual void on_metric_update(py::dict metrics) override;

    // START_METHOD_ON_SHUTDOWN
    // START_CONTRACT:
    // PURPOSE: Действия при завершении работы мониторинга
    // INPUTS: Нет
    // OUTPUTS: void
    // SIDE_EFFECTS: Фиксирует время завершения; освобождение ресурсов
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

    // START_METHOD_UPDATE_UI
    // START_CONTRACT:
    // PURPOSE: Обновление UI компонентов значениями из финальных метрик
    // OUTPUTS: py::object — словарь с обновлёнными значениями для Gradio компонентов
    // KEYWORDS: [DOMAIN(9): UIUpdate; TECH(7): Gradio]
    // END_CONTRACT
    virtual py::object update_ui();

    // START_METHOD_GET_FINAL_METRICS
    // START_CONTRACT:
    // PURPOSE: Получение финальных метрик
    // OUTPUTS: py::dict — копия финальных метрик
    // KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): Statistics]
    // END_CONTRACT
    virtual py::dict get_final_metrics() const;

    // START_METHOD_GET_SUMMARY
    // START_CONTRACT:
    // PURPOSE: Получение текстовой сводки
    // OUTPUTS: std::string — текстовая сводка
    // KEYWORDS: [CONCEPT(6): Summary; DOMAIN(8): Statistics]
    // END_CONTRACT
    virtual std::string get_summary() const;

    // START_METHOD_EXPORT_JSON
    // START_CONTRACT:
    // PURPOSE: Экспорт статистики в JSON файл
    // INPUTS:
    // - file_path: const std::string& — путь к файлу
    // OUTPUTS: bool — true если экспорт успешен
    // SIDE_EFFECTS: Создаёт файл с данными
    // KEYWORDS: [DOMAIN(7): Export; TECH(5): JSON]
    // END_CONTRACT
    virtual bool export_json(const std::string& file_path) const;

    // START_METHOD_EXPORT_CSV
    // START_CONTRACT:
    // PURPOSE: Экспорт статистики в CSV файл
    // INPUTS:
    // - file_path: const std::string& — путь к файлу
    // OUTPUTS: bool — true если экспорт успешен
    // SIDE_EFFECTS: Создаёт файл CSV
    // KEYWORDS: [DOMAIN(7): Export; TECH(5): CSV]
    // END_CONTRACT
    virtual bool export_csv(const std::string& file_path) const;

    // START_METHOD_EXPORT_TXT
    // START_CONTRACT:
    // PURPOSE: Экспорт статистики в TXT файл (читаемый текстовый формат)
    // INPUTS:
    // - file_path: const std::string& — путь к файлу
    // OUTPUTS: std::string — путь к файлу при успехе или сообщение об ошибке
    // SIDE_EFFECTS: Создаёт текстовый файл с читабельным отчётом
    // KEYWORDS: [DOMAIN(7): Export; TECH(5): TXT]
    // END_CONTRACT
    virtual std::string export_txt(const std::string& file_path) const;

    // START_METHOD_GET_PERFORMANCE_ANALYSIS
    // START_CONTRACT:
    // PURPOSE: Получение анализа производительности
    // OUTPUTS: py::dict — анализ производительности
    // KEYWORDS: [DOMAIN(8): Performance; CONCEPT(7): Analysis]
    // END_CONTRACT
    virtual py::dict get_performance_analysis() const;

    // START_METHOD_IS_COMPLETE
    // START_CONTRACT:
    // PURPOSE: Проверка завершения сбора статистики
    // OUTPUTS: bool — True если статистика собрана
    // KEYWORDS: [CONCEPT(5): Getter]
    // END_CONTRACT
    virtual bool is_complete() const;

    // START_METHOD_RESET
    // START_CONTRACT:
    // PURPOSE: Сброс статистики
    // OUTPUTS: void
    // SIDE_EFFECTS: Очищает все данные
    // KEYWORDS: [CONCEPT(7): Reset]
    // END_CONTRACT
    virtual void reset();

    // START_METHOD_ADD_SESSION
    // START_CONTRACT:
    // PURPOSE: Добавление сессии в историю
    // INPUTS:
    // - metrics: py::dict — метрики сессии
    // OUTPUTS: void
    // KEYWORDS: [CONCEPT(7): History]
    // END_CONTRACT
    virtual void add_session(py::dict metrics);

    // START_METHOD_GET_SESSION_HISTORY
    // START_CONTRACT:
    // PURPOSE: Получение истории сессий
    // OUTPUTS: py::list — история сессий
    // KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): SessionHistory]
    // END_CONTRACT
    virtual py::list get_session_history() const;

    // START_METHOD_GET_TOTAL_STATISTICS
    // START_CONTRACT:
    // PURPOSE: Получение общей статистики по всем сессиям
    // OUTPUTS: py::dict — общая статистика
    // KEYWORDS: [DOMAIN(8): Aggregation; CONCEPT(7): Statistics]
    // END_CONTRACT
    virtual py::dict get_total_statistics() const;

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

    // START_METHOD_ON_FINISH
    // START_CONTRACT:
    // PURPOSE: Обработчик завершения генерации кошельков
    // INPUTS:
    // - final_metrics: py::dict — финальные метрики генерации
    // OUTPUTS: void
    // SIDE_EFFECTS: Фиксирует финальные метрики; вычисляет производные показатели
    // KEYWORDS: [DOMAIN(9): Finalization; CONCEPT(7): MetricsProcessing]
    // END_CONTRACT
    virtual void on_finish(py::dict final_metrics) override;

    // START_METHOD_GET_NAME
    // START_CONTRACT:
    // PURPOSE: Получение имени плагина
    // OUTPUTS: std::string — имя плагина
    // KEYWORDS: [CONCEPT(5): Getter]
    // END_CONTRACT
    virtual std::string get_name() const override;

    // START_METHOD_GET_PRIORITY
    // START_CONTRACT:
    // PURPOSE: Получения приоритета плагина
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
    // UI компоненты (Gradio)
    py::object _gradio_components;

    // Финальные метрики
    FinalStatistics _final_metrics;

    // Время начала генерации
    double _start_time;

    // Время завершения генерации
    double _end_time;

    // Флаг завершения
    bool _is_complete;

    // История сессий (аналог List[Dict] в Python)
    std::deque<SessionEntry> _session_history;

    // Счётчик сессий
    int32_t _session_counter;

    // Внутренние методы

    // START_METHOD_BUILD_UI_COMPONENTS
    // START_CONTRACT:
    // PURPOSE: Построение UI компонентов плагина для Gradio интерфейса
    // OUTPUTS: py::object — словарь UI компонентов
    // KEYWORDS: [DOMAIN(7): UI; CONCEPT(6): Builder]
    // END_CONTRACT
    py::object _build_ui_components();

    // START_METHOD_ON_ENTER_STAGE
    // START_CONTRACT:
    // PURPOSE: Обработчик входа на этап финальной статистики
    // OUTPUTS: void
    // KEYWORDS: [CONCEPT(7): StageHandler]
    // END_CONTRACT
    void _on_enter_stage();

    // START_METHOD_FORMAT_TIME
    // START_CONTRACT:
    // PURPOSE: Форматирование времени в читаемый вид
    // INPUTS:
    // - seconds: double — время в секундах
    // OUTPUTS: std::string — отформатированное время (HH:MM:SS)
    // KEYWORDS: [CONCEPT(7): Formatting]
    // END_CONTRACT
    std::string _format_time(double seconds) const;

    // START_METHOD_GENERATE_TITLE_HTML
    // START_CONTRACT:
    // PURPOSE: Генерация HTML заголовка секции
    // INPUTS:
    // - title: const std::string& — заголовок
    // OUTPUTS: std::string — HTML строка
    // KEYWORDS: [CONCEPT(6): HTML; TECH(5): Gradio]
    // END_CONTRACT
    std::string _generate_title_html(const std::string& title) const;

    // START_METHOD_CALCULATE_RUNTIME
    // START_CONTRACT:
    // PURPOSE: Вычисление времени работы и производных показателей
    // OUTPUTS: void
    // KEYWORDS: [DOMAIN(8): Calculation; CONCEPT(7): Metrics]
    // END_CONTRACT
    void _calculate_runtime();

    // START_METHOD_GET_CURRENT_TIME
    // START_CONTRACT:
    // PURPOSE: Получение текущего времени
    // OUTPUTS: double — Unix timestamp
    // KEYWORDS: [CONCEPT(6): Timestamp]
    // END_CONTRACT
    double _get_current_time() const;
};
// END_CLASS_FINAL_STATS_PLUGIN


// START_CLASS_FINAL_STATS_PLUGIN_TRAMPOLINE
// START_CONTRACT:
// PURPOSE: Trampoline класс для обеспечения возможности наследования от C++ класса FinalStatsPlugin в Python.
// Позволяет переопределять методы в Python и вызывать их из C++.
// KEYWORDS: [PATTERN(9): TrampolineClass; DOMAIN(9): Pybind11; TECH(7): PythonBindings]
// END_CONTRACT

class FinalStatsPluginTrampoline : public FinalStatsPlugin {
public:
    // Конструктор trampoline
    using FinalStatsPlugin::FinalStatsPlugin;

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
            FinalStatsPlugin,
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
            FinalStatsPlugin,
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
            FinalStatsPlugin,
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
            FinalStatsPlugin,
            get_ui_components
        );
    }

    // START_METHOD_UPDATE_UI_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода update_ui - позволяет переопределить в Python
    // OUTPUTS: py::object
    // END_CONTRACT
    py::object update_ui() override {
        PYBIND11_OVERRIDE(
            py::object,
            FinalStatsPlugin,
            update_ui
        );
    }

    // START_METHOD_GET_FINAL_METRICS_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода get_final_metrics - позволяет переопределить в Python
    // OUTPUTS: py::dict
    // END_CONTRACT
    py::dict get_final_metrics() const override {
        PYBIND11_OVERRIDE(
            py::dict,
            FinalStatsPlugin,
            get_final_metrics
        );
    }

    // START_METHOD_GET_SUMMARY_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода get_summary - позволяет переопределить в Python
    // OUTPUTS: std::string
    // END_CONTRACT
    std::string get_summary() const override {
        PYBIND11_OVERRIDE(
            std::string,
            FinalStatsPlugin,
            get_summary
        );
    }

    // START_METHOD_EXPORT_JSON_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода export_json - позволяет переопределить в Python
    // INPUTS:
    // - file_path: const std::string& — путь к файлу
    // OUTPUTS: bool
    // END_CONTRACT
    bool export_json(const std::string& file_path) const override {
        PYBIND11_OVERRIDE(
            bool,
            FinalStatsPlugin,
            export_json,
            file_path
        );
    }

    // START_METHOD_EXPORT_CSV_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода export_csv - позволяет переопределить в Python
    // INPUTS:
    // - file_path: const std::string& — путь к файлу
    // OUTPUTS: bool
    // END_CONTRACT
    bool export_csv(const std::string& file_path) const override {
        PYBIND11_OVERRIDE(
            bool,
            FinalStatsPlugin,
            export_csv,
            file_path
        );
    }

    // START_METHOD_EXPORT_TXT_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода export_txt - позволяет переопределить в Python
    // INPUTS:
    // - file_path: const std::string& — путь к файлу
    // OUTPUTS: std::string
    // END_CONTRACT
    std::string export_txt(const std::string& file_path) const override {
        PYBIND11_OVERRIDE(
            std::string,
            FinalStatsPlugin,
            export_txt,
            file_path
        );
    }

    // START_METHOD_GET_PERFORMANCE_ANALYSIS_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода get_performance_analysis - позволяет переопределить в Python
    // OUTPUTS: py::dict
    // END_CONTRACT
    py::dict get_performance_analysis() const override {
        PYBIND11_OVERRIDE(
            py::dict,
            FinalStatsPlugin,
            get_performance_analysis
        );
    }

    // START_METHOD_IS_COMPLETE_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода is_complete - позволяет переопределить в Python
    // OUTPUTS: bool
    // END_CONTRACT
    bool is_complete() const override {
        PYBIND11_OVERRIDE(
            bool,
            FinalStatsPlugin,
            is_complete
        );
    }

    // START_METHOD_RESET_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода reset - позволяет переопределить в Python
    // OUTPUTS: void
    // END_CONTRACT
    void reset() override {
        PYBIND11_OVERRIDE(
            void,
            FinalStatsPlugin,
            reset
        );
    }

    // START_METHOD_ADD_SESSION_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода add_session - позволяет переопределить в Python
    // INPUTS:
    // - metrics: py::dict — метрики сессии
    // OUTPUTS: void
    // END_CONTRACT
    void add_session(py::dict metrics) override {
        PYBIND11_OVERRIDE(
            void,
            FinalStatsPlugin,
            add_session,
            metrics
        );
    }

    // START_METHOD_GET_SESSION_HISTORY_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода get_session_history - позволяет переопределить в Python
    // OUTPUTS: py::list
    // END_CONTRACT
    py::list get_session_history() const override {
        PYBIND11_OVERRIDE(
            py::list,
            FinalStatsPlugin,
            get_session_history
        );
    }

    // START_METHOD_GET_TOTAL_STATISTICS_TRAMPOLINE
    // START_CONTRACT:
    // PURPOSE: Trampoline для метода get_total_statistics - позволяет переопределить в Python
    // OUTPUTS: py::dict
    // END_CONTRACT
    py::dict get_total_statistics() const override {
        PYBIND11_OVERRIDE(
            py::dict,
            FinalStatsPlugin,
            get_total_statistics
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
            FinalStatsPlugin,
            on_start,
            selected_list_path
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
            FinalStatsPlugin,
            on_finish,
            final_metrics
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
            FinalStatsPlugin,
            health_check
        );
    }
};
// END_CLASS_FINAL_STATS_PLUGIN_TRAMPOLINE


#endif // WALLET_MONITOR_FINAL_STATS_PLUGIN_HPP
