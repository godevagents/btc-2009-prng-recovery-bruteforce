# FILE: src/monitor/_cpp/final_stats.py
# VERSION: 2.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Python-обёртка для C++ модуля плагина финальной статистики мониторинга. Обеспечивает итоговую статистику и экспорт результатов. Только C++ реализация - Python fallback НЕПРИЕМЛЕМ.
# SCOPE: Плагин финальной статистики, итоговые метрики, записи сессий, производительность, экспорт
# INPUT: Нет (модуль предоставляет классы)
# OUTPUT: Классы FinalStatsPlugin, FinalStatistics, SessionEntry, PerformanceMetrics, ExportFormat
# KEYWORDS: [DOMAIN(9): FinalStatistics; DOMAIN(8): CppBinding; CONCEPT(9): NoFallback; TECH(7): PyBind11; TECH(6): Export]
# LINKS: [IMPORTS(9): final_stats_plugin_cpp; EXPORTS(9): FinalStatsPlugin; EXPORTS(8): FinalStatistics; EXPORTS(8): SessionEntry; EXPORTS(8): PerformanceMetrics; EXPORTS(8): ExportFormat]
# LINKS_TO_SPECIFICATION: [Спецификация final_stats из docs/cpp_modules/final_stats_plugin_draft_code_plan_v2.md]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 10 [Плагин финальной статистики мониторинга] => FinalStatsPlugin
# CLASS 8 [Итоговая статистика сессии] => FinalStatistics
# CLASS 7 [Запись о сессии генерации] => SessionEntry
# CLASS 6 [Метрики производительности] => PerformanceMetrics
# CLASS 5 [Формат экспорта данных] => ExportFormat
# END_MODULE_MAP
# START_USE_CASES:
# - [FinalStatsPlugin]: System (StatisticsExport) -> GenerateFinalStats -> StatsExported
# - [FinalStatistics]: Analysis (Aggregation) -> AggregateResults -> FinalStatsAvailable
# - [SessionEntry]: Plugin (SessionTracking) -> RecordSession -> SessionStored
# - [PerformanceMetrics]: Analysis (Measurement) -> MeasurePerformance -> MetricsAvailable
# - [ExportFormat]: User (Export) -> ChooseFormat -> DataFormatted
# END_USE_CASES
"""
Модуль final_stats.py — Python-обёртка для C++ модуля плагина финальной статистики мониторинга.

ВНИМАНИЕ: Этот модуль требует наличия скомпилированного C++ модуля final_stats_plugin_cpp.
Python fallback НЕПРЕДУСМОТРЕН - только C++ реализация.

Экспортирует:
    - FinalStatsPlugin: Плагин для сбора и экспорта финальной статистики
    - FinalStatistics: Класс для хранения итоговой статистики сессии
    - SessionEntry: Класс для записи о сессии генерации
    - PerformanceMetrics: Класс для метрик производительности
    - ExportFormat: Перечисление форматов экспорта данных

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
_logger = logging.getLogger("src.monitor._cpp.final_stats")
if not _logger.handlers:
    _file_handler = _setup_file_logging()
    _logger.addHandler(_file_handler)
    _logger.setLevel(logging.INFO)

# ============================================================================
# ИМПОРТ C++ МОДУЛЯ
# ============================================================================

# START_FUNCTION_IMPORT_CPP_MODULE
# START_CONTRACT:
# PURPOSE: Импорт C++ модуля final_stats_plugin_cpp с жёсткой проверкой доступности
# INPUTS: Нет
# OUTPUTS: Импортированный модуль
# SIDE_EFFECTS: Вызывает ImportError при отсутствии C++ модуля
# KEYWORDS: [PATTERN(9): HardImport; DOMAIN(9): ModuleLoading; TECH(6): Import]
# END_CONTRACT

def _import_cpp_module():
    """
    Импорт C++ модуля final_stats_plugin_cpp.
    
    ВНИМАНИЕ: Это жёсткий импорт. При отсутствии C++ модуля
    выбрасывается ImportError с инструкцией по сборке.
    
    Returns:
        Импортированный C++ модуль final_stats_plugin_cpp
        
    Raises:
        ImportError: Если C++ модуль недоступен
    """
    _logger.info(f"[IMPORT][START] Попытка импорта final_stats_plugin_cpp...")
    
    try:
        import final_stats_plugin_cpp
        _logger.info(f"[IMPORT][SUCCESS] C++ модуль final_stats_plugin_cpp успешно импортирован [SUCCESS]")
        return final_stats_plugin_cpp
    except (ImportError, ModuleNotFoundError) as e:
        _logger.error(f"[IMPORT][CRITICAL] C++ модуль final_stats_plugin_cpp недоступен: {e} [FAIL]")
        
        build_instructions = f"""
================================================================================
ОШИБКА: C++ модуль final_stats_plugin_cpp недоступен
================================================================================

Требуемый модуль: final_stats_plugin_cpp
Описание: Плагин финальной статистики мониторинга

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

Документация: docs/cpp_modules/final_stats_plugin_draft_code_plan_v2.md

================================================================================
"""
        _logger.error(f"[IMPORT][CRITICAL]{build_instructions}")
        raise ImportError(
            f"C++ модуль final_stats_plugin_cpp недоступен. "
            f"Пожалуйста, соберите C++ модуль следуя инструкциям в docs/cpp_modules/final_stats_plugin_draft_code_plan_v2.md"
        )

# END_FUNCTION_IMPORT_CPP_MODULE

# ============================================================================
# ИМПОРТ КЛАССОВ ИЗ C++ МОДУЛЯ
# ============================================================================

# Получаем C++ модуль
_cpp_module = _import_cpp_module()

# Импортируем классы из C++ модуля
try:
    FinalStatsPlugin = _cpp_module.FinalStatsPlugin
    _logger.info(f"[IMPORT][SUCCESS] Класс FinalStatsPlugin импортирован из C++ [SUCCESS]")
except AttributeError as e:
    _logger.error(f"[IMPORT][CRITICAL] Класс FinalStatsPlugin не найден в C++ модуле: {e} [FAIL]")
    raise ImportError(f"C++ модуль final_stats_plugin_cpp не содержит класса FinalStatsPlugin: {e}")

try:
    FinalStatistics = _cpp_module.FinalStatistics
    _logger.info(f"[IMPORT][SUCCESS] Класс FinalStatistics импортирован из C++ [SUCCESS]")
except AttributeError as e:
    _logger.error(f"[IMPORT][CRITICAL] Класс FinalStatistics не найден в C++ модуле: {e} [FAIL]")
    raise ImportError(f"C++ модуль final_stats_plugin_cpp не содержит класса FinalStatistics: {e}")

try:
    SessionEntry = _cpp_module.SessionEntry
    _logger.info(f"[IMPORT][SUCCESS] Класс SessionEntry импортирован из C++ [SUCCESS]")
except AttributeError as e:
    _logger.error(f"[IMPORT][CRITICAL] Класс SessionEntry не найден в C++ модуле: {e} [FAIL]")
    raise ImportError(f"C++ модуль final_stats_plugin_cpp не содержит класса SessionEntry: {e}")

try:
    PerformanceMetrics = _cpp_module.PerformanceMetrics
    _logger.info(f"[IMPORT][SUCCESS] Класс PerformanceMetrics импортирован из C++ [SUCCESS]")
except AttributeError as e:
    _logger.error(f"[IMPORT][CRITICAL] Класс PerformanceMetrics не найден в C++ модуле: {e} [FAIL]")
    raise ImportError(f"C++ модуль final_stats_plugin_cpp не содержит класса PerformanceMetrics: {e}")

try:
    ExportFormat = _cpp_module.ExportFormat
    _logger.info(f"[IMPORT][SUCCESS] Класс ExportFormat импортирован из C++ [SUCCESS]")
except AttributeError as e:
    _logger.error(f"[IMPORT][CRITICAL] Класс ExportFormat не найден в C++ модуле: {e} [FAIL]")
    raise ImportError(f"C++ модуль final_stats_plugin_cpp не содержит класса ExportFormat: {e}")

# ============================================================================
# ЭКСПОРТ
# ============================================================================

__all__ = [
    # Классы из C++ модуля
    "FinalStatsPlugin",
    "FinalStatistics",
    "SessionEntry",
    "PerformanceMetrics",
    "ExportFormat",
]

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ ПРИ ИМПОРТЕ
# ============================================================================

_logger.info(f"[INIT][SUCCESS] Модуль src.monitor._cpp.final_stats успешно инициализирован, используется C++ реализация [SUCCESS]")
