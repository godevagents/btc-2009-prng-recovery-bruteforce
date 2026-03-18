// FILE: src/core/pybind11_wrapper.cpp
// VERSION: 1.1.0
// START_MODULE_CONTRACT:
// PURPOSE: Python bindings для core C++ модулей (rand_add, orchestrator).
// SCOPE: Экспорт классов RandAddImplementation и EntropyXPOrchestrator в Python.
// INPUT: Вызовы из Python кода для создания экземпляров и вызова методов.
// OUTPUT: Возврат состояния PRNG или выполнение полного цикла энтропии.
// KEYWORDS: [TECH(10): Pybind11; CONCEPT(8): Python_Binding; DOMAIN(9): PRNG]
// LINKS: [USES_API(10): pybind11; WRAPS(9): rand_add.h; WRAPS(9): orchestrator.h]
// END_MODULE_CONTRACT
// START_MODULE_MAP:
// CLASS 10 [Экспортирует класс RandAddImplementation] => RandAddImplementation
// CLASS 9 [Экспортирует класс EntropyXPOrchestrator] => EntropyXPOrchestrator
// END_MODULE_MAP
// START_USE_CASES:
// - [RandAddImplementation]: BitcoinCore (Startup) -> CreatePRNGInstance -> PRNGReady
// - [EntropyXPOrchestrator]: BitcoinCore (Startup) -> RunFullEntropyCycle -> PRNGStateFinalized
// END_USE_CASES

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <iostream>
#include "rand_add.h"
#include "orchestrator.h"

namespace py = pybind11;

// START_MODULE_CORE_PYBIND11
// START_CONTRACT:
// PURPOSE: Создание Python модуля для core C++ классов.
// KEYWORDS: [TECH(10): Pybind11; CONCEPT(8): Python_Binding]
// END_CONTRACT

PYBIND11_MODULE(core_cpp, m) {
    m.doc() = "Core C++ modules for ENTROPY project: RandAddImplementation and EntropyXPOrchestrator";

    // START_CLASS_RandAddImplementation_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт класса RandAddImplementation в Python.
    // KEYWORDS: [TECH(10): pybind11; CONCEPT(9): ClassBinding; DOMAIN(10): PRNG]
    // END_CONTRACT
    py::class_<RandAddImplementation>(m, "RandAddImplementation")
        .def(py::init<>(),
             "Initialize RAND_add implementation with default state (1043 bytes buffer).")
        .def("rand_add", &RandAddImplementation::rand_add,
             py::arg("buf"), py::arg("num"), py::arg("add_entropy"),
             "Forensic replica of ssleay_rand_add() from OpenSSL 0.9.8h.\n"
             "Args:\n"
             "    buf: Buffer containing entropy data (bytes)\n"
             "    num: Size of buffer in bytes\n"
             "    add_entropy: Estimated entropy in bits")
        .def("process_entropy", &RandAddImplementation::process_entropy,
             py::arg("data"), py::arg("entropy_estimate") = 0.0,
             "Convenience method to process entropy stream.\n"
             "Args:\n"
             "    data: Vector of bytes containing entropy\n"
             "    entropy_estimate: Estimated entropy in bits (default: 0.0)")
        .def("get_state", &RandAddImplementation::get_state,
             "Get current PRNG state (1043 bytes).\n"
             "Returns:\n"
             "    bytes: Copy of state buffer")
        .def("get_state_hex", &RandAddImplementation::get_state_hex,
             "Get current PRNG state as hex string.\n"
             "Returns:\n"
             "    str: Hex representation of state");
    // END_CLASS_RandAddImplementation_PYBIND

    // START_CLASS_EntropyXPOrchestrator_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт класса EntropyXPOrchestrator в Python.
    // KEYWORDS: [TECH(10): pybind11; CONCEPT(9): ClassBinding; DOMAIN(9): Orchestration]
    // END_CONTRACT
    py::class_<EntropyXPOrchestrator>(m, "EntropyXPOrchestrator")
        .def(py::init<>(),
             "Initialize entropy orchestrator for Windows XP SP3 reconstruction.")
        .def("run", &EntropyXPOrchestrator::run,
             py::arg("seed") = 0,
             "Run full entropy collection cycle: poll -> bitmap -> hkey -> RAND_add.\n"
             "Args:\n"
             "    seed: Optional seed for deterministic generation (default: 0)\n"
             "Returns:\n"
             "    bytes: Final PRNG state (1043 bytes)")
        .def("run_poll_only", &EntropyXPOrchestrator::run_poll_only,
             py::arg("seed") = 0,
             "Run only RAND_poll phase.\n"
             "Args:\n"
             "    seed: Optional seed for deterministic generation (default: 0)\n"
             "Returns:\n"
             "    bytes: Entropy stream from poll phase")
        .def("run_bitmap_only", &EntropyXPOrchestrator::run_bitmap_only,
             "Run only GetBitmap phase.\n"
             "Returns:\n"
             "    bytes: Final PRNG state after bitmap phase");
    // END_CLASS_EntropyXPOrchestrator_PYBIND
}
// END_MODULE_CORE_PYBIND11
