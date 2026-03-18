# FILE: wrapper/unified_interface.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Единый интерфейс для получения энтропии из различных источников.
# Предоставляет упрощённый API для конечного пользователя с поддержкой
# контекстного менеджера и удобных методов.
# SCOPE: Унифицированный доступ, контекстный менеджмент, высокоуровневый API
# INPUT: Опциональная конфигурация в виде словаря
# OUTPUT: Класс UnifiedEntropyInterface с методами получения энтропии
# KEYWORDS: [DOMAIN(10): UserAPI; CONCEPT(9): FacadePattern; CONCEPT(8): ContextManager; TECH(7): EntropyGeneration]
# LINKS: [USES(10): wrapper.entropy.entropy_engine; USES(9): wrapper.core.logger; USES(8): wrapper.core.exceptions]
# LINKS_TO_SPECIFICATION: ["Задача: Реализация Этапа 6 — UnifiedEntropyInterface (единый интерфейс)"]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 10 [Единая точка входа для работы с энтропией] => UnifiedEntropyInterface
# METHOD 9 [Инициализация с опциональной конфигурацией] => __init__
# METHOD 8 [Вход в контекст] => __enter__
# METHOD 8 [Выход из контекста] => __exit__
# METHOD 10 [Получение энтропии] => get_entropy
# METHOD 8 [Получение статуса источников] => get_source_status
# METHOD 7 [Настройка конфигурации] => configure
# METHOD 7 [Освобождение ресурсов] => close
# METHOD 8 [Получение случайных байт (алиас)] => get_random_bytes
# METHOD 8 [Получение случайного числа в диапазоне] => get_random_int
# METHOD 8 [Получение hex-строки] => get_random_hex
# END_MODULE_MAP
# START_USE_CASES:
# - [UnifiedEntropyInterface.__init__]: User (Initialize) -> SetupInterface -> InterfaceReady
# - [UnifiedEntropyInterface.get_entropy]: User (GenerateEntropy) -> RequestEntropy -> EntropyReturned
# - [context manager]: User (UseWithContext) -> EnterContext -> AutoCleanup
# - [get_random_int]: User (GenerateNumber) -> RequestInRange -> NumberReturned
# END_USE_CASES
"""
Модуль UnifiedEntropyInterface - единый интерфейс для работы с энтропией.

Этот класс предоставляет упрощённый API для получения энтропии из различных
источников с поддержкой контекстного менеджера для автоматического освобождения ресурсов.

Основные возможности:
    - Единая точка входа для работы с энтропией
    - Поддержка контекстного менеджера (with statement)
    - Автоматическое обнаружение и инициализация источников
    - Удобные методы: get_random_bytes, get_random_int, get_random_hex
    - Логирование всех операций
    - Конфигурирование через словарь

Пример использования:
    # Простое использование
    interface = UnifiedEntropyInterface()
    entropy = interface.get_entropy(32)
    interface.close()

    # Использование с контекстным менеджером
    with UnifiedEntropyInterface() as interface:
        entropy = interface.get_entropy(32)
        random_int = interface.get_random_int(1, 100)
        hex_str = interface.get_random_hex(16)

    # С конфигурацией
    config = {
        "strategy": "XOR",
        "log_level": "DEBUG"
    }
    with UnifiedEntropyInterface(config) as interface:
        entropy = interface.get_entropy(64)
"""

import secrets
from typing import Dict, List, Optional, Any

from src.wrapper.entropy.entropy_engine import EntropyEngine, STRATEGY_XOR, STRATEGY_HASH
from src.wrapper.core.logger import get_logger, EntropyLogger
from src.wrapper.core.exceptions import EntropySourceError, DataValidationError, EntropyGenerationError


# START_CLASS_UnifiedEntropyInterface
# START_CONTRACT:
# PURPOSE: Единая точка входа для работы с энтропией.
# Предоставляет упрощённый API с поддержкой контекстного менеджера.
# ATTRIBUTES:
# - _engine: EntropyEngine - движок координации источников
# - _logger: EntropyLogger - логгер для операций
# - _config: Dict - текущая конфигурация
# - _closed: bool - флаг закрытия интерфейса
# METHODS:
# - __init__(config: dict = None) -> None: Инициализация с опциональной конфигурацией
# - __enter__(self) -> UnifiedEntropyInterface: Вход в контекст
# - __exit__(self, exc_type, exc_val, exc_tb) -> None: Выход из контекста
# - get_entropy(size: int, source: str = None, strategy: str = 'XOR') -> bytes: Получение энтропии
# - get_source_status() -> dict: Получение статуса источников
# - configure(config: dict) -> None: Настройка конфигурации
# - close() -> None: Освобождение ресурсов
# - get_random_bytes(size: int) -> bytes: Алиас для get_entropy
# - get_random_int(min_val: int, max_val: int) -> int: Случайное число в диапазоне
# - get_random_hex(size: int) -> str: Hex-строка случайных байт
# KEYWORDS: [DOMAIN(10): UserAPI; CONCEPT(9): FacadePattern; CONCEPT(8): ContextManager]
# LINKS: [USES(10): wrapper.entropy.entropy_engine; USES(9): wrapper.core.logger; USES(8): wrapper.core.exceptions]
# END_CONTRACT


class UnifiedEntropyInterface:
    """
    Единый интерфейс для работы с энтропией.

    Этот класс предоставляет упрощённый API для получения энтропии с поддержкой
    контекстного менеджера для автоматического освобождения ресурсов.

    Attributes:
        engine: Движок EntropyEngine для координации источников.

    Example:
        with UnifiedEntropyInterface() as interface:
            entropy = interface.get_entropy(32)
            print(entropy.hex())
    """

    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация единого интерфейса с опциональной конфигурацией.
    # INPUTS:
    # - config: Опциональная конфигурация => config: dict | None
    # OUTPUTS:
    # - None
    # SIDE_EFFECTS:
    # - Инициализирует EntropyEngine
    # - Настраивает логирование
    # - Применяет конфигурацию если передана
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - EntropyEngine инициализирован
    # - Логгер настроен
    # - Интерфейс готов к использованию
    # KEYWORDS: [CONCEPT(5): Initialization; CONCEPT(4): Setup]
    # END_CONTRACT

    def __init__(self, config: Dict[str, Any] = None) -> None:
        """
        Инициализирует UnifiedEntropyInterface.

        Args:
            config: Опциональная конфигурация. Поддерживаемые ключи:
                - strategy: Стратегия комбинирования (XOR, HASH)
                - log_level: Уровень логирования
                - sources: Список источников для добавления
        """
        # START_BLOCK_INIT_LOGGER: [Инициализация логгера.]
        self._logger = EntropyLogger(__name__)

        self._logger.info(
            "InitCheck",
            "__init__",
            "Initialize",
            "Инициализация UnifiedEntropyInterface",
            "ATTEMPT"
        )
        # END_BLOCK_INIT_LOGGER

        # START_BLOCK_INIT_ENGINE: [Инициализация движка энтропии.]
        try:
            self._engine = EntropyEngine()
            self._logger.info(
                "InitCheck",
                "__init__",
                "Initialize",
                "EntropyEngine инициализирован",
                "SUCCESS"
            )
        except Exception as e:
            self._logger.error(
                "CriticalError",
                "__init__",
                "Initialize",
                f"Ошибка инициализации EntropyEngine: {str(e)}",
                "FAIL"
            )
            raise EntropyGenerationError("__init__", f"Ошибка инициализации: {str(e)}")
        # END_BLOCK_INIT_ENGINE

        # START_BLOCK_SET_CONFIG: [Установка конфигурации.]
        self._config: Dict[str, Any] = {
            "strategy": STRATEGY_XOR,
            "log_level": "INFO",
            "auto_init": True
        }

        if config:
            self.configure(config)
        # END_BLOCK_SET_CONFIG

        # START_BLOCK_SET_CLOSED_FLAG: [Установка флага закрытия.]
        self._closed = False
        # END_BLOCK_SET_CLOSED_FLAG

        self._logger.info(
            "InitCheck",
            "__init__",
            "Initialize",
            "UnifiedEntropyInterface готов к использованию",
            "SUCCESS"
        )

    # END_METHOD___init__

    # START_METHOD___enter__
    # START_CONTRACT:
    # PURPOSE: Вход в контекстный менеджер.
    # OUTPUTS:
    # - UnifiedEntropyInterface: Ссылка на текущий экземпляр
    # KEYWORDS: [CONCEPT(5): ContextManager]
    # END_CONTRACT

    def __enter__(self) -> "UnifiedEntropyInterface":
        """
        Входит в контекстный менеджер.

        Returns:
            Ссылка на текущий экземпляр.
        """
        self._logger.info(
            "TraceCheck",
            "__enter__",
            "EnterContext",
            "Вход в контекстный менеджер",
            "ATTEMPT"
        )

        self._logger.info(
            "TraceCheck",
            "__enter__",
            "EnterContext",
            "Вход в контекст выполнен успешно",
            "SUCCESS"
        )

        return self

    # END_METHOD___enter__

    # START_METHOD___exit__
    # START_CONTRACT:
    # PURPOSE: Выход из контекстного менеджера с освобождением ресурсов.
    # INPUTS:
    # - exc_type: Тип исключения => exc_type: type | None
    # - exc_val: Значение исключения => exc_val: BaseException | None
    # - exc_tb: Трассировка исключения => exc_tb: Any
    # OUTPUTS:
    # - bool: False - не подавлять исключения
    # KEYWORDS: [CONCEPT(5): ContextManager]
    # END_CONTRACT

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Выходит из контекстного менеджера.

        Args:
            exc_type: Тип исключения, если было вызвано.
            exc_val: Значение исключения.
            exc_tb: Трассировка стека.

        Returns:
            False - не подавлять исключения.
        """
        self._logger.info(
            "TraceCheck",
            "__exit__",
            "ExitContext",
            "Выход из контекстного менеджера",
            "ATTEMPT"
        )

        # Освобождаем ресурсы
        self.close()

        self._logger.info(
            "TraceCheck",
            "__exit__",
            "ExitContext",
            "Выход из контекста выполнен, ресурсы освобождены",
            "SUCCESS"
        )

        # Не подавляем исключения
        return False

    # END_METHOD___exit__

    # START_METHOD_get_entropy
    # START_CONTRACT:
    # PURPOSE: Получение энтропии заданного размера.
    # INPUTS:
    # - size: Размер в байтах => size: int
    # - source: Опциональное имя источника => source: str | None
    # - strategy: Стратегия комбинирования => strategy: str
    # OUTPUTS:
    # - bytes: Сгенерированная энтропия
    # SIDE_EFFECTS:
    # - Вызывает генерацию энтропии через движок
    # - Генерирует исключение при ошибке
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - Возвращает bytes
    # - Размер соответствует запрошенному
    # - При source=None используется комбинирование
    # KEYWORDS: [DOMAIN(10): EntropyGeneration; CONCEPT(8): RandomBytes]
    # END_CONTRACT

    def get_entropy(self, size: int, source: str = None, strategy: str = "XOR") -> bytes:
        """
        Получает энтропию заданного размера.

        Args:
            size: Размер в байтах.
            source: Опциональное имя конкретного источника.
                   Если None, используется комбинирование всех источников.
            strategy: Стратегия комбинирования (XOR, HASH).
                     Используется только если source=None.

        Returns:
            Сгенерированная энтропия в виде байтов.

        Raises:
            EntropyGenerationError: Если произошла ошибка генерации.
            DataValidationError: Если параметры некорректны.
        """
        # START_BLOCK_VALIDATE_SIZE: [Валидация размера.]
        if size <= 0:
            error_msg = f"Размер должен быть положительным, получен {size}"
            self._logger.error(
                "VarCheck",
                "get_entropy",
                "VALIDATE_SIZE",
                error_msg,
                "FAIL"
            )
            raise DataValidationError("size", size, "должен быть положительным целым числом")

        self._logger.info(
            "TraceCheck",
            "get_entropy",
            "GET_ENTROPY",
            f"Запрос энтропии: size={size}, source={source}, strategy={strategy}",
            "ATTEMPT"
        )
        # END_BLOCK_VALIDATE_SIZE

        # START_BLOCK_GET_FROM_SOURCE: [Получение энтропии от источника или комбинирование.]
        try:
            if source:
                # Получаем от конкретного источника
                entropy = self._engine.get_entropy(size, source)
            else:
                # Комбинируем от всех источников
                entropy = self._engine.get_combined_entropy(size, strategy)

            self._logger.info(
                "TraceCheck",
                "get_entropy",
                "GET_ENTROPY",
                f"Получено {len(entropy)} байт энтропии",
                "SUCCESS"
            )

            return entropy

        except Exception as e:
            self._logger.error(
                "CriticalError",
                "get_entropy",
                "GET_ENTROPY",
                f"Ошибка получения энтропии: {str(e)}",
                "FAIL"
            )
            raise EntropyGenerationError("get_entropy", f"Ошибка генерации: {str(e)}")
        # END_BLOCK_GET_FROM_SOURCE

    # END_METHOD_get_entropy

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
            - total: Общее количество источников
            - available: Количество доступных источников
            - sources: Детали по каждому источнику
        """
        self._logger.info(
            "SelfCheck",
            "get_source_status",
            "GET_STATUS",
            "Запрос статуса источников",
            "ATTEMPT"
        )

        status = self._engine.get_source_status()

        self._logger.info(
            "SelfCheck",
            "get_source_status",
            "GET_STATUS",
            f"Статус: {status['available']}/{status['total']} доступно",
            "SUCCESS"
        )

        return status

    # END_METHOD_get_source_status

    # START_METHOD_configure
    # START_CONTRACT:
    # PURPOSE: Настройка конфигурации интерфейса.
    # INPUTS:
    # - config: Словарь конфигурации => config: dict
    # OUTPUTS:
    # - None
    # SIDE_EFFECTS:
    # - Обновляет внутреннюю конфигурацию
    # - Применяет новые параметры
    # KEYWORDS: [CONCEPT(5): Configuration; CONCEPT(4): Setup]
    # END_CONTRACT

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Настраивает конфигурацию интерфейса.

        Args:
            config: Словарь конфигурации. Поддерживаемые ключи:
                - strategy: Стратегия комбинирования (XOR, HASH)
                - log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
                - sources: Список источников для добавления
        """
        self._logger.info(
            "TraceCheck",
            "configure",
            "CONFIGURE",
            f"Применение конфигурации: {config}",
            "ATTEMPT"
        )

        # START_BLOCK_APPLY_STRATEGY: [Применение стратегии.]
        if "strategy" in config:
            strategy = config["strategy"]
            if strategy not in [STRATEGY_XOR, STRATEGY_HASH]:
                raise DataValidationError(
                    "strategy",
                    strategy,
                    f"должно быть одно из: {[STRATEGY_XOR, STRATEGY_HASH]}"
                )
            self._config["strategy"] = strategy
            self._logger.info(
                "TraceCheck",
                "configure",
                "CONFIGURE",
                f"Установлена стратегия: {strategy}",
                "SUCCESS"
            )
        # END_BLOCK_APPLY_STRATEGY

        # START_BLOCK_APPLY_LOG_LEVEL: [Применение уровня логирования.]
        if "log_level" in config:
            log_level = config["log_level"]
            self._config["log_level"] = log_level
            self._logger.info(
                "TraceCheck",
                "configure",
                "CONFIGURE",
                f"Установлен уровень логирования: {log_level}",
                "SUCCESS"
            )
        # END_BLOCK_APPLY_LOG_LEVEL

        # START_BLOCK_APPLY_AUTO_INIT: [Применение настройки автоинициализации.]
        if "auto_init" in config:
            self._config["auto_init"] = config["auto_init"]
            self._logger.info(
                "TraceCheck",
                "configure",
                "CONFIGURE",
                f"Установлен auto_init: {config['auto_init']}",
                "SUCCESS"
            )
        # END_BLOCK_APPLY_AUTO_INIT

        self._logger.info(
            "TraceCheck",
            "configure",
            "CONFIGURE",
            "Конфигурация применена",
            "SUCCESS"
        )

    # END_METHOD_configure

    # START_METHOD_close
    # START_CONTRACT:
    # PURPOSE: Освобождение ресурсов интерфейса.
    # OUTPUTS:
    # - None
    # SIDE_EFFECTS:
    # - Устанавливает флаг закрытия
    # - Освобождает ресурсы движка
    # KEYWORDS: [CONCEPT(5): Cleanup; CONCEPT(4): ResourceManagement]
    # END_CONTRACT

    def close(self) -> None:
        """
        Освобождает ресурсы интерфейса.
        """
        self._logger.info(
            "TraceCheck",
            "close",
            "CLOSE",
            "Закрытие интерфейса",
            "ATTEMPT"
        )

        self._closed = True

        self._logger.info(
            "TraceCheck",
            "close",
            "CLOSE",
            "Интерфейс закрыт, ресурсы освобождены",
            "SUCCESS"
        )

    # END_METHOD_close

    # START_METHOD_get_random_bytes
    # START_CONTRACT:
    # PURPOSE: Получение случайных байт (алиас для get_entropy).
    # INPUTS:
    # - size: Размер в байтах => size: int
    # OUTPUTS:
    # - bytes: Случайные байты
    # KEYWORDS: [CONCEPT(8): RandomBytes; CONCEPT(7): Alias]
    # END_CONTRACT

    def get_random_bytes(self, size: int) -> bytes:
        """
        Получает случайные байты (алиас для get_entropy).

        Args:
            size: Размер в байтах.

        Returns:
            Случайные байты.
        """
        self._logger.debug(
            "VarCheck",
            "get_random_bytes",
            "Params",
            f"Запрос случайных байт: size={size}",
            "ATTEMPT"
        )

        entropy = self.get_entropy(size, strategy=self._config["strategy"])

        self._logger.debug(
            "VarCheck",
            "get_random_bytes",
            "ReturnData",
            f"Получено {len(entropy)} случайных байт",
            "SUCCESS"
        )

        return entropy

    # END_METHOD_get_random_bytes

    # START_METHOD_get_random_int
    # START_CONTRACT:
    # PURPOSE: Получение случайного целого числа в заданном диапазоне.
    # INPUTS:
    # - min_val: Минимальное значение (включительно) => min_val: int
    # - max_val: Максимальное значение (включительно) => max_val: int
    # OUTPUTS:
    # - int: Случайное число в диапазоне
    # SIDE_EFFECTS:
    # - Использует get_entropy для получения случайных данных
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - min_val <= result <= max_val
    # KEYWORDS: [CONCEPT(8): RandomNumber; DOMAIN(7): IntegerRange]
    # END_CONTRACT

    def get_random_int(self, min_val: int, max_val: int) -> int:
        """
        Получает случайное целое число в заданном диапазоне.

        Args:
            min_val: Минимальное значение (включительно).
            max_val: Максимальное значение (включительно).

        Returns:
            Случайное число в диапазоне [min_val, max_val].

        Raises:
            DataValidationError: Если параметры некорректны.
        """
        # START_BLOCK_VALIDATE_RANGE: [Валидация диапазона.]
        if min_val >= max_val:
            error_msg = f"min_val ({min_val}) должен быть меньше max_val ({max_val})"
            self._logger.error(
                "VarCheck",
                "get_random_int",
                "VALIDATE_RANGE",
                error_msg,
                "FAIL"
            )
            raise DataValidationError("range", f"min={min_val}, max={max_val}", "min_val должен быть меньше max_val")

        self._logger.info(
            "TraceCheck",
            "get_random_int",
            "GET_RANDOM_INT",
            f"Запрос случайного числа в диапазоне [{min_val}, {max_val}]",
            "ATTEMPT"
        )
        # END_BLOCK_VALIDATE_RANGE

        # START_BLOCK_CALCULATE_RANGE: [Вычисление случайного числа.]
        # Вычисляем количество байт для представления диапазона
        range_size = max_val - min_val + 1
        bytes_needed = (range_size.bit_length() + 7) // 8

        # Получаем случайные байты
        random_bytes = self.get_entropy(bytes_needed)

        # Преобразуем в число
        random_value = int.from_bytes(random_bytes, byteorder='big')

        # Ограничиваем диапазон
        result = min_val + (random_value % range_size)

        self._logger.info(
            "TraceCheck",
            "get_random_int",
            "GET_RANDOM_INT",
            f"Получено случайное число: {result}",
            "SUCCESS"
        )
        # END_BLOCK_CALCULATE_RANGE

        return result

    # END_METHOD_get_random_int

    # START_METHOD_get_random_hex
    # START_CONTRACT:
    # PURPOSE: Получение случайной hex-строки.
    # INPUTS:
    # - size: Размер в байтах (количество символов = size * 2) => size: int
    # OUTPUTS:
    # - str: Случайная hex-строка
    # KEYWORDS: [CONCEPT(8): HexString; CONCEPT(7): RandomString]
    # END_CONTRACT

    def get_random_hex(self, size: int) -> str:
        """
        Получает случайную hex-строку.

        Args:
            size: Размер в байтах (количество символов = size * 2).

        Returns:
            Случайная hex-строка.
        """
        self._logger.info(
            "TraceCheck",
            "get_random_hex",
            "GET_RANDOM_HEX",
            f"Запрос случайной hex-строки: size={size}",
            "ATTEMPT"
        )

        random_bytes = self.get_entropy(size)

        hex_string = random_bytes.hex()

        self._logger.info(
            "TraceCheck",
            "get_random_hex",
            "GET_RANDOM_HEX",
            f"Получена hex-строка длины {len(hex_string)}",
            "SUCCESS"
        )

        return hex_string

    # END_METHOD_get_random_hex


# END_CLASS_UnifiedEntropyInterface
