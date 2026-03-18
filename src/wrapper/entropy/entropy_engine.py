# FILE: wrapper/entropy/entropy_engine.py
# VERSION: 3.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Координация источников энтропии на базе C++ биндингов.
# C++ модуль является ОБЯЗАТЕЛЬНЫМ - без него система не работает.
# SCOPE: Управление источниками, координация, комбинирование энтропии, C++ интеграция
# INPUT: Нет (значения передаются в методы)
# OUTPUT: Класс EntropyEngine с методами координации источников
# KEYWORDS: [DOMAIN(10): EntropyCoordination; CONCEPT(9): SourceManagement; CONCEPT(8): EntropyCombining; TECH(7): CppBinding]
# LINKS: [USES(10): wrapper.core.base; USES(9): wrapper.core.exceptions; USES(8): wrapper.core.logger]
# LINKS_TO_SPECIFICATION: ["Задача: C++ EntropyEngine - ТОЛЬКО C++"]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 10 [Координатор источников энтропии на базе C++] => EntropyEngine
# METHOD 9 [Добавляет источник энтропии] => add_source
# METHOD 8 [Удаляет источник энтропии по имени] => remove_source
# METHOD 9 [Возвращает список доступных источников] => get_available_sources
# METHOD 10 [Получает энтропию от указанного источника] => get_entropy
# METHOD 10 [Генерирует полную энтропию из всех источников] => generate_full_entropy
# METHOD 10 [Получает комбинированную энтропию из всех источников] => get_combined_entropy
# METHOD 8 [Возвращает статус всех источников] => get_source_status
# CONST 5 [Тип источника: RandPoll] => SOURCE_RAND_POLL
# CONST 5 [Тип источника: Bitmap] => SOURCE_BITMAP
# CONST 5 [Тип источника: HKey] => SOURCE_HKEY
# CONST 5 [Тип источника: Full (все источники)] => SOURCE_FULL
# CONST 5 [Стратегия XOR для комбинирования] => STRATEGY_XOR
# CONST 5 [Стратегия HASH для комбинирования] => STRATEGY_HASH
# END_MODULE_MAP
# START_USE_CASES:
# - [EntropyEngine.__init__]: System (Initialize) -> LoadCppOrFail -> EngineReady
# - [EntropyEngine.get_entropy]: User (GenerateEntropy) -> RequestFromCppSource -> EntropyReturned
# - [EntropyEngine.generate_full_entropy]: User (GenerateFullEntropy) -> CombineAllSources -> FullEntropyReturned
# - [EntropyEngine.get_combined_entropy]: User (CombineEntropy) -> CombineAll -> CombinedEntropyReturned
# END_USE_CASES
"""
Модуль EntropyEngine - координатор источников энтропии на базе C++ биндингов.

Класс EntropyEngine работает ТОЛЬКО с C++ модулями.

Основные возможности:
    - Использование C++ биндингов (ОБЯЗАТЕЛЬНО)
    - Поддержка 3 источников энтропии: RandPoll, Bitmap, HKey
    - Генерация полной энтропии (все 3 источника)
    - Поддержка стратегий комбинирования: XOR, HASH
    - Логирование всех операций
    Пример использования:
    engine = EntropyEngine()
    
    # Получить энтропию от конкретного источника
    entropy = engine.get_entropy("rand_poll", seed=12345)
    
    # Получить полную энтропию (все 3 источника)
    full_entropy = engine.generate_full_entropy(seed=12345)
    
    # Получить комбинированную энтропию
    combined = engine.get_combined_entropy(32, strategy="XOR")
"""
import os
import hashlib
from typing import Dict, List, Optional, Any

from src.wrapper.core.exceptions import EntropyGenerationError
from src.wrapper.core.logger import EntropyLogger

# Константы типов источников энтропии
SOURCE_RAND_POLL = "rand_poll"
SOURCE_BITMAP = "bitmap"
SOURCE_HKEY = "hkey"
SOURCE_FULL = "full"

# Список поддерживаемых типов источников
SUPPORTED_SOURCES = [SOURCE_RAND_POLL, SOURCE_BITMAP, SOURCE_HKEY, SOURCE_FULL]

# Константы стратегий комбинирования
STRATEGY_XOR = "XOR"
STRATEGY_HASH = "HASH"

# Список поддерживаемых стратегий
SUPPORTED_STRATEGIES = [STRATEGY_XOR, STRATEGY_HASH]

# Путь к C++ модулю по умолчанию
DEFAULT_CPP_MODULE_PATH = "lib/entropy_engine_cpp.cpython-310-x86_64-linux-gnu.so"


# START_CLASS_EntropyEngine
# START_CONTRACT:
# PURPOSE: Координатор источников энтропии на базе C++ биндингов.
# ATTRIBUTES:
# - _cpp_engine: Optional - C++ EntropyEngine из биндингов
# - _logger: logging.Logger - Логгер для класса
# - _seed: int - Seed для воспроизводимости
# METHODS:
# - __init__(cpp_module_path: str = None, seed: int = 0) -> None: Инициализация с C++ модулем
# - get_entropy(source_type: str, seed: int = None) -> bytes: Получение энтропии от источника
# - generate_full_entropy(seed: int = None) -> bytes: Генерация полной энтропии (RandPoll + Bitmap + HKey)
# - add_source(source: Any) -> None: Добавление источника
# - remove_source(source_name: str) -> None: Удаление источника
# - get_available_sources() -> List[str]: Получение списка доступных источников
# - get_combined_entropy(size: int, strategy: str = 'XOR') -> bytes: Комбинирование энтропии
# - get_source_status() -> Dict[str, Any]: Получение статуса источников
# KEYWORDS: [DOMAIN(10): EntropyCoordination; CONCEPT(9): CppBinding; CONCEPT(8): SourceManagement]
# LINKS: [USES(10): wrapper.core.exceptions; USES(8): wrapper.core.logger]
# END_CONTRACT


class EntropyEngine:
    """
    Координатор источников энтропии на базе C++ биндингов.

    Этот класс работает ТОЛЬКО с C++ модулями.
    """

    # Кеш для загруженного C++ модуля (уровень класса)
    _cpp_module_cache = None
    _cpp_engine_cache = None
    _cpp_module_path_cache = None

    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация координатора источников энтропии на базе C++ биндингов.
    # INPUTS:
    # - cpp_module_path: Путь к C++ модулю (опционально) => cpp_module_path: str | None
    # - seed: Начальное значение для генератора => seed: int
    # OUTPUTS:
    # - None
    # SIDE_EFFECTS:
    # - Загружает C++ биндинги или выбрасывает исключение
    # - Устанавливает seed для воспроизводимости
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - C++ модуль загружен успешно
    # - Логгер настроен
    # - Seed установлен корректно
    # KEYWORDS: [CONCEPT(5): Initialization; CONCEPT(4): CppBinding]
    # END_CONTRACT

    def __init__(
        self,
        cpp_module_path: Optional[str] = None,
        seed: int = 0
    ) -> None:
        """
        Инициализирует EntropyEngine с C++ биндингами.

        Args:
            cpp_module_path: Путь к C++ модулю. Если None, используется путь по умолчанию.
            seed: Начальное значение для генератора случайных чисел.

        Raises:
            EntropyGenerationError: Если C++ модуль не загружен.
        """
        self._cpp_engine = None
        self._seed = seed
        self._sources: Dict[str, Any] = {}
        
        # Инициализация логгера
        self._logger = EntropyLogger(__name__)

        self._logger.info(
            "InitCheck",
            "__init__",
            "Initialize",
            f"Инициализация EntropyEngine с seed={seed}",
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
            self._seed = 0

        # Загружаем C++ модуль
        self._cpp_module = None
        self._cpp_engine_instance = None
        if not self._lazy_load_cpp_module(cpp_module_path):
            error_msg = "C++ модуль не загружен - это критическая ошибка"
            self._logger.error(
                "CriticalError",
                "__init__",
                "LoadCpp",
                error_msg,
                "FAIL"
            )
            raise EntropyGenerationError("C++ модуль недоступен", error_msg)

        self._logger.info(
            "InitCheck",
            "__init__",
            "Initialize",
            f"EntropyEngine инициализирован с C++ модулем",
            "SUCCESS"
        )

    # END_METHOD___init__

    # START_METHOD__lazy_load_cpp_module
    # START_CONTRACT:
    # PURPOSE: Lazy загрузка C++ модуля с использованием кеша на уровне класса.
    # INPUTS:
    # - module_path: Путь к модулю => module_path: str | None
    # OUTPUTS:
    # - bool: True если модуль загружен успешно
    # KEYWORDS: [CONCEPT(5): CppBinding; TECH(4): LazyLoading; CONCEPT(5): Caching]
    # END_CONTRACT

    def _lazy_load_cpp_module(self, module_path: Optional[str] = None) -> bool:
        """
        Lazy загрузка C++ модуля с кешированием на уровне класса.

        Args:
            module_path: Путь к модулю.

        Returns:
            True если модуль загружен успешно.
        """
        self._logger.info(
            "LibCheck",
            "_lazy_load_cpp_module",
            "LazyLoad",
            "Попытка загрузки C++ биндингов",
            "ATTEMPT"
        )

        # Разрешаем путь к модулю
        full_path = self._resolve_cpp_module_path(module_path)
        
        if full_path is None or not os.path.exists(full_path):
            self._logger.error(
                "LibCheck",
                "_lazy_load_cpp_module",
                "ModuleNotFound",
                f"C++ модуль не найден: {full_path}",
                "FAIL"
            )
            return False

        # Проверяем: если путь тот же и модуль уже загружен в кеш - используем кеш
        if (EntropyEngine._cpp_module_cache is not None and 
            EntropyEngine._cpp_module_path_cache == full_path and
            EntropyEngine._cpp_engine_cache is not None):
            
            self._logger.info(
                "LibCheck",
                "_lazy_load_cpp_module",
                "UseCache",
                f"Использование кешированного C++ модуля: {full_path}",
                "SUCCESS"
            )
            
            # Используем кешированный модуль
            self._cpp_module = EntropyEngine._cpp_module_cache
            self._cpp_engine_instance = EntropyEngine._cpp_engine_cache
            return True

        # Модуль не в кеше - загружаем
        load_success = self._try_load_cpp_module(full_path)
        
        if load_success:
            # Сохраняем в кеш уровня класса
            EntropyEngine._cpp_module_cache = self._cpp_module
            EntropyEngine._cpp_engine_cache = self._cpp_engine
            EntropyEngine._cpp_module_path_cache = full_path
            
            self._cpp_engine_instance = self._cpp_engine
            
            self._logger.info(
                "LibCheck",
                "_lazy_load_cpp_module",
                "CacheUpdate",
                f"C++ модуль добавлен в кеш: {full_path}",
                "SUCCESS"
            )
        
        return load_success

    # END_METHOD__lazy_load_cpp_module

    # START_METHOD__try_load_cpp_module
    # START_CONTRACT:
    # PURPOSE: Попытка загрузки C++ модуля биндингов.
    # INPUTS:
    # - module_path: Путь к модулю => module_path: str | None
    # OUTPUTS:
    # - bool: True если модуль загружен успешно
    # KEYWORDS: [CONCEPT(5): CppBinding; TECH(4): DynamicLoading]
    # END_CONTRACT

    def _try_load_cpp_module(self, module_path: Optional[str] = None) -> bool:
        """
        Пытается загрузить C++ модуль биндингов.

        Args:
            module_path: Путь к модулю.

        Returns:
            True если модуль загружен успешно.
        """
        self._logger.info(
            "LibCheck",
            "_try_load_cpp_module",
            "LoadModule",
            "Попытка загрузки C++ биндингов",
            "ATTEMPT"
        )

        try:
            # Разрешаем путь к модулю
            full_path = self._resolve_cpp_module_path(module_path)
            
            if full_path is None or not os.path.exists(full_path):
                self._logger.error(
                    "LibCheck",
                    "_try_load_cpp_module",
                    "ModuleNotFound",
                    f"C++ модуль не найден: {full_path}",
                    "FAIL"
                )
                return False

            # Пробуем импортировать модуль
            import importlib.util
            spec = importlib.util.spec_from_file_location("entropy_engine_cpp", full_path)
            if spec is None or spec.loader is None:
                raise ImportError("Не удалось создать spec для модуля")

            self._cpp_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self._cpp_module)

            # Проверяем наличие класса EntropyEngine
            if not hasattr(self._cpp_module, 'EntropyEngine'):
                raise AttributeError("Модуль не содержит класса EntropyEngine")

            # Создаём экземпляр C++ движка
            self._cpp_engine = self._cpp_module.EntropyEngine()

            self._logger.info(
                "LibCheck",
                "_try_load_cpp_module",
                "LoadSuccess",
                f"C++ биндинги загружены успешно: {full_path}",
                "SUCCESS"
            )
            return True

        except Exception as e:
            self._logger.error(
                "CriticalError",
                "_try_load_cpp_module",
                "LoadFailed",
                f"Не удалось загрузить C++ модуль: {str(e)}",
                "FAIL"
            )
            self._cpp_engine = None
            return False

    # END_METHOD__try_load_cpp_module

    # START_METHOD__resolve_cpp_module_path
    # START_CONTRACT:
    # PURPOSE: Разрешение пути к C++ модулю.
    # INPUTS:
    # - module_path: Относительный или абсолютный путь => module_path: str | None
    # OUTPUTS:
    # - str | None: Полный путь к модулю или None
    # KEYWORDS: [CONCEPT(5): PathResolution]
    # END_CONTRACT

    def _resolve_cpp_module_path(self, module_path: Optional[str] = None) -> Optional[str]:
        """
        Разрешает путь к C++ модулю.

        Args:
            module_path: Путь к модулю.

        Returns:
            Полный путь к модулю или None.
        """
        if module_path is None:
            module_path = DEFAULT_CPP_MODULE_PATH

        if os.path.isabs(module_path) and os.path.exists(module_path):
            return module_path

        # Проверяем относительно текущей директории
        if os.path.exists(module_path):
            return os.path.abspath(module_path)

        # Проверяем в директории lib
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        lib_path = os.path.join(project_root, module_path)
        if os.path.exists(lib_path):
            return lib_path

        # Проверяем стандартные пути
        standard_paths = [
            os.path.join(project_root, "lib", "entropy_engine_cpp.cpython-310-x86_64-linux-gnu.so"),
            os.path.join(project_root, "build", "compilation", "entropy_engine_cpp.cpython-310-x86_64-linux-gnu.so"),
        ]
        for path in standard_paths:
            if os.path.exists(path):
                return path

        return None

    # END_METHOD__resolve_cpp_module_path

    # START_METHOD_get_entropy
    # START_CONTRACT:
    # PURPOSE: Получение энтропии от указанного источника через C++.
    # INPUTS:
    # - source_type: Тип источника энтропии => source_type: str
    # - seed: Опциональный seed для генерации => seed: int | None
    # OUTPUTS:
    # - bytes: Сгенерированная энтропия
    # SIDE_EFFECTS:
    # - Вызов метода get_entropy у C++ модуля
    # - Генерирует исключение при ошибке
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - Возвращает bytes
    # - Поддерживаемые типы: rand_poll, bitmap, hkey, full
    # - Генерирует исключение при некорректном типе источника
    # KEYWORDS: [DOMAIN(10): EntropyGeneration; CONCEPT(8): SourceAccess]
    # LINKS_TO_SPECIFICATION: ["Требование: Реализовать метод get_entropy(source_type: str, seed: int = None) -> bytes"]
    # END_CONTRACT

    def get_entropy(self, source_type: str, seed: Optional[int] = None) -> bytes:
        """
        Получает энтропию от указанного источника через C++ модуль.

        Args:
            source_type: Тип источника энтропии. Доступны: "rand_poll", "bitmap", "hkey", "full".
            seed: Опциональный seed для генерации. Если None, используется seed из конструктора.

        Returns:
            Сгенерированная энтропия в виде байтов.

        Raises:
            EntropyGenerationError: Если тип источника не поддерживается или произошла ошибка.
        """
        # START_BLOCK_VALIDATE_SOURCE_TYPE: [Валидация типа источника.]
        self._logger.info(
            "TraceCheck",
            "get_entropy",
            "ValidateSourceType",
            f"Запрос энтропии от источника: {source_type}, seed: {seed}",
            "ATTEMPT"
        )

        if source_type not in SUPPORTED_SOURCES:
            error_msg = f"Неподдерживаемый тип источника: {source_type}. Поддерживаются: {SUPPORTED_SOURCES}"
            self._logger.error(
                "VarCheck",
                "get_entropy",
                "ValidateSourceType",
                error_msg,
                "FAIL"
            )
            raise EntropyGenerationError(error_msg)
        # END_BLOCK_VALIDATE_SOURCE_TYPE

        # Применяем seed если передан
        effective_seed = seed if seed is not None else self._seed

        # START_BLOCK_GET_ENTROPY: [Получение энтропии от C++ источника.]
        try:
            cpp_engine = self._cpp_engine_instance if self._cpp_engine_instance is not None else self._cpp_engine
            
            source_map = {
                SOURCE_RAND_POLL: "rand_poll",
                SOURCE_BITMAP: "bitmap",
                SOURCE_HKEY: "hkey",
            }
            cpp_source_name = source_map.get(source_type, source_type)
            
            entropy = cpp_engine.get_entropy(32, cpp_source_name)

            self._logger.info(
                "TraceCheck",
                "get_entropy",
                "GetEntropy",
                f"Получено {len(entropy)} байт энтропии от {source_type}",
                "SUCCESS"
            )
            return entropy

        except Exception as e:
            self._logger.error(
                "CriticalError",
                "get_entropy",
                "GetEntropy",
                f"Ошибка получения энтропии от {source_type}: {str(e)}",
                "FAIL"
            )
            raise EntropyGenerationError(f"Ошибка получения энтропии от {source_type}", str(e))
        # END_BLOCK_GET_ENTROPY

    # END_METHOD_get_entropy

    # START_METHOD_generate_full_entropy
    # START_CONTRACT:
    # PURPOSE: Генерация полной энтропии из всех трёх источников через C++.
    # INPUTS:
    # - seed: Опциональный seed для генерации => seed: int | None
    # OUTPUTS:
    # - bytes: Объединённая энтропия от всех источников (порядок: RandPoll -> Bitmap -> HKey)
    # SIDE_EFFECTS:
    # - Вызывает get_entropy для каждого источника
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - Возвращает bytes
    # - Порядок: RandPoll -> Bitmap -> HKey
    # - Генерирует исключение если ни один источник недоступен
    # KEYWORDS: [DOMAIN(10): EntropyGeneration; CONCEPT(9): FullEntropy; CONCEPT(8): Combining]
    # LINKS_TO_SPECIFICATION: ["Требование: Реализовать метод generate_full_entropy(seed: int = None) -> bytes"]
    # END_CONTRACT

    def generate_full_entropy(self, seed: Optional[int] = None) -> bytes:
        """
        Генерирует полную энтропию из всех трёх источников через C++ модуль.

        Порядок источников:
            1. RandPoll
            2. Bitmap
            3. HKey

        Args:
            seed: Опциональный seed для генерации. Если None, используется seed из конструктора.

        Returns:
            Объединённая энтропия от всех источников в виде байтов.

        Raises:
            EntropyGenerationError: Если ни один источник недоступен.
        """
        # START_BLOCK_VALIDATE_SOURCES: [Проверка доступности источников.]
        self._logger.info(
            "TraceCheck",
            "generate_full_entropy",
            "ValidateSources",
            f"Генерация полной энтропии, seed: {seed}",
            "ATTEMPT"
        )
        # END_BLOCK_VALIDATE_SOURCES

        # START_BLOCK_COLLECT_ENTROPY: [Сбор энтропии от всех источников.]
        entropy_parts: List[bytes] = []

        # Порядок: RandPoll -> Bitmap -> HKey
        source_order = [SOURCE_RAND_POLL, SOURCE_BITMAP, SOURCE_HKEY]

        for src_type in source_order:
            try:
                self._logger.debug(
                    "TraceCheck",
                    "generate_full_entropy",
                    "CollectEntropy",
                    f"Получение энтропии от {src_type}",
                    "ATTEMPT"
                )

                entropy = self.get_entropy(src_type)
                entropy_parts.append(entropy)

                self._logger.debug(
                    "TraceCheck",
                    "generate_full_entropy",
                    "CollectEntropy",
                    f"Получено {len(entropy)} байт от {src_type}",
                    "SUCCESS"
                )

            except Exception as e:
                self._logger.error(
                    "CriticalError",
                    "generate_full_entropy",
                    "CollectEntropy",
                    f"Ошибка получения энтропии от {src_type}: {str(e)}",
                    "FAIL"
                )
                raise EntropyGenerationError(f"Ошибка получения энтропии от {src_type}", str(e))

        if not entropy_parts:
            error_msg = "Не удалось получить энтропию ни от одного источника"
            self._logger.error(
                "CriticalError",
                "generate_full_entropy",
                "CollectEntropy",
                error_msg,
                "FAIL"
            )
            raise EntropyGenerationError("generate_full_entropy", error_msg)

        self._logger.info(
            "TraceCheck",
            "generate_full_entropy",
            "CollectEntropy",
            f"Получена энтропия от {len(entropy_parts)} источников",
            "SUCCESS"
        )
        # END_BLOCK_COLLECT_ENTROPY

        # START_BLOCK_COMBINE_ENTROPY: [Объединение энтропии.]
        combined_entropy = b"".join(entropy_parts)

        self._logger.info(
            "TraceCheck",
            "generate_full_entropy",
            "CombineEntropy",
            f"Полная энтропия сгенерирована: {len(combined_entropy)} байт",
            "SUCCESS"
        )

        return combined_entropy
        # END_BLOCK_COMBINE_ENTROPY

    # END_METHOD_generate_full_entropy

    # START_METHOD_add_source
    # START_CONTRACT:
    # PURPOSE: Добавление источника энтропии в координатор.
    # INPUTS:
    # - source: Источник энтропии для добавления => source: Any
    # OUTPUTS:
    # - None
    # KEYWORDS: [DOMAIN(9): SourceManagement; CONCEPT(7): Registration]
    # END_CONTRACT

    def add_source(self, source: Any) -> None:
        """
        Добавляет источник энтропии в координатор.

        Args:
            source: Источник энтропии для добавления.
        """
        source_name = source.__class__.__name__

        self._logger.info(
            "TraceCheck",
            "add_source",
            "ADD_SOURCE",
            f"Добавление источника: {source_name}",
            "ATTEMPT"
        )

        self._sources[source_name] = source

        self._logger.info(
            "TraceCheck",
            "add_source",
            "ADD_SOURCE",
            f"Источник {source_name} добавлен успешно",
            "SUCCESS"
        )

    # END_METHOD_add_source

    # START_METHOD_remove_source
    # START_CONTRACT:
    # PURPOSE: Удаление источника энтропии из координатора.
    # INPUTS:
    # - source_name: Имя источника для удаления => source_name: str
    # OUTPUTS:
    # - None
    # KEYWORDS: [DOMAIN(9): SourceManagement; CONCEPT(7): Deregistration]
    # END_CONTRACT

    def remove_source(self, source_name: str) -> None:
        """
        Удаляет источник энтропии из координатора.

        Args:
            source_name: Имя источника для удаления.
        """
        if source_name not in self._sources:
            error_msg = f"Источник {source_name} не найден"
            self._logger.error(
                "VarCheck",
                "remove_source",
                "VALIDATE_SOURCE_EXISTS",
                error_msg,
                "FAIL"
            )
            raise EntropyGenerationError(error_msg)

        del self._sources[source_name]

        self._logger.info(
            "TraceCheck",
            "remove_source",
            "REMOVE_SOURCE",
            f"Источник {source_name} удален успешно",
            "SUCCESS"
        )

    # END_METHOD_remove_source

    # START_METHOD_get_available_sources
    # START_CONTRACT:
    # PURPOSE: Получение списка доступных источников энтропии.
    # OUTPUTS:
    # - List[str]: Список имен доступных источников
    # KEYWORDS: [DOMAIN(8): SourceDiscovery; CONCEPT(6): Introspection]
    # END_CONTRACT

    def get_available_sources(self) -> List[str]:
        """
        Возвращает список доступных источников энтропии.

        Returns:
            Список имен источников, которые доступны и инициализированы.
        """
        available = ["cpp_engine"]
        return available

    # END_METHOD_get_available_sources

    # START_METHOD_get_combined_entropy
    # START_CONTRACT:
    # PURPOSE: Получение комбинированной энтропии из всех доступных источников.
    # INPUTS:
    # - size: Требуемый размер энтропии в байтах => size: int
    # - strategy: Стратегия комбинирования (XOR, HASH) => strategy: str
    # OUTPUTS:
    # - bytes: Комбинированная энтропия
    # KEYWORDS: [DOMAIN(10): EntropyCombining; CONCEPT(9): Aggregation; CONCEPT(8): XOR; CONCEPT(8): Hashing]
    # END_CONTRACT

    def get_combined_entropy(self, size: int, strategy: str = STRATEGY_XOR) -> bytes:
        """
        Получает комбинированную энтропию из всех доступных источников через C++.

        Args:
            size: Требуемый размер энтропии в байтах.
            strategy: Стратегия комбинирования (XOR, HASH).

        Returns:
            Комбинированная энтропия в виде байтов.

        Raises:
            EntropyGenerationError: Если стратегия не поддерживается.
        """
        # START_BLOCK_VALIDATE_STRATEGY: [Валидация стратегии комбинирования.]
        self._logger.info(
            "TraceCheck",
            "get_combined_entropy",
            "COMBINE_ENTROPY",
            f"Запрос комбинированной энтропии размером {size} со стратегией {strategy}",
            "ATTEMPT"
        )

        if strategy not in SUPPORTED_STRATEGIES:
            error_msg = f"Неподдерживаемая стратегия: {strategy}. Поддерживаются: {SUPPORTED_STRATEGIES}"
            self._logger.error(
                "VarCheck",
                "get_combined_entropy",
                "VALIDATE_STRATEGY",
                error_msg,
                "FAIL"
            )
            raise EntropyGenerationError(error_msg)
        # END_BLOCK_VALIDATE_STRATEGY

        # START_BLOCK_GET_COMBINED: [Получение комбинированной энтропии.]
        try:
            cpp_engine = self._cpp_engine_instance if self._cpp_engine_instance is not None else self._cpp_engine
            
            # Получаем CombineStrategy из C++ модуля
            cpp_strategy = self._cpp_module.CombineStrategy
            
            if strategy == STRATEGY_XOR:
                combined = cpp_engine.get_combined_entropy(size, cpp_strategy.XOR)
            else:
                combined = cpp_engine.get_combined_entropy(size, cpp_strategy.HASH)

            self._logger.info(
                "TraceCheck",
                "get_combined_entropy",
                "COMBINE_ENTROPY",
                f"Комбинированная энтропия создана: {len(combined)} байт, стратегия: {strategy}",
                "SUCCESS"
            )

            return combined

        except Exception as e:
            self._logger.error(
                "CriticalError",
                "get_combined_entropy",
                "COMBINE_ENTROPY",
                f"Ошибка комбинирования энтропии: {str(e)}",
                "FAIL"
            )
            raise EntropyGenerationError(f"Ошибка комбинирования энтропии", str(e))
        # END_BLOCK_GET_COMBINED

    # END_METHOD_get_combined_entropy

    # START_METHOD_get_source_status
    # START_CONTRACT:
    # PURPOSE: Получение статуса всех источников энтропии.
    # OUTPUTS:
    # - Dict[str, Any]: Словарь со статусами источников
    # KEYWORDS: [CONCEPT(6): Introspection; DOMAIN(8): StatusReporting]
    # END_CONTRACT

    def get_source_status(self) -> Dict[str, Any]:
        """
        Возвращает статус всех источников энтропии.

        Returns:
            Словарь со статусами источников, включая:
            - use_cpp: Всегда True
            - available: Количество доступных источников
            - total: Общее количество источников
        """
        cpp_engine = self._cpp_engine_instance if self._cpp_engine_instance is not None else self._cpp_engine
        source_count = cpp_engine.source_count()
        
        status: Dict[str, Any] = {
            "use_cpp": True,
            "available": source_count,
            "total": source_count,
            "sources": {
                "cpp_engine": {
                    "available": True
                }
            }
        }

        return status

    # END_METHOD_get_source_status

    # START_PROPERTY_use_cpp
    # START_CONTRACT:
    # PURPOSE: Свойство для проверки использования C++ биндингов.
    # OUTPUTS:
    # - bool: Всегда True
    # KEYWORDS: [PATTERN(5): Property; CONCEPT(4): CppBinding]
    # END_CONTRACT

    @property
    def use_cpp(self) -> bool:
        """
        Возвращает True - C++ используется всегда.

        Returns:
            True.
        """
        return True

    # END_PROPERTY_use_cpp


# END_CLASS_EntropyEngine
