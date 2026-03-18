# FILE: src/monitor/_cpp/final_stats_wrapper.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Python-обёртка для C++ плагина final_stats_plugin_cpp с адаптацией финальной статистики к UI интерфейсу. Обеспечивает сбор и отображение итоговой статистики после завершения генерации, генерацию отчётов и экспорт данных.
# SCOPE: Финальная статистика, генерация отчётов, экспорт данных, система сравнения с предыдущими запусками
# INPUT: Финальные метрики от генератора, события завершения работы
# OUTPUT: UI компоненты для отображения финальной статистики, методы экспорта, система сравнения
# KEYWORDS: [DOMAIN(9): FinalStats; DOMAIN(8): Statistics; TECH(8): CppBinding; CONCEPT(7): Fallback; TECH(7): Export]
# LINKS: [USES_API(8): src.monitor._cpp.plugin_base_wrapper; USES_API(7): src.monitor.plugins.final_stats; USES_API(6): gradio]
# LINKS_TO_SPECIFICATION: [create_final_stats_wrapper_plan.md]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 10 [Обёртка для C++ FinalStatsPlugin с Python-friendly интерфейсом] => FinalStatsPlugin
# CLASS 8 [Финальный отчёт статистики] => FinalStatsReport
# CLASS 7 [Конфигурация плагина финальной статистики] => FinalStatsConfig
# FUNC 6 [Фабрика плагина финальной статистики] => create_final_stats_plugin
# FUNC 5 [Получение конфигурации по умолчанию] => get_default_config
# END_MODULE_MAP
# START_USE_CASES:
# - [FinalStatsPlugin]: System (MonitoringComplete) -> ShowFinalSummary -> ResultsDisplayed
# - [collect_final_stats]: Generator (Complete) -> CaptureFinalMetrics -> StatsCalculated
# - [generate_report]: Admin (Report) -> GenerateReport -> ReportReady
# - [export_report]: Admin (Export) -> SaveToFile -> FileCreated
# - [compare_with_previous]: Admin (Analysis) -> CompareStats -> ComparisonReady
# END_USE_CASES
"""
Модуль final_stats_wrapper.py — Python-обёртка для C++ плагина финальной статистики.

Обеспечивает:
- Сбор и агрегацию финальной статистики
- Генерацию отчётов в различных форматах (JSON, HTML, TEXT)
- Экспорт данных в файлы
- Сравнение с предыдущими запусками
- Fallback на Python реализацию при отсутствии C++ модуля

Пример использования:
    from src.monitor._cpp.final_stats_wrapper import FinalStatsPlugin
    
    # Создание плагина
    plugin = FinalStatsPlugin(config={"priority": 30})
    
    # Инициализация
    plugin.initialize({"app": app})
    
    # Сбор финальной статистики
    plugin.collect_final_stats({
        "iteration_count": 1000000,
        "wallet_count": 500000,
        "match_count": 0,
        "runtime_seconds": 3600.0,
    })
    
    # Генерация отчёта
    report = plugin.generate_report(format='json')
    
    # Экспорт отчёта
    plugin.export_report("final_stats.json", format='json')
"""

import json
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
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
_logger = logging.getLogger("src.monitor._cpp.final_stats_wrapper")
if not _logger.handlers:
    _file_handler = _setup_file_logging()
    _logger.addHandler(_file_handler)
    _logger.setLevel(logging.DEBUG)

logger = _logger

# ============================================================================
# КОНСТАНТЫ
# ============================================================================

# START_CONSTANTS_FINAL_STATS_WRAPPER
MAX_HISTORY_SESSIONS = 100
DEFAULT_REPORT_FORMAT = "json"
SUPPORTED_FORMATS = {"json", "html", "text"}

# Секции статистики
STAT_SECTIONS = {
    "summary": "Сводка",
    "performance": "Производительность",
    "matches": "Совпадения",
    "entropy": "Энтропия",
    "stages": "Стадии",
}

# Ключи финальных метрик
METRIC_ITERATION_COUNT = "iteration_count"
METRIC_WALLET_COUNT = "wallet_count"
METRIC_MATCH_COUNT = "match_count"
METRIC_RUNTIME_SECONDS = "runtime_seconds"
METRIC_AVG_ITERATION_TIME_MS = "avg_iteration_time_ms"
METRIC_ITERATIONS_PER_SECOND = "iterations_per_second"
METRIC_WALLETS_PER_SECOND = "wallets_per_second"
METRIC_ENTROPY_STATS = "entropy_stats"
METRIC_STAGE_BREAKDOWN = "stage_breakdown"

# Все поддерживаемые метрики
ALL_FINAL_METRICS: Set[str] = {
    METRIC_ITERATION_COUNT,
    METRIC_WALLET_COUNT,
    METRIC_MATCH_COUNT,
    METRIC_RUNTIME_SECONDS,
    METRIC_AVG_ITERATION_TIME_MS,
    METRIC_ITERATIONS_PER_SECOND,
    METRIC_WALLETS_PER_SECOND,
    METRIC_ENTROPY_STATS,
    METRIC_STAGE_BREAKDOWN,
}

# END_CONSTANTS_FINAL_STATS_WRAPPER

# ============================================================================
# ЗАГРУЗКА C++ МОДУЛЯ С FALLBACK
# ============================================================================

# START_FUNCTION_IMPORT_CPP_MODULE
# START_CONTRACT:
# PURPOSE: Импорт C++ модуля final_stats_plugin_cpp с fallback на Python
# OUTPUTS:
# - Dict с ключами 'available', 'FinalStatsPlugin', 'FinalStatsReport', 'error'
# KEYWORDS: [PATTERN(7): ModuleCheck; DOMAIN(8): ModuleLoading; TECH(6): Import]
# END_CONTRACT

def _import_cpp_module() -> Dict[str, Any]:
    """
    Импорт C++ модуля final_stats_plugin_cpp с fallback на Python.
    
    Returns:
        Словарь с информацией о доступности модуля и классами
    """
    try:
        from final_stats_plugin_cpp import (
            FinalStatsPlugin as _FinalStatsPlugin,
            FinalStatsReport as _FinalStatsReport,
        )
        
        logger.info(f"[_import_cpp_module][MODULE_CHECK] C++ модуль final_stats_plugin_cpp доступен [SUCCESS]")
        return {
            'available': True,
            'FinalStatsPlugin': _FinalStatsPlugin,
            'FinalStatsReport': _FinalStatsReport,
        }
    except ImportError as e:
        logger.info(f"[_import_cpp_module][MODULE_CHECK] C++ модуль final_stats_plugin_cpp недоступен: {e}, используем Python fallback [INFO]")
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

# START_CLASS_FINAL_STATS_REPORT
# START_CONTRACT:
# PURPOSE: Класс для хранения финального отчёта статистики
# ATTRIBUTES:
# - total_iterations: int — общее количество итераций
# - total_wallets: int — общее количество кошельков
# - total_matches: int — общее количество совпадений
# - runtime_seconds: float — общее время выполнения в секундах
# - avg_iteration_time_ms: float — среднее время итерации в мс
# - iterations_per_second: float — итераций в секунду
# - wallets_per_second: float — кошельков в секунду
# - entropy_stats: Dict[str, Any] — статистика по энтропии
# - stage_breakdown: Dict[str, float] — разбивка по стадиям
# - timestamp: float — timestamp создания отчёта
# KEYWORDS: [PATTERN(7): DataClass; DOMAIN(8): FinalStats; CONCEPT(6): Report]
# END_CONTRACT

@dataclass
class FinalStatsReport:
    """Финальный отчёт статистики."""
    total_iterations: int = 0
    total_wallets: int = 0
    total_matches: int = 0
    runtime_seconds: float = 0.0
    avg_iteration_time_ms: float = 0.0
    iterations_per_second: float = 0.0
    wallets_per_second: float = 0.0
    entropy_stats: Dict[str, Any] = field(default_factory=dict)
    stage_breakdown: Dict[str, float] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразование отчёта в словарь.
        
        Returns:
            Словарь с данными отчёта
        """
        return {
            "total_iterations": self.total_iterations,
            "total_wallets": self.total_wallets,
            "total_matches": self.total_matches,
            "runtime_seconds": self.runtime_seconds,
            "avg_iteration_time_ms": self.avg_iteration_time_ms,
            "iterations_per_second": self.iterations_per_second,
            "wallets_per_second": self.wallets_per_second,
            "entropy_stats": self.entropy_stats,
            "stage_breakdown": self.stage_breakdown,
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat(),
        }
    
    def to_summary(self) -> str:
        """
        Генерация текстового резюме отчёта.
        
        Returns:
            Текстовое резюме
        """
        lines = [
            "=" * 60,
            "ФИНАЛЬНАЯ СТАТИСТИКА",
            "=" * 60,
            f"Итераций: {self.total_iterations:,}",
            f"Кошельков: {self.total_wallets:,}",
            f"Совпадений: {self.total_matches:,}",
            f"Время работы: {self._format_time(self.runtime_seconds)}",
            f"Итераций/сек: {self.iterations_per_second:.2f}",
            f"Кошельков/сек: {self.wallets_per_second:.2f}",
            f"Среднее время итерации: {self.avg_iteration_time_ms:.4f} мс",
            "=" * 60,
        ]
        return "\n".join(lines)
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """Форматирование времени в читаемый вид."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

# END_CLASS_FINAL_STATS_REPORT

# START_CLASS_FINAL_STATS_CONFIG
# START_CONTRACT:
# PURPOSE: Класс для хранения конфигурации плагина финальной статистики
# ATTRIBUTES:
# - enable_html_report: bool — включить HTML отчёты
# - enable_text_report: bool — включить TEXT отчёты
# - max_history_sessions: int — максимум сессий в истории
# - auto_export_on_finish: bool — автоматический экспорт при завершении
# - default_export_path: str — путь для экспорта по умолчанию
# KEYWORDS: [PATTERN(7): DataClass; DOMAIN(8): Configuration; CONCEPT(6): Settings]
# END_CONTRACT

@dataclass
class FinalStatsConfig:
    """Конфигурация плагина финальной статистики."""
    enable_html_report: bool = True
    enable_text_report: bool = True
    max_history_sessions: int = MAX_HISTORY_SESSIONS
    auto_export_on_finish: bool = False
    default_export_path: str = "final_stats"
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование конфигурации в словарь."""
        return {
            "enable_html_report": self.enable_html_report,
            "enable_text_report": self.enable_text_report,
            "max_history_sessions": self.max_history_sessions,
            "auto_export_on_finish": self.auto_export_on_finish,
            "default_export_path": self.default_export_path,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FinalStatsConfig":
        """Создание конфигурации из словаря."""
        return cls(
            enable_html_report=data.get("enable_html_report", True),
            enable_text_report=data.get("enable_text_report", True),
            max_history_sessions=data.get("max_history_sessions", MAX_HISTORY_SESSIONS),
            auto_export_on_finish=data.get("auto_export_on_finish", False),
            default_export_path=data.get("default_export_path", "final_stats"),
        )

# END_CLASS_FINAL_STATS_CONFIG

# ============================================================================
# ОСНОВНОЙ КЛАСС FINAL STATS PLUGIN WRAPPER
# ============================================================================

# START_CLASS_FINAL_STATS_PLUGIN
# START_CONTRACT:
# PURPOSE: Обёртка для C++ FinalStatsPlugin с Python-friendly интерфейсом. Обеспечивает сбор финальной статистики, генерацию отчётов и экспорт данных.
# ATTRIBUTES:
# - C++ плагин => _cpp_plugin: Optional[Any]
# - Python плагин => _py_plugin: Optional[Any]
# - Флаг использования C++ => _use_cpp: bool
# - Финальные метрики => _final_metrics: Dict[str, Any]
# - Время начала выполнения => _execution_start_time: Optional[float]
# - Время окончания выполнения => _execution_end_time: Optional[float]
# - История сессий => _session_history: List[Dict]
# - Сгенерированный отчёт => _report: Optional[FinalStatsReport]
# - Флаг готовности отчёта => _report_ready: bool
# METHODS:
# - Инициализация плагина => initialize(config)
# - Обработка события => process_event(event)
# - Получение статуса => get_status()
# - Завершение работы => shutdown()
# - Сбор финальной статистики => collect_final_stats(metrics_data)
# - Получение общего количества итераций => get_total_iterations()
# - Получение общего количества кошельков => get_total_wallets_generated()
# - Получение общего количества совпадений => get_total_matches_found()
# - Получение среднего времени итерации => get_average_iteration_time()
# - Получение общего времени выполнения => get_total_execution_time()
# - Получение статистики по энтропии => get_entropy_stats()
# - Получение разбивки по стадиям => get_stage_breakdown()
# - Получение метрик эффективности => get_efficiency_metrics()
# - Генерация отчёта => generate_report(format='json')
# - Экспорт отчёта => export_report(filepath, format='json')
# - Получение сводной статистики => get_summary_statistics()
# - Сравнение с предыдущим запуском => compare_with_previous(previous_stats)
# KEYWORDS: [PATTERN(8): Wrapper; DOMAIN(9): FinalStats; TECH(8): CppBinding; CONCEPT(7): Fallback]
# LINKS: [EXTENDS(8): BaseMonitorPlugin; USES_API(7): final_stats.py]
# END_CONTRACT

class FinalStatsPlugin(BaseMonitorPlugin):
    """
    Обёртка для C++ FinalStatsPlugin с Python-friendly интерфейсом.
    
    Обеспечивает:
    - Сбор и агрегацию финальной статистики
    - Генерацию отчётов в различных форматах (JSON, HTML, TEXT)
    - Экспорт данных в файлы
    - Сравнение с предыдущими запусками
    - Fallback на Python реализацию при отсутствии C++ модуля
    
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
    
    DESCRIPTION: str = "Обёртка для C++ плагина финальной статистики"
    """Описание плагина"""
    
    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация обёртки FinalStatsPlugin с загрузкой C++ или Python модуля
    # INPUTS:
    # - config: Optional[Dict[str, Any]] — словарь конфигурации плагина
    # OUTPUTS: Инициализированный объект FinalStatsPlugin
    # SIDE_EFFECTS: Загружает C++ модуль или Python fallback; инициализирует хранилище метрик
    # KEYWORDS: [CONCEPT(5): Initialization; DOMAIN(7): PluginSetup]
    # TEST_CONDITIONS_SUCCESS_CRITERIA: Плагин должен корректно определить доступность C++ модуля
    # END_CONTRACT
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Инициализация обёртки FinalStatsPlugin.
        
        Args:
            config: Словарь конфигурации плагина (опционально)
        """
        # Инициализация базового класса
        super().__init__(name="final_stats", config=config)
        
        # Получение информации о C++ модуле
        self._cpp_module_info = _get_cpp_module_info()
        self._use_cpp = self._cpp_module_info.get('available', False)
        
        # Инициализация C++ или Python плагина
        self._cpp_plugin = None
        self._py_plugin = None
        
        if self._use_cpp:
            try:
                self._cpp_plugin = self._cpp_module_info['FinalStatsPlugin']()
                logger.info(f"[FinalStatsPlugin][INIT][ConditionCheck] Используется C++ плагин [SUCCESS]")
            except Exception as e:
                logger.warning(f"[FinalStatsPlugin][INIT][ExceptionCaught] Ошибка при создании C++ плагина: {e}, используем Python fallback")
                self._use_cpp = False
        
        if not self._use_cpp:
            # Python реализация не используется - используем встроенную реализацию
            logger.info(f"[FinalStatsPlugin][INIT][ConditionCheck] Используется встроенная Python реализация [SUCCESS]")
        
        # Инициализация хранилища данных
        self._final_metrics: Dict[str, Any] = {}
        self._execution_start_time: Optional[float] = None
        self._execution_end_time: Optional[float] = None
        self._session_history: List[Dict] = []
        self._report: Optional[FinalStatsReport] = None
        self._report_ready: bool = False
        self._has_final_data: bool = False
        
        # Конфигурация
        self._plugin_config = FinalStatsConfig.from_dict(config or {})
        
        # Логирование
        self._logger.info(f"[FinalStatsPlugin][INIT][VarCheck] Плагин инициализирован, C++: {self._use_cpp} [VALUE]")
    
    # END_METHOD___init__
    
    # ============================================================================
    # СВОЙСТВА (PROPERTIES)
    # ============================================================================
    
    # START_PROPERTY_HAS_FINAL_DATA
    @property
    def has_final_data(self) -> bool:
        """
        Проверка наличия финальных данных.
        
        Returns:
            True если финальные данные собраны
        """
        return self._has_final_data
    # END_PROPERTY_HAS_FINAL_DATA
    
    # START_PROPERTY_REPORT_READY
    @property
    def report_ready(self) -> bool:
        """
        Проверка готовности отчёта.
        
        Returns:
            True если отчёт готов
        """
        return self._report_ready
    # END_PROPERTY_REPORT_READY
    
    # START_PROPERTY_EXECUTION_START_TIME
    @property
    def execution_start_time(self) -> Optional[float]:
        """
        Получение времени начала выполнения.
        
        Returns:
            Timestamp времени начала или None
        """
        return self._execution_start_time
    # END_PROPERTY_EXECUTION_START_TIME
    
    # START_PROPERTY_EXECUTION_END_TIME
    @property
    def execution_end_time(self) -> Optional[float]:
        """
        Получения времени окончания выполнения.
        
        Returns:
            Timestamp времени окончания или None
        """
        return self._execution_end_time
    # END_PROPERTY_EXECUTION_END_TIME
    
    # START_PROPERTY_FINAL_METRICS
    @property
    def final_metrics(self) -> Dict[str, Any]:
        """
        Получение финальных метрик.
        
        Returns:
            Копия словаря финальных метрик
        """
        return self._final_metrics.copy()
    # END_PROPERTY_FINAL_METRICS
    
    # START_PROPERTY_SESSION_HISTORY
    @property
    def session_history(self) -> List[Dict]:
        """
        Получение истории сессий.
        
        Returns:
            Копия списка истории сессий
        """
        return self._session_history.copy()
    # END_PROPERTY_SESSION_HISTORY
    
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
        self._logger.info(f"[FinalStatsPlugin][INITIALIZE][StepComplete] Начало инициализации плагина")
        
        # Обработка случая когда config равен None
        if config is None:
            config = {}
        
        # Обновление конфигурации
        if config and 'config' in config:
            self._plugin_config = FinalStatsConfig.from_dict(config['config'])
        
        # Сохранение ссылки на приложение
        self._app = config.get('app')
        
        # Обновление статуса
        self._status["state"] = "initialized"
        self._status["message"] = "Plugin initialized"
        
        self._logger.info(f"[FinalStatsPlugin][INITIALIZE][StepComplete] Инициализация плагина завершена [SUCCESS]")
    
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
        
        self._logger.debug(f"[FinalStatsPlugin][PROCESS_EVENT][ConditionCheck] Получено событие типа: {event_type} [VALUE]")
        
        if event_type == EVENT_TYPE_METRIC:
            # Обработка события метрики (финальной)
            metrics = event.get('data', {})
            if isinstance(metrics, dict):
                self.collect_final_stats(metrics)
            
            self._logger.debug(f"[FinalStatsPlugin][PROCESS_EVENT][StepComplete] Обработано событие метрики [SUCCESS]")
        
        elif event_type == EVENT_TYPE_START:
            # Запуск выполнения
            self._execution_start_time = time.time()
            self._status["state"] = "running"
            self._status["message"] = "Execution started"
            self._logger.info(f"[FinalStatsPlugin][PROCESS_EVENT][StepComplete] Получено событие START [SUCCESS]")
        
        elif event_type == EVENT_TYPE_STOP:
            # Остановка выполнения
            self._execution_end_time = time.time()
            self._status["state"] = "completed"
            self._status["message"] = "Execution completed"
            self._logger.info(f"[FinalStatsPlugin][PROCESS_EVENT][StepComplete] Получено событие STOP [SUCCESS]")
        
        elif event_type == EVENT_TYPE_STATUS:
            # Обработка события статуса
            status_data = event.get('data', {})
            self._logger.debug(f"[FinalStatsPlugin][PROCESS_EVENT][Info] Событие статуса: {status_data}")
        
        else:
            self._logger.warning(f"[FinalStatsPlugin][PROCESS_EVENT][ConditionCheck] Неизвестный тип события: {event_type} [FAIL]")
    
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
            "has_final_data": self._has_final_data,
            "report_ready": self._report_ready,
            "execution_start_time": self._execution_start_time,
            "execution_end_time": self._execution_end_time,
            "total_iterations": self.get_total_iterations(),
            "total_wallets": self.get_total_wallets_generated(),
            "total_matches": self.get_total_matches_found(),
            "total_execution_time": self.get_total_execution_time(),
        }
        
        self._logger.debug(f"[FinalStatsPlugin][GET_STATUS][ReturnData] Статус: {status} [VALUE]")
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
        self._logger.info(f"[FinalStatsPlugin][SHUTDOWN][StepComplete] Начало завершения работы плагина")
        
        # Фиксация времени окончания если ещё не зафиксировано
        if self._execution_end_time is None:
            self._execution_end_time = time.time()
        
        # Сохранение текущей сессии в историю
        if self._has_final_data:
            self._save_session_to_history()
        
        # Обновление статуса
        self._status["state"] = "shutdown"
        self._status["message"] = "Plugin shutdown complete"
        
        self._logger.info(f"[FinalStatsPlugin][SHUTDOWN][StepComplete] Завершение работы плагина завершено [SUCCESS]")
    
    # END_METHOD_SHUTDOWN
    
    # START_METHOD_ON_FINISH
    # START_CONTRACT:
    # PURPOSE: Обработка события завершения работы и сбор финальной статистики
    # INPUTS:
    # - final_metrics: Dict[str, Any] — словарь финальных метрик
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Обновляет внутренние метрики; генерирует отчёт
    # KEYWORDS: [DOMAIN(8): FinalStats; CONCEPT(7): EventHandler]
    # END_CONTRACT
    def on_finish(self, final_metrics: Dict[str, Any]) -> None:
        """
        Обработка события завершения работы и сбор финальной статистики.
        
        Args:
            final_metrics: Словарь финальных метрик
        """
        self._logger.info(f"[FinalStatsPlugin][ON_FINISH][StepComplete] Обработка завершения работы")
        
        # Вызываем collect_final_stats для сбора статистики
        self.collect_final_stats(final_metrics)
        
        self._logger.info(f"[FinalStatsPlugin][ON_FINISH][StepComplete] Финальная статистика собрана [SUCCESS]")
    
    # END_METHOD_ON_FINISH
    
    # START_METHOD_UPDATE_UI
    # START_CONTRACT:
    # PURPOSE: Получение данных для обновления UI
    # OUTPUTS:
    # - Dict[str, Any] — словарь с данными для UI
    # KEYWORDS: [TECH(7): Gradio; DOMAIN(8): UIComponents]
    # END_CONTRACT
    def update_ui(self) -> Dict[str, Any]:
        """
        Получение данных для обновления UI.
        
        Returns:
            Словарь с данными для обновления UI-компонентов
        """
        summary = self.get_summary_statistics()
        
        # Форматирование времени
        runtime_seconds = summary.get("total_execution_time", 0)
        hours = int(runtime_seconds // 3600)
        minutes = int((runtime_seconds % 3600) // 60)
        secs = int(runtime_seconds % 60)
        runtime_formatted = f"{hours:02d}:{minutes:02d}:{secs:02d}"
        
        ui_data = {
            "total_iterations": summary.get("total_iterations", 0),
            "total_matches": summary.get("total_matches", 0),
            "total_wallets": summary.get("total_wallets", 0),
            "runtime": runtime_seconds,
            "runtime_formatted": runtime_formatted,
            "avg_iteration_time": summary.get("average_iteration_time", 0),
            "iterations_per_second": summary.get("iterations_per_second", 0),
            "wallets_per_second": summary.get("wallets_per_second", 0),
        }
        
        self._logger.debug(f"[FinalStatsPlugin][UPDATE_UI][ReturnData] UI данные: {ui_data} [VALUE]")
        return ui_data
    
    # END_METHOD_UPDATE_UI
    
    # ============================================================================
    # СПЕЦИФИЧЕСКИЕ МЕТОДЫ ФИНАЛЬНОЙ СТАТИСТИКИ
    # ============================================================================
    
    # START_METHOD_COLLECT_FINAL_STATS
    # START_CONTRACT:
    # PURPOSE: Сбор финальной статистики из переданных метрик
    # INPUTS:
    # - metrics_data: Dict[str, Any] — словарь финальных метрик
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Обновляет внутренние метрики; вычисляет производные показатели
    # KEYWORDS: [DOMAIN(9): Statistics; CONCEPT(7): DataCollection]
    # END_CONTRACT
    def collect_final_stats(self, metrics_data: Dict[str, Any]) -> None:
        """
        Сбор финальной статистики из переданных метрик.
        
        Args:
            metrics_data: Словарь финальных метрик
        """
        self._logger.info(f"[FinalStatsPlugin][COLLECT_FINAL_STATS][StepComplete] Начало сбора финальной статистики")
        
        # Копирование метрик
        self._final_metrics = metrics_data.copy()
        
        # DYNAMIC_LOG: Логируем полученные метрики для диагностики
        self._logger.debug(f"[FinalStatsPlugin][COLLECT_FINAL_STATS][Debug] Полученные метрики: {self._final_metrics} [VALUE]")
        
        # Вычисление производных показателей
        # DYNAMIC_LOG: Проверяем наличие ключей runtime_seconds и uptime
        runtime = self._final_metrics.get(METRIC_RUNTIME_SECONDS, 0.0)
        if runtime == 0.0:
            # Пробуем получить из ключа uptime (используется в gradio_app)
            runtime = self._final_metrics.get("uptime", 0.0)
            self._logger.debug(f"[FinalStatsPlugin][COLLECT_FINAL_STATS][Debug] Использован ключ 'uptime': {runtime} [VALUE]")
        
        iterations = self._final_metrics.get(METRIC_ITERATION_COUNT, 0)
        wallets = self._final_metrics.get(METRIC_WALLET_COUNT, 0)
        
        self._logger.debug(f"[FinalStatsPlugin][COLLECT_FINAL_STATS][Debug] runtime={runtime}, iterations={iterations}, wallets={wallets} [VALUE]")
        
        if runtime > 0 and iterations > 0:
            self._final_metrics[METRIC_AVG_ITERATION_TIME_MS] = (runtime / iterations) * 1000
            self._final_metrics[METRIC_ITERATIONS_PER_SECOND] = iterations / runtime
            self._final_metrics[METRIC_WALLETS_PER_SECOND] = wallets / runtime
        
        # Установка флага наличия данных
        self._has_final_data = True
        
        # Генерация отчёта
        self._report = self._generate_internal_report()
        self._report_ready = True
        
        # Автоматический экспорт если настроен
        if self._plugin_config.auto_export_on_finish:
            self.export_report(
                f"{self._plugin_config.default_export_path}.json",
                format="json"
            )
        
        self._logger.info(f"[FinalStatsPlugin][COLLECT_FINAL_STATS][StepComplete] Финальная статистика собрана: {iterations} итераций, {runtime:.2f} сек [SUCCESS]")
    
    # END_METHOD_COLLECT_FINAL_STATS
    
    # START_METHOD_GET_TOTAL_ITERATIONS
    # START_CONTRACT:
    # PURPOSE: Получение общего количества итераций
    # OUTPUTS:
    # - int — общее количество итераций
    # KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): Statistics]
    # END_CONTRACT
    def get_total_iterations(self) -> int:
        """
        Получение общего количества итераций.
        
        Returns:
            Общее количество итераций
        """
        return self._final_metrics.get(METRIC_ITERATION_COUNT, 0)
    
    # END_METHOD_GET_TOTAL_ITERATIONS
    
    # START_METHOD_GET_TOTAL_WALLETS_GENERATED
    # START_CONTRACT:
    # PURPOSE: Получение общего количества сгенерированных кошельков
    # OUTPUTS:
    # - int — общее количество кошельков
    # KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): Statistics]
    # END_CONTRACT
    def get_total_wallets_generated(self) -> int:
        """
        Получение общего количества сгенерированных кошельков.
        
        Returns:
            Общее количество кошельков
        """
        return self._final_metrics.get(METRIC_WALLET_COUNT, 0)
    
    # END_METHOD_GET_TOTAL_WALLETS_GENERATED
    
    # START_METHOD_GET_TOTAL_MATCHES_FOUND
    # START_CONTRACT:
    # PURPOSE: Получение общего количества найденных совпадений
    # OUTPUTS:
    # - int — общее количество совпадений
    # KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): Statistics]
    # END_CONTRACT
    def get_total_matches_found(self) -> int:
        """
        Получение общего количества найденных совпадений.
        
        Returns:
            Общее количество совпадений
        """
        return self._final_metrics.get(METRIC_MATCH_COUNT, 0)
    
    # END_METHOD_GET_TOTAL_MATCHES_FOUND
    
    # START_METHOD_GET_AVERAGE_ITERATION_TIME
    # START_CONTRACT:
    # PURPOSE: Получение среднего времени итерации
    # OUTPUTS:
    # - float — среднее время итерации в миллисекундах
    # KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): Performance]
    # END_CONTRACT
    def get_average_iteration_time(self) -> float:
        """
        Получение среднего времени итерации.
        
        Returns:
            Среднее время итерации в миллисекундах
        """
        return self._final_metrics.get(METRIC_AVG_ITERATION_TIME_MS, 0.0)
    
    # END_METHOD_GET_AVERAGE_ITERATION_TIME
    
    # START_METHOD_GET_TOTAL_EXECUTION_TIME
    # START_CONTRACT:
    # PURPOSE: Получение общего времени выполнения
    # OUTPUTS:
    # - float — общее время выполнения в секундах
    # KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): Performance]
    # END_CONTRACT
    def get_total_execution_time(self) -> float:
        """
        Получение общего времени выполнения.
        
        Returns:
            Общее время выполнения в секундах
        """
        # Проверяем внутренние таймеры
        if self._execution_end_time and self._execution_start_time:
            return self._execution_end_time - self._execution_start_time
        
        # Пробуем получить из метрик (проверяем все возможные ключи)
        runtime = self._final_metrics.get(METRIC_RUNTIME_SECONDS, 0.0)
        if runtime == 0.0:
            # Пробуем ключ uptime (используется в gradio_app)
            runtime = self._final_metrics.get("uptime", 0.0)
        
        return runtime
    
    # END_METHOD_GET_TOTAL_EXECUTION_TIME
    
    # START_METHOD_GET_ENTROPY_STATS
    # START_CONTRACT:
    # PURPOSE: Получение статистики по энтропии
    # OUTPUTS:
    # - Dict[str, Any] — статистика по энтропии
    # KEYWORDS: [CONCEPT(5): Getter; DOMAIN(7): Entropy]
    # END_CONTRACT
    def get_entropy_stats(self) -> Dict[str, Any]:
        """
        Получение статистики по энтропии.
        
        Returns:
            Словарь со статистикой по энтропии
        """
        return self._final_metrics.get(METRIC_ENTROPY_STATS, {})
    
    # END_METHOD_GET_ENTROPY_STATS
    
    # START_METHOD_GET_STAGE_BREAKDOWN
    # START_CONTRACT:
    # PURPOSE: Получение разбивки по стадиям
    # OUTPUTS:
    # - Dict[str, float] — разбивка по стадиям (время в секундах)
    # KEYWORDS: [CONCEPT(5): Getter; DOMAIN(7): Stages]
    # END_CONTRACT
    def get_stage_breakdown(self) -> Dict[str, float]:
        """
        Получение разбивки по стадиям.
        
        Returns:
            Словарь со временем выполнения каждой стадии в секундах
        """
        return self._final_metrics.get(METRIC_STAGE_BREAKDOWN, {})
    
    # END_METHOD_GET_STAGE_BREAKDOWN
    
    # START_METHOD_GET_EFFICIENCY_METRICS
    # START_CONTRACT:
    # PURPOSE: Получение метрик эффективности
    # OUTPUTS:
    # - Dict[str, Any] — метрики эффективности
    # KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): Efficiency]
    # END_CONTRACT
    def get_efficiency_metrics(self) -> Dict[str, Any]:
        """
        Получение метрик эффективности.
        
        Returns:
            Словарь с метриками эффективности
        """
        return {
            "iterations_per_second": self._final_metrics.get(METRIC_ITERATIONS_PER_SECOND, 0.0),
            "wallets_per_second": self._final_metrics.get(METRIC_WALLETS_PER_SECOND, 0.0),
            "avg_iteration_time_ms": self._final_metrics.get(METRIC_AVG_ITERATION_TIME_MS, 0.0),
            "total_execution_time": self.get_total_execution_time(),
            "total_iterations": self.get_total_iterations(),
            "total_wallets": self.get_total_wallets_generated(),
        }
    
    # END_METHOD_GET_EFFICIENCY_METRICS
    
    # START_METHOD_GENERATE_REPORT
    # START_CONTRACT:
    # PURPOSE: Генерация отчёта в указанном формате
    # INPUTS:
    # - format: str — формат отчёта ('json', 'html', 'text')
    # OUTPUTS:
    # - str — сгенерированный отчёт
    # KEYWORDS: [DOMAIN(7): Reporting; CONCEPT(6): Generation]
    # END_CONTRACT
    def generate_report(self, format: str = "json") -> str:
        """
        Генерация отчёта в указанном формате.
        
        Args:
            format: Формат отчёта ('json', 'html', 'text')
            
        Returns:
            Строка сгенерированного отчёта
        """
        format = format.lower()
        
        if format not in SUPPORTED_FORMATS:
            self._logger.warning(f"[FinalStatsPlugin][GENERATE_REPORT][ConditionCheck] Неподдерживаемый формат: {format} [FAIL]")
            format = DEFAULT_REPORT_FORMAT
        
        self._logger.info(f"[FinalStatsPlugin][GENERATE_REPORT][StepComplete] Генерация отчёта в формате {format}")
        
        if format == "json":
            return self._generate_json_report()
        elif format == "html":
            return self._generate_html_report()
        elif format == "text":
            return self._generate_text_report()
        
        return ""
    
    # END_METHOD_GENERATE_REPORT
    
    # START_METHOD_EXPORT_REPORT
    # START_CONTRACT:
    # PURPOSE: Экспорт отчёта в файл
    # INPUTS:
    # - filepath: str — путь к файлу для сохранения
    # - format: str — формат экспорта ('json', 'html', 'text')
    # OUTPUTS:
    # - bool — True если экспорт успешен
    # SIDE_EFFECTS: Создаёт файл с отчётом
    # KEYWORDS: [DOMAIN(7): Export; TECH(5): FileIO]
    # END_CONTRACT
    def export_report(self, filepath: str, format: str = "json") -> bool:
        """
        Экспорт отчёта в файл.
        
        Args:
            filepath: Путь к файлу для сохранения
            format: Формат экспорта ('json', 'html', 'text')
            
        Returns:
            True если экспорт успешен
        """
        try:
            report_content = self.generate_report(format)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self._logger.info(f"[FinalStatsPlugin][EXPORT_REPORT][StepComplete] Отчёт экспортирован в {filepath} [SUCCESS]")
            return True
        except Exception as e:
            self._logger.error(f"[FinalStatsPlugin][EXPORT_REPORT][ExceptionCaught] Ошибка экспорта: {e} [FAIL]")
            return False
    
    # END_METHOD_EXPORT_REPORT
    
    # START_METHOD_GET_SUMMARY_STATISTICS
    # START_CONTRACT:
    # PURPOSE: Получение сводной статистики
    # OUTPUTS:
    # - Dict[str, Any] — словарь со сводной статистикой
    # KEYWORDS: [CONCEPT(6): Summary; DOMAIN(8): Statistics]
    # END_CONTRACT
    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Получение сводной статистики.
        
        Returns:
            Словарь со сводной статистикой
        """
        summary = {
            "total_iterations": self.get_total_iterations(),
            "total_wallets": self.get_total_wallets_generated(),
            "total_matches": self.get_total_matches_found(),
            "total_execution_time": self.get_total_execution_time(),
            "average_iteration_time": self.get_average_iteration_time(),
            "iterations_per_second": self._final_metrics.get(METRIC_ITERATIONS_PER_SECOND, 0.0),
            "wallets_per_second": self._final_metrics.get(METRIC_WALLETS_PER_SECOND, 0.0),
            "entropy_stats": self.get_entropy_stats(),
            "stage_breakdown": self.get_stage_breakdown(),
            "efficiency_metrics": self.get_efficiency_metrics(),
            "execution_start_time": self._execution_start_time,
            "execution_end_time": self._execution_end_time,
            "report_ready": self._report_ready,
            "has_final_data": self._has_final_data,
        }
        
        self._logger.debug(f"[FinalStatsPlugin][GET_SUMMARY_STATISTICS][ReturnData] Сводка: {summary} [VALUE]")
        return summary
    
    # END_METHOD_GET_SUMMARY_STATISTICS
    
    # START_METHOD_COMPARE_WITH_PREVIOUS
    # START_CONTRACT:
    # PURPOSE: Сравнение текущей статистики с предыдущим запуском
    # INPUTS:
    # - previous_stats: Dict[str, Any] — статистика предыдущего запуска
    # OUTPUTS:
    # - Dict[str, Any] — словарь с результатами сравнения
    # KEYWORDS: [DOMAIN(8): Comparison; CONCEPT(7): Analysis]
    # END_CONTRACT
    def compare_with_previous(self, previous_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Сравнение текущей статистики с предыдущим запуском.
        
        Args:
            previous_stats: Статистика предыдущего запуска
            
        Returns:
            Словарь с результатами сравнения
        """
        current = self.get_summary_statistics()
        
        # Сравнение итераций
        prev_iterations = previous_stats.get("total_iterations", 0)
        curr_iterations = current.get("total_iterations", 0)
        iterations_diff = curr_iterations - prev_iterations
        iterations_pct = (iterations_diff / prev_iterations * 100) if prev_iterations > 0 else 0
        
        # Сравнение времени
        prev_time = previous_stats.get("total_execution_time", 0)
        curr_time = current.get("total_execution_time", 0)
        time_diff = curr_time - prev_time
        
        # Сравнение скорости
        prev_rate = previous_stats.get("iterations_per_second", 0)
        curr_rate = current.get("iterations_per_second", 0)
        rate_diff = curr_rate - prev_rate
        
        comparison = {
            "iterations": {
                "previous": prev_iterations,
                "current": curr_iterations,
                "difference": iterations_diff,
                "percent_change": iterations_pct,
            },
            "execution_time": {
                "previous": prev_time,
                "current": curr_time,
                "difference": time_diff,
            },
            "iteration_rate": {
                "previous": prev_rate,
                "current": curr_rate,
                "difference": rate_diff,
            },
            "improvement": iterations_pct > 0,
        }
        
        self._logger.info(f"[FinalStatsPlugin][COMPARE_WITH_PREVIOUS][StepComplete] Сравнение выполнено [SUCCESS]")
        return comparison
    
    # END_METHOD_COMPARE_WITH_PREVIOUS
    
    # ============================================================================
    # ВНУТРЕННИЕ МЕТОДЫ
    # ============================================================================
    
    # START_METHOD_GENERATE_INTERNAL_REPORT
    # START_CONTRACT:
    # PURPOSE: Генерация внутреннего объекта отчёта
    # OUTPUTS:
    # - FinalStatsReport — объект отчёта
    # KEYWORDS: [DOMAIN(7): Reporting; CONCEPT(6): Generation]
    # END_CONTRACT
    def _generate_internal_report(self) -> FinalStatsReport:
        """Генерация внутреннего объекта отчёта."""
        return FinalStatsReport(
            total_iterations=self.get_total_iterations(),
            total_wallets=self.get_total_wallets_generated(),
            total_matches=self.get_total_matches_found(),
            runtime_seconds=self.get_total_execution_time(),
            avg_iteration_time_ms=self.get_average_iteration_time(),
            iterations_per_second=self._final_metrics.get(METRIC_ITERATIONS_PER_SECOND, 0.0),
            wallets_per_second=self._final_metrics.get(METRIC_WALLETS_PER_SECOND, 0.0),
            entropy_stats=self.get_entropy_stats(),
            stage_breakdown=self.get_stage_breakdown(),
            timestamp=time.time(),
        )
    
    # END_METHOD_GENERATE_INTERNAL_REPORT
    
    # START_METHOD_GENERATE_JSON_REPORT
    # START_CONTRACT:
    # PURPOSE: Генерация JSON отчёта
    # OUTPUTS:
    # - str — JSON строка
    # KEYWORDS: [DOMAIN(7): JSON; TECH(6): Serialization]
    # END_CONTRACT
    def _generate_json_report(self) -> str:
        """Генерация JSON отчёта."""
        report_data = self.get_summary_statistics()
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    
    # END_METHOD_GENERATE_JSON_REPORT
    
    # START_METHOD_GENERATE_HTML_REPORT
    # START_CONTRACT:
    # PURPOSE: Генерация HTML отчёта
    # OUTPUTS:
    # - str — HTML строка
    # KEYWORDS: [DOMAIN(6): HTML; TECH(5): Web]
    # END_CONTRACT
    def _generate_html_report(self) -> str:
        """Генерация HTML отчёта."""
        summary = self.get_summary_statistics()
        
        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Финальная статистика</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .section {{
            margin: 20px 0;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }}
        .section h2 {{
            color: #667eea;
            margin-top: 0;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        .metric:last-child {{
            border-bottom: none;
        }}
        .metric-label {{
            font-weight: bold;
            color: #555;
        }}
        .metric-value {{
            color: #333;
        }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            color: #888;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Финальная статистика</h1>
        
        <div class="section">
            <h2>Основные показатели</h2>
            <div class="metric">
                <span class="metric-label">Всего итераций:</span>
                <span class="metric-value">{summary.get('total_iterations', 0):,}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Всего кошельков:</span>
                <span class="metric-value">{summary.get('total_wallets', 0):,}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Найдено совпадений:</span>
                <span class="metric-value">{summary.get('total_matches', 0):,}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Время работы:</span>
                <span class="metric-value">{self._format_time(summary.get('total_execution_time', 0))}</span>
            </div>
        </div>
        
        <div class="section">
            <h2>Производительность</h2>
            <div class="metric">
                <span class="metric-label">Итераций в секунду:</span>
                <span class="metric-value">{summary.get('iterations_per_second', 0):.2f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Кошельков в секунду:</span>
                <span class="metric-value">{summary.get('wallets_per_second', 0):.2f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Среднее время итерации:</span>
                <span class="metric-value">{summary.get('average_iteration_time', 0):.4f} мс</span>
            </div>
        </div>
        
        <div class="footer">
            Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    # END_METHOD_GENERATE_HTML_REPORT
    
    # START_METHOD_GENERATE_TEXT_REPORT
    # START_CONTRACT:
    # PURPOSE: Генерация текстового отчёта
    # OUTPUTS:
    # - str — текстовая строка
    # KEYWORDS: [DOMAIN(5): Text; TECH(5): Plain]
    # END_CONTRACT
    def _generate_text_report(self) -> str:
        """Генерация текстового отчёта."""
        summary = self.get_summary_statistics()
        
        lines = [
            "=" * 60,
            "ФИНАЛЬНАЯ СТАТИСТИКА ГЕНЕРАТОРА КОШЕЛЬКОВ",
            "=" * 60,
            "",
            "ОСНОВНЫЕ ПОКАЗАТЕЛИ:",
            f"  Всего итераций: {summary.get('total_iterations', 0):,}",
            f"  Всего кошельков: {summary.get('total_wallets', 0):,}",
            f"  Найдено совпадений: {summary.get('total_matches', 0):,}",
            f"  Время работы: {self._format_time(summary.get('total_execution_time', 0))}",
            "",
            "ПРОИЗВОДИТЕЛЬНОСТЬ:",
            f"  Итераций в секунду: {summary.get('iterations_per_second', 0):.2f}",
            f"  Кошельков в секунду: {summary.get('wallets_per_second', 0):.2f}",
            f"  Среднее время итерации: {summary.get('average_iteration_time', 0):.4f} мс",
            "",
            "=" * 60,
            f"Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
        ]
        
        return "\n".join(lines)
    
    # END_METHOD_GENERATE_TEXT_REPORT
    
    # START_METHOD_FORMAT_TIME
    # START_CONTRACT:
    # PURPOSE: Форматирование времени в читаемый вид
    # INPUTS:
    # - seconds: float — время в секундах
    # OUTPUTS:
    # - str — отформатированное время
    # KEYWORDS: [CONCEPT(7): Formatting]
    # END_CONTRACT
    def _format_time(self, seconds: float) -> str:
        """Форматирование времени в читаемый вид."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    # END_METHOD_FORMAT_TIME
    
    # START_METHOD_SAVE_SESSION_TO_HISTORY
    # START_CONTRACT:
    # PURPOSE: Сохранение текущей сессии в историю
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Добавляет запись в историю сессий
    # KEYWORDS: [CONCEPT(7): History; DOMAIN(8): Persistence]
    # END_CONTRACT
    def _save_session_to_history(self) -> None:
        """Сохранение текущей сессии в историю."""
        session_data = self.get_summary_statistics()
        session_data["session_timestamp"] = time.time()
        
        self._session_history.append(session_data)
        
        # Ограничение размера истории
        max_sessions = self._plugin_config.max_history_sessions
        if len(self._session_history) > max_sessions:
            self._session_history = self._session_history[-max_sessions:]
        
        self._logger.debug(f"[FinalStatsPlugin][SAVE_SESSION_TO_HISTORY][StepComplete] Сессия сохранена в историю [SUCCESS]")
    
    # END_METHOD_SAVE_SESSION_TO_HISTORY
    
    # START_METHOD_RESET
    # START_CONTRACT:
    # PURPOSE: Сброс статистики
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Очищает все данные
    # KEYWORDS: [CONCEPT(7): Reset; DOMAIN(8): Statistics]
    # END_CONTRACT
    def reset(self) -> None:
        """
        Сброс статистики.
        """
        self._logger.info(f"[FinalStatsPlugin][RESET][StepComplete] Начало сброса статистики")
        
        # Очистка метрик
        self._final_metrics = {}
        self._execution_start_time = None
        self._execution_end_time = None
        self._report = None
        self._report_ready = False
        self._has_final_data = False
        
        # Обновление статуса
        self._status["state"] = "initialized"
        self._status["message"] = "Statistics reset"
        
        self._logger.info(f"[FinalStatsPlugin][RESET][StepComplete] Статистика сброшена [SUCCESS]")
    
    # END_METHOD_RESET
    
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
            "summary": self.get_summary_statistics(),
            "has_final_data": self._has_final_data,
            "report_ready": self._report_ready,
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
        return f"FinalStatsPlugin(name={self._name}, using_cpp={self._use_cpp}, has_data={self._has_final_data})"
    
    # END_METHOD___repr__
    
    # START_METHOD___str__
    # START_CONTRACT:
    # PURPOSE: Читаемое строковое представление плагина
    # OUTPUTS: str — читаемое представление
    # KEYWORDS: [CONCEPT(5): StringRepr]
    # END_CONTRACT
    def __str__(self) -> str:
        """Читаемое строковое представление плагина."""
        return f"FinalStatsPlugin '{self._name}' (C++: {self._use_cpp}, данные: {self._has_final_data}, отчёт: {self._report_ready})"
    
    # END_METHOD___str__


# END_CLASS_FINAL_STATS_PLUGIN

# ============================================================================
# ФАБРИКА ПЛАГИНА
# ============================================================================

# START_FUNCTION_CREATE_FINAL_STATS_PLUGIN
# START_CONTRACT:
# PURPOSE: Фабричная функция для создания плагина финальной статистики
# INPUTS:
# - config: Optional[Dict[str, Any]] — конфигурация плагина
# OUTPUTS:
# - FinalStatsPlugin — созданный экземпляр плагина
# KEYWORDS: [PATTERN(7): Factory; DOMAIN(8): PluginCreation]
# END_CONTRACT

def create_final_stats_plugin(config: Optional[Dict[str, Any]] = None) -> FinalStatsPlugin:
    """
    Фабричная функция для создания плагина финальной статистики.
    
    Args:
        config: Конфигурация плагина (опционально)
        
    Returns:
        Экземпляр FinalStatsPlugin
    """
    logger.info(f"[create_final_stats_plugin][ConditionCheck] Создание плагина финальной статистики [ATTEMPT]")
    plugin = FinalStatsPlugin(config=config)
    logger.info(f"[create_final_stats_plugin][StepComplete] Плагин создан: {plugin} [SUCCESS]")
    return plugin

# END_FUNCTION_CREATE_FINAL_STATS_PLUGIN

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
        "name": "final_stats",
        "priority": 30,
        "enabled": True,
        "config": FinalStatsConfig().to_dict(),
    }

# END_FUNCTION_GET_DEFAULT_CONFIG

# ============================================================================
# ЭКСПОРТ
# ============================================================================

__all__ = [
    # Классы
    "FinalStatsPlugin",
    "FinalStatsReport",
    "FinalStatsConfig",
    # Функции
    "create_final_stats_plugin",
    "get_default_config",
    # Константы
    "METRIC_ITERATION_COUNT",
    "METRIC_WALLET_COUNT",
    "METRIC_MATCH_COUNT",
    "METRIC_RUNTIME_SECONDS",
    "METRIC_AVG_ITERATION_TIME_MS",
    "METRIC_ITERATIONS_PER_SECOND",
    "METRIC_WALLETS_PER_SECOND",
    "METRIC_ENTROPY_STATS",
    "METRIC_STAGE_BREAKDOWN",
    "ALL_FINAL_METRICS",
    "SUPPORTED_FORMATS",
    "STAT_SECTIONS",
]

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ ПРИ ИМПОРТЕ
# ============================================================================

logger.info(f"[INIT] Модуль final_stats_wrapper.py загружен, C++ модуль доступен: {_get_cpp_module_info().get('available', False)} [INFO]")
