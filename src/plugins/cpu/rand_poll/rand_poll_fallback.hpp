// FILE: src/plugins/cpu/rand_poll/rand_poll_fallback.hpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Standalone fallback эмуляция RAND_poll() для Windows XP SP3.
// Не требует OpenSSL/RandAddImplementation, возвращает сырые байтовые данные.
// Используется когда основной модуль недоступен.
// SCOPE: Эмуляция 5 фаз сбора энтропии: NetAPI, CryptoAPI, User32, Toolhelp32, Kernel32.
// KEYWORDS: [DOMAIN(10): Forensics; DOMAIN(9): EntropyEmulation; TECH(8): Windows_API; CONCEPT(9): Standalone]
// LINKS: [SIMULATES(10): rand_win.c; USES(8): rand_poll_constants.txt]
// END_MODULE_CONTRACT

// START_MODULE_MAP:
// CLASS 8 [Fallback эмулятор RAND_poll] => RandPollFallback
// FUNC 9 [Генерирует полную энтропию (5 фаз)] => generate_full_entropy
// FUNC 8 [Фаза 1: NetAPI статистика] => phase_1_netapi
// FUNC 8 [Фаза 2: CryptoAPI RNG] => phase_2_cryptoapi
// FUNC 8 [Фаза 3: User32 UI данные] => phase_3_user32
// FUNC 9 [Фаза 4: Toolhelp32 Snapshot] => phase_4_toolhelp32
// FUNC 8 [Фаза 5: Kernel32 системные данные] => phase_5_kernel32
// FUNC 7 [Конвертер диапазонов] => gen_le_range
// CONST 9 [Частота PERF counter] => PERF_FREQ
// END_MODULE_MAP

#ifndef RAND_POLL_FALLBACK_HPP
#define RAND_POLL_FALLBACK_HPP

#include <vector>
#include <string>
#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <ctime>
#include <sstream>
#include <algorithm>
#include <iostream>
#include <fstream>
#include <iomanip>
#include <memory>

// START_CONSTANTS
// START_CONTRACT:
// PURPOSE: Константы для криминалистической эмуляции.
// KEYWORDS: [CONCEPT(7): Constants; DOMAIN(8): PerformanceCounters]
// END_CONTRACT

// Частота HP T5122 Performance Counter (HPET)
constexpr uint32_t PERF_FREQ = 3579545;

// Диапазоны из rand_poll_constants.txt
constexpr uint64_t QPC_MIN_VALUE = 0x00000000C00135E4ULL;
constexpr uint64_t QPC_MAX_VALUE = 0x00000009100042A8ULL;

// END_CONSTANTS

// START_STRUCTS_WINDOWS_API
// START_CONTRACT:
// PURPOSE: Windows API структуры для Toolhelp32.
// KEYWORDS: [DOMAIN(9): WindowsAPI; TECH(8): StructDefinition]
// END_CONTRACT

// START_STRUCT_HEAPLIST32
// START_CONTRACT:
// PURPOSE: Структура HEAPLIST32 для Toolhelp32Snapshot.
// ATTRIBUTES:
// - [Размер структуры] => dwSize: [uint32_t]
// - [ID процесса] => th32ProcessID: [uint32_t]
// - [ID кучи] => th32HeapID: [uint32_t]
// - [Флаги] => dwFlags: [uint32_t]
// KEYWORDS: [DOMAIN(8): HeapTracking; TECH(7): Kernel32]
// END_CONTRACT
struct HEAPLIST32 {
    uint32_t dwSize;
    uint32_t th32ProcessID;
    uint32_t th32HeapID;
    uint32_t dwFlags;
};
// END_STRUCT_HEAPLIST32

// START_STRUCT_HEAPENTRY32
// START_CONTRACT:
// PURPOSE: Структура HEAPENTRY32 для перечисления блоков кучи.
// ATTRIBUTES:
// - [Размер структуры] => dwSize: [uint32_t]
// - [Дескриптор кучи] => hHandle: [uint32_t]
// - [Адрес блока] => dwAddress: [uint32_t]
// - [Размер блока] => dwBlockSize: [uint32_t]
// - [Флаги] => dwFlags: [uint32_t]
// - [Счетчик блокировок] => dwLockCount: [uint32_t]
// - [Зарезервировано] => dwResvd: [uint32_t]
// - [ID процесса] => th32ProcessID: [uint32_t]
// - [ID кучи] => th32HeapID: [uint32_t]
// KEYWORDS: [DOMAIN(8): HeapTracking; TECH(7): Kernel32]
// END_CONTRACT
struct HEAPENTRY32 {
    uint32_t dwSize;
    uint32_t hHandle;
    uint32_t dwAddress;
    uint32_t dwBlockSize;
    uint32_t dwFlags;
    uint32_t dwLockCount;
    uint32_t dwResvd;
    uint32_t th32ProcessID;
    uint32_t th32HeapID;
};
// END_STRUCT_HEAPENTRY32

// START_STRUCT_PROCESSENTRY32
// START_CONTRACT:
// PURPOSE: Структура PROCESSENTRY32 для перечисления процессов.
// ATTRIBUTES:
// - [Размер структуры] => dwSize: [uint32_t]
// - [Счетчик использования] => cntUsage: [uint32_t]
// - [ID процесса] => th32ProcessID: [uint32_t]
// - [ID кучи по умолчанию] => th32DefaultHeapID: [uint32_t]
// - [ID модуля] => th32ModuleID: [uint32_t]
// - [Количество потоков] => cntThreads: [uint32_t]
// - [ID родительского процесса] => th32ParentProcessID: [uint32_t]
// - [База приоритета класса] => pcPriClassBase: [int32_t]
// - [Флаги] => dwFlags: [uint32_t]
// - [Имя исполняемого файла] => szExeFile: [char[260]]
// KEYWORDS: [DOMAIN(9): ProcessManagement; TECH(8): Kernel32]
// END_CONTRACT
struct PROCESSENTRY32 {
    uint32_t dwSize;
    uint32_t cntUsage;
    uint32_t th32ProcessID;
    uint32_t th32DefaultHeapID;
    uint32_t th32ModuleID;
    uint32_t cntThreads;
    uint32_t th32ParentProcessID;
    int32_t pcPriClassBase;
    uint32_t dwFlags;
    char szExeFile[260];
};
// END_STRUCT_PROCESSENTRY32

// START_STRUCT_THREADENTRY32
// START_CONTRACT:
// PURPOSE: Структура THREADENTRY32 для перечисления потоков.
// ATTRIBUTES:
// - [Размер структуры] => dwSize: [uint32_t]
// - [Счетчик использования] => cntUsage: [uint32_t]
// - [ID потока] => th32ThreadID: [uint32_t]
// - [ID процесса-владельца] => th32OwnerProcessID: [uint32_t]
// - [Базовый приоритет] => tpBasePri: [int32_t]
// - [Дельта приоритета] => tpDeltaPri: [int32_t]
// - [Флаги] => dwFlags: [uint32_t]
// KEYWORDS: [DOMAIN(9): ThreadManagement; TECH(8): Kernel32]
// END_CONTRACT
struct THREADENTRY32 {
    uint32_t dwSize;
    uint32_t cntUsage;
    uint32_t th32ThreadID;
    uint32_t th32OwnerProcessID;
    int32_t tpBasePri;
    int32_t tpDeltaPri;
    uint32_t dwFlags;
};
// END_STRUCT_THREADENTRY32

// START_STRUCT_MODULEENTRY32
// START_CONTRACT:
// PURPOSE: Структура MODULEENTRY32 для перечисления модулей.
// ATTRIBUTES:
// - [Размер структуры] => dwSize: [uint32_t]
// - [ID модуля] => th32ModuleID: [uint32_t]
// - [ID процесса] => th32ProcessID: [uint32_t]
// - [Глобальный счетчик использования] => GlblcntUsage: [uint32_t]
// - [Счетчик использования процесса] => ProccntUsage: [uint32_t]
// - [Базовый адрес] => modBaseAddr: [uint8_t*]
// - [Размер модуля] => modBaseSize: [uint32_t]
// - [Дескриптор модуля] => hModule: [void*]
// - [Имя модуля] => szModule: [char[256]]
// - [Путь к модулю] => szExePath: [char[260]]
// KEYWORDS: [DOMAIN(8): ModuleManagement; TECH(8): Kernel32]
// END_CONTRACT
struct MODULEENTRY32 {
    uint32_t dwSize;
    uint32_t th32ModuleID;
    uint32_t th32ProcessID;
    uint32_t GlblcntUsage;
    uint32_t ProccntUsage;
    uint8_t* modBaseAddr;
    uint32_t modBaseSize;
    void* hModule;
    char szModule[256];
    char szExePath[260];
};
// END_STRUCT_MODULEENTRY32

// START_STRUCT_CURSORINFO
// START_CONTRACT:
// PURPOSE: Структура CURSORINFO для GetCursorInfo.
// ATTRIBUTES:
// - [Размер структуры] => cbSize: [uint32_t]
// - [Флаги] => flags: [uint32_t]
// - [Дескриптор курсора] => hCursor: [uint32_t]
// - [Координата X] => pt.x: [int32_t]
// - [Координата Y] => pt.y: [int32_t]
// KEYWORDS: [DOMAIN(7): UI_State; TECH(6): User32]
// END_CONTRACT
struct CURSORINFO {
    uint32_t cbSize;
    uint32_t flags;
    uint32_t hCursor;
    int32_t ptX;
    int32_t ptY;
};
// END_STRUCT_CURSORINFO

// START_STRUCT_MEMORYSTATUS
// START_CONTRACT:
// PURPOSE: Структура MEMORYSTATUS для GlobalMemoryStatus.
// ATTRIBUTES:
// - [Размер структуры] => dwLength: [uint32_t]
// - [Процент загрузки памяти] => dwMemoryLoad: [uint32_t]
// - [Всего физической памяти] => dwTotalPhys: [uint32_t]
// - [Доступно физической памяти] => dwAvailPhys: [uint32_t]
// - [Всего файла подкачки] => dwTotalPageFile: [uint32_t]
// - [Доступно файла подкачки] => dwAvailPageFile: [uint32_t]
// - [Всего виртуальной памяти] => dwTotalVirtual: [uint32_t]
// - [Доступно виртуальной памяти] => dwAvailVirtual: [uint32_t]
// KEYWORDS: [DOMAIN(8): MemoryInfo; TECH(7): Kernel32]
// END_CONTRACT
struct MEMORYSTATUS {
    uint32_t dwLength;
    uint32_t dwMemoryLoad;
    uint32_t dwTotalPhys;
    uint32_t dwAvailPhys;
    uint32_t dwTotalPageFile;
    uint32_t dwAvailPageFile;
    uint32_t dwTotalVirtual;
    uint32_t dwAvailVirtual;
};
// END_STRUCT_MEMORYSTATUS

// END_STRUCTS_WINDOWS_API

// Forward declarations
inline void set_fallback_seed(uint32_t seed);
inline uint32_t random_uint32_fallback();
inline uint32_t random_uint32_range_fallback(uint32_t min_val, uint32_t max_val);
inline std::vector<uint8_t> gen_le_range_fallback(const std::string& start_hex,
                                                   const std::string& end_hex = "",
                                                   size_t size = 4);

// Logging helper
inline void LogToAiState(const std::string& classifier, const std::string& func,
                        const std::string& block, const std::string& op,
                        const char* desc, const std::string& status) {
    std::string logLine = "[" + classifier + "][" + func + "][" + block + "][" + op + "] " + (desc ? desc : "") + " [" + status + "]";
    std::ofstream logFile("app.log", std::ios_base::app);
    if (logFile.is_open()) {
        logFile << logLine << std::endl;
    }
}

#ifdef ENABLE_LOGGING
#define LOG_TRACE_FB(classifier, func, block, op, desc, status) \
    LogToAiState(classifier, func, block, op, desc, status);
// Бинарный вывод без строковых операций в hot path
#define LOG_TRACE_FB_BIN(classifier, func, block, op, status) \
    LogToAiState(classifier, func, block, op, nullptr, status);
#else
#define LOG_TRACE_FB(classifier, func, block, op, desc, status)
#define LOG_TRACE_FB_BIN(classifier, func, block, op, status)
#endif

// START_FUNCTION_set_fallback_seed
// START_CONTRACT:
// PURPOSE: Установка seed для fallback генератора случайных чисел.
// INPUTS:
// - [Seed для генератора] => seed: [uint32_t]
// OUTPUTS: void
// KEYWORDS: [CONCEPT(5): RandomSeed]
// END_CONTRACT
inline void set_fallback_seed(uint32_t seed) {
    const char* FuncName = "set_fallback_seed";
    LOG_TRACE_FB_BIN("VarCheck", FuncName, "INPUT_PARAMS", "Params", "INFO");
    std::srand(seed);
    LOG_TRACE_FB_BIN("TraceCheck", FuncName, "SET_SEED", "StepComplete", "SUCCESS");
}

// START_FUNCTION_random_uint32_fallback
// START_CONTRACT:
// PURPOSE: Генерация случайного uint32_t для fallback.
// OUTPUTS:
// - uint32_t - Случайное число
// KEYWORDS: [CONCEPT(6): RandomGeneration]
// END_CONTRACT
inline uint32_t random_uint32_fallback() {
    return static_cast<uint32_t>(std::rand());
}

// START_FUNCTION_random_uint32_range_fallback
// START_CONTRACT:
// PURPOSE: Генерация случайного uint32_t в заданном диапазоне.
// INPUTS:
// - [Минимальное значение] => min_val: [uint32_t]
// - [Максимальное значение] => max_val: [uint32_t]
// OUTPUTS:
// - uint32_t - Случайное число в диапазоне [min_val, max_val]
// KEYWORDS: [CONCEPT(6): RandomGeneration; CONCEPT(7): RangeCheck]
// END_CONTRACT
inline uint32_t random_uint32_range_fallback(uint32_t min_val, uint32_t max_val) {
    return min_val + (std::rand() % (max_val - min_val + 1));
}

// START_FUNCTION_gen_le_range_fallback
// START_CONTRACT:
// PURPOSE: Генерирует байтовую последовательность (Little-Endian) из hex-диапазонов.
// INPUTS:
// - [Начало диапазона или константы] => start_hex: [std::string]
// - [Конец диапазона] => end_hex: [std::string]
// - [Размер в байтах] => size: [size_t]
// OUTPUTS:
// - std::vector<uint8_t> - Упакованное значение
// KEYWORDS: [PATTERN(7): Factory; DOMAIN(5): DataConversion; TECH(6): Struct]
// END_CONTRACT
inline std::vector<uint8_t> gen_le_range_fallback(const std::string& start_hex,
                                                  const std::string& end_hex,
                                                  size_t size) {
    const char* FuncName = "gen_le_range_fallback";
    uint64_t val = 0;
    bool is_const_list = false;
    std::vector<uint64_t> options;

    // START_BLOCK_PARSE_HEX: [Парсинг hex-строк и определение режима.]
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
            size_t idx = random_uint32_fallback() % options.size();
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
        val = s + (random_uint32_fallback() % (e - s + 1));
    }
    // END_BLOCK_PARSE_HEX

    // START_BLOCK_PACK_LE: [Упаковка значения в Little-Endian.]
    std::vector<uint8_t> result(size, 0);
    for (size_t i = 0; i < size && i < 8; ++i) {
        result[i] = static_cast<uint8_t>((val >> (i * 8)) & 0xFF);
    }
    // END_BLOCK_PACK_LE

    return result;
}
// END_FUNCTION_gen_le_range_fallback

// START_CLASS_RandPollFallback
// START_CONTRACT:
// PURPOSE: Standalone fallback эмулятор RAND_poll.
// Не требует OpenSSL, возвращает сырые байтовые данные энтропии.
// ATTRIBUTES:
// - [Seed для генератора] => seed: [uint32_t]
// - [Выполненные фазы] => phases_executed: [std::vector<bool>]
// KEYWORDS: [PATTERN(8): Builder; DOMAIN(9): EntropyEmulation; TECH(5): Standalone]
// END_CONTRACT

class RandPollFallback {
public:
    // START_METHOD___init__
// START_CONTRACT:
// PURPOSE: Инициализация fallback эмулятора.
// INPUTS:
// - [Seed для воспроизводимости] => seed: [uint32_t]
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
    RandPollFallback(uint32_t seed = 0) : seed(seed) {
        if (seed != 0) {
            set_fallback_seed(seed);
        } else {
            uint32_t time_seed = static_cast<uint32_t>(std::time(nullptr));
            set_fallback_seed(time_seed);
            this->seed = time_seed;
        }
        
        phases_executed.resize(5, false);
        
        LOG_TRACE_FB_BIN("SelfCheck", "__init__", "INIT_STATE", "Params", "SUCCESS");
    }
    // END_METHOD___init__

    // START_METHOD_phase_1_netapi
    // START_CONTRACT:
    // PURPOSE: Эмуляция фазы 1 - NetAPI статистика (LanmanWorkstation, LanmanServer).
    // Возвращает 32 + 17 полей + HCRYPTPROV = ~200 байт данных.
    // OUTPUTS:
    // - std::vector<uint8_t> - Данные энтропии фазы 1
    // KEYWORDS: [DOMAIN(8): Networking; TECH(7): NetAPI32]
    // END_CONTRACT
    std::vector<uint8_t> phase_1_netapi() {
        const char* FuncName = "phase_1_netapi";
        LOG_TRACE_FB("TraceCheck", FuncName, "PHASE_START", "StepStart", 
                      "Начало фазы 1: NetAPI", "INFO");
        
        std::vector<uint8_t> entropy_data;
        
        // START_BLOCK_LANMAN_WORKSTATION: [Генерация статистики LanmanWorkstation - 32 поля.]
        // Поля из rand_poll_constants.txt (пункт 1.1 - 1.38)
        std::vector<uint8_t> temp;
        
        // StatisticsStartTime (8 байт)
        temp = gen_le_range_fallback("00 5D 69 49", "00 B1 76 49", 8);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // BytesReceived (8 байт)
        temp = gen_le_range_fallback("A5 0D 00 00", "00 40 78 1D", 8);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // SmbsReceived (8 байт)
        temp = gen_le_range_fallback("E8 03 00 00", "10 27 00 00", 8);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // PagingReadBytesRequested (8 байт)
        temp = gen_le_range_fallback("00 B0 6B 2F", "00 40 07 54", 8);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // NonPagingReadBytesRequested (8 байт)
        temp = gen_le_range_fallback("00 12 7A 05", "00 37 EE 11", 8);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // CacheReadBytesRequested (8 байт)
        temp = gen_le_range_fallback("00 B0 6B 2F", "00 60 69 59", 8);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // NetworkReadBytesRequested (8 байт)
        temp = gen_le_range_fallback("00 32 D0 02", "00 98 96 08", 8);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // BytesTransmitted (8 байт)
        temp = gen_le_range_fallback("00 42 31 01", "00 08 AF 04", 8);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // SmbsTransmitted (8 байт)
        temp = gen_le_range_fallback("B8 0B 00 00", "10 27 00 00", 8);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // PagingWriteBytesRequested (8 байт)
        temp = gen_le_range_fallback("00 42 31 01", "00 08 AF 08", 8);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // NonPagingWriteBytesRequested (8 байт)
        temp = gen_le_range_fallback("00 10 A5 01", "00 30 D4 05", 8);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // CacheWriteBytesRequested (8 байт)
        temp = gen_le_range_fallback("00 20 BC 05", "00 80 D6 17", 8);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // NetworkWriteBytesRequested (8 байт)
        temp = gen_le_range_fallback("00 96 98 00", "00 FA 21 02", 8);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // InitiallyFailedOperations (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "0A 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // FailedCompletionOperations (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "05 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // ReadOperations (4 байта)
        temp = gen_le_range_fallback("40 38 01 00", "D0 D0 03 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // RandomAccessReadOperations (4 байта)
        temp = gen_le_range_fallback("30 75 00 00", "A0 86 01 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // ReadSmbs (4 байта)
        temp = gen_le_range_fallback("F4 01 00 00", "D0 07 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // LargeReadSmbs (4 байта)
        temp = gen_le_range_fallback("64 00 00 00", "F4 01 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // SmallReadSmbs (4 байта)
        temp = gen_le_range_fallback("90 01 00 00", "DC 05 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // WriteOperations (4 байта)
        temp = gen_le_range_fallback("20 4E 00 00", "18 11 01 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // RandomAccessWriteOperations (4 байта)
        temp = gen_le_range_fallback("10 27 00 00", "30 75 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // WriteSmbs (4 байта)
        temp = gen_le_range_fallback("C8 00 00 00", "E8 03 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // LargeWriteSmbs (4 байта)
        temp = gen_le_range_fallback("32 00 00 00", "C8 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // SmallWriteSmbs (4 байта)
        temp = gen_le_range_fallback("96 00 00 00", "20 03 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // RawReadsDenied (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "00 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // RawWritesDenied (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "00 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // NetworkErrors (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "05 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // Sessions (4 байта)
        temp = gen_le_range_fallback("01 00 00 00", "03 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // FailedSessions (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "00 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // Reconnects (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "05 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // CoreConnects (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "02 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // Lanman20Connects (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "00 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // Lanman21Connects (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "00 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // LanmanNtConnects (4 байта)
        temp = gen_le_range_fallback("01 00 00 00", "03 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // ServerDisconnects (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "05 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // HungSessions (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "00 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // UseCount (4 байта)
        temp = gen_le_range_fallback("01 00 00 00", "0A 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        // END_BLOCK_LANMAN_WORKSTATION
        
        // START_BLOCK_LANMAN_SERVER: [Генерация статистики LanmanServer - 17 полей.]
        // Поля из rand_poll_constants.txt (пункт 2.1 - 2.17)
        
        // sts0_start (4 байта)
        temp = gen_le_range_fallback("80 81 66 49", "80 B0 70 49", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // sts0_fopens (4 байта)
        temp = gen_le_range_fallback("0A 00 00 00", "64 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // sts0_devopens (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "00 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // sts0_jobsqueued (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "00 00 05 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // sts0_sopens (4 байта)
        temp = gen_le_range_fallback("01 00 00 00", "05 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // sts0_stimedout (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "02 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // sts0_serrorout (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "00 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // sts0_pwerrors (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "05 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // sts0_perrors (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "00 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // sts0_syserrors (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "00 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // sts0_bytessent_low (4 байта)
        temp = gen_le_range_fallback("00 40 06 00", "00 A0 7C 05", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // sts0_bytessent_high (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "00 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // sts0_bytesrcvd_low (4 байта)
        temp = gen_le_range_fallback("00 00 01 00", "00 00 C0 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // sts0_bytesrcvd_high (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "00 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // sts0_avresponse (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "0A 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // sts0_reqbufneed (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "00 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // sts0_bigbufneed (4 байта)
        temp = gen_le_range_fallback("00 00 00 00", "00 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        // END_BLOCK_LANMAN_SERVER
        
        // START_BLOCK_HCRYPTPROV: [Генерация HCRYPTPROV (4 байта).]
        temp = gen_le_range_fallback("00 00 10 00", "00 00 90 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        // END_BLOCK_HCRYPTPROV
        
        phases_executed[0] = true;
        
        LOG_TRACE_FB_BIN("TraceCheck", FuncName, "PHASE_COMPLETE", "StepComplete", "SUCCESS");
        
        return entropy_data;
    }
    // END_METHOD_phase_1_netapi

    // START_METHOD_phase_2_cryptoapi
    // START_CONTRACT:
    // PURPOSE: Эмуляция фазы 2 - CryptGenRandom (64 байта случайных данных).
    // OUTPUTS:
    // - std::vector<uint8_t> - Данные энтропии фазы 2
    // KEYWORDS: [DOMAIN(9): Crypto; TECH(8): CryptoAPI]
    // END_CONTRACT
    std::vector<uint8_t> phase_2_cryptoapi() {
        const char* FuncName = "phase_2_cryptoapi";
        LOG_TRACE_FB("TraceCheck", FuncName, "PHASE_START", "StepStart", 
                      "Начало фазы 2: CryptoAPI", "INFO");
        
        // START_BLOCK_CRYPT_GEN_RANDOM: [Генерация 64 случайных байт.]
        std::vector<uint8_t> entropy_data(64);
        for (size_t i = 0; i < 64; ++i) {
            entropy_data[i] = static_cast<uint8_t>(random_uint32_fallback() % 256);
        }
        // END_BLOCK_CRYPT_GEN_RANDOM
        
        phases_executed[1] = true;
        
        LOG_TRACE_FB_BIN("TraceCheck", FuncName, "PHASE_COMPLETE", "StepComplete", "SUCCESS");
        
        return entropy_data;
    }
    // END_METHOD_phase_2_cryptoapi

    // START_METHOD_phase_3_user32
    // START_CONTRACT:
    // PURPOSE: Эмуляция фазы 3 - User32 UI данные (GetForegroundWindow, CURSORINFO, GetQueueStatus).
    // OUTPUTS:
    // - std::vector<uint8_t> - Данные энтропии фазы 3
    // KEYWORDS: [DOMAIN(7): UI_State; TECH(6): User32]
    // END_CONTRACT
    std::vector<uint8_t> phase_3_user32() {
        const char* FuncName = "phase_3_user32";
        LOG_TRACE_FB_BIN("TraceCheck", FuncName, "PHASE_START", "StepStart", "INFO");
        
        std::vector<uint8_t> entropy_data;
        std::vector<uint8_t> temp;
        
        // START_BLOCK_GET_FOREGROUND_WINDOW: [Генерация HWND (4 байта).]
        temp = gen_le_range_fallback("00 00 01 00, 24 01 00 00", "", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        // END_BLOCK_GET_FOREGROUND_WINDOW
        
        // START_BLOCK_CURSORINFO: [Генерация CURSORINFO (20 байт).]
        // cbSize (4 байта)
        temp = gen_le_range_fallback("14 00 00 00", "", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // flags (4 байта)
        temp = gen_le_range_fallback("01 00 00 00", "", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // hCursor (4 байта)
        temp = gen_le_range_fallback("02 00 01 00", "", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // pt.x (4 байта)
        temp = gen_le_range_fallback("80 02 00 00", "", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // pt.y (4 байта)
        temp = gen_le_range_fallback("00 02 00 00", "", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        // END_BLOCK_CURSORINFO
        
        // START_BLOCK_GET_QUEUE_STATUS: [Генерация QueueStatus (4 байта).]
        temp = gen_le_range_fallback("6B 00 00 00", "", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        // END_BLOCK_GET_QUEUE_STATUS
        
        phases_executed[2] = true;
        
        LOG_TRACE_FB_BIN("TraceCheck", FuncName, "PHASE_COMPLETE", "StepComplete", "SUCCESS");
        
        return entropy_data;
    }
    // END_METHOD_phase_3_user32

    // START_METHOD_phase_4_toolhelp32
    // START_CONTRACT:
    // PURPOSE: Эмуляция фазы 4 - Toolhelp32Snapshot (процессы, потоки, модули).
    // OUTPUTS:
    // - std::vector<uint8_t> - Данные энтропии фазы 4
    // KEYWORDS: [DOMAIN(9): OS_Internals; TECH(8): Kernel32]
    // END_CONTRACT
    std::vector<uint8_t> phase_4_toolhelp32() {
        const char* FuncName = "phase_4_toolhelp32";
        LOG_TRACE_FB("TraceCheck", FuncName, "PHASE_START", "StepStart", 
                      "Начало фазы 4: Toolhelp32", "INFO");
        
        std::vector<uint8_t> entropy_data;
        std::vector<uint8_t> temp;
        
        // Модель процессов для эмуляции (4 процесса)
        const int num_processes = 4;
        const uint32_t pids[] = {0x00050A00, 0x00070A00, 0x00090A00, 0x00100A30};
        const uint32_t thread_counts[] = {80, 3, 25, 12};
        
        // START_BLOCK_HEAPLIST32: [Генерация HEAPLIST32 + HEAPENTRY32.]
        for (int p = 0; p < num_processes; ++p) {
            // HEAPLIST32 (16 байт)
            temp = gen_le_range_fallback("10 00 00 00", "", 4);
            entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
            
            // th32ProcessID
            temp = gen_le_range_fallback("A0 05 00 00", "30 11 00 00", 4);
            entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
            
            // th32HeapID
            std::vector<uint8_t> heap_id_bytes = gen_le_range_fallback("00 00 09 00", "00 00 60 04", 4);
            entropy_data.insert(entropy_data.end(), heap_id_bytes.begin(), heap_id_bytes.end());
            
            // dwFlags
            temp = gen_le_range_fallback("00 00 00 00", "", 4);
            entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
            
            // HEAPENTRY32 (до 40 записей)
            uint32_t entry_count = random_uint32_range_fallback(15, 40);
            for (uint32_t e = 0; e < entry_count; ++e) {
                // dwSize (4 байта)
                temp = gen_le_range_fallback("24 00 00 00", "", 4);
                entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
                
                // hHandle = th32HeapID
                entropy_data.insert(entropy_data.end(), heap_id_bytes.begin(), heap_id_bytes.end());
                
                // dwAddress
                uint32_t addr = random_uint32_range_fallback(0x00090500, 0x00100000);
                std::vector<uint8_t> addr_bytes(4);
                for (size_t i = 0; i < 4; ++i) {
                    addr_bytes[i] = static_cast<uint8_t>((addr >> (i * 8)) & 0xFF);
                }
                entropy_data.insert(entropy_data.end(), addr_bytes.begin(), addr_bytes.end());
                
                // dwBlockSize
                temp = gen_le_range_fallback("20 00 00 00", "40 00 00 00", 4);
                entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
                
                // dwFlags
                temp = gen_le_range_fallback("01 00 00 00, 02 00 00 00", "", 4);
                entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
                
                // dwLockCount
                temp = gen_le_range_fallback("00 00 00 00", "", 4);
                entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
                
                // dwResvd (1 байт)
                entropy_data.push_back(0x00);
                
                // th32ProcessID
                temp = gen_le_range_fallback("A0 05 00 00", "30 11 00 00", 4);
                entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
                
                // th32HeapID
                temp = gen_le_range_fallback("00 15 00 00", "05 00 00 00", 4);
                entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
            }
        }
        // END_BLOCK_HEAPLIST32
        
        // START_BLOCK_PROCESSENTRY32: [Генерация PROCESSENTRY32.]
        for (int p = 0; p < num_processes; ++p) {
            // dwSize (4 байта)
            temp = gen_le_range_fallback("28 01 00 00", "", 4);
            entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
            
            // cntUsage
            temp = gen_le_range_fallback("00 00 00 00", "", 4);
            entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
            
            // th32ProcessID
            temp = gen_le_range_fallback("A0 05 00 00", "30 11 00 00", 4);
            entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
            
            // th32DefaultHeapID
            temp = gen_le_range_fallback("00 00 00 00", "", 4);
            entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
            
            // th32ModuleID
            temp = gen_le_range_fallback("00 00 00 00", "", 4);
            entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
            
            // cntThreads
            temp = gen_le_range_fallback("03 00 00 00", "08 00 00 00", 4);
            entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
            
            // th32ParentProcessID
            temp = gen_le_range_fallback("20 02 00 00", "50 06 00 00", 4);
            entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
            
            // pcPriClassBase
            temp = gen_le_range_fallback("08 00 00 00", "", 4);
            entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
            
            // dwFlags
            temp = gen_le_range_fallback("00 00 00 00", "", 4);
            entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
            
            // szExeFile (260 байт) - bitcoin.exe
            std::vector<uint8_t> exe_name(260, 0);
            const char* bitcoin_name = "bitcoin.exe";
            for (size_t i = 0; i < strlen(bitcoin_name) && i < exe_name.size(); ++i) {
                exe_name[i] = static_cast<uint8_t>(bitcoin_name[i]);
            }
            entropy_data.insert(entropy_data.end(), exe_name.begin(), exe_name.end());
        }
        // END_BLOCK_PROCESSENTRY32
        
        // START_BLOCK_THREADENTRY32: [Генерация THREADENTRY32.]
        for (int p = 0; p < num_processes; ++p) {
            for (int t = 0; t < static_cast<int>(thread_counts[p]); ++t) {
                // dwSize (4 байта)
                temp = gen_le_range_fallback("1C 00 00 00", "", 4);
                entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
                
                // cntUsage
                temp = gen_le_range_fallback("00 00 00 00", "", 4);
                entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
                
                // th32ThreadID
                temp = gen_le_range_fallback("04 00 00 00", "50 12 00 00", 4);
                entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
                
                // th32OwnerProcessID
                temp = gen_le_range_fallback("A0 05 00 00", "30 11 00 00", 4);
                entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
                
                // tpBasePri
                temp = gen_le_range_fallback("04 00 00 00", "0F 00 00 00", 4);
                entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
                
                // tpDeltaPri
                temp = gen_le_range_fallback("00 00 00 00", "", 4);
                entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
                
                // dwFlags
                temp = gen_le_range_fallback("00 00 00 00", "", 4);
                entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
            }
        }
        // END_BLOCK_THREADENTRY32
        
        // START_BLOCK_MODULEENTRY32: [Генерация MODULEENTRY32.]
        // dwSize (4 байта)
        temp = gen_le_range_fallback("24 02 00 00", "", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // th32ModuleID
        temp = gen_le_range_fallback("01 00 00 00", "", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // th32ProcessID
        temp = gen_le_range_fallback("A0 05 00 00", "30 11 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // GlblcntUsage
        temp = gen_le_range_fallback("FF FF 00 00", "", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // ProccntUsage
        temp = gen_le_range_fallback("FF FF 00 00", "", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // modBaseAddr (4 байта)
        temp = gen_le_range_fallback("00 00 40 00", "", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // modBaseSize (4 байта)
        temp = gen_le_range_fallback("00 00 70 00", "", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // szModule (256 байт) - itcoin.exe
        std::vector<uint8_t> mod_name(256, 0);
        const char* mod_str = "itcoin.exe";
        for (size_t i = 0; i < strlen(mod_str) && i < mod_name.size(); ++i) {
            mod_name[i] = static_cast<uint8_t>(mod_str[i]);
        }
        entropy_data.insert(entropy_data.end(), mod_name.begin(), mod_name.end());
        
        // szExePath (260 байт) - C:\bitcoin\bitcoin.exe
        std::vector<uint8_t> mod_path(260, 0);
        const char* path_str = "C:\\bitcoin\\bitcoin.exe";
        for (size_t i = 0; i < strlen(path_str) && i < mod_path.size(); ++i) {
            mod_path[i] = static_cast<uint8_t>(path_str[i]);
        }
        entropy_data.insert(entropy_data.end(), mod_path.begin(), mod_path.end());
        // END_BLOCK_MODULEENTRY32
        
        phases_executed[3] = true;
        
        LOG_TRACE_FB("TraceCheck", FuncName, "PHASE_COMPLETE", "StepComplete", 
                     "Фаза 4 завершена, сгенерировано " + std::to_string(entropy_data.size()) + " байт", "SUCCESS");
        
        return entropy_data;
    }
    // END_METHOD_phase_4_toolhelp32

    // START_METHOD_phase_5_kernel32
    // START_CONTRACT:
    // PURPOSE: Эмуляция фазы 5 - Kernel32 системные данные (RDTSC, QPC, MemoryStatus, PID).
    // OUTPUTS:
    // - std::vector<uint8_t> - Данные энтропии фазы 5
    // KEYWORDS: [DOMAIN(8): SystemInfo; TECH(7): Timers]
    // END_CONTRACT
    std::vector<uint8_t> phase_5_kernel32() {
        const char* FuncName = "phase_5_kernel32";
        LOG_TRACE_FB("TraceCheck", FuncName, "PHASE_START", "StepStart", 
                      "Начало фазы 5: Kernel32", "INFO");
        
        std::vector<uint8_t> entropy_data;
        std::vector<uint8_t> temp;
        
        // START_BLOCK_RDTSC: [Генерация RDTSC (4 байта).]
        temp = gen_le_range_fallback("00 00 00 00", "FF FF FF FF", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        // END_BLOCK_RDTSC
        
        // START_BLOCK_QPC: [Генерация QueryPerformanceCounter (8 байт).]
        temp = gen_le_range_fallback("E4 35 01 C0 00 00 00 00", "A8 42 10 00 09 00 00 00", 8);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        // END_BLOCK_QPC
        
        // START_BLOCK_MEMORYSTATUS: [Генерация MEMORYSTATUS (32 байта).]
        // dwLength
        temp = gen_le_range_fallback("20 00 00 00", "", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // dwMemoryLoad
        temp = gen_le_range_fallback("0F 00 00 00", "1E 00 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // dwTotalPhys
        temp = gen_le_range_fallback("00 00 D0 CF", "00 00 00 E0", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // dwAvailPhys
        temp = gen_le_range_fallback("00 9C E4 A6", "00 3F C6 B8", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // dwTotalPageFile
        temp = gen_le_range_fallback("00 F2 05 2A", "00 86 3B A1", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // dwAvailPageFile
        temp = gen_le_range_fallback("00 8D 38 0C", "00 21 6E 83", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // dwTotalVirtual
        temp = gen_le_range_fallback("00 00 FE 7F, FF FF FF 7F", "", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        
        // dwAvailVirtual
        temp = gen_le_range_fallback("00 F0 FD 7F, F0 FD 7F 00", "", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        // END_BLOCK_MEMORYSTATUS
        
        // START_BLOCK_PID: [Генерация GetCurrentProcessId (4 байта).]
        temp = gen_le_range_fallback("6C 07 00 00", "C4 09 00 00", 4);
        entropy_data.insert(entropy_data.end(), temp.begin(), temp.end());
        // END_BLOCK_PID
        
        phases_executed[4] = true;
        
        LOG_TRACE_FB("TraceCheck", FuncName, "PHASE_COMPLETE", "StepComplete", 
                     "Фаза 5 завершена, сгенерировано " + std::to_string(entropy_data.size()) + " байт", "SUCCESS");
        
        return entropy_data;
    }
    // END_METHOD_phase_5_kernel32

    // START_METHOD_generate_full_entropy
    // START_CONTRACT:
    // PURPOSE: Генерирует полную энтропию всех 5 фаз.
    // OUTPUTS:
    // - std::vector<uint8_t> - Конкатенация всех фаз
    // KEYWORDS: [PATTERN(9): TemplateMethod; CONCEPT(8): Workflow]
    // END_CONTRACT
    std::vector<uint8_t> generate_full_entropy() {
        const char* FuncName = "generate_full_entropy";
        LOG_TRACE_FB("TraceCheck", FuncName, "EXEC_FLOW", "StepStart", 
                      "Начало генерации полной энтропии (5 фаз)", "INFO");
        
        std::vector<uint8_t> all_entropy;
        
        // Фаза 1: NetAPI
        std::vector<uint8_t> phase1 = phase_1_netapi();
        all_entropy.insert(all_entropy.end(), phase1.begin(), phase1.end());
        
        // Фаза 2: CryptoAPI
        std::vector<uint8_t> phase2 = phase_2_cryptoapi();
        all_entropy.insert(all_entropy.end(), phase2.begin(), phase2.end());
        
        // Фаза 3: User32
        std::vector<uint8_t> phase3 = phase_3_user32();
        all_entropy.insert(all_entropy.end(), phase3.begin(), phase3.end());
        
        // Фаза 4: Toolhelp32
        std::vector<uint8_t> phase4 = phase_4_toolhelp32();
        all_entropy.insert(all_entropy.end(), phase4.begin(), phase4.end());
        
        // Фаза 5: Kernel32
        std::vector<uint8_t> phase5 = phase_5_kernel32();
        all_entropy.insert(all_entropy.end(), phase5.begin(), phase5.end());
        
        LOG_TRACE_FB("TraceCheck", FuncName, "EXEC_FLOW", "ReturnData", 
                     "Генерация завершена, всего " + std::to_string(all_entropy.size()) + " байт", "SUCCESS");
        
        return all_entropy;
    }
    // END_METHOD_generate_full_entropy

    // START_METHOD_get_entropy
    // START_CONTRACT:
    // PURPOSE: Получение энтропии указанного размера.
    // INPUTS:
    // - [Требуемый размер в байтах] => size: [size_t]
    // OUTPUTS:
    // - std::vector<uint8_t> - Энтропия указанного размера
    // KEYWORDS: [DOMAIN(10): EntropyGeneration; CONCEPT(7): DataGeneration]
    // END_CONTRACT
    std::vector<uint8_t> get_entropy(size_t size) {
        const char* FuncName = "get_entropy";
        LOG_TRACE_FB("VarCheck", FuncName, "INPUT_PARAMS", "Params", 
                      "Запрошен размер энтропии: " + std::to_string(size), "INFO");
        
        // Генерируем полную энтропию
        std::vector<uint8_t> full_entropy = generate_full_entropy();
        
        // Если данных больше чем нужно, обрезаем
        if (full_entropy.size() >= size) {
            full_entropy.resize(size);
            return full_entropy;
        }
        
        // Если данных меньше, дополняем
        std::vector<uint8_t> result = full_entropy;
        while (result.size() < size) {
            size_t remaining = size - result.size();
            size_t copy_size = std::min(full_entropy.size(), remaining);
            result.insert(result.end(), full_entropy.begin(), full_entropy.begin() + copy_size);
        }
        
        LOG_TRACE_FB("TraceCheck", FuncName, "RETURN_DATA", "ReturnData", 
                     "Возвращено " + std::to_string(result.size()) + " байт", "SUCCESS");
        
        return result;
    }
    // END_METHOD_get_entropy

    // START_METHOD_get_phases_info
    // START_CONTRACT:
    // PURPOSE: Получение информации о выполненных фазах.
    // OUTPUTS:
    // - std::vector<bool> - Вектор флагов выполнения фаз
    // KEYWORDS: [CONCEPT(5): Introspection]
    // END_CONTRACT
    std::vector<bool> get_phases_info() const {
        return phases_executed;
    }
    // END_METHOD_get_phases_info

private:
    uint32_t seed;
    std::vector<bool> phases_executed;
};
// END_CLASS_RandPollFallback

// START_STANDALONE_FUNCTIONS
// START_CONTRACT:
// PURPOSE: Удобные функции-обертки для использования без создания класса.
// KEYWORDS: [CONCEPT(6): ConvenienceWrapper]
// END_CONTRACT

// START_FUNCTION_generate_entropy_fallback
// START_CONTRACT:
// PURPOSE: Генерирует энтропию используя fallback эмуляцию.
// INPUTS:
// - [Требуемый размер] => size: [size_t]
// - [Seed для воспроизводимости] => seed: [uint32_t]
// OUTPUTS:
// - std::vector<uint8_t> - Сгенерированная энтропия
// KEYWORDS: [DOMAIN(10): EntropyGeneration; CONCEPT(8): Standalone]
// END_CONTRACT
inline std::vector<uint8_t> generate_entropy_fallback(size_t size, uint32_t seed = 0) {
    RandPollFallback fallback(seed);
    return fallback.get_entropy(size);
}
// END_FUNCTION_generate_entropy_fallback

// START_FUNCTION_generate_full_entropy_fallback
// START_CONTRACT:
// PURPOSE: Генерирует полную энтропию всех 5 фаз.
// INPUTS:
// - [Seed для воспроизводимости] => seed: [uint32_t]
// OUTPUTS:
// - std::vector<uint8_t> - Полная энтропия
// KEYWORDS: [DOMAIN(10): EntropyGeneration; CONCEPT(8): FullPipeline]
// END_CONTRACT
inline std::vector<uint8_t> generate_full_entropy_fallback(uint32_t seed = 0) {
    RandPollFallback fallback(seed);
    return fallback.generate_full_entropy();
}
// END_FUNCTION_generate_full_entropy_fallback

// END_STANDALONE_FUNCTIONS

#endif // RAND_POLL_FALLBACK_HPP
