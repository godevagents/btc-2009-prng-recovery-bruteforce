// FILE: src/monitor_cpp/bindings/metrics_bindings.cpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Python bindings для модуля metrics с использованием pybind11
// SCOPE: Python-C++ interoperability, pybind11 bindings
// INPUTS: Python объекты (dict, function)
// OUTPUTS: Python extension module metrics_cpp
// KEYWORDS: [TECH(9): pybind11; DOMAIN(8): PythonBindings; CONCEPT(7): Interop]
// END_MODULE_CONTRACT

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/chrono.h>
#include <pybind11/functional.h>
#include <memory>
#include "metrics.hpp"

namespace py = pybind11;
using namespace pybind11::literals;

//==============================================================================
// Helper Functions
//==============================================================================

/**
 * @brief Конвертация Python dict в MetricsMap
 * @param dict Python словарь
 * @return C++ MetricsMap
 * @details
 * - Рекурсивно обрабатывает вложенные словари
 * - Поддерживает: int, float, str, dict
 * - Остальные типы конвертируются в строковое представление
 */
MetricsMap py_dict_to_metrics_map(const py::dict& dict) {
    MetricsMap result;
    for (auto [key, value] : dict) {
        std::string name = py::str(key).cast<std::string>();
        
        if (py::isinstance<py::int_>(value)) {
            result[name] = value.cast<int64_t>();
        } else if (py::isinstance<py::float_>(value)) {
            result[name] = value.cast<double>();
        } else if (py::isinstance<py::str>(value)) {
            result[name] = value.cast<std::string>();
        } else if (py::isinstance<py::dict>(value)) {
            // Рекурсивная обработка вложенных словарей
            result[name] = py_dict_to_metrics_map(value.cast<py::dict>());
        } else {
            // Default: строковое представление
            result[name] = py::str(value).cast<std::string>();
        }
    }
    return result;
}

//==============================================================================
// MetricEntry Binding
//==============================================================================

// START_FUNCTION_bind_metric_entry
// START_CONTRACT:
// PURPOSE: Создание Python bindings для структуры MetricEntry
// INPUTS: m - pybind11 модуль
// OUTPUTS: Добавление класса MetricEntry в модуль
// KEYWORDS: [TECH(8): pybind11; CONCEPT(6): Binding]
// END_CONTRACT
void bind_metric_entry(py::module& m) {
    py::class_<MetricEntry>(m, "MetricEntry")
        .def(py::init<>())
        .def(py::init<const MetricValue&>())
        .def(py::init<const MetricValue&, const std::map<std::string, MetricValue>&>())
        .def_readwrite("timestamp", &MetricEntry::timestamp)
        .def_readwrite("value", &MetricEntry::value)
        .def_readwrite("metadata", &MetricEntry::metadata)
        .def("__repr__", [](const MetricEntry& e) {
            return "<MetricEntry>";
        });
}

// END_FUNCTION_bind_metric_entry

//==============================================================================
// MetricsStore Binding
//==============================================================================

// START_FUNCTION_bind_metrics_store
// START_CONTRACT:
// PURPOSE: Создание Python bindings для класса MetricsStore
// INPUTS: m - pybind11 модуль
// OUTPUTS: Добавление класса MetricsStore в модуль
// KEYWORDS: [TECH(8): pybind11; CONCEPT(6): Binding]
// END_CONTRACT
void bind_metrics_store(py::module& m) {
    py::class_<MetricsStore, std::shared_ptr<MetricsStore>>(m, "MetricsStore")
        .def(py::init<size_t>(), "max_history_size"_a = 10000)
        
        // Константы
        .def_readonly_static("ITERATION_COUNT", &MetricsStore::ITERATION_COUNT)
        .def_readonly_static("MATCH_COUNT", &MetricsStore::MATCH_COUNT)
        .def_readonly_static("WALLET_COUNT", &MetricsStore::WALLET_COUNT)
        .def_readonly_static("ELAPSED_TIME", &MetricsStore::ELAPSED_TIME)
        .def_readonly_static("ENTROPY_DATA", &MetricsStore::ENTROPY_DATA)
        .def_readonly_static("ADDRESSES_EXTRACTED", &MetricsStore::ADDRESSES_EXTRACTED)
        .def_readonly_static("MATCHES_FOUND", &MetricsStore::MATCHES_FOUND)
        .def_readonly_static("ITERATIONS_PER_SECOND", &MetricsStore::ITERATIONS_PER_SECOND)
        .def_readonly_static("WALLETS_PER_SECOND", &MetricsStore::WALLETS_PER_SECOND)
        
        // Основные операции
        .def("update", [](MetricsStore& self, const py::dict& dict) {
            self.update(py_dict_to_metrics_map(dict));
        }, "metrics"_a)
        .def("get_current", &MetricsStore::get_current)
        .def("get_history", &MetricsStore::get_history, 
             "metric_name"_a, "limit"_a = std::nullopt)
        
        // Вычисления
        .def("compute_rate", &MetricsStore::compute_rate,
             "metric_name"_a, "window_seconds"_a = 60)
        
        // Сводка
        .def("get_summary", &MetricsStore::get_summary)
        
        // Управление
        .def("reset", &MetricsStore::reset)
        .def("reset_metric", &MetricsStore::reset_metric, "metric_name"_a)
        .def("get_metric_names", &MetricsStore::get_metric_names)
        
        // Подписка
        .def("subscribe", [](MetricsStore& self, py::function callback) {
            MetricCallback cpp_callback = [callback](const MetricsMap& metrics) {
                // Конвертация MetricsMap обратно в Python dict
                py::dict py_dict;
                for (const auto& [key, value] : metrics) {
                    // Упрощённая конвертация
                    py::object py_value;
                    if (std::holds_alternative<int64_t>(value)) {
                        py_value = py::int_(std::get<int64_t>(value));
                    } else if (std::holds_alternative<double>(value)) {
                        py_value = py::float_(std::get<double>(value));
                    } else if (std::holds_alternative<std::string>(value)) {
                        py_value = py::str(std::get<std::string>(value));
                    } else {
                        py_value = py::none();
                    }
                    py_dict[key.c_str()] = py_value;
                }
                callback(py_dict);
            };
            self.subscribe(cpp_callback);
        }, "callback"_a)
        .def("unsubscribe", [](MetricsStore& self, py::function callback) {
            // Примечание: полная реализация требует сохранения указателя на callback
            // Для упрощения - можно использовать weak approach
        }, "callback"_a)
        
        // Snapshot
        .def("get_snapshot", &MetricsStore::get_snapshot);
    
    // Snapshot binding
    py::class_<MetricsStore::Snapshot>(m, "MetricsSnapshot")
        .def_readonly("current", &MetricsStore::Snapshot::current)
        .def_readonly("history", &MetricsStore::Snapshot::history)
        .def_readonly("timestamp", &MetricsStore::Snapshot::timestamp)
        .def_readonly("update_count", &MetricsStore::Snapshot::update_count);
}

// END_FUNCTION_bind_metrics_store

//==============================================================================
// MetricsCollector Binding
//==============================================================================

// START_FUNCTION_bind_metrics_collector
// START_CONTRACT:
// PURPOSE: Создание Python bindings для класса MetricsCollector
// INPUTS: m - pybind11 модуль
// OUTPUTS: Добавление класса MetricsCollector в модуль
// KEYWORDS: [TECH(8): pybind11; CONCEPT(6): Binding]
// END_CONTRACT
void bind_metrics_collector(py::module& m) {
    py::class_<MetricsCollector>(m, "MetricsCollector")
        .def(py::init<std::shared_ptr<MetricsStore>, double>(),
             "metrics_store"_a, "collection_interval"_a = 1.0)
        
        // Управление источниками
        .def("add_source", [](MetricsCollector& self, const std::string& name, py::function collector_fn) {
            CollectorFunction cpp_fn = [collector_fn]() -> MetricsMap {
                py::dict result = collector_fn();
                return py_dict_to_metrics_map(result);
            };
            self.add_source(name, cpp_fn);
        }, "name"_a, "collector_fn"_a)
        .def("remove_source", &MetricsCollector::remove_source, "name"_a)
        
        // Управление сбором
        .def("start", &MetricsCollector::start)
        .def("stop", &MetricsCollector::stop)
        .def("collect", &MetricsCollector::collect)
        
        // Получение метрик
        .def("get_current_metrics", &MetricsCollector::get_current_metrics)
        
        // Состояние
        .def_property_readonly("is_collecting", &MetricsCollector::is_collecting);
}

// END_FUNCTION_bind_metrics_collector

//==============================================================================
// Module Definition
//==============================================================================

// START_FUNCTION_PYBIND11_MODULE
// START_CONTRACT:
// PURPOSE: Определение Python extension module
// KEYWORDS: [TECH(9): pybind11; CONCEPT(7): Module]
// END_CONTRACT
PYBIND11_MODULE(metrics_cpp, m) {
    m.doc() = "C++ implementation of metrics module for wallet generation monitoring";
    
    bind_metric_entry(m);
    bind_metrics_store(m);
    bind_metrics_collector(m);
}

// END_FUNCTION_PYBIND11_MODULE
