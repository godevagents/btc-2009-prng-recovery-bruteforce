// FILE: src/core/entropy_engine_bindings.cpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Python bindings для EntropyEngine класса.
// SCOPE: Экспорт EntropyEngine в Python с поддержкой XOR и HASH стратегий.
// INPUT: Вызовы из Python кода для создания экземпляров и вызова методов.
// OUTPUT: Энтропия в виде bytes или список доступных источников.
// KEYWORDS: [TECH(10): Pybind11; CONCEPT(8): Python_Binding; DOMAIN(9): EntropyCoordination]
// LINKS: [USES_API(10): pybind11; WRAPS(9): entropy_engine.h]
// END_MODULE_CONTRACT

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <iostream>
#include "entropy_engine.hpp"

namespace py = pybind11;

// START_MODULE_ENTROPY_ENGINE_PYBIND
// START_CONTRACT:
// PURPOSE: Создание Python модуля для EntropyEngine класса.
// KEYWORDS: [TECH(10): Pybind11; CONCEPT(8): Python_Binding]
// END_CONTRACT

PYBIND11_MODULE(entropy_engine_cpp, m) {
    m.doc() = "EntropyEngine C++ module - coordinator of entropy sources with XOR and HASH combining strategies";
    
    // START_ENUM_CombineStrategy_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт перечисления CombineStrategy в Python.
    // KEYWORDS: [TECH(10): pybind11; CONCEPT(9): EnumBinding]
    // END_CONTRACT
    py::enum_<CombineStrategy>(m, "CombineStrategy")
        .value("XOR", CombineStrategy::XOR, "XOR strategy for combining entropy")
        .value("HASH", CombineStrategy::HASH, "HASH (SHA-256) strategy for combining entropy")
        .export_values();
    // END_ENUM_CombineStrategy_PYBIND
    
    // START_STRUCT_SourceStatus_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт структуры SourceStatus в Python.
    // KEYWORDS: [TECH(10): pybind11; CONCEPT(8): StructBinding]
    // END_CONTRACT
    py::class_<SourceStatus>(m, "SourceStatus")
        .def(py::init<>())
        .def_readwrite("name", &SourceStatus::name)
        .def_readwrite("available", &SourceStatus::available)
        .def_readwrite("initialized", &SourceStatus::initialized);
    // END_STRUCT_SourceStatus_PYBIND
    
    // START_CLASS_EntropyEngine_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт класса EntropyEngine в Python.
    // KEYWORDS: [TECH(10): pybind11; CONCEPT(9): ClassBinding; DOMAIN(10): EntropyCoordination]
    // END_CONTRACT
    py::class_<EntropyEngine>(m, "EntropyEngine")
        .def(py::init<>(),
             "Initialize EntropyEngine with default state.")
        .def("add_source", &EntropyEngine::add_source,
             py::arg("name"), py::arg("generator"),
             "Add an entropy source to the coordinator.\n"
             "Args:\n"
             "    name: Name of the entropy source (str)\n"
             "    generator: A callable that takes size (int) and returns bytes")
        .def("remove_source", &EntropyEngine::remove_source,
             py::arg("source_name"),
             "Remove an entropy source from the coordinator.\n"
             "Args:\n"
             "    source_name: Name of the source to remove (str)")
        .def("get_available_sources", &EntropyEngine::get_available_sources,
             "Get list of available entropy source names.\n"
             "Returns:\n"
             "    list: List of source names")
        .def("get_entropy", [](EntropyEngine& self, size_t size, const std::string& source_name) -> py::bytes {
            std::vector<uint8_t> result = self.get_entropy(size, source_name);
            return py::bytes(reinterpret_cast<const char*>(result.data()), result.size());
        }, py::arg("size"), py::arg("source_name") = "",
             "Get entropy from specified source or first available.\n"
             "Args:\n"
             "    size: Number of bytes to generate (int)\n"
             "    source_name: Name of source (str, optional)\n"
             "Returns:\n"
             "    bytes: Entropy data")
        .def("get_combined_entropy", [](EntropyEngine& self, size_t size, CombineStrategy strategy) -> py::bytes {
            std::vector<uint8_t> result = self.get_combined_entropy(size, strategy);
            return py::bytes(reinterpret_cast<const char*>(result.data()), result.size());
        }, py::arg("size"), py::arg("strategy") = CombineStrategy::XOR,
             "Get combined entropy from all available sources.\n"
             "Args:\n"
             "    size: Number of bytes to generate (int)\n"
             "    strategy: CombineStrategy.XOR or CombineStrategy.HASH\n"
             "Returns:\n"
             "    bytes: Combined entropy data")
        .def("get_source_status", &EntropyEngine::get_source_status,
             "Get status of all entropy sources.\n"
             "Returns:\n"
             "    list: List of SourceStatus objects")
        .def("is_initialized", &EntropyEngine::is_initialized,
             "Check if engine is initialized.\n"
             "Returns:\n"
             "    bool: True if initialized")
        .def("source_count", &EntropyEngine::source_count,
             "Get number of registered sources.\n"
             "Returns:\n"
             "    int: Number of sources");
    // END_CLASS_EntropyEngine_PYBIND
}
// END_MODULE_ENTROPY_ENGINE_PYBIND
