# FILE: src/monitor/_cpp/plugin_base_wrapper.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Python-обёртка для C++ модуля базового класса плагинов мониторинга. Обеспечивает единый интерфейс для создания плагинов с поддержкой C++ бэкенда и fallback на Python реализацию.
# SCOPE: Абстрактный базовый класс, система хуков событий, константы событий, fallback механизм
# INPUT: Нет (модуль предоставляет классы и функции)
# OUTPUT: Класс BaseMonitorPlugin, Константы EVENT_TYPE_*, Функции fallback
# KEYWORDS: [DOMAIN(9): PluginSystem; DOMAIN(8): CppBinding; CONCEPT(8): AbstractClass; TECH(7): Fallback]
# LINKS: [USES_API(8): abc; USES_API(6): typing; IMPORTS(7): src.monitor._cpp]
# LINKS_TO_SPECIFICATION: [Спецификация плагинов мониторинга из dev_plan_monitor_init.md]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 10 [Базовый класс для всех плагинов мониторинга с поддержкой C++] => BaseMonitorPlugin
# CONST 6 [Константы типов событий] => EVENT_TYPE_*
# END_MODULE_MAP
# START_USE_CASES:
# - [BaseMonitorPlugin]: System (PluginLifecycle) -> ProvideBaseInterface -> PluginArchitectureDefined
# - [register_hook]: Plugin (EventSubscription) -> RegisterCallback -> EventHandlerReady
# - [emit_event]: System (EventDispatch) -> NotifySubscribers -> HandlersExecuted
# - [initialize]: Plugin (Initialization) -> ConfigurePlugin -> PluginReady
# END_USE_CASES
"""
Модуль plugin_base_wrapper.py — Python-обёртка для C++ модуля базового класса плагинов.

Этот модуль обеспечивает:
- Базовый класс BaseMonitorPlugin с поддержкой C++ бэкенда
- Систему хуков для событий (register/unregister/emit)
- Fallback на Python реализацию при отсутствии C++ модуля
- Константы типов событий

Константы событий:
- EVENT_TYPE_START: Запуск генератора
- EVENT_TYPE_STOP: Остановка генератора
- EVENT_TYPE_METRIC: Обновление метрик
- EVENT_TYPE_MATCH: Обнаружение совпадений
- EVENT_TYPE_ERROR: Ошибка
- EVENT_TYPE_STATUS: Изменение статуса
"""

import logging
import sys
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field

# ============================================================================
# КОНФИГУРАЦИЯ ЛОГИРОВАНИЯ
# ============================================================================

def _setup_file_logging() -> logging.FileHandler:
    """Настройка логирования в файл app.log."""
    # Определяем путь к корневой директории проекта
    project_root = Path(__file__).parent.parent.parent.parent
    log_file = project_root / "app.log"
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s][%(name)s][%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    return file_handler

# Настройка логирования для модуля
_logger = logging.getLogger("src.monitor._cpp.plugin_base_wrapper")
if not _logger.handlers:
    _file_handler = _setup_file_logging()
    _logger.addHandler(_file_handler)
    _logger.setLevel(logging.DEBUG)

logger = _logger

# ============================================================================
# КОНСТАНТЫ ТИПОВ СОБЫТИЙ
# ============================================================================

# START_CONSTANTS_EVENT_TYPES
# START_CONTRACT:
# PURPOSE: Определение констант для типов событий плагинов мониторинга
# KEYWORDS: [CONCEPT(7): Constants; DOMAIN(8): EventSystem]
# END_CONTRACT

EVENT_TYPE_START: str = "start"
"""Событие запуска генератора кошельков"""

EVENT_TYPE_STOP: str = "stop"
"""Событие остановки генератора кошельков"""

EVENT_TYPE_METRIC: str = "metric"
"""Событие обновления метрик генерации"""

EVENT_TYPE_MATCH: str = "match"
"""Событие обнаружения совпадений адресов"""

EVENT_TYPE_ERROR: str = "error"
"""Событие ошибки в процессе генерации"""

EVENT_TYPE_STATUS: str = "status"
"""Событие изменения статуса плагина или системы"""

# END_CONSTANTS_EVENT_TYPES

# Список всех типов событий для валидации
ALL_EVENT_TYPES: Set[str] = {
    EVENT_TYPE_START,
    EVENT_TYPE_STOP,
    EVENT_TYPE_METRIC,
    EVENT_TYPE_MATCH,
    EVENT_TYPE_ERROR,
    EVENT_TYPE_STATUS,
}

# ============================================================================
# ПРОВЕРКА ДОСТУПНОСТИ C++ МОДУЛЯ
# ============================================================================

# START_FUNCTION_CHECK_CPP_AVAILABILITY
# START_CONTRACT:
# PURPOSE: Проверка доступности C++ модуля plugin_base_cpp
# OUTPUTS:
# - bool - True если C++ модуль доступен, False в противном случае
# KEYWORDS: [PATTERN(7): ModuleCheck; DOMAIN(8): ModuleLoading; TECH(6): Import]
# END_CONTRACT

def _check_cpp_availability() -> bool:
    """
    Проверка доступности C++ модуля plugin_base_cpp.
    
    Returns:
        True если C++ модуль доступен, False в противном случае
    """
    try:
        import plugin_base_cpp
        logger.info(f"[_check_cpp_availability][MODULE_CHECK] C++ модуль plugin_base_cpp доступен [SUCCESS]")
        return True
    except (ImportError, ModuleNotFoundError) as e:
        logger.info(f"[_check_cpp_availability][MODULE_CHECK] C++ модуль plugin_base_cpp недоступен: {e} [FAIL]")
        return False
    except Exception as e:
        logger.warning(f"[_check_cpp_availability][MODULE_CHECK] Ошибка при проверке C++ модуля: {e} [FAIL]")
        return False

# Кэш доступности C++ модуля
_CPP_AVAILABLE: Optional[bool] = None

def _get_cpp_available() -> bool:
    """Получение кэшированного статуса доступности C++ модуля."""
    global _CPP_AVAILABLE
    if _CPP_AVAILABLE is None:
        _CPP_AVAILABLE = _check_cpp_availability()
    return _CPP_AVAILABLE

# END_FUNCTION_CHECK_CPP_AVAILABILITY

# ============================================================================
# FALLBACK НА PYTHON РЕАЛИЗАЦИЮ
# ============================================================================

# START_FUNCTION_GET_CPP_MODULE
# START_CONTRACT:
# PURPOSE: Получение C++ модуля или Python fallback
# OUTPUTS:
# - Any - C++ модуль или Python fallback
# KEYWORDS: [PATTERN(7): Factory; DOMAIN(9): ModuleLoading; TECH(8): DynamicImport]
# END_CONTRACT

def _get_cpp_module():
    """
    Получение C++ модуля с fallback на Python реализацию.
    
    Returns:
        C++ модуль plugin_base_cpp если доступен, иначе None
    """
    if _get_cpp_available():
        try:
            import plugin_base_cpp
            logger.info(f"[_get_cpp_module][ReturnData] Возвращен C++ модуль plugin_base_cpp [SUCCESS]")
            return plugin_base_cpp
        except Exception as e:
            logger.warning(f"[_get_cpp_module][ExceptionCaught] Ошибка импорта C++ модуля: {e}, используем fallback")
    
    logger.info(f"[_get_cpp_module][ReturnData] C++ модуль недоступен, будет использован Python fallback [INFO]")
    return None

# END_FUNCTION_GET_CPP_MODULE

# ============================================================================
# КЛАСС ДЛЯ ХРАНЕНИЯ КОНФИГУРАЦИИ ПЛАГИНА
# ============================================================================

# START_CLASS_PLUGIN_CONFIG
# START_CONTRACT:
# PURPOSE: Класс для хранения конфигурации плагина мониторинга
# ATTRIBUTES:
# - name: str — уникальное имя плагина
# - priority: int — приоритет плагина (0 = highest, 100 = lowest)
# - enabled: bool — флаг включения плагина
# - config: Dict[str, Any] — словарь конфигурации плагина
# KEYWORDS: [PATTERN(7): DataClass; DOMAIN(8): PluginConfig; CONCEPT(6): Configuration]
# END_CONTRACT

@dataclass
class PluginConfig:
    """
    Класс для хранения конфигурации плагина мониторинга.
    """
    name: str
    priority: int = 50
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование конфигурации в словарь."""
        return {
            "name": self.name,
            "priority": self.priority,
            "enabled": self.enabled,
            "config": self.config,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginConfig":
        """Создание конфигурации из словаря."""
        return cls(
            name=data.get("name", ""),
            priority=data.get("priority", 50),
            enabled=data.get("enabled", True),
            config=data.get("config", {}),
        )

# END_CLASS_PLUGIN_CONFIG

# ============================================================================
# БАЗОВЫЙ КЛАСС ПЛАГИНА МОНИТОРИНГА
# ============================================================================

# START_CLASS_BASE_MONITOR_PLUGIN
# START_CONTRACT:
# PURPOSE: Базовый класс для всех плагинов системы мониторинга с поддержкой C++ бэкенда и fallback на Python реализацию. Определяет общий интерфейс, жизненный цикл и систему хуков событий.
# ATTRIBUTES:
# - Уникальное имя плагина => _name: str
# - Конфигурация плагина => _config: PluginConfig
# - Флаг использования C++ бэкенда => _using_cpp: bool
# - Словарь зарегистрированных хуков => _hooks: Dict[str, List[Callable]]
# - Логгер плагина => _logger: logging.Logger
# METHODS:
# - Инициализация плагина => initialize(config)
# - Обработка события => process_event(event)
# - Получение статуса => get_status()
# - Завершение работы => shutdown()
# - Регистрация хука => register_hook(event_type, callback)
# - Отмена регистрации хука => unregister_hook(event_type)
# - Генерация события => emit_event(event)
# KEYWORDS: [PATTERN(8): AbstractClass; DOMAIN(9): PluginSystem; TECH(7): CppBinding]
# LINKS: [USES_API(8): abc.ABC; IMPLEMENTS(7): HookSystem]
# END_CONTRACT

class BaseMonitorPlugin(ABC):
    """
    Базовый класс для всех плагинов системы мониторинга.
    
    Обеспечивает единый интерфейс для создания плагинов с поддержкой:
    - C++ бэкенда (если доступен)
    - Fallback на Python реализацию
    - Системы хуков для событий
    
    Абстрактные методы (должны быть реализованы наследниками):
        - initialize(config): Инициализация плагина
        - process_event(event): Обработка события
        - get_status(): Получение статуса плагина
        - shutdown(): Корректное завершение работы
    
    Пример использования:
        class MyPlugin(BaseMonitorPlugin):
            def initialize(self, config):
                self.logger.info(f"Инициализация плагина {self.name}")
            
            def process_event(self, event):
                self.logger.info(f"Получено событие: {event}")
            
            def get_status(self):
                return {"state": "running"}
            
            def shutdown(self):
                self.logger.info("Завершение работы плагина")
    """
    
    VERSION: str = "1.0.0"
    """Версия плагина по умолчанию"""
    
    AUTHOR: str = "Wallet Generator Team"
    """Автор плагина по умолчанию"""
    
    DESCRIPTION: str = "Base monitor plugin"
    """Описание плагина по умолчанию"""
    
    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация базового плагина с именем и конфигурацией
    # INPUTS:
    # - name: str — уникальное имя плагина
    # - config: Optional[Dict[str, Any]] — словарь конфигурации плагина
    # OUTPUTS: Инициализированный объект плагина
    # SIDE_EFFECTS: Создаёт логгер; инициализирует систему хуков; проверяет доступность C++ модуля
    # KEYWORDS: [CONCEPT(5): Initialization; DOMAIN(7): PluginSetup]
    # TEST_CONDITIONS_SUCCESS_CRITERIA: Плагин должен иметь уникальное имя и пустой список хуков после инициализации
    # END_CONTRACT
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Инициализация базового плагина мониторинга.
        
        Args:
            name: Уникальное имя плагина
            config: Словарь конфигурации плагина (опционально)
        """
        # Инициализация атрибутов
        self._name = name
        self._config = PluginConfig(
            name=name,
            priority=config.get("priority", 50) if config else 50,
            enabled=config.get("enabled", True) if config else True,
            config=config.get("config", {}) if config else {},
        )
        self._hooks: Dict[str, List[Callable]] = {}
        self._status: Dict[str, Any] = {"state": "initialized", "message": "Plugin initialized"}
        
        # Проверка доступности C++ модуля
        self._cpp_module = _get_cpp_module()
        self._using_cpp = self._cpp_module is not None
        
        # Настройка логирования
        self._logger = logging.getLogger(f"{__name__}.{name}")
        if not self._logger.handlers:
            self._logger.addHandler(_file_handler)
            self._logger.setLevel(logging.DEBUG)
        
        # Логирование инициализации
        self._logger.debug(f"[BaseMonitorPlugin][INIT][ConditionCheck] Инициализирован плагин: {name}")
        self._logger.debug(f"[BaseMonitorPlugin][INIT][VarCheck] C++ модуль доступен: {self._using_cpp} [VALUE]")
        self._logger.debug(f"[BaseMonitorPlugin][INIT][VarCheck] Приоритет: {self._config.priority} [VALUE]")
        self._logger.debug(f"[BaseMonitorPlugin][INIT][VarCheck] Включён: {self._config.enabled} [VALUE]")
    
    # END_METHOD___init__
    
    # ============================================================================
    # СВОЙСТВА (PROPERTIES)
    # ============================================================================
    
    # START_PROPERTY_NAME
    @property
    def name(self) -> str:
        """
        Получение имени плагина.
        
        Returns:
            Имя плагина
        """
        return self._name
    # END_PROPERTY_NAME
    
    # START_PROPERTY_ENABLED
    @property
    def enabled(self) -> bool:
        """
        Получение состояния включения плагина.
        
        Returns:
            True если плагин включён, False в противном случае
        """
        return self._config.enabled
    # END_PROPERTY_ENABLED
    
    # START_PROPERTY_CPP_AVAILABLE
    @property
    def cpp_available(self) -> bool:
        """
        Проверка доступности C++ модуля.
        
        Returns:
            True если C++ модуль доступен, False в противном случае
        """
        return self._cpp_module is not None
    # END_PROPERTY_CPP_AVAILABLE
    
    # START_PROPERTY_USING_CPP
    @property
    def using_cpp(self) -> bool:
        """
        Проверка использования C++ бэкенда.
        
        Returns:
            True если плагин использует C++ бэкенд, False если используется Python реализация
        """
        return self._using_cpp
    # END_PROPERTY_USING_CPP
    
    # START_PROPERTY_HOOKS
    @property
    def hooks(self) -> Dict[str, List[Callable]]:
        """
        Получение словаря зарегистрированных хуков.
        
        Returns:
            Словарь с типами событий в качестве ключей и списками callback-функций в качестве значений
        """
        return self._hooks.copy()
    # END_PROPERTY_HOOKS
    
    # ============================================================================
    # АБСТРАКТНЫЕ МЕТОДЫ (ДОЛЖНЫ БЫТЬ РЕАЛИЗОВАНЫ НАСЛЕДНИКАМИ)
    # ============================================================================
    
    # START_METHOD_INITIALIZE
    # START_CONTRACT:
    # PURPOSE: Инициализация плагина с переданной конфигурацией
    # INPUTS:
    # - config: Dict[str, Any] — словарь конфигурации плагина
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Может инициализировать внутреннее состояние; может зарегистрировать компоненты
    # KEYWORDS: [DOMAIN(8): PluginSetup; CONCEPT(6): Initialization]
    # TEST_CONDITIONS_SUCCESS_CRITERIA: Метод должен корректно обработать любую конфигурацию
    # END_CONTRACT
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Инициализация плагина.
        
        Args:
            config: Словарь конфигурации плагина
        """
        pass
    
    # END_METHOD_INITIALIZE
    
    # START_METHOD_PROCESS_EVENT
    # START_CONTRACT:
    # PURPOSE: Обработка события, поступившего в плагин
    # INPUTS:
    # - event: Dict[str, Any] — словарь с данными события (должен содержать ключ 'type')
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Может изменить внутреннее состояние плагина; может сгенерировать новые события
    # KEYWORDS: [DOMAIN(9): EventProcessing; CONCEPT(7): EventHandler]
    # TEST_CONDITIONS_SUCCESS_CRITERIA: Метод должен корректно обработать события всех типов
    # END_CONTRACT
    @abstractmethod
    def process_event(self, event: Dict[str, Any]) -> None:
        """
        Обработка события.
        
        Args:
            event: Словарь с данными события (обязательно должен содержать ключ 'type')
        """
        pass
    
    # END_METHOD_PROCESS_EVENT
    
    # START_METHOD_GET_STATUS
    # START_CONTRACT:
    # PURPOSE: Получение текущего статуса плагина
    # OUTPUTS:
    # - Dict[str, Any] — словарь со статусом плагина
    # SIDE_EFFECTS: Нет
    # KEYWORDS: [CONCEPT(5): Getter; DOMAIN(6): StatusCheck]
    # TEST_CONDITIONS_SUCCESS_CRITERIA: Метод всегда должен возвращать словарь
    # END_CONTRACT
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Получение статуса плагина.
        
        Returns:
            Словарь со статусом плагина (должен содержать ключ 'state')
        """
        pass
    
    # END_METHOD_GET_STATUS
    
    # START_METHOD_SHUTDOWN
    # START_CONTRACT:
    # PURPOSE: Корректное завершение работы плагина
    # INPUTS: Нет
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Освобождение занятых ресурсов; сохранение состояния (если необходимо)
    # KEYWORDS: [CONCEPT(8): Cleanup; DOMAIN(7): Shutdown]
    # TEST_CONDITIONS_SUCCESS_CRITERIA: Метод должен корректно освободить все ресурсы
    # END_CONTRACT
    @abstractmethod
    def shutdown(self) -> None:
        """
        Корректное завершение работы плагина.
        
        Должен освободить все занятые ресурсы и сохранить состояние (если необходимо).
        """
        pass
    
    # ============================================================================
    # ОСНОВНЫЕ МЕТОДЫ УПРАВЛЕНИЯ
    # ============================================================================
    
    # START_METHOD_ENABLE
    # START_CONTRACT:
    # PURPOSE: Включение плагина
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Устанавливает флаг enabled = True; логирует событие включения
    # KEYWORDS: [CONCEPT(6): StateManagement; DOMAIN(7): PluginControl]
    # END_CONTRACT
    def enable(self) -> None:
        """Включение плагина."""
        self._config.enabled = True
        self._status["state"] = "enabled"
        self._logger.info(f"[BaseMonitorPlugin][ENABLE][StepComplete] Плагин {self._name} включён [SUCCESS]")
    
    # END_METHOD_ENABLE
    
    # START_METHOD_DISABLE
    # START_CONTRACT:
    # PURPOSE: Отключение плагина
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Устанавливает флаг enabled = False; логирует событие отключения
    # KEYWORDS: [CONCEPT(6): StateManagement; DOMAIN(7): PluginControl]
    # END_CONTRACT
    def disable(self) -> None:
        """Отключение плагина."""
        self._config.enabled = False
        self._status["state"] = "disabled"
        self._logger.info(f"[BaseMonitorPlugin][DISABLE][StepComplete] Плагин {self._name} отключён [SUCCESS]")
    
    # END_METHOD_DISABLE
    
    # START_METHOD_IS_ENABLED
    # START_CONTRACT:
    # PURPOSE: Проверка состояния плагина
    # OUTPUTS:
    # - bool — True если плагин включён, False если выключен
    # KEYWORDS: [CONCEPT(5): Getter; DOMAIN(6): StateCheck]
    # END_CONTRACT
    def is_enabled(self) -> bool:
        """
        Проверка состояния плагина.
        
        Returns:
            True если плагин включён, False в противном случае
        """
        return self._config.enabled
    
    # END_METHOD_IS_ENABLED
    
    # START_METHOD_GET_NAME
    # START_CONTRACT:
    # PURPOSE: Получение имени плагина
    # OUTPUTS:
    # - str — имя плагина
    # KEYWORDS: [CONCEPT(5): Getter]
    # END_CONTRACT
    def get_name(self) -> str:
        """
        Получение имени плагина.
        
        Returns:
            Имя плагина
        """
        return self._name
    
    # END_METHOD_GET_NAME
    
    # START_METHOD_GET_CONFIG
    # START_CONTRACT:
    # PURPOSE: Получение текущей конфигурации плагина
    # OUTPUTS:
    # - Dict[str, Any] — словарь конфигурации плагина
    # KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): Configuration]
    # END_CONTRACT
    def get_config(self) -> Dict[str, Any]:
        """
        Получение текущей конфигурации плагина.
        
        Returns:
            Словарь конфигурации плагина
        """
        return self._config.to_dict()
    
    # END_METHOD_GET_CONFIG
    
    # START_METHOD_UPDATE_CONFIG
    # START_CONTRACT:
    # PURPOSE: Обновление конфигурации плагина
    # INPUTS:
    # - config: Dict[str, Any] — новый словарь конфигурации
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Обновляет внутреннюю конфигурацию; логирует изменения
    # KEYWORDS: [CONCEPT(6): Setter; DOMAIN(8): Configuration]
    # END_CONTRACT
    def update_config(self, config: Dict[str, Any]) -> None:
        """
        Обновление конфигурации плагина.
        
        Args:
            config: Новый словарь конфигурации
        """
        if "priority" in config:
            self._config.priority = config["priority"]
        if "enabled" in config:
            self._config.enabled = config["enabled"]
        if "config" in config:
            self._config.config.update(config["config"])
        
        self._logger.info(f"[BaseMonitorPlugin][UPDATE_CONFIG][StepComplete] Конфигурация плагина {self._name} обновлена [SUCCESS]")
        self._logger.debug(f"[BaseMonitorPlugin][UPDATE_CONFIG][VarCheck] Новая конфигурация: {self._config.to_dict()} [VALUE]")
    
    # END_METHOD_UPDATE_CONFIG
    
    # ============================================================================
    # СИСТЕМА ХУКОВ (EVENT HOOKS)
    # ============================================================================
    
    # START_METHOD_REGISTER_HOOK
    # START_CONTRACT:
    # PURPOSE: Регистрация обработчика события для указанного типа события
    # INPUTS:
    # - event_type: str — тип события (одна из констант EVENT_TYPE_*)
    # - callback: Callable — функция-обработчик события
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Добавляет callback в список обработчиков указанного типа события
    # KEYWORDS: [DOMAIN(8): EventHook; CONCEPT(7): Subscription]
    # TEST_CONDITIONS_SUCCESS_CRITERIA: После регистрации callback должен вызываться при генерации события
    # END_CONTRACT
    def register_hook(self, event_type: str, callback: Callable) -> None:
        """
        Регистрация обработчика события.
        
        Args:
            event_type: Тип события (одна из констант EVENT_TYPE_*)
            callback: Функция-обработчик события
        """
        # Валидация типа события
        if event_type not in ALL_EVENT_TYPES:
            self._logger.warning(f"[BaseMonitorPlugin][REGISTER_HOOK][ConditionCheck] Неизвестный тип события: {event_type} [FAIL]")
            return
        
        # Инициализация списка хуков для типа события, если его нет
        if event_type not in self._hooks:
            self._hooks[event_type] = []
        
        # Добавление callback в список
        self._hooks[event_type].append(callback)
        self._logger.debug(f"[BaseMonitorPlugin][REGISTER_HOOK][StepComplete] Зарегистрирован хук для события {event_type} [SUCCESS]")
        self._logger.debug(f"[BaseMonitorPlugin][REGISTER_HOOK][VarCheck] Всего хуков для {event_type}: {len(self._hooks[event_type])} [VALUE]")
    
    # END_METHOD_REGISTER_HOOK
    
    # START_METHOD_UNREGISTER_HOOK
    # START_CONTRACT:
    # PURPOSE: Отмена регистрации всех обработчиков для указанного типа события
    # INPUTS:
    # - event_type: str — тип события (одна из констант EVENT_TYPE_*)
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Удаляет все callback для указанного типа события
    # KEYWORDS: [DOMAIN(8): EventHook; CONCEPT(7): Unsubscription]
    # END_CONTRACT
    def unregister_hook(self, event_type: str) -> None:
        """
        Отмена регистрации всех обработчиков для указанного типа события.
        
        Args:
            event_type: Тип события
        """
        if event_type in self._hooks:
            count = len(self._hooks[event_type])
            del self._hooks[event_type]
            self._logger.debug(f"[BaseMonitorPlugin][UNREGISTER_HOOK][StepComplete] Отменены хуки для события {event_type} (было: {count}) [SUCCESS]")
        else:
            self._logger.debug(f"[BaseMonitorPlugin][UNREGISTER_HOOK][Info] Хуки для события {event_type} не найдены [INFO]")
    
    # END_METHOD_UNREGISTER_HOOK
    
    # START_METHOD_EMIT_EVENT
    # START_CONTRACT:
    # PURPOSE: Генерация события для всех зарегистрированных обработчиков
    # INPUTS:
    # - event: Dict[str, Any] — словарь с данными события (должен содержать ключ 'type')
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Вызывает все зарегистрированные callback для события указанного типа
    # KEYWORDS: [DOMAIN(9): EventDispatch; CONCEPT(7): Broadcasting]
    # TEST_CONDITIONS_SUCCESS_CRITERIA: Все зарегистрированные callback должны быть вызваны
    # END_CONTRACT
    def emit_event(self, event: Dict[str, Any]) -> None:
        """
        Генерация события для всех зарегистрированных обработчиков.
        
        Args:
            event: Словарь с данными события (обязательно должен содержать ключ 'type')
        """
        # Получение типа события
        event_type = event.get("type", "unknown")
        
        # Проверка наличия обработчиков для данного типа события
        if event_type not in self._hooks:
            self._logger.debug(f"[BaseMonitorPlugin][EMIT_EVENT][Info] Нет зарегистрированных хуков для события {event_type} [INFO]")
            return
        
        # Получение списка обработчиков
        callbacks = self._hooks[event_type]
        
        self._logger.debug(f"[BaseMonitorPlugin][EMIT_EVENT][ConditionCheck] Найдено {len(callbacks)} хуков для события {event_type} [VALUE]")
        
        # Вызов всех зарегистрированных callback
        for callback in callbacks:
            try:
                callback(event)
                self._logger.debug(f"[BaseMonitorPlugin][EMIT_EVENT][CallExternal] Вызван callback для события {event_type} [SUCCESS]")
            except Exception as e:
                self._logger.error(f"[BaseMonitorPlugin][EMIT_EVENT][ExceptionCaught] Ошибка при вызове callback: {e} [FAIL]")
    
    # END_METHOD_EMIT_EVENT
    
    # ============================================================================
    # ЛОГИРОВАНИЕ
    # ============================================================================
    
    # START_METHOD_LOG
    # START_CONTRACT:
    # PURPOSE: Логирование сообщения от имени плагина
    # INPUTS:
    # - level: str — уровень логирования ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    # - message: str — текст сообщения
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Записывает сообщение в лог с именем плагина
    # KEYWORDS: [CONCEPT(6): Logging; DOMAIN(7): Diagnostics]
    # END_CONTRACT
    def log(self, level: str, message: str) -> None:
        """
        Логирование сообщения от имени плагина.
        
        Args:
            level: Уровень логирования ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
            message: Текст сообщения
        """
        # Преобразование уровня в верхний регистр
        level_upper = level.upper()
        
        # Валидация уровня логирования
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if level_upper not in valid_levels:
            self._logger.warning(f"[BaseMonitorPlugin][LOG][ConditionCheck] Неизвестный уровень логирования: {level} [FAIL]")
            level_upper = "INFO"
        
        # Логирование сообщения
        log_message = f"[{self._name}] {message}"
        
        if level_upper == "DEBUG":
            self._logger.debug(log_message)
        elif level_upper == "INFO":
            self._logger.info(log_message)
        elif level_upper == "WARNING":
            self._logger.warning(log_message)
        elif level_upper == "ERROR":
            self._logger.error(log_message)
        elif level_upper == "CRITICAL":
            self._logger.critical(log_message)
    
    # END_METHOD_LOG
    
    # ============================================================================
    # МЕТОДЫ СРАВНЕНИЯ И ХЭШИРОВАНИЯ
    # ============================================================================
    
    # START_METHOD___lt__
    # START_CONTRACT:
    # PURPOSE: Сравнение плагинов по приоритету
    # INPUTS:
    # - other: BaseMonitorPlugin — другой плагин для сравнения
    # OUTPUTS: bool — результат сравнения
    # KEYWORDS: [CONCEPT(8): Comparison; DOMAIN(6): Sorting]
    # END_CONTRACT
    def __lt__(self, other: "BaseMonitorPlugin") -> bool:
        """Сравнение плагинов по приоритету."""
        return self._config.priority < other._config.priority
    
    # END_METHOD___lt__
    
    # START_METHOD___eq__
    # START_CONTRACT:
    # PURPOSE: Проверка равенства плагинов
    # INPUTS:
    # - other: object — объект для сравнения
    # OUTPUTS: bool — результат сравнения
    # KEYWORDS: [CONCEPT(7): Equality; DOMAIN(5): Comparison]
    # END_CONTRACT
    def __eq__(self, other: object) -> bool:
        """Проверка равенства плагинов по имени."""
        if isinstance(other, BaseMonitorPlugin):
            return self._name == other._name
        return False
    
    # END_METHOD___eq__
    
    # START_METHOD___hash__
    # START_CONTRACT:
    # PURPOSE: Получение хэша плагина
    # OUTPUTS: int — хэш плагина
    # KEYWORDS: [CONCEPT(6): Hashing]
    # END_CONTRACT
    def __hash__(self) -> int:
        """Получение хэша плагина по имени."""
        return hash(self._name)
    
    # END_METHOD___hash__
    
    # ============================================================================
    # СТАНДАРТНЫЕ МЕТОДЫ
    # ============================================================================
    
    # START_METHOD___repr__
    # START_CONTRACT:
    # PURPOSE: Строковое представление плагина
    # OUTPUTS: str — строковое представление
    # KEYWORDS: [CONCEPT(5): StringRepr]
    # END_CONTRACT
    def __repr__(self) -> str:
        """Строковое представление плагина."""
        return f"BaseMonitorPlugin(name={self._name}, priority={self._config.priority}, enabled={self._config.enabled}, using_cpp={self._using_cpp})"
    
    # END_METHOD___repr__
    
    # START_METHOD___str__
    # START_CONTRACT:
    # PURPOSE: Читаемое строковое представление плагина
    # OUTPUTS: str — читаемое представление
    # KEYWORDS: [CONCEPT(5): StringRepr]
    # END_CONTRACT
    def __str__(self) -> str:
        """Читаемое строковое представление плагина."""
        return f"Плагин '{self._name}' (приоритет: {self._config.priority}, включён: {self._config.enabled}, C++: {self._using_cpp})"
    
    # END_METHOD___str__


# END_CLASS_BASE_MONITOR_PLUGIN

# ============================================================================
# ЭКСПОРТ
# ============================================================================

__all__ = [
    # Константы событий
    "EVENT_TYPE_START",
    "EVENT_TYPE_STOP",
    "EVENT_TYPE_METRIC",
    "EVENT_TYPE_MATCH",
    "EVENT_TYPE_ERROR",
    "EVENT_TYPE_STATUS",
    "ALL_EVENT_TYPES",
    # Классы
    "BaseMonitorPlugin",
    "PluginConfig",
    # Функции
    "_get_cpp_available",
    "_get_cpp_module",
]

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ ПРИ ИМПОРТЕ
# ============================================================================

logger.info(f"[INIT] Модуль plugin_base_wrapper.py загружен, C++ доступен: {_get_cpp_available()} [INFO]")
