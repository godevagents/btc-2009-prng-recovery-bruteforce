// FILE: src/core/rand_add.cpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Криминалистическая репликация алгоритма RAND_add() из OpenSSL 0.9.8h (md_rand.c).
// SCOPE: Реализация ssleay_rand_add(), криптографическое смешивание энтропии.
// INPUT: entropy_stream (bytes) от источников энтропии.
// OUTPUT: state[1043] (bytes) - финальное состояние PRNG (STATE_SIZE + MD_DIGEST_LENGTH).
// KEYWORDS: [DOMAIN(10): OpenSSL_Clone; DOMAIN(10): Entropy_Mixing; TECH(6): MD5; CONCEPT(10): PRNG_State]
// LINKS: [IMPLEMENTS(10): md_rand.c:ssleay_rand_add]
// END_MODULE_CONTRACT

#include "rand_add.h"
#include <openssl/md5.h>
#include "entropy_pipeline_cache.hpp"
#include <cstring>
#include <algorithm>
#include <iomanip>
#include <sstream>
#include <memory>

// Global reference to entropy cache (initialized in RAND_poll)
extern std::shared_ptr<EntropyPipelineCache> g_entropy_cache;

// START_METHOD___init__
// START_CONTRACT:
// PURPOSE: Инициализация состояния PRNG согласно md_rand.c.
// KEYWORDS: [CONCEPT(5): Initialization; DOMAIN(5): PRNG]
// END_CONTRACT
RandAddImplementation::RandAddImplementation()
    : state(STATE_BUFFER_SIZE, 0)
    , md(MD_DIGEST_LENGTH, 0)
    , md_count{0, 0}
    , state_index(0)
    , entropy(0.0)
    , initialized(true)  // PRNG инициализирован после создания объекта
    , state_num(0)
{
    // Инициализация согласно md_rand.c
    // state[1043] инициализируется нулями (STATE_SIZE + MD_DIGEST_LENGTH)
    // md[16] инициализируется нулями (MD5)
    // md_count[2] инициализируется нулями
    // initialized = true: конструктор успешно завершен, PRNG готов к использованию
}
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

void RandAddImplementation::rand_add(const uint8_t* buf, size_t num, double add_entropy) {
    std::lock_guard<std::mutex> lock(m_mutex);
    
    if (buf == nullptr || num == 0) {
        return;
    }

    // START_BLOCK_CHECK_INITIALIZED: [Проверка состояния инициализации PRNG.]
    if (!initialized) {
        // Логирование предупреждения о неинициализированном PRNG (аналог OpenSSL поведения)
        // OpenSSL не блокирует работу, но логирует предупреждение в debug режиме
        // Для криминалистической точности логируем событие
        if (g_entropy_cache && g_entropy_cache->is_active()) {
            g_entropy_cache->log_entropy_source("PRNG_NOT_INITIALIZED_WARNING", nullptr, 0);
        }
    }
    // END_BLOCK_CHECK_INITIALIZED

    // START_BLOCK_LOG_INPUT_ENTROPY: [Логирование входных данных энтропии в кеш.]
    // Логирование входных данных энтропии (опционально, проверяется is_active())
    if (g_entropy_cache && g_entropy_cache->is_active()) {
        g_entropy_cache->log_entropy_source("rand_add_input", buf, num);
    }
    // END_BLOCK_LOG_INPUT_ENTROPY

    // START_BLOCK_COPY_LOCAL_STATE: [Копирование локального состояния.]
    // Копирование локального состояния согласно md_rand.c:95-97
    std::array<uint32_t, 2> md_c = md_count;
    std::vector<uint8_t> local_md = md;
    // END_BLOCK_COPY_LOCAL_STATE

    // START_BLOCK_UPDATE_STATE_INDEX: [Обновление индекса состояния.]
    // Обновление индекса состояния согласно md_rand.c:99-106
    size_t old_state_index = state_index;
    state_index += num;

    if (state_index >= STATE_SIZE) {
        state_index %= STATE_SIZE;
        state_num = STATE_SIZE;
    } else if (state_num < STATE_SIZE) {
        if (state_index > state_num) {
            state_num = state_index;
        }
    }
    // END_BLOCK_UPDATE_STATE_INDEX

    // START_BLOCK_UPDATE_MD_COUNT: [Обновление счетчика блоков.]
    // Обновление счетчика блоков согласно md_rand.c:108-110
    size_t blocks_count = (num / MD_DIGEST_LENGTH) + ((num % MD_DIGEST_LENGTH > 0) ? 1 : 0);
    md_c[1] += static_cast<uint32_t>(blocks_count);
    md_count[1] += static_cast<uint32_t>(blocks_count);
    // END_BLOCK_UPDATE_MD_COUNT

    // START_BLOCK_MD5_MIXING_LOOP: [Основной цикл MD5 смешивания.]
    // Основной цикл MD5 смешивания согласно md_rand.c:112-148
    size_t st_idx = old_state_index;
    size_t buf_pos = 0;

    for (size_t i = 0; i < num; i += MD_DIGEST_LENGTH) {
        size_t remaining = num - i;
        size_t j = (remaining >= MD_DIGEST_LENGTH) ? MD_DIGEST_LENGTH : remaining;

        // START_BLOCK_MD5_INIT: [Инициализация MD5 контекста.]
        MD5_CTX sh;
        MD5_Init(&sh);
        // END_BLOCK_MD5_INIT

        // START_BLOCK_MD5_UPDATE_LOCAL_MD: [Обновление MD5 локальным md.]
        MD5_Update(&sh, local_md.data(), MD_DIGEST_LENGTH);
        // END_BLOCK_MD5_UPDATE_LOCAL_MD

        // START_BLOCK_MD5_UPDATE_STATE: [Обновление MD5 состоянием.]
        // Обновление MD5 состоянием согласно md_rand.c:128-133
        int k = static_cast<int>((st_idx + j) - STATE_SIZE);
        if (k > 0) {
            MD5_Update(&sh, state.data() + st_idx, j - k);
            MD5_Update(&sh, state.data(), k);
        } else {
            MD5_Update(&sh, state.data() + st_idx, j);
        }
        // END_BLOCK_MD5_UPDATE_STATE

        // START_BLOCK_MD5_UPDATE_BUF: [Обновление MD5 входным буфером.]
        MD5_Update(&sh, buf + buf_pos, j);
        buf_pos += j;
        // END_BLOCK_MD5_UPDATE_BUF

        // START_BLOCK_MD5_UPDATE_COUNT: [Обновление MD5 счетчиком.]
        // Обновление MD5 счетчиком согласно md_rand.c:139
        uint32_t count_data[2] = {md_c[0], md_c[1]};
        MD5_Update(&sh, count_data, sizeof(count_data));
        // END_BLOCK_MD5_UPDATE_COUNT

        // START_BLOCK_MD5_FINALIZE: [Финализация MD5.]
        unsigned char digest[MD_DIGEST_LENGTH];
        MD5_Final(digest, &sh);
        std::memcpy(local_md.data(), digest, MD_DIGEST_LENGTH);
        // END_BLOCK_MD5_FINALIZE

        // START_BLOCK_INCREMENT_MD_COUNT: [Инкремент счетчика.]
        md_c[1]++;
        // END_BLOCK_INCREMENT_MD_COUNT

        // START_BLOCK_XOR_STATE: [XOR состояния с MD5.]
        // XOR состояния с MD5 согласно md_rand.c:144-148
        for (size_t k_idx = 0; k_idx < j; k_idx++) {
            state[st_idx] ^= local_md[k_idx];
            st_idx++;
            if (st_idx >= STATE_SIZE) {
                st_idx = 0;
            }
        }
        // END_BLOCK_XOR_STATE
    }
    // END_BLOCK_MD5_MIXING_LOOP

    // START_BLOCK_UPDATE_GLOBAL_MD: [Обновление глобального MD через XOR.]
    // Обновление глобального MD через XOR согласно md_rand.c:151-152
    for (size_t k_idx = 0; k_idx < MD_DIGEST_LENGTH; k_idx++) {
        md[k_idx] ^= local_md[k_idx];
    }
    // END_BLOCK_UPDATE_GLOBAL_MD

    // START_BLOCK_UPDATE_ENTROPY: [Обновление энтропии с ограничением.]
    // Обновление энтропии с ограничением согласно md_rand.c:155-156
    // Ограничение: энтропия не накапливается бесконечно, а ограничивается константой ENTROPY_NEEDED
    if (entropy < ENTROPY_NEEDED) {
        entropy += add_entropy;
    }
    // END_BLOCK_UPDATE_ENTROPY

    // START_BLOCK_LOG_MIXING_RESULT: [Логирование результата смешивания в кеш.]
    // Логирование состояния после смешивания (опционально)
    if (g_entropy_cache && g_entropy_cache->is_active()) {
        g_entropy_cache->log_entropy_source("rand_add_mixed", state.data(), std::min(state.size(), static_cast<size_t>(64)));
    }
    // END_BLOCK_LOG_MIXING_RESULT
}
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

void RandAddImplementation::process_entropy(const std::vector<uint8_t>& data, double entropy_estimate) {
    std::lock_guard<std::mutex> lock(m_mutex);
    rand_add(data.data(), data.size(), entropy_estimate);
}
// END_METHOD_process_entropy

// START_METHOD_get_state
// START_CONTRACT:
// PURPOSE: Возврат финального состояния state[1043].
// OUTPUTS:
// - [std::vector<uint8_t>] - Копия буфера state[1043].
// KEYWORDS: [PATTERN(5): Getter; DOMAIN(5): State]
// END_CONTRACT

std::vector<uint8_t> RandAddImplementation::get_state() const {
    std::lock_guard<std::mutex> lock(m_mutex);
    return state;
}
// END_METHOD_get_state

// START_METHOD_get_state_hex
// START_CONTRACT:
// PURPOSE: Возврат state[1043] в hex формате для отладки.
// OUTPUTS:
// - [std::string] - Hex строка.
// END_CONTRACT

std::string RandAddImplementation::get_state_hex() const {
    std::lock_guard<std::mutex> lock(m_mutex);
    std::stringstream ss;
    ss << std::hex << std::setfill('0');
    for (uint8_t byte : state) {
        ss << std::setw(2) << static_cast<int>(byte);
    }
    return ss.str();
}
// END_METHOD_get_state_hex

// START_METHOD_lock
// START_CONTRACT:
// PURPOSE: Блокировка мьютекса для совместимости с OpenSSL API (аналог CRYPTO_LOCK_RAND).
// KEYWORDS: [PATTERN(8): OpenSSL_API; CONCEPT(7): Mutex]
// END_CONTRACT

void RandAddImplementation::lock() const {
    m_mutex.lock();
}
// END_METHOD_lock

// START_METHOD_unlock
// START_CONTRACT:
// PURPOSE: Разблокировка мьютекса для совместимости с OpenSSL API.
// KEYWORDS: [PATTERN(8): OpenSSL_API; CONCEPT(7): Mutex]
// END_CONTRACT

void RandAddImplementation::unlock() const {
    m_mutex.unlock();
}
// END_METHOD_unlock

// START_METHOD_is_initialized
// START_CONTRACT:
// PURPOSE: Проверка состояния инициализации PRNG (потокобезопасная).
// OUTPUTS:
// - [bool] - true если PRNG инициализирован.
// KEYWORDS: [PATTERN(5): Getter; DOMAIN(5): State; CONCEPT(7): ThreadSafe]
// END_CONTRACT

bool RandAddImplementation::is_initialized() const {
    std::lock_guard<std::mutex> lock(m_mutex);
    return initialized;
}
// END_METHOD_is_initialized
