# FILE: src/monitor/_cpp/live_stats.py
# VERSION: 2.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Python-обёртка для C++ модуля плагина live-статистики мониторинга. Обеспечивает real-time отображение метрик генерации. Только C++ реализация - Python fallback НЕПРИЕМЛЕМ.
# SCOPE: Плагин live-статистики, метрики, snapshot-данные, текущая статистика
# INPUT: Нет (модуль предоставляет классы)
# OUTPUT: Классы LiveStatsPlugin, MetricSnapshot, Statistics, CurrentStats
# KEYWORDS: [DOMAIN(9): LiveStatistics; DOMAIN(8): CppBinding; CONCEPT(9): NoFallback; TECH(7): PyBind11; TECH(6): RealTime]
# LINKS: [IMPORTS(9): live_stats_plugin_cpp; EXPORTS(9): LiveStatsPlugin; EXPORTS(8): MetricSnapshot; EXPORTS(8): Statistics; EXPORTS(8): CurrentStats]
# LINKS_TO_SPECIFICATION: [Спецификация live_stats из docs/cpp_modules/live_stats_plugin_draft_code_plan_v2.md]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 10 [Плагин live-статистики мониторинга] => LiveStatsPlugin
# CLASS 8 [Снимок метрик за период] => MetricSnapshot
# CLASS 7 [Статистические данные] => Statistics
# CLASS 6 [Текущая статистика] => CurrentStats
# END_MODULE_MAP
# START_USE_CASES:
# - [LiveStatsPlugin]: System (LiveMonitoring) -> TrackRealtimeMetrics -> LiveStatsDisplayed
# - [MetricSnapshot]: Plugin (DataCapture) -> CaptureMetrics -> SnapshotAvailable
# - [Statistics]: Analysis (Computation) -> CalculateStats -> StatsAvailable
# - [CurrentStats]: Display (RealTime) -> ShowCurrentMetrics -> CurrentStateVisible
# END_USE_CASES
"""
Модуль live_stats.py — Python-обёртка для C++ модуля плагина live-статистики мониторинга.

ВНИМАНИЕ: Этот модуль требует наличия скомпилированного C++ модуля live_stats_plugin_cpp.
Python fallback НЕПРЕДУСМОТРЕН - только C++ реализация.

Экспортирует:
    - LiveStatsPlugin: Плагин для отображения live-статистики генерации
    - MetricSnapshot: Класс для хранения снимка метрик за период
    - Statistics: Класс для статистических вычислений
    - CurrentStats: Класс для текущей статистики в реальном времени

При отсутствии C++ модуля выбрасывается ImportError с инструкцией по сборке.
"""

import logging
from pathlib import Path

# ============================================================================
# КОНФИГУРАЦИЯ ЛОГИРОВАНИЯ
# ============================================================================

def _setup_file_logging() -> logging.FileHandler:
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

# Настройка логирования для модуля
_logger = logging.getLogger("src.monitor._cpp.live_stats")
if not _logger.handlers:
    _file_handler = _setup_file_logging()
    _logger.addHandler(_file_handler)
    _logger.setLevel(logging.INFO)

# ============================================================================
# ИМПОРТ C++ МОДУЛЯ
# ============================================================================

# START_FUNCTION_IMPORT_CPP_MODULE
# START_CONTRACT:
# PURPOSE: Импорт C++ модуля live_stats_plugin_cpp с жёсткой проверкой доступности
# INPUTS: Нет
# OUTPUTS: Импортированный модуль
# SIDE_EFFECTS: Вызывает ImportError при отсутствии C++ модуля
# KEYWORDS: [PATTERN(9): HardImport; DOMAIN(9): ModuleLoading; TECH(6): Import]
# END_CONTRACT

def _import_cpp_module():
    """
    Импорт C++ модуля live_stats_plugin_cpp.
    
    ВНИМАНИЕ: Это жёсткий импорт. При отсутствии C++ модуля
    выбрасывается ImportError с инструкцией по сборке.
    
    Returns:
        Импортированный C++ модуль live_stats_plugin_cpp
        
    Raises:
        ImportError: Если C++ модуль недоступен
    """
    _logger.info(f"[IMPORT][START] Попытка импорта live_stats_plugin_cpp...")
    
    try:
        import live_stats_plugin_cpp
        _logger.info(f"[IMPORT][SUCCESS] C++ модуль live_stats_plugin_cpp успешно импортирован [SUCCESS]")
        return live_stats_plugin_cpp
    except (ImportError, ModuleNotFoundError) as e:
        _logger.error(f"[IMPORT][CRITICAL] C++ модуль live_stats_plugin_cpp недоступен: {e} [FAIL]")
        
        build_instructions = f"""
================================================================================
ОШИБКА: C++ модуль live_stats_plugin_cpp недоступен
================================================================================

Требуемый модуль: live_stats_plugin_cpp
Описание: Плагин live-статистики мониторинга

ИНСТРУКЦИЯ ПО СБОРКЕ:
----------------------
1. Перейдите в директорию src/monitor/_cpp
2. Выполните сборку C++ модулей:
   cd src/monitor/_cpp
   ./build.sh
   
   Или используя CMake:
   cd src/monitor/_cpp
   mkdir -p build && cd build
   cmake ..
   make

3. После успешной сборки перезапустите приложение

Документация: docs/cpp_modules/live_stats_plugin_draft_code_plan_v2.md

================================================================================
"""
        _logger.error(f"[IMPORT][CRITICAL]{build_instructions}")
        raise ImportError(
            f"C++ модуль live_stats_plugin_cpp недоступен. "
            f"Пожалуйста, соберите C++ модуль следуя инструкциям в docs/cpp_modules/live_stats_plugin_draft_code_plan_v2.md"
        )

# END_FUNCTION_IMPORT_CPP_MODULE

# ============================================================================
# ИМПОРТ КЛАССОВ ИЗ C++ МОДУЛЯ
# ============================================================================

# Получаем C++ модуль
_cpp_module = _import_cpp_module()

# Импортируем классы из C++ модуля
try:
    LiveStatsPlugin = _cpp_module.LiveStatsPlugin
    _logger.info(f"[IMPORT][SUCCESS] Класс LiveStatsPlugin импортирован из C++ [SUCCESS]")
except AttributeError as e:
    _logger.error(f"[IMPORT][CRITICAL] Класс LiveStatsPlugin не найден в C++ модуле: {e} [FAIL]")
    raise ImportError(f"C++ модуль live_stats_plugin_cpp не содержит класса LiveStatsPlugin: {e}")

try:
    MetricSnapshot = _cpp_module.MetricSnapshot
    _logger.info(f"[IMPORT][SUCCESS] Класс MetricSnapshot импортирован из C++ [SUCCESS]")
except AttributeError as e:
    _logger.error(f"[IMPORT][CRITICAL] Класс MetricSnapshot не найден в C++ модуле: {e} [FAIL]")
    raise ImportError(f"C++ модуль live_stats_plugin_cpp не содержит класса MetricSnapshot: {e}")

try:
    Statistics = _cpp_module.Statistics
    _logger.info(f"[IMPORT][SUCCESS] Класс Statistics импортирован из C++ [SUCCESS]")
except AttributeError as e:
    _logger.error(f"[IMPORT][CRITICAL] Класс Statistics не найден в C++ модуле: {e} [FAIL]")
    raise ImportError(f"C++ модуль live_stats_plugin_cpp не содержит класса Statistics: {e}")

try:
    CurrentStats = _cpp_module.CurrentStats
    _logger.info(f"[IMPORT][SUCCESS] Класс CurrentStats импортирован из C++ [SUCCESS]")
except AttributeError as e:
    _logger.error(f"[IMPORT][CRITICAL] Класс CurrentStats не найден в C++ модуле: {e} [FAIL]")
    raise ImportError(f"C++ модуль live_stats_plugin_cpp не содержит класса CurrentStats: {e}")

# ============================================================================
# ЭКСПОРТ
# ============================================================================

__all__ = [
    # Классы из C++ модуля
    "LiveStatsPlugin",
    "MetricSnapshot",
    "Statistics",
    "CurrentStats",
]

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ ПРИ ИМПОРТЕ
# ============================================================================

_logger.info(f"[INIT][SUCCESS] Модуль src.monitor._cpp.live_stats успешно инициализирован, используется C++ реализация [SUCCESS]")
