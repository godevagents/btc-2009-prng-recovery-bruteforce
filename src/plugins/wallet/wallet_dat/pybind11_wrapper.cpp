/**
 * FILE: src/plugins/wallet/wallet_dat/pybind11_wrapper.cpp
 * VERSION: 1.0.0
 * PURPOSE: Python bindings for wallet.dat creation module.
 * LANGUAGE: C++11 with pybind11
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "wallet_dat.h"
#include "../batch_gen/batch_gen.h"

namespace py = pybind11;

// START_MODULE_CONTRACT:
// PURPOSE: Python-обертка для C++ реализации записи wallet.dat.
// SCOPE: Экспорт класса WalletDatWriter и его методов в Python.
// KEYWORDS: [TECH(9): pybind11; DOMAIN(8): PythonBindings; DOMAIN(7): BerkeleyDB]
// END_MODULE_CONTRACT

PYBIND11_MODULE(wallet_dat_cpp, m) {
    m.doc() = "C++ implementation of wallet.dat creation (Berkeley DB format)";
    
    // Сначала регистрируем базовый класс (интерфейс)
    // START_CLASS_WalletDatWriterInterface_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт интерфейса WalletDatWriterInterface в Python.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(8): InterfaceBinding]
    // END_CONTRACT
    py::class_<wallet_dat::WalletDatWriterInterface>(m, "WalletDatWriterInterface")
        .def("initialize", &wallet_dat::WalletDatWriterInterface::initialize)
        .def("create_database", &wallet_dat::WalletDatWriterInterface::createDatabase)
        .def("write_version", &wallet_dat::WalletDatWriterInterface::writeVersion)
        .def("write_default_key", &wallet_dat::WalletDatWriterInterface::writeDefaultKey)
        .def("write_key_pair", &wallet_dat::WalletDatWriterInterface::writeKeyPair)
        .def("write_address_book", &wallet_dat::WalletDatWriterInterface::writeAddressBook)
        .def("write_setting", &wallet_dat::WalletDatWriterInterface::writeSetting)
        .def("write_tx", &wallet_dat::WalletDatWriterInterface::writeTx)
        .def("write_wallet_collection", &wallet_dat::WalletDatWriterInterface::writeWalletCollection)
        .def("close", &wallet_dat::WalletDatWriterInterface::close)
        .def("read_wallet_dat", &wallet_dat::WalletDatWriterInterface::readWalletDat)
        .def("get_file_path", &wallet_dat::WalletDatWriterInterface::getFilePath)
        .def("set_master_key", &wallet_dat::WalletDatWriterInterface::setMasterKey)
        .def("encrypt_wallet", &wallet_dat::WalletDatWriterInterface::encryptWallet)
        .def("is_encrypted", &wallet_dat::WalletDatWriterInterface::isEncrypted)
        .def("verify_password", &wallet_dat::WalletDatWriterInterface::verifyPassword);
    // END_CLASS_WalletDatWriterInterface_PYBIND
    
    // Потом наследуемый класс
    // START_CLASS_WalletDatWriter_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт класса WalletDatWriter в Python.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(8): ClassBinding; DOMAIN(7): WalletDat]
    // END_CONTRACT
    py::class_<wallet_dat::WalletDatWriter, 
               wallet_dat::WalletDatWriterInterface>(m, "WalletDatWriter")
        .def(py::init<>(),
             "Initialize wallet.dat writer.")
        .def("initialize", &wallet_dat::WalletDatWriter::initialize,
             py::arg("db_path"),
             "Initialize with database path.")
        .def("create_database", &wallet_dat::WalletDatWriter::createDatabase,
             py::arg("filename") = "wallet.dat",
             "Create/open database file.")
        .def("write_version", &wallet_dat::WalletDatWriter::writeVersion,
             py::arg("version") = 10500,
             "Write database version.")
        .def("write_default_key", &wallet_dat::WalletDatWriter::writeDefaultKey,
             py::arg("pubkey"),
             "Write default public key.")
        .def("write_key_pair", &wallet_dat::WalletDatWriter::writeKeyPair,
             py::arg("pubkey"),
             py::arg("privkey"),
             "Write key pair (public + private). If encrypted, writes ckey.")
        .def("write_address_book", &wallet_dat::WalletDatWriter::writeAddressBook,
             py::arg("address"),
             py::arg("name"),
             "Write address book entry.")
        .def("write_setting", &wallet_dat::WalletDatWriter::writeSetting,
             py::arg("key"),
             py::arg("value"),
             "Write setting entry.")
        .def("write_tx", &wallet_dat::WalletDatWriter::writeTx,
             py::arg("tx_hash"),
             py::arg("tx_data"),
             "Write transaction entry.")
        .def("write_wallet_collection", &wallet_dat::WalletDatWriter::writeWalletCollection,
             py::arg("collection"),
             "Write complete wallet collection.")
        .def("close", &wallet_dat::WalletDatWriter::close,
             "Close database and free resources.")
        .def("read_wallet_dat", &wallet_dat::WalletDatWriter::readWalletDat,
             py::arg("filepath"),
             "Read wallet.dat file.")
        .def("get_file_path", &wallet_dat::WalletDatWriter::getFilePath,
             "Get current file path.")
        .def("set_master_key", &wallet_dat::WalletDatWriter::setMasterKey,
             py::arg("password"),
             "Set master key from password.")
        .def("encrypt_wallet", &wallet_dat::WalletDatWriter::encryptWallet,
             py::arg("password"),
             "Enable wallet encryption with password. Writes mkey record.")
        .def("is_encrypted", &wallet_dat::WalletDatWriter::isEncrypted,
             "Check if wallet is encrypted.")
        .def("verify_password", &wallet_dat::WalletDatWriter::verifyPassword,
             py::arg("password"),
             "Verify password against stored checksum.");
    // END_CLASS_WalletDatWriter_PYBIND

    // START_FUNCTION_create_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт фабричной функции create в Python.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(8): FactoryFunction]
    // END_CONTRACT
    m.def("create", &wallet_dat::WalletDatPluginFactory::create,
          "Create new wallet.dat writer instance.");
    // END_FUNCTION_create_PYBIND

    // START_FUNCTION_get_version_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт функции getVersion в Python.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(7): VersionInfo]
    // END_CONTRACT
    m.def("get_version", &wallet_dat::WalletDatPluginFactory::getVersion,
          "Get plugin version.");
    // END_FUNCTION_get_version_PYBIND

    // Constants
    m.attr("WALLET_VERSION") = wallet_dat::WALLET_VERSION;
    m.attr("WALLET_FILENAME") = wallet_dat::WALLET_FILENAME;
    m.attr("WALLET_DB_NAME") = wallet_dat::WALLET_DB_NAME;
}
