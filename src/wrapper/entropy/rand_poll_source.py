# FILE: wrapper/entropy/rand_poll_source.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Обёртка над C++ модулем rand_poll_cpp для получения энтропии.
# Эмулирует криминалистическую реконструкцию RAND_poll() для Windows XP SP3.
# SCOPE: Энтропия, 5 фаз сбора, Windows API эмуляция
# INPUT: Нет (значения seed и size передаются в методы)
# OUTPUT: Класс RandPollSource с методами получения энтропии
# KEYWORDS: [DOMAIN(10): EntropyGeneration; DOMAIN(9): Forensics; TECH(8): Windows_API; TECH(7): Emulation]
# LINKS: [USES(9): wrapper.core.base; USES(8): wrapper.core.exceptions; USES(7): wrapper.core.logger]
# LINKS_TO_SPECIFICATION: ["Задача: Реализация Этапа 2 — RandPollSource (обёртка над rand_poll_cpp)"]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 10 [Источник энтропии на основе rand_poll_cpp] => RandPollSource
# METHOD 9 [Выполняет полный цикл сбора энтропии (5 фаз)] => execute_poll
# METHOD 8 [Получает энтропию от источника] => get_entropy
# METHOD 7 [Валидирует размер запрашиваемой энтропии] => validate_size
# METHOD 8 [Возвращает информацию о фазах] => get_phases_info
# CONST 5 [Максимальный размер энтропии в байтах] => MAX_ENTROPY_SIZE
# CONST 5 [Минимальный размер энтропии в байтах] => MIN_ENTROPY_SIZE
# END_MODULE_MAP
# START_USE_CASES:
# - [RandPollSource.__init__]: System (Initialize) -> LoadModule -> SourceReady
# - [RandPollSource.get_entropy]: User (GenerateEntropy) -> RequestEntropy -> EntropyReturned
# - [RandPollSource.execute_poll]: System (ExecutePoll) -> Run5Phases -> StateReturned
# END_USE_CASES
"""
Модуль RandPollSource - обёртка над C++ модулем rand_poll_cpp.

Класс RandPollSource обеспечивает интерфейс для генерации энтропии через
криминалистическую реконструкцию RAND_poll() для Windows XP SP3.

Основные возможности:
    - Загрузка C++ модуля rand_poll_cpp
    - Выполнение 5 фаз сбора энтропии
    - Валидация входных параметров
    - Логирование операций
    - Fallback на Python-эмуляцию при недоступности модуля

Пример использования:
    source = RandPollSource(seed=12345)
    if source.is_available():
        entropy = source.get_entropy(32)
        print(f"Получено {len(entropy)} байт энтропии")
"""
import os
import sys
import struct
import random
import hashlib
import importlib.util
from typing import Optional, List, Dict, Any

from src.wrapper.core.base import EntropySource
from src.wrapper.core.exceptions import DataValidationError, EntropyGenerationError, ModuleLoadError
from src.wrapper.core.logger import EntropyLogger, get_logger

# Константы для валидации
MAX_ENTROPY_SIZE = 1024
MIN_ENTROPY_SIZE = 1

# Путь к модулю по умолчанию (в lib/ директории)
DEFAULT_MODULE_PATH = "lib/rand_poll_cpp.cpython-310-x86_64-linux-gnu.so"


# START_CLASS_RandPollSource
# START_CONTRACT:
# PURPOSE: Источник энтропии на основе криминалистической реконструкции RAND_poll.
# Наследует функциональность от EntropySource и добавляет поддержку 5 фаз реконструкции.
# ATTRIBUTES:
# - seed: int - Начальное значение для генератора случайных чисел
# - _phases_info: Dict - Информация о выполненных фазах
# - _use_fallback: bool - Флаг использования Python-эмуляции
# METHODS:
# - __init__(module_path: str = None, seed: int = 0) -> None: Инициализация с загрузкой модуля
# - get_entropy(size: int) -> bytes: Получение энтропии указанного размера
# - execute_poll() -> bytes: Выполнение полного цикла (5 фаз)
# - get_phases_info() -> Dict[str, Any]: Получение информации о фазах
# - validate_size(size: int) -> bool: Валидация размера энтропии
# KEYWORDS: [DOMAIN(10): EntropyGeneration; DOMAIN(9): Forensics; TECH(8): Windows_API]
# LINKS: [INHERITS(10): EntropySource; USES(8): wrapper.core.exceptions]
# END_CONTRACT


class RandPollSource(EntropySource):
    """
    Источник энтропии на основе криминалистической реконструкции RAND_poll.

    Этот класс оборачивает C++ модуль rand_poll_cpp и предоставляет интерфейс
    для генерации энтропии через 5 фаз сбора:
        1. NetAPI - статистика сети (LanmanWorkstation, LanmanServer)
        2. CryptoAPI - CryptGenRandom
        3. User32 - данные UI (GetForegroundWindow, CURSORINFO)
        4. Toolhelp32 - снимок процессов и потоков
        5. Kernel32 - системные данные (RDTSC, QPC, MemoryStatus)

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
        Инициализирует источник энтропии RandPollSource.

        Args:
            module_path: Путь к .so модулю. Если None, используется путь по умолчанию.
            seed: Начальное значение для генератора случайных чисел.
        """
        self.seed = seed
        self._phases_info: Dict[str, Any] = {}
        self._use_fallback: bool = False
        self._module_path = module_path or DEFAULT_MODULE_PATH
        self._cpp_module = None  # pybind11 module reference
        self._cpp_instance = None  # RandPollReconstructorXP instance
        
        # Кеширование для is_available()
        self._availability_cached = False
        self._is_available_cached = False

        # Инициализация логгера
        self._logger = EntropyLogger(self.__class__.__name__)
        self._logger.info(
            "InitCheck",
            "__init__",
            "Initialize",
            f"Инициализация RandPollSource с seed={seed}, module_path={self._module_path}",
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

        # Попытка загрузки C++ модуля
        try:
            # Разрешаем путь к модулю
            full_module_path = self._resolve_module_path(self._module_path)
            
            if not os.path.exists(full_module_path):
                raise FileNotFoundError(f"Модуль не найден: {full_module_path}")
            
            # Загружаем модуль через importlib
            spec = importlib.util.spec_from_file_location(
                "rand_poll_cpp", 
                full_module_path
            )
            if spec is None or spec.loader is None:
                raise ImportError("Не удалось создать spec для модуля")
            
            self._cpp_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self._cpp_module)
            
            # Создаем экземпляр RandPollReconstructorXP с seed
            if hasattr(self._cpp_module, 'RandPollReconstructorXP'):
                self._cpp_instance = self._cpp_module.RandPollReconstructorXP(self.seed)
                self._logger.info(
                    "InitCheck",
                    "__init__",
                    "LoadModule",
                    f"C++ модуль загружен успешно. RandPollReconstructorXP инициализирован с seed={self.seed}",
                    "SUCCESS"
                )
            else:
                raise AttributeError("RandPollReconstructorXP не найден в модуле")
            
            # BUG_FIX_CONTEXT: Инициализация _is_available при успешной загрузке модуля
            self._is_available = True
            self.is_initialized = True
                
        except Exception as e:
            # Любая ошибка при загрузке модуля - используем fallback
            self._logger.warning(
                "LibCheck",
                "__init__",
                "LoadModule",
                f"Не удалось загрузить C++ модуль: {str(e)}. Используется fallback.",
                "ATTEMPT"
            )
            self._use_fallback = True
            self._is_available = True
            self.is_initialized = True
            # Устанавливаем seed для fallback
            random.seed(self.seed)

        self._logger.info(
            "InitCheck",
            "__init__",
            "Initialize",
            f"RandPollSource инициализирован. Использование fallback: {self._use_fallback}",
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
            if self._use_fallback:
                self._logger.info(
                    "TraceCheck",
                    "get_entropy",
                    "USE_FALLBACK",
                    f"Генерация энтропии через Python-эмуляцию, размер: {size}",
                    "ATTEMPT"
                )
                entropy = self._generate_fallback_entropy(size)
            else:
                self._logger.info(
                    "TraceCheck",
                    "get_entropy",
                    "CALL_CPP_MODULE",
                    f"Генерация энтропии через C++ модуль, размер: {size}",
                    "ATTEMPT"
                )
                entropy = self._generate_cpp_entropy(size)

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

    # START_METHOD_execute_poll
    # START_CONTRACT:
    # PURPOSE: Выполнение полного цикла сбора энтропии (5 фаз).
    # OUTPUTS:
    # - bytes: Состояние PRNG после выполнения всех фаз
    # KEYWORDS: [DOMAIN(9): EntropyReconstruction; CONCEPT(8): Workflow]
    # END_CONTRACT

    def execute_poll(self) -> bytes:
        """
        Выполняет полный цикл сбора энтропии (5 фаз).

        Фазы:
            1. NetAPI - сбор статистики сети
            2. CryptoAPI - генерация случайных чисел
            3. User32 - сбор данных UI
            4. Toolhelp32 - снимок процессов и потоков
            5. Kernel32 - сбор системных данных

        Returns:
            Состояние PRNG в виде байтов.
        """
        # Используем C++ модуль если доступен
        if not self._use_fallback and self._cpp_instance is not None:
            self._logger.info(
                "TraceCheck",
                "execute_poll",
                "EXECUTE_CPP_POLL",
                "Выполнение C++ RandPollReconstructorXP.execute_poll()",
                "ATTEMPT"
            )
            
            # Вызываем C++ метод
            result = self._cpp_instance.execute_poll()
            
            # Конвертируем результат
            if isinstance(result, str):
                poll_data = result.encode('latin-1')
            else:
                poll_data = bytes(result)
            
            self._logger.info(
                "TraceCheck",
                "execute_poll",
                "EXECUTE_CPP_POLL",
                f"C++ poll выполнен, получено {len(poll_data)} байт",
                "SUCCESS"
            )
            return poll_data
        
        # Иначе используем Python fallback
        self._logger.info(
            "TraceCheck",
            "execute_poll",
            "EXECUTE_PHASES",
            "Начало выполнения 5 фаз сбора энтропии (Python fallback)",
            "ATTEMPT"
        )

        self._phases_info = {
            "phase_1_netapi": {"executed": False, "entropy_contribution": 0.0},
            "phase_2_cryptoapi": {"executed": False, "entropy_contribution": 0.0},
            "phase_3_user32": {"executed": False, "entropy_contribution": 0.0},
            "phase_4_toolhelp32": {"executed": False, "entropy_contribution": 0.0},
            "phase_5_kernel32": {"executed": False, "entropy_contribution": 0.0},
        }

        # Выполнение фаз
        phases = [
            ("phase_1_netapi", self._execute_phase_1_netapi, 45.0 + 17.0 + 0.0),
            ("phase_2_cryptoapi", self._execute_phase_2_cryptoapi, 0.0),
            ("phase_3_user32", self._execute_phase_3_user32, 2.0 + 1.0),
            ("phase_4_toolhelp32", self._execute_phase_4_toolhelp32, 3.0 + 5.0 * 40 + 9.0 + 6.0 * 20 + 9.0),
            ("phase_5_kernel32", self._execute_phase_5_kernel32, 1.0 + 0.0 + 1.0 + 1.0),
        ]

        all_entropy = b""

        for phase_name, phase_func, entropy_estimate in phases:
            self._logger.debug(
                "TraceCheck",
                "execute_poll",
                "EXECUTE_PHASE",
                f"Выполнение фазы: {phase_name}",
                "ATTEMPT"
            )

            phase_data = phase_func()
            all_entropy += phase_data
            self._phases_info[phase_name]["executed"] = True
            self._phases_info[phase_name]["entropy_contribution"] = entropy_estimate

            self._logger.info(
                "TraceCheck",
                "execute_poll",
                "PHASE_COMPLETE",
                f"Фаза {phase_name} выполнена, добавлено {len(phase_data)} байт",
                "SUCCESS"
            )

        # Добавляем HKEY_PERFORMANCE_DATA (фаза 6)
        hkey_data = self._execute_hkey_performance_data()
        all_entropy += hkey_data

        self._logger.info(
            "TraceCheck",
            "execute_poll",
            "EXECUTE_PHASES",
            f"Все фазы выполнены. Total: {len(all_entropy)} байт",
            "SUCCESS"
        )

        return all_entropy

    # END_METHOD_execute_poll

    # START_METHOD__execute_phase_1_netapi
    # START_CONTRACT:
    # PURPOSE: Эмуляция фазы 1 - сбор статистики NetAPI.
    # OUTPUTS:
    # - bytes: Данные энтропии фазы
    # KEYWORDS: [DOMAIN(8): Networking; TECH(7): NetAPI32]
    # END_CONTRACT

    def _execute_phase_1_netapi(self) -> bytes:
        """
        Эмулирует сбор статистики NetAPI (LanmanWorkstation, LanmanServer).
        """
        entropy_data = bytearray()

        # LanmanWorkstation статистика (32 поля по 4 байта)
        for _ in range(32):
            entropy_data.extend(struct.pack('<I', random.randint(0, 0xFFFFFFFF)))

        # LanmanServer статистика (17 полей по 4 байта)
        for _ in range(17):
            entropy_data.extend(struct.pack('<I', random.randint(0, 0xFFFFFFFF)))

        # HCRYPTPROV
        entropy_data.extend(struct.pack('<I', random.randint(0x00001000, 0x00009000)))

        return bytes(entropy_data)

    # END_METHOD__execute_phase_1_netapi

    # START_METHOD__execute_phase_2_cryptoapi
    # START_CONTRACT:
    # PURPOSE: Эмуляция фазы 2 - CryptGenRandom.
    # OUTPUTS:
    # - bytes: Данные энтропии фазы
    # KEYWORDS: [DOMAIN(9): Crypto; TECH(8): CryptoAPI]
    # END_CONTRACT

    def _execute_phase_2_cryptoapi(self) -> bytes:
        """
        Эмулирует CryptGenRandom (64 байта).
        """
        return bytes([random.randint(0, 255) for _ in range(64)])

    # END_METHOD__execute_phase_2_cryptoapi

    # START_METHOD__execute_phase_3_user32
    # START_CONTRACT:
    # PURPOSE: Эмуляция фазы 3 - сбор данных User32.
    # OUTPUTS:
    # - bytes: Данные энтропии фазы
    # KEYWORDS: [DOMAIN(7): UI_State; TECH(6): User32]
    # END_CONTRACT

    def _execute_phase_3_user32(self) -> bytes:
        """
        Эмулирует сбор данных User32 (GetForegroundWindow, CURSORINFO, GetQueueStatus).
        """
        entropy_data = bytearray()

        # GetForegroundWindow (HWND)
        entropy_data.extend(struct.pack('<I', random.choice([0x00010024, 0x01010000])))

        # CURSORINFO (20 байт)
        entropy_data.extend(struct.pack('<I', 0x00000014))  # cbSize
        entropy_data.extend(struct.pack('<I', 0x00000001))  # flags
        entropy_data.extend(struct.pack('<I', 0x00010002))  # hCursor
        entropy_data.extend(struct.pack('<I', 0x00000280))  # pt.x
        entropy_data.extend(struct.pack('<I', 0x00000200))  # pt.y

        # GetQueueStatus
        entropy_data.extend(struct.pack('<I', 0x0000006B))

        return bytes(entropy_data)

    # END_METHOD__execute_phase_3_user32

    # START_METHOD__execute_phase_4_toolhelp32
    # START_CONTRACT:
    # PURPOSE: Эмуляция фазы 4 - Toolhelp32Snapshot.
    # OUTPUTS:
    # - bytes: Данные энтропии фазы
    # KEYWORDS: [DOMAIN(9): OS_Internals; TECH(8): Kernel32]
    # END_CONTRACT

    def _execute_phase_4_toolhelp32(self) -> bytes:
        """
        Эмулирует Toolhelp32Snapshot (процессы, потоки, модули).
        """
        entropy_data = bytearray()

        # HEAPLIST32 для каждого процесса
        for _ in range(4):
            entropy_data.extend(struct.pack('<I', 0x00000010))  # dwSize
            entropy_data.extend(struct.pack('<I', random.randint(0x00050A00, 0x00110A30)))  # th32ProcessID
            entropy_data.extend(struct.pack('<I', random.randint(0x00090000, 0x04000000)))  # th32HeapID
            entropy_data.extend(struct.pack('<I', 0x00000000))  # dwFlags

            # HEAPENTRY32 (до 40 записей)
            for _ in range(random.randint(15, 40)):
                entropy_data.extend(struct.pack('<I', 0x00000024))  # dwSize
                entropy_data.extend(struct.pack('<I', random.randint(0x00090000, 0x04000000)))  # hHandle
                entropy_data.extend(struct.pack('<I', random.randint(0x00090500, 0x00100000)))  # dwAddress
                entropy_data.extend(struct.pack('<I', random.randint(0x00000020, 0x00000040)))  # dwBlockSize
                entropy_data.extend(struct.pack('<I', random.choice([0x00000001, 0x00000002])))  # dwFlags
                entropy_data.extend(struct.pack('<I', 0x00000000))  # dwLockCount
                entropy_data.extend(struct.pack('B', 0x00))  # dwResvd
                entropy_data.extend(struct.pack('<I', random.randint(0x00090000, 0x00110A30)))  # th32ProcessID
                entropy_data.extend(struct.pack('<I', random.randint(0x00001500, 0x00050000)))  # th32HeapID

        # PROCESSENTRY32
        for _ in range(4):
            entropy_data.extend(struct.pack('<I', 0x00000128))  # dwSize
            entropy_data.extend(struct.pack('<I', 0x00000000))  # cntUsage
            entropy_data.extend(struct.pack('<I', random.randint(0x00050A00, 0x00110A30)))  # th32ProcessID
            entropy_data.extend(struct.pack('<I', 0x00000000))  # th32DefaultHeapID
            entropy_data.extend(struct.pack('<I', 0x00000000))  # th32ModuleID
            entropy_data.extend(struct.pack('<I', random.randint(0x00000003, 0x00000008)))  # cntThreads
            entropy_data.extend(struct.pack('<I', random.randint(0x00020020, 0x00060050)))  # th32ParentProcessID
            entropy_data.extend(struct.pack('<I', 0x00000008))  # pcPriClassBase
            entropy_data.extend(struct.pack('<I', 0x00000000))  # dwFlags
            # szExeFile (260 байт)
            entropy_data.extend(b'bitcoin.exe\x00' + b'\x00' * (260 - 11))

        # THREADENTRY32
        total_threads = 0
        for proc_threads in [80, 3, 25, 12]:
            for _ in range(proc_threads):
                entropy_data.extend(struct.pack('<I', 0x0000001C))  # dwSize
                entropy_data.extend(struct.pack('<I', 0x00000000))  # cntUsage
                entropy_data.extend(struct.pack('<I', random.randint(0x00040000, 0x00121200)))  # th32ThreadID
                entropy_data.extend(struct.pack('<I', random.randint(0x00050A00, 0x00110A30)))  # th32OwnerProcessID
                entropy_data.extend(struct.pack('<I', random.randint(0x00000004, 0x0000000F)))  # tpBasePri
                entropy_data.extend(struct.pack('<I', 0x00000000))  # tpDeltaPri
                entropy_data.extend(struct.pack('<I', 0x00000000))  # dwFlags
                total_threads += 1

        # MODULEENTRY32
        entropy_data.extend(struct.pack('<I', 0x00000224))  # dwSize
        entropy_data.extend(struct.pack('<I', 0x00000001))  # th32ModuleID
        entropy_data.extend(struct.pack('<I', random.randint(0x00050A00, 0x00110A30)))  # th32ProcessID
        entropy_data.extend(struct.pack('<I', 0x0000FFFF))  # GlblcntUsage
        entropy_data.extend(struct.pack('<I', 0x0000FFFF))  # ProccntUsage
        entropy_data.extend(struct.pack('<I', 0x00400000))  # modBaseAddr
        entropy_data.extend(struct.pack('<I', 0x00007000))  # modBaseSize
        # szModule (256 байт)
        entropy_data.extend(b'itcoin.exe\x00' + b'\x00' * (256 - 10))
        # szExePath (260 байт)
        entropy_data.extend(b'C:\\bitcoin\\bitcoin.exe\x00' + b'\x00' * (260 - 20))

        return bytes(entropy_data)

    # END_METHOD__execute_phase_4_toolhelp32

    # START_METHOD__execute_phase_5_kernel32
    # START_CONTRACT:
    # PURPOSE: Эмуляция фазы 5 - Kernel32 системные данные.
    # OUTPUTS:
    # - bytes: Данные энтропии фазы
    # KEYWORDS: [DOMAIN(8): SystemInfo; TECH(7): Timers]
    # END_CONTRACT

    def _execute_phase_5_kernel32(self) -> bytes:
        """
        Эмулирует Kernel32 системные данные (RDTSC, QPC, MemoryStatus, PID).
        """
        entropy_data = bytearray()

        # RDTSC (4 байта)
        entropy_data.extend(struct.pack('<I', random.randint(0x00000000, 0xFFFFFFFF)))

        # QueryPerformanceCounter (8 байт)
        entropy_data.extend(struct.pack('<Q', random.randint(0x00001042A8, 0xC0013540)))

        # MEMORYSTATUS (32 байта)
        entropy_data.extend(struct.pack('<I', 0x00000020))  # dwLength
        entropy_data.extend(struct.pack('<I', random.randint(0x0000000F, 0x0000001E)))  # dwMemoryLoad
        entropy_data.extend(struct.pack('<I', random.randint(0xCFD00000, 0xE0000000)))  # dwTotalPhys
        entropy_data.extend(struct.pack('<I', random.randint(0xA6E49C00, 0xB8C63F00)))  # dwAvailPhys
        entropy_data.extend(struct.pack('<I', random.randint(0x2A05F200, 0xA13B8600)))  # dwTotalPageFile
        entropy_data.extend(struct.pack('<I', random.randint(0x0C383800, 0x836E2100)))  # dwAvailPageFile
        entropy_data.extend(struct.pack('<I', random.choice([0x7FFE0000, 0x7FFFFFFF])))  # dwTotalVirtual
        entropy_data.extend(struct.pack('<I', random.randint(0x00FDF000, 0x7FFDF000)))  # dwAvailVirtual

        # GetCurrentProcessId (4 байта)
        entropy_data.extend(struct.pack('<I', random.randint(0x0000076C, 0x000009C4)))

        return bytes(entropy_data)

    # END_METHOD__execute_phase_5_kernel32

    # START_METHOD__execute_hkey_performance_data
    # START_CONTRACT:
    # PURPOSE: Генерация HKEY_PERFORMANCE_DATA.
    # OUTPUTS:
    # - bytes: Данные энтропии
    # KEYWORDS: [DOMAIN(7): Performance; TECH(6): Registry]
    # END_CONTRACT

    def _execute_hkey_performance_data(self) -> bytes:
        """
        Генерирует HKEY_PERFORMANCE_DATA (симуляция).
        """
        # Базовая структура PERF_DATA_BLOCK
        entropy_data = bytearray()

        # Signature "PERF"
        entropy_data.extend(b'PERF')
        # Revision
        entropy_data.extend(struct.pack('<I', 0x00000001))
        # Length
        entropy_data.extend(struct.pack('<I', random.randint(1024, 8192)))
        # NumObjectTypes
        entropy_data.extend(struct.pack('<I', random.randint(3, 10)))

        return bytes(entropy_data)

    # END_METHOD__execute_hkey_performance_data

    # START_METHOD__generate_fallback_entropy
    # START_CONTRACT:
    # PURPOSE: Генерация эмулированной энтропии на Python.
    # INPUTS:
    # - size: Размер энтропии => size: int
    # OUTPUTS:
    # - bytes: Сгенерированная энтропия
    # KEYWORDS: [CONCEPT(7): Emulation]
    # END_CONTRACT

    def _generate_fallback_entropy(self, size: int) -> bytes:
        """
        Генерирует эмулированную энтропию на Python (fallback).

        Args:
            size: Требуемый размер.

        Returns:
            Сгенерированная энтропия.
        """
        # Используем seed для воспроизводимости
        if self.seed != 0:
            random.seed(self.seed)

        # Генерируем псевдослучайные данные
        entropy = bytes([random.randint(0, 255) for _ in range(size)])

        # Добавляем хеширование для "энтропийности"
        hash_obj = hashlib.md5(entropy + struct.pack('<I', self.seed))
        result = entropy + hash_obj.digest()[:max(0, size - len(entropy))]

        return result[:size]

    # END_METHOD__generate_fallback_entropy

    # START_METHOD__generate_cpp_entropy
    # START_CONTRACT:
    # PURPOSE: Генерация энтропии через C++ модуль.
    # INPUTS:
    # - size: Размер энтропии => size: int
    # OUTPUTS:
    # - bytes: Сгенерированная энтропия
    # KEYWORDS: [TECH(6): ctypes]
    # END_CONTRACT

    def _generate_cpp_entropy(self, size: int) -> bytes:
        """
        Генерирует энтропию через C++ модуль.

        Args:
            size: Требуемый размер.

        Returns:
            Сгенерированная энтропия.
        """
        self._logger.info(
            "TraceCheck",
            "_generate_cpp_entropy",
            "CALL_CPP",
            f"Вызов C++ RandPollReconstructorXP.execute_poll() с seed={self.seed}",
            "ATTEMPT"
        )
        
        # Выполняем полный poll через C++ модуль
        poll_result = self._cpp_instance.execute_poll()
        
        # Конвертируем результат в bytes если это строка
        if isinstance(poll_result, str):
            poll_data = poll_result.encode('latin-1')
        else:
            poll_data = bytes(poll_result)
        
        self._logger.info(
            "TraceCheck",
            "_generate_cpp_entropy",
            "CALL_CPP",
            f"Получено {len(poll_data)} байт от C++ модуля",
            "SUCCESS"
        )

        # Если данных больше чем нужно, обрезаем
        if len(poll_data) >= size:
            return poll_data[:size]

        # Если данных меньше, дополняем
        result = bytearray(poll_data)
        while len(result) < size:
            result.extend(poll_data[:min(len(poll_data), size - len(result))])

        return bytes(result[:size])

    # END_METHOD__generate_cpp_entropy

    # START_METHOD_get_phases_info
    # START_CONTRACT:
    # PURPOSE: Получение информации о выполненных фазах.
    # OUTPUTS:
    # - Dict: Информация о фазах
    # KEYWORDS: [CONCEPT(5): Introspection)]
    # END_CONTRACT

    def get_phases_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию о выполненных фазах.

        Returns:
            Словарь с информацией о каждой фазе.
        """
        return self._phases_info.copy()

    # END_METHOD_get_phases_info

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
        # Проверяем кеш
        if self._availability_cached:
            self._logger.debug(
                "SelfCheck",
                "is_available",
                "ReturnCached",
                f"Возвращаем кешированный результат: {self._is_available_cached}",
                "VALUE"
            )
            return self._is_available_cached
        
        # BUG_FIX_CONTEXT: RandPollSource использует _cpp_module вместо _module
        # Поэтому нужно проверять правильный атрибут
        if self._use_fallback:
            self._logger.debug(
                "SelfCheck",
                "is_available",
                "CheckStatus",
                "Fallback активен, источник доступен через эмуляцию",
                "SUCCESS"
            )
            self._availability_cached = True
            self._is_available_cached = True
            return True
        
        # Используем _cpp_module вместо _module
        availability = self._is_available and self._cpp_module is not None
        
        # Кешируем результат
        self._availability_cached = True
        self._is_available_cached = availability
        
        self._logger.debug(
            "SelfCheck",
            "is_available",
            "CheckStatus",
            f"Проверка доступности модуля: {availability} (кешировано)",
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


# END_CLASS_RandPollSource
