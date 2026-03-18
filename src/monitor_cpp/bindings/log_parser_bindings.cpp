// FILE: src/monitor_cpp/bindings/log_parser_bindings.cpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Python bindings для модуля log_parser через pybind11.
// Обеспечивает доступ к C++ классам LogParser, LogFilter, LogAggregator, LogWatcher из Python.
// SCOPE: Python интеграция, pybind11 bindings
// INPUTS: Python объекты
// OUTPUTS: Python extension module log_parser_cpp
// KEYWORDS: [TECH(9): pybind11; DOMAIN(8): PythonBindings; CONCEPT(7): Interop]
// END_MODULE_CONTRACT

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <pybind11/chrono.h>
#include <memory>
#include "../integrations/log_parser.hpp"

namespace py = pybind11;
using namespace pybind11::literals;

//==============================================================================
// Helper Functions
//==============================================================================

//==============================================================================
// ParsedEntry Binding
//==============================================================================

// START_FUNCTION_bind_parsed_entry
// START_CONTRACT:
// PURPOSE: Создание Python bindings для структуры ParsedEntry
// INPUTS: m - pybind11 модуль
// OUTPUTS: Добавление класса ParsedEntry в модуль
// KEYWORDS: [TECH(8): pybind11; CONCEPT(6): Binding]
// END_CONTRACT
void bind_parsed_entry(py::module& m) {
    py::class_<ParsedEntry>(m, "ParsedEntry")
        .def(py::init<>(), "Default constructor")
        .def(py::init<double, const std::string&>(), 
             py::arg("timestamp"), 
             py::arg("raw_line"),
             "Constructor with timestamp and raw line")
        .def(py::init<const ParsedEntry&>(), 
             py::arg("other"),
             "Copy constructor")
        .def_readwrite("timestamp", &ParsedEntry::timestamp)
        .def_readwrite("raw_line", &ParsedEntry::raw_line)
        .def_readwrite("iteration_count", &ParsedEntry::iteration_count)
        .def_readwrite("match_count", &ParsedEntry::match_count)
        .def_readwrite("wallet_count", &ParsedEntry::wallet_count)
        .def_readwrite("entropy_bits", &ParsedEntry::entropy_bits)
        .def_readwrite("stage", &ParsedEntry::stage)
        .def_readwrite("error", &ParsedEntry::error)
        .def("has_error", &ParsedEntry::has_error, "Check if entry has error")
        .def("has_iteration", &ParsedEntry::has_iteration, "Check if entry has iteration")
        .def("is_empty", &ParsedEntry::is_empty, "Check if entry is empty")
        .def("__repr__", &ParsedEntry::to_string);
}
// END_FUNCTION_bind_parsed_entry

//==============================================================================
// LogMetrics Binding
//==============================================================================

// START_FUNCTION_bind_log_metrics
// START_CONTRACT:
// PURPOSE: Создание Python bindings для структуры LogMetrics
// INPUTS: m - pybind11 модуль
// OUTPUTS: Добавление класса LogMetrics в модуль
// KEYWORDS: [TECH(8): pybind11; CONCEPT(6): Binding]
// END_CONTRACT
void bind_log_metrics(py::module& m) {
    py::class_<LogMetrics>(m, "LogMetrics")
        .def(py::init<>(), "Default constructor")
        .def(py::init<const LogMetrics&>(), 
             py::arg("other"),
             "Copy constructor")
        .def_readwrite("iteration_count", &LogMetrics::iteration_count)
        .def_readwrite("match_count", &LogMetrics::match_count)
        .def_readwrite("wallet_count", &LogMetrics::wallet_count)
        .def_readwrite("entropy_bits", &LogMetrics::entropy_bits)
        .def_readwrite("stage", &LogMetrics::stage)
        .def_readwrite("is_monitoring", &LogMetrics::is_monitoring)
        .def_readwrite("last_update_time", &LogMetrics::last_update_time)
        .def_readwrite("error_count", &LogMetrics::error_count)
        .def("reset", &LogMetrics::reset, "Reset metrics to default values")
        .def("to_dict", &LogMetrics::to_dict, "Convert to dictionary")
        .def("__repr__", &LogMetrics::to_string);
}
// END_FUNCTION_bind_log_metrics

//==============================================================================
// RegexPatterns Binding
//==============================================================================

// START_FUNCTION_bind_regex_patterns
// START_CONTRACT:
// PURPOSE: Создание Python bindings для класса RegexPatterns
// INPUTS: m - pybind11 модуль
// OUTPUTS: Добавление класса RegexPatterns в модуль
// KEYWORDS: [TECH(8): pybind11; CONCEPT(6): Binding]
// END_CONTRACT
void bind_regex_patterns(py::module& m) {
    py::class_<RegexPatterns>(m, "RegexPatterns")
        .def(py::init<>(), "Default constructor - compiles all patterns")
        .def("find_iteration", &RegexPatterns::find_iteration, 
             py::arg("line"),
             "Find iteration count in line")
        .def("find_match", &RegexPatterns::find_match, 
             py::arg("line"),
             "Find match count in line")
        .def("find_wallet", &RegexPatterns::find_wallet, 
             py::arg("line"),
             "Find wallet count in line")
        .def("find_entropy", &RegexPatterns::find_entropy, 
             py::arg("line"),
             "Find entropy bits in line")
        .def("find_stage", &RegexPatterns::find_stage, 
             py::arg("line"),
             "Find stage in line")
        .def("find_error", &RegexPatterns::find_error, 
             py::arg("line"),
             "Find error in line")
        .def("find_progress", &RegexPatterns::find_progress, 
             py::arg("line"),
             "Find progress in line")
        .def("find_address", &RegexPatterns::find_address, 
             py::arg("line"),
             "Find Bitcoin address in line")
        .def("search", &RegexPatterns::search, 
             py::arg("line"), 
             py::arg("pattern"),
             "Search for custom pattern")
        .def("get_pattern_names", &RegexPatterns::get_pattern_names,
             "Get list of available pattern names")
        .def_static("validate_pattern", &RegexPatterns::validate_pattern,
                    py::arg("pattern"),
                    "Validate a regex pattern");
}
// END_FUNCTION_bind_regex_patterns

//==============================================================================
// LogFilter Binding
//==============================================================================

// START_FUNCTION_bind_log_filter
// START_CONTRACT:
// PURPOSE: Создание Python bindings для класса LogFilter
// INPUTS: m - pybind11 модуль
// OUTPUTS: Добавление класса LogFilter в модуль
// KEYWORDS: [TECH(8): pybind11; CONCEPT(6): Binding]
// END_CONTRACT
void bind_log_filter(py::module& m) {
    py::enum_<LogFilter::Level>(m, "LogFilterLevel")
        .value("DEBUG", LogFilter::Level::DEBUG)
        .value("INFO", LogFilter::Level::INFO)
        .value("WARNING", LogFilter::Level::WARNING)
        .value("ERROR", LogFilter::Level::ERROR)
        .value("CRITICAL", LogFilter::Level::CRITICAL)
        .export_values();
    
    py::class_<LogFilter>(m, "LogFilter")
        .def(py::init<>(), "Default constructor")
        .def("set_min_level", &LogFilter::set_min_level, py::arg("level"),
             "Set minimum log level filter")
        .def("set_time_range", &LogFilter::set_time_range, 
             py::arg("start_time"), py::arg("end_time"),
             "Set time range filter")
        .def("set_pattern", &LogFilter::set_pattern, py::arg("pattern"),
             "Set regex pattern filter")
        .def("set_stages", &LogFilter::set_stages, py::arg("stages"),
             "Set stages filter")
        .def("apply", &LogFilter::apply, py::arg("entries"),
             "Apply filter to entries")
        .def("reset", &LogFilter::reset, "Reset all filters");
}
// END_FUNCTION_bind_log_filter

//==============================================================================
// LogAggregator Binding
//==============================================================================

// START_FUNCTION_bind_log_aggregator
// START_CONTRACT:
// PURPOSE: Создание Python bindings для класса LogAggregator
// INPUTS: m - pybind11 модуль
// OUTPUTS: Добавление класса LogAggregator в модуль
// KEYWORDS: [TECH(8): pybind11; CONCEPT(6): Binding]
// END_CONTRACT
void bind_log_aggregator(py::module& m) {
    py::class_<LogAggregator::Statistics>(m, "AggregatorStatistics")
        .def_readonly("min", &LogAggregator::Statistics::min)
        .def_readonly("max", &LogAggregator::Statistics::max)
        .def_readonly("avg", &LogAggregator::Statistics::avg)
        .def_readonly("median", &LogAggregator::Statistics::median)
        .def_readonly("stddev", &LogAggregator::Statistics::stddev)
        .def_readonly("count", &LogAggregator::Statistics::count);
    
    py::class_<LogAggregator>(m, "LogAggregator")
        .def(py::init<size_t>(), py::arg("max_history") = 10000,
             "Constructor with max history size")
        .def("add_entry", &LogAggregator::add_entry, py::arg("entry"),
             "Add entry for aggregation")
        .def("clear", &LogAggregator::clear, "Clear all data")
        .def("get_iteration_stats", &LogAggregator::get_iteration_stats,
             "Get iteration statistics")
        .def("get_match_stats", &LogAggregator::get_match_stats,
             "Get match statistics")
        .def("get_wallet_stats", &LogAggregator::get_wallet_stats,
             "Get wallet statistics")
        .def("get_stage_distribution", &LogAggregator::get_stage_distribution,
             "Get stage distribution")
        .def("get_time_range", &LogAggregator::get_time_range,
             "Get time range")
        .def("get_total_count", &LogAggregator::get_total_count,
             "Get total entry count");
}
// END_FUNCTION_bind_log_aggregator

//==============================================================================
// LogParser Binding
//==============================================================================

// START_FUNCTION_bind_log_parser
// START_CONTRACT:
// PURPOSE: Создание Python bindings для класса LogParser
// INPUTS: m - pybind11 модуль
// OUTPUTS: Добавление класса LogParser в модуль
// KEYWORDS: [TECH(8): pybind11; CONCEPT(6): Binding]
// END_CONTRACT
void bind_log_parser(py::module& m) {
    py::class_<LogParser>(m, "LogParser")
        .def(py::init<const std::string&, size_t>(),
             py::arg("log_file_path") = "logs/infinite_loop.log",
             py::arg("max_cache_size") = 1000,
             "Construct a LogParser instance")
        
        // -------------------------------------------------------------------------
        // PARSING METHODS
        // -------------------------------------------------------------------------
        
        .def("parse_file", &LogParser::parse_file,
             "Parse entire log file")
        
        .def("parse_new_lines", &LogParser::parse_new_lines,
             "Parse only new lines for real-time monitoring")
        
        .def("parse_new_lines_async", &LogParser::parse_new_lines_async,
             "Parse new lines asynchronously")
        
        .def("parse_line", &LogParser::parse_line,
             py::arg("line"),
             "Parse a single log line")
        
        // -------------------------------------------------------------------------
        // METRICS METHODS
        // -------------------------------------------------------------------------
        
        .def("get_current_metrics", &LogParser::get_current_metrics,
             "Get current metrics as LogMetrics object")
        
        .def("reset", &LogParser::reset,
             "Reset parser state")
        
        // -------------------------------------------------------------------------
        // CACHE METHODS
        // -------------------------------------------------------------------------
        
        .def("get_cached_entries", &LogParser::get_cached_entries,
             "Get cached log entries")
        
        .def("get_cache_size", &LogParser::get_cache_size,
             "Get number of cached entries")
        
        // -------------------------------------------------------------------------
        // ANALYTICS METHODS
        // -------------------------------------------------------------------------
        
        .def("get_iteration_rate", &LogParser::get_iteration_rate,
             py::arg("window_seconds") = 60,
             "Calculate iteration rate")
        
        .def("get_errors", &LogParser::get_errors,
             "Get all errors from cache")
        
        .def("get_stages", &LogParser::get_stages,
             "Get stage statistics")
        
        .def("get_progress", &LogParser::get_progress,
             "Get last progress value")
        
        // -------------------------------------------------------------------------
        // SEARCH METHODS
        // -------------------------------------------------------------------------
        
        .def("search_patterns", &LogParser::search_patterns,
             py::arg("pattern"),
             "Search entries by regex pattern")
        
        // -------------------------------------------------------------------------
        // MATCH EVENT METHODS
        // -------------------------------------------------------------------------
        
        .def("parse_match_event", &LogParser::parse_match_event,
             py::arg("log_line"),
             "Parse match event from log line")
        
        // -------------------------------------------------------------------------
        // FILE MANAGEMENT METHODS
        // -------------------------------------------------------------------------
        
        .def("set_log_file", &LogParser::set_log_file,
             py::arg("log_file_path"),
             "Set new log file path")
        
        .def("get_file_info", &LogParser::get_file_info,
             "Get file information")
        
        .def("is_monitoring", &LogParser::is_monitoring,
             "Check if monitoring is active")
        
        .def("has_new_data", &LogParser::has_new_data,
             "Check if there is new data in the file");
}
// END_FUNCTION_bind_log_parser

//==============================================================================
// LogWatcher Binding
//==============================================================================

// START_FUNCTION_bind_log_watcher
// START_CONTRACT:
// PURPOSE: Создание Python bindings для класса LogWatcher
// INPUTS: m - pybind11 модуль
// OUTPUTS: Добавление класса LogWatcher в модуль
// KEYWORDS: [TECH(8): pybind11; CONCEPT(6): Binding]
// END_CONTRACT
void bind_log_watcher(py::module& m) {
    py::class_<LogWatcher>(m, "LogWatcher")
        .def(py::init<const std::string&, std::shared_ptr<LogParser>>(),
             py::arg("log_file_path"),
             py::arg("parser"),
             "Construct a LogWatcher instance")
        
        .def("set_callback", &LogWatcher::set_callback, py::arg("callback"),
             "Set callback function for new data")
        
        .def("start", &LogWatcher::start, py::arg("interval") = 1.0,
             "Start watching for new data")
        
        .def("stop", &LogWatcher::stop,
             "Stop watching")
        
        .def("is_running", &LogWatcher::is_running,
             "Check if watcher is running")
        
        .def("check_for_updates", &LogWatcher::check_for_updates,
             "Manually check for updates");
}
// END_FUNCTION_bind_log_watcher

//==============================================================================
// Module Definition
//==============================================================================

// START_FUNCTION_PYBIND11_MODULE
// START_CONTRACT:
// PURPOSE: Определение Python extension module
// KEYWORDS: [TECH(9): pybind11; CONCEPT(7): Module]
// END_CONTRACT
PYBIND11_MODULE(log_parser_cpp, m) {
    m.doc() = "C++ Log Parser module for wallet generator monitoring";
    m.attr("__version__") = "1.0.0";
    
    bind_parsed_entry(m);
    bind_log_metrics(m);
    bind_regex_patterns(m);
    bind_log_filter(m);
    bind_log_aggregator(m);
    bind_log_parser(m);
    bind_log_watcher(m);
    
    // -------------------------------------------------------------------------
    // MODULE-LEVEL FUNCTIONS
    // -------------------------------------------------------------------------
    
    m.def("create_parser", 
          [](const std::string& path, size_t cache_size) {
              return std::make_unique<LogParser>(path, cache_size);
          },
          py::arg("log_file_path") = "logs/infinite_loop.log",
          py::arg("max_cache_size") = 1000,
          "Create a new LogParser instance");
    
    m.def("create_aggregator", 
          [](size_t max_history) {
              return std::make_unique<LogAggregator>(max_history);
          },
          py::arg("max_history") = 10000,
          "Create a new LogAggregator instance");
    
    m.def("create_filter", 
          []() {
              return std::make_unique<LogFilter>();
          },
          "Create a new LogFilter instance");
}

// END_FUNCTION_PYBIND11_MODULE
