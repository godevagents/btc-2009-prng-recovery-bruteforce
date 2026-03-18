// FILE: src/plugins/cpu/bitmap/bitmap_generator.hpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Генерация битмапов для криминалистической энтропии.
// Эмулирует GetBitmapBits для Windows XP SP3 с Gold gradient и MD5 хешированием.
// SCOPE: Генерация 48 блоков видеобуфера 1024x768, MD5 хеширование
// INPUT: uint32_t seed - начальное значение для генератора
// OUTPUT: std::vector<uint8_t> - 768 байт MD5 хешей (48 * 16 байт)
// KEYWORDS: [DOMAIN(10): EntropyGeneration; DOMAIN(9): Graphics; CONCEPT(9): BitmapEmulation; TECH(8): MD5]
// LINKS: [USES(8): getbitmaps.h; USES(7): openssl_md5]
// END_MODULE_CONTRACT

#ifndef BITMAP_GENERATOR_HPP
#define BITMAP_GENERATOR_HPP

#include <vector>
#include <cstdint>
#include <cstring>
#include <algorithm>
#include <openssl/md5.h>

// Константы для генерации битмапов (криминалистические требования)
static constexpr int WIDTH = 1024;
static constexpr int HEIGHT = 768;
static constexpr int BYTES_PER_PIXEL = 3;
static constexpr int STRIDE = WIDTH * BYTES_PER_PIXEL;
static constexpr int BLOCK_HEIGHT = 16;
static constexpr int TOTAL_BLOCKS = 48;
static constexpr int BLOCK_SIZE = WIDTH * BLOCK_HEIGHT * BYTES_PER_PIXEL; // 49152 байт
static constexpr int MD5_HASH_SIZE = 16; // Переименовано чтобы избежать конфликта с OpenSSL
static constexpr int MAX_ENTROPY_SIZE = TOTAL_BLOCKS * MD5_HASH_SIZE; // 768 байт

// Цвета в BGR формате (Windows XP эмуляция)
static constexpr uint8_t XP_BLUE_B = 0xA5;  // B
static constexpr uint8_t XP_BLUE_G = 0x6E;  // G
static constexpr uint8_t XP_BLUE_R = 0x3A;  // R

static constexpr uint8_t WIN_BTNS_B = 0xD8;  // B
static constexpr uint8_t WIN_BTNS_G = 0x81;  // G
static constexpr uint8_t WIN_BTNS_R = 0x00;  // R (заголовок окна)

// Gold gradient в BGR формате
static constexpr uint8_t GOLD_DARK_B = 0x00;  // B = 0x00
static constexpr uint8_t GOLD_DARK_G = 0x70;  // G = 0x70
static constexpr uint8_t GOLD_DARK_R = 0xAA;  // R = 0xAA -> RGB(0xAA, 0x70, 0x00)

static constexpr uint8_t GOLD_LIGHT_B = 0x40;  // B = 0x40
static constexpr uint8_t GOLD_LIGHT_G = 0xDF;  // G = 0xDF
static constexpr uint8_t GOLD_LIGHT_R = 0xFF;  // R = 0xFF -> RGB(0xFF, 0xDF, 0x40)

// START_MODULE_MAP:
// FUNC 10 [Генерирует все 48 блоков битмапов и возвращает MD5 хеши] => generate_bitmap_entropy
// FUNC 9 [Генерирует один блок видеобуфера 1024x16] => generate_block
// FUNC 9 [Вычисляет MD5 хеш блока] => compute_md5
// FUNC 8 [Вычисляет значение пикселя с градиентом] => get_gold_pixel
// FUNC 8 [Вычисляет значение фонового пикселя] => get_xp_background_pixel
// FUNC 7 [Вычисляет значение пикселя окна] => get_window_pixel
// CONST 5 [Ширина буфера] => WIDTH
// CONST 5 [Высота буфера] => HEIGHT
// CONST 5 [Байт на пиксель] => BYTES_PER_PIXEL
// CONST 5 [Количество блоков] => TOTAL_BLOCKS
// CONST 5 [Высота блока] => BLOCK_HEIGHT
// CONST 5 [Размер MD5 в байтах] => MD5_HASH_SIZE
// END_MODULE_MAP

// START_USE_CASES:
// - [generate_bitmap_entropy]: System (EntropyGeneration) -> Generate48Blocks -> MD5HashesReturned
// - [generate_block]: System (BlockGeneration) -> GenerateVideoBuffer -> BlockDataReturned
// - [compute_md5]: System (HashComputation) -> ComputeHash -> HashReturned
// END_USE_CASES

// =============================================================================
// HELPER FUNCTIONS (определяются перед использованием)
// =============================================================================

// START_FUNCTION_get_gold_pixel
// START_CONTRACT:
// PURPOSE: Вычисляет значение пикселя для золотого градиента (Genesis Block).
// INPUTS:
// - x: Координата X => x: int
// - y: Координата Y => y: int
// - b: Ссылка на компонент B => b: uint8_t&
// - g: Ссылка на компонент G => g: uint8_t&
// - r: Ссылка на компонент R => r: uint8_t&
// KEYWORDS: [CONCEPT(7): Gradient; DOMAIN(7): Graphics]
// END_CONTRACT
inline void get_gold_pixel(int x, int y, uint8_t& b, uint8_t& g, uint8_t& r) {
    // Линейная интерполяция между GOLD_DARK и GOLD_LIGHT
    // Диапазон 32x32 пикселя
    int local_x = x - 32;
    int local_y = y - 32;
    int max_val = 62; // 32 + 32 - 2
    
    double t = static_cast<double>(local_x + local_y) / static_cast<double>(max_val);
    t = std::max(0.0, std::min(1.0, t));
    
    b = static_cast<uint8_t>(GOLD_DARK_B + (GOLD_LIGHT_B - GOLD_DARK_B) * t);
    g = static_cast<uint8_t>(GOLD_DARK_G + (GOLD_LIGHT_G - GOLD_DARK_G) * t);
    r = static_cast<uint8_t>(GOLD_DARK_R + (GOLD_LIGHT_R - GOLD_DARK_R) * t);
}
// END_FUNCTION_get_gold_pixel

// START_FUNCTION_get_xp_background_pixel
// START_CONTRACT:
// PURPOSE: Вычисляет значение фонового пикселя Windows XP с шумом.
// INPUTS:
// - x: Координата X => x: int
// - y: Координата Y => y: int
// - seed: Начальное значение для генератора шума => seed: uint32_t
// - b: Ссылка на компонент B => b: uint8_t&
// - g: Ссылка на компонент G => g: uint8_t&
// - r: Ссылка на компонент R => r: uint8_t&
// KEYWORDS: [CONCEPT(7): NoiseGeneration; DOMAIN(7): WindowsXP]
// END_CONTRACT
inline void get_xp_background_pixel(int x, int y, uint32_t seed, uint8_t& b, uint8_t& g, uint8_t& r) {
    // Небольшой шум на фоне
    int noise = ((x ^ y) + static_cast<int>(seed)) % 3;
    
    b = XP_BLUE_B + noise;
    g = XP_BLUE_G;
    r = XP_BLUE_R - noise;
}
// END_FUNCTION_get_xp_background_pixel

// START_FUNCTION_get_window_pixel
// START_CONTRACT:
// PURPOSE: Вычисляет значение пикселя окна приложения.
// INPUTS:
// - x: Координата X => x: int
// - y: Координата Y => y: int
// - b: Ссылка на компонент B => b: uint8_t&
// - g: Ссылка на компонент G => g: uint8_t&
// - r: Ссылка на компонент R => r: uint8_t&
// KEYWORDS: [CONCEPT(6): WindowUI; DOMAIN(6): Emulation]
// END_CONTRACT
inline void get_window_pixel(int x, int y, uint8_t& b, uint8_t& g, uint8_t& r) {
    // Заголовок окна (верхние 25 строк - от 200 до 225)
    if (y < 225) {
        // Заголовок окна - классический стиль
        b = WIN_BTNS_B;
        g = WIN_BTNS_G;
        r = WIN_BTNS_R;
    } else {
        // Тело окна - светло-серый (BGR)
        b = 0xD4;
        g = 0xD0;
        r = 0xC8;
    }
}
// END_FUNCTION_get_window_pixel

// START_FUNCTION_compute_md5
// START_CONTRACT:
// PURPOSE: Вычисляет MD5 хеш блока данных.
// INPUTS:
// - data: Указатель на данные => data: const uint8_t*
// - size: Размер данных в байтах => size: size_t
// OUTPUTS:
// - std::vector<uint8_t>: MD5 хеш (16 байт)
// KEYWORDS: [TECH(9): MD5; CONCEPT(8): HashComputation]
// END_CONTRACT
inline std::vector<uint8_t> compute_md5(const uint8_t* data, size_t size) {
    std::vector<uint8_t> md5_hash(MD5_HASH_SIZE);
    
    MD5(data, size, md5_hash.data());
    
    return md5_hash;
}
// END_FUNCTION_compute_md5

// =============================================================================
// MAIN FUNCTIONS
// =============================================================================

// START_FUNCTION_generate_block
// START_CONTRACT:
// PURPOSE: Генерирует один блок видеобуфера (16 строк x 1024 пикселя x 3 байта).
// INPUTS:
// - block_idx: Индекс блока (0-47) => block_idx: int
// - seed: Начальное значение для генератора => seed: uint32_t
// OUTPUTS:
// - std::vector<uint8_t>: Данные блока (49152 байт)
// KEYWORDS: [DOMAIN(9): VideoBuffer; CONCEPT(8): BlockGeneration]
// END_CONTRACT
inline std::vector<uint8_t> generate_block(int block_idx, uint32_t seed = 0) {
    std::vector<uint8_t> block_data;
    block_data.reserve(BLOCK_SIZE);
    
    int block_y = block_idx * BLOCK_HEIGHT;
    
    // Генерация 16 строк
    for (int y = 0; y < BLOCK_HEIGHT; ++y) {
        int global_y = block_y + y;
        
        // Генерация 1024 пикселей в строке
        for (int x = 0; x < WIDTH; ++x) {
            uint8_t b, g, r;
            
            // Определение типа пикселя
            if (32 <= x && x < 64 && 32 <= global_y && global_y < 64) {
                // Gold gradient - Genesis Block
                get_gold_pixel(x, global_y, b, g, r);
            } else if (300 <= x && x < 724 && 200 <= global_y && global_y < 500) {
                // Окно приложения
                get_window_pixel(x, global_y, b, g, r);
            } else {
                // Фон Windows XP с шумом
                get_xp_background_pixel(x, global_y, seed, b, g, r);
            }
            
            // BGR формат для видеобуфера
            block_data.push_back(b);
            block_data.push_back(g);
            block_data.push_back(r);
        }
    }
    
    return block_data;
}
// END_FUNCTION_generate_block

// START_FUNCTION_generate_bitmap_entropy
// START_CONTRACT:
// PURPOSE: Генерирует 48 блоков видеобуфера и возвращает MD5 хеши.
// INPUTS:
// - seed: Начальное значение для генератора => seed: uint32_t
// OUTPUTS:
// - std::vector<uint8_t>: Вектор MD5 хешей (768 байт)
// SIDE_EFFECTS:
// - Выделяет память для 48 блоков видеобуфера
// TEST_CONDITIONS_SUCCESS_CRITERIA:
// - Возвращает вектор размером 768 байт
// - Каждый блок генерируется корректно
// - MD5 хеши вычисляются правильно
// KEYWORDS: [DOMAIN(10): EntropyGeneration; CONCEPT(9): BitmapEmulation; TECH(8): MD5]
// END_CONTRACT
inline std::vector<uint8_t> generate_bitmap_entropy(uint32_t seed = 0) {
    std::vector<uint8_t> entropy_data;
    entropy_data.reserve(MAX_ENTROPY_SIZE);
    
    // Генерация 48 блоков
    for (int block_idx = 0; block_idx < TOTAL_BLOCKS; ++block_idx) {
        // Генерация данных блока
        std::vector<uint8_t> block_data = generate_block(block_idx, seed);
        
        // Вычисление MD5 хеша
        std::vector<uint8_t> md5_hash = compute_md5(block_data.data(), block_data.size());
        
        // Добавление хеша к результату
        entropy_data.insert(entropy_data.end(), md5_hash.begin(), md5_hash.end());
    }
    
    return entropy_data;
}
// END_FUNCTION_generate_bitmap_entropy

// START_FUNCTION_validate_entropy_size
// START_CONTRACT:
// PURPOSE: Валидирует размер запрашиваемой энтропии.
// INPUTS:
// - size: Размер в байтах => size: size_t
// OUTPUTS:
// - bool: True если размер валиден
// KEYWORDS: [DOMAIN(8): Validation]
// END_CONTRACT
inline bool validate_entropy_size(size_t size) {
    return size >= 1 && size <= MAX_ENTROPY_SIZE;
}
// END_FUNCTION_validate_entropy_size

// START_FUNCTION_get_entropy
// START_CONTRACT:
// PURPOSE: Основная функция для получения энтропии из битмапов.
// INPUTS:
// - size: Требуемый размер энтропии в байтах => size: size_t
// - seed: Начальное значение для генератора => seed: uint32_t
// OUTPUTS:
// - std::vector<uint8_t>: Сгенерированная энтропия
// KEYWORDS: [DOMAIN(10): EntropyGeneration; CONCEPT(9): BitmapEmulation]
// END_CONTRACT
inline std::vector<uint8_t> get_entropy(size_t size, uint32_t seed = 0) {
    // Валидация размера
    if (!validate_entropy_size(size)) {
        return std::vector<uint8_t>();
    }
    
    // Генерация полных данных
    std::vector<uint8_t> full_entropy = generate_bitmap_entropy(seed);
    
    // Возврат запрошенного размера
    return std::vector<uint8_t>(full_entropy.begin(), full_entropy.begin() + size);
}
// END_FUNCTION_get_entropy

#endif // BITMAP_GENERATOR_HPP
