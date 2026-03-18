/**
 * FILE: src/plugins/wallet/address_matcher/pybind11_wrapper.cpp
 * VERSION: 1.0.0
 * PURPOSE: Python bindings for Bitcoin address list comparison module.
 * LANGUAGE: C++11 with pybind11
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/chrono.h>
#include "address_matcher.h"

namespace py = pybind11;

// START_MODULE_CONTRACT:
// PURPOSE: Python-обертка для C++ реализации сравнения списков адресов.
// SCOPE: Экспорт класса AddressMatcher и его методов в Python.
// KEYWORDS: [TECH(9): pybind11; DOMAIN(8): PythonBindings; DOMAIN(9): AddressMatching]
// END_MODULE_CONTRACT

PYBIND11_MODULE(address_matcher_cpp, m) {
    m.doc() = "C++ implementation of Bitcoin address list comparison with switch-mode algorithm";
    
    // START_STRUCT_RawAddress_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт структуры RawAddress в Python.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(7): StructBinding]
    // END_CONTRACT
    py::class_<address_matcher::RawAddress>(m, "RawAddress")
        .def(py::init<>())
        .def(py::init([](const std::vector<unsigned char>& data) {
            if (data.size() != address_matcher::RAW_ADDRESS_SIZE) {
                throw std::runtime_error("Data must be exactly 25 bytes");
            }
            address_matcher::RawAddress result;
            memcpy(result.data, data.data(), address_matcher::RAW_ADDRESS_SIZE);
            return result;
        }), py::arg("data"))
        .def("get_data", [](const address_matcher::RawAddress& self) {
            return std::vector<unsigned char>(self.data, self.data + address_matcher::RAW_ADDRESS_SIZE);
        })
        .def("__eq__", [](const address_matcher::RawAddress& self, const address_matcher::RawAddress& other) {
            return self == other;
        });
    // END_STRUCT_RawAddress_PYBIND
    
    // START_STRUCT_MatchResult_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт структуры MatchResult в Python.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(7): StructBinding]
    // END_CONTRACT
    py::class_<address_matcher::MatchResult>(m, "MatchResult")
        .def(py::init<>())
        .def_readwrite("matches", &address_matcher::MatchResult::matches)
        .def_readwrite("mode_used", &address_matcher::MatchResult::mode_used)
        .def_readwrite("execution_time_ms", &address_matcher::MatchResult::execution_time_ms)
        .def_readwrite("lookup_size", &address_matcher::MatchResult::lookup_size)
        .def_readwrite("query_size", &address_matcher::MatchResult::query_size);
    // END_STRUCT_MatchResult_PYBIND
    
    // START_CLASS_AddressMatcherInterface_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт интерфейса AddressMatcherInterface в Python.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(8): InterfaceBinding]
    // END_CONTRACT
    py::class_<address_matcher::AddressMatcherInterface>(m, "AddressMatcherInterface")
        .def("decode_base58", &address_matcher::AddressMatcherInterface::decodeBase58,
             py::arg("address"),
             "Decode Base58 address to raw binary format (25 bytes).")
        .def("encode_base58", &address_matcher::AddressMatcherInterface::encodeBase58,
             py::arg("raw"),
             "Encode raw binary address to Base58 string.")
        .def("load_addresses_from_file", &address_matcher::AddressMatcherInterface::loadAddressesFromFile,
             py::arg("filepath"),
             "Load addresses from text file (one per line).")
        .def("find_intersection", &address_matcher::AddressMatcherInterface::findIntersection,
             py::arg("list1"),
             py::arg("list2"),
             "Find intersection between two address lists using switch-mode algorithm.")
        .def("generate_list1", &address_matcher::AddressMatcherInterface::generateList1,
             py::arg("entropy_data"),
             "Generate LIST_1 (1000 addresses) from entropy data.");
    // END_CLASS_AddressMatcherInterface_PYBIND
    
    // START_CLASS_AddressMatcher_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт класса AddressMatcher в Python.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(8): ClassBinding; DOMAIN(9): AddressMatching]
    // END_CONTRACT
    py::class_<address_matcher::AddressMatcher, 
               address_matcher::AddressMatcherInterface>(m, "AddressMatcher")
        .def(py::init<>(),
             "Initialize address matcher.")
        .def("decode_base58", &address_matcher::AddressMatcher::decodeBase58,
             py::arg("address"),
             "Decode Base58 address to raw binary format (25 bytes).")
        .def("encode_base58", &address_matcher::AddressMatcher::encodeBase58,
             py::arg("raw"),
             "Encode raw binary address to Base58 string.")
        .def("load_addresses_from_file", &address_matcher::AddressMatcher::loadAddressesFromFile,
             py::arg("filepath"),
             "Load addresses from text file (one per line).")
        .def("find_intersection", &address_matcher::AddressMatcher::findIntersection,
             py::arg("list1"),
             py::arg("list2"),
             "Find intersection between two address lists using switch-mode algorithm.")
        .def("generate_list1", &address_matcher::AddressMatcher::generateList1,
             py::arg("entropy_data"),
             "Generate LIST_1 (1000 addresses) from entropy data.");
    // END_CLASS_AddressMatcher_PYBIND
    
    // START_FUNCTION_create_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт фабричной функции create в Python.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(8): FactoryFunction]
    // END_CONTRACT
    m.def("create", &address_matcher::AddressMatcherPluginFactory::create,
          "Create new address matcher instance.");
    // END_FUNCTION_create_PYBIND
    
    // START_FUNCTION_get_version_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт функции getVersion в Python.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(7): VersionInfo]
    // END_CONTRACT
    m.def("get_version", &address_matcher::AddressMatcherPluginFactory::getVersion,
          "Get plugin version.");
    // END_FUNCTION_get_version_PYBIND
    
    // Constants
    m.attr("RAW_ADDRESS_SIZE") = address_matcher::RAW_ADDRESS_SIZE;
    m.attr("DEFAULT_LIST1_SIZE") = address_matcher::DEFAULT_LIST1_SIZE;
    m.attr("MAX_LIST_SIZE") = address_matcher::MAX_LIST_SIZE;
}
