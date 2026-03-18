# FILE: src/monitor/_cpp/live_stats_wrapper.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Python-обёртка для C++ плагина live_stats_plugin_cpp с адаптацией live-статистики к UI интерфейсу. Обеспечивает реальновременное обновление метрик, интеграцию с Gradio UI и fallback на Python реализацию.
# SCOPE: Real-time мониторинг метрик, обновление статистики, адаптация данных для UI, система подписки на обновления
# INPUT: События метрик от генератора, команды управления мониторингом
# OUTPUT: UI компоненты для отображения live-метрик, методы получения статистики, система подписки
# KEYWORDS: [DOMAIN(9): LiveMonitoring; DOMAIN(8): RealTime; TECH(8): CppBinding; CONCEPT(7): Fallback; TECH(7): Gradio]
# LINKS: [USES_API(8): src.monitor._cpp.plugin_base_wrapper; USES_API(7): src.monitor.plugins.live_stats; USES_API(6): gradio]
# LINKS_TO_SPECIFICATION: [create_live_stats_wrapper_plan.md]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 10 [Обёртка для C++ LiveStatsPlugin с Python-friendly интерфейсом] => LiveStatsPlugin
# CLASS 8 [Данные live-статистики для UI] => LiveStatsData
# CLASS 7 [Конфигурация плагина live-статистики] => LiveStatsConfig
# FUNC 6 [Фабрика плагина live-статистики] => create_live_stats_plugin
# FUNC 5 [Получение конфигурации по умолчанию] => get_default_config
# END_MODULE_MAP
# START_USE_CASES:
# - [LiveStatsPlugin]: System (Monitoring) -> ProvideLiveStats -> RealTimeMetricsAvailable
# - [update_metric]: Generator (Update) -> ProcessMetric -> UIUpdated
# - [get_current_metrics]: UI (Query) -> ReturnMetrics -> DataProvided
# - [start_monitoring]: User (Control) -> StartMonitoring -> MonitoringActive
# - [stop_monitoring]: User (Control) -> StopMonitoring -> MonitoringStopped
# - [subscribe]: UI (Subscription) -> RegisterCallback -> UpdatesReady
# END_USE_CASES
"""
Модуль live_stats_wrapper.py — Python-обёртка для C++ плагина live-статистики.

Обеспечивает:
- Реальновременное обновление статистики
- Интеграцию с Gradio UI
- Адаптацию данных для отображения
- Fallback на Python реализацию при отсутствии C++ модуля
- Систему подписки на обновления

Пример использования:
    from src.monitor._cpp.live_stats_wrapper import LiveStatsPlugin
    
    # Создание плагина
    plugin = LiveStatsPlugin(config={"priority": 20})
    
    # Инициализация
    plugin.initialize({"app": app})
    
    # Обновление метрик
    plugin.update_metric("iteration_count", 1000)
    plugin.update_metric("wallet_count", 500)
    
    # Получение метрик
    metrics = plugin.get_current_metrics()
    
    # Управление мониторингом
    plugin.start_monitoring()
    plugin.stop_monitoring()
"""

import logging
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

# Импорт базового класса
from src.monitor._cpp.plugin_base_wrapper import (
    BaseMonitorPlugin,
    EVENT_TYPE_METRIC,
    EVENT_TYPE_START,
    EVENT_TYPE_STOP,
    EVENT_TYPE_STATUS,
    _get_cpp_available,
    _get_cpp_module,
)

# ============================================================================
# КОНФИГУРАЦИЯ ЛОГИРОВАНИЯ
# ============================================================================

def _setup_file_logging() -> logging.FileHandler:
    """Настройка логирования в файл app.log."""
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
_logger = logging.getLogger("src.monitor._cpp.live_stats_wrapper")
if not _logger.handlers:
    _file_handler = _setup_file_logging()
    _logger.addHandler(_file_handler)
    _logger.setLevel(logging.DEBUG)

logger = _logger

# ============================================================================
# КОНСТАНТЫ
# ============================================================================

# START_CONSTANTS_LIVE_STATS_WRAPPER
MAX_HISTORY_POINTS = 100
DEFAULT_REFRESH_INTERVAL = 1.0  # секунды
THEME_COLORS = {
    "primary": "#2196F3",
    "success": "#4CAF50",
    "warning": "#FF9800",
    "danger": "#F44336",
    "info": "#00BCD4",
}

# Имена поддерживаемых метрик
METRIC_ITERATION_COUNT = "iteration_count"
METRIC_WALLET_COUNT = "wallet_count"
METRIC_MATCH_COUNT = "match_count"
METRIC_ENTROPY_BITS = "entropy_bits"
METRIC_ENTROPY_QUALITY = "entropy_quality"
METRIC_PROGRESS_PERCENT = "progress_percent"
METRIC_ACTIVE_STAGE = "active_stage"

# Все поддерживаемые метрики
ALL_METRICS: Set[str] = {
    METRIC_ITERATION_COUNT,
    METRIC_WALLET_COUNT,
    METRIC_MATCH_COUNT,
    METRIC_ENTROPY_BITS,
    METRIC_ENTROPY_QUALITY,
    METRIC_PROGRESS_PERCENT,
    METRIC_ACTIVE_STAGE,
}

# END_CONSTANTS_LIVE_STATS_WRAPPER

# ============================================================================
# ЗАГРУЗКА C++ МОДУЛЯ С FALLBACK
# ============================================================================

# START_FUNCTION_IMPORT_CPP_MODULE
# START_CONTRACT:
# PURPOSE: Импорт C++ модуля live_stats_plugin_cpp с fallback на Python
# OUTPUTS:
# - Dict с ключами 'available', 'LiveStatsPlugin', 'LiveStatsData', 'error'
# KEYWORDS: [PATTERN(7): ModuleCheck; DOMAIN(8): ModuleLoading; TECH(6): Import]
# END_CONTRACT

def _import_cpp_module() -> Dict[str, Any]:
    """
    Импорт C++ модуля live_stats_plugin_cpp с fallback на Python.
    
    Returns:
        Словарь с информацией о доступности модуля и классами
    """
    try:
        from live_stats_plugin_cpp import (
            LiveStatsPlugin as _LiveStatsPlugin,
            LiveStatsData as _LiveStatsData,
        )
        
        logger.info(f"[_import_cpp_module][MODULE_CHECK] C++ модуль live_stats_plugin_cpp доступен [SUCCESS]")
        return {
            'available': True,
            'LiveStatsPlugin': _LiveStatsPlugin,
            'LiveStatsData': _LiveStatsData,
        }
    except ImportError as e:
        logger.info(f"[_import_cpp_module][MODULE_CHECK] C++ модуль live_stats_plugin_cpp недоступен: {e}, используем Python fallback [INFO]")
        return {'available': False, 'error': str(e)}
    except Exception as e:
        logger.warning(f"[_import_cpp_module][MODULE_CHECK] Ошибка при загрузке C++ модуля: {e} [FAIL]")
        return {'available': False, 'error': str(e)}

# Кэш загруженного модуля
_CPP_MODULE: Optional[Dict[str, Any]] = None

def _get_cpp_module_info() -> Dict[str, Any]:
    """Получение информации о C++ модуле с кэшированием."""
    global _CPP_MODULE
    if _CPP_MODULE is None:
        _CPP_MODULE = _import_cpp_module()
    return _CPP_MODULE

# END_FUNCTION_IMPORT_CPP_MODULE

# ============================================================================
# КЛАССЫ ДАННЫХ
# ============================================================================

# START_CLASS_LIVE_STATS_DATA
# START_CONTRACT:
# PURPOSE: Класс для хранения данных live-статистики для UI отображения
# ATTRIBUTES:
# - iteration: int — количество итераций
# - total_generated: int — количество сгенерированных кошельков
# - matches_found: int — количество найденных совпадений
# - addresses_checked: int — количество проверенных адресов
# - entropy_quality: float — качество энтропии
# - progress_percent: float — процент выполнения
# - eta_seconds: Optional[float] — ETA в секундах
# - time_elapsed: float — прошедшее время
# - current_batch: int — текущий батч
# - batches_total: int — всего батчей
# KEYWORDS: [PATTERN(7): DataClass; DOMAIN(8): LiveStats; CONCEPT(6): UI]
# END_CONTRACT

@dataclass
class LiveStatsData:
    """Данные live-статистики для UI отображения."""
    iteration: int = 0
    total_generated: int = 0
    matches_found: int = 0
    addresses_checked: int = 0
    entropy_quality: float = 0.0
    progress_percent: float = 0.0
    eta_seconds: Optional[float] = None
    time_elapsed: float = 0.0
    current_batch: int = 0
    batches_total: int = 0
    
    def to_display_dict(self) -> Dict[str, Any]:
        """
        Преобразование данных для отображения в UI.
        
        Returns:
            Словарь с отформатированными данными для UI
        """
        return {
            'iteration': self.iteration,
            'total_generated': f"{self.total_generated:,}",
            'matches': self.matches_found,
            'checked': f"{self.addresses_checked:,}",
            'entropy': f"{self.entropy_quality:.2%}",
            'progress': f"{self.progress_percent:.1f}%",
            'eta': self._format_eta(self.eta_seconds),
            'elapsed': self._format_time(self.time_elapsed),
        }
    
    @staticmethod
    def _format_eta(seconds: Optional[float]) -> str:
        """Форматирование ETA."""
        if seconds is None:
            return "Calculating..."
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """Форматирование времени."""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

# END_CLASS_LIVE_STATS_DATA

# START_CLASS_LIVE_STATS_CONFIG
# START_CONTRACT:
# PURPOSE: Класс для хранения конфигурации плагина live-статистики
# ATTRIBUTES:
# - max_history_points: int — максимум точек истории
# - refresh_interval: float — интервал обновления
# - enable_charts: bool — включить графики
# - chart_update_interval: int — интервал обновления графиков
# KEYWORDS: [PATTERN(7): DataClass; DOMAIN(8): Configuration; CONCEPT(6): Settings]
# END_CONTRACT

@dataclass
class LiveStatsConfig:
    """Конфигурация плагина live-статистики."""
    max_history_points: int = MAX_HISTORY_POINTS
    refresh_interval: float = DEFAULT_REFRESH_INTERVAL
    enable_charts: bool = True
    chart_update_interval: int = 10
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование конфигурации в словарь."""
        return {
            "max_history_points": self.max_history_points,
            "refresh_interval": self.refresh_interval,
            "enable_charts": self.enable_charts,
            "chart_update_interval": self.chart_update_interval,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LiveStatsConfig":
        """Создание конфигурации из словаря."""
        return cls(
            max_history_points=data.get("max_history_points", MAX_HISTORY_POINTS),
            refresh_interval=data.get("refresh_interval", DEFAULT_REFRESH_INTERVAL),
            enable_charts=data.get("enable_charts", True),
            chart_update_interval=data.get("chart_update_interval", 10),
        )

# END_CLASS_LIVE_STATS_CONFIG

# ============================================================================
# ОСНОВНОЙ КЛАСС LIVE STATS PLUGIN WRAPPER
# ============================================================================

# START_CLASS_LIVE_STATS_PLUGIN
# START_CONTRACT:
# PURPOSE: Обёртка для C++ LiveStatsPlugin с Python-friendly интерфейсом. Обеспечивает реальновременное обновление статистики, интеграцию с Gradio UI и fallback на Python реализацию.
# ATTRIBUTES:
# - C++ плагин => _cpp_plugin: Optional[Any]
# - Python плагин => _py_plugin: Optional[Any]
# - Флаг использования C++ => _use_cpp: bool
# - Подписки на обновления => _subscribers: List[Callable]
# - История метрик => _metrics_history: Dict[str, Deque[float]]
# - Текущие метрики => _current_metrics: Dict[str, Any]
# - Флаг мониторинга => _is_monitoring: bool
# - Время начала мониторинга => _start_timestamp: Optional[float]
# - Количество обновлений => _update_count: int
# METHODS:
# - Инициализация плагина => initialize(config)
# - Обработка события => process_event(event)
# - Получение статуса => get_status()
# - Завершение работы => shutdown()
# - Обновление метрики => update_metric(name, value)
# - Получение метрик => get_current_metrics()
# - Получение скорости метрики => get_metric_rate(metric_name, window_seconds)
# - Получение скорости итераций => get_iteration_rate()
# - Получение скорости кошельков => get_wallet_rate()
# - Получение скорости энтропии => get_entropy_rate()
# - Получение активной стадии => get_active_stage()
# - Получение процента выполнения => get_progress_percentage()
# - Запуск мониторинга => start_monitoring()
# - Остановка мониторинга => stop_monitoring()
# - Проверка мониторинга => is_monitoring()
# - Сброс статистики => reset()
# - Получение сводки => get_summary()
# KEYWORDS: [PATTERN(8): Wrapper; DOMAIN(9): LiveMonitoring; TECH(8): CppBinding; CONCEPT(7): Fallback]
# LINKS: [EXTENDS(8): BaseMonitorPlugin; USES_API(7): live_stats.py]
# END_CONTRACT

class LiveStatsPlugin(BaseMonitorPlugin):
    """
    Обёртка для C++ LiveStatsPlugin с Python-friendly интерфейсом.
    
    Обеспечивает:
    - Реальновременное обновление статистики
    - Интеграцию с Gradio UI
    - Адаптацию данных для отображения
    - Fallback на Python реализацию при отсутствии C++ модуля
    - Систему подписки на обновления
    
    Наследует абстрактные методы от BaseMonitorPlugin:
        - initialize(config): Инициализация плагина
        - process_event(event): Обработка события
        - get_status(): Получение статуса плагина
        - shutdown(): Корректное завершение работы
    """
    
    VERSION: str = "1.0.0"
    """Версия плагина"""
    
    AUTHOR: str = "Wallet Generator Team"
    """Автор плагина"""
    
    DESCRIPTION: str = "Обёртка для C++ плагина live-статистики"
    """Описание плагина"""
    
    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация обёртки LiveStatsPlugin с загрузкой C++ или Python модуля
    # INPUTS:
    # - config: Optional[Dict[str, Any]] — словарь конфигурации плагина
    # OUTPUTS: Инициализированный объект LiveStatsPlugin
    # SIDE_EFFECTS: Загружает C++ модуль или Python fallback; инициализирует хранилище метрик
    # KEYWORDS: [CONCEPT(5): Initialization; DOMAIN(7): PluginSetup]
    # TEST_CONDITIONS_SUCCESS_CRITERIA: Плагин должен корректно определить доступность C++ модуля
    # END_CONTRACT
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Инициализация обёртки LiveStatsPlugin.
        
        Args:
            config: Словарь конфигурации плагина (опционально)
        """
        # Инициализация базового класса
        super().__init__(name="live_stats", config=config)
        
        # Получение информации о C++ модуле
        self._cpp_module_info = _get_cpp_module_info()
        self._use_cpp = self._cpp_module_info.get('available', False)
        
        # Инициализация C++ или Python плагина
        self._cpp_plugin = None
        self._py_plugin = None
        
        if self._use_cpp:
            try:
                self._cpp_plugin = self._cpp_module_info['LiveStatsPlugin']()
                logger.info(f"[LiveStatsPlugin][INIT][ConditionCheck] Используется C++ плагин [SUCCESS]")
            except Exception as e:
                logger.warning(f"[LiveStatsPlugin][INIT][ExceptionCaught] Ошибка при создании C++ плагина: {e}, используем Python fallback")
                self._use_cpp = False
        
        if not self._use_cpp:
            # Python реализация не используется - используем встроенную реализацию
            logger.info(f"[LiveStatsPlugin][INIT][ConditionCheck] Используется встроенная Python реализация [SUCCESS]")
        
        # Инициализация хранилища метрик
        self._subscribers: List[Callable] = []
        self._metrics_history: Dict[str, Deque[float]] = {
            metric: deque(maxlen=MAX_HISTORY_POINTS) for metric in ALL_METRICS
        }
        self._current_metrics: Dict[str, Any] = {
            metric: 0 for metric in ALL_METRICS
        }
        self._metrics_timestamps: Deque[float] = deque(maxlen=MAX_HISTORY_POINTS)
        
        # Состояние мониторинга
        self._is_monitoring: bool = False
        self._start_timestamp: Optional[float] = None
        self._update_count: int = 0
        self._last_update_time: float = 0
        
        # История для расчёта скоростей
        self._history_iterations: Deque[float] = deque(maxlen=MAX_HISTORY_POINTS)
        self._history_wallets: Deque[float] = deque(maxlen=MAX_HISTORY_POINTS)
        self._history_timestamps: Deque[float] = deque(maxlen=MAX_HISTORY_POINTS)
        
        # Конфигурация
        self._plugin_config = LiveStatsConfig.from_dict(config or {})
        
        # Логирование
        self._logger.info(f"[LiveStatsPlugin][INIT][VarCheck] Плагин инициализирован, C++: {self._use_cpp} [VALUE]")
    
    # END_METHOD___init__
    
    # ============================================================================
    # СВОЙСТВА (PROPERTIES)
    # ============================================================================
    
    # START_PROPERTY_METRICS
    @property
    def metrics(self) -> Dict[str, Any]:
        """
        Получение текущих метрик.
        
        Returns:
            Словарь текущих метрик
        """
        return self._current_metrics.copy()
    # END_PROPERTY_METRICS
    
    # START_PROPERTY_MONITORING_DURATION
    @property
    def monitoring_duration(self) -> float:
        """
        Получение длительности мониторинга в секундах.
        
        Returns:
            Длительность мониторинга в секундах
        """
        if self._start_timestamp is None:
            return 0.0
        return time.time() - self._start_timestamp
    # END_PROPERTY_MONITORING_DURATION
    
    # START_PROPERTY_UPDATE_COUNT
    @property
    def update_count(self) -> int:
        """
        Получение количества обновлений.
        
        Returns:
            Количество обновлений метрик
        """
        return self._update_count
    # END_PROPERTY_UPDATE_COUNT
    
    # ============================================================================
    # АБСТРАКТНЫЕ МЕТОДЫ (РЕАЛИЗАЦИЯ)
    # ============================================================================
    
    # START_METHOD_INITIALIZE
    # START_CONTRACT:
    # PURPOSE: Инициализация плагина с переданной конфигурацией
    # INPUTS:
    # - config: Dict[str, Any] — словарь конфигурации плагина
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Инициализирует внутреннее состояние; может зарегистрировать компоненты
    # KEYWORDS: [DOMAIN(8): PluginSetup; CONCEPT(6): Initialization]
    # TEST_CONDITIONS_SUCCESS_CRITERIA: Метод должен корректно обработать любую конфигурацию
    # END_CONTRACT
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Инициализация плагина.
        
        Args:
            config: Словарь конфигурации плагина
        """
        self._logger.info(f"[LiveStatsPlugin][INITIALIZE][StepComplete] Начало инициализации плагина")
        
        # Обработка случая когда config равен None
        if config is None:
            config = {}
        
        # Обновление конфигурации
        if config and 'config' in config:
            self._plugin_config = LiveStatsConfig.from_dict(config['config'])
        
        # Сохранение ссылки на приложение
        self._app = config.get('app')
        
        # Обновление статуса
        self._status["state"] = "initialized"
        self._status["message"] = "Plugin initialized"
        
        self._logger.info(f"[LiveStatsPlugin][INITIALIZE][StepComplete] Инициализация плагина завершена [SUCCESS]")
    
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
    def process_event(self, event: Dict[str, Any]) -> None:
        """
        Обработка события.
        
        Args:
            event: Словарь с данными события (обязательно должен содержать ключ 'type')
        """
        event_type = event.get('type', 'unknown')
        
        self._logger.debug(f"[LiveStatsPlugin][PROCESS_EVENT][ConditionCheck] Получено событие типа: {event_type} [VALUE]")
        
        if event_type == EVENT_TYPE_METRIC:
            # Обработка события метрики
            metrics = event.get('data', {})
            if isinstance(metrics, dict):
                for name, value in metrics.items():
                    if name in ALL_METRICS:
                        self.update_metric(name, value)
            
            self._logger.debug(f"[LiveStatsPlugin][PROCESS_EVENT][StepComplete] Обработано событие метрики [SUCCESS]")
        
        elif event_type == EVENT_TYPE_START:
            # Запуск мониторинга
            self.start_monitoring()
            self._logger.info(f"[LiveStatsPlugin][PROCESS_EVENT][StepComplete] Получено событие START [SUCCESS]")
        
        elif event_type == EVENT_TYPE_STOP:
            # Остановка мониторинга
            self.stop_monitoring()
            self._logger.info(f"[LiveStatsPlugin][PROCESS_EVENT][StepComplete] Получено событие STOP [SUCCESS]")
        
        elif event_type == EVENT_TYPE_STATUS:
            # Обработка события статуса
            status_data = event.get('data', {})
            self._logger.debug(f"[LiveStatsPlugin][PROCESS_EVENT][Info] Событие статуса: {status_data}")
        
        else:
            self._logger.warning(f"[LiveStatsPlugin][PROCESS_EVENT][ConditionCheck] Неизвестный тип события: {event_type} [FAIL]")
    
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
    def get_status(self) -> Dict[str, Any]:
        """
        Получение статуса плагина.
        
        Returns:
            Словарь со статусом плагина
        """
        status = {
            "state": self._status.get("state", "unknown"),
            "message": self._status.get("message", ""),
            "using_cpp": self._use_cpp,
            "is_monitoring": self._is_monitoring,
            "update_count": self._update_count,
            "monitoring_duration": self.monitoring_duration,
            "current_metrics": self._current_metrics.copy(),
        }
        
        self._logger.debug(f"[LiveStatsPlugin][GET_STATUS][ReturnData] Статус: {status} [VALUE]")
        return status
    
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
    def shutdown(self) -> None:
        """
        Корректное завершение работы плагина.
        
        Должен освободить все занятые ресурсы и сохранить состояние.
        """
        self._logger.info(f"[LiveStatsPlugin][SHUTDOWN][StepComplete] Начало завершения работы плагина")
        
        # Остановка мониторинга
        if self._is_monitoring:
            self.stop_monitoring()
        
        # Очистка подписчиков
        self._subscribers.clear()
        
        # Очистка истории метрик
        self._metrics_history.clear()
        self._history_iterations.clear()
        self._history_wallets.clear()
        self._history_timestamps.clear()
        
        # Обновление статуса
        self._status["state"] = "shutdown"
        self._status["message"] = "Plugin shutdown complete"
        
        self._logger.info(f"[LiveStatsPlugin][SHUTDOWN][StepComplete] Завершение работы плагина завершено [SUCCESS]")
    
    # END_METHOD_SHUTDOWN
    
    # ============================================================================
    # СПЕЦИФИЧЕСКИЕ МЕТОДЫ LIVE-СТАТИСТИКИ
    # ============================================================================
    
    # START_METHOD_UPDATE_METRIC
    # START_CONTRACT:
    # PURPOSE: Обновление метрики в реальном времени
    # INPUTS:
    # - name: str — имя метрики
    # - value: Any — значение метрики
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Обновляет текущую метрику; добавляет в историю; уведомляет подписчиков
    # KEYWORDS: [DOMAIN(9): RealTime; CONCEPT(7): MetricUpdate]
    # END_CONTRACT
    def update_metric(self, name: str, value: Any) -> None:
        """
        Обновление метрики в реальном времени.
        
        Args:
            name: Имя метрики
            value: Значение метрики
        """
        if name not in ALL_METRICS:
            self._logger.warning(f"[LiveStatsPlugin][UPDATE_METRIC][ConditionCheck] Неизвестная метрика: {name} [FAIL]")
            return
        
        # Преобразование значения в float
        try:
            float_value = float(value)
        except (ValueError, TypeError) as e:
            self._logger.warning(f"[LiveStatsPlugin][UPDATE_METRIC][ExceptionCaught] Ошибка преобразования значения: {e} [FAIL]")
            return
        
        # Обновление текущего значения
        old_value = self._current_metrics.get(name, 0)
        self._current_metrics[name] = float_value
        
        # Добавление в историю
        current_time = time.time()
        self._metrics_history[name].append(float_value)
        self._metrics_timestamps.append(current_time)
        
        # Обновление истории для расчёта скоростей
        if name == METRIC_ITERATION_COUNT:
            delta = float_value - old_value
            self._history_iterations.append(delta)
            self._history_timestamps.append(current_time)
        elif name == METRIC_WALLET_COUNT:
            delta = float_value - old_value
            self._history_wallets.append(delta)
        
        # Увеличение счётчика обновлений
        self._update_count += 1
        self._last_update_time = current_time
        
        # Запуск мониторинга при первом обновлении
        if not self._is_monitoring and float_value > 0:
            self.start_monitoring()
        
        # Уведомление подписчиков
        self._notify_subscribers()
        
        self._logger.debug(f"[LiveStatsPlugin][UPDATE_METRIC][VarCheck] Метрика {name}: {float_value} [VALUE]")
    
    # END_METHOD_UPDATE_METRIC
    
    # START_METHOD_GET_CURRENT_METRICS
    # START_CONTRACT:
    # PURPOSE: Получение текущих метрик
    # OUTPUTS:
    # - Dict[str, Any] — словарь текущих метрик
    # KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): Metrics]
    # END_CONTRACT
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Получение текущих метрик.
        
        Returns:
            Словарь текущих метрик
        """
        return self._current_metrics.copy()
    
    # END_METHOD_GET_CURRENT_METRICS
    
    # START_METHOD_GET_METRIC_RATE
    # START_CONTRACT:
    # PURPOSE: Получение скорости изменения метрики
    # INPUTS:
    # - metric_name: str — имя метрики
    # - window_seconds: int — окно в секундах для расчёта скорости
    # OUTPUTS:
    # - float — скорость изменения метрики (в единицах в секунду)
    # KEYWORDS: [DOMAIN(8): RateCalculation; CONCEPT(7): TimeWindow]
    # END_CONTRACT
    def get_metric_rate(self, metric_name: str, window_seconds: int = 60) -> float:
        """
        Получение скорости изменения метрики.
        
        Args:
            metric_name: Имя метрики
            window_seconds: Окно в секундах для расчёта скорости
            
        Returns:
            Скорость изменения метрики (в единицах в секунду)
        """
        if metric_name not in self._metrics_history:
            return 0.0
        
        history = self._metrics_history[metric_name]
        if not history:
            return 0.0
        
        current_time = time.time()
        
        # Фильтрация по окну
        relevant_values = []
        relevant_times = []
        
        for i, timestamp in enumerate(reversed(list(self._metrics_timestamps))):
            if current_time - timestamp <= window_seconds:
                if len(history) > i:
                    relevant_values.append(list(history)[-(i+1)])
                    relevant_times.append(timestamp)
        
        if len(relevant_values) < 2:
            return 0.0
        
        # Расчёт скорости
        value_delta = relevant_values[-1] - relevant_values[0]
        time_delta = relevant_times[-1] - relevant_times[0]
        
        if time_delta <= 0:
            return 0.0
        
        rate = value_delta / time_delta
        
        self._logger.debug(f"[LiveStatsPlugin][GET_METRIC_RATE][VarCheck] Скорость {metric_name}: {rate} [VALUE]")
        return rate
    
    # END_METHOD_GET_METRIC_RATE
    
    # START_METHOD_GET_ITERATION_RATE
    # START_CONTRACT:
    # PURPOSE: Получение скорости итераций
    # OUTPUTS:
    # - float — скорость итераций (итераций в секунду)
    # KEYWORDS: [DOMAIN(8): RateCalculation; CONCEPT(6): Iteration]
    # END_CONTRACT
    def get_iteration_rate(self) -> float:
        """
        Получение скорости итераций.
        
        Returns:
            Скорость итераций (итераций в секунду)
        """
        # Использование истории итераций
        if not self._history_iterations or not self._history_timestamps:
            return 0.0
        
        current_time = time.time()
        
        # Фильтрация по последним 60 секундам
        recent_deltas = []
        recent_times = []
        
        for i, timestamp in enumerate(reversed(list(self._history_timestamps))):
            if current_time - timestamp <= 60:
                if len(self._history_iterations) > i:
                    recent_deltas.append(list(self._history_iterations)[-(i+1)])
                    recent_times.append(timestamp)
        
        if not recent_deltas or len(recent_deltas) < 2:
            return 0.0
        
        total_delta = sum(recent_deltas)
        time_delta = recent_times[-1] - recent_times[0]
        
        if time_delta <= 0:
            return 0.0
        
        rate = total_delta / time_delta
        
        self._logger.debug(f"[LiveStatsPlugin][GET_ITERATION_RATE][VarCheck] Скорость итераций: {rate} [VALUE]")
        return rate
    
    # END_METHOD_GET_ITERATION_RATE
    
    # START_METHOD_GET_WALLET_RATE
    # START_CONTRACT:
    # PURPOSE: Получение скорости генерации кошельков
    # OUTPUTS:
    # - float — скорость кошельков (кошельков в секунду)
    # KEYWORDS: [DOMAIN(8): RateCalculation; CONCEPT(6): Wallet]
    # END_CONTRACT
    def get_wallet_rate(self) -> float:
        """
        Получение скорости генерации кошельков.
        
        Returns:
            Скорость кошельков (кошельков в секунду)
        """
        return self.get_metric_rate(METRIC_WALLET_COUNT, window_seconds=60)
    
    # END_METHOD_GET_WALLET_RATE
    
    # START_METHOD_GET_ENTROPY_RATE
    # START_CONTRACT:
    # PURPOSE: Получения скорости накопления энтропии
    # OUTPUTS:
    # - float — скорость энтропии (бит в секунду)
    # KEYWORDS: [DOMAIN(8): RateCalculation; CONCEPT(6): Entropy]
    # END_CONTRACT
    def get_entropy_rate(self) -> float:
        """
        Получение скорости накопления энтропии.
        
        Returns:
            Скорость энтропии (бит в секунду)
        """
        return self.get_metric_rate(METRIC_ENTROPY_BITS, window_seconds=60)
    
    # END_METHOD_GET_ENTROPY_RATE
    
    # START_METHOD_GET_ACTIVE_STAGE
    # START_CONTRACT:
    # PURPOSE: Получение текущей стадии генерации
    # OUTPUTS:
    # - str — название текущей стадии
    # KEYWORDS: [CONCEPT(5): Getter; DOMAIN(7): Stage]
    # END_CONTRACT
    def get_active_stage(self) -> str:
        """
        Получение текущей стадии генерации.
        
        Returns:
            Название текущей стадии
        """
        stage = self._current_metrics.get(METRIC_ACTIVE_STAGE, "idle")
        
        if isinstance(stage, (int, float)):
            # Преобразование числового кода стадии в строку
            stage_map = {
                0: "idle",
                1: "initialization",
                2: "entropy_collection",
                3: "key_generation",
                4: "wallet_generation",
                5: "matching",
                6: "completed",
            }
            stage = stage_map.get(int(stage), "unknown")
        
        return str(stage)
    
    # END_METHOD_GET_ACTIVE_STAGE
    
    # START_METHOD_GET_PROGRESS_PERCENTAGE
    # START_CONTRACT:
    # PURPOSE: Получение процента выполнения
    # OUTPUTS:
    # - float — процент выполнения (0-100)
    # KEYWORDS: [CONCEPT(5): Getter; DOMAIN(7): Progress]
    # END_CONTRACT
    def get_progress_percentage(self) -> float:
        """
        Получение процента выполнения.
        
        Returns:
            Процент выполнения (0-100)
        """
        progress = self._current_metrics.get(METRIC_PROGRESS_PERCENT, 0.0)
        
        try:
            return float(progress)
        except (ValueError, TypeError):
            return 0.0
    
    # END_METHOD_GET_PROGRESS_PERCENTAGE
    
    # START_METHOD_START_MONITORING
    # START_CONTRACT:
    # PURPOSE: Запуск мониторинга
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Устанавливает флаг мониторинга; записывает время начала
    # KEYWORDS: [CONCEPT(6): Control; DOMAIN(7): Monitoring]
    # END_CONTRACT
    def start_monitoring(self) -> None:
        """
        Запуск мониторинга.
        """
        if not self._is_monitoring:
            self._is_monitoring = True
            self._start_timestamp = time.time()
            self._status["state"] = "monitoring"
            self._status["message"] = "Monitoring active"
            
            self._logger.info(f"[LiveStatsPlugin][START_MONITORING][StepComplete] Мониторинг запущен [SUCCESS]")
        else:
            self._logger.debug(f"[LiveStatsPlugin][START_MONITORING][Info] Мониторинг уже запущен [INFO]")
    
    # END_METHOD_START_MONITORING
    
    # START_METHOD_STOP_MONITORING
    # START_CONTRACT:
    # PURPOSE: Остановка мониторинга
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Сбрасывает флаг мониторинга
    # KEYWORDS: [CONCEPT(6): Control; DOMAIN(7): Monitoring]
    # END_CONTRACT
    def stop_monitoring(self) -> None:
        """
        Остановка мониторинга.
        """
        if self._is_monitoring:
            self._is_monitoring = False
            self._status["state"] = "stopped"
            self._status["message"] = "Monitoring stopped"
            
            self._logger.info(f"[LiveStatsPlugin][STOP_MONITORING][StepComplete] Мониторинг остановлен [SUCCESS]")
        else:
            self._logger.debug(f"[LiveStatsPlugin][STOP_MONITORING][Info] Мониторинг уже остановлен [INFO]")
    
    # END_METHOD_STOP_MONITORING
    
    # START_METHOD_IS_MONITORING
    # START_CONTRACT:
    # PURPOSE: Проверка активности мониторинга
    # OUTPUTS:
    # - bool — True если мониторинг активен
    # KEYWORDS: [CONCEPT(5): Getter; DOMAIN(7): Monitoring]
    # END_CONTRACT
    def is_monitoring(self) -> bool:
        """
        Проверка активности мониторинга.
        
        Returns:
            True если мониторинг активен
        """
        return self._is_monitoring
    
    # END_METHOD_IS_MONITORING
    
    # START_METHOD_RESET
    # START_CONTRACT:
    # PURPOSE: Сброс статистики
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Очищает историю метрик; сбрасывает счётчики
    # KEYWORDS: [CONCEPT(7): Reset; DOMAIN(8): Statistics]
    # END_CONTRACT
    def reset(self) -> None:
        """
        Сброс статистики.
        """
        self._logger.info(f"[LiveStatsPlugin][RESET][StepComplete] Начало сброса статистики")
        
        # Очистка текущих метрик
        self._current_metrics = {metric: 0 for metric in ALL_METRICS}
        
        # Очистка истории
        for metric in ALL_METRICS:
            self._metrics_history[metric].clear()
        
        self._history_iterations.clear()
        self._history_wallets.clear()
        self._history_timestamps.clear()
        self._metrics_timestamps.clear()
        
        # Сброс состояния мониторинга
        self._is_monitoring = False
        self._start_timestamp = None
        self._update_count = 0
        self._last_update_time = 0
        
        # Обновление статуса
        self._status["state"] = "reset"
        self._status["message"] = "Statistics reset"
        
        self._logger.info(f"[LiveStatsPlugin][RESET][StepComplete] Статистика сброшена [SUCCESS]")
    
    # END_METHOD_RESET
    
    # START_METHOD_GET_SUMMARY
    # START_CONTRACT:
    # PURPOSE: Получение сводки текущей статистики
    # OUTPUTS:
    # - Dict[str, Any] — словарь со сводкой статистики
    # KEYWORDS: [CONCEPT(6): Summary; DOMAIN(8): Statistics]
    # END_CONTRACT
    def get_summary(self) -> Dict[str, Any]:
        """
        Получение сводки текущей статистики.
        
        Returns:
            Словарь со сводкой статистики
        """
        summary = {
            "is_monitoring": self._is_monitoring,
            "monitoring_duration": self.monitoring_duration,
            "update_count": self._update_count,
            "iteration_rate": self.get_iteration_rate(),
            "wallet_rate": self.get_wallet_rate(),
            "entropy_rate": self.get_entropy_rate(),
            "active_stage": self.get_active_stage(),
            "progress_percent": self.get_progress_percentage(),
            "metrics": self._current_metrics.copy(),
        }
        
        self._logger.debug(f"[LiveStatsPlugin][GET_SUMMARY][ReturnData] Сводка: {summary} [VALUE]")
        return summary
    
    # END_METHOD_GET_SUMMARY
    
    # ============================================================================
    # СИСТЕМА ПОДПИСКИ
    # ============================================================================
    
    # START_METHOD_SUBSCRIBE
    # START_CONTRACT:
    # PURPOSE: Подписка на обновления метрик
    # INPUTS:
    # - callback: Callable — функция-обработчик обновлений
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Добавляет callback в список подписчиков
    # KEYWORDS: [DOMAIN(8): Subscription; CONCEPT(7): Callback]
    # END_CONTRACT
    def subscribe(self, callback: Callable) -> None:
        """
        Подписка на обновления метрик.
        
        Args:
            callback: Функция-обработчик обновлений
        """
        if callback not in self._subscribers:
            self._subscribers.append(callback)
            self._logger.info(f"[LiveStatsPlugin][SUBSCRIBE][StepComplete] Подписка добавлена [SUCCESS]")
    
    # END_METHOD_SUBSCRIBE
    
    # START_METHOD_UNSUBSCRIBE
    # START_CONTRACT:
    # PURPOSE: Отписка от обновлений метрик
    # INPUTS:
    # - callback: Callable — функция-обработчик для удаления
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Удаляет callback из списка подписчиков
    # KEYWORDS: [DOMAIN(8): Subscription; CONCEPT(7): Callback]
    # END_CONTRACT
    def unsubscribe(self, callback: Callable) -> None:
        """
        Отписка от обновлений метрик.
        
        Args:
            callback: Функция-обработчик для удаления
        """
        if callback in self._subscribers:
            self._subscribers.remove(callback)
            self._logger.info(f"[LiveStatsPlugin][UNSUBSCRIBE][StepComplete] Подписка удалена [SUCCESS]")
    
    # END_METHOD_UNSUBSCRIBE
    
    # START_METHOD_NOTIFY_SUBSCRIBERS
    # START_CONTRACT:
    # PURPOSE: Уведомление всех подписчиков об обновлении метрик
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Вызывает все зарегистрированные callback
    # KEYWORDS: [DOMAIN(9): Broadcasting; CONCEPT(7): Notification]
    # END_CONTRACT
    def _notify_subscribers(self) -> None:
        """Уведомление всех подписчиков об обновлении метрик."""
        if not self._subscribers:
            return
        
        for callback in self._subscribers:
            try:
                callback(self._current_metrics.copy())
            except Exception as e:
                self._logger.error(f"[LiveStatsPlugin][NOTIFY_SUBSCRIBERS][ExceptionCaught] Ошибка при уведомлении подписчика: {e} [FAIL]")
    
    # END_METHOD_NOTIFY_SUBSCRIBERS
    
    # ============================================================================
    # UI КОМПОНЕНТЫ
    # ============================================================================
    
    # START_METHOD_GET_UI_COMPONENTS
    # START_CONTRACT:
    # PURPOSE: Получение UI компонентов для Gradio
    # OUTPUTS:
    # - Dict[str, Any] — словарь UI компонентов
    # KEYWORDS: [TECH(7): Gradio; DOMAIN(8): UIComponents]
    # END_CONTRACT
    def get_ui_components(self) -> Dict[str, Any]:
        """
        Получение UI компонентов для Gradio.
        
        Returns:
            Словарь UI компонентов
        """
        # Возвращаем базовые компоненты
        return {
            "metrics": self._current_metrics.copy(),
            "is_monitoring": self._is_monitoring,
            "monitoring_duration": self.monitoring_duration,
            "iteration_rate": self.get_iteration_rate(),
            "wallet_rate": self.get_wallet_rate(),
            "progress_percent": self.get_progress_percentage(),
        }
    
    # END_METHOD_GET_UI_COMPONENTS
    
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
        return f"LiveStatsPlugin(name={self._name}, using_cpp={self._use_cpp}, monitoring={self._is_monitoring})"
    
    # END_METHOD___repr__
    
    # START_METHOD___str__
    # START_CONTRACT:
    # PURPOSE: Читаемое строковое представление плагина
    # OUTPUTS: str — читаемое представление
    # KEYWORDS: [CONCEPT(5): StringRepr]
    # END_CONTRACT
    def __str__(self) -> str:
        """Читаемое строковое представление плагина."""
        return f"LiveStatsPlugin '{self._name}' (C++: {self._use_cpp}, мониторинг: {self._is_monitoring}, обновлений: {self._update_count})"
    
    # END_METHOD___str__


# END_CLASS_LIVE_STATS_PLUGIN

# ============================================================================
# ФАБРИКА ПЛАГИНА
# ============================================================================

# START_FUNCTION_CREATE_LIVE_STATS_PLUGIN
# START_CONTRACT:
# PURPOSE: Фабричная функция для создания плагина live-статистики
# INPUTS:
# - config: Optional[Dict[str, Any]] — конфигурация плагина
# OUTPUTS:
# - LiveStatsPlugin — созданный экземпляр плагина
# KEYWORDS: [PATTERN(7): Factory; DOMAIN(8): PluginCreation]
# END_CONTRACT

def create_live_stats_plugin(config: Optional[Dict[str, Any]] = None) -> LiveStatsPlugin:
    """
    Фабричная функция для создания плагина live-статистики.
    
    Args:
        config: Конфигурация плагина (опционально)
        
    Returns:
        Экземпляр LiveStatsPlugin
    """
    logger.info(f"[create_live_stats_plugin][ConditionCheck] Создание плагина live-статистики [ATTEMPT]")
    plugin = LiveStatsPlugin(config=config)
    logger.info(f"[create_live_stats_plugin][StepComplete] Плагин создан: {plugin} [SUCCESS]")
    return plugin

# END_FUNCTION_CREATE_LIVE_STATS_PLUGIN

# START_FUNCTION_GET_DEFAULT_CONFIG
# START_CONTRACT:
# PURPOSE: Получение конфигурации плагина по умолчанию
# OUTPUTS:
# - Dict[str, Any] — словарь конфигурации по умолчанию
# KEYWORDS: [CONCEPT(7): Defaults; DOMAIN(8): Configuration]
# END_CONTRACT

def get_default_config() -> Dict[str, Any]:
    """
    Получение конфигурации плагина по умолчанию.
    
    Returns:
        Словарь конфигурации по умолчанию
    """
    return {
        "name": "live_stats",
        "priority": 20,
        "enabled": True,
        "config": LiveStatsConfig().to_dict(),
    }

# END_FUNCTION_GET_DEFAULT_CONFIG

# ============================================================================
# ЭКСПОРТ
# ============================================================================

__all__ = [
    # Классы
    "LiveStatsPlugin",
    "LiveStatsData",
    "LiveStatsConfig",
    # Функции
    "create_live_stats_plugin",
    "get_default_config",
    # Константы метрик
    "METRIC_ITERATION_COUNT",
    "METRIC_WALLET_COUNT",
    "METRIC_MATCH_COUNT",
    "METRIC_ENTROPY_BITS",
    "METRIC_ENTROPY_QUALITY",
    "METRIC_PROGRESS_PERCENT",
    "METRIC_ACTIVE_STAGE",
    "ALL_METRICS",
]

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ ПРИ ИМПОРТЕ
# ============================================================================

logger.info(f"[INIT] Модуль live_stats_wrapper.py загружен, C++ модуль доступен: {_get_cpp_module_info().get('available', False)} [INFO]")
