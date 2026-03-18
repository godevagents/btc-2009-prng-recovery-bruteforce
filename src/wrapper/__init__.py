# FILE: wrapper/__init__.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Точка входа в Python-обёртку для генерации энтропии.
# Экспортирует основные классы для удобного использования.
# SCOPE: Python-обёртка, унифицированный интерфейс
# INPUT: Нет
# OUTPUT: Основные классы: EntropySource, EntropyLogger, исключения
# KEYWORDS: [DOMAIN(9): PythonWrapper; CONCEPT(7): Facade; TECH(5): API]
# LINKS: [USES(8): wrapper.core; USES(7): wrapper.entropy]
# LINKS_TO_SPECIFICATION: ["Задача: Реализация Этапа 1 — Базовая инфраструктура Python-обёртки"]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# MODULE 10 [Точка входа в обёртку] => wrapper
# END_MODULE_MAP
# START_USE_CASES:
# - [import src.wrapper]: Developer (Use) -> ImportModule -> AccessToClasses
# - [EntropySource]: User (GenerateEntropy) -> CreateSource -> EntropyAvailable
# - [EntropyLogger]: System (Logging) -> GetLogger -> LoggingReady
# END_USE_CASES
"""
Python-обёртка для C++ модулей генерации энтропии.

Модуль предоставляет унифицированный интерфейс для работы с C++ модулями:
- rand_poll_cpp: Сбор энтропии через системные вызовы
- getbitmaps_cpp: Генерация битмапов для Bitcoin
- hkey_performance_data_cpp: Генерация данных о производительности

Основные классы:
    EntropySource: Абстрактный базовый класс для источников энтропии.
    EntropyLogger: Класс для логирования с форматом проекта.

Исключения:
    EntropySourceError: Базовый класс исключений.
    ModuleLoadError: Ошибка загрузки модуля.
    DataValidationError: Ошибка валидации данных.
    EntropyGenerationError: Ошибка генерации энтропии.

Пример использования:
    from src.wrapper import EntropySource, EntropyLogger

    logger = EntropyLogger("MyModule")
    logger.info("SelfCheck", "main", "Start", "Запуск приложения", "INFO")

    source = EntropySource(module_path="rand_poll_cpp.so")
    if source.is_available():
        entropy = source.get_entropy(32)
"""

from src.wrapper.core import (
    EntropySource,
    EntropySourceError,
    ModuleLoadError,
    DataValidationError,
    EntropyGenerationError,
    EntropyLogger,
    get_logger,
    setup_logger,
)

from src.wrapper.unified_interface import UnifiedEntropyInterface

__version__ = "1.0.0"

__all__ = [
    "EntropySource",
    "EntropySourceError",
    "ModuleLoadError",
    "DataValidationError",
    "EntropyGenerationError",
    "EntropyLogger",
    "get_logger",
    "setup_logger",
    "UnifiedEntropyInterface",
    "__version__",
]
