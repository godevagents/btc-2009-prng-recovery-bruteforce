# FILE: wrapper/entropy/__init__.py
# VERSION: 2.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Инициализация модуля wrapper.entropy для источников энтропии с поддержкой C++ биндингов.
# SCOPE: Источники энтропии, движок энтропии, C++ интеграция
# INPUT: Нет
# OUTPUT: Модуль для работы с источниками энтропии
# KEYWORDS: [DOMAIN(9): EntropyGeneration; CONCEPT(6): InitModule; CONCEPT(5): CppBinding]
# LINKS: [USES(8): wrapper.core]
# LINKS_TO_SPECIFICATION: ["Задача: Python/C++ API Интеграция EntropyEngine"]
# END_MODULE_CONTRACT

"""
Модуль wrapper.entropy - источники энтропии и движок с поддержкой C++ биндингов.

Этот модуль содержит:
    rand_poll_source.py: Обёртка для rand_poll_cpp с Python fallback
    getbitmaps_source.py: Обёртка для getbitmaps_cpp с Python fallback
    hkey_source.py: Обёртка для hkey_performance_data_cpp с Python fallback
    entropy_engine.py: Координация источников энтропии с C++ биндингами

Основные классы:
    EntropyEngine: Координатор источников с поддержкой C++ биндингов
    RandPollSource: Источник энтропии RAND_poll
    GetBitmapsSource: Источник энтропии из битмапов
    HKeyPerformanceSource: Источник энтропии из HKEY_PERFORMANCE_DATA

Константы типов источников:
    SOURCE_RAND_POLL = "rand_poll"
    SOURCE_BITMAP = "bitmap"
    SOURCE_HKEY = "hkey"
    SOURCE_FULL = "full"

Пример использования:
    from src.wrapper.entropy import EntropyEngine, SOURCE_RAND_POLL
    
    engine = EntropyEngine(seed=12345)
    
    # Получить энтропию от источника
    entropy = engine.get_entropy(SOURCE_RAND_POLL)
    
    # Получить полную энтропию
    full_entropy = engine.generate_full_entropy()
    
    # Получить fallback данные
    fallback = engine.get_fallback_data(SOURCE_RAND_POLL)
"""

from src.wrapper.entropy.entropy_engine import (
    EntropyEngine,
    SOURCE_RAND_POLL,
    SOURCE_BITMAP,
    SOURCE_HKEY,
    SOURCE_FULL,
    STRATEGY_XOR,
    STRATEGY_HASH,
    SUPPORTED_SOURCES,
    SUPPORTED_STRATEGIES,
)

from src.wrapper.entropy.rand_poll_source import RandPollSource

from src.wrapper.entropy.getbitmaps_source import GetBitmapsSource

from src.wrapper.entropy.hkey_source import HKeyPerformanceSource

__all__ = [
    # Главный класс
    "EntropyEngine",
    
    # Константы типов источников
    "SOURCE_RAND_POLL",
    "SOURCE_BITMAP", 
    "SOURCE_HKEY",
    "SOURCE_FULL",
    
    # Константы стратегий
    "STRATEGY_XOR",
    "STRATEGY_HASH",
    
    # Списки поддерживаемых значений
    "SUPPORTED_SOURCES",
    "SUPPORTED_STRATEGIES",
    
    # Классы источников
    "RandPollSource",
    "GetBitmapsSource",
    "HKeyPerformanceSource",
]
