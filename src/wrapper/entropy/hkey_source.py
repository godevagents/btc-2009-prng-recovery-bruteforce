# FILE: wrapper/entropy/hkey_source.py
# VERSION: 1.1.0
# START_MODULE_CONTRACT:
# PURPOSE: Обёртка над hkey_performance_data_cpp для получения энтропии из данных HKEY_PERFORMANCE_DATA.
# Эмулирует криминалистическую реконструкцию RegQueryValueEx для Windows XP SP3.
# SCOPE: Энтропия, Windows Performance Counter, PERF_DATA_BLOCK, бинарные структуры
# INPUT: Нет (значения seed и size передаются в методы)
# OUTPUT: Класс HKeyPerformanceSource с методами получения энтропии
# KEYWORDS: [DOMAIN(10): EntropyGeneration; DOMAIN(9): WindowsPerformance; DOMAIN(8): Forensics; TECH(7): BinaryStructures]
# LINKS: [USES(9): wrapper.core.base; USES(8): wrapper.core.exceptions; USES(7): wrapper.core.logger]
# LINKS_TO_SPECIFICATION: ["Задача: Реализация Этапа 4 — HKeyPerformanceSource (обёртка над hkey_performance_data_cpp)"]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 10 [Источник энтропии на основе hkey_performance_data_cpp] => HKeyPerformanceSource
# METHOD 9 [Генерирует полный дамп HKEY_PERFORMANCE_DATA] => execute
# METHOD 8 [Получает энтропию от источника] => get_entropy
# METHOD 7 [Валидирует размер запрашиваемой энтропии] => validate_size
# CONST 5 [Максимальный размер энтропии в байтах] => MAX_ENTROPY_SIZE
# CONST 5 [Минимальный размер энтропии в байтах] => MIN_ENTROPY_SIZE
# CONST 6 [Базовая частота производительности Windows XP] => PERF_FREQ
# END_MODULE_MAP
# START_USE_CASES:
# - [HKeyPerformanceSource.__init__]: System (Initialize) -> LoadModule -> SourceReady
# - [HKeyPerformanceSource.get_entropy]: User (GenerateEntropy) -> RequestEntropy -> EntropyReturned
# - [HKeyPerformanceSource.execute]: System (ExecuteHKEY) -> GeneratePerformanceData -> BinaryDataReturned
# END_USE_CASES
"""
Модуль HKeyPerformanceSource - обёртка над C++ модулем hkey_performance_data_cpp.

Класс HKeyPerformanceSource обеспечивает интерфейс для генерации энтропии через
криминалистическую реконструкцию HKEY_PERFORMANCE_DATA для Windows XP SP3.

Основные возможности:
    - Загрузка C++ модуля hkey_performance_data_cpp
    - Генерация данных PERF_DATA_BLOCK (системные счетчики производительности)
    - Поддержка 28 типов объектов (System, Memory, Processor, Process, Network и др.)
    - Генерация экземпляров с именами процессов (bitcoin.exe, svchost.exe и др.)
    - Вычисление MD5 хеша данных (согласно Bitcoin 0.1.0)
    - Валидация входных параметров
    - Логирование операций
    - Fallback на Python-эмуляцию при недоступности модуля

Пример использования:
    source = HKeyPerformanceSource(seed=12345)
    if source.is_available():
        entropy = source.get_entropy(32)
        print(f"Получено {len(entropy)} байт энтропии")
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
MAX_ENTROPY_SIZE = 65536  # Максимальный размер данных HKEY_PERFORMANCE_DATA
MIN_ENTROPY_SIZE = 1

# Константы из C++ исходника и документации
PERF_FREQ = 3579545  # Базовая частота производительности Windows XP (Q6600)
Q6600_CORES = 4  # Количество ядер Q6600
BASE_PERF_TIME = 0xC00505E4
BASE_PERF_100NS = 128755000000000000

# Размеры структур Windows Performance
PERF_COUNTER_DEF_SIZE = 40
PERF_OBJECT_HEADER_SIZE = 64
PERF_DATA_BLOCK_SIZE = 64
PERF_INSTANCE_DEF_HEADER_SIZE = 40

# Путь к модулю по умолчанию (относительно корня проекта)
DEFAULT_MODULE_PATH = "lib/hkey_performance_data_cpp.cpython-310-x86_64-linux-gnu.so"

# Импорт pybind11 модуля для генерации HKEY_PERFORMANCE_DATA
def _import_hkey_module(module_path: str):
    """
    Импортирует pybind11 модуль hkey_performance_data_cpp.
    
    Args:
        module_path: Путь к .so модулю.
        
    Returns:
        Импортированный модуль или None при ошибке.
    """
    import importlib.util
    import os
    
    # Разрешаем путь к модулю
    if os.path.isabs(module_path):
        full_path = module_path
    else:
        # Проверяем в корне проекта
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        full_path = os.path.join(project_root, 'lib', module_path)
        if not os.path.exists(full_path):
            full_path = os.path.join(project_root, module_path)
    
    if not os.path.exists(full_path):
        return None
    
    spec = importlib.util.spec_from_file_location("hkey_performance_data_cpp", full_path)
    if spec is None or spec.loader is None:
        return None
    
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None


# START_CLASS_HKeyPerformanceSource
# START_CONTRACT:
# PURPOSE: Источник энтропии на основе криминалистической реконструкции HKEY_PERFORMANCE_DATA.
# Наследует функциональность от EntropySource и добавляет поддержку генерации данных Performance Counter.
# ATTRIBUTES:
# - seed: int - Начальное значение для генератора случайных чисел
# - seconds_passed: int - Количество секунд с базовой точки времени
# - _use_fallback: bool - Флаг использования Python-эмуляции
# - _entropy_data: bytes - Кэш сгенерированных данных энтропии
# METHODS:
# - __init__(module_path: str = None, seed: int = 0, seconds_passed: int = 0) -> None: Инициализация
# - get_entropy(size: int) -> bytes: Получение энтропии указанного размера
# - execute() -> bytes: Выполнение генерации HKEY_PERFORMANCE_DATA
# - validate_size(size: int) -> bool: Валидация размера энтропии
# KEYWORDS: [DOMAIN(10): EntropyGeneration; DOMAIN(9): WindowsPerformance; DOMAIN(8): Forensics]
# LINKS: [INHERITS(10): EntropySource; USES(8): wrapper.core.exceptions]
# END_CONTRACT


class HKeyPerformanceSource(EntropySource):
    """
    Источник энтропии на основе криминалистической реконструкции HKEY_PERFORMANCE_DATA.

    Этот класс оборачивает C++ модуль hkey_performance_data_cpp и предоставляет интерфейс
    для генерации энтропии через данные Windows Performance Counter:
        - Генерация PERF_DATA_BLOCK (заголовок)
        - Генерация 28 типов объектов (System, Memory, Processor, Process, Network и др.)
        - Генерация экземпляров с именами процессов (bitcoin.exe, svchost.exe и др.)
        - Вычисление MD5 хеша полного дампа

    Attributes:
        seed: Начальное значение для генератора случайных чисел.
        seconds_passed: Количество секунд с базовой точки времени.
        is_available: Флаг доступности источника энтропии.
    """

    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация источника энтропии с загрузкой C++ модуля.
    # INPUTS:
    # - module_path: Путь к .so модулю (опционально) => module_path: str | None
    # - seed: Начальное значение для генератора => seed: int
    # - seconds_passed: Количество секунд с базовой точки => seconds_passed: int
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
        seed: int = 0,
        seconds_passed: int = 0
    ) -> None:
        """
        Инициализирует источник энтропии HKeyPerformanceSource.

        Args:
            module_path: Путь к .so модулю. Если None, используется путь по умолчанию.
            seed: Начальное значение для генератора случайных чисел.
            seconds_passed: Количество секунд с базовой точки времени.
        """
        self.seed = seed
        self.seconds_passed = seconds_passed
        self._use_fallback: bool = False
        self._module_path = module_path or DEFAULT_MODULE_PATH
        self._entropy_data: Optional[bytes] = None

        # Инициализация логгера
        self._logger = EntropyLogger(self.__class__.__name__)
        self._logger.info(
            "InitCheck",
            "__init__",
            "Initialize",
            f"Инициализация HKeyPerformanceSource с seed={seed}, seconds_passed={seconds_passed}, module_path={self._module_path}",
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

        # Проверка seconds_passed
        if seconds_passed < 0:
            self._logger.warning(
                "VarCheck",
                "__init__",
                "ValidateSeconds",
                f"Некорректный seconds_passed: {seconds_passed}, будет использован seconds_passed=0",
                "FAIL"
            )
            self.seconds_passed = 0

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
            f"HKeyPerformanceSource инициализирован. Использование fallback: {self._use_fallback}",
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
    # - bytes: Сгенерированная энтропия (MD5 хеш данных HKEY_PERFORMANCE_DATA)
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
            Сгенерированная энтропия в виде байтов (MD5 хеш данных HKEY_PERFORMANCE_DATA).

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
                f"Сгенерировано {len(entropy)} байт энтропии",
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
    # PURPOSE: Выполнение генерации HKEY_PERFORMANCE_DATA и возврат MD5 хеша.
    # OUTPUTS:
    # - bytes: MD5 хеш данных HKEY_PERFORMANCE_DATA (16 байт)
    # KEYWORDS: [DOMAIN(9): WindowsPerformance; CONCEPT(8): MD5Hashing]
    # END_CONTRACT

    def execute(self) -> bytes:
        """
        Выполняет генерацию HKEY_PERFORMANCE_DATA и возвращает MD5 хеш.

        Генерирует полный дамп данных Performance Counter (системные счетчики),
        вычисляет MD5 хеш и возвращает его (16 байт).

        Returns:
            MD5 хеш данных HKEY_PERFORMANCE_DATA в виде байтов.
        """
        self._logger.info(
            "TraceCheck",
            "execute",
            "EXECUTE_HKEY",
            f"Начало генерации HKEY_PERFORMANCE_DATA (seconds_passed={self.seconds_passed})",
            "ATTEMPT"
        )

        if self._use_fallback:
            entropy_data = self._generate_fallback_hkey()
        else:
            entropy_data = self._generate_cpp_hkey()

        self._entropy_data = entropy_data

        self._logger.info(
            "TraceCheck",
            "execute",
            "EXECUTE_HKEY",
            f"Сгенерировано {len(entropy_data)} байт энтропии (MD5 хеш)",
            "SUCCESS"
        )

        return entropy_data

    # END_METHOD_execute

    # START_METHOD__generate_fallback_hkey
    # START_CONTRACT:
    # PURPOSE: Генерация HKEY_PERFORMANCE_DATA на Python (fallback).
    # OUTPUTS:
    # - bytes: MD5 хеш данных
    # KEYWORDS: [CONCEPT(7): Emulation; TECH(6): MD5]
    # END_CONTRACT

    def _generate_fallback_hkey(self) -> bytes:
        """
        Генерирует HKEY_PERFORMANCE_DATA на Python (fallback).

        Эмулирует структуру PERF_DATA_BLOCK согласно документации:
        - Заголовок PERF_DATA_BLOCK (сигнатура, версия, время и т.д.)
        - 28 типов объектов (System, Memory, Processor, Process, Network и др.)
        - Экземпляры с именами процессов

        Returns:
            MD5 хеш сгенерированных данных.
        """
        # Используем seed для воспроизводимости
        if self.seed != 0:
            random.seed(self.seed)

        self._logger.info(
            "TraceCheck",
            "_generate_fallback_hkey",
            "GENERATE_PERF_DATA",
            "Генерация PERF_DATA_BLOCK (fallback)",
            "ATTEMPT"
        )

        entropy_data = bytearray()

        # START_BLOCK_GENERATE_PERF_HEADER: [Генерация заголовка PERF_DATA_BLOCK]
        # 1.1 Signature "PERF" (UTF-16LE)
        entropy_data.extend(b'P\x00E\x00R\x00F\x00')

        # 1.2 LittleEndian
        entropy_data.extend(struct.pack('<I', 1))

        # 1.3 Version
        entropy_data.extend(struct.pack('<I', 1))

        # 1.4 Revision
        entropy_data.extend(struct.pack('<I', 1))

        # 1.5 TotalByteLength (случайное значение в диапазоне)
        total_length = random.randint(0x000927C0, 0x00124F80)
        entropy_data.extend(struct.pack('<I', total_length))

        # 1.6 HeaderLength
        entropy_data.extend(struct.pack('<I', PERF_DATA_BLOCK_SIZE))

        # 1.7 NumObjectTypes
        num_object_types = 28
        entropy_data.extend(struct.pack('<I', num_object_types))

        # 1.8 DefaultObject
        entropy_data.extend(struct.pack('<I', 0xFFFFFFFF))

        # 1.9 SystemTime (16 байт)
        year = 2009
        month = 1
        day_of_week = random.randint(0, 6)
        day = random.randint(9, 20)
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        millisecond = random.randint(0, 999)

        entropy_data.extend(struct.pack('<H', year))  # wYear
        entropy_data.extend(struct.pack('<H', month))  # wMonth
        entropy_data.extend(struct.pack('<H', day_of_week))  # wDayOfWeek
        entropy_data.extend(struct.pack('<H', day))  # wDay
        entropy_data.extend(struct.pack('<H', hour))  # wHour
        entropy_data.extend(struct.pack('<H', minute))  # wMinute
        entropy_data.extend(struct.pack('<H', second))  # wSecond
        entropy_data.extend(struct.pack('<H', millisecond))  # wMilliseconds

        # 1.10 PerfTime
        perf_time = BASE_PERF_TIME + (self.seconds_passed * PERF_FREQ)
        entropy_data.extend(struct.pack('<Q', perf_time))

        # 1.11 PerfFreq
        entropy_data.extend(struct.pack('<Q', PERF_FREQ))

        # 1.12 PerfTime100nSec
        perf_100ns = BASE_PERF_100NS + (self.seconds_passed * 10000000)
        entropy_data.extend(struct.pack('<Q', perf_100ns))

        # 1.13 SystemNameLength
        sys_name = "SATOSHI-PC"
        sys_name_utf16 = sys_name.encode('utf-16-le')
        sys_name_len = len(sys_name_utf16) + 2  # +2 для завершающего нуля
        entropy_data.extend(struct.pack('<I', sys_name_len))

        # 1.14 SystemNameOffset
        entropy_data.extend(struct.pack('<I', PERF_DATA_BLOCK_SIZE))
        # END_BLOCK_GENERATE_PERF_HEADER

        # START_BLOCK_GENERATE_SYSTEM_NAME: [Добавление имени системы]
        entropy_data.extend(sys_name_utf16)
        entropy_data.extend(b'\x00\x00')  # Завершающий нуль
        # Выравнивание до 8 байт
        while len(entropy_data) % 8 != 0:
            entropy_data.append(0)
        # END_BLOCK_GENERATE_SYSTEM_NAME

        # START_BLOCK_GENERATE_OBJECTS: [Генерация объектов производительности]
        # Генерируем 28 типов объектов (как в документации)
        object_ids = [2, 4, 6, 7, 8, 9] + list(range(10, 29))  # System, Memory, Processor, PhysicalDisk, Network Interface и др.

        for obj_id in object_ids:
            obj_data = self._generate_single_object(obj_id, perf_time)
            entropy_data.extend(obj_data)

        self._logger.info(
            "TraceCheck",
            "_generate_fallback_hkey",
            "GENERATE_OBJECTS",
            f"Сгенерировано {len(object_ids)} объектов производительности",
            "ATTEMPT"
        )
        # END_BLOCK_GENERATE_OBJECTS

        # START_BLOCK_COMPUTE_MD5: [Вычисление MD5 хеша]
        # Согласно Bitcoin 0.1.0, возвращается MD5 хеш данных
        md5_hash = hashlib.md5(bytes(entropy_data)).digest()

        self._logger.debug(
            "VarCheck",
            "_generate_fallback_hkey",
            "COMPUTE_MD5",
            f"MD5 хеш данных: {md5_hash.hex()}",
            "VALUE"
        )
        # END_BLOCK_COMPUTE_MD5

        return md5_hash

    # END_METHOD__generate_fallback_hkey

    # START_METHOD__generate_single_object
    # START_CONTRACT:
    # PURPOSE: Генерация одного объекта PERF_OBJECT_TYPE.
    # INPUTS:
    # - obj_id: Идентификатор объекта => obj_id: int
    # - perf_time: Время производительности => perf_time: int
    # OUTPUTS:
    # - bytes: Бинарные данные объекта
    # KEYWORDS: [DOMAIN(8): PerformanceObjects; TECH(7): BinaryStructures]
    # END_CONTRACT

    def _generate_single_object(self, obj_id: int, perf_time: int) -> bytes:
        """
        Генерирует один объект PERF_OBJECT_TYPE.

        Args:
            obj_id: Идентификатор объекта.
            perf_time: Время производительности.

        Returns:
            Бинарные данные объекта.
        """
        obj_data = bytearray()

        # Количество счетчиков (28-32)
        counter_count = random.randint(28, 32)

        # Определение экземпляров в зависимости от типа объекта
        instances = []
        if obj_id == 238:  # Processor
            for i in range(Q6600_CORES):
                instances.append(str(i))
            instances.append("_Total")
        elif obj_id == 230:  # Process
            instances = ["System", "smss.exe", "csrss.exe", "winlogon.exe",
                         "services.exe", "lsass.exe", "svchost.exe", "explorer.exe", "bitcoin.exe"]
            for _ in range(3):
                instances.append("svchost.exe")
        elif obj_id == 272:  # Network
            instances = ["Intel(R) PRO/1000"]

        # START_BLOCK_GENERATE_COUNTERS: [Генерация счетчиков]
        # PERF_COUNTER_DEFINITION (40 байт каждый)
        counter_offset = 8  # Начинаем с 8 байт (после PERF_COUNTER_BLOCK заголовка)

        for i in range(counter_count):
            # ByteLength
            obj_data.extend(struct.pack('<I', PERF_COUNTER_DEF_SIZE))

            # NameTitleIndex
            name_title = obj_id + (i * 2) + 2
            obj_data.extend(struct.pack('<I', name_title))

            # Reserved
            obj_data.extend(struct.pack('<I', 0))

            # HelpTitleIndex
            help_title = obj_id + (i * 2) + 3
            obj_data.extend(struct.pack('<I', help_title))

            # Reserved
            obj_data.extend(struct.pack('<I', 0))

            # DefaultScale (список констант: 0, -1, -2, 1, 7)
            default_scale = random.choice([0, -1, -2, 1, 7])
            obj_data.extend(struct.pack('<i', default_scale))

            # DetailLevel
            obj_data.extend(struct.pack('<I', 100))

            # CounterType (список констант)
            counter_type = random.choice([0, 65536, 5253120, 66048, 66050, 5379200, 2816])
            obj_data.extend(struct.pack('<I', counter_type))

            # CounterSize (8 байт для 64-битных)
            obj_data.extend(struct.pack('<I', 8))

            # CounterOffset
            obj_data.extend(struct.pack('<I', counter_offset))
            counter_offset += 8
        # END_BLOCK_GENERATE_COUNTERS

        # START_BLOCK_GENERATE_INSTANCES: [Генерация экземпляров]
        if instances:
            # Мультиинстансный объект
            for name in instances:
                # Конвертация имени в UTF-16LE
                name_utf16 = name.encode('utf-16-le')
                name_len = len(name_utf16) + 2  # +2 для завершающего нуля

                # Выравнивание до 8 байт
                name_len_aligned = (name_len + 7) & ~7
                inst_def_len = PERF_INSTANCE_DEF_HEADER_SIZE + name_len_aligned

                # PERF_INSTANCE_DEFINITION заголовок
                obj_data.extend(struct.pack('<I', inst_def_len))  # ByteLength
                obj_data.extend(struct.pack('<I', 0))  # Reserved
                obj_data.extend(struct.pack('<I', 0))  # Reserved
                obj_data.extend(struct.pack('<I', 0xFFFFFFFF))  # UniqueID
                obj_data.extend(struct.pack('<I', PERF_INSTANCE_DEF_HEADER_SIZE))  # NameOffset
                obj_data.extend(struct.pack('<I', name_len))  # NameLength

                # Имя + выравнивание
                obj_data.extend(name_utf16)
                obj_data.extend(b'\x00\x00')  # Завершающий нуль
                while len(obj_data) % 8 != 0:
                    obj_data.append(0)

                # PERF_COUNTER_BLOCK
                block_len = 8 + (counter_count * 8)
                block_len_aligned = (block_len + 7) & ~7
                obj_data.extend(struct.pack('<I', block_len_aligned))

                # Грязный паддинг (мусор из памяти)
                padding_len = block_len_aligned - 4
                for _ in range(padding_len):
                    obj_data.append(random.choice([0x00, 0x00, random.randint(0, 255), 0xCC]))
        else:
            # Singleton объект (как Memory)
            block_len = 8 + (counter_count * 8)
            block_len_aligned = (block_len + 7) & ~7
            obj_data.extend(struct.pack('<I', block_len_aligned))

            # Грязный паддинг
            padding_len = block_len_aligned - 4
            for _ in range(padding_len):
                obj_data.append(random.choice([0x00, 0x00, random.randint(0, 255), 0xCC]))
        # END_BLOCK_GENERATE_INSTANCES

        # START_BLOCK_GENERATE_HEADER: [Генерация заголовка объекта]
        header = bytearray()

        # TotalLength
        total_obj_len = PERF_OBJECT_HEADER_SIZE + len(obj_data)
        header.extend(struct.pack('<I', total_obj_len))

        # DefinitionLength
        def_len = PERF_OBJECT_HEADER_SIZE + (counter_count * PERF_COUNTER_DEF_SIZE)
        header.extend(struct.pack('<I', def_len))

        # HeaderLength
        header.extend(struct.pack('<I', PERF_OBJECT_HEADER_SIZE))

        # ObjectNameTitleIndex
        header.extend(struct.pack('<I', obj_id))

        # ObjectHelpTitleIndex
        header.extend(struct.pack('<I', obj_id + 1))

        # DetailLevel
        header.extend(struct.pack('<I', 100))

        # DefaultCount
        default_count = random.choice([0, -1])
        header.extend(struct.pack('<i', default_count))

        # NumInstances
        num_instances = len(instances) if instances else -1
        header.extend(struct.pack('<i', num_instances))

        # CodePage
        header.extend(struct.pack('<I', 0))

        # PerfTime
        header.extend(struct.pack('<Q', perf_time))

        # PerfFreq
        header.extend(struct.pack('<Q', PERF_FREQ))

        # Объединяем заголовок и данные
        result = bytes(header) + bytes(obj_data)
        # END_BLOCK_GENERATE_HEADER

        return result

    # END_METHOD__generate_single_object

    # START_METHOD__generate_cpp_hkey
    # START_CONTRACT:
    # PURPOSE: Генерация HKEY_PERFORMANCE_DATA через C++ модуль.
    # OUTPUTS:
    # - bytes: MD5 хеш данных
    # KEYWORDS: [TECH(6): ctypes]
    # END_CONTRACT

    def _generate_cpp_hkey(self) -> bytes:
        """
        Генерирует HKEY_PERFORMANCE_DATA через pybind11 C++ модуль.

        Вызывает функцию generate_hkey_performance_data_legacy из pybind11 модуля,
        вычисляет MD5 хеш и возвращает его.

        Returns:
            MD5 хеш данных HKEY_PERFORMANCE_DATA.
        """
        self._logger.info(
            "TraceCheck",
            "_generate_cpp_hkey",
            "CALL_PYBIND11_MODULE",
            "Вызов pybind11 модуля hkey_performance_data_cpp",
            "ATTEMPT"
        )

        try:
            # Импортируем pybind11 модуль
            hkey_module = _import_hkey_module(self._module_path)
            
            if hkey_module is None:
                self._logger.warning(
                    "TraceCheck",
                    "_generate_cpp_hkey",
                    "MODULE_LOAD_FAILED",
                    "Не удалось загрузить pybind11 модуль, используем fallback",
                    "ATTEMPT"
                )
                return self._generate_fallback_hkey()
            
            # Вызываем функцию generate_hkey_performance_data_legacy
            # Функция возвращает bytes (через py::bytes)
            perf_data = hkey_module.generate_hkey_performance_data_legacy(self.seconds_passed)
            
            if not perf_data or len(perf_data) == 0:
                self._logger.warning(
                    "TraceCheck",
                    "_generate_cpp_hkey",
                    "CPP_RETURN_EMPTY",
                    "C++ модуль вернул пустые данные, используем fallback",
                    "ATTEMPT"
                )
                return self._generate_fallback_hkey()
            
            self._logger.debug(
                "VarCheck",
                "_generate_cpp_hkey",
                "CPP_DATA_SIZE",
                f"Получено данных от C++ модуля: {len(perf_data)} байт",
                "VALUE"
            )
            
            # Вычисляем MD5 хеш данных PERF_DATA_BLOCK
            md5_hash = hashlib.md5(perf_data).digest()
            
            self._logger.debug(
                "VarCheck",
                "_generate_cpp_hkey",
                "COMPUTE_MD5",
                f"MD5 хеш данных: {md5_hash.hex()}",
                "VALUE"
            )
            
            self._logger.info(
                "TraceCheck",
                "_generate_cpp_hkey",
                "CPP_SUCCESS",
                "Успешно получен MD5 хеш через pybind11 модуль",
                "SUCCESS"
            )
            
            return md5_hash

        except AttributeError as e:
            # Функция не найдена в модуле
            self._logger.warning(
                "TraceCheck",
                "_generate_cpp_hkey",
                "CPP_FUNCTION_NOT_FOUND",
                f"Функция не найдена в модуле: {e}, используем fallback",
                "ATTEMPT"
            )
            return self._generate_fallback_hkey()

        except Exception as e:
            # Любая другая ошибка
            self._logger.warning(
                "TraceCheck",
                "_generate_cpp_hkey",
                "CPP_ERROR",
                f"Ошибка вызова pybind11 модуля: {e}, используем fallback",
                "ATTEMPT"
            )
            return self._generate_fallback_hkey()

    # END_METHOD__generate_cpp_hkey

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


# END_CLASS_HKeyPerformanceSource
