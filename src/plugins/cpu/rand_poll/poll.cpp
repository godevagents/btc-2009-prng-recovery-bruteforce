// FILE: src/plugins/cpu/rand_poll/poll.cpp
// VERSION: 2.2.1
// START_MODULE_CONTRACT:
// PURPOSE: Оптимизированная криминалистическая реконструкция RAND_poll() для Windows XP SP3.
// Восстановлена функция gen_le_range для совместимости с pybind11 wrapper.
// KEYWORDS: [DOMAIN(10): EntropyGeneration; DOMAIN(9): Forensics; TECH(8): Optimization]
// END_MODULE_CONTRACT

#ifndef RAND_POLL_CPP_H
#define RAND_POLL_CPP_H

#include <vector>
#include <string>
#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <ctime>
#include <algorithm>
#include <memory>
#include <sstream>

#include "rand_add.h"
#include "hkey_performance_data.h"
#include "rand_poll_fallback.hpp"

// ============================================================================
// OPTIMIZATION: Compile-time constants (constexpr)
// ============================================================================

// START_CONSTANT_ARRAY_PHASE1_RANGES
constexpr uint64_t PHASE1_WS_RANGES[][2] = {
    // First 13 entries are 8-byte fields
    {0x005D6949, 0x00B17649}, {0x00000DA5, 0x1D784000}, {0x000003E8, 0x00271000},
    {0x2F6BB000, 0x54074000}, {0x057A1200, 0x11EE3700}, {0x2F6BB000, 0x59696000},
    {0x02D03200, 0x08969800}, {0x01314200, 0x04AF0800}, {0x00000BB8, 0x00271000},
    {0x01314200, 0x04AF0800}, {0x01A51000, 0x05D43000}, {0x05BC2000, 0x17D68000},
    {0x00989600, 0x0221FA00},
    // Remaining 4-byte fields
    {0x0000000A, 0x0A000000}, {0x00000005, 0x05000000}, {0x00013840, 0x0003D0D0},
    {0x00007530, 0x000186A0}, {0x000001F4, 0x000007D0}, {0x00000064, 0x000001F4},
    {0x00014E90, 0x00011102}, {0x00002710, 0x00007530}, {0x00000032, 0x000000C8},
    {0x00000096, 0x00000320}, {0x00000020, 0x000000C8}, {0x00000000, 0x00000000},
    {0x00000000, 0x00000000}, {0x00000000, 0x00000000}, {0x00000001, 0x03000000},
    {0x00000000, 0x00000000}, {0x00000000, 0x05000000}, {0x00000000, 0x02000000},
    {0x00000000, 0x00000000}, {0x00000000, 0x00000000}, {0x00000001, 0x03000000},
    {0x00000000, 0x05000000}, {0x00000000, 0x00000000}, {0x00000000, 0x0A000000}
};

constexpr uint64_t PHASE1_SS_RANGES[][2] = {
    {0x80816649, 0x80B07049}, {0x0000000A, 0x64000000}, {0x00000000, 0x00000000},
    {0x00000000, 0x00050000}, {0x00000001, 0x05000000}, {0x00000000, 0x02000000},
    {0x00000000, 0x00000000}, {0x00000000, 0x05000000}, {0x00000000, 0x00000000},
    {0x00000000, 0x00000000}, {0x00064000, 0x00057CA0}, {0x00000000, 0x00000000},
    {0x00010000, 0x0000C000}, {0x00000000, 0x00000000}, {0x00000000, 0x0A000000},
    {0x00000000, 0x00000000}, {0x00000000, 0x00000000}
};
// END_CONSTANT_ARRAY_PHASE1_RANGES

// START_CONSTANT_ARRAY_PHASE3
constexpr uint64_t PHASE3_HWND_LIST[] = { 0x00000100, 0x24010000 };
constexpr uint64_t PHASE3_CURSOR_CONSTS[] = { 0x00000014, 0x00000001, 0x00010002, 0x00000280, 0x00000200 };
constexpr uint64_t PHASE3_QS_CONST = 0x0000006B;
// END_CONSTANT_ARRAY_PHASE3

// START_CONSTANT_ARRAY_PHASE4
constexpr uint64_t PHASE4_HEAPLIST_RANGES[][2] = {
    {0x00000010, 0x00000010}, {0x000005A0, 0x00001130}, {0x00090000, 0x00046000}, {0x00000000, 0x00000000}
};
constexpr uint64_t PHASE4_HEAPENTRY_RANGES[][2] = {
    {0x00000024, 0x00000024}, {0x00000020, 0x00000040}, {0x00000001, 0x00000002}
};
constexpr uint64_t PHASE4_PROCESSENTRY_RANGES[][2] = {
    {0x00000128, 0x00000128}, {0x000005A0, 0x00001130}, {0x00000003, 0x00000008}, 
    {0x00000220, 0x00000650}, {0x00000008, 0x00000008}
};
constexpr uint64_t PHASE4_THREADENTRY_RANGES[][2] = {
    {0x0000001C, 0x0000001C}, {0x00000004, 0x00001250}, {0x000005A0, 0x00001130}, {0x00000004, 0x0000000F}
};
constexpr uint64_t PHASE4_MODULEENTRY_RANGES[][2] = {
    {0x00000224, 0x00000224}, {0x00000001, 0x00000001}, {0x000005A0, 0x00001130},
    {0x0000FFFF, 0x0000FFFF}, {0x00400000, 0x00400000}, {0x00700000, 0x00700000}
};
// END_CONSTANT_ARRAY_PHASE4

// START_CONSTANT_ARRAY_PHASE5
constexpr uint64_t PHASE5_RDTSC_RANGE[][2] = { {0x00000000, 0xFFFFFFFF} };
constexpr uint64_t PHASE5_QPC_RANGE[][2] = { {0xC00135E4, 0x00001042A8} };
constexpr uint64_t PHASE5_MEMORYSTATUS_RANGES[][2] = {
    {0x00000020, 0x00000020}, {0x0000000F, 0x0000001E}, {0xCFD00000, 0xE0000000},
    {0xA6E49C00, 0xB8C63F00}, {0x2A05F200, 0xA13B8600}, {0x0C388D00, 0x836E2100}
};
constexpr uint64_t PHASE5_VIRT_LIST[] = { 0x7FFE0000, 0x7FFFFFFF };
constexpr uint64_t PHASE5_AVAILVIRT_LIST[] = { 0x7FFDF000, 0xF0FD7F00 };
constexpr uint64_t PHASE5_PID_RANGE[][2] = { {0x0000076C, 0x000009C4} };
// END_CONSTANT_ARRAY_PHASE5

// START_STRUCT_ProcessModel
struct ProcessModel {
    const char* name;
    uint32_t pid;
    uint32_t threads;
    uint32_t ppid;
};
// END_STRUCT_ProcessModel

static const ProcessModel ALL_PROCESSES[] = {
    {"System", 4, 80, 0}, {"smss.exe", 368, 3, 4}, {"csrss.exe", 476, 11, 368},
    {"winlogon.exe", 536, 21, 368}, {"services.exe", 652, 17, 536}, {"lsass.exe", 680, 21, 536},
    {"explorer.exe", 1456, 16, 1484}, {"svchost.exe", 856, 25, 652}, {"spoolsv.exe", 1024, 12, 652},
    {"alg.exe", 1108, 7, 652}, {"bitcoin.exe", 3180, 12, 1484}
    // Full list assumed
};
constexpr size_t ALL_PROCESSES_COUNT = sizeof(ALL_PROCESSES) / sizeof(ALL_PROCESSES[0]);

// Global RNG
static uint32_t g_seed = 0;

inline void set_random_seed(uint32_t seed) {
    g_seed = seed;
    std::srand(seed);
}

inline uint32_t random_uint32() { return std::rand(); }

inline uint32_t random_uint32_range(uint32_t min_val, uint32_t max_val) {
    if (min_val > max_val) std::swap(min_val, max_val);
    return min_val + (std::rand() % (max_val - min_val + 1));
}

// Helper for optimized internal logic
inline void append_le_uint32(std::vector<uint8_t>& buf, uint32_t val) {
    buf.push_back(val & 0xFF);
    buf.push_back((val >> 8) & 0xFF);
    buf.push_back((val >> 16) & 0xFF);
    buf.push_back((val >> 24) & 0xFF);
}

inline void append_le_uint64(std::vector<uint8_t>& buf, uint64_t val) {
    buf.push_back(val & 0xFF);
    buf.push_back((val >> 8) & 0xFF);
    buf.push_back((val >> 16) & 0xFF);
    buf.push_back((val >> 24) & 0xFF);
    buf.push_back((val >> 32) & 0xFF);
    buf.push_back((val >> 40) & 0xFF);
    buf.push_back((val >> 48) & 0xFF);
    buf.push_back((val >> 56) & 0xFF);
}

// START_FUNCTION_gen_le_range
// PURPOSE: Python binding compatibility wrapper. Parses hex strings.
static std::vector<uint8_t> gen_le_range(const std::string& start_hex,
                                          const std::string& end_hex = "",
                                          size_t size = 4) {
    uint64_t val = 0;
    bool is_const_list = false;
    std::vector<uint64_t> options;

    if (start_hex.find(',') != std::string::npos || end_hex.empty()) {
        is_const_list = true;
        std::stringstream ss(start_hex);
        std::string token;
        while (std::getline(ss, token, ',')) {
            token.erase(std::remove_if(token.begin(), token.end(), ::isspace), token.end());
            if (!token.empty()) {
                uint64_t opt_val = std::stoull(token, nullptr, 16);
                options.push_back(opt_val);
            }
        }
        if (!options.empty()) {
            size_t idx = random_uint32() % options.size();
            val = options[idx];
        }
    } else {
        std::string start_clean = start_hex;
        std::string end_clean = end_hex;
        start_clean.erase(std::remove_if(start_clean.begin(), start_clean.end(), ::isspace), start_clean.end());
        end_clean.erase(std::remove_if(end_clean.begin(), end_clean.end(), ::isspace), end_clean.end());

        uint64_t s = std::stoull(start_clean, nullptr, 16);
        uint64_t e = std::stoull(end_clean, nullptr, 16);
        if (s > e) std::swap(s, e);
        val = s + (random_uint32() % (e - s + 1));
    }

    std::vector<uint8_t> result(size, 0);
    for (size_t i = 0; i < size && i < 8; ++i) {
        result[i] = static_cast<uint8_t>((val >> (i * 8)) & 0xFF);
    }
    return result;
}
// END_FUNCTION_gen_le_range

// START_CLASS_RandPollReconstructorXP
class RandPollReconstructorXP {
public:
    RandPollReconstructorXP(uint32_t seed = 0) {
        if (seed != 0) {
            set_random_seed(seed);
            this->seed = seed;
        } else {
            this->seed = static_cast<uint32_t>(std::time(nullptr));
            set_random_seed(this->seed);
        }
        rand_add_impl = std::unique_ptr<RandAddImplementation>(new RandAddImplementation());
        
        int num_processes = random_uint32_range(40, 70);
        std::vector<int> indices;
        for (size_t i = 0; i < ALL_PROCESSES_COUNT - 1; ++i) indices.push_back(i);
        std::random_shuffle(indices.begin(), indices.end());
        for (int i = 0; i < num_processes && i < (int)indices.size(); ++i) {
            process_model.push_back(ALL_PROCESSES[indices[i]]);
        }
        process_model.push_back(ALL_PROCESSES[ALL_PROCESSES_COUNT - 1]);
    }

    void _rand_add(const std::vector<uint8_t>& data, double entropy, const char* tag) {
        if (rand_add_impl) rand_add_impl->rand_add(data.data(), data.size(), entropy);
    }

    // Optimized Phase 1
    void _phase_1_netapi_stats() {
        std::vector<uint8_t> ws;
        ws.reserve(200);
        
        int idx = 0;
        for (const auto& range : PHASE1_WS_RANGES) {
            bool is_8byte = (idx < 13);
            uint64_t min_val = range[0];
            uint64_t max_val = range[1];
            if (min_val > max_val) std::swap(min_val, max_val);
            uint64_t val = min_val + (std::rand() % (max_val - min_val + 1));
            
            if (is_8byte) append_le_uint64(ws, val);
            else append_le_uint32(ws, static_cast<uint32_t>(val));
            idx++;
        }
        _rand_add(ws, 45.0, "LanmanWorkstation");

        std::vector<uint8_t> ss;
        ss.reserve(100);
        for (const auto& range : PHASE1_SS_RANGES) {
            uint64_t min_val = range[0];
            uint64_t max_val = range[1];
            if (min_val > max_val) std::swap(min_val, max_val);
            uint64_t val = min_val + (std::rand() % (max_val - min_val + 1));
            append_le_uint32(ss, static_cast<uint32_t>(val));
        }
        _rand_add(ss, 17.0, "LanmanServer");

        std::vector<uint8_t> hprov;
        append_le_uint32(hprov, random_uint32_range(0x00001000, 0x00009000));
        _rand_add(hprov, 0.0, "HCRYPTPROV");
    }

    void _phase_2_cryptoapi_rng() {
        std::vector<uint8_t> buf(64);
        for (size_t i = 0; i < 64; ++i) buf[i] = static_cast<uint8_t>(random_uint32() % 256);
        _rand_add(buf, 0.0, "CryptGenRandom");
    }

    void _phase_3_user32_ui() {
        std::vector<uint8_t> hwnd;
        append_le_uint32(hwnd, PHASE3_HWND_LIST[std::rand() % 2]);
        _rand_add(hwnd, 0.0, "GetForegroundWindow");

        std::vector<uint8_t> ci;
        ci.reserve(30);
        for(size_t i=0; i<5; ++i) append_le_uint32(ci, PHASE3_CURSOR_CONSTS[i]);
        _rand_add(ci, 2.0, "CURSORINFO");

        std::vector<uint8_t> qs;
        append_le_uint32(qs, PHASE3_QS_CONST);
        _rand_add(qs, 1.0, "GetQueueStatus");
    }

    void _phase_4_toolhelp32_snapshot() {
        for (const auto& proc : process_model) {
            std::vector<uint8_t> hl;
            hl.reserve(16);
            for (const auto& r : PHASE4_HEAPLIST_RANGES) {
                append_le_uint32(hl, random_uint32_range((uint32_t)r[0], (uint32_t)r[1]));
            }
            uint32_t heap_id = *reinterpret_cast<const uint32_t*>(&hl[8]);
            _rand_add(hl, 3.0, "HEAPLIST32");

            uint32_t entry_count = random_uint32_range(15, 80);
            for (uint32_t i = 0; i < entry_count; ++i) {
                std::vector<uint8_t> he;
                he.reserve(40);
                append_le_uint32(he, 0x24);
                append_le_uint32(he, heap_id);
                append_le_uint32(he, random_uint32_range(0x500, 0x10000));
                append_le_uint32(he, random_uint32_range(0x20, 0x40));
                append_le_uint32(he, (std::rand() % 2 == 0) ? 0x01 : 0x02);
                _rand_add(he, 5.0, "HEAPENTRY32");
            }
        }

        for (const auto& proc : process_model) {
            std::vector<uint8_t> pe;
            pe.reserve(300);
            append_le_uint32(pe, 0x128);
            append_le_uint32(pe, 0);
            append_le_uint32(pe, proc.pid); // use actual PID from model
            append_le_uint32(pe, 0);
            append_le_uint32(pe, 0);
            append_le_uint32(pe, proc.threads);
            append_le_uint32(pe, proc.ppid);
            append_le_uint32(pe, 0x08);
            append_le_uint32(pe, 0);
            
            std::vector<uint8_t> exe_name(260, 0);
            for(size_t j=0; proc.name[j] != '\0' && j < 260; ++j) exe_name[j] = proc.name[j];
            pe.insert(pe.end(), exe_name.begin(), exe_name.end());
            _rand_add(pe, 9.0, "PROCESSENTRY32");
        }

        for (const auto& proc : process_model) {
            for (uint32_t t = 0; t < proc.threads; ++t) {
                std::vector<uint8_t> te;
                te.reserve(28);
                append_le_uint32(te, 0x1C);
                append_le_uint32(te, 0);
                append_le_uint32(te, random_uint32_range(4, 0x1250));
                append_le_uint32(te, proc.pid);
                append_le_uint32(te, random_uint32_range(4, 0x0F));
                append_le_uint32(te, 0);
                append_le_uint32(te, 0);
                _rand_add(te, 6.0, "THREADENTRY32");
            }
        }

        std::vector<uint8_t> me;
        me.reserve(560);
        append_le_uint32(me, 0x224);
        append_le_uint32(me, 0x01);
        append_le_uint32(me, random_uint32_range(0x5A0, 0x1130));
        append_le_uint32(me, 0xFFFF);
        append_le_uint32(me, 0xFFFF);
        append_le_uint32(me, 0x00400000);
        append_le_uint32(me, 0x00700000);
        append_le_uint32(me, 0x00400000);
        
        std::vector<uint8_t> mod_name(256, 0);
        me.insert(me.end(), mod_name.begin(), mod_name.end());
        std::vector<uint8_t> mod_path(260, 0);
        me.insert(me.end(), mod_path.begin(), mod_path.end());
        _rand_add(me, 9.0, "MODULEENTRY32");
    }

    void _phase_5_kernel32_sys() {
        std::vector<uint8_t> rdtsc;
        append_le_uint32(rdtsc, random_uint32());
        _rand_add(rdtsc, 1.0, "RDTSC");

        std::vector<uint8_t> qpc;
        uint64_t qpc_val = PHASE5_QPC_RANGE[0][0] + (std::rand() % (PHASE5_QPC_RANGE[0][1] - PHASE5_QPC_RANGE[0][0] + 1));
        append_le_uint64(qpc, qpc_val);
        _rand_add(qpc, 0.0, "QPC");

        std::vector<uint8_t> ms;
        ms.reserve(32);
        for (const auto& r : PHASE5_MEMORYSTATUS_RANGES) {
            append_le_uint32(ms, random_uint32_range((uint32_t)r[0], (uint32_t)r[1]));
        }
        append_le_uint32(ms, PHASE5_VIRT_LIST[std::rand() % 2]);
        append_le_uint32(ms, PHASE5_AVAILVIRT_LIST[std::rand() % 2]);
        _rand_add(ms, 1.0, "MEMORYSTATUS");

        std::vector<uint8_t> pid;
        append_le_uint32(pid, random_uint32_range(PHASE5_PID_RANGE[0][0], PHASE5_PID_RANGE[0][1]));
        _rand_add(pid, 1.0, "PID");
    }

    std::vector<uint8_t> execute_poll() {
        _phase_1_netapi_stats();
        _phase_2_cryptoapi_rng();
        _phase_3_user32_ui();
        _phase_4_toolhelp32_snapshot();
        _phase_5_kernel32_sys();

        generate_hkey_performance_data(0, rand_add_impl.get());
        if (rand_add_impl) return rand_add_impl->get_state();
        return {};
    }

private:
    std::unique_ptr<RandAddImplementation> rand_add_impl;
    std::vector<ProcessModel> process_model;
    uint32_t seed;
};
// END_CLASS_RandPollReconstructorXP

#endif // RAND_POLL_CPP_H
