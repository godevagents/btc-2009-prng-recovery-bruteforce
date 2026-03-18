/**
 * FILE: src/plugins/cpu/rand_poll/pybind11_wrapper.cpp
 * VERSION: 1.0.0
 * PURPOSE: Python bindings for poll module (C++ implementation of RAND_poll).
 * LANGUAGE: C++11 with pybind11
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "poll.cpp"

namespace py = pybind11;

// START_MODULE_CONTRACT:
// PURPOSE: Python-обертка для C++ реализации RAND_poll.
// SCOPE: Экспорт класса RandPollReconstructorXP и его методов в Python.
// KEYWORDS: [TECH(9): pybind11; DOMAIN(8): PythonBindings]
// END_MODULE_CONTRACT

PYBIND11_MODULE(rand_poll_cpp, m) {
    m.doc() = "C++ implementation of RAND_poll entropy collection for Windows XP SP3";

    // START_CLASS_RandPollReconstructorXP_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт класса RandPollReconstructorXP в Python.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(8): ClassBinding]
    // END_CONTRACT
    py::class_<RandPollReconstructorXP>(m, "RandPollReconstructorXP")
        .def(py::init<uint32_t>(), py::arg("seed") = 0,
             "Initialize RAND_poll reconstructor with optional seed for deterministic generation.")
        .def("execute_poll", &RandPollReconstructorXP::execute_poll,
             "Execute full RAND_poll entropy collection sequence (5 phases).")
        .def("_rand_add", &RandPollReconstructorXP::_rand_add,
             py::arg("data"), py::arg("entropy_estimate"), py::arg("source_tag"),
             "Simulate RAND_add call (internal method).")
        .def("_phase_1_netapi_stats", &RandPollReconstructorXP::_phase_1_netapi_stats,
             "Phase 1: Emulate NetAPI statistics collection.")
        .def("_phase_2_cryptoapi_rng", &RandPollReconstructorXP::_phase_2_cryptoapi_rng,
             "Phase 2: Emulate CryptGenRandom.")
        .def("_phase_3_user32_ui", &RandPollReconstructorXP::_phase_3_user32_ui,
             "Phase 3: Emulate User32 UI data collection.")
        .def("_phase_4_toolhelp32_snapshot", &RandPollReconstructorXP::_phase_4_toolhelp32_snapshot,
             "Phase 4: Emulate Toolhelp32Snapshot.")
        .def("_phase_5_kernel32_sys", &RandPollReconstructorXP::_phase_5_kernel32_sys,
             "Phase 5: Emulate Kernel32 system data collection.");
    // END_CLASS_RandPollReconstructorXP_PYBIND

    // START_FUNCTION_gen_le_range_PYBIND
    // START_CONTRACT:
    // PURPOSE: Экспорт функции gen_le_range в Python.
    // KEYWORDS: [TECH(9): pybind11; CONCEPT(8): FunctionBinding]
    // END_CONTRACT
    m.def("gen_le_range", &gen_le_range,
          py::arg("start_hex"), py::arg("end_hex") = "", py::arg("size") = 4,
          "Generate Little-Endian byte sequence from hex ranges.");
    // END_FUNCTION_gen_le_range_PYBIND
}
