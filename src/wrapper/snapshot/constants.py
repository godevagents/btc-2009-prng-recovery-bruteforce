# FILE: wrapper/snapshot/constants.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Константы для работы со снапшотами энтропии.
# SCOPE: Константы размеров, версии формата, магические числа
# INPUT: Нет
# OUTPUT: Константы для модуля snapshot
# KEYWORDS: [DOMAIN(9): Constants; CONCEPT(7): Configuration; TECH(5): Size]
# LINKS: [FROM(10): src.core.rand_add.h]
# END_MODULE_CONTRACT

"""
Константы для модуля снапшотов энтропии.

Значения соответствуют спецификации OpenSSL 0.9.8h (md_rand.c) и
определениям из src/core/rand_add.h.
"""

# START_BLOCK_SIZE_CONSTANTS: [Константы размеров из rand_add.h]
# Константы соответствуют OpenSSL 0.9.8h (SHA-1 по умолчанию):
# - STATE_SIZE = 1023: reference/openssl/OpenSSL_098h/crypto/rand/md_rand.c:136
# - USE_SHA1_RAND по умолчанию: reference/openssl/OpenSSL_098h/crypto/rand/rand_lcl.h:118-120
# - MD_DIGEST_LENGTH = SHA_DIGEST_LENGTH = 20: reference/openssl/OpenSSL_098h/crypto/rand/rand_lcl.h:142
# - STATE_BUFFER_SIZE = 1043: reference/openssl/OpenSSL_098h/crypto/rand/md_rand.c:138

# Размер кольцевого буфера PRNG (соответствует STATE_SIZE в rand_add.h)
STATE_SIZE: int = 1023

# Размер SHA-1 дайджеста (соответствует MD_DIGEST_LENGTH в rand_add.h)
# OpenSSL 0.9.8h по умолчанию использует SHA-1 для PRNG
MD_DIGEST_LENGTH: int = 20

# Полный размер буфера состояния: STATE_SIZE + MD_DIGEST_LENGTH
# state[1023] + sha1[20] = 1043 байт
STATE_BUFFER_SIZE: int = STATE_SIZE + MD_DIGEST_LENGTH
# END_BLOCK_SIZE_CONSTANTS

# START_BLOCK_VERSION_CONSTANTS: [Константы версии формата]
# Версия формата снапшота
SNAPSHOT_VERSION: str = "1.0.0"

# Магическое число для бинарного формата
SNAPSHOT_MAGIC: bytes = b"SNAP"

# Версия бинарного формата (0x0100 = 1.0)
SNAPSHOT_BINARY_VERSION: int = 0x0100
# END_BLOCK_VERSION_CONSTANTS

# START_BLOCK_HASH_ALGORITHMS: [Константы алгоритмов хеширования]
# Поддерживаемые алгоритмы хеширования фаз
HASH_ALGORITHM_NONE: str = "None"
HASH_ALGORITHM_MD5: str = "MD5"
HASH_ALGORITHM_SHA1: str = "SHA1"
HASH_ALGORITHM_SHA256: str = "SHA256"

# Список поддерживаемых алгоритмов
SUPPORTED_HASH_ALGORITHMS: list = [
    HASH_ALGORITHM_NONE,
    HASH_ALGORITHM_MD5,
    HASH_ALGORITHM_SHA1,
    HASH_ALGORITHM_SHA256
]

# Размеры хешей для каждого алгоритма
HASH_SIZES: dict = {
    HASH_ALGORITHM_NONE: 0,
    HASH_ALGORITHM_MD5: 16,
    HASH_ALGORITHM_SHA1: 20,
    HASH_ALGORITHM_SHA256: 32
}
# END_BLOCK_HASH_ALGORITHMS

# START_BLOCK_PHASE_DEFAULTS: [Константы фаз энтропии]
# Имена фаз энтропийного пайплайна
PHASE_RAND_POLL: str = "RAND_poll"
PHASE_GET_BITMAP_BITS: str = "GetBitmapBits"
PHASE_HKEY_PERFORMANCE: str = "HKEY_PERFORMANCE_DATA"
PHASE_QPC: str = "QueryPerformanceCounter"

# Имена источников в EntropyEngine
SOURCE_RAND_POLL: str = "RandPollSource"
SOURCE_GET_BITMAPS: str = "GetBitmapsSource"
SOURCE_HKEY: str = "HKeyPerformanceSource"
SOURCE_QPC: str = "QPCSource"

# Словарь соответствия фаз и источников
PHASE_TO_SOURCE: dict = {
    PHASE_RAND_POLL: SOURCE_RAND_POLL,
    PHASE_GET_BITMAP_BITS: SOURCE_GET_BITMAPS,
    PHASE_HKEY_PERFORMANCE: SOURCE_HKEY,
    PHASE_QPC: SOURCE_QPC
}

# Словарь соответствия фаз и алгоритмов хеширования
PHASE_TO_HASH: dict = {
    PHASE_RAND_POLL: HASH_ALGORITHM_NONE,
    PHASE_GET_BITMAP_BITS: HASH_ALGORITHM_MD5,
    PHASE_HKEY_PERFORMANCE: HASH_ALGORITHM_MD5,
    PHASE_QPC: HASH_ALGORITHM_SHA256
}

# Размеры данных по умолчанию для каждой фазы
PHASE_DEFAULT_SIZES: dict = {
    PHASE_RAND_POLL: 1024,
    PHASE_GET_BITMAP_BITS: 768,
    PHASE_HKEY_PERFORMANCE: 4096,
    PHASE_QPC: 8
}
# END_BLOCK_PHASE_DEFAULTS
