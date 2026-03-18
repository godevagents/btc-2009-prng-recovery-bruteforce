// FILE: src/plugins/cpu/bitmap/getbitmaps.h
// VERSION: 1.1.0
// START_MODULE_CONTRACT:
// PURPOSE: Заголовочный файл для C++ плагина GetBitmapBits.
// SCOPE: Экспорт функции GetBitcoinGenesisStream для использования в orchestrator.
// KEYWORDS: [DOMAIN(9): Graphics; DOMAIN(8): MemoryEmulation; CONCEPT(9): BitcoinGenesis]
// END_MODULE_CONTRACT

#ifndef GETBITMAPS_H
#define GETBITMAPS_H

#include <vector>
#include <cstdint>
#include "bitmap_generator.hpp"

// Forward declaration
class RandAddImplementation;

// START_FUNCTION_GetBitcoinGenesisStream
// START_CONTRACT:
// PURPOSE: Формирует массив байтов, представляющий снимок экрана, и передает MD5 хеши блоков в RAND_add.
// INPUTS:
// - [Ссылка на реализацию RAND_add] => rand_add_impl: [RandAddImplementation&]
// OUTPUTS:
// - void - Функция не возвращает данные, а передает их через RAND_add.
// SIDE_EFFECTS:
// - Вызывает rand_add_impl.rand_add() для каждого блока видеобуфера.
// KEYWORDS: [PATTERN(7): Generator; DOMAIN(9): VideoBuffer; TECH(9): MD5; DOMAIN(10): EntropyMixing]
// END_CONTRACT

void GetBitcoinGenesisStream(RandAddImplementation& rand_add_impl);
// END_FUNCTION_GetBitcoinGenesisStream

// START_FUNCTION_GetBitmapEntropyDirect
// START_CONTRACT:
// PURPOSE: Прямая генерация энтропии из битмапов без использования RandAddImplementation.
// INPUTS:
// - seed: Начальное значение для генератора => seed: uint32_t
// OUTPUTS:
// - std::vector<uint8_t>: Вектор MD5 хешей (768 байт)
// KEYWORDS: [DOMAIN(10): EntropyGeneration; CONCEPT(9): BitmapEmulation]
// END_CONTRACT

inline std::vector<uint8_t> GetBitmapEntropyDirect(uint32_t seed = 0) {
    return generate_bitmap_entropy(seed);
}
// END_FUNCTION_GetBitmapEntropyDirect

#endif // GETBITMAPS_H
