# FILE: src/monitor/_cpp/__init__.py
# VERSION: 2.1.0

"""
Python-обёртки для C++ модулей плагинов мониторинга.

Этот модуль обеспечивает доступ к C++ модулям плагинов мониторинга.
При отсутствии C++ модулей соответствующие флаги *_AVAILABLE устанавливаются в False.

Требуемые C++ модули:
    - plugin_base_cpp: Базовый класс плагинов
    - live_stats_plugin_cpp: Плагин live-статистики
    - match_notifier_plugin_cpp: Плагин уведомлений о совпадениях
    - final_stats_plugin_cpp: Плагин финальной статистики
    - log_parser_cpp: Парсер логов
    - metrics_cpp: Модуль метрик

Флаги доступности:
    - CPP_AVAILABLE: Общая доступность C++ модулей
    - LOG_PARSER_AVAILABLE: Доступность парсера логов
    - METRICS_AVAILABLE: Доступность модуля метрик
    - PLUGIN_BASE_AVAILABLE: Доступность базового плагина
    - LIVE_STATS_AVAILABLE: Доступность live-статистики
    - FINAL_STATS_AVAILABLE: Доступность финальной статистики
    - MATCH_NOTIFIER_AVAILABLE: Доступность уведомлений о совпадениях
"""

import logging
import sys
import os
from pathlib import Path

# Добавляем путь к текущей директории для поиска .so модулей
_cpp_dir = Path(__file__).parent
if str(_cpp_dir) not in sys.path:
    sys.path.insert(0, str(_cpp_dir))

# ============================================================================
# КОНФИГУРАЦИЯ ЛОГИРОВАНИЯ
# ============================================================================

def _setup_file_logging():
    """Настройка логирования в файл app.log."""
    project_root = Path(__file__).parent.parent.parent
    log_file = project_root / "app.log"
    
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s][%(name)s][%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    return file_handler

# Настройка логирования
_logger = logging.getLogger("src.monitor._cpp")
_logger.setLevel(logging.INFO)

_file_handler = _setup_file_logging()
_logger.addHandler(_file_handler)
_logger.propagate = False

# ============================================================================
# ФЛАГИ ДОСТУПНОСТИ C++ МОДУЛЕЙ
# ============================================================================

VERSION: str = "2.1.0"
"""Версия пакета C++ обёрток"""

# Флаги доступности - будут установлены при проверке модулей
LOG_PARSER_AVAILABLE: bool = False
"""FLAG доступности C++ модуля log_parser"""

METRICS_AVAILABLE: bool = False
"""FLAG доступности C++ модуля метрик"""

PLUGIN_BASE_AVAILABLE: bool = False
"""FLAG доступности C++ модуля базового плагина"""

LIVE_STATS_AVAILABLE: bool = False
"""FLAG доступности C++ модуля live-статистики"""

FINAL_STATS_AVAILABLE: bool = False
"""FLAG доступности C++ модуля финальной статистики"""

MATCH_NOTIFIER_AVAILABLE: bool = False
"""FLAG доступности C++ модуля уведомлений о совпадениях"""

CPP_AVAILABLE: bool = False
"""Общий флаг доступности C++ модулей"""

PLUGIN_BASE_VERSION: str = "2.0.0"
"""Версия модуля базового плагина"""

LIVE_STATS_VERSION: str = "2.0.0"
"""Версия модуля live-статистики"""

MATCH_NOTIFIER_VERSION: str = "2.0.0"
"""Версия модуля уведомлений о совпадениях"""

FINAL_STATS_VERSION: str = "2.0.0"
"""Версия модуля финальной статистики"""

# ============================================================================
# ПРОВЕРКА ДОСТУПНОСТИ C++ МОДУЛЕЙ (МЯГКАЯ)
# ============================================================================

def _check_cpp_modules() -> None:
    """
    Проверка доступности всех C++ модулей.
    
    Мягкая проверка: при отсутствии модулей устанавливает флаги в False
    и выводит предупреждения в лог, но не выбрасывает исключений.
    """
    global CPP_AVAILABLE, LOG_PARSER_AVAILABLE, METRICS_AVAILABLE
    global PLUGIN_BASE_AVAILABLE, LIVE_STATS_AVAILABLE, FINAL_STATS_AVAILABLE, MATCH_NOTIFIER_AVAILABLE
    
    required_modules = {
        "plugin_base_cpp": ("PLUGIN_BASE_AVAILABLE", "Базовый класс плагинов мониторинга"),
        "live_stats_plugin_cpp": ("LIVE_STATS_AVAILABLE", "Плагин live-статистики"),
        "match_notifier_plugin_cpp": ("MATCH_NOTIFIER_AVAILABLE", "Плагин уведомлений о совпадениях"),
        "final_stats_plugin_cpp": ("FINAL_STATS_AVAILABLE", "Плагин финальной статистики"),
        "log_parser_cpp": ("LOG_PARSER_AVAILABLE", "Парсер логов"),
        "metrics_cpp": ("METRICS_AVAILABLE", "Модуль метрик"),
    }
    
    available_count = 0
    
    _logger.info(f"[INIT][START] Проверка доступности C++ модулей...")
    
    for module_name, (flag_name, description) in required_modules.items():
        try:
            __import__(module_name)
            # Устанавливаем соответствующий флаг в True
            globals()[flag_name] = True
            available_count += 1
            _logger.info(f"[INIT][ConditionCheck] {module_name}: ДОСТУПЕН, {flag_name}=True [SUCCESS]")
        except (ImportError, ModuleNotFoundError) as e:
            _logger.warning(f"[INIT][ConditionCheck] {module_name}: НЕДОСТУПЕН, {flag_name}=False [WARNING]")
    
    # Устанавливаем общий флаг
    CPP_AVAILABLE = (available_count > 0)
    
    if available_count > 0:
        _logger.info(f"[INIT][SUCCESS] Доступно {available_count} из {len(required_modules)} C++ модулей [SUCCESS]")
    else:
        _logger.warning(f"[INIT][WARNING] Ни один C++ модуль недоступен. Будут использоваться Python fallback. [WARNING]")

# ============================================================================
# ИМПОРТ C++ МОДУЛЕЙ (УСЛОВНЫЙ)
# ============================================================================

def _import_cpp_modules() -> None:
    """
    Импорт доступных C++ модулей плагинов мониторинга.
    
    Импортирует только те модули, которые доступны (соответствующий флаг = True).
    """
    global plugin_base_cpp, live_stats_plugin_cpp, match_notifier_plugin_cpp
    global final_stats_plugin_cpp, log_parser_cpp, metrics_cpp
    
    # Импортируем доступные модули
    modules_to_import = [
        ("plugin_base_cpp", PLUGIN_BASE_AVAILABLE),
        ("live_stats_plugin_cpp", LIVE_STATS_AVAILABLE),
        ("match_notifier_plugin_cpp", MATCH_NOTIFIER_AVAILABLE),
        ("final_stats_plugin_cpp", FINAL_STATS_AVAILABLE),
        ("log_parser_cpp", LOG_PARSER_AVAILABLE),
        ("metrics_cpp", METRICS_AVAILABLE),
    ]
    
    _logger.info(f"[INIT][START] Импорт доступных C++ модулей...")
    
    for module_name, is_available in modules_to_import:
        if is_available:
            try:
                globals()[module_name] = __import__(module_name)
                _logger.info(f"[INIT][Import] {module_name} импортирован [SUCCESS]")
            except ImportError as e:
                _logger.warning(f"[INIT][Import] Ошибка импорта {module_name}: {e} [WARNING]")
        else:
            _logger.info(f"[INIT][Import] {module_name} пропущен (flag=False) [INFO]")
    
    _logger.info(f"[INIT][SUCCESS] Импорт C++ модулей завершён [SUCCESS]")

# ============================================================================
# ФУНКЦИИ ПОЛУЧЕНИЯ МОДУЛЕЙ
# ============================================================================

def get_log_parser_module():
    """Получить модуль log_parser_cpp, если доступен."""
    if LOG_PARSER_AVAILABLE:
        try:
            return __import__("log_parser_cpp")
        except ImportError:
            pass
    return None

def get_metrics_module():
    """Получить модуль metrics_cpp, если доступен."""
    if METRICS_AVAILABLE:
        try:
            return __import__("metrics_cpp")
        except ImportError:
            pass
    return None

def get_plugin_base_module():
    """Получить модуль plugin_base_cpp, если доступен."""
    if PLUGIN_BASE_AVAILABLE:
        try:
            return __import__("plugin_base_cpp")
        except ImportError:
            pass
    return None

def get_live_stats_module():
    """Получить модуль live_stats_plugin_cpp, если доступен."""
    if LIVE_STATS_AVAILABLE:
        try:
            return __import__("live_stats_plugin_cpp")
        except ImportError:
            pass
    return None

def get_final_stats_module():
    """Получить модуль final_stats_plugin_cpp, если доступен."""
    if FINAL_STATS_AVAILABLE:
        try:
            return __import__("final_stats_plugin_cpp")
        except ImportError:
            pass
    return None

def get_match_notifier_module():
    """Получить модуль match_notifier_plugin_cpp, если доступен."""
    if MATCH_NOTIFIER_AVAILABLE:
        try:
            return __import__("match_notifier_plugin_cpp")
        except ImportError:
            pass
    return None

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ ПРИ ИМПОРТЕ ПАКЕТА
# ============================================================================

# Выполняем мягкую проверку при импорте пакета
_check_cpp_modules()
_import_cpp_modules()

# ============================================================================
# ЭКСПОРТ КЛАССОВ ИЗ C++ МОДУЛЕЙ (УСЛОВНЫЙ)
# ============================================================================

# Импортируем классы из модулей для удобного доступа (с обработкой ошибок)
try:
    from plugin_base_cpp import BaseMonitorPlugin, PluginMetadata, MonitorAppProtocol
    _logger.info(f"[INIT][Import] Классы из plugin_base_cpp импортированы [SUCCESS]")
except (ImportError, NameError) as e:
    _logger.warning(f"[INIT][Import] Не удалось импортировать классы из plugin_base_cpp: {e} [WARNING]")
    # Определяем классы-заглушки для избежания ошибок при импорте
    class _DummyBaseMonitorPlugin:
        pass
    class _DummyPluginMetadata:
        pass
    class _DummyMonitorAppProtocol:
        pass
    BaseMonitorPlugin = _DummyBaseMonitorPlugin
    PluginMetadata = _DummyPluginMetadata
    MonitorAppProtocol = _DummyMonitorAppProtocol

try:
    from live_stats_plugin_cpp import LiveStatsPlugin, MetricSnapshot, Statistics, CurrentStats
    _logger.info(f"[INIT][Import] Классы из live_stats_plugin_cpp импортированы [SUCCESS]")
except (ImportError, NameError) as e:
    _logger.warning(f"[INIT][Import] Не удалось импортировать классы из live_stats_plugin_cpp: {e} [WARNING]")
    class _DummyLiveStatsPlugin:
        pass
    class _DummyMetricSnapshot:
        pass
    class _DummyStatistics:
        pass
    class _DummyCurrentStats:
        pass
    LiveStatsPlugin = _DummyLiveStatsPlugin
    MetricSnapshot = _DummyMetricSnapshot
    Statistics = _DummyStatistics
    CurrentStats = _DummyCurrentStats

try:
    from match_notifier_plugin_cpp import MatchNotifierPlugin, MatchEntry, NotificationSettings, MatchSeverity, NotificationType
    _logger.info(f"[INIT][Import] Классы из match_notifier_plugin_cpp импортированы [SUCCESS]")
except (ImportError, NameError) as e:
    _logger.warning(f"[INIT][Import] Не удалось импортировать классы из match_notifier_plugin_cpp: {e} [WARNING]")
    class _DummyMatchNotifierPlugin:
        pass
    class _DummyMatchEntry:
        pass
    class _DummyNotificationSettings:
        pass
    class _DummyMatchSeverity:
        pass
    class _DummyNotificationType:
        pass
    MatchNotifierPlugin = _DummyMatchNotifierPlugin
    MatchEntry = _DummyMatchEntry
    NotificationSettings = _DummyNotificationSettings
    MatchSeverity = _DummyMatchSeverity
    NotificationType = _DummyNotificationType

try:
    from final_stats_plugin_cpp import FinalStatsPlugin, FinalStatistics, SessionEntry, PerformanceMetrics, ExportFormat
    _logger.info(f"[INIT][Import] Классы из final_stats_plugin_cpp импортированы [SUCCESS]")
except (ImportError, NameError) as e:
    _logger.warning(f"[INIT][Import] Не удалось импортировать классы из final_stats_plugin_cpp: {e} [WARNING]")
    class _DummyFinalStatsPlugin:
        pass
    class _DummyFinalStatistics:
        pass
    class _DummySessionEntry:
        pass
    class _DummyPerformanceMetrics:
        pass
    class _DummyExportFormat:
        pass
    FinalStatsPlugin = _DummyFinalStatsPlugin
    FinalStatistics = _DummyFinalStatistics
    SessionEntry = _DummySessionEntry
    PerformanceMetrics = _DummyPerformanceMetrics
    ExportFormat = _DummyExportFormat

try:
    from log_parser_cpp import LogParser, LogEntry, ParserConfig
    _logger.info(f"[INIT][Import] Классы из log_parser_cpp импортированы [SUCCESS]")
except (ImportError, NameError) as e:
    _logger.warning(f"[INIT][Import] Не удалось импортировать классы из log_parser_cpp: {e} [WARNING]")
    class _DummyLogParser:
        pass
    class _DummyLogEntry:
        pass
    class _DummyParserConfig:
        pass
    LogParser = _DummyLogParser
    LogEntry = _DummyLogEntry
    ParserConfig = _DummyParserConfig

try:
    from metrics_cpp import MetricsStore, MetricPoint, AggregationType
    _logger.info(f"[INIT][Import] Классы из metrics_cpp импортированы [SUCCESS]")
except (ImportError, NameError) as e:
    _logger.warning(f"[INIT][Import] Не удалось импортировать классы из metrics_cpp: {e} [WARNING]")
    class _DummyMetricsStore:
        pass
    class _DummyMetricPoint:
        pass
    class _DummyAggregationType:
        pass
    MetricsStore = _DummyMetricsStore
    MetricPoint = _DummyMetricPoint
    AggregationType = _DummyAggregationType

# ============================================================================
# ЭКСПОРТ
# ============================================================================

__all__ = [
    # Версия
    "VERSION",
    "CPP_AVAILABLE",
    
    # Флаги доступности модулей
    "LOG_PARSER_AVAILABLE",
    "METRICS_AVAILABLE",
    "PLUGIN_BASE_AVAILABLE",
    "LIVE_STATS_AVAILABLE",
    "FINAL_STATS_AVAILABLE",
    "MATCH_NOTIFIER_AVAILABLE",
    
    # Версии модулей
    "PLUGIN_BASE_VERSION",
    "LIVE_STATS_VERSION",
    "MATCH_NOTIFIER_VERSION",
    "FINAL_STATS_VERSION",
    
    # Модули (для продвинутого использования)
    "plugin_base_cpp",
    "live_stats_plugin_cpp",
    "match_notifier_plugin_cpp",
    "final_stats_plugin_cpp",
    "log_parser_cpp",
    "metrics_cpp",
    
    # Функции получения модулей
    "get_log_parser_module",
    "get_metrics_module",
    "get_plugin_base_module",
    "get_live_stats_module",
    "get_final_stats_module",
    "get_match_notifier_module",
    
    # Классы из plugin_base_cpp
    "BaseMonitorPlugin",
    "PluginMetadata",
    "MonitorAppProtocol",
    
    # Классы из live_stats_plugin_cpp
    "LiveStatsPlugin",
    "MetricSnapshot",
    "Statistics",
    "CurrentStats",
    
    # Классы из match_notifier_plugin_cpp
    "MatchNotifierPlugin",
    "MatchEntry",
    "NotificationSettings",
    "MatchSeverity",
    "NotificationType",
    
    # Классы из final_stats_plugin_cpp
    "FinalStatsPlugin",
    "FinalStatistics",
    "SessionEntry",
    "PerformanceMetrics",
    "ExportFormat",
    
    # Классы из log_parser_cpp
    "LogParser",
    "LogEntry",
    "ParserConfig",
    
    # Классы из metrics_cpp
    "MetricsStore",
    "MetricPoint",
    "AggregationType",
]

# ============================================================================
# ИНФОРМАЦИЯ ПРИ УСПЕШНОЙ ИНИЦИАЛИЗАЦИИ
# ============================================================================

_logger.info(f"[INIT][SUCCESS] Модуль src.monitor._cpp версии {VERSION} успешно инициализирован")
_logger.info(f"[INIT][INFO] Все C++ модули плагинов мониторинга загружены")
