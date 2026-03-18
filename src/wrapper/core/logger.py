# FILE: wrapper/core/logger.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Централизованная система логирования для Python-обёртки генерации энтропии.
# Обеспечивает единый формат логирования и запись в файл app.log в корне проекта.
# SCOPE: Логирование, отладка, мониторинг
# INPUT: Нет (модуль предоставляет функции и классы логирования)
# OUTPUT: Функции и классы для логирования: get_logger, EntropyLogger
# KEYWORDS: [DOMAIN(9): Logging; CONCEPT(7): LoggingSystem; TECH(5): Python_logging]
# LINKS: [USED_BY(8): wrapper.core.base; USES(7): logging]
# LINKS_TO_SPECIFICATION: ["Задача: Реализация Этапа 1 — Базовая инфраструктура Python-обёртки"]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# FUNC 10 [Создает и настраивает логгер с файловым обработчиком] => setup_logger
# FUNC 8 [Возвращает логгер для указанного имени модуля] => get_logger
# CLASS 9 [Класс-обёртка для логирования с дополнительными методами] => EntropyLogger
# END_MODULE_MAP
# START_USE_CASES:
# - [setup_logger]: System (Startup) -> ConfigureLogging -> LoggingReady
# - [get_logger]: Developer (Debug) -> GetModuleLogger -> LoggerAvailable
# - [EntropyLogger.log_phase]: System (GenerateEntropy) -> LogPhaseExecution -> PhaseLogged
# END_USE_CASES
"""
Модуль логирования для Python-обёртки генерации энтропии.

Формат лога: [CLASSIFIER][FUNC][BLOCK][OP] Description [STATUS]

Классификаторы:
    - VarCheck: Проверка переменных
    - SelfCheck: Самопроверка
    - CriticalError: Критическая ошибка
    - TempLog: Временное логирование
    - LibCheck: Проверка библиотек
    - TraceCheck: Трассировка выполнения
    - ConditionCheck: Проверка условий
    - InitCheck: Проверка инициализации
    - ReturnData: Возврат данных
    - CallExternal: Вызов внешнего сервиса

Статусы:
    - SUCCESS: Успешное выполнение
    - FAIL: Ошибка
    - ATTEMPT: Попытка
    - INFO: Информация
    - VALUE: Значение
    - ERROR_STATE: Состояние ошибки
"""
import logging
import os
from typing import Optional

# Константы для формата логирования
LOG_FORMAT = "[{classifier}][{func}][{block}][{op}] {description} [{status}]"
DEFAULT_LOG_LEVEL = logging.DEBUG
LOG_FILE_NAME = "app.log"
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), LOG_FILE_NAME)


# START_FUNCTION_setup_logger
# START_CONTRACT:
# PURPOSE: Настраивает корневой логгер приложения с файловым и консольным обработчиками.
# Записывает логи в файл app.log в корне проекта.
# INPUTS:
# - level: Уровень логирования (по умолчанию DEBUG) => level: int
# - log_file: Путь к файлу логов (по умолчанию app.log) => log_file: str | None
# OUTPUTS:
# - logging.Logger: Настроенный логгер
# SIDE_EFFECTS:
# - Создает файл логов, если он не существует
# - Добавляет обработчики к корневому логгеру
# TEST_CONDITIONS_SUCCESS_CRITERIA:
# - Логгер имеет файловый обработчик
# - Логгер имеет консольный обработчик
# - Формат логов соответствует шаблону
# KEYWORDS: [DOMAIN(9): Logging; CONCEPT(7): Configuration]
# LINKS: [CALLS(6): logging.FileHandler; CALLS(6): logging.StreamHandler]
# END_CONTRACT


def setup_logger(
    level: int = DEFAULT_LOG_LEVEL,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Настраивает корневой логгер приложения.

    Args:
        level: Уровень логирования.
        log_file: Путь к файлу логов. Если None, используется app.log в корне проекта.

    Returns:
        Настроенный экземпляр логгера.
    """
    logger = logging.getLogger()
    logger.setLevel(level)

    if logger.handlers:
        return logger

    file_path = log_file if log_file else LOG_FILE_PATH
    file_handler = logging.FileHandler(file_path, mode='a', encoding='utf-8')
    file_handler.setLevel(level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    formatter = logging.Formatter(
        '[%(levelname)s][%(name)s][%(funcName)s][%(module)s] %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"[InitCheck][setup_logger][CONFIGURE][StepComplete] Логирование настроено. Файл: {file_path} [SUCCESS]")

    return logger

# END_FUNCTION_setup_logger


# START_FUNCTION_get_logger
# START_CONTRACT:
# PURPOSE: Возвращает логгер для указанного имени модуля с предварительной настройкой.
# INPUTS:
# - name: Имя модуля для логгера => name: str
# OUTPUTS:
# - logging.Logger: Логгер для указанного модуля
# KEYWORDS: [DOMAIN(9): Logging; CONCEPT(5): Factory]
# LINKS: [CALLS(6): setup_logger]
# END_CONTRACT


def get_logger(name: str) -> logging.Logger:
    """
    Возвращает логгер для указанного имени модуля.

    Args:
        name: Имя модуля.

    Returns:
        Логгер для модуля.
    """
    setup_logger()
    return logging.getLogger(name)

# END_FUNCTION_get_logger


# START_CLASS_EntropyLogger
# START_CONTRACT:
# PURPOSE: Класс-обёртка для логирования с дополнительными методами,
# специфичными для генерации энтропии.
# ATTRIBUTES:
# - logger: logging.Logger - Базовый логгер
# - module_name: str - Имя модуля
# METHODS:
# - log_phase(name: str, status: str) -> None: Логирование фазы
# - log_data(key: str, data: bytes, status: str) -> None: Логирование данных
# - log_error(msg: str, exc: Exception = None) -> None: Логирование ошибки
# - debug(classifier: str, block: str, op: str, description: str, status: str) -> None: Отладочное логирование
# - info(classifier: str, block: str, op: str, description: str, status: str) -> None: Информационное логирование
# - warning(classifier: str, block: str, op: str, description: str, status: str) -> None: Предупреждение
# - error(classifier: str, block: str, op: str, description: str, status: str) -> None: Ошибка
# KEYWORDS: [DOMAIN(9): Logging; CONCEPT(7): Wrapper; PATTERN(6): Facade]
# LINKS: [USES(7): logging.Logger]
# END_CONTRACT


class EntropyLogger:
    """
    Класс-обёртка для логирования с форматом проекта.

    Обеспечивает единый формат логирования для всех модулей генерации энтропии:
    [CLASSIFIER][FUNC][BLOCK][OP] Description [STATUS]

    Attributes:
        logger: Базовый логгер.
        module_name: Имя модуля для логирования.
    """

    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация логгера с именем модуля.
    # INPUTS:
    # - module_name: Имя модуля => module_name: str
    # OUTPUTS:
    # - None
    # KEYWORDS: [CONCEPT(5): Initialization]
    # END_CONTRACT

    def __init__(self, module_name: str) -> None:
        """
        Инициализирует EntropyLogger.

        Args:
            module_name: Имя модуля для логирования.
        """
        self.module_name = module_name
        self.logger = get_logger(module_name)
        self.logger.debug(f"[InitCheck][EntropyLogger][INIT][StepComplete] Инициализирован логгер для {module_name} [SUCCESS]")

    # END_METHOD___init__

    # START_METHOD_log_phase
    # START_CONTRACT:
    # PURPOSE: Логирование выполнения фазы генерации энтропии.
    # INPUTS:
    # - name: Имя фазы => name: str
    # - status: Статус выполнения => status: str
    # OUTPUTS:
    # - None
    # KEYWORDS: [DOMAIN(8): PhaseTracking]
    # END_CONTRACT

    def log_phase(self, name: str, status: str) -> None:
        """
        Логирует выполнение фазы генерации энтропии.

        Args:
            name: Имя фазы.
            status: Статус выполнения (SUCCESS, FAIL, ATTEMPT).
        """
        self.info("TraceCheck", name, "ExecutePhase", f"Фаза '{name}' выполнена", status)

    # END_METHOD_log_phase

    # START_METHOD_log_data
    # START_CONTRACT:
    # PURPOSE: Логирование данных (например, сгенерированной энтропии).
    # INPUTS:
    # - key: Ключ для данных => key: str
    # - data: Данные для логирования => data: bytes
    # - status: Статус => status: str
    # OUTPUTS:
    # - None
    # KEYWORDS: [DOMAIN(8): DataLogging]
    # END_CONTRACT

    def log_data(self, key: str, data: bytes, status: str) -> None:
        """
        Логирует данные с информацией о размере.

        Args:
            key: Ключ для данных.
            data: Бинарные данные.
            status: Статус логирования.
        """
        data_size = len(data) if data else 0
        self.debug("VarCheck", key, "LogData", f"key={key}, size={data_size} байт", status)

    # END_METHOD_log_data

    # START_METHOD_log_error
    # START_CONTRACT:
    # PURPOSE: Логирование ошибки с опциональным исключением.
    # INPUTS:
    # - message: Сообщение об ошибке => message: str
    # - exc: Исключение (опционально) => exc: Exception | None
    # OUTPUTS:
    # - None
    # KEYWORDS: [DOMAIN(9): ErrorLogging]
    # END_CONTRACT

    def log_error(self, message: str, exc: Optional[Exception] = None) -> None:
        """
        Логирует ошибку.

        Args:
            message: Сообщение об ошибке.
            exc: Исключение (опционально).
        """
        if exc:
            self.error("CriticalError", "ERROR_HANDLER", "ExceptionCaught", f"{message}: {str(exc)}", "FAIL")
        else:
            self.error("CriticalError", "ERROR_HANDLER", "RaiseError", message, "FAIL")

    # END_METHOD_log_error

    # START_METHOD_debug
    # START_CONTRACT:
    # PURPOSE: Отладочное логирование с форматом проекта.
    # INPUTS:
    # - classifier: Классификатор => classifier: str
    # - block: Имя блока => block: str
    # - op: Тип операции => op: str
    # - description: Описание => description: str
    # - status: Статус => status: str
    # OUTPUTS:
    # - None
    # KEYWORDS: [DOMAIN(7): DebugLogging]
    # END_CONTRACT

    def debug(
        self,
        classifier: str,
        block: str,
        op: str,
        description: str,
        status: str
    ) -> None:
        """
        Отладочное логирование в формате проекта.

        Args:
            classifier: Классификатор (VarCheck, SelfCheck, etc.).
            block: Имя блока кода.
            op: Тип операции.
            description: Описание события.
            status: Статус (SUCCESS, FAIL, etc.).
        """
        log_message = LOG_FORMAT.format(
            classifier=classifier,
            func=self.module_name,
            block=block,
            op=op,
            description=description,
            status=status
        )
        self.logger.debug(log_message)

    # END_METHOD_debug

    # START_METHOD_info
    # START_CONTRACT:
    # PURPOSE: Информационное логирование с форматом проекта.
    # INPUTS:
    # - classifier: Классификатор => classifier: str
    # - block: Имя блока => block: str
    # - op: Тип операции => op: str
    # - description: Описание => description: str
    # - status: Статус => status: str
    # OUTPUTS:
    # - None
    # KEYWORDS: [DOMAIN(7): InfoLogging]
    # END_CONTRACT

    def info(
        self,
        classifier: str,
        block: str,
        op: str,
        description: str,
        status: str
    ) -> None:
        """
        Информационное логирование в формате проекта.

        Args:
            classifier: Классификатор.
            block: Имя блока кода.
            op: Тип операции.
            description: Описание события.
            status: Статус.
        """
        log_message = LOG_FORMAT.format(
            classifier=classifier,
            func=self.module_name,
            block=block,
            op=op,
            description=description,
            status=status
        )
        self.logger.info(log_message)

    # END_METHOD_info

    # START_METHOD_warning
    # START_CONTRACT:
    # PURPOSE: Логирование предупреждения с форматом проекта.
    # INPUTS:
    # - classifier: Классификатор => classifier: str
    # - block: Имя блока => block: str
    # - op: Тип операции => op: str
    # - description: Описание => description: str
    # - status: Статус => status: str
    # OUTPUTS:
    # - None
    # KEYWORDS: [DOMAIN(7): WarningLogging]
    # END_CONTRACT

    def warning(
        self,
        classifier: str,
        block: str,
        op: str,
        description: str,
        status: str
    ) -> None:
        """
        Логирование предупреждения в формате проекта.

        Args:
            classifier: Классификатор.
            block: Имя блока кода.
            op: Тип операции.
            description: Описание события.
            status: Статус.
        """
        log_message = LOG_FORMAT.format(
            classifier=classifier,
            func=self.module_name,
            block=block,
            op=op,
            description=description,
            status=status
        )
        self.logger.warning(log_message)

    # END_METHOD_warning

    # START_METHOD_error
    # START_CONTRACT:
    # PURPOSE: Логирование ошибки с форматом проекта.
    # INPUTS:
    # - classifier: Классификатор => classifier: str
    # - block: Имя блока => block: str
    # - op: Тип операции => op: str
    # - description: Описание => description: str
    # - status: Статус => status: str
    # OUTPUTS:
    # - None
    # KEYWORDS: [DOMAIN(9): ErrorLogging]
    # END_CONTRACT

    def error(
        self,
        classifier: str,
        block: str,
        op: str,
        description: str,
        status: str
    ) -> None:
        """
        Логирование ошибки в формате проекта.

        Args:
            classifier: Классификатор.
            block: Имя блока кода.
            op: Тип операции.
            description: Описание события.
            status: Статус.
        """
        log_message = LOG_FORMAT.format(
            classifier=classifier,
            func=self.module_name,
            block=block,
            op=op,
            description=description,
            status=status
        )
        self.logger.error(log_message)

    # END_METHOD_error

# END_CLASS_EntropyLogger
