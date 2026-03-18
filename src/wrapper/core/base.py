# FILE: wrapper/core/base.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Определяет базовые классы для источников энтропии в Python-обёртке.
# Предоставляет абстрактный базовый класс EntropySource с методами загрузки .so модулей
# и интерфейсом для получения энтропии.
# SCOPE: Управление модулями, интерфейс источников энтропии
# INPUT: Нет (модуль предоставляет классы)
# OUTPUT: Базовые классы: EntropySource
# KEYWORDS: [DOMAIN(9): EntropySource; CONCEPT(8): AbstractBaseClass; TECH(6): ctypes]
# LINKS: [USES(8): wrapper.core.exceptions; USES(7): wrapper.core.logger]
# LINKS_TO_SPECIFICATION: ["Задача: Реализация Этапа 1 — Базовая инфраструктура Python-обёртки"]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# ABC_CLASS 10 [Абстрактный базовый класс для источников энтропии] => EntropySource
# END_MODULE_MAP
# START_USE_CASES:
# - [EntropySource.__init__]: System (LoadModule) -> InitializeWithModulePath -> ModuleLoaded
# - [EntropySource.get_entropy]: User (GenerateEntropy) -> RequestEntropy -> EntropyReturned
# - [EntropySource.is_available]: System (CheckAvailability) -> QueryModuleStatus -> StatusReturned
# - [EntropySource._load_module]: System (LoadModule) -> LoadSOFile -> ModuleHandleReturned
# END_USE_CASES
"""
Модуль базовых классов для Python-обёртки генерации энтропии.

Классы:
    EntropySource: Абстрактный базовый класс для источников энтропии.

Пример использования:
    class RandPollSource(EntropySource):
        def get_entropy(self, size: int) -> bytes:
            return self._module.execute_poll()

    source = RandPollSource(module_path="rand_poll_cpp.cpython-310-x86_64-linux-gnu.so")
    if source.is_available():
        entropy = source.get_entropy(32)
"""
import ctypes
import os
from abc import ABC, abstractmethod
from typing import Any, Optional

from src.wrapper.core.exceptions import ModuleLoadError
from src.wrapper.core.logger import EntropyLogger


# START_CLASS_EntropySource
# START_CONTRACT:
# PURPOSE: Абстрактный базовый класс для источников энтропии.
# Определяет интерфейс для загрузки C++ модулей и получения энтропии.
# ATTRIBUTES:
# - module_path: str - Путь к .so модулю
# - _module: Optional[ctypes.CDLL] - Загруженный C++ модуль
# - _logger: EntropyLogger - Логгер для класса
# - _is_available: bool - Флаг доступности модуля
# METHODS:
# - __init__(module_path: str) -> None: Инициализация с загрузкой модуля
# - get_entropy(size: int) -> bytes: Абстрактный метод получения энтропии
# - is_available() -> bool: Проверка доступности модуля
# - _load_module() -> None: Загрузка .so модуля через ctypes
# KEYWORDS: [DOMAIN(9): EntropySource; CONCEPT(8): AbstractBaseClass; TECH(6): ctypes]
# LINKS: [USES(8): ctypes; USES(7): wrapper.core.exceptions; USES(7): wrapper.core.logger]
# END_CONTRACT


class EntropySource(ABC):
    """
    Абстрактный базовый класс для источников энтропии.

    Этот класс предоставляет базовую функциональность для загрузки C++ модулей
    через ctypes и интерфейс для получения энтропии.

    Attributes:
        module_path: Путь к .so модулю.
        is_initialized: Флаг успешной инициализации.
    """

    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация источника энтропии с загрузкой C++ модуля.
    # INPUTS:
    # - module_path: Путь к .so модулю => module_path: str
    # OUTPUTS:
    # - None
    # SIDE_EFFECTS:
    # - Загружает .so модуль через ctypes
    # - Устанавливает флаг доступности
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - Модуль загружен без ошибок
    # - Логгер инициализирован
    # KEYWORDS: [CONCEPT(5): Initialization; TECH(5): ctypes]
    # END_CONTRACT

    def __init__(self, module_path: str) -> None:
        """
        Инициализирует источник энтропии.

        Args:
            module_path: Путь к .so модулю.
        """
        self.module_path = module_path
        self._module: Optional[ctypes.CDLL] = None
        self._logger = EntropyLogger(self.__class__.__name__)
        self._is_available: bool = False
        self.is_initialized: bool = False

        self._logger.info(
            "InitCheck",
            "__init__",
            "Initialize",
            f"Инициализация источника энтропии: {module_path}",
            "ATTEMPT"
        )

        try:
            self._load_module()
            self.is_initialized = True
            self._logger.info(
                "InitCheck",
                "__init__",
                "Initialize",
                f"Источник энтропии инициализирован успешно",
                "SUCCESS"
            )
        except ModuleLoadError as e:
            self._logger.log_error(f"Ошибка загрузки модуля: {e}", e)
            self.is_initialized = False
            # BUG_FIX_CONTEXT: Генерируем исключение дальше, чтобы subclasses
            # могли обработать ошибку и активировать fallback
            raise

    # END_METHOD___init__

    # START_METHOD_get_entropy
    # START_CONTRACT:
    # PURPOSE: Абстрактный метод получения энтропии от источника.
    # INPUTS:
    # - size: Требуемый размер энтропии в байтах => size: int
    # OUTPUTS:
    # - bytes: Сгенерированная энтропия
    # SIDE_EFFECTS:
    # - Вызов C++ модуля для генерации энтропии
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - Возвращает bytes
    # - Размер данных соответствует требованиям
    # KEYWORDS: [DOMAIN(9): EntropyGeneration; CONCEPT(7): AbstractMethod]
    # END_CONTRACT

    @abstractmethod
    def get_entropy(self, size: int) -> bytes:
        """
        Получает энтропию от источника.

        Args:
            size: Требуемый размер энтропии в байтах.

        Returns:
            Сгенерированная энтропия в виде байтов.
        """
        pass

    # END_METHOD_get_entropy

    # START_METHOD_is_available
    # START_CONTRACT:
    # PURPOSE: Проверка доступности модуля и возможности генерации энтропии.
    # INPUTS:
    # - Нет
    # OUTPUTS:
    # - bool: True если модуль загружен и доступен, False иначе
    # KEYWORDS: [DOMAIN(8): AvailabilityCheck]
    # END_CONTRACT

    def is_available(self) -> bool:
        """
        Проверяет доступность источника энтропии.

        Returns:
            True если модуль загружен и доступен, False иначе.
        """
        availability = self._is_available and self._module is not None
        self._logger.debug(
            "SelfCheck",
            "is_available",
            "CheckStatus",
            f"Проверка доступности модуля: {availability}",
            "VALUE" if availability else "FAIL"
        )
        return availability

    # END_METHOD_is_available

    # START_METHOD__load_module
    # START_CONTRACT:
    # PURPOSE: Защищенный метод загрузки .so модуля через ctypes.
    # INPUTS:
    # - Нет (использует self.module_path)
    # OUTPUTS:
    # - None
    # SIDE_EFFECTS:
    # - Устанавливает self._module при успешной загрузке
    # - Устанавливает self._is_available
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - Файл существует
    # - Модуль успешно загружен через ctypes
    # - Обрабатываются исключения OSError и FileNotFoundError
    # KEYWORDS: [TECH(6): ctypes; CONCEPT(6): ModuleLoading]
    # END_CONTRACT

    def _load_module(self) -> None:
        """
        Загружает .so модуль через ctypes.

        Raises:
            ModuleLoadError: Если модуль не найден или не может быть загружен.
        """
        self._logger.debug(
            "LibCheck",
            "_load_module",
            "CheckFile",
            f"Проверка существования файла модуля: {self.module_path}",
            "ATTEMPT"
        )

        if not os.path.exists(self.module_path):
            raise ModuleLoadError(
                self.module_path,
                f"Файл модуля не найден: {self.module_path}"
            )

        self._logger.debug(
            "LibCheck",
            "_load_module",
            "LoadSO",
            f"Загрузка модуля через ctypes: {self.module_path}",
            "ATTEMPT"
        )

        try:
            self._module = ctypes.CDLL(self.module_path)
            self._is_available = True
            self._logger.info(
                "LibCheck",
                "_load_module",
                "LoadSO",
                f"Модуль успешно загружен: {self.module_path}",
                "SUCCESS"
            )
        except OSError as e:
            self._is_available = False
            self._logger.error(
                "CriticalError",
                "_load_module",
                "LoadSO",
                f"Ошибка загрузки модуля: {str(e)}",
                "FAIL"
            )
            raise ModuleLoadError(self.module_path, str(e))

    # END_METHOD__load_module

    # START_METHOD_get_module
    # START_CONTRACT:
    # PURPOSE: Возвращает загруженный модуль для прямого доступа.
    # INPUTS:
    # - Нет
    # OUTPUTS:
    # - Optional[ctypes.CDLL]: Загруженный модуль или None
    # KEYWORDS: [CONCEPT(5): Accessor]
    # END_CONTRACT

    def get_module(self) -> Optional[ctypes.CDLL]:
        """
        Возвращает загруженный C++ модуль.

        Returns:
            Загруженный модуль или None, если модуль не загружен.
        """
        return self._module

    # END_METHOD_get_module

    # START_METHOD_validate_size
    # START_CONTRACT:
    # PURPOSE: Валидация размера запрашиваемой энтропии.
    # INPUTS:
    # - size: Размер в байтах => size: int
    # OUTPUTS:
    # - bool: True если размер валиден
    # KEYWORDS: [DOMAIN(8): Validation]
    # END_CONTRACT

    def validate_size(self, size: int) -> bool:
        """
        Валидирует размер запрашиваемой энтропии.

        Args:
            size: Размер в байтах.

        Returns:
            True если размер положительный, иначе False.
        """
        is_valid = size > 0
        self._logger.debug(
            "VarCheck",
            "validate_size",
            "ConditionCheck",
            f"Проверка размера: size={size}, валиден={is_valid}",
            "SUCCESS" if is_valid else "FAIL"
        )
        return is_valid

    # END_METHOD_validate_size

# END_CLASS_EntropySource
