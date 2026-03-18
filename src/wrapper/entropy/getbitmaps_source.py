# FILE: wrapper/entropy/getbitmaps_source.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Обёртка над getbitmaps_cpp для получения энтропии из битмапов.
# Эмулирует криминалистическую реконструкцию GetBitmapBits для Windows XP.
# SCOPE: Энтропия, видеобуфер, MD5 хеши, 48 блоков
# INPUT: Нет (значения seed и size передаются в методы)
# OUTPUT: Класс GetBitmapsSource с методами получения энтропии
# KEYWORDS: [DOMAIN(10): EntropyGeneration; DOMAIN(9): Graphics; CONCEPT(9): BitmapEmulation; TECH(8): MD5]
# LINKS: [USES(9): wrapper.core.base; USES(8): wrapper.core.exceptions; USES(7): wrapper.core.logger]
# LINKS_TO_SPECIFICATION: ["Задача: Реализация Этапа 3 — GetBitmapsSource (обёртка над getbitmaps_cpp)"]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 10 [Источник энтропии на основе getbitmaps_cpp] => GetBitmapsSource
# METHOD 9 [Выполняет генерацию битмапов и возврат MD5 хешей] => execute
# METHOD 8 [Получает энтропию от источника] => get_entropy
# METHOD 7 [Валидирует размер запрашиваемой энтропии] => validate_size
# METHOD 8 [Возвращает количество обработанных блоков] => get_block_count
# CONST 5 [Количество блоков битмапов] => TOTAL_BLOCKS
# CONST 5 [Размер MD5 хеша в байтах] => MD5_DIGEST_LENGTH
# END_MODULE_MAP
# START_USE_CASES:
# - [GetBitmapsSource.__init__]: System (Initialize) -> LoadModule -> SourceReady
# - [GetBitmapsSource.get_entropy]: User (GenerateEntropy) -> RequestEntropy -> EntropyReturned
# - [GetBitmapsSource.execute]: System (ExecuteBitmap) -> Generate48Blocks -> MD5HashesReturned
# END_USE_CASES
"""
Модуль GetBitmapsSource - обёртка над C++ модулем getbitmaps_cpp.

Класс GetBitmapsSource обеспечивает интерфейс для генерации энтропии через
криминалистическую реконструкцию GetBitmapBits для Windows XP SP3.

Основные возможности:
    - Загрузка C++ модуля getbitmaps_cpp
    - Генерация 48 блоков видеобуфера (эмуляция Bitcoin Genesis Block)
    - Вычисление MD5 хешей для каждого блока
    - Валидация входных параметров
    - Логирование операций
    - Fallback на Python-эмуляцию при недоступности модуля

Пример использования:
    source = GetBitmapsSource()
    if source.is_available():
        entropy = source.get_entropy(32)
        print(f"Получено {len(entropy)} байт энтропии из {source.get_block_count()} блоков")
"""
import os
import ctypes
import struct
import hashlib
import random
from typing import Optional, List, Dict, Any

from src.wrapper.core.base import EntropySource
from src.wrapper.core.exceptions import DataValidationError, EntropyGenerationError, ModuleLoadError
from src.wrapper.core.logger import EntropyLogger, get_logger

# Константы для валидации
MAX_ENTROPY_SIZE = 768  # 48 блоков * 16 байт MD5 = 768 байт
MIN_ENTROPY_SIZE = 1
TOTAL_BLOCKS = 48
MD5_DIGEST_LENGTH = 16
BLOCK_SIZE = 49152  # 16 строк * 1024 пикселей * 3 байта (BGR)

# Константы для генерации битмапов (из C++ исходника)
RAW_WIDTH = 1024
RAW_HEIGHT = 768
RAW_BPP = 3
RAW_STRIDE = 3072
BLOCK_HEIGHT = 16

# Путь к модулю по умолчанию (в lib/ директории)
DEFAULT_MODULE_PATH = "lib/getbitmaps_cpp.cpython-310-x86_64-linux-gnu.so"


# START_CLASS_GetBitmapsSource
# START_CONTRACT:
# PURPOSE: Источник энтропии на основе криминалистической реконструкции GetBitmapBits.
# Наследует функциональность от EntropySource и добавляет поддержку 48 блоков битмапов.
# ATTRIBUTES:
# - seed: int - Начальное значение для генератора случайных чисел
# - _block_count: int - Количество обработанных блоков
# - _use_fallback: bool - Флаг использования Python-эмуляции
# - _entropy_data: bytes - Кэш сгенерированных данных энтропии
# METHODS:
# - __init__(module_path: str = None, seed: int = 0) -> None: Инициализация с загрузкой модуля
# - get_entropy(size: int) -> bytes: Получение энтропии указанного размера
# - execute() -> bytes: Выполнение генерации битмапов
# - get_block_count() -> int: Получение количества обработанных блоков
# - validate_size(size: int) -> bool: Валидация размера энтропии
# KEYWORDS: [DOMAIN(10): EntropyGeneration; DOMAIN(9): Graphics; CONCEPT(9): BitmapEmulation]
# LINKS: [INHERITS(10): EntropySource; USES(8): wrapper.core.exceptions]
# END_CONTRACT


class GetBitmapsSource(EntropySource):
    """
    Источник энтропии на основе криминалистической реконструкции GetBitmapBits.

    Этот класс оборачивает C++ модуль getbitmaps_cpp и предоставляет интерфейс
    для генерации энтропии через 48 блоков видеобуфера:
        - Генерация видеобуфера 1024x768 (BGR)
        - Разбиение на 48 блоков по 16 строк
        - Вычисление MD5 хеша для каждого блока
        - Возврат MD5 хешей (всего 768 байт)

    Attributes:
        seed: Начальное значение для генератора случайных чисел.
        is_available: Флаг доступности источника энтропии.
    """

    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация источника энтропии с загрузкой C++ модуля.
    # INPUTS:
    # - module_path: Путь к .so модулю (опционально) => module_path: str | None
    # - seed: Начальное значение для генератора => seed: int
    # OUTPUTS:
    # - None
    # SIDE_EFFECTS:
    # - Загружает .so модуль через ctypes
    # - Устанавливает seed для воспроизводимости
    # - Инициализирует fallback при недоступности модуля
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - Модуль загружен или включен fallback
    # - Seed установлен корректно
    # - Логгер инициализирован
    # KEYWORDS: [CONCEPT(5): Initialization; TECH(6): ctypes]
    # END_CONTRACT

    def __init__(
        self,
        module_path: Optional[str] = None,
        seed: int = 0
    ) -> None:
        """
        Инициализирует источник энтропии GetBitmapsSource.

        Args:
            module_path: Путь к .so модулю. Если None, используется путь по умолчанию.
            seed: Начальное значение для генератора случайных чисел.
        """
        self.seed = seed
        self._block_count: int = 0
        self._use_fallback: bool = False
        self._module_path = module_path or DEFAULT_MODULE_PATH
        self._entropy_data: Optional[bytes] = None

        # Инициализация логгера
        self._logger = EntropyLogger(self.__class__.__name__)
        self._logger.info(
            "InitCheck",
            "__init__",
            "Initialize",
            f"Инициализация GetBitmapsSource с seed={seed}, module_path={self._module_path}",
            "ATTEMPT"
        )

        # Проверка и установка seed
        if seed < 0 or seed > 0xFFFFFFFF:
            self._logger.warning(
                "VarCheck",
                "__init__",
                "ValidateSeed",
                f"Некорректный seed: {seed}, будет использован seed=0",
                "FAIL"
            )
            self.seed = 0

        # Попытка загрузки модуля
        try:
            # Разрешаем путь к модулю
            full_module_path = self._resolve_module_path(self._module_path)
            super().__init__(full_module_path)
            # Если super() успешен, _use_fallback остается False
        except Exception:
            # Любая ошибка при загрузке модуля - используем fallback
            self._logger.warning(
                "LibCheck",
                "__init__",
                "LoadModule",
                f"Не удалось загрузить C++ модуль. Используется fallback.",
                "ATTEMPT"
            )
            self._use_fallback = True
            self._is_available = True
            self.is_initialized = True
            self._module = None
            self._is_available = True
            # Устанавливаем seed для fallback
            random.seed(self.seed)

        self._logger.info(
            "InitCheck",
            "__init__",
            "Initialize",
            f"GetBitmapsSource инициализирован. Использование fallback: {self._use_fallback}",
            "SUCCESS"
        )

    # END_METHOD___init__

    # START_METHOD__resolve_module_path
    # START_CONTRACT:
    # PURPOSE: Разрешение пути к модулю.
    # INPUTS:
    # - module_path: Относительный или абсолютный путь => module_path: str
    # OUTPUTS:
    # - str: Полный путь к модулю
    # KEYWORDS: [CONCEPT(5): PathResolution]
    # END_CONTRACT

    def _resolve_module_path(self, module_path: str) -> str:
        """
        Разрешает путь к модулю.

        Args:
            module_path: Путь к модулю.

        Returns:
            Полный путь к модулю.
        """
        if os.path.isabs(module_path):
            return module_path

        # Проверяем относительно текущей директории
        if os.path.exists(module_path):
            return os.path.abspath(module_path)

        # Проверяем в корне проекта
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        full_path = os.path.join(project_root, module_path)
        if os.path.exists(full_path):
            return full_path

        # Возвращаем исходный путь для генерации ошибки
        return module_path

    # END_METHOD__resolve_module_path

    # START_METHOD_get_entropy
    # START_CONTRACT:
    # PURPOSE: Получение энтропии от источника указанного размера.
    # INPUTS:
    # - size: Требуемый размер энтропии в байтах => size: int
    # OUTPUTS:
    # - bytes: Сгенерированная энтропия
    # SIDE_EFFECTS:
    # - Вызов C++ модуля или fallback для генерации
    # - Валидация входного параметра
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - Возвращает bytes
    # - Размер данных соответствует запрошенному или максимально возможному
    # - Генерирует исключение при некорректном размере
    # KEYWORDS: [DOMAIN(10): EntropyGeneration; CONCEPT(7): DataGeneration]
    # LINKS_TO_SPECIFICATION: ["Требование: Реализовать метод get_entropy(size: int) -> bytes"]
    # END_CONTRACT

    def get_entropy(self, size: int) -> bytes:
        """
        Получает энтропию от источника.

        Args:
            size: Требуемый размер энтропии в байтах.

        Returns:
            Сгенерированная энтропия в виде байтов.

        Raises:
            DataValidationError: Если размер выходит за допустимые пределы.
            EntropyGenerationError: Если произошла ошибка генерации.
        """
        # START_BLOCK_VALIDATE_SIZE: [Валидация размера запрашиваемой энтропии.]
        self._logger.debug(
            "VarCheck",
            "get_entropy",
            "VALIDATE_SIZE",
            f"Запрошен размер энтропии: {size}",
            "ATTEMPT"
        )

        if not self.validate_size(size):
            error_msg = f"Некорректный размер энтропии: {size}. Допустимый диапазон: {MIN_ENTROPY_SIZE}-{MAX_ENTROPY_SIZE}"
            self._logger.error(
                "VarCheck",
                "get_entropy",
                "VALIDATE_SIZE",
                error_msg,
                "FAIL"
            )
            raise DataValidationError("size", size, f"должно быть в диапазоне {MIN_ENTROPY_SIZE}-{MAX_ENTROPY_SIZE}")
        # END_BLOCK_VALIDATE_SIZE

        # START_BLOCK_GENERATE_ENTROPY: [Генерация энтропии.]
        try:
            # Сначала выполняем генерацию (кешируем результат)
            if self._entropy_data is None:
                self._entropy_data = self.execute()

            if self._use_fallback:
                self._logger.info(
                    "TraceCheck",
                    "get_entropy",
                    "USE_FALLBACK",
                    f"Получение энтропии из Python-эмуляции, размер: {size}",
                    "ATTEMPT"
                )
            else:
                self._logger.info(
                    "TraceCheck",
                    "get_entropy",
                    "CALL_CPP_MODULE",
                    f"Получение энтропии из C++ модуля, размер: {size}",
                    "ATTEMPT"
                )

            # Возвращаем запрошенный размер
            entropy = self._entropy_data[:size]

            self._logger.info(
                "TraceCheck",
                "get_entropy",
                "GENERATE_ENTROPY",
                f"Сгенерировано {len(entropy)} байт энтропии из {self._block_count} блоков",
                "SUCCESS"
            )
            return entropy

        except Exception as e:
            self._logger.error(
                "CriticalError",
                "get_entropy",
                "GENERATE_ENTROPY",
                f"Ошибка генерации энтропии: {str(e)}",
                "FAIL"
            )
            raise EntropyGenerationError("get_entropy", str(e))
        # END_BLOCK_GENERATE_ENTROPY

    # END_METHOD_get_entropy

    # START_METHOD_execute
    # START_CONTRACT:
    # PURPOSE: Выполнение генерации битмапов и возврат MD5 хешей.
    # OUTPUTS:
    # - bytes: MD5 хеши всех 48 блоков (768 байт)
    # KEYWORDS: [DOMAIN(9): BitmapGeneration; CONCEPT(8): MD5Hashing]
    # END_CONTRACT

    def execute(self) -> bytes:
        """
        Выполняет генерацию битмапов и возвращает MD5 хеши.

        Генерирует 48 блоков видеобуфера (каждый 49152 байт),
        вычисляет MD5 хеш для каждого блока и возвращает
        все хеши (48 * 16 = 768 байт).

        Returns:
            MD5 хеши всех блоков в виде байтов.
        """
        self._logger.info(
            "TraceCheck",
            "execute",
            "EXECUTE_BITMAPS",
            f"Начало генерации {TOTAL_BLOCKS} блоков битмапов",
            "ATTEMPT"
        )

        self._block_count = 0

        if self._use_fallback:
            entropy_data = self._generate_fallback_bitmaps()
        else:
            entropy_data = self._generate_cpp_bitmaps()

        self._block_count = TOTAL_BLOCKS
        self._entropy_data = entropy_data

        self._logger.info(
            "TraceCheck",
            "execute",
            "EXECUTE_BITMAPS",
            f"Сгенерировано {len(entropy_data)} байт энтропии из {self._block_count} блоков",
            "SUCCESS"
        )

        return entropy_data

    # END_METHOD_execute

    # START_METHOD__generate_fallback_bitmaps
    # START_CONTRACT:
    # PURPOSE: Генерация битмапов на Python (fallback).
    # OUTPUTS:
    # - bytes: MD5 хеши всех блоков
    # KEYWORDS: [CONCEPT(7): Emulation; TECH(6): MD5]
    # END_CONTRACT

    def _generate_fallback_bitmaps(self) -> bytes:
        """
        Генерирует битмапы на Python (fallback).

        Returns:
            MD5 хеши всех 48 блоков.
        """
        # Используем seed для воспроизводимости
        if self.seed != 0:
            random.seed(self.seed)

        md5_hashes = bytearray()

        # Цвета для генерации пикселей (из C++ исходника)
        XP_BLUE = (0xA5, 0x6E, 0x3A)
        WIN_BTNS = (0xC8, 0xD0, 0xD4)
        GOLD_DARK = (0x00, 0x70, 0xAA)
        GOLD_LIGHT = (0x40, 0xDF, 0xFF)

        # Генерация 48 блоков
        for block_idx in range(TOTAL_BLOCKS):
            block_y = block_idx * BLOCK_HEIGHT

            self._logger.debug(
                "TraceCheck",
                "_generate_fallback_bitmaps",
                "GENERATE_BLOCK",
                f"Генерация блока {block_idx} (block_y={block_y})",
                "ATTEMPT"
            )

            # Генерация данных блока (16 строк)
            block_data = bytearray()
            for y in range(block_y, block_y + BLOCK_HEIGHT):
                for x in range(RAW_WIDTH):
                    # Генерация пикселя
                    if 32 <= x < 64 and 32 <= y < 64:
                        # Золотой градиент
                        t = (x - 32 + y - 32) / 62.0
                        r = int(GOLD_DARK[0] * (1.0 - t) + GOLD_LIGHT[0] * t)
                        g = int(GOLD_DARK[1] * (1.0 - t) + GOLD_LIGHT[1] * t)
                        b = int(GOLD_DARK[2] * (1.0 - t) + GOLD_LIGHT[2] * t)
                        block_data.extend([b, g, r])  # BGR формат
                    elif 300 <= x < 724 and 200 <= y < 500:
                        # Окно приложения
                        if y < 225:
                            block_data.extend([0xD8, 0x81, 0x00])  # Заголовок окна
                        else:
                            block_data.extend([WIN_BTNS[2], WIN_BTNS[1], WIN_BTNS[0]])
                    else:
                        # Фон Windows XP с шумом
                        noise = (x ^ y) % 3
                        block_data.extend([
                            XP_BLUE[0] + noise,
                            XP_BLUE[1],
                            XP_BLUE[2] - noise
                        ])

            # Вычисление MD5 хеша
            md5_hash = hashlib.md5(bytes(block_data)).digest()
            md5_hashes.extend(md5_hash)

            # Логирование первых 8 байт MD5
            md5_hex = md5_hash[:8].hex()
            self._logger.debug(
                "VarCheck",
                "_generate_fallback_bitmaps",
                "COMPUTE_MD5",
                f"MD5 хеш блока {block_idx} (первые 8 байт): {md5_hex}...",
                "VALUE"
            )

        self._logger.info(
            "TraceCheck",
            "_generate_fallback_bitmaps",
            "GENERATE_BLOCKS",
            f"Сгенерировано {len(md5_hashes)} байт (48 MD5 хешей)",
            "SUCCESS"
        )

        return bytes(md5_hashes)

    # END_METHOD__generate_fallback_bitmaps

    # START_METHOD__generate_cpp_bitmaps
    # START_CONTRACT:
    # PURPOSE: Генерация битмапов через C++ модуль.
    # OUTPUTS:
    # - bytes: MD5 хеши всех блоков
    # KEYWORDS: [TECH(6): ctypes]
    # END_CONTRACT

    def _generate_cpp_bitmaps(self) -> bytes:
        """
        Генерирует битмапы через C++ модуль.

        Returns:
            MD5 хеши всех 48 блоков.
        """
        # START_BLOCK_CALL_CPP_FUNCTION: [Вызов C++ функции через pybind11]
        
        # Пробуем использовать C++ модуль через import (pybind11)
        try:
            import sys
            import os
            
            # Добавляем lib в путь если ещё нет
            lib_path = os.path.abspath('lib')
            if lib_path not in sys.path:
                sys.path.insert(0, lib_path)
            
            import getbitmaps_cpp
            result = getbitmaps_cpp.get_bitmap_md5_hashes(self.seed)
            
            self._logger.info(
                "TraceCheck",
                "_generate_cpp_bitmaps",
                "CALL_CPP_FUNCTION",
                "Успешно вызвана C++ функция get_bitmap_md5_hashes через pybind11",
                "SUCCESS"
            )
            return result
        except Exception as e:
            self._logger.warning(
                "LibCheck",
                "_generate_cpp_bitmaps",
                "CALL_CPP_FUNCTION",
                f"Ошибка вызова C++ функции: {e}, используем fallback",
                "ATTEMPT"
            )
            return self._generate_fallback_bitmaps()
        # END_BLOCK_CALL_CPP_FUNCTION

    # END_METHOD__generate_cpp_bitmaps

    # START_METHOD_get_block_count
    # START_CONTRACT:
    # PURPOSE: Получение количества обработанных блоков.
    # OUTPUTS:
    # - int: Количество блоков
    # KEYWORDS: [CONCEPT(5): Introspection)]
    # END_CONTRACT

    def get_block_count(self) -> int:
        """
        Возвращает количество обработанных блоков.

        Returns:
            Количество блоков (48).
        """
        return self._block_count

    # END_METHOD_get_block_count

    # START_METHOD_is_available
    # START_CONTRACT:
    # PURPOSE: Переопределение метода для поддержки fallback.
    # INPUTS: Нет
    # OUTPUTS: bool - True если источник доступен (включая fallback)
    # KEYWORDS: [CONCEPT(5): AvailabilityCheck]
    # END_CONTRACT

    def is_available(self) -> bool:
        """
        Переопределяет метод is_available для поддержки fallback.
        
        Returns:
            True если модуль загружен ИЛИ используется fallback.
        """
        # BUG_FIX_CONTEXT: При использовании fallback модуль может быть None,
        # но источник всё равно доступен через Python-эмуляцию
        if self._use_fallback:
            self._logger.debug(
                "SelfCheck",
                "is_available",
                "CheckStatus",
                "Fallback активен, источник доступен через эмуляцию",
                "SUCCESS"
            )
            return True
        
        # Используем стандартную логику базового класса
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
            True если размер положительный и в пределах допустимого диапазона.
        """
        is_valid = MIN_ENTROPY_SIZE <= size <= MAX_ENTROPY_SIZE
        self._logger.debug(
            "VarCheck",
            "validate_size",
            "ConditionCheck",
            f"Проверка размера: size={size}, валиден={is_valid}",
            "SUCCESS" if is_valid else "FAIL"
        )
        return is_valid

    # END_METHOD_validate_size


# END_CLASS_GetBitmapsSource
