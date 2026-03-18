/**
 * FILE: src/plugins/crypto/ecdsa_keys/pybind11_wrapper.cpp
 * VERSION: 1.0.1
 * PURPOSE: Python bindings for ECDSA secp256k1 key generation module.
 * LANGUAGE: C++11 with pybind11
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "ecdsa_keys.h"

namespace py = pybind11;

// START_MODULE_CONTRACT:
// PURPOSE: Python-обертка для C++ реализации генерации ECDSA ключей secp256k1.
// SCOPE: Экспорт класса Secp256k1KeyGenerator и его методов в Python.
// KEYWORDS: [TECH(9): pybind11; DOMAIN(8): PythonBindings; DOMAIN(7): ECDSA]
// END_MODULE_CONTRACT

PYBIND11_MODULE(ecdsa_keys_cpp, m) {
    m.doc() = "C++ implementation of ECDSA secp256k1 key generation for Bitcoin wallets";
    
    // START_CLASS_ECDSAPluginInterface_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт интерфейса ECDSAPluginInterface в Python (базовый класс).
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(8): InterfaceBinding]
    // END_CONTRACT
    py::class_<wallet::crypto::ECDSAPluginInterface>(m, "ECDSAPluginInterface")
        .def("generate_key", &wallet::crypto::ECDSAPluginInterface::generateKey)
        .def("get_private_key", &wallet::crypto::ECDSAPluginInterface::getPrivateKey)
        .def("get_public_key", &wallet::crypto::ECDSAPluginInterface::getPublicKey)
        .def("set_private_key", &wallet::crypto::ECDSAPluginInterface::setPrivateKey)
        .def("set_public_key", &wallet::crypto::ECDSAPluginInterface::setPublicKey)
        .def("add_entropy", [](wallet::crypto::ECDSAPluginInterface& self, const std::vector<unsigned char>& data) {
            if (!data.empty()) {
                self.addEntropy(data.data(), data.size());
            }
        }, py::arg("data"))
        .def("get_address", &wallet::crypto::ECDSAPluginInterface::getAddress)
        .def("is_valid", &wallet::crypto::ECDSAPluginInterface::isValid)
        .def("get_entropy_pool_size", &wallet::crypto::ECDSAPluginInterface::getEntropyPoolSize);
    // END_CLASS_ECDSAPluginInterface_PYBIND

    // START_CLASS_Secp256k1KeyGenerator_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт класса Secp256k1KeyGenerator в Python.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(8): ClassBinding; DOMAIN(7): ECDSA]
    // END_CONTRACT
    py::class_<wallet::crypto::Secp256k1KeyGenerator, 
               wallet::crypto::ECDSAPluginInterface>(m, "Secp256k1KeyGenerator")
        .def(py::init<>(),
             "Initialize ECDSA key generator for secp256k1 curve.")
        .def("generate_key", &wallet::crypto::Secp256k1KeyGenerator::generateKey,
             "Generate new ECDSA key pair (private + public).")
        .def("get_private_key", &wallet::crypto::Secp256k1KeyGenerator::getPrivateKey,
             "Get private key in DER format (279 bytes).")
        .def("get_public_key", &wallet::crypto::Secp256k1KeyGenerator::getPublicKey,
             "Get public key in uncompressed format (65 bytes).")
        .def("set_private_key", &wallet::crypto::Secp256k1KeyGenerator::setPrivateKey,
             py::arg("private_key"),
             "Set private key from DER format.")
        .def("set_public_key", &wallet::crypto::Secp256k1KeyGenerator::setPublicKey,
             py::arg("public_key"),
             "Set public key (65 bytes).")
        .def("add_entropy", [](wallet::crypto::Secp256k1KeyGenerator& self, const std::vector<unsigned char>& data) {
            if (!data.empty()) {
                self.addEntropy(data.data(), data.size());
            }
        },
             py::arg("data"),
             "Add entropy to OpenSSL RNG.")
        .def("get_address", &wallet::crypto::Secp256k1KeyGenerator::getAddress,
             "Get Bitcoin address from public key (Base58Check).")
        .def("is_valid", &wallet::crypto::Secp256k1KeyGenerator::isValid,
             "Check if current key is valid.")
        .def("get_entropy_pool_size", &wallet::crypto::Secp256k1KeyGenerator::getEntropyPoolSize,
             "Get entropy pool size (1043 bytes for OpenSSL RAND_poll).");
    // END_CLASS_Secp256k1KeyGenerator_PYBIND

    // START_FUNCTION_create_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт фабричной функции create в Python.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(8): FactoryFunction]
    // END_CONTRACT
    m.def("create", &wallet::crypto::ECDSAKeyPluginFactory::create,
          "Create new ECDSA key generator instance.");
    // END_FUNCTION_create_PYBIND

    // START_FUNCTION_get_version_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт функции getVersion в Python.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(7): VersionInfo]
    // END_CONTRACT
    m.def("get_version", &wallet::crypto::ECDSAKeyPluginFactory::getVersion,
          "Get plugin version.");
    // END_FUNCTION_get_version_PYBIND

    // Constants
    m.attr("PRIVATE_KEY_SIZE") = wallet::crypto::PRIVATE_KEY_SIZE;
    m.attr("PUBLIC_KEY_SIZE") = wallet::crypto::PUBLIC_KEY_SIZE;
    m.attr("SIGNATURE_SIZE") = wallet::crypto::SIGNATURE_SIZE;
    m.attr("NID_secp256k1") = wallet::crypto::SECP256K1_NID;
}
