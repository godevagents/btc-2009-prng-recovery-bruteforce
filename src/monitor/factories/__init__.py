# FILE: src/monitor/factories/__init__.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Модуль фабрик для создания экземпляров плагинов мониторинга. Централизованный механизм создания плагинов с поддержкой различных типов.
# SCOPE: Фабрики плагинов, конфигурация плагинов, система создания экземпляров
# INPUT: Конфигурация плагинов, типы плагинов
# OUTPUT: Экземпляры плагинов, доступные типы плагинов, исключения при ошибках создания
# KEYWORDS: [DOMAIN(9): PluginFactory; DOMAIN(8): PluginCreation; TECH(7): FactoryPattern; CONCEPT(6): Instantiation]
# LINKS: [USES_API(8): src.monitor._cpp.live_stats_wrapper; USES_API(7): src.monitor._cpp.final_stats_wrapper; USES_API(7): src.monitor._cpp.match_notifier_wrapper]
# LINKS_TO_SPECIFICATION: [create_factories_init_plan.md]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 10 [Перечисление типов плагинов мониторинга] => PluginType
# CLASS 9 [Конфигурация плагина для фабрики] => PluginConfig
# CLASS 8 [Исключение при ошибке создания плагина] => PluginCreationError
# FUNC 7 [Создание плагина по конфигурации] => create_plugin
# FUNC 6 [Получение списка доступных плагинов] => get_available_plugins
# FUNC 5 [Заглушка класса фабрики] => PluginFactory
# END_MODULE_MAP
# START_USE_CASES:
# - [create_plugin]: System (PluginCreation) -> CreatePluginInstance -> PluginReady
# - [get_available_plugins]: Admin (Query) -> ListAvailablePlugins -> PluginTypesList
# - [PluginFactory]: System (PluginManagement) -> ManagePluginLifecycle -> PluginsManaged
# END_USE_CASES
"""
Модуль factories — Фабрики для создания объектов мониторинга.

Модуль предоставляет:
- Перечисление типов плагинов (PluginType)
- Конфигурацию плагинов (PluginConfig)
- Исключение при ошибке создания (PluginCreationError)
- Функцию создания плагина (create_plugin)
- Функцию получения доступных плагинов (get_available_plugins)

Пример использования:
    from src.monitor.factories import create_plugin, PluginConfig, PluginType
    
    # Создание конфигурации плагина
    config = PluginConfig(
        name="my_live_stats",
        plugin_type=PluginType.LIVE_STATS,
        config={"priority": 20},
        use_cpp=True
    )
    
    # Создание плагина
    plugin = create_plugin(config)
    
    # Получение списка доступных плагинов
    available = get_available_plugins()
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# ============================================================================
# КОНФИГУРАЦИЯ ЛОГИРОВАНИЯ
# ============================================================================

def _setup_file_logging() -> logging.FileHandler:
    """Настройка логирования в файл app.log."""
    project_root = Path(__file__).parent.parent.parent
    log_file = project_root / "app.log"
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s][%(name)s][%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    return file_handler

# Настройка логирования для модуля
_logger = logging.getLogger("src.monitor.factories")
if not _logger.handlers:
    _file_handler = _setup_file_logging()
    _logger.addHandler(_file_handler)
    _logger.setLevel(logging.DEBUG)

logger = _logger

# ============================================================================
# КОНСТАНТЫ
# ============================================================================

# START_CONSTANTS_FACTORIES
DEFAULT_PLUGIN_PRIORITY = 50
MAX_PLUGINS = 20

# Типы плагинов по умолчанию
DEFAULT_PLUGIN_TYPES = [
    'live_stats',
    'final_stats',
    'match_notifier',
]

# END_CONSTANTS_FACTORIES

# ============================================================================
# ПЕРЕЧИСЛЕНИЕ ТИПОВ ПЛАГИНОВ
# ============================================================================

# START_ENUM_PLUGINTYPE
# START_CONTRACT:
# PURPOSE: Перечисление доступных типов плагинов мониторинга
# KEYWORDS: [PATTERN(7): Enum; DOMAIN(9): PluginType; CONCEPT(6): TypeSystem]
# END_CONTRACT

class PluginType(Enum):
    """
    Перечисление типов плагинов мониторинга.
    
    Определяет все доступные типы плагинов, которые могут быть созданы
    через фабричную систему.
    """
    
    # START_ENUM_MEMBER_LIVE_STATS
    # START_CONTRACT:
    # PURPOSE: Плагин live-статистики для реальновременного мониторинга метрик
    # KEYWORDS: [DOMAIN(9): LiveMonitoring; DOMAIN(8): RealTime]
    # END_CONTRACT
    LIVE_STATS = "live_stats"
    # END_ENUM_MEMBER_LIVE_STATS
    
    # START_ENUM_MEMBER_FINAL_STATS
    # START_CONTRACT:
    # PURPOSE: Плагин финальной статистики для итоговых отчётов
    # KEYWORDS: [DOMAIN(9): FinalStats; DOMAIN(8): Statistics]
    # END_CONTRACT
    FINAL_STATS = "final_stats"
    # END_ENUM_MEMBER_FINAL_STATS
    
    # START_ENUM_MEMBER_MATCH_NOTIFIER
    # START_CONTRACT:
    # PURPOSE: Плагин уведомлений о совпадениях
    # KEYWORDS: [DOMAIN(9): Notifications; DOMAIN(8): Matching]
    # END_CONTRACT
    MATCH_NOTIFIER = "match_notifier"
    # END_ENUM_MEMBER_MATCH_NOTIFIER

# END_ENUM_PLUGINTYPE

# ============================================================================
# ДАТАКЛАСС КОНФИГУРАЦИИ ПЛАГИНА
# ============================================================================

# START_DATACLASS_PLUGINCONFIG
# START_CONTRACT:
# PURPOSE: dataclass для хранения конфигурации плагина
# ATTRIBUTES:
# - name: str — уникальное имя плагина
# - plugin_type: PluginType — тип плагина из перечисления
# - config: Dict[str, Any] — словарь конфигурации плагина
# - use_cpp: bool — использовать C++ реализацию (по умолчанию True)
# KEYWORDS: [PATTERN(7): DataClass; DOMAIN(9): Configuration; CONCEPT(6): Settings]
# END_CONTRACT

@dataclass
class PluginConfig:
    """
    Конфигурация плагина для фабрики.
    
    Используется для передачи параметров при создании плагина.
    Содержит имя, тип, конфигурацию и флаг использования C++ реализации.
    
    Attributes:
        name: Уникальное имя плагина
        plugin_type: Тип плагина из перечисления PluginType
        config: Словарь с параметрами конфигурации плагина
        use_cpp: Флаг использования C++ реализации (по умолчанию True)
    """
    
    name: str
    """Уникальное имя плагина"""
    
    plugin_type: PluginType
    """Тип плагина из перечисления PluginType"""
    
    config: Dict[str, Any] = field(default_factory=dict)
    """Словарь конфигурации плагина"""
    
    use_cpp: bool = True
    """Использовать C++ реализацию (по умолчанию True)"""
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразование конфигурации в словарь.
        
        Returns:
            Словарь с данными конфигурации
        """
        return {
            "name": self.name,
            "plugin_type": self.plugin_type.value,
            "config": self.config,
            "use_cpp": self.use_cpp,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginConfig":
        """
        Создание конфигурации из словаря.
        
        Args:
            data: Словарь с данными конфигурации
            
        Returns:
            Экземпляр PluginConfig
        """
        plugin_type_value = data.get("plugin_type", "live_stats")
        if isinstance(plugin_type_value, str):
            plugin_type = PluginType(plugin_type_value)
        else:
            plugin_type = plugin_type_value
            
        return cls(
            name=data.get("name", "unnamed_plugin"),
            plugin_type=plugin_type,
            config=data.get("config", {}),
            use_cpp=data.get("use_cpp", True),
        )

# END_DATACLASS_PLUGINCONFIG

# ============================================================================
# ИСКЛЮЧЕНИЕ ПРИ ОШИБКЕ СОЗДАНИЯ ПЛАГИНА
# ============================================================================

# START_EXCEPTION_PLUGINCREATIONERROR
# START_CONTRACT:
# PURPOSE: Исключение, выбрасываемое при ошибке создания плагина
# KEYWORDS: [PATTERN(7): Exception; DOMAIN(8): ErrorHandling; CONCEPT(6): CustomError]
# END_CONTRACT

class PluginCreationError(Exception):
    """
    Исключение при ошибке создания плагина.
    
    Выбрасывается в случаях, когда не удаётся создать экземпляр плагина:
    - Неизвестный тип плагина
    - Ошибка инициализации
    - Отсутствие необходимых зависимостей
    """
    
    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация исключения с сообщением об ошибке
    # INPUTS:
    # - message: str — сообщение об ошибке
    # - plugin_type: Optional[PluginType] — тип плагина (если применимо)
    # KEYWORDS: [CONCEPT(5): Initialization]
    # END_CONTRACT
    def __init__(self, message: str, plugin_type: Optional[PluginType] = None) -> None:
        """
        Инициализация исключения.
        
        Args:
            message: Сообщение об ошибке
            plugin_type: Тип плагина (опционально)
        """
        self.plugin_type = plugin_type
        full_message = message
        if plugin_type:
            full_message = f"{message} (plugin_type={plugin_type.value})"
        
        super().__init__(full_message)
        logger.error(f"[PluginCreationError][INIT] Ошибка создания плагина: {full_message}")
    # END_METHOD___init__

# END_EXCEPTION_PLUGINCREATIONERROR

# ============================================================================
# ФАБРИЧНЫЕ ФУНКЦИИ
# ============================================================================

# START_FUNCTION_CREATE_PLUGIN
# START_CONTRACT:
# PURPOSE: Создание плагина по конфигурации
# INPUTS:
# - config: PluginConfig — конфигурация плагина
# OUTPUTS:
# - BaseMonitorPlugin — созданный экземпляр плагина
# SIDE_EFFECTS: Создаёт экземпляр указанного типа плагина
# KEYWORDS: [PATTERN(7): Factory; DOMAIN(9): PluginCreation; CONCEPT(6): Instantiation]
# TEST_CONDITIONS_SUCCESS_CRITERIA: Функция должна вернуть экземпляр плагина указанного типа
# END_CONTRACT

def create_plugin(config: PluginConfig) -> Any:
    """
    Создание плагина по конфигурации.
    
    Фабричная функция, которая создаёт экземпляр плагина
    на основе переданной конфигурации. Поддерживает различные
    типы плагинов: live_stats, final_stats, match_notifier.
    
    Args:
        config: Конфигурация плагина
        
    Returns:
        Экземпляр плагина соответствующего типа
        
    Raises:
        PluginCreationError: Если указан неизвестный тип плагина
        
    Note:
        Это заглушка. Полная реализация будет в итерации 1.9.
    """
    logger.info(f"[create_plugin][ConditionCheck] Создание плагина: name={config.name}, type={config.plugin_type.value}, use_cpp={config.use_cpp} [ATTEMPT]")
    
    # Заглушка - полная реализация будет в 1.9
    plugin_type = config.plugin_type
    
    # Импорт базового класса
    try:
        from src.monitor._cpp.plugin_base_wrapper import BaseMonitorPlugin
    except ImportError as e:
        logger.error(f"[create_plugin][ExceptionCaught] Не удалось импортировать BaseMonitorPlugin: {e} [FAIL]")
        raise PluginCreationError(f"Не удалось импортировать базовый класс плагина", plugin_type)
    
    # Создание плагина в зависимости от типа
    if plugin_type == PluginType.LIVE_STATS:
        try:
            from src.monitor._cpp.live_stats_wrapper import LiveStatsPlugin
            plugin = LiveStatsPlugin(config=config.config)
            logger.info(f"[create_plugin][StepComplete] Плагин live_stats создан: {config.name} [SUCCESS]")
            return plugin
        except Exception as e:
            logger.error(f"[create_plugin][ExceptionCaught] Ошибка создания live_stats: {e} [FAIL]")
            raise PluginCreationError(f"Ошибка создания плагина: {e}", plugin_type)
    
    elif plugin_type == PluginType.FINAL_STATS:
        try:
            from src.monitor._cpp.final_stats_wrapper import FinalStatsPlugin
            plugin = FinalStatsPlugin(config=config.config)
            logger.info(f"[create_plugin][StepComplete] Плагин final_stats создан: {config.name} [SUCCESS]")
            return plugin
        except Exception as e:
            logger.error(f"[create_plugin][ExceptionCaught] Ошибка создания final_stats: {e} [FAIL]")
            raise PluginCreationError(f"Ошибка создания плагина: {e}", plugin_type)
    
    elif plugin_type == PluginType.MATCH_NOTIFIER:
        try:
            from src.monitor._cpp.match_notifier_wrapper import MatchNotifierPlugin
            plugin = MatchNotifierPlugin(config=config.config)
            logger.info(f"[create_plugin][StepComplete] Плагин match_notifier создан: {config.name} [SUCCESS]")
            return plugin
        except Exception as e:
            logger.error(f"[create_plugin][ExceptionCaught] Ошибка создания match_notifier: {e} [FAIL]")
            raise PluginCreationError(f"Ошибка создания плагина: {e}", plugin_type)
    
    else:
        logger.error(f"[create_plugin][ConditionCheck] Неизвестный тип плагина: {plugin_type} [FAIL]")
        raise PluginCreationError(f"Неизвестный тип плагина: {plugin_type}", plugin_type)

# END_FUNCTION_CREATE_PLUGIN

# START_FUNCTION_GET_AVAILABLE_PLUGINS
# START_CONTRACT:
# PURPOSE: Получение списка доступных типов плагинов
# OUTPUTS:
# - List[PluginType] — список доступных типов плагинов
# KEYWORDS: [PATTERN(7): Registry; DOMAIN(8): PluginTypes; CONCEPT(6): Enumeration]
# END_CONTRACT

def get_available_plugins() -> List[PluginType]:
    """
    Получение списка доступных типов плагинов.
    
    Возвращает перечень всех типов плагинов, которые могут быть
    созданы через фабричную систему.
    
    Returns:
        Список типов плагинов (PluginType)
    """
    logger.debug(f"[get_available_plugins][ReturnData] Возвращаем доступные типы плагинов [VALUE]")
    return list(PluginType)

# END_FUNCTION_GET_AVAILABLE_PLUGINS

# ============================================================================
# КЛАСС ФАБРИКИ ПЛАГИНОВ (ЗАГЛУШКА)
# ============================================================================

# START_CLASS_PLUGINFACTORY
# START_CONTRACT:
# PURPOSE: Класс фабрики плагинов (заглушка для будущей реализации)
# ATTRIBUTES:
# - _plugins: Dict[str, Any] — словарь созданных плагинов
# KEYWORDS: [PATTERN(7): Factory; DOMAIN(9): PluginFactory; CONCEPT(6): Singleton]
# END_CONTRACT

class PluginFactory:
    """
    Класс фабрики плагинов.
    
    Заглушка для централизованного управления плагинами.
    Полная реализация будет добавлена в итерации 1.9.
    
    Attributes:
        _plugins: Словарь созданных плагинов
    """
    
    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация фабрики плагинов
    # KEYWORDS: [CONCEPT(5): Initialization]
    # END_CONTRACT
    def __init__(self) -> None:
        """Инициализация фабрики плагинов."""
        self._plugins: Dict[str, Any] = {}
        logger.info(f"[PluginFactory][INIT] Фабрика плагинов инициализирована [SUCCESS]")
    # END_METHOD___init__
    
    # START_METHOD_CREATE
    # START_CONTRACT:
    # PURPOSE: Создание плагина через фабрику
    # INPUTS:
    # - config: PluginConfig — конфигурация плагина
    # OUTPUTS:
    # - Any — созданный экземпляр плагина
    # KEYWORDS: [DOMAIN(9): PluginCreation]
    # END_CONTRACT
    def create(self, config: PluginConfig) -> Any:
        """
        Создание плагина через фабрику.
        
        Args:
            config: Конфигурация плагина
            
        Returns:
            Созданный экземпляр плагина
        """
        plugin = create_plugin(config)
        self._plugins[config.name] = plugin
        logger.info(f"[PluginFactory][CREATE] Плагин добавлен в фабрику: {config.name} [SUCCESS]")
        return plugin
    # END_METHOD_CREATE
    
    # START_METHOD_GET
    # START_CONTRACT:
    # PURPOSE: Получение плагина по имени
    # INPUTS:
    # - name: str — имя плагина
    # OUTPUTS:
    # - Optional[Any] — экземпляр плагина или None
    # KEYWORDS: [CONCEPT(5): Getter]
    # END_CONTRACT
    def get(self, name: str) -> Optional[Any]:
        """
        Получение плагина по имени.
        
        Args:
            name: Имя плагина
            
        Returns:
            Экземпляр плагина или None
        """
        return self._plugins.get(name)
    # END_METHOD_GET
    
    # START_METHOD_LIST
    # START_CONTRACT:
    # PURPOSE: Получение списка имён всех созданных плагинов
    # OUTPUTS:
    # - List[str] — список имён плагинов
    # KEYWORDS: [CONCEPT(5): Getter]
    # END_CONTRACT
    def list(self) -> List[str]:
        """
        Получение списка имён всех созданных плагинов.
        
        Returns:
            Список имён плагинов
        """
        return list(self._plugins.keys())
    # END_METHOD_LIST

# END_CLASS_PLUGINFACTORY

# ============================================================================
# ЭКСПОРТ
# ============================================================================

# START_EXPORTS
__all__ = [
    # Перечисления
    "PluginType",
    # Конфигурация
    "PluginConfig",
    # Исключения
    "PluginCreationError",
    # Функции
    "create_plugin",
    "get_available_plugins",
    # Классы
    "PluginFactory",
    # Константы
    "DEFAULT_PLUGIN_PRIORITY",
    "MAX_PLUGINS",
    "DEFAULT_PLUGIN_TYPES",
]

# END_EXPORTS

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ ПРИ ИМПОРТЕ
# ============================================================================

logger.info(f"[INIT] Модуль factories загружен, доступно плагинов: {len(PluginType)} [INFO]")
