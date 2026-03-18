// FILE: src/plugins/cpu/randaddseed/hkey_performance_data.cpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Высокопроизводительная генерация данных HKEY_PERFORMANCE_DATA для имитации
// поведения Windows XP SP3 на Intel Core 2 Quad Q6600. Модуль генерирует бинарные данные,
// совместимые с форматом PERF_DATA_BLOCK, PERF_OBJECT_TYPE, PERF_COUNTER_DEFINITION,
// PERF_INSTANCE_DEFINITION и PERF_COUNTER_BLOCK. Также реализует MD5 хеширование
// и добавление энтропии в PRNG через RAND_add() согласно Bitcoin 0.1.0.
// SCOPE: Генерация бинарных структур данных Windows Performance Counter, выравнивание памяти,
// создание случайных временных меток, имитация мусора в памяти (stack/heap garbage),
// MD5 хеширование и оценка энтропии.
// INPUT: seconds_passed (int) - количество секунд, прошедших с базовой точки времени;
// rand_add_impl (RandAddImplementation*) - указатель на реализацию RAND_add.
// OUTPUT: std::vector<uint8_t> - бинарный буфер с данными HKEY_PERFORMANCE_DATA (legacy функция);
// void - модификация состояния PRNG через RAND_add (новая функция).
// KEYWORDS: [DOMAIN(9): WindowsPerformance; DOMAIN(8): Forensics; TECH(9): MD5; TECH(7): BinaryStructures; CONCEPT(9): EntropyEstimation; CONCEPT(6): MemoryAlignment]
// LINKS: [READS_DATA_FROM(6): hkey_performance_data.txt; USES_API(9): OpenSSL_MD5; CALLS(9): RandAddImplementation.rand_add]
// END_MODULE_CONTRACT
// START_MODULE_MAP:
// FUNC 9 [Выравнивает размер до границы 8 байт] => align_8
// FUNC 8 [Генерирует грязный паддинг с мусором из памяти XP] => get_dirty_padding
// FUNC 9 [Генерирует один объект PERF_OBJECT_TYPE] => generate_single_object
// FUNC 9 [Генерирует полный дамп HKEY_PERFORMANCE_DATA (legacy версия)] => generate_hkey_performance_data_legacy
// FUNC 9 [Генерирует дамп, вычисляет MD5 и вызывает RAND_add] => generate_hkey_performance_data
// CONST 7 [Базовая частота производительности Windows XP] => PERF_FREQ
// CONST 6 [Количество ядер Q6600] => Q6600_CORES
// END_MODULE_MAP
// START_USE_CASES:
// - [generate_hkey_performance_data_legacy]: ForensicTool (BitcoinWalletAnalysis) -> GenerateEntropyData -> PerformanceDataAvailable
// - [generate_hkey_performance_data]: BitcoinCore (Startup) -> AddEntropyToPRNG -> PRNGStateUpdated
// - [generate_single_object]: Generator (ObjectCreation) -> BuildPerfObject -> ObjectBufferReady
// END_USE_CASES

#include <vector>
#include <cstdint>
#include <cstring>
#include <random>
#include <ctime>
#include <string>
#include <algorithm>
#include <openssl/md5.h>
#include "rand_add.h"
#include "cache/include/entropy_pipeline_cache.hpp"

// Global reference to entropy cache (initialized in RAND_poll)
extern std::shared_ptr<EntropyPipelineCache> g_entropy_cache;

// START_CONSTANTS
// Константы для Q6600 и Windows XP SP3
constexpr uint32_t Q6600_CORES = 4;
constexpr uint64_t PERF_FREQ = 3579545ULL;
constexpr uint64_t BASE_PERF_TIME = 0xC00505E4ULL;
constexpr uint64_t BASE_PERF_100NS = 128755000000000000ULL;

// Размеры структур Windows Performance
constexpr uint32_t PERF_COUNTER_DEF_SIZE = 40;
constexpr uint32_t PERF_OBJECT_HEADER_SIZE = 64;
constexpr uint32_t PERF_DATA_BLOCK_SIZE = 64;
constexpr uint32_t PERF_INSTANCE_DEF_HEADER_SIZE = 40;
// END_CONSTANTS

// START_FUNCTION_align_8
// START_CONTRACT:
// PURPOSE: Выравнивает размер до границы 8 байт для совместимости с Windows XP.
// INPUTS:
// - [Исходный размер в байтах] => size: uint32_t
// OUTPUTS:
// - uint32_t - Выровненный размер (кратный 8)
// KEYWORDS: [TECH(8): MemoryAlignment; CONCEPT(7): Padding]
// END_CONTRACT

inline uint32_t align_8(uint32_t size) {
    return (size + 7) & ~7;
}
// END_FUNCTION_align_8

// START_FUNCTION_get_dirty_padding
// START_CONTRACT:
// PURPOSE: Генерирует грязный паддинг, имитирующий мусор из памяти Windows XP (stack/heap garbage).
// Включает значения 0x00, случайные байты и 0xCC (INT3 breakpoint).
// INPUTS:
// - [Длина паддинга в байтах] => length: uint32_t
// OUTPUTS:
// - std::vector<uint8_t> - Вектор с байтами грязного паддинга
// KEYWORDS: [DOMAIN(9): Forensics; CONCEPT(8): MemoryGarbage; TECH(6): RandomGeneration]
// END_CONTRACT

std::vector<uint8_t> get_dirty_padding(uint32_t length) {
    std::vector<uint8_t> padding;
    if (length == 0) return padding;
    
    padding.reserve(length);
    
    // Инициализация генератора случайных чисел
    static std::random_device rd;
    static std::mt19937 gen(rd());
    static std::uniform_int_distribution<uint8_t> byte_dist(0, 255);
    static std::uniform_int_distribution<uint8_t> choice_dist(0, 3);
    
    for (uint32_t i = 0; i < length; ++i) {
        uint8_t choice = choice_dist(gen);
        switch (choice) {
            case 0: padding.push_back(0x00); break;
            case 1: padding.push_back(0x00); break;
            case 2: padding.push_back(byte_dist(gen)); break;
            case 3: padding.push_back(0xCC); break; // INT3 breakpoint
        }
    }
    
    return padding;
}
// END_FUNCTION_get_dirty_padding

// START_STRUCT_PerfObjectConfig
// START_CONTRACT:
// PURPOSE: Конфигурация объекта производительности для генерации.
// ATTRIBUTES:
// - [Идентификатор объекта] => id: uint32_t
// - [Имя объекта] => name: std::string
// - [Количество счетчиков] => counter_count: uint32_t
// - [Список имен экземпляров] => instances: std::vector<std::string>
// KEYWORDS: [CONCEPT(7): Configuration; DOMAIN(8): PerformanceObjects]
// END_CONTRACT

struct PerfObjectConfig {
    uint32_t id;
    std::string name;
    uint32_t counter_count;
    std::vector<std::string> instances;
};
// END_STRUCT_PerfObjectConfig

// START_FUNCTION_get_forensic_objects_config
// START_CONTRACT:
// PURPOSE: Возвращает конфигурацию объектов производительности для Q6600/XP SP3.
// OUTPUTS:
// - std::vector<PerfObjectConfig> - Список конфигураций объектов
// KEYWORDS: [DOMAIN(9): Forensics; CONCEPT(7): Configuration; TECH(6): WindowsXP]
// END_CONTRACT

std::vector<PerfObjectConfig> get_forensic_objects_config() {
    std::vector<PerfObjectConfig> configs;

    // Детерминированный генератор для counter_count (диапазон 28-32)
    static std::mt19937 counter_gen(45); // Детерминированный генератор с фиксированным seed
    static std::uniform_int_distribution<uint32_t> counter_dist(28, 32);

    // System Object (ID: 2)
    configs.push_back({2, "System", counter_dist(counter_gen), {}});

    // Memory Object (ID: 4)
    configs.push_back({4, "Memory", counter_dist(counter_gen), {}});

    // Processor Object (ID: 238)
    std::vector<std::string> processor_instances;
    for (uint32_t i = 0; i < Q6600_CORES; ++i) {
        processor_instances.push_back(std::to_string(i));
    }
    processor_instances.push_back("_Total");
    configs.push_back({238, "Processor", counter_dist(counter_gen), processor_instances});

    // Process Object (ID: 230)
    std::vector<std::string> process_instances = {
        "System", "smss.exe", "csrss.exe", "winlogon.exe",
        "services.exe", "lsass.exe", "svchost.exe", "explorer.exe", "bitcoin.exe"
    };
    // Добавляем 3 экземпляра svchost.exe
    for (int i = 0; i < 3; ++i) {
        process_instances.push_back("svchost.exe");
    }
    configs.push_back({230, "Process", counter_dist(counter_gen), process_instances});

    // Network Object (ID: 272)
    configs.push_back({272, "Network", counter_dist(counter_gen), {"Intel(R) PRO/1000"}});

    // Объекты 6-28 (дополнительные объекты Windows XP SP3)
    // Объект 6: Processor
    configs.push_back({6, "Processor", counter_dist(counter_gen), {"_Total"}});

    // Объект 7: PhysicalDisk
    configs.push_back({7, "PhysicalDisk", counter_dist(counter_gen), {"0 C:", "1 D:"}});

    // Объект 8: Memory
    configs.push_back({8, "Memory", counter_dist(counter_gen), {}});

    // Объект 9: Network Interface
    configs.push_back({9, "Network Interface", counter_dist(counter_gen), {"Intel[R] PRO_1000 MT Network Connection"}});

    // Объекты 10-28: дополнительные объекты Windows XP SP3
    for (size_t i = 10; i <= 28; ++i) {
        configs.push_back({static_cast<uint32_t>(i), "Object_" + std::to_string(i), counter_dist(counter_gen), {}});
    }

    return configs;
}
// END_FUNCTION_get_forensic_objects_config

// START_FUNCTION_generate_single_object
// START_CONTRACT:
// PURPOSE: Генерирует бинарный буфер для одного объекта PERF_OBJECT_TYPE с соблюдением
// 8-байтового выравнивания всех структур.
// INPUTS:
// - [Конфигурация объекта] => obj_cfg: const PerfObjectConfig&
// - [Текущее время производительности] => perf_time: uint64_t
// - [Частота производительности] => perf_freq: uint64_t
// OUTPUTS:
// - std::vector<uint8_t> - Бинарный буфер объекта PERF_OBJECT_TYPE
// KEYWORDS: [DOMAIN(9): WindowsPerformance; TECH(8): BinaryStructures; CONCEPT(7): MemoryAlignment]
// END_CONTRACT

std::vector<uint8_t> generate_single_object(const PerfObjectConfig& obj_cfg, 
                                            uint64_t perf_time, 
                                            uint64_t perf_freq) {
    std::vector<uint8_t> result;
    
    uint32_t obj_id = obj_cfg.id;
    uint32_t counters_count = obj_cfg.counter_count;
    const std::vector<std::string>& instances_list = obj_cfg.instances;
    
    // START_BLOCK_GENERATE_COUNTERS: [Генерация PERF_COUNTER_DEFINITION структур]
    std::vector<uint8_t> counters_buf;
    counters_buf.reserve(counters_count * PERF_COUNTER_DEF_SIZE);
    
    uint32_t curr_data_offset = 8;
    
    for (uint32_t i = 0; i < counters_count; ++i) {
        // PERF_COUNTER_DEFINITION структура (40 байт)
        // 3.1 ByteLength
        counters_buf.insert(counters_buf.end(),
            reinterpret_cast<const uint8_t*>(&PERF_COUNTER_DEF_SIZE),
            reinterpret_cast<const uint8_t*>(&PERF_COUNTER_DEF_SIZE) + 4);

        // 3.2 NameTitleIndex
        uint32_t name_title = obj_id + (i * 2) + 2;
        counters_buf.insert(counters_buf.end(),
            reinterpret_cast<const uint8_t*>(&name_title),
            reinterpret_cast<const uint8_t*>(&name_title) + 4);

        // 3.3 Reserved
        uint32_t reserved = 0;
        counters_buf.insert(counters_buf.end(),
            reinterpret_cast<const uint8_t*>(&reserved),
            reinterpret_cast<const uint8_t*>(&reserved) + 4);

        // 3.4 HelpTitleIndex
        uint32_t help_title = obj_id + (i * 2) + 3;
        counters_buf.insert(counters_buf.end(),
            reinterpret_cast<const uint8_t*>(&help_title),
            reinterpret_cast<const uint8_t*>(&help_title) + 4);

        // 3.5 Reserved
        counters_buf.insert(counters_buf.end(),
            reinterpret_cast<const uint8_t*>(&reserved),
            reinterpret_cast<const uint8_t*>(&reserved) + 4);
        
        // 3.6 DefaultScale (список констант: 0, -1, -2, 1, 7)
        static std::vector<int32_t> default_scale_list = {0, -1, -2, 1, 7};
        static std::mt19937 scale_gen(42); // Детерминированный генератор с фиксированным seed
        static std::uniform_int_distribution<size_t> scale_dist(0, default_scale_list.size() - 1);
        int32_t default_scale = default_scale_list[scale_dist(scale_gen)];
        counters_buf.insert(counters_buf.end(),
            reinterpret_cast<const uint8_t*>(&default_scale),
            reinterpret_cast<const uint8_t*>(&default_scale) + 4);
        
        // 3.7 DetailLevel
        uint32_t detail_level = 100;
        counters_buf.insert(counters_buf.end(),
            reinterpret_cast<const uint8_t*>(&detail_level),
            reinterpret_cast<const uint8_t*>(&detail_level) + 4);
        
        // 3.8 CounterType (список констант: 0, 65536, 5253120, 66048, 66050, 5379200, 2816)
        static std::vector<uint32_t> counter_type_list = {
            0x00000000,      // 0
            0x00010000,      // 65536 - PERF_COUNTER_RAWCOUNT
            0x00505040,      // 5253120
            0x00010400,      // 66048
            0x00020400,      // 66050
            0x00512020,      // 5379200
            0x00000B00       // 2816
        };
        static std::mt19937 type_gen(43); // Детерминированный генератор с фиксированным seed
        static std::uniform_int_distribution<size_t> type_dist(0, counter_type_list.size() - 1);
        uint32_t counter_type = counter_type_list[type_dist(type_gen)];
        counters_buf.insert(counters_buf.end(),
            reinterpret_cast<const uint8_t*>(&counter_type),
            reinterpret_cast<const uint8_t*>(&counter_type) + 4);
        
        // 3.9 CounterSize (64-bit)
        uint32_t counter_size = 8;
        counters_buf.insert(counters_buf.end(),
            reinterpret_cast<const uint8_t*>(&counter_size),
            reinterpret_cast<const uint8_t*>(&counter_size) + 4);
        
        // 3.10 CounterOffset
        counters_buf.insert(counters_buf.end(),
            reinterpret_cast<const uint8_t*>(&curr_data_offset),
            reinterpret_cast<const uint8_t*>(&curr_data_offset) + 4);
        
        curr_data_offset += 8;
    }
    // END_BLOCK_GENERATE_COUNTERS
    
    // START_BLOCK_GENERATE_INSTANCES: [Генерация экземпляров и блоков данных]
    std::vector<uint8_t> instances_buf;
    
    if (!instances_list.empty()) {
        // Мультиинстансный объект
        for (const std::string& name : instances_list) {
            // Конвертация имени в UTF-16LE
            std::vector<uint8_t> name_utf16;
            for (char c : name) {
                name_utf16.push_back(static_cast<uint8_t>(c));
                name_utf16.push_back(0);
            }
            name_utf16.push_back(0);
            name_utf16.push_back(0);
            
            uint32_t name_len = static_cast<uint32_t>(name_utf16.size());
            uint32_t name_len_aligned = align_8(name_len);
            uint32_t inst_def_len = PERF_INSTANCE_DEF_HEADER_SIZE + name_len_aligned;
            
            // PERF_INSTANCE_DEFINITION заголовок (4.1 - 4.6)
            // ByteLength, UniqueID, NameOffset, NameLength, ParentObjectInstance, ParentObjectIndex
            uint32_t parent_obj_inst = 0xFFFFFFFF;
            uint32_t name_offset = PERF_INSTANCE_DEF_HEADER_SIZE;
            uint32_t reserved = 0;
            
            instances_buf.insert(instances_buf.end(),
                reinterpret_cast<const uint8_t*>(&inst_def_len),
                reinterpret_cast<const uint8_t*>(&inst_def_len) + 4);
            instances_buf.insert(instances_buf.end(),
                reinterpret_cast<const uint8_t*>(&reserved),
                reinterpret_cast<const uint8_t*>(&reserved) + 4);
            instances_buf.insert(instances_buf.end(),
                reinterpret_cast<const uint8_t*>(&reserved),
                reinterpret_cast<const uint8_t*>(&reserved) + 4);
            instances_buf.insert(instances_buf.end(),
                reinterpret_cast<const uint8_t*>(&parent_obj_inst),
                reinterpret_cast<const uint8_t*>(&parent_obj_inst) + 4);
            instances_buf.insert(instances_buf.end(),
                reinterpret_cast<const uint8_t*>(&name_offset),
                reinterpret_cast<const uint8_t*>(&name_offset) + 4);
            instances_buf.insert(instances_buf.end(),
                reinterpret_cast<const uint8_t*>(&name_len),
                reinterpret_cast<const uint8_t*>(&name_len) + 4);
            
            // Имя + грязный паддинг (4.7)
            instances_buf.insert(instances_buf.end(), name_utf16.begin(), name_utf16.end());
            std::vector<uint8_t> name_padding = get_dirty_padding(name_len_aligned - name_len);
            instances_buf.insert(instances_buf.end(), name_padding.begin(), name_padding.end());
            
            // PERF_COUNTER_BLOCK (выравнивание данных по 8 байт)
            uint32_t block_len = align_8(8 + (counters_count * 8));
            instances_buf.insert(instances_buf.end(),
                reinterpret_cast<const uint8_t*>(&block_len),
                reinterpret_cast<const uint8_t*>(&block_len) + 4);
            
            std::vector<uint8_t> block_padding = get_dirty_padding(block_len - 4);
            instances_buf.insert(instances_buf.end(), block_padding.begin(), block_padding.end());
        }
    } else {
        // Singleton объект (как Memory)
        uint32_t block_len = align_8(8 + (counters_count * 8));
        instances_buf.insert(instances_buf.end(),
            reinterpret_cast<const uint8_t*>(&block_len),
            reinterpret_cast<const uint8_t*>(&block_len) + 4);
        
        std::vector<uint8_t> block_padding = get_dirty_padding(block_len - 4);
        instances_buf.insert(instances_buf.end(), block_padding.begin(), block_padding.end());
    }
    // END_BLOCK_GENERATE_INSTANCES
    
    // START_BLOCK_GENERATE_HEADER: [Генерация заголовка PERF_OBJECT_TYPE]
    uint32_t header_len = PERF_OBJECT_HEADER_SIZE;
    uint32_t def_len = header_len + static_cast<uint32_t>(counters_buf.size());
    uint32_t total_obj_len = def_len + static_cast<uint32_t>(instances_buf.size());
    
    // PERF_OBJECT_TYPE заголовок
    // TotalLength, DefinitionLength, HeaderLength, ObjectNameTitleIndex,
    // ObjectNameTitleIndex, DetailLevel, DefaultCount, NumInstances,
    // CodePage, PerfTime, PerfFreq
    // DefaultCount (список констант: 0, -1)
    static std::vector<int32_t> default_count_list = {0, -1};
    static std::mt19937 count_gen(44); // Детерминированный генератор с фиксированным seed
    static std::uniform_int_distribution<size_t> count_dist(0, default_count_list.size() - 1);
    int32_t default_count = default_count_list[count_dist(count_gen)];
    int32_t num_instances = instances_list.empty() ? -1 : static_cast<int32_t>(instances_list.size());
    uint32_t code_page = 0;
    
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&total_obj_len),
        reinterpret_cast<const uint8_t*>(&total_obj_len) + 4);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&def_len),
        reinterpret_cast<const uint8_t*>(&def_len) + 4);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&header_len),
        reinterpret_cast<const uint8_t*>(&header_len) + 4);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&obj_id),
        reinterpret_cast<const uint8_t*>(&obj_id) + 4);
    uint32_t obj_id_plus1 = obj_id + 1;
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&obj_id_plus1),
        reinterpret_cast<const uint8_t*>(&obj_id_plus1) + 4);
    uint32_t detail_level = 100;
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&detail_level),
        reinterpret_cast<const uint8_t*>(&detail_level) + 4);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&default_count),
        reinterpret_cast<const uint8_t*>(&default_count) + 4);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&num_instances),
        reinterpret_cast<const uint8_t*>(&num_instances) + 4);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&code_page),
        reinterpret_cast<const uint8_t*>(&code_page) + 4);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&perf_time),
        reinterpret_cast<const uint8_t*>(&perf_time) + 8);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&perf_freq),
        reinterpret_cast<const uint8_t*>(&perf_freq) + 8);
    // END_BLOCK_GENERATE_HEADER
    
    // Добавляем счетчики и экземпляры
    result.insert(result.end(), counters_buf.begin(), counters_buf.end());
    result.insert(result.end(), instances_buf.begin(), instances_buf.end());
    
    return result;
}
// END_FUNCTION_generate_single_object

// START_FUNCTION_generate_hkey_performance_data_legacy
// START_CONTRACT:
// PURPOSE: Генерирует полный дамп HKEY_PERFORMANCE_DATA для имитации RegQueryValueEx
// на SATOSHI-PC в диапазоне 09.01.2009 - 20.01.2009. Legacy версия для обратной совместимости.
// INPUTS:
// - [Количество секунд, прошедших с базовой точки] => seconds_passed: int
// OUTPUTS:
// - std::vector<uint8_t> - Полный бинарный буфер PERF_DATA_BLOCK
// KEYWORDS: [DOMAIN(9): Forensics; DOMAIN(8): WindowsPerformance; TECH(7): BinaryStructures; CONCEPT(6): EntropyGeneration]
// END_CONTRACT

std::vector<uint8_t> generate_hkey_performance_data_legacy(int seconds_passed = 0) {
    std::vector<uint8_t> result;
    
    // START_BLOCK_GENERATE_TIME: [Генерация случайного SystemTime в диапазоне 9-20 января 2009]
    static std::random_device rd;
    static std::mt19937 gen(rd());
    static std::uniform_int_distribution<int> day_dist(9, 20);
    static std::uniform_int_distribution<int> hour_dist(0, 23);
    static std::uniform_int_distribution<int> min_dist(0, 59);
    static std::uniform_int_distribution<int> sec_dist(0, 59);
    static std::uniform_int_distribution<int> ms_dist(0, 999);
    
    int random_day = day_dist(gen);
    int random_hour = hour_dist(gen);
    int random_min = min_dist(gen);
    int random_sec = sec_dist(gen);
    int random_ms = ms_dist(gen);
    
    // SYSTEMTIME структура (16 байт)
    // wYear, wMonth, wDayOfWeek, wDay, wHour, wMinute, wSecond, wMilliseconds
    uint16_t st_year = 2009;
    uint16_t st_month = 1;
    uint16_t st_day = static_cast<uint16_t>(random_day);
    
    // Вычисление дня недели (Sunday = 0, Monday = 1...)
    // Для 9 января 2009: пятница = 5
    // Используем простую формулу для диапазона 9-20 января 2009
    int day_of_week = (random_day - 9 + 5) % 7;
    uint16_t st_day_of_week = static_cast<uint16_t>(day_of_week);
    
    uint16_t st_hour = static_cast<uint16_t>(random_hour);
    uint16_t st_minute = static_cast<uint16_t>(random_min);
    uint16_t st_second = static_cast<uint16_t>(random_sec);
    uint16_t st_milliseconds = static_cast<uint16_t>(random_ms);
    // END_BLOCK_GENERATE_TIME
    
    // START_BLOCK_CALCULATE_PERF_TIMERS: [Расчет временных меток производительности]
    uint64_t perf_time = BASE_PERF_TIME + (static_cast<uint64_t>(seconds_passed) * PERF_FREQ);
    uint64_t perf_100ns = BASE_PERF_100NS + (static_cast<uint64_t>(seconds_passed) * 10000000ULL);
    // END_BLOCK_CALCULATE_PERF_TIMERS
    
    // START_BLOCK_GENERATE_SYSTEM_NAME: [Подготовка имени системы в Unicode]
    std::string sys_name_str = "SATOSHI-PC";
    std::vector<uint8_t> sys_name_utf16;
    for (char c : sys_name_str) {
        sys_name_utf16.push_back(static_cast<uint8_t>(c));
        sys_name_utf16.push_back(0);
    }
    sys_name_utf16.push_back(0);
    sys_name_utf16.push_back(0);
    
    uint32_t sys_name_len = static_cast<uint32_t>(sys_name_utf16.size());
    uint32_t sys_name_padded_len = align_8(sys_name_len);
    
    std::vector<uint8_t> sys_name_block = sys_name_utf16;
    std::vector<uint8_t> sys_name_padding = get_dirty_padding(sys_name_padded_len - sys_name_len);
    sys_name_block.insert(sys_name_block.end(), sys_name_padding.begin(), sys_name_padding.end());
    // END_BLOCK_GENERATE_SYSTEM_NAME
    
    // START_BLOCK_GENERATE_OBJECTS: [Генерация всех объектов производительности]
    std::vector<PerfObjectConfig> configs = get_forensic_objects_config();
    std::vector<uint8_t> objects_data;
    
    for (const auto& cfg : configs) {
        std::vector<uint8_t> obj_data = generate_single_object(cfg, perf_time, PERF_FREQ);
        objects_data.insert(objects_data.end(), obj_data.begin(), obj_data.end());
    }
    // END_BLOCK_GENERATE_OBJECTS
    
    // START_BLOCK_GENERATE_HEADER: [Сборка PERF_DATA_BLOCK]
    uint32_t total_len = PERF_DATA_BLOCK_SIZE + static_cast<uint32_t>(sys_name_block.size()) + 
                         static_cast<uint32_t>(objects_data.size());
    
    // PERF_DATA_BLOCK заголовок (1.1 - 1.14)
    // Signature 'PERF' (UTF-16LE), LittleEndian, Version, Revision, TotalLength, 
    // HeaderLength, NumObjectTypes, DefaultObject, SystemTime, PerfTime, PerfFreq,
    // PerfTime100nSec, SystemNameLength, SystemNameOffset
    
    // Signature: 'P\x00E\x00R\x00F\x00'
    uint8_t signature[8] = {'P', 0, 'E', 0, 'R', 0, 'F', 0};
    result.insert(result.end(), signature, signature + 8);
    
    uint32_t little_endian = 1;
    uint32_t version = 1;
    uint32_t revision = 1;
    uint32_t header_length = PERF_DATA_BLOCK_SIZE;
    uint32_t num_object_types = 28;
    uint32_t default_object = 0xFFFFFFFF;
    
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&little_endian),
        reinterpret_cast<const uint8_t*>(&little_endian) + 4);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&version),
        reinterpret_cast<const uint8_t*>(&version) + 4);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&revision),
        reinterpret_cast<const uint8_t*>(&revision) + 4);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&total_len),
        reinterpret_cast<const uint8_t*>(&total_len) + 4);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&header_length),
        reinterpret_cast<const uint8_t*>(&header_length) + 4);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&num_object_types),
        reinterpret_cast<const uint8_t*>(&num_object_types) + 4);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&default_object),
        reinterpret_cast<const uint8_t*>(&default_object) + 4);
    
    // SystemTime (16 байт)
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&st_year),
        reinterpret_cast<const uint8_t*>(&st_year) + 2);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&st_month),
        reinterpret_cast<const uint8_t*>(&st_month) + 2);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&st_day_of_week),
        reinterpret_cast<const uint8_t*>(&st_day_of_week) + 2);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&st_day),
        reinterpret_cast<const uint8_t*>(&st_day) + 2);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&st_hour),
        reinterpret_cast<const uint8_t*>(&st_hour) + 2);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&st_minute),
        reinterpret_cast<const uint8_t*>(&st_minute) + 2);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&st_second),
        reinterpret_cast<const uint8_t*>(&st_second) + 2);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&st_milliseconds),
        reinterpret_cast<const uint8_t*>(&st_milliseconds) + 2);
    
    // PerfTime, PerfFreq, PerfTime100nSec
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&perf_time),
        reinterpret_cast<const uint8_t*>(&perf_time) + 8);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&PERF_FREQ),
        reinterpret_cast<const uint8_t*>(&PERF_FREQ) + 8);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&perf_100ns),
        reinterpret_cast<const uint8_t*>(&perf_100ns) + 8);
    
    // SystemNameLength, SystemNameOffset
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&sys_name_len),
        reinterpret_cast<const uint8_t*>(&sys_name_len) + 4);
    result.insert(result.end(),
        reinterpret_cast<const uint8_t*>(&header_length),
        reinterpret_cast<const uint8_t*>(&header_length) + 4);
    // END_BLOCK_GENERATE_HEADER
    
    // Добавляем имя системы и объекты
    result.insert(result.end(), sys_name_block.begin(), sys_name_block.end());
    result.insert(result.end(), objects_data.begin(), objects_data.end());
    
    return result;
}
// END_FUNCTION_generate_hkey_performance_data_legacy

// START_FUNCTION_generate_hkey_performance_data
// START_CONTRACT:
// PURPOSE: Генерирует полный дамп HKEY_PERFORMANCE_DATA, вычисляет MD5 хеш и вызывает RAND_add()
// для добавления энтропии в PRNG согласно Bitcoin 0.1.0.
// INPUTS:
// - [Количество секунд, прошедших с базовой точки] => seconds_passed: int
// - [Указатель на реализацию RAND_add] => rand_add_impl: RandAddImplementation*
// OUTPUTS:
// - void - Функция не возвращает значение, модифицирует состояние PRNG через RAND_add
// SIDE_EFFECTS:
// - Модифицирует состояние PRNG через rand_add_impl->rand_add()
// - Очищает дамп из памяти после использования (для безопасности)
// TEST_CONDITIONS_SUCCESS_CRITERIA:
// - rand_add_impl не должен быть nullptr
// - Дамп должен быть успешно сгенерирован
// - MD5 хеш должен быть корректно вычислен
// - RAND_add должен быть вызван с корректными параметрами
// LINKS_TO_SPECIFICATION: [PHASE_4_TASKS_4.4-4.5_ARCHITECTURAL_PLAN.md: Задачи 4.6-4.9]
// KEYWORDS: [DOMAIN(9): Forensics; DOMAIN(8): WindowsPerformance; TECH(9): MD5; CONCEPT(9): EntropyEstimation; PATTERN(8): Bitcoin_0.1.0]
// LINKS: [CALLS(9): generate_hkey_performance_data_legacy; USES_API(9): OpenSSL_MD5; CALLS(9): RandAddImplementation.rand_add]
// END_CONTRACT

void generate_hkey_performance_data(int seconds_passed, RandAddImplementation* rand_add_impl) {
    // START_BLOCK_VALIDATE_INPUT: [Проверка входных аргументов на корректность]
    bool input_valid = (rand_add_impl != nullptr);
    if (!input_valid) {
        return;
    }
    // END_BLOCK_VALIDATE_INPUT

    // Начало фазы HKEY
    if (g_entropy_cache && g_entropy_cache->is_active()) {
        g_entropy_cache->begin_phase("HKEY");
    }

    // START_BLOCK_GENERATE_DUMP: [Генерация дампа HKEY_PERFORMANCE_DATA]
    std::vector<uint8_t> dump = generate_hkey_performance_data_legacy(seconds_passed);
    size_t dump_size = dump.size();
    
    // Логирование данных Performance Counter в кеш энтропии
    if (g_entropy_cache && g_entropy_cache->is_active()) {
        g_entropy_cache->log_entropy_source("hkey_performance_counter_data", dump.data(), dump_size);
    }
    // END_BLOCK_GENERATE_DUMP

    // START_BLOCK_COMPUTE_MD5: [Вычисление MD5 хеша полного дампа]
    unsigned char md5_hash[MD5_DIGEST_LENGTH];
    MD5(dump.data(), dump_size, md5_hash);
    
    // Логирование MD5 хеша в кеш энтропии
    if (g_entropy_cache && g_entropy_cache->is_active()) {
        g_entropy_cache->log_entropy_source("hkey_md5_hash", md5_hash, MD5_DIGEST_LENGTH);
    }
    // END_BLOCK_COMPUTE_MD5

    // START_BLOCK_CALCULATE_ENTROPY: [Расчет оценки энтропии по формуле Bitcoin 0.1.0]
    // Формула: min(nSize/500.0, 16.0) где 16.0 = sizeof(MD5 hash) в байтах
    double entropy_estimate = std::min(dump_size / 500.0, 16.0);
    
    // Логирование параметров HKEY в кеш энтропии
    if (g_entropy_cache && g_entropy_cache->is_active()) {
        std::vector<uint8_t> hkey_params;
        // Добавляем seconds_passed (4 байта)
        for (int i = 0; i < 4; ++i) {
            hkey_params.push_back(static_cast<uint8_t>((seconds_passed >> (i * 8)) & 0xFF));
        }
        // Добавляем размер дампа (4 байта)
        for (int i = 0; i < 4; ++i) {
            hkey_params.push_back(static_cast<uint8_t>((dump_size >> (i * 8)) & 0xFF));
        }
        // Добавляем оценку энтропии (8 байт double)
        const uint8_t* entropy_bytes = reinterpret_cast<const uint8_t*>(&entropy_estimate);
        hkey_params.insert(hkey_params.end(), entropy_bytes, entropy_bytes + 8);
        
        g_entropy_cache->log_entropy_source("hkey_parameters", hkey_params.data(), hkey_params.size());
    }
    // END_BLOCK_CALCULATE_ENTROPY

    // START_BLOCK_CALL_RAND_ADD: [Вызов RAND_add с хешем и оценкой энтропии]
    rand_add_impl->rand_add(md5_hash, MD5_DIGEST_LENGTH, entropy_estimate);
    // END_BLOCK_CALL_RAND_ADD

    // START_BLOCK_CLEAR_DUMP: [Очистка дампа из памяти для безопасности]
    std::fill(dump.begin(), dump.end(), 0);
    dump.clear();
    // END_BLOCK_CLEAR_DUMP
    
    // Завершение фазы HKEY
    if (g_entropy_cache && g_entropy_cache->is_active()) {
        g_entropy_cache->end_phase("HKEY");
    }
}
// END_FUNCTION_generate_hkey_performance_data
