// FILE: src/core/rand_add.h
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Криминалистическая репликация алгоритма RAND_add() из OpenSSL 0.9.8h (md_rand.c).
// SCOPE: Реализация ssleay_rand_add(), криптографическое смешивание энтропии.
// INPUT: entropy_stream (bytes) от источников энтропии.
// OUTPUT: state[1043] (bytes) - финальное состояние PRNG (STATE_SIZE + MD_DIGEST_LENGTH).
// KEYWORDS: [DOMAIN(10): OpenSSL_Clone; DOMAIN(10): Entropy_Mixing; TECH(6): MD5; CONCEPT(10): PRNG_State]
// LINKS: [IMPLEMENTS(10): md_rand.c:ssleay_rand_add]
// END_MODULE_CONTRACT

#ifndef RAND_ADD_H
#define RAND_ADD_H

#include <vector>
#include <cstdint>
#include <string>
#include <array>
#include <mutex>
#include <openssl/md5.h>

// START_CONSTANTS
// OpenSSL 0.9.8h использует MD5 для PRNG (в соответствии с forensic_compliance):
// - STATE_SIZE = 1023: reference/openssl/OpenSSL_098h/crypto/rand/md_rand.c:136
// - MD5_DIGEST_LENGTH = 16: reference/openssl/OpenSSL_098h/crypto/md5/md5.h
// - MD_DIGEST_LENGTH = 16: reference/openssl/OpenSSL_098h/crypto/rand/rand_lcl.h:142
// - STATE_BUFFER_SIZE = 1043: reference/openssl/OpenSSL_098h/crypto/rand/md_rand.c:138
constexpr size_t STATE_SIZE = 1023;
constexpr size_t MD_DIGEST_LENGTH = 16;  // MD5 (16 байт)
constexpr size_t STATE_BUFFER_SIZE = STATE_SIZE + MD_DIGEST_LENGTH;  // 1043 байт для соответствия OpenSSL 0.9.8h

// Константа ограничения накопления энтропии (32 байта = 256 бит)
// Соответствует ENTROPY_NEEDED в OpenSSL 0.9.8h: reference/openssl/OpenSSL_098h/crypto/rand/rand_lcl.h
constexpr double ENTROPY_NEEDED = 32.0;
// END_CONSTANTS

// START_CLASS_RandAddImplementation
// START_CONTRACT:
// PURPOSE: Криминалистическая репликация ssleay_rand_add() из md_rand.c:81-205.
// ATTRIBUTES:
// - [Буфер состояния PRNG 1043 байт (STATE_SIZE + MD_DIGEST_LENGTH)] => state: [std::vector<uint8_t>]
// - [MD5 аккумулятор 16 байт] => md: [std::vector<uint8_t>]
// - [Счетчики блоков md_count[2]] => md_count: [std::array<uint32_t, 2>]
// - [Индекс записи в state环形 буфер] => state_index: [size_t]
// - [Накопленная энтропия] => entropy: [double]
// - [Флаг инициализации] => initialized: [bool]
// METHODS:
// - [Основной метод добавления энтропии - точная копия ssleay_rand_add] => rand_add(buf, num, add_entropy)
// - [Обработка входного потока] => process_entropy(data)
// - [Получение финального state] => get_state()
// KEYWORDS: [PATTERN(10): ExactClone; DOMAIN(10): OpenSSL_Internal; TECH(6): MD5]
// LINKS: [IMPLEMENTS(10): md_rand.c:ssleay_rand_add; USES(8): OpenSSL_MD5]
// END_CONTRACT

class RandAddImplementation {
public:
    // START_METHOD___init__
    // START_CONTRACT:
    // PURPOSE: Инициализация состояния PRNG согласно md_rand.c.
    // KEYWORDS: [CONCEPT(5): Initialization; DOMAIN(5): PRNG]
    // END_CONTRACT
    RandAddImplementation();
    // END_METHOD___init__

    // START_METHOD_rand_add
    // START_CONTRACT:
    // PURPOSE: Криминалистическая репликация ssleay_rand_add() из md_rand.c:81-205.
    // INPUTS:
    // - [Буфер данных для добавления] => buf: [const uint8_t*]
    // - [Размер буфера в байтах] => num: [size_t]
    // - [Оценка энтропии бит] => add_entropy: [double]
    // OUTPUTS:
    // - [None] - Модифицирует внутреннее состояние state.
    // SIDE_EFFECTS:
    // - Модифицирует this->state (环形 буфер 1043 байт)
    // - Обновляет this->md и this->md_count
    // KEYWORDS: [PATTERN(10): ExactReplica; DOMAIN(10): EntropyMixing; TECH(6): MD5]
    // LINKS: [IMPLEMENTS(10): md_rand.c:ssleay_rand_add; USES(8): OpenSSL_MD5]
    // END_CONTRACT
    void rand_add(const uint8_t* buf, size_t num, double add_entropy);
    // END_METHOD_rand_add

    // START_METHOD_process_entropy
    // START_CONTRACT:
    // PURPOSE: Удобный метод для обработки потока энтропии.
    // INPUTS:
    // - [Поток данных для обработки] => data: [const std::vector<uint8_t>&]
    // - [Оценка энтропии бит] => entropy_estimate: [double]
    // OUTPUTS:
    // - [None] - Модифицирует внутреннее состояние.
    // KEYWORDS: [PATTERN(7): Wrapper; DOMAIN(8): API]
    // END_CONTRACT
    void process_entropy(const std::vector<uint8_t>& data, double entropy_estimate = 0.0);
    // END_METHOD_process_entropy

    // START_METHOD_get_state
    // START_CONTRACT:
    // PURPOSE: Возврат финального состояния state[1043].
    // OUTPUTS:
    // - [std::vector<uint8_t>] - Копия буфера state[1043].
    // KEYWORDS: [PATTERN(5): Getter; DOMAIN(5): State]
    // END_CONTRACT
    std::vector<uint8_t> get_state() const;
    // END_METHOD_get_state

    // START_METHOD_get_state_hex
    // START_CONTRACT:
    // PURPOSE: Возврат state[1043] в hex формате для отладки.
    // OUTPUTS:
    // - [std::string] - Hex строка.
    // END_CONTRACT
    std::string get_state_hex() const;
    // END_METHOD_get_state_hex

    // START_METHOD_lock
    // START_CONTRACT:
    // PURPOSE: Блокировка мьютекса для совместимости с OpenSSL API (аналог CRYPTO_LOCK_RAND).
    // KEYWORDS: [PATTERN(8): OpenSSL_API; CONCEPT(7): Mutex]
    // END_CONTRACT
    void lock() const;
    // END_METHOD_lock

    // START_METHOD_unlock
    // START_CONTRACT:
    // PURPOSE: Разблокировка мьютекса для совместимости с OpenSSL API.
    // KEYWORDS: [PATTERN(8): OpenSSL_API; CONCEPT(7): Mutex]
    // END_CONTRACT
    void unlock() const;
    // END_METHOD_unlock

    // START_METHOD_is_initialized
    // START_CONTRACT:
    // PURPOSE: Проверка состояния инициализации PRNG (потокобезопасная).
    // OUTPUTS:
    // - [bool] - true если PRNG инициализирован.
    // KEYWORDS: [PATTERN(5): Getter; DOMAIN(5): State; CONCEPT(7): ThreadSafe]
    // END_CONTRACT
    bool is_initialized() const;
    // END_METHOD_is_initialized

private:
    // Атрибуты класса
    mutable std::mutex m_mutex;
    std::vector<uint8_t> state;
    std::vector<uint8_t> md;
    std::array<uint32_t, 2> md_count;
    size_t state_index;
    double entropy;
    bool initialized;
    size_t state_num;
};

// END_CLASS_RandAddImplementation

#endif // RAND_ADD_H
