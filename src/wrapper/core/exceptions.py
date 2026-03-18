# FILE: wrapper/core/exceptions.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Определяет кастомные исключения для модулей генерации энтропии.
# Иерархия исключений позволяет различать ошибки на разных уровнях абстракции:
# загрузка модулей, валидация данных, генерация энтропии.
# SCOPE: Обработка ошибок, логирование, валидация
# INPUT: Нет (модуль предоставляет классы исключений)
# OUTPUT: Классы исключений: EntropySourceError, ModuleLoadError, DataValidationError, EntropyGenerationError
# KEYWORDS: [DOMAIN(9): ErrorHandling; CONCEPT(7): Exceptions; PATTERN(6): Hierarchy]
# LINKS: [USED_BY(8): wrapper.core.base; USES(5): logging]
# LINKS_TO_SPECIFICATION: ["Задача: Реализация Этапа 1 — Базовая инфраструктура Python-обёртки"]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 10 [Базовый класс для всех исключений модуля энтропии] => EntropySourceError
# CLASS 8 [Исключение при ошибке загрузки .so модуля] => ModuleLoadError
# CLASS 8 [Исключение при ошибке валидации входных данных] => DataValidationError
# CLASS 8 [Исключение при ошибке генерации энтропии] => EntropyGenerationError
# END_MODULE_MAP
# START_USE_CASES:
# - [ModuleLoadError]: System (LoadModule) -> TryLoadSO -> ModuleLoadErrorRaised
# - [DataValidationError]: User (GenerateEntropy) -> ValidateInput -> DataValidationErrorRaised
# - [EntropyGenerationError]: System (GenerateEntropy) -> CallCPPModule -> EntropyGenerationErrorRaised
# END_USE_CASES
"""
Модуль кастомных исключений для Python-обёртки генерации энтропии.

Исключения:
    EntropySourceError: Базовое исключение для всех ошибок модуля.
    ModuleLoadError: Исключение при ошибке загрузки .so модуля.
    DataValidationError: Исключение при ошибке валидации входных данных.
    EntropyGenerationError: Исключение при ошибке генерации энтропии.

Пример использования:
    try:
        source = EntropySource(module_path)
    except ModuleLoadError as e:
        logger.error(f"Не удалось загрузить модуль: {e}")
"""
import logging

# START_CLASS_EntropySourceError
# START_CONTRACT:
# PURPOSE: Базовый класс для всех исключений в модуле генерации энтропии.
# Используется как родительский класс для иерархии исключений.
# ATTRIBUTES:
# - message: str - Сообщение об ошибке
# - source_name: str - Имя источника, вызвавшего ошибку
# METHODS:
# - __init__(message: str, source_name: str = None) -> None
# KEYWORDS: [DOMAIN(9): ErrorHandling; CONCEPT(7): Exceptions; PATTERN(6): BaseClass]
# LINKS: [DERIVED_BY(8): ModuleLoadError; DERIVED_BY(8): DataValidationError; DERIVED_BY(8): EntropyGenerationError]
# END_CONTRACT


class EntropySourceError(Exception):
    """
    Базовый класс для всех исключений модуля генерации энтропии.

    Этот класс является корневым для иерархии исключений, используемых
    в Python-обёртке над C++ модулями генерации энтропии.

    Attributes:
        message: Сощение об ошибке.
        source_name: Имя источника, вызвавшего ошибку (опционально).
    """

    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация исключения с сообщением и именем источника.
    # INPUTS:
    # - message: Описание ошибки => message: str
    # - source_name: Имя источника (опционально) => source_name: str | None
    # OUTPUTS:
    # - None
    # KEYWORDS: [CONCEPT(5): Initialization]
    # END_CONTRACT

    def __init__(self, message: str, source_name: str = None) -> None:
        """
        Инициализирует исключение EntropySourceError.

        Args:
            message: Сообщение об ошибке.
            source_name: Имя источника, вызвавшего ошибку.
        """
        self.message = message
        self.source_name = source_name
        full_message = f"[{source_name}] {message}" if source_name else message
        super().__init__(full_message)
        logger = logging.getLogger(__name__)
        logger.error(f"[CriticalError][EntropySourceError][INIT][ExceptionRaised] {full_message} [FAIL]")

    # END_METHOD___init__

# END_CLASS_EntropySourceError


# START_CLASS_ModuleLoadError
# START_CONTRACT:
# PURPOSE: Исключение при ошибке загрузки .so модуля.
# Возникает, когда не удается загрузить C++ модуль через ctypes или модуль недоступен.
# ATTRIBUTES:
# - module_path: str - Путь к модулю
# - reason: str - Причина ошибки
# METHODS:
# - __init__(module_path: str, reason: str) -> None
# KEYWORDS: [DOMAIN(9): ModuleLoading; CONCEPT(7): Exceptions; TECH(5): ctypes]
# LINKS: [INHERITS(10): EntropySourceError]
# END_CONTRACT


class ModuleLoadError(EntropySourceError):
    """
    Исключение при ошибке загрузки .so модуля.

    Возникает в следующих случаях:
    - Файл модуля не найден
    - Ошибка импорта модуля
    - Модуль не содержит требуемых функций
    - Ошибка ctypes при загрузке

    Attributes:
        module_path: Путь к модулю.
        reason: Причина ошибки.
    """

    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация исключения с путём к модулю и причиной ошибки.
    # INPUTS:
    # - module_path: Путь к .so модулю => module_path: str
    # - reason: Причина ошибки загрузки => reason: str
    # OUTPUTS:
    # - None
    # KEYWORDS: [CONCEPT(5): Initialization]
    # END_CONTRACT

    def __init__(self, module_path: str, reason: str) -> None:
        """
        Инициализирует исключение ModuleLoadError.

        Args:
            module_path: Путь к .so модулю.
            reason: Причина ошибки загрузки.
        """
        self.module_path = module_path
        self.reason = reason
        message = f"Не удалось загрузить модуль '{module_path}': {reason}"
        super().__init__(message, source_name="ModuleLoader")
        logger = logging.getLogger(__name__)
        logger.error(f"[CriticalError][ModuleLoadError][LOAD_MODULE][ExceptionRaised] "
                     f"module_path={module_path}, reason={reason} [FAIL]")

    # END_METHOD___init__

# END_CLASS_ModuleLoadError


# START_CLASS_DataValidationError
# START_CONTRACT:
# PURPOSE: Исключение при ошибке валидации входных данных.
# Возникает, когда входные данные не проходят проверку на корректность.
# ATTRIBUTES:
# - field_name: str - Имя поля с некорректными данными
# - invalid_value: any - Значение, которое не прошло валидацию
# - validation_rule: str - Правило валидации
# METHODS:
# - __init__(field_name: str, invalid_value: any, validation_rule: str) -> None
# KEYWORDS: [DOMAIN(9): Validation; CONCEPT(7): Exceptions; PATTERN(6): InputCheck]
# LINKS: [INHERITS(10): EntropySourceError]
# END_CONTRACT


class DataValidationError(EntropySourceError):
    """
    Исключение при ошибке валидации входных данных.

    Возникает в следующих случаях:
    - Некорректный тип данных
    - Значение вне допустимого диапазона
    - Нарушение бизнес-правил валидации

    Attributes:
        field_name: Имя поля с некорректными данными.
        invalid_value: Значение, которое не прошло валидацию.
        validation_rule: Правило валидации.
    """

    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация исключения с информацией о валидации.
    # INPUTS:
    # - field_name: Имя поля => field_name: str
    # - invalid_value: Некорректное значение => invalid_value: any
    # - validation_rule: Правило валидации => validation_rule: str
    # OUTPUTS:
    # - None
    # KEYWORDS: [CONCEPT(5): Initialization]
    # END_CONTRACT

    def __init__(self, field_name: str, invalid_value: any, validation_rule: str) -> None:
        """
        Инициализирует исключение DataValidationError.

        Args:
            field_name: Имя поля с некорректными данными.
            invalid_value: Значение, которое не прошло валидацию.
            validation_rule: Правило валидации.
        """
        self.field_name = field_name
        self.invalid_value = invalid_value
        self.validation_rule = validation_rule
        message = f"Ошибка валидации поля '{field_name}': значение {invalid_value} не удовлетворяет правилу '{validation_rule}'"
        super().__init__(message, source_name="DataValidator")
        logger = logging.getLogger(__name__)
        logger.warning(f"[VarCheck][DataValidationError][VALIDATE][ConditionCheck] "
                       f"field={field_name}, value={invalid_value}, rule={validation_rule} [FAIL]")

    # END_METHOD___init__

# END_CLASS_DataValidationError


# START_CLASS_EntropyGenerationError
# START_CONTRACT:
# PURPOSE: Исключение при ошибке генерации энтропии.
# Возникает, когда C++ модуль возвращает ошибку или генерирует некорректные данные.
# ATTRIBUTES:
# - phase: str - Фаза генерации, на которой произошла ошибка
# - cpp_error: str - Ошибка от C++ модуля (если доступна)
# METHODS:
# - __init__(phase: str, cpp_error: str = None) -> None
# KEYWORDS: [DOMAIN(9): EntropyGeneration; CONCEPT(7): Exceptions; PATTERN(6): Pipeline]
# LINKS: [INHERITS(10): EntropySourceError]
# END_CONTRACT


class EntropyGenerationError(EntropySourceError):
    """
    Исключение при ошибке генерации энтропии.

    Возникает в следующих случаях:
    - Ошибка в C++ модуле при генерации энтропии
    - Некорректные данные, возвращенные C++ модулем
    - Нарушение контракта генерации энтропии

    Attributes:
        phase: Фаза генерации, на которой произошла ошибка.
        cpp_error: Ошибка от C++ модуля (опционально).
    """

    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация исключения с информацией о фазе генерации.
    # INPUTS:
    # - phase: Название фазы генерации => phase: str
    # - cpp_error: Ошибка от C++ модуля (опционально) => cpp_error: str | None
    # OUTPUTS:
    # - None
    # KEYWORDS: [CONCEPT(5): Initialization]
    # END_CONTRACT

    def __init__(self, phase: str, cpp_error: str = None) -> None:
        """
        Инициализирует исключение EntropyGenerationError.

        Args:
            phase: Фаза генерации, на которой произошла ошибка.
            cpp_error: Ошибка от C++ модуля.
        """
        self.phase = phase
        self.cpp_error = cpp_error
        message = f"Ошибка генерации энтропии на фазе '{phase}'"
        if cpp_error:
            message += f": {cpp_error}"
        super().__init__(message, source_name="EntropyGenerator")
        logger = logging.getLogger(__name__)
        logger.error(f"[CriticalError][EntropyGenerationError][GENERATE_ENTROPY][ExceptionRaised] "
                     f"phase={phase}, cpp_error={cpp_error} [FAIL]")

    # END_METHOD___init__

# END_CLASS_EntropyGenerationError
