# FILE: wrapper/core/__init__.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Инициализация модуля wrapper.core с экспортом базовых классов и исключений.
# SCOPE: Python-обёртка, базовые классы, исключения
# INPUT: Нет
# OUTPUT: Экспортируемые классы: EntropySource, EntropySourceError, ModuleLoadError, DataValidationError, EntropyGenerationError, EntropyLogger
# KEYWORDS: [DOMAIN(9): PythonWrapper; CONCEPT(6): InitModule]
# LINKS: [USES(8): wrapper.core.base; USES(8): wrapper.core.exceptions; USES(8): wrapper.core.logger]
# LINKS_TO_SPECIFICATION: ["Задача: Реализация Этапа 1 — Базовая инфраструктура Python-обёртки"]
# END_MODULE_CONTRACT

"""
Модуль wrapper.core - базовые компоненты Python-обёртки.

Экспортирует:
    EntropySource: Абстрактный базовый класс для источников энтропии.
    EntropySourceError: Базовый класс исключений.
    ModuleLoadError: Исключение при ошибке загрузки модуля.
    DataValidationError: Исключение при ошибке валидации.
    EntropyGenerationError: Исключение при ошибке генерации энтропии.
    EntropyLogger: Класс для логирования.
    get_logger: Функция для получения логгера.
"""

from src.wrapper.core.base import EntropySource
from src.wrapper.core.exceptions import (
    EntropySourceError,
    ModuleLoadError,
    DataValidationError,
    EntropyGenerationError,
)
from src.wrapper.core.logger import EntropyLogger, get_logger, setup_logger

__all__ = [
    "EntropySource",
    "EntropySourceError",
    "ModuleLoadError",
    "DataValidationError",
    "EntropyGenerationError",
    "EntropyLogger",
    "get_logger",
    "setup_logger",
]
