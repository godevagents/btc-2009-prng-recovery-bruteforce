// FILE: src/plugins/cpu/randaddseed/QueryPerformanceCounter.h
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Генерация значений QueryPerformanceCounter для имитации поведения Windows XP SP3
// на Intel Core 2 Quad Q6600. Модуль предоставляет функцию для генерации случайных значений
// в диапазоне, соответствующем реальным значениям счетчика производительности Windows.
// SCOPE: Генерация случайных значений LARGE_INTEGER в заданном диапазоне, добавление
// энтропии в PRNG через RAND_add() согласно Bitcoin 0.1.0.
// INPUT: rand_add_impl (RandAddImplementation*) - указатель на реализацию RAND_add.
// OUTPUT: void - модификация состояния PRNG через RAND_add.
// KEYWORDS: [DOMAIN(9): WindowsPerformance; DOMAIN(8): Forensics; TECH(7): RandomGeneration; CONCEPT(9): EntropyEstimation; PATTERN(8): Bitcoin_0.1.0]
// LINKS: [READS_DATA_FROM(6): rand_poll_constants.txt; CALLS(9): RandAddImplementation.rand_add]
// END_MODULE_CONTRACT
// START_MODULE_MAP:
// FUNC 9 [Генерирует случайное значение QueryPerformanceCounter и добавляет в PRNG] => generate_query_performance_counter
// CONST 8 [Минимальное значение QueryPerformanceCounter] => QPC_MIN_VALUE
// CONST 8 [Максимальное значение QueryPerformanceCounter] => QPC_MAX_VALUE
// END_MODULE_MAP
// START_USE_CASES:
// - [generate_query_performance_counter]: BitcoinCore (Startup) -> AddEntropyFromPerformanceCounter -> PRNGStateUpdated
// END_USE_CASES

#ifndef QUERY_PERFORMANCE_COUNTER_H
#define QUERY_PERFORMANCE_COUNTER_H

#include <cstdint>
#include "rand_add.h"

// START_CONSTANTS
// Диапазон QueryPerformanceCounter из rand_poll_constants.txt
// E4 35 01 C0 00 00 00 00 — A8 42 10 00 09 00 00 00 (little-endian)
constexpr uint64_t QPC_MIN_VALUE = 0x00000000C00135E4ULL; // 3221225476
constexpr uint64_t QPC_MAX_VALUE = 0x00000009100042A8ULL; // 38654705704
// END_CONSTANTS

// START_FUNCTION_generate_query_performance_counter
// START_CONTRACT:
// PURPOSE: Генерирует случайное значение QueryPerformanceCounter в заданном диапазоне,
// вычисляет SHA256 хеш и вызывает RAND_add() для добавления энтропии в PRNG.
// INPUTS:
// - [Указатель на реализацию RAND_add] => rand_add_impl: RandAddImplementation*
// OUTPUTS:
// - void - Функция не возвращает значение, модифицирует состояние PRNG через RAND_add
// SIDE_EFFECTS:
// - Модифицирует состояние PRNG через rand_add_impl->rand_add()
// TEST_CONDITIONS_SUCCESS_CRITERIA:
// - rand_add_impl не должен быть nullptr
// - Сгенерированное значение должно быть в диапазоне [QPC_MIN_VALUE, QPC_MAX_VALUE]
// - SHA256 хеш должен быть корректно вычислен
// - RAND_add должен быть вызван с корректными параметрами
// LINKS_TO_SPECIFICATION: [rand_poll_constants.txt: QueryPerformanceCounter]
// KEYWORDS: [DOMAIN(9): WindowsPerformance; TECH(9): SHA256; CONCEPT(9): EntropyEstimation; PATTERN(8): Bitcoin_0.1.0]
// LINKS: [USES_API(9): OpenSSL_SHA256; CALLS(9): RandAddImplementation.rand_add]
// END_CONTRACT

void generate_query_performance_counter(RandAddImplementation* rand_add_impl);
// END_FUNCTION_generate_query_performance_counter

#endif // QUERY_PERFORMANCE_COUNTER_H
