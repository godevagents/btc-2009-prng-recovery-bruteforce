// FILE: src/plugins/cpu/randaddseed/pybind11_wrapper.cpp
// VERSION: 1.2.0
// START_MODULE_CONTRACT:
// PURPOSE: Python bindings для модуля hkey_performance_data. Обеспечивает интеграцию
// C++ реализации генерации HKEY_PERFORMANCE_DATA с Python через pybind11.
// SCOPE: Экспорт функций генерации данных производительности в Python пространство имен.
// INPUT: Вызовы из Python кода с параметрами seconds_passed и rand_add_impl.
// OUTPUT: Возврат бинарных данных в Python в виде bytes или модификация состояния PRNG.
// KEYWORDS: [TECH(9): PyBind11; DOMAIN(8): PythonIntegration; CONCEPT(7): Interop]
// LINKS: [USES_API(9): pybind11; WRAPS(8): hkey_performance_data.cpp; USES(8): rand_add.h]
// END_MODULE_CONTRACT
// START_MODULE_MAP:
// FUNC 9 [Экспортирует legacy функцию генерации HKEY_PERFORMANCE_DATA] => generate_hkey_performance_data_legacy
// FUNC 9 [Экспортирует новую функцию с RAND_add] => generate_hkey_performance_data
// FUNC 9 [Экспортирует функцию генерации QueryPerformanceCounter] => generate_query_performance_counter
// END_MODULE_MAP
// START_USE_CASES:
// - [generate_hkey_performance_data_legacy]: PythonCode (EntropyGeneration) -> CallCPPFunction -> GetPerformanceData
// - [generate_hkey_performance_data]: BitcoinCore (Startup) -> AddEntropyToPRNG -> PRNGStateUpdated
// - [generate_query_performance_counter]: BitcoinCore (Startup) -> AddEntropyFromPerformanceCounter -> PRNGStateUpdated
// END_USE_CASES

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <stdexcept>
#include <iostream>
#include <fstream>
#include <sstream>
#include "hkey_performance_data.h"
#include "QueryPerformanceCounter.h"
#include "rand_add.h"

// =============================================================================
// LOGGING UTILITIES
// =============================================================================

inline void LogToAiState(const std::string& classifier, const std::string& func, 
                         const std::string& block, const std::string& op, 
                         const std::string& desc, const std::string& status) {
    std::string logLine = "[" + classifier + "][" + func + "][" + block + "][" + op + "] " + desc + " [" + status + "]";
    // Console output removed - logs only to file
    std::ofstream logFile("app.log", std::ios_base::app);
    if (logFile.is_open()) {
        logFile << logLine << std::endl;
    }
}

#define LOG_TRACE(classifier, func, block, op, desc, status) \
    LogToAiState(classifier, func, block, op, desc, status);

namespace py = pybind11;

// START_MODULE_hkey_performance_data_cpp
PYBIND11_MODULE(hkey_performance_data_cpp, m) {
    m.doc() = "HKEY_PERFORMANCE_DATA generation for Windows XP entropy reconstruction";

    // START_FUNCTION_generate_hkey_performance_data_legacy_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт legacy функции генерации дампа.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(8): FunctionBinding]
    // END_CONTRACT
    m.def(
        "generate_hkey_performance_data_legacy",
        [](int seconds_passed = 0) -> py::bytes {
            const char* FuncName = "generate_hkey_performance_data_legacy";
            LOG_TRACE("VarCheck", FuncName, "INPUT_PARAMS", "Params", 
                      "Вызов legacy генератора, seconds_passed: " + std::to_string(seconds_passed), "INFO");
            
            std::vector<uint8_t> data = generate_hkey_performance_data_legacy(seconds_passed);
            
            LOG_TRACE("TraceCheck", FuncName, "GENERATE_COMPLETE", "ReturnData", 
                      "Сгенерировано данных: " + std::to_string(data.size()) + " байт", "SUCCESS");
            
            return py::bytes(reinterpret_cast<const char*>(data.data()), data.size());
        },
        py::arg("seconds_passed") = 0,
        "Generate HKEY_PERFORMANCE_DATA dump mimicking RegQueryValueEx on SATOSHI-PC (legacy version).\n"
        "Args:\n"
        "    seconds_passed: Number of seconds passed from base time (default: 0)\n"
        "Returns:\n"
        "    bytes: Binary buffer containing PERF_DATA_BLOCK structure"
    );
    // END_FUNCTION_generate_hkey_performance_data_legacy_PYBIND

    // START_FUNCTION_generate_hkey_performance_data_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт новой функции с RAND_add и проверкой на nullptr.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(8): FunctionBinding; CONCEPT(7): NullCheck]
    // END_CONTRACT
    m.def(
        "generate_hkey_performance_data",
        [](int seconds_passed, RandAddImplementation* rand_add_impl) {
            const char* FuncName = "generate_hkey_performance_data";
            LOG_TRACE("VarCheck", FuncName, "INPUT_PARAMS", "Params", 
                      "seconds_passed: " + std::to_string(seconds_passed) + ", rand_add_impl: " + 
                      (rand_add_impl ? "valid" : "nullptr"), "INFO");
            
            // START_BLOCK_VALIDATE_INPUT: [Проверка входного указателя на nullptr.]
            if (!rand_add_impl) {
                LOG_TRACE("CriticalError", FuncName, "VALIDATE_INPUT", "ExceptionCaught", 
                          "rand_add_impl не может быть nullptr", "FAIL");
                throw std::runtime_error("rand_add_impl cannot be null");
            }
            LOG_TRACE("VarCheck", FuncName, "VALIDATE_INPUT", "ConditionCheck", 
                      "rand_add_impl валиден", "SUCCESS");
            // END_BLOCK_VALIDATE_INPUT

            // START_BLOCK_CALL_FUNCTION: [Вызов функции generate_hkey_performance_data.]
            LOG_TRACE("CallExternal", FuncName, "CALL_FUNCTION", "CallExternal", 
                      "Вызов generate_hkey_performance_data", "ATTEMPT");
            
            generate_hkey_performance_data(seconds_passed, rand_add_impl);
            
            LOG_TRACE("TraceCheck", FuncName, "CALL_FUNCTION", "StepComplete", 
                      "generate_hkey_performance_data выполнена", "SUCCESS");
            // END_BLOCK_CALL_FUNCTION
        },
        py::arg("seconds_passed"), py::arg("rand_add_impl"),
        "Generate HKEY_PERFORMANCE_DATA dump, compute SHA256 hash and call RAND_add (Bitcoin 0.1.0 style).\n"
        "Args:\n"
        "    seconds_passed: Number of seconds passed from base time\n"
        "    rand_add_impl: RandAddImplementation instance for adding entropy (required)\n"
        "Raises:\n"
        "    RuntimeError: If rand_add_impl is null\n"
        "Note:\n"
        "    This function does not return data; it modifies PRNG state via RAND_add"
    );
    // END_FUNCTION_generate_hkey_performance_data_PYBIND

    // START_FUNCTION_generate_query_performance_counter_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт функции генерации QueryPerformanceCounter с RAND_add.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(8): FunctionBinding; CONCEPT(7): NullCheck]
    // END_CONTRACT
    m.def(
        "generate_query_performance_counter",
        [](RandAddImplementation* rand_add_impl) {
            const char* FuncName = "generate_query_performance_counter";
            LOG_TRACE("VarCheck", FuncName, "INPUT_PARAMS", "Params", 
                      "rand_add_impl: " + std::string(rand_add_impl ? "valid" : "nullptr"), "INFO");
            
            // START_BLOCK_VALIDATE_INPUT: [Проверка входного указателя на nullptr.]
            if (!rand_add_impl) {
                LOG_TRACE("CriticalError", FuncName, "VALIDATE_INPUT", "ExceptionCaught", 
                          "rand_add_impl не может быть nullptr", "FAIL");
                throw std::runtime_error("rand_add_impl cannot be null");
            }
            LOG_TRACE("VarCheck", FuncName, "VALIDATE_INPUT", "ConditionCheck", 
                      "rand_add_impl валиден", "SUCCESS");
            // END_BLOCK_VALIDATE_INPUT

            // START_BLOCK_CALL_FUNCTION: [Вызов функции generate_query_performance_counter.]
            LOG_TRACE("CallExternal", FuncName, "CALL_FUNCTION", "CallExternal", 
                      "Вызов generate_query_performance_counter", "ATTEMPT");
            
            generate_query_performance_counter(rand_add_impl);
            
            LOG_TRACE("TraceCheck", FuncName, "CALL_FUNCTION", "StepComplete", 
                      "generate_query_performance_counter выполнена", "SUCCESS");
            // END_BLOCK_CALL_FUNCTION
        },
        py::arg("rand_add_impl"),
        "Generate random QueryPerformanceCounter value, compute SHA256 hash and call RAND_add (Bitcoin 0.1.0 style).\n"
        "Args:\n"
        "    rand_add_impl: RandAddImplementation instance for adding entropy (required)\n"
        "Raises:\n"
        "    RuntimeError: If rand_add_impl is null\n"
        "Note:\n"
        "    This function does not return data; it modifies PRNG state via RAND_add"
    );
    // END_FUNCTION_generate_query_performance_counter_PYBIND
}
// END_MODULE_hkey_performance_data_cpp
