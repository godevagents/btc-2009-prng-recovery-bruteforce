/**
 * FILE: src/plugins/wallet/batch_gen/pybind11_wrapper.cpp
 * VERSION: 1.0.0
 * PURPOSE: Python bindings for batch wallet generation module.
 * LANGUAGE: C++11 with pybind11
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "batch_gen.h"

namespace py = pybind11;

// START_MODULE_CONTRACT:
// PURPOSE: Python-обертка для C++ реализации пакетной генерации кошельков.
// SCOPE: Экспорт класса BatchWalletGenerator и его методов в Python.
// KEYWORDS: [TECH(9): pybind11; DOMAIN(8): PythonBindings; DOMAIN(7): BatchWallet]
// END_MODULE_CONTRACT

PYBIND11_MODULE(batch_gen_cpp, m) {
    m.doc() = "C++ implementation of batch wallet generation (1000 wallets from single entropy)";
    
    // START_STRUCT_WalletData_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт структуры WalletData в Python.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(7): StructBinding]
    // END_CONTRACT
    py::class_<wallet_batch::WalletData>(m, "WalletData")
        .def(py::init<>())
        .def_readwrite("index", &wallet_batch::WalletData::index)
        .def_readwrite("public_key", &wallet_batch::WalletData::public_key)
        .def_readwrite("private_key", &wallet_batch::WalletData::private_key)
        .def_readwrite("address", &wallet_batch::WalletData::address)
        .def_readwrite("timestamp", &wallet_batch::WalletData::timestamp)
        .def_readwrite("entropy_source", &wallet_batch::WalletData::entropy_source);
    // END_STRUCT_WalletData_PYBIND

    // START_STRUCT_WalletDBEntry_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт структуры WalletDBEntry в Python.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(7): StructBinding]
    // END_CONTRACT
    py::class_<wallet_batch::WalletDBEntry>(m, "WalletDBEntry")
        .def(py::init<>())
        .def_readwrite("key_type", &wallet_batch::WalletDBEntry::key_type)
        .def_readwrite("key_data", &wallet_batch::WalletDBEntry::key_data)
        .def_readwrite("value_data", &wallet_batch::WalletDBEntry::value_data);
    // END_STRUCT_WalletDBEntry_PYBIND

    // START_CLASS_WalletCollection_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт класса WalletCollection в Python.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(8): ClassBinding]
    // END_CONTRACT
    py::class_<wallet_batch::WalletCollection>(m, "WalletCollection")
        .def(py::init<>())
        .def("add_wallet", &wallet_batch::WalletCollection::addWallet,
             py::arg("wallet"),
             "Add wallet to collection.")
        .def("get_wallet_at", &wallet_batch::WalletCollection::getWalletAt,
             py::arg("index"),
             "Get wallet at index.")
        .def("size", &wallet_batch::WalletCollection::size,
             "Get collection size.")
        .def("clear", &wallet_batch::WalletCollection::clear,
             "Clear collection.")
        .def("get_all", &wallet_batch::WalletCollection::getAll,
             "Get all wallets.")
        .def("to_db_entries", &wallet_batch::WalletCollection::toDBEntries,
             "Convert to DB entries.");
    // END_CLASS_WalletCollection_PYBIND

    // START_CLASS_BatchWalletGeneratorInterface_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт интерфейса BatchWalletGeneratorInterface в Python.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(8): InterfaceBinding]
    // END_CONTRACT
    py::class_<wallet_batch::BatchWalletGeneratorInterface>(m, "BatchWalletGeneratorInterface")
        .def("initialize", &wallet_batch::BatchWalletGeneratorInterface::initialize)
        .def("generate_wallets", &wallet_batch::BatchWalletGeneratorInterface::generateWallets)
        .def("get_wallet_at_index", &wallet_batch::BatchWalletGeneratorInterface::getWalletAtIndex)
        .def("export_to_db_format", &wallet_batch::BatchWalletGeneratorInterface::exportToDBFormat)
        .def("get_wallet_count", &wallet_batch::BatchWalletGeneratorInterface::getWalletCount);
    // END_CLASS_BatchWalletGeneratorInterface_PYBIND

    // START_CLASS_BatchWalletGenerator_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт класса BatchWalletGenerator в Python.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(8): ClassBinding; DOMAIN(7): BatchWallet]
    // END_CONTRACT
    py::class_<wallet_batch::BatchWalletGenerator, 
               wallet_batch::BatchWalletGeneratorInterface>(m, "BatchWalletGenerator")
        .def(py::init<>(),
             "Initialize batch wallet generator.")
        .def("initialize", &wallet_batch::BatchWalletGenerator::initialize,
             py::arg("entropy_data"),
             "Initialize with entropy snapshot data.")
        .def("generate_wallets", &wallet_batch::BatchWalletGenerator::generateWallets,
             py::arg("count") = 1000,
             py::arg("deterministic") = true,
             "Generate wallets (default: 1000, deterministic mode).")
        .def("get_wallet_at_index", &wallet_batch::BatchWalletGenerator::getWalletAtIndex,
             py::arg("index"),
             "Get wallet at specific index.")
        .def("export_to_db_format", &wallet_batch::BatchWalletGenerator::exportToDBFormat,
             "Export collection to Berkeley DB format.")
        .def("get_wallet_count", &wallet_batch::BatchWalletGenerator::getWalletCount,
             "Get number of generated wallets.");
    // END_CLASS_BatchWalletGenerator_PYBIND

    // START_FUNCTION_create_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт фабричной функции create в Python.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(8): FactoryFunction]
    // END_CONTRACT
    m.def("create", &wallet_batch::BatchWalletPluginFactory::create,
          "Create new batch wallet generator instance.");
    // END_FUNCTION_create_PYBIND

    // START_FUNCTION_get_version_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт функции getVersion в Python.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(7): VersionInfo]
    // END_CONTRACT
    m.def("get_version", &wallet_batch::BatchWalletPluginFactory::getVersion,
          "Get plugin version.");
    // END_FUNCTION_get_version_PYBIND

    // Constants
    m.attr("DEFAULT_WALLET_COUNT") = wallet_batch::DEFAULT_WALLET_COUNT;
    m.attr("MAX_WALLET_COUNT") = wallet_batch::MAX_WALLET_COUNT;
}
