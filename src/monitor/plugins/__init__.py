# FILE: src/monitor/plugins/__init__.py
# VERSION: 1.1.0
# START_MODULE_CONTRACT:
# PURPOSE: Модуль плагинов мониторинга. Содержит базовый класс и специализированные плагины для разных этапов мониторинга генерации кошельков Bitcoin. Поддерживает C++ обёртки с fallback на Python реализации.
# SCOPE: Экспорт плагинов, управление жизненным циклом мониторинга
# INPUT: Нет (модуль предоставляет классы для импорта)
# OUTPUT: Классы плагинов: BaseMonitorPlugin, ListSelectorPlugin, LiveStatsPlugin, MatchNotifierPlugin, FinalStatsPlugin
# KEYWORDS: [DOMAIN(9): Monitoring; DOMAIN(8): Plugins; CONCEPT(7): Extensibility; TECH(5): Gradio; CONCEPT(6): CppWrapper]
# LINKS: [USES_API(8): src.monitor.plugins.base; USES_API(7): src.monitor.plugins.list_selector; USES_API(7): src.monitor.plugins.live_stats; USES_API(7): src.monitor.plugins.match_notifier; USES_API(7): src.monitor.plugins.final_stats; USES_API(6): src.monitor._cpp]
# LINKS_TO_SPECIFICATION: [Спецификация плагинов мониторинга из dev_plan_monitor_init.md]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CONST 10 [Модуль плагинов мониторинга] => PLUGINS_NAMESPACE
# FUNC 8 [Получить модуль live-статистики] => get_live_stats_module
# FUNC 8 [Получить модуль финальной статистики] => get_final_stats_module
# FUNC 8 [Получить модуль уведомлений о совпадениях] => get_match_notifier_module
# END_MODULE_MAP
# START_USE_CASES:
# - [import]: Developer (Development) -> ImportPlugins -> PluginsAvailable
# - [BaseMonitorPlugin]: System (PluginSystem) -> ProvideBaseInterface -> PluginArchitectureDefined
# - [LiveStatsPlugin]: Monitor (LiveMonitoring) -> TrackLiveStats -> LiveStatsDisplayed
# - [FinalStatsPlugin]: Monitor (FinalResults) -> DisplayFinalStats -> FinalStatsReady
# - [MatchNotifierPlugin]: System (MatchFound) -> NotifyAboutMatch -> UserAlerted
# END_USE_CASES
"""
Модуль плагинов мониторинга.
Содержит базовый класс и специализированные плагины для разных этапов мониторинга.
"""

import logging
import os
from pathlib import Path

# Настройка логирования с FileHandler для app.log
_logger = logging.getLogger(__name__)
if not _logger.handlers:
    # Используем абсолютный путь от корня проекта
    _project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _log_dir = os.path.join(_project_root)
    # Создаём директорию для логов если она не существует
    os.makedirs(_log_dir, exist_ok=True)
    _log_file = os.path.join(_log_dir, "app.log")
    _file_handler = logging.FileHandler(_log_file, encoding="utf-8")
    _file_handler.setLevel(logging.DEBUG)
    _formatter = logging.Formatter(
        "[%(asctime)s][%(name)s][%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    _file_handler.setFormatter(_formatter)
    _logger.addHandler(_file_handler)
    _logger.setLevel(logging.DEBUG)

logger = _logger

# ============================================================================
# ИМПОРТЫ ИЗ C++ МОДУЛЯ
# ============================================================================
# Импортируем флаги доступности и функции получения модулей из _cpp
try:
    from src.monitor._cpp import (
        LIVE_STATS_AVAILABLE,
        FINAL_STATS_AVAILABLE,
        MATCH_NOTIFIER_AVAILABLE,
        get_live_stats_module,
        get_final_stats_module,
        get_match_notifier_module,
    )
    _CPP_IMPORT_SUCCESS = True
except ImportError as e:
    logger.warning(f"[ModuleInit][plugins/__init__.py] Ошибка импорта из src.monitor._cpp: {e} [FAIL]")
    LIVE_STATS_AVAILABLE = False
    FINAL_STATS_AVAILABLE = False
    MATCH_NOTIFIER_AVAILABLE = False
    get_live_stats_module = None
    get_final_stats_module = None
    get_match_notifier_module = None
    _CPP_IMPORT_SUCCESS = False

# ============================================================================
# ИМПОРТЫ ПЛАГИНОВ С FALLBACK
# ============================================================================

# Попытка импорта C++ обёрток для плагинов, с fallback на Python реализацию
# LiveStatsPlugin
logger.debug(f"[ModuleInit][plugins/__init__.py] Проверка LiveStatsPlugin: LIVE_STATS_AVAILABLE={LIVE_STATS_AVAILABLE} [INFO]")
try:
    from src.monitor._cpp.live_stats_wrapper import LiveStatsPlugin
    _LIVE_STATS_CPP = True
    logger.info("[ModuleInit][plugins/__init__.py] Используется C++ обёртка для LiveStatsPlugin [SUCCESS]")
except ImportError as e:
    raise ImportError(f"[ModuleInit][plugins/__init__.py] Не удалось импортировать C++ LiveStatsPlugin: {e}. Python fallback более не поддерживается.")

# FinalStatsPlugin
logger.debug(f"[ModuleInit][plugins/__init__.py] Проверка FinalStatsPlugin: FINAL_STATS_AVAILABLE={FINAL_STATS_AVAILABLE} [INFO]")
try:
    from src.monitor._cpp.final_stats_wrapper import FinalStatsPlugin
    _FINAL_STATS_CPP = True
    logger.info("[ModuleInit][plugins/__init__.py] Используется C++ обёртка для FinalStatsPlugin [SUCCESS]")
except ImportError as e:
    raise ImportError(f"[ModuleInit][plugins/__init__.py] Не удалось импортировать C++ FinalStatsPlugin: {e}. Python fallback более не поддерживается.")

# MatchNotifierPlugin
logger.debug(f"[ModuleInit][plugins/__init__.py] Проверка MatchNotifierPlugin: MATCH_NOTIFIER_AVAILABLE={MATCH_NOTIFIER_AVAILABLE} [INFO]")
try:
    from src.monitor._cpp.match_notifier_wrapper import MatchNotifierPlugin
    _MATCH_NOTIFIER_CPP = True
    logger.info("[ModuleInit][plugins/__init__.py] Используется C++ обёртка для MatchNotifierPlugin [SUCCESS]")
except ImportError as e:
    raise ImportError(f"[ModuleInit][plugins/__init__.py] Не удалось импортировать C++ MatchNotifierPlugin: {e}. Python fallback более не поддерживается.")

# Python-only плагины остаются без изменений
# Пытаемся импортировать BaseMonitorPlugin из C++ обёртки
from src.monitor._cpp.plugin_base_wrapper import BaseMonitorPlugin
logger.info("[ModuleInit][plugins/__init__.py] BaseMonitorPlugin: используется C++ обёртка [SUCCESS]")

from src.monitor.plugins.list_selector import ListSelectorPlugin

# ============================================================================
# СЛУЖЕБНЫЕ ПЕРЕМЕННЫЕ
# ============================================================================

# Определение типа реализаций плагинов (C++ или Python)
__live_stats_cpp_version__ = _LIVE_STATS_CPP
__final_stats_cpp_version__ = _FINAL_STATS_CPP
__match_notifier_cpp_version__ = _MATCH_NOTIFIER_CPP

# ============================================================================
# ЭКСПОРТ ПЛАГИНОВ
# ============================================================================

__all__ = [
    # Классы плагинов
    "BaseMonitorPlugin",
    "ListSelectorPlugin",
    "LiveStatsPlugin",
    "MatchNotifierPlugin",
    "FinalStatsPlugin",
    # Флаги доступности C++ модулей
    "LIVE_STATS_AVAILABLE",
    "FINAL_STATS_AVAILABLE",
    "MATCH_NOTIFIER_AVAILABLE",
    # Функции получения модулей
    "get_live_stats_module",
    "get_final_stats_module",
    "get_match_notifier_module",
    # Служебные переменные
    "__live_stats_cpp_version__",
    "__final_stats_cpp_version__",
    "__match_notifier_cpp_version__",
]
