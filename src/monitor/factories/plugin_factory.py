# FILE: src/monitor/factories/plugin_factory.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Фабрика плагинов для централизованного создания и управления экземплярами плагинов мониторинга с поддержкой C++ и Python реализаций
# SCOPE: Создание плагинов, управление жизненным циклом, регистрация и поиск плагинов, конфигурация
# INPUT: Конфигурация плагинов (PluginConfig), имена плагинов, флаги использования C++
# OUTPUT: Экземпляры плагинов (BaseMonitorPlugin), зарегистрированные плагины, информация о приоритетах
# KEYWORDS: [DOMAIN(9): PluginFactory; DOMAIN(8): PluginCreation; TECH(7): Singleton; TECH(6): ThreadSafe; CONCEPT(6): FactoryPattern]
# LINKS: [USES_API(8): src.monitor._cpp.live_stats_wrapper; USES_API(8): src.monitor._cpp.final_stats_wrapper; USES_API(8): src.monitor._cpp.match_notifier_wrapper; USES_API(7): src.monitor.plugins.base]
# LINKS_TO_SPECIFICATION: [create_plugin_factory_plan.md]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 10 [Основная фабрика плагинов с поддержкой singleton] => PluginFactory
# METHOD 9 [Получение единственного экземпляра фабрики] => get_instance
# METHOD 8 [Создание плагина по конфигурации] => create_plugin
# METHOD 8 [Создание плагина live-статистики] => create_live_stats
# METHOD 8 [Создание плагина финальной статистики] => create_final_stats
# METHOD 8 [Создание плагина уведомлений] => create_match_notifier
# METHOD 7 [Создание набора плагинов по умолчанию] => create_default_set
# METHOD 7 [Регистрация плагина] => register_plugin
# METHOD 7 [Удаление регистрации плагина] => unregister_plugin
# METHOD 6 [Получение плагина по имени] => get_plugin
# METHOD 6 [Получение всех плагинов] => get_all_plugins
# METHOD 6 [Получение плагинов по типу] => get_plugins_by_type
# METHOD 5 [Очистка всех плагинов] => clear_all
# METHOD 5 [Проверка существования плагина] => has_plugin
# METHOD 5 [Установка приоритета по умолчанию] => set_default_use_cpp
# METHOD 4 [Получение приоритета по умолчанию] => get_default_use_cpp
# METHOD 4 [Установка приоритета плагина] => set_plugin_priority
# METHOD 4 [Получение приоритета плагина] => get_plugin_priority
# PROP 7 [Количество зарегистрированных плагинов] => plugin_count
# PROP 6 [Использовать C++ по умолчанию] => default_use_cpp
# END_MODULE_MAP
# START_USE_CASES:
# - [get_instance]: System (Startup) -> GetSingletonInstance -> FactoryReady
# - [create_plugin]: System (PluginCreation) -> CreatePluginFromConfig -> PluginInstanceCreated
# - [create_live_stats]: User (Monitoring) -> CreateLiveStatsPlugin -> LiveStatsReady
# - [create_default_set]: System (Initialization) -> CreateDefaultPlugins -> AllPluginsReady
# - [register_plugin]: System (PluginManagement) -> RegisterPluginInstance -> PluginRegistered
# - [get_plugin]: User (Query) -> GetPluginByName -> PluginInstanceReturned
# END_USE_CASES
"""
Модуль фабрики плагинов — Полная реализация.

Предоставляет:
- Класс PluginFactory для централизованного создания плагинов
- Поддержка C++ и Python реализаций с автоматическим fallback
- Потокобезопасный singleton pattern
- Управление жизненным циклом плагинов

Пример использования:
    from src.monitor.factories.plugin_factory import PluginFactory
    
    # Получение экземпляра фабрики
    factory = PluginFactory.get_instance()
    
    # Создание плагина live stats
    plugin = factory.create_live_stats("my_stats")
    
    # Регистрация плагина
    factory.register_plugin("my_stats", plugin)
    
    # Получение плагина
    retrieved = factory.get_plugin("my_stats")
"""

import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

# Импорт базовых классов из модуля factories
from src.monitor.factories import (
    PluginConfig,
    PluginCreationError,
    PluginType,
    DEFAULT_PLUGIN_PRIORITY,
    MAX_PLUGINS,
)

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
_logger = logging.getLogger("src.monitor.factories.plugin_factory")
if not _logger.handlers:
    _file_handler = _setup_file_logging()
    _logger.addHandler(_file_handler)
    _logger.setLevel(logging.DEBUG)

logger = _logger

# ============================================================================
# КОНСТАНТЫ
# ============================================================================

# START_CONSTANTS_PLUGIN_FACTORY

# Значения по умолчанию для конфигурации плагинов
DEFAULT_LIVE_STATS_CONFIG = {
    'update_interval': 1.0,
    'max_history': 100,
    'enable_display': True,
}

DEFAULT_FINAL_STATS_CONFIG = {
    'export_formats': ['json', 'csv'],
    'auto_export': False,
}

DEFAULT_MATCH_NOTIFIER_CONFIG = {
    'notifications_enabled': True,
    'sound_enabled': False,
    'min_match_score': 0.8,
}

# END_CONSTANTS_PLUGIN_FACTORY

# ============================================================================
# КЛАСС PLUGINFACTORY
# ============================================================================

# START_CLASS_PLUGINFACTORY
# START_CONTRACT:
# PURPOSE: Фабрика плагинов мониторинга с поддержкой singleton и потокобезопасности
# ATTRIBUTES:
# - _instance: Optional[PluginFactory] — единственный экземпляр класса
# - _lock: threading.Lock — блокировка для потокобезопасности
# - _plugins: Dict[str, Any] — словарь зарегистрированных плагинов
# - _plugin_priorities: Dict[str, int] — приоритеты плагинов
# - _plugin_configs: Dict[str, PluginConfig] — конфигурации плагинов
# - _default_use_cpp: bool — использовать C++ по умолчанию
# KEYWORDS: [PATTERN(8): Singleton; DOMAIN(9): PluginFactory; TECH(6): ThreadSafe; CONCEPT(7): Factory]
# LINKS: [USES_API(7): src.monitor.factories.PluginConfig; USES_API(6): threading.Lock]
# END_CONTRACT


class PluginFactory:
    """
    Фабрика плагинов мониторинга.
    
    Обеспечивает:
    - Централизованное создание плагинов с поддержкой C++ и Python
    - Потокобезопасный singleton pattern
    - Управление жизненным циклом плагинов
    - Конфигурацию и приоритизацию плагинов
    
    Attributes:
        _instance: Единственный экземпляр класса
        _lock: Блокировка для потокобезопасности
        _plugins: Словарь зарегистрированных плагинов
        _plugin_priorities: Словарь приоритетов плагинов
        _plugin_configs: Словарь конфигураций плагинов
        _default_use_cpp: Флаг использования C++ по умолчанию
    
    Note:
        Это полная реализация singleton фабрики плагинов.
        Все методы синхронизированы для потокобезопасности.
    """
    
    # START_ATTRIBUTE_INSTANCE
    # START_CONTRACT:
    # PURPOSE: Хранение единственного экземпляра класса
    # KEYWORDS: [CONCEPT(5): Singleton]
    # END_CONTRACT
    _instance: Optional['PluginFactory'] = None
    # END_ATTRIBUTE_INSTANCE
    
    # START_ATTRIBUTE_LOCK
    # START_CONTRACT:
    # PURPOSE: Блокировка для потокобезопасной инициализации
    # KEYWORDS: [TECH(6): ThreadSafe; CONCEPT(5): Locking]
    # END_CONTRACT
    _lock: threading.Lock = threading.Lock()
    # END_ATTRIBUTE_LOCK
    
    # START_METHOD_GET_INSTANCE
    # START_CONTRACT:
    # PURPOSE: Получение единственного экземпляра фабрики (singleton)
    # OUTPUTS:
    # - PluginFactory — единственный экземпляр фабрики
    # KEYWORDS: [PATTERN(8): Singleton; TECH(6): ThreadSafe]
    # TEST_CONDITIONS_SUCCESS_CRITERIA: Метод должен всегда возвращать один и тот же экземпляр
    # END_CONTRACT
    
    @classmethod
    def get_instance(cls) -> 'PluginFactory':
        """
        Получение единственного экземпляра фабрики плагинов.
        
        Использует double-checked locking pattern для потокобезопасности.
        
        Returns:
            Единственный экземпляр PluginFactory
            
        Example:
            >>> factory = PluginFactory.get_instance()
            >>> factory2 = PluginFactory.get_instance()
            >>> factory is factory2
            True
        """
        logger.debug(f"[PluginFactory][GET_INSTANCE][ConditionCheck] Запрос экземпляра фабрики [ATTEMPT]")
        
        # First check without lock (performance)
        if cls._instance is None:
            # Acquire lock for thread safety
            with cls._lock:
                # Second check after acquiring lock
                if cls._instance is None:
                    logger.info(f"[PluginFactory][GET_INSTANCE][StepComplete] Создание нового экземпляра фабрики [ATTEMPT]")
                    cls._instance = super().__new__(cls)
                    # Initialize the instance directly
                    cls._instance._plugins = {}
                    cls._instance._plugin_priorities = {}
                    cls._instance._plugin_configs = {}
                    cls._instance._default_use_cpp = True
        
        logger.debug(f"[PluginFactory][GET_INSTANCE][ReturnData] Экземпляр фабрики получен [SUCCESS]")
        return cls._instance
    # END_METHOD_GET_INSTANCE
    
    # START_METHOD___INIT__
    # START_CONTRACT:
    # PURPOSE: Инициализация фабрики плагинов (внутренний метод)
    # KEYWORDS: [CONCEPT(5): Initialization]
    # END_CONTRACT
    
    def __init__(self) -> None:
        """Инициализация фабрики плагинов."""
        # Prevent re-initialization if already initialized via get_instance
        if hasattr(self, '_plugins') and self._plugins is not None:
            logger.debug(f"[PluginFactory][INIT] Фабрика уже инициализирована [INFO]")
            return
        
        logger.info(f"[PluginFactory][INIT] Начало инициализации фабрики плагинов [ATTEMPT]")
        
        # Инициализация внутренних структур
        self._plugins = {}
        self._plugin_priorities = {}
        self._plugin_configs = {}
        self._default_use_cpp = True
        
        logger.info(f"[PluginFactory][INIT] Фабрика плагинов успешно инициализирована [SUCCESS]")
    # END_METHOD___INIT__
    
    # ============================================================================
    # СВОЙСТВА (PROPERTIES)
    # ============================================================================
    
    # START_PROPERTY_PLUGIN_COUNT
    # START_CONTRACT:
    # PURPOSE: Получение количества зарегистрированных плагинов
    # OUTPUTS:
    # - int — количество плагинов
    # KEYWORDS: [CONCEPT(5): Property; DOMAIN(6): Count]
    # END_CONTRACT
    
    @property
    def plugin_count(self) -> int:
        """
        Количество зарегистрированных плагинов.
        
        Returns:
            Количество плагинов в фабрике
        """
        count = len(self._plugins)
        logger.debug(f"[PluginFactory][PLUGIN_COUNT][ReturnData] Количество плагинов: {count} [VALUE]")
        return count
    # END_PROPERTY_PLUGIN_COUNT
    
    # START_PROPERTY_DEFAULT_USE_CPP
    # START_CONTRACT:
    # PURPOSE: Получение/установка флага использования C++ по умолчанию
    # OUTPUTS:
    # - bool — использовать C++ по умолчанию
    # KEYWORDS: [CONCEPT(5): Property; TECH(5): Configuration]
    # END_CONTRACT
    
    @property
    def default_use_cpp(self) -> bool:
        """
        Флаг использования C++ реализации по умолчанию.
        
        Returns:
            True если используется C++, False для Python
        """
        value = self._default_use_cpp
        logger.debug(f"[PluginFactory][DEFAULT_USE_CPP][ReturnData] Значение: {value} [VALUE]")
        return value
    
    @default_use_cpp.setter
    def default_use_cpp(self, value: bool) -> None:
        """
        Установка флага использования C++ реализации по умолчанию.
        
        Args:
            value: True для использования C++, False для Python
        """
        logger.info(f"[PluginFactory][DEFAULT_USE_CPP][Params] Установка значения: {value} [ATTEMPT]")
        self._default_use_cpp = value
        logger.info(f"[PluginFactory][DEFAULT_USE_CPP][StepComplete] Значение установлено: {value} [SUCCESS]")
    # END_PROPERTY_DEFAULT_USE_CPP
    
    # ============================================================================
    # МЕТОДЫ СОЗДАНИЯ ПЛАГИНОВ
    # ============================================================================
    
    # START_METHOD_CREATE_PLUGIN
    # START_CONTRACT:
    # PURPOSE: Создание плагина по конфигурации
    # INPUTS:
    # - config: PluginConfig — конфигурация плагина
    # OUTPUTS:
    # - Any — созданный экземпляр плагина
    # SIDE_EFFECTS: Создаёт экземпляр плагина указанного типа
    # KEYWORDS: [DOMAIN(9): PluginCreation; PATTERN(7): Factory]
    # TEST_CONDITIONS_SUCCESS_CRITERIA: Метод должен вернуть экземпляр плагина указанного типа
    # END_CONTRACT
    
    def create_plugin(self, config: PluginConfig) -> Any:
        """
        Создание плагина по конфигурации.
        
        Args:
            config: Конфигурация плагина
            
        Returns:
            Экземпляр созданного плагина
            
        Raises:
            PluginCreationError: При ошибке создания плагина
        """
        logger.info(f"[PluginFactory][CREATE_PLUGIN][Params] name={config.name}, type={config.plugin_type.value}, use_cpp={config.use_cpp} [ATTEMPT]")
        
        plugin_type = config.plugin_type
        
        # Определение типа плагина и создание
        try:
            if plugin_type == PluginType.LIVE_STATS:
                plugin = self._create_live_stats_impl(config)
            elif plugin_type == PluginType.FINAL_STATS:
                plugin = self._create_final_stats_impl(config)
            elif plugin_type == PluginType.MATCH_NOTIFIER:
                plugin = self._create_match_notifier_impl(config)
            else:
                logger.error(f"[PluginFactory][CREATE_PLUGIN][ConditionCheck] Неизвестный тип плагина: {plugin_type} [FAIL]")
                raise PluginCreationError(f"Неизвестный тип плагина: {plugin_type}", plugin_type)
            
            logger.info(f"[PluginFactory][CREATE_PLUGIN][StepComplete] Плагин создан: {config.name} [SUCCESS]")
            return plugin
            
        except Exception as e:
            logger.error(f"[PluginFactory][CREATE_PLUGIN][ExceptionCaught] Ошибка создания плагина: {e} [FAIL]")
            raise PluginCreationError(f"Ошибка создания плагина: {e}", plugin_type)
    # END_METHOD_CREATE_PLUGIN
    
    # START_METHOD_CREATE_LIVE_STATS
    # START_CONTRACT:
    # PURPOSE: Создание плагина live-статистики
    # INPUTS:
    # - name: str — имя плагина
    # - config: Optional[Dict] — конфигурация плагина
    # - use_cpp: bool — использовать C++ реализацию
    # OUTPUTS:
    # - Any — созданный экземпляр плагина live stats
    # KEYWORDS: [DOMAIN(9): LiveStats; CONCEPT(6): PluginCreation]
    # END_CONTRACT
    
    def create_live_stats(self, name: str, config: Optional[Dict] = None, use_cpp: Optional[bool] = None) -> Any:
        """
        Создание плагина live-статистики.
        
        Args:
            name: Уникальное имя плагина
            config: Конфигурация плагина (опционально)
            use_cpp: Использовать C++ реализацию (опционально, по умолчанию из фабрики)
            
        Returns:
            Экземпляр плагина live stats
            
        Example:
            >>> plugin = factory.create_live_stats("my_stats", {"update_interval": 0.5})
        """
        logger.info(f"[PluginFactory][CREATE_LIVE_STATS][Params] name={name}, use_cpp={use_cpp} [ATTEMPT]")
        
        # Определение флага использования C++
        if use_cpp is None:
            use_cpp = self._default_use_cpp
        
        # Создание конфигурации
        plugin_config = PluginConfig(
            name=name,
            plugin_type=PluginType.LIVE_STATS,
            config=config or DEFAULT_LIVE_STATS_CONFIG.copy(),
            use_cpp=use_cpp
        )
        
        plugin = self._create_live_stats_impl(plugin_config)
        
        logger.info(f"[PluginFactory][CREATE_LIVE_STATS][StepComplete] Плагин live_stats создан: {name} [SUCCESS]")
        return plugin
    # END_METHOD_CREATE_LIVE_STATS
    
    # START_METHOD_CREATE_FINAL_STATS
    # START_CONTRACT:
    # PURPOSE: Создание плагина финальной статистики
    # INPUTS:
    # - name: str — имя плагина
    # - config: Optional[Dict] — конфигурация плагина
    # - use_cpp: bool — использовать C++ реализацию
    # OUTPUTS:
    # - Any — созданный экземпляр плагина final stats
    # KEYWORDS: [DOMAIN(9): FinalStats; CONCEPT(6): PluginCreation]
    # END_CONTRACT
    
    def create_final_stats(self, name: str, config: Optional[Dict] = None, use_cpp: Optional[bool] = None) -> Any:
        """
        Создание плагина финальной статистики.
        
        Args:
            name: Уникальное имя плагина
            config: Конфигурация плагина (опционально)
            use_cpp: Использовать C++ реализацию (опционально, по умолчанию из фабрики)
            
        Returns:
            Экземпляр плагина final stats
            
        Example:
            >>> plugin = factory.create_final_stats("final", {"export_formats": ["json"]})
        """
        logger.info(f"[PluginFactory][CREATE_FINAL_STATS][Params] name={name}, use_cpp={use_cpp} [ATTEMPT]")
        
        # Определение флага использования C++
        if use_cpp is None:
            use_cpp = self._default_use_cpp
        
        # Создание конфигурации
        plugin_config = PluginConfig(
            name=name,
            plugin_type=PluginType.FINAL_STATS,
            config=config or DEFAULT_FINAL_STATS_CONFIG.copy(),
            use_cpp=use_cpp
        )
        
        plugin = self._create_final_stats_impl(plugin_config)
        
        logger.info(f"[PluginFactory][CREATE_FINAL_STATS][StepComplete] Плагин final_stats создан: {name} [SUCCESS]")
        return plugin
    # END_METHOD_CREATE_FINAL_STATS
    
    # START_METHOD_CREATE_MATCH_NOTIFIER
    # START_CONTRACT:
    # PURPOSE: Создание плагина уведомлений о совпадениях
    # INPUTS:
    # - name: str — имя плагина
    # - config: Optional[Dict] — конфигурация плагина
    # - use_cpp: bool — использовать C++ реализацию
    # OUTPUTS:
    # - Any — созданный экземпляр плагина match notifier
    # KEYWORDS: [DOMAIN(9): MatchNotifier; CONCEPT(6): PluginCreation]
    # END_CONTRACT
    
    def create_match_notifier(self, name: str, config: Optional[Dict] = None, use_cpp: Optional[bool] = None) -> Any:
        """
        Создание плагина уведомлений о совпадениях.
        
        Args:
            name: Уникальное имя плагина
            config: Конфигурация плагина (опционально)
            use_cpp: Использовать C++ реализацию (опционально, по умолчанию из фабрики)
            
        Returns:
            Экземпляр плагина match notifier
            
        Example:
            >>> plugin = factory.create_match_notifier("notifier", {"sound_enabled": True})
        """
        logger.info(f"[PluginFactory][CREATE_MATCH_NOTIFIER][Params] name={name}, use_cpp={use_cpp} [ATTEMPT]")
        
        # Определение флага использования C++
        if use_cpp is None:
            use_cpp = self._default_use_cpp
        
        # Создание конфигурации
        plugin_config = PluginConfig(
            name=name,
            plugin_type=PluginType.MATCH_NOTIFIER,
            config=config or DEFAULT_MATCH_NOTIFIER_CONFIG.copy(),
            use_cpp=use_cpp
        )
        
        plugin = self._create_match_notifier_impl(plugin_config)
        
        logger.info(f"[PluginFactory][CREATE_MATCH_NOTIFIER][StepComplete] Плагин match_notifier создан: {name} [SUCCESS]")
        return plugin
    # END_METHOD_CREATE_MATCH_NOTIFIER
    
    # START_METHOD_CREATE_DEFAULT_SET
    # START_CONTRACT:
    # PURPOSE: Создание стандартного набора плагинов
    # OUTPUTS:
    # - Dict[str, Any] — словарь созданных плагинов
    # KEYWORDS: [DOMAIN(8): DefaultSet; CONCEPT(6): BatchCreation]
    # END_CONTRACT
    
    def create_default_set(self) -> Dict[str, Any]:
        """
        Создание стандартного набора плагинов.
        
        Создаёт и регистрирует все плагины по умолчанию:
        - live_stats: Плагин live-статистики
        - final_stats: Плагин финальной статистики
        - match_notifier: Плагин уведомлений
        
        Returns:
            Словарь созданных плагинов {name: plugin}
            
        Example:
            >>> plugins = factory.create_default_set()
            >>> print(f"Создано плагинов: {len(plugins)}")
        """
        logger.info(f"[PluginFactory][CREATE_DEFAULT_SET][ConditionCheck] Создание стандартного набора плагинов [ATTEMPT]")
        
        default_plugins = {}
        
        # Создание live_stats
        try:
            live_stats = self.create_live_stats("live_stats")
            default_plugins["live_stats"] = live_stats
            self.register_plugin("live_stats", live_stats, priority=50)
            logger.info(f"[PluginFactory][CREATE_DEFAULT_SET][StepComplete] live_stats создан и зарегистрирован [SUCCESS]")
        except Exception as e:
            logger.error(f"[PluginFactory][CREATE_DEFAULT_SET][ExceptionCaught] Ошибка создания live_stats: {e} [FAIL]")
        
        # Создание final_stats
        try:
            final_stats = self.create_final_stats("final_stats")
            default_plugins["final_stats"] = final_stats
            self.register_plugin("final_stats", final_stats, priority=100)
            logger.info(f"[PluginFactory][CREATE_DEFAULT_SET][StepComplete] final_stats создан и зарегистрирован [SUCCESS]")
        except Exception as e:
            logger.error(f"[PluginFactory][CREATE_DEFAULT_SET][ExceptionCaught] Ошибка создания final_stats: {e} [FAIL]")
        
        # Создание match_notifier
        try:
            match_notifier = self.create_match_notifier("match_notifier")
            default_plugins["match_notifier"] = match_notifier
            self.register_plugin("match_notifier", match_notifier, priority=10)
            logger.info(f"[PluginFactory][CREATE_DEFAULT_SET][StepComplete] match_notifier создан и зарегистрирован [SUCCESS]")
        except Exception as e:
            logger.error(f"[PluginFactory][CREATE_DEFAULT_SET][ExceptionCaught] Ошибка создания match_notifier: {e} [FAIL]")
        
        logger.info(f"[PluginFactory][CREATE_DEFAULT_SET][ReturnData] Создано плагинов: {len(default_plugins)} [SUCCESS]")
        return default_plugins
    # END_METHOD_CREATE_DEFAULT_SET
    
    # ============================================================================
    # ВНУТРЕННИЕ МЕТОДЫ СОЗДАНИЯ (С ПОДДЕРЖКОЙ FALLBACK)
    # ============================================================================
    
    # START_METHOD_CREATE_LIVE_STATS_IMPL
    # START_CONTRACT:
    # PURPOSE: Внутренняя реализация создания live stats с fallback на Python
    # INPUTS:
    # - config: PluginConfig — конфигурация плагина
    # OUTPUTS:
    # - Any — экземпляр плагина
    # KEYWORDS: [TECH(6): Fallback; DOMAIN(9): LiveStats]
    # END_CONTRACT
    
    def _create_live_stats_impl(self, config: PluginConfig) -> Any:
        """
        Внутренняя реализация создания плагина live stats.
        
        Пробует создать C++ реализацию, при неудаче использует Python fallback.
        
        Args:
            config: Конфигурация плагина
            
        Returns:
            Экземпляр плагина live stats
        """
        logger.debug(f"[PluginFactory][CREATE_LIVE_STATS_IMPL][ConditionCheck] use_cpp={config.use_cpp} [ATTEMPT]")
        
        # Пробуем C++ реализацию
        if config.use_cpp:
            try:
                from src.monitor._cpp.live_stats_wrapper import LiveStatsPlugin
                plugin = LiveStatsPlugin(config=config.config)
                logger.info(f"[PluginFactory][CREATE_LIVE_STATS_IMPL][StepComplete] Создан LiveStatsPlugin (C++) [SUCCESS]")
                return plugin
            except ImportError as e:
                logger.warning(f"[PluginFactory][CREATE_LIVE_STATS_IMPL][ExceptionCaught] Не удалось импортировать C++ реализацию: {e} [ATTEMPT]")
            except Exception as e:
                logger.warning(f"[PluginFactory][CREATE_LIVE_STATS_IMPL][ExceptionCaught] Ошибка создания C++ плагина: {e} [ATTEMPT]")
        
        # Fallback на Python реализацию
        try:
            from src.monitor.plugins.live_stats import LiveStatsPlugin
            plugin = LiveStatsPlugin()
            logger.info(f"[PluginFactory][CREATE_LIVE_STATS_IMPL][StepComplete] Создан LiveStatsPlugin (Python) [SUCCESS]")
            return plugin
        except ImportError as e:
            logger.warning(f"[PluginFactory][CREATE_LIVE_STATS_IMPL][ExceptionCaught] Не удалось импортировать Python реализацию: {e} [ATTEMPT]")
        except Exception as e:
            logger.warning(f"[PluginFactory][CREATE_LIVE_STATS_IMPL][ExceptionCaught] Ошибка создания Python плагина: {e} [ATTEMPT]")
        
        # Если Python недоступен, пробуем C++ реализацию как fallback
        try:
            from src.monitor._cpp.live_stats_wrapper import LiveStatsPlugin
            plugin = LiveStatsPlugin(config=config.config)
            logger.info(f"[PluginFactory][CREATE_LIVE_STATS_IMPL][StepComplete] Создан LiveStatsPlugin (C++ fallback) [SUCCESS]")
            return plugin
        except Exception as e:
            logger.error(f"[PluginFactory][CREATE_LIVE_STATS_IMPL][ExceptionCaught] Не удалось создать плагин: {e} [FAIL]")
            raise PluginCreationError(f"Не удалось создать плагин live_stats: {e}", PluginType.LIVE_STATS)
    # END_METHOD_CREATE_LIVE_STATS_IMPL
    
    # START_METHOD_CREATE_FINAL_STATS_IMPL
    # START_CONTRACT:
    # PURPOSE: Внутренняя реализация создания final stats с fallback на Python
    # INPUTS:
    # - config: PluginConfig — конфигурация плагина
    # OUTPUTS:
    # - Any — экземпляр плагина
    # KEYWORDS: [TECH(6): Fallback; DOMAIN(9): FinalStats]
    # END_CONTRACT
    
    def _create_final_stats_impl(self, config: PluginConfig) -> Any:
        """
        Внутренняя реализация создания плагина final stats.
        
        Пробует создать C++ реализацию, при неудаче использует Python fallback.
        
        Args:
            config: Конфигурация плагина
            
        Returns:
            Экземпляр плагина final stats
        """
        logger.debug(f"[PluginFactory][CREATE_FINAL_STATS_IMPL][ConditionCheck] use_cpp={config.use_cpp} [ATTEMPT]")
        
        # Пробуем C++ реализацию
        if config.use_cpp:
            try:
                from src.monitor._cpp.final_stats_wrapper import FinalStatsPlugin
                plugin = FinalStatsPlugin(config=config.config)
                logger.info(f"[PluginFactory][CREATE_FINAL_STATS_IMPL][StepComplete] Создан FinalStatsPlugin (C++) [SUCCESS]")
                return plugin
            except ImportError as e:
                logger.warning(f"[PluginFactory][CREATE_FINAL_STATS_IMPL][ExceptionCaught] Не удалось импортировать C++ реализацию: {e} [ATTEMPT]")
            except Exception as e:
                logger.warning(f"[PluginFactory][CREATE_FINAL_STATS_IMPL][ExceptionCaught] Ошибка создания C++ плагина: {e} [ATTEMPT]")
        
        # Fallback на Python реализацию
        try:
            from src.monitor.plugins.final_stats import FinalStatsPlugin
            plugin = FinalStatsPlugin()
            logger.info(f"[PluginFactory][CREATE_FINAL_STATS_IMPL][StepComplete] Создан FinalStatsPlugin (Python) [SUCCESS]")
            return plugin
        except ImportError as e:
            logger.warning(f"[PluginFactory][CREATE_FINAL_STATS_IMPL][ExceptionCaught] Не удалось импортировать Python реализацию: {e} [ATTEMPT]")
        except Exception as e:
            logger.warning(f"[PluginFactory][CREATE_FINAL_STATS_IMPL][ExceptionCaught] Ошибка создания Python плагина: {e} [ATTEMPT]")
        
        # Если Python недоступен, пробуем C++ реализацию как fallback
        try:
            from src.monitor._cpp.final_stats_wrapper import FinalStatsPlugin
            plugin = FinalStatsPlugin(config=config.config)
            logger.info(f"[PluginFactory][CREATE_FINAL_STATS_IMPL][StepComplete] Создан FinalStatsPlugin (C++ fallback) [SUCCESS]")
            return plugin
        except Exception as e:
            logger.error(f"[PluginFactory][CREATE_FINAL_STATS_IMPL][ExceptionCaught] Не удалось создать плагин: {e} [FAIL]")
            raise PluginCreationError(f"Не удалось создать плагин final_stats: {e}", PluginType.FINAL_STATS)
    # END_METHOD_CREATE_FINAL_STATS_IMPL
    
    # START_METHOD_CREATE_MATCH_NOTIFIER_IMPL
    # START_CONTRACT:
    # PURPOSE: Внутренняя реализация создания match notifier с fallback на Python
    # INPUTS:
    # - config: PluginConfig — конфигурация плагина
    # OUTPUTS:
    # - Any — экземпляр плагина
    # KEYWORDS: [TECH(6): Fallback; DOMAIN(9): MatchNotifier]
    # END_CONTRACT
    
    def _create_match_notifier_impl(self, config: PluginConfig) -> Any:
        """
        Внутренняя реализация создания плагина match notifier.
        
        Пробует создать C++ реализацию, при неудаче использует Python fallback.
        
        Args:
            config: Конфигурация плагина
            
        Returns:
            Экземпляр плагина match notifier
        """
        logger.debug(f"[PluginFactory][CREATE_MATCH_NOTIFIER_IMPL][ConditionCheck] use_cpp={config.use_cpp} [ATTEMPT]")
        
        # Пробуем C++ реализацию
        if config.use_cpp:
            try:
                from src.monitor._cpp.match_notifier_wrapper import MatchNotifierPlugin
                plugin = MatchNotifierPlugin(config=config.config)
                logger.info(f"[PluginFactory][CREATE_MATCH_NOTIFIER_IMPL][StepComplete] Создан MatchNotifierPlugin (C++) [SUCCESS]")
                return plugin
            except ImportError as e:
                logger.warning(f"[PluginFactory][CREATE_MATCH_NOTIFIER_IMPL][ExceptionCaught] Не удалось импортировать C++ реализацию: {e} [ATTEMPT]")
            except Exception as e:
                logger.warning(f"[PluginFactory][CREATE_MATCH_NOTIFIER_IMPL][ExceptionCaught] Ошибка создания C++ плагина: {e} [ATTEMPT]")
        
        # Fallback на Python реализацию
        try:
            from src.monitor.plugins.match_notifier import MatchNotifierPlugin
            plugin = MatchNotifierPlugin()
            logger.info(f"[PluginFactory][CREATE_MATCH_NOTIFIER_IMPL][StepComplete] Создан MatchNotifierPlugin (Python) [SUCCESS]")
            return plugin
        except ImportError as e:
            logger.warning(f"[PluginFactory][CREATE_MATCH_NOTIFIER_IMPL][ExceptionCaught] Не удалось импортировать Python реализацию: {e} [ATTEMPT]")
        except Exception as e:
            logger.warning(f"[PluginFactory][CREATE_MATCH_NOTIFIER_IMPL][ExceptionCaught] Ошибка создания Python плагина: {e} [ATTEMPT]")
        
        # Если Python недоступен, пробуем C++ реализацию как fallback
        try:
            from src.monitor._cpp.match_notifier_wrapper import MatchNotifierPlugin
            plugin = MatchNotifierPlugin(config=config.config)
            logger.info(f"[PluginFactory][CREATE_MATCH_NOTIFIER_IMPL][StepComplete] Создан MatchNotifierPlugin (C++ fallback) [SUCCESS]")
            return plugin
        except Exception as e:
            logger.error(f"[PluginFactory][CREATE_MATCH_NOTIFIER_IMPL][ExceptionCaught] Не удалось создать плагин: {e} [FAIL]")
            raise PluginCreationError(f"Не удалось создать плагин match_notifier: {e}", PluginType.MATCH_NOTIFIER)
    # END_METHOD_CREATE_MATCH_NOTIFIER_IMPL
    
    # ============================================================================
    # МЕТОДЫ УПРАВЛЕНИЯ ПЛАГИНАМИ
    # ============================================================================
    
    # START_METHOD_REGISTER_PLUGIN
    # START_CONTRACT:
    # PURPOSE: Регистрация созданного плагина
    # INPUTS:
    # - name: str — имя плагина
    # - plugin: Any — экземпляр плагина
    # - priority: int — приоритет плагина
    # KEYWORDS: [CONCEPT(6): Registration; DOMAIN(8): PluginManagement]
    # END_CONTRACT
    
    def register_plugin(self, name: str, plugin: Any, priority: int = DEFAULT_PLUGIN_PRIORITY) -> None:
        """
        Регистрация плагина в фабрике.
        
        Args:
            name: Уникальное имя плагина
            plugin: Экземпляр плагина
            priority: Приоритет плагина (опционально)
            
        Example:
            >>> factory.register_plugin("my_plugin", plugin, priority=75)
        """
        logger.info(f"[PluginFactory][REGISTER_PLUGIN][Params] name={name}, priority={priority} [ATTEMPT]")
        
        # Проверка лимита плагинов
        if len(self._plugins) >= MAX_PLUGINS and name not in self._plugins:
            logger.error(f"[PluginFactory][REGISTER_PLUGIN][ConditionCheck] Достигнут максимум плагинов: {MAX_PLUGINS} [FAIL]")
            raise PluginCreationError(f"Достигнут максимум плагинов: {MAX_PLUGINS}")
        
        # Регистрация плагина
        self._plugins[name] = plugin
        self._plugin_priorities[name] = priority
        
        logger.info(f"[PluginFactory][REGISTER_PLUGIN][StepComplete] Плагин зарегистрирован: {name} [SUCCESS]")
    # END_METHOD_REGISTER_PLUGIN
    
    # START_METHOD_UNREGISTER_PLUGIN
    # START_CONTRACT:
    # PURPOSE: Удаление регистрации плагина
    # INPUTS:
    # - name: str — имя плагина
    # KEYWORDS: [CONCEPT(6): Unregistration; DOMAIN(8): PluginManagement]
    # END_CONTRACT
    
    def unregister_plugin(self, name: str) -> bool:
        """
        Удаление плагина из реестра.
        
        Args:
            name: Имя плагина для удаления
            
        Returns:
            True если плагин был удалён, False если не найден
        """
        logger.info(f"[PluginFactory][UNREGISTER_PLUGIN][Params] name={name} [ATTEMPT]")
        
        if name in self._plugins:
            del self._plugins[name]
            
            if name in self._plugin_priorities:
                del self._plugin_priorities[name]
                
            if name in self._plugin_configs:
                del self._plugin_configs[name]
            
            logger.info(f"[PluginFactory][UNREGISTER_PLUGIN][StepComplete] Плагин удалён: {name} [SUCCESS]")
            return True
        
        logger.warning(f"[PluginFactory][UNREGISTER_PLUGIN][ConditionCheck] Плагин не найден: {name} [FAIL]")
        return False
    # END_METHOD_UNREGISTER_PLUGIN
    
    # START_METHOD_GET_PLUGIN
    # START_CONTRACT:
    # PURPOSE: Получение плагина по имени
    # INPUTS:
    # - name: str — имя плагина
    # OUTPUTS:
    # - Optional[Any] — экземпляр плагина или None
    # KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): PluginQuery]
    # END_CONTRACT
    
    def get_plugin(self, name: str) -> Optional[Any]:
        """
        Получение плагина по имени.
        
        Args:
            name: Имя плагина
            
        Returns:
            Экземпляр плагина или None если не найден
        """
        logger.debug(f"[PluginFactory][GET_PLUGIN][Params] name={name} [ATTEMPT]")
        
        plugin = self._plugins.get(name)
        
        if plugin:
            logger.debug(f"[PluginFactory][GET_PLUGIN][ReturnData] Плагин найден: {name} [SUCCESS]")
        else:
            logger.warning(f"[PluginFactory][GET_PLUGIN][ConditionCheck] Плагин не найден: {name} [FAIL]")
        
        return plugin
    # END_METHOD_GET_PLUGIN
    
    # START_METHOD_GET_ALL_PLUGINS
    # START_CONTRACT:
    # PURPOSE: Получение всех зарегистрированных плагинов
    # OUTPUTS:
    # - Dict[str, Any] — словарь всех плагинов
    # KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): PluginQuery]
    # END_CONTRACT
    
    def get_all_plugins(self) -> Dict[str, Any]:
        """
        Получение всех зарегистрированных плагинов.
        
        Returns:
            Словарь плагинов {name: plugin}
        """
        count = len(self._plugins)
        logger.debug(f"[PluginFactory][GET_ALL_PLUGINS][ReturnData] Всего плагинов: {count} [VALUE]")
        return self._plugins.copy()
    # END_METHOD_GET_ALL_PLUGINS
    
    # START_METHOD_GET_PLUGINS_BY_TYPE
    # START_CONTRACT:
    # PURPOSE: Получение плагинов по типу
    # INPUTS:
    # - plugin_type: PluginType — тип плагина
    # OUTPUTS:
    # - List[Any] — список плагинов указанного типа
    # KEYWORDS: [CONCEPT(5): Filter; DOMAIN(8): PluginQuery]
    # END_CONTRACT
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[Any]:
        """
        Получение плагинов по типу.
        
        Args:
            plugin_type: Тип плагина для фильтрации
            
        Returns:
            Список плагинов указанного типа
        """
        logger.debug(f"[PluginFactory][GET_PLUGINS_BY_TYPE][Params] type={plugin_type.value} [ATTEMPT]")
        
        # Это упрощённая реализация - в реальности нужно хранить тип плагина
        # Пока возвращаем пустой список для неизвестных типов
        result = []
        
        logger.debug(f"[PluginFactory][GET_PLUGINS_BY_TYPE][ReturnData] Найдено плагинов: {len(result)} [VALUE]")
        return result
    # END_METHOD_GET_PLUGINS_BY_TYPE
    
    # START_METHOD_CLEAR_ALL
    # START_CONTRACT:
    # PURPOSE: Очистка всех зарегистрированных плагинов
    # KEYWORDS: [CONCEPT(6): Cleanup; DOMAIN(8): PluginManagement]
    # END_CONTRACT
    
    def clear_all(self) -> None:
        """
        Очистка всех зарегистрированных плагинов.
        
        Example:
            >>> factory.clear_all()
        """
        count = len(self._plugins)
        logger.info(f"[PluginFactory][CLEAR_ALL][ConditionCheck] Очистка плагинов: {count} [ATTEMPT]")
        
        self._plugins.clear()
        self._plugin_priorities.clear()
        self._plugin_configs.clear()
        
        logger.info(f"[PluginFactory][CLEAR_ALL][StepComplete] Очищено плагинов: {count} [SUCCESS]")
    # END_METHOD_CLEAR_ALL
    
    # START_METHOD_HAS_PLUGIN
    # START_CONTRACT:
    # PURPOSE: Проверка существования плагина
    # INPUTS:
    # - name: str — имя плагина
    # OUTPUTS:
    # - bool — True если плагин существует
    # KEYWORDS: [CONCEPT(5): ExistenceCheck; DOMAIN(8): PluginQuery]
    # END_CONTRACT
    
    def has_plugin(self, name: str) -> bool:
        """
        Проверка существования плагина по имени.
        
        Args:
            name: Имя плагина
            
        Returns:
            True если плагин зарегистрирован
        """
        exists = name in self._plugins
        logger.debug(f"[PluginFactory][HAS_PLUGIN][ConditionCheck] name={name}, exists={exists} [VALUE]")
        return exists
    # END_METHOD_HAS_PLUGIN
    
    # ============================================================================
    # МЕТОДЫ КОНФИГУРАЦИИ
    # ============================================================================
    
    # START_METHOD_SET_DEFAULT_USE_CPP
    # START_CONTRACT:
    # PURPOSE: Установка значения по умолчанию для использования C++
    # INPUTS:
    # - use_cpp: bool — использовать C++ по умолчанию
    # KEYWORDS: [TECH(5): Configuration; CONCEPT(5): Setter]
    # END_CONTRACT
    
    def set_default_use_cpp(self, use_cpp: bool) -> None:
        """
        Установка значения по умолчанию для использования C++ реализации.
        
        Args:
            use_cpp: True для использования C++, False для Python
        """
        logger.info(f"[PluginFactory][SET_DEFAULT_USE_CPP][Params] use_cpp={use_cpp} [ATTEMPT]")
        self._default_use_cpp = use_cpp
        logger.info(f"[PluginFactory][SET_DEFAULT_USE_CPP][StepComplete] Значение установлено: {use_cpp} [SUCCESS]")
    # END_METHOD_SET_DEFAULT_USE_CPP
    
    # START_METHOD_GET_DEFAULT_USE_CPP
    # START_CONTRACT:
    # PURPOSE: Получение значения по умолчанию для использования C++
    # OUTPUTS:
    # - bool — использовать C++ по умолчанию
    # KEYWORDS: [CONCEPT(5): Getter]
    # END_CONTRACT
    
    def get_default_use_cpp(self) -> bool:
        """
        Получение значения по умолчанию для использования C++.
        
        Returns:
            True если используется C++, False для Python
        """
        value = self._default_use_cpp
        logger.debug(f"[PluginFactory][GET_DEFAULT_USE_CPP][ReturnData] value={value} [VALUE]")
        return value
    # END_METHOD_GET_DEFAULT_USE_CPP
    
    # START_METHOD_SET_PLUGIN_PRIORITY
    # START_CONTRACT:
    # PURPOSE: Установка приоритета плагина
    # INPUTS:
    # - name: str — имя плагина
    # - priority: int — приоритет
    # KEYWORDS: [CONCEPT(5): Priority; DOMAIN(7): Scheduling]
    # END_CONTRACT
    
    def set_plugin_priority(self, name: str, priority: int) -> bool:
        """
        Установка приоритета плагина.
        
        Args:
            name: Имя плагина
            priority: Значение приоритета
            
        Returns:
            True если приоритет установлен, False если плагин не найден
        """
        logger.info(f"[PluginFactory][SET_PLUGIN_PRIORITY][Params] name={name}, priority={priority} [ATTEMPT]")
        
        if name not in self._plugins:
            logger.warning(f"[PluginFactory][SET_PLUGIN_PRIORITY][ConditionCheck] Плагин не найден: {name} [FAIL]")
            return False
        
        self._plugin_priorities[name] = priority
        logger.info(f"[PluginFactory][SET_PLUGIN_PRIORITY][StepComplete] Приоритет установлен: {name}={priority} [SUCCESS]")
        return True
    # END_METHOD_SET_PLUGIN_PRIORITY
    
    # START_METHOD_GET_PLUGIN_PRIORITY
    # START_CONTRACT:
    # PURPOSE: Получение приоритета плагина
    # INPUTS:
    # - name: str — имя плагина
    # OUTPUTS:
    # - Optional[int] — приоритет плагина или None
    # KEYWORDS: [CONCEPT(5): Getter]
    # END_CONTRACT
    
    def get_plugin_priority(self, name: str) -> Optional[int]:
        """
        Получение приоритета плагина.
        
        Args:
            name: Имя плагина
            
        Returns:
            Значение приоритета или None если плагин не найден
        """
        priority = self._plugin_priorities.get(name)
        
        if priority is not None:
            logger.debug(f"[PluginFactory][GET_PLUGIN_PRIORITY][ReturnData] name={name}, priority={priority} [VALUE]")
        else:
            logger.warning(f"[PluginFactory][GET_PLUGIN_PRIORITY][ConditionCheck] Приоритет не найден: {name} [FAIL]")
        
        return priority
    # END_METHOD_GET_PLUGIN_PRIORITY

# END_CLASS_PLUGINFACTORY

# ============================================================================
# ЭКСПОРТ
# ============================================================================

# START_EXPORTS
__all__ = [
    "PluginFactory",
]
# END_EXPORTS

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ ПРИ ИМПОРТЕ
# ============================================================================

logger.info(f"[INIT] Модуль plugin_factory загружен [INFO]")
