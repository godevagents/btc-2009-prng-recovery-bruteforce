// FILE: src/plugins/cpu/randaddseed/hkey_performance_data.h
// VERSION: 1.1.0
// START_MODULE_CONTRACT:
// PURPOSE: Заголовочный файл для C++ плагина HKEY_PERFORMANCE_DATA.
// SCOPE: Экспорт функций generate_hkey_performance_data_legacy и generate_hkey_performance_data
// для использования в orchestrator и других модулях.
// KEYWORDS: [DOMAIN(9): WindowsPerformance; DOMAIN(8): Forensics; TECH(9): SHA256; TECH(7): BinaryStructures; CONCEPT(9): EntropyEstimation]
// END_MODULE_CONTRACT

#ifndef HKEY_PERFORMANCE_DATA_H
#define HKEY_PERFORMANCE_DATA_H

#include <vector>
#include <cstdint>

// Предварительное объявление для избежания циклической зависимости
class RandAddImplementation;

// START_FUNCTION_generate_hkey_performance_data_legacy
// START_CONTRACT:
// PURPOSE: Генерирует полный дамп HKEY_PERFORMANCE_DATA для имитации RegQueryValueEx.
// Legacy версия для обратной совместимости.
// INPUTS:
// - [Количество секунд, прошедших с базовой точки] => seconds_passed: [int]
// OUTPUTS:
// - std::vector<uint8_t> - Полный бинарный буфер PERF_DATA_BLOCK
// KEYWORDS: [DOMAIN(9): Forensics; DOMAIN(8): WindowsPerformance; TECH(7): BinaryStructures; CONCEPT(6): EntropyGeneration]
// END_CONTRACT

std::vector<uint8_t> generate_hkey_performance_data_legacy(int seconds_passed = 0);
// END_FUNCTION_generate_hkey_performance_data_legacy

// START_FUNCTION_generate_hkey_performance_data
// START_CONTRACT:
// PURPOSE: Генерирует полный дамп HKEY_PERFORMANCE_DATA, вычисляет SHA256 хеш и вызывает RAND_add()
// для добавления энтропии в PRNG согласно Bitcoin 0.1.0.
// INPUTS:
// - [Количество секунд, прошедших с базовой точки] => seconds_passed: [int]
// - [Указатель на реализацию RAND_add] => rand_add_impl: [RandAddImplementation*]
// OUTPUTS:
// - void - Функция не возвращает значение, модифицирует состояние PRNG через RAND_add
// SIDE_EFFECTS:
// - Модифицирует состояние PRNG через rand_add_impl->rand_add()
// - Очищает дамп из памяти после использования (для безопасности)
// KEYWORDS: [DOMAIN(9): Forensics; DOMAIN(8): WindowsPerformance; TECH(9): SHA256; CONCEPT(9): EntropyEstimation; PATTERN(8): Bitcoin_0.1.0]
// LINKS: [CALLS(9): generate_hkey_performance_data_legacy; USES_API(9): OpenSSL_SHA256; CALLS(9): RandAddImplementation.rand_add]
// END_CONTRACT

void generate_hkey_performance_data(int seconds_passed, RandAddImplementation* rand_add_impl);
// END_FUNCTION_generate_hkey_performance_data

#endif // HKEY_PERFORMANCE_DATA_H
