// FILE: src/core/orchestrator.cpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Оркестратор для последовательного выполнения цепочки: poll.cpp -> getbitmaps.cpp -> hkey_performance_data.cpp -> RAND_add.
// SCOPE: Координация работы плагинов CPU/GPU источников энтропии с использованием C++ реализации.
// KEYWORDS: [DOMAIN(9): Workflow; PATTERN(9): Orchestrator; TECH(8): CppIntegration]
// END_MODULE_CONTRACT

#include "orchestrator.h"
#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>

// Включаем заголовки плагинов
#include "../plugins/cpu/rand_poll/poll.h"
#include "../plugins/cpu/bitmap/getbitmaps.h"
#include "../plugins/cpu/randaddseed/hkey_performance_data.h"

// Логирование в стиле проекта
inline void LogToAiState(const std::string& classifier, const std::string& func,
                         const std::string& block, const std::string& op,
                         const std::string& desc, const std::string& status) {
    std::string logLine = "[" + classifier + "][" + func + "][" + block + "][" + op + "] " + desc + " [" + status + "]";
    // Console output removed - logs only to file
    std::ofstream logFile("app.log", std::ios_base::app);
    if (logFile.is_open()) {
        logFile << logLine << std::endl;
    }
}

#define LOG_TRACE(classifier, func, block, op, desc, status) \
    LogToAiState(classifier, func, block, op, desc, status);

// START_METHOD___init__
// START_CONTRACT:
// PURPOSE: Инициализация оркестратора.
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
EntropyXPOrchestrator::EntropyXPOrchestrator()
    : rand_engine(new RandAddImplementation())
{
    LOG_TRACE("SelfCheck", "EntropyXPOrchestrator", "INIT_STATE", "Params", "Orchestrator initialized", "SUCCESS");
}
// END_METHOD___init__

// START_METHOD_run
// START_CONTRACT:
// PURPOSE: Запуск полного цикла: rand_poll -> getbitmaps -> hkey_performance_data -> RAND_add -> финальный state.
// INPUTS:
// - [Seed для детерминированной генерации] => seed: [int32_t]
// OUTPUTS:
// - [std::vector<uint8_t>] - Финальное состояние state[1023].
// KEYWORDS: [PATTERN(10): MainWorkflow; CONCEPT(9): EndToEnd]
// END_CONTRACT

std::vector<uint8_t> EntropyXPOrchestrator::run(int32_t seed) {
    LOG_TRACE("TraceCheck", "EntropyXPOrchestrator", "RUN", "StepStart", "=== НАЧАЛО ПОЛНОГО ЦИКЛА ===", "INFO");
    
    // START_BLOCK_PHASE_1: [Этап 1: RAND_poll (C++ версия).]
    LOG_TRACE("TraceCheck", "EntropyXPOrchestrator", "RUN_POLL", "StepStart", "=== ЭТАП 1: RAND_poll (C++) ===", "INFO");
    std::vector<uint8_t> entropy_stream = _run_poll(seed);
    // END_BLOCK_PHASE_1
    
    // START_BLOCK_PHASE_2: [Этап 2: RAND_add(entropy_stream).]
    LOG_TRACE("TraceCheck", "EntropyXPOrchestrator", "RAND_ADD_POLL", "StepStart", "=== ЭТАП 2: RAND_add(entropy_stream) ===", "INFO");
    rand_engine->process_entropy(entropy_stream, entropy_stream.size() * 0.5);
    // END_BLOCK_PHASE_2
    
    // START_BLOCK_PHASE_3: [Этап 3: GetBitmapBits с MD5 хешированием блоков.]
    LOG_TRACE("TraceCheck", "EntropyXPOrchestrator", "GET_BITMAP", "StepStart", "=== ЭТАП 3: GetBitmapBits (MD5 блоки) ===", "INFO");
    _get_bitmap_stream();
    // END_BLOCK_PHASE_3
    
    // START_BLOCK_PHASE_4: [Этап 4: Пропущен - RAND_add вызывается внутри GetBitmapBits.]
    LOG_TRACE("TraceCheck", "EntropyXPOrchestrator", "RAND_ADD_BITMAP", "StepStart", "=== ЭТАП 4: RAND_add вызывается внутри GetBitmapBits ===", "INFO");
    // RAND_add теперь вызывается внутри GetBitcoinGenesisStream для каждого MD5 хеша блока
    // END_BLOCK_PHASE_4
    
    // START_BLOCK_PHASE_5: [Этап 5: HKEY_PERFORMANCE_DATA.]
    LOG_TRACE("TraceCheck", "EntropyXPOrchestrator", "GET_HKEY", "StepStart", "=== ЭТАП 5: HKEY_PERFORMANCE_DATA ===", "INFO");
    std::vector<uint8_t> hkey_stream = _get_hkey_performance_data(0);
    // END_BLOCK_PHASE_5
    
    // START_BLOCK_PHASE_6: [Этап 6: RAND_add(hkey_stream).]
    LOG_TRACE("TraceCheck", "EntropyXPOrchestrator", "RAND_ADD_HKEY", "StepStart", "=== ЭТАП 6: RAND_add(hkey_stream) ===", "INFO");
    rand_engine->process_entropy(hkey_stream, hkey_stream.size() * 0.3);
    // END_BLOCK_PHASE_6
    
    // START_BLOCK_PHASE_7: [Этап 7: Финальное состояние.]
    std::vector<uint8_t> final_state = rand_engine->get_state();
    
    LOG_TRACE("TraceCheck", "EntropyXPOrchestrator", "GET_FINAL_STATE", "StepStart", "=== ЭТАП 7: ФИНАЛЬНОЕ СОСТОЯНИЕ ===", "INFO");
    LOG_TRACE("VarCheck", "EntropyXPOrchestrator", "GET_FINAL_STATE", "ReturnData", 
              "final_state: " + std::to_string(final_state.size()) + " bytes", "VALUE");
    LOG_TRACE("TraceCheck", "EntropyXPOrchestrator", "RUN", "StepComplete", "=== ЦИКЛ ЗАВЕРШЕН ===", "SUCCESS");
    // END_BLOCK_PHASE_7
    
    return final_state;
}
// END_METHOD_run

// START_METHOD_run_poll_only
// START_CONTRACT:
// PURPOSE: Запуск только RAND_poll этапа.
// INPUTS:
// - [Seed для детерминированной генерации] => seed: [int32_t]
// OUTPUTS:
// - [std::vector<uint8_t>] - Состояние после только poll этапа.
// END_CONTRACT

std::vector<uint8_t> EntropyXPOrchestrator::run_poll_only(int32_t seed) {
    LOG_TRACE("TraceCheck", "EntropyXPOrchestrator", "RUN_POLL_ONLY", "StepStart", "=== ТОЛЬКО RAND_poll ===", "INFO");
    
    std::vector<uint8_t> entropy_stream = _run_poll(seed);
    rand_engine->process_entropy(entropy_stream, entropy_stream.size() * 0.5);
    
    return rand_engine->get_state();
}
// END_METHOD_run_poll_only

// START_METHOD_run_bitmap_only
// START_CONTRACT:
// PURPOSE: Запуск только GetBitmap этапа.
// OUTPUTS:
// - [std::vector<uint8_t>] - Состояние после только bitmap этапа.
// END_CONTRACT

std::vector<uint8_t> EntropyXPOrchestrator::run_bitmap_only() {
    LOG_TRACE("TraceCheck", "EntropyXPOrchestrator", "RUN_BITMAP_ONLY", "StepStart", "=== ТОЛЬКО GetBitmapBits ===", "INFO");
    
    // GetBitcoinGenesisStream теперь вызывает RAND_add внутри себя для каждого MD5 хеша блока
    _get_bitmap_stream();
    
    return rand_engine->get_state();
}
// END_METHOD_run_bitmap_only

// START_METHOD__run_poll
// START_CONTRACT:
// PURPOSE: Внутренний запуск RAND_poll через C++ модуль.
// INPUTS:
// - [Seed для детерминированной генерации] => seed: [int32_t]
// OUTPUTS:
// - [std::vector<uint8_t>] - Entropy stream от RAND_poll.
// END_CONTRACT

std::vector<uint8_t> EntropyXPOrchestrator::_run_poll(int32_t seed) {
    // START_BLOCK_CREATE_POLL_RECONSTRUCTOR: [Создание экземпляра RAND_poll.]
    RandPollReconstructorXP poll_reconstructor(static_cast<uint32_t>(seed));
    // END_BLOCK_CREATE_POLL_RECONSTRUCTOR
    
    // START_BLOCK_EXECUTE_POLL: [Выполнение RAND_poll.]
    std::vector<uint8_t> entropy_stream = poll_reconstructor.execute_poll();
    // END_BLOCK_EXECUTE_POLL
    
    LOG_TRACE("VarCheck", "EntropyXPOrchestrator", "RUN_POLL", "ReturnData", 
              "entropy_stream: " + std::to_string(entropy_stream.size()) + " bytes", "VALUE");
    
    return entropy_stream;
}
// END_METHOD__run_poll

// START_METHOD__get_bitmap_stream
// START_CONTRACT:
// PURPOSE: Генерация видеобуфера с MD5 хешированием блоков и передачей в RAND_add.
// SIDE_EFFECTS:
// - Вызывает GetBitcoinGenesisStream с rand_engine для передачи MD5 хешей.
// END_CONTRACT

void EntropyXPOrchestrator::_get_bitmap_stream() {
    // START_BLOCK_CALL_GETBITMAPS: [Вызов GetBitcoinGenesisStream с rand_engine.]
    GetBitcoinGenesisStream(*rand_engine);
    // END_BLOCK_CALL_GETBITMAPS
    
    LOG_TRACE("TraceCheck", "EntropyXPOrchestrator", "GENERATE_BITMAP", "StepComplete", 
              "Видеобуфер сгенерирован и MD5 хеши переданы в RAND_add", "SUCCESS");
}
// END_METHOD__get_bitmap_stream

// START_METHOD__get_hkey_performance_data
// START_CONTRACT:
// PURPOSE: Получение HKEY_PERFORMANCE_DATA через C++ модуль.
// INPUTS:
// - [Секунды, прошедшие с запуска] => seconds_passed: [int32_t]
// OUTPUTS:
// - [std::vector<uint8_t>] - Сырой бинарный буфер PERF_DATA_BLOCK.
// END_CONTRACT

std::vector<uint8_t> EntropyXPOrchestrator::_get_hkey_performance_data(int32_t seconds_passed) {
    // START_BLOCK_CALL_HKEY: [Вызов generate_hkey_performance_data_legacy.]
    std::vector<uint8_t> stream = generate_hkey_performance_data_legacy(seconds_passed);
    // END_BLOCK_CALL_HKEY
    
    LOG_TRACE("VarCheck", "EntropyXPOrchestrator", "GENERATE_HKEY", "ReturnData", 
              "Сгенерировано " + std::to_string(stream.size()) + " байт", "VALUE");
    
    return stream;
}
// END_METHOD__get_hkey_performance_data
