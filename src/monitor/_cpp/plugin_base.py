# FILE: src/monitor/_cpp/plugin_base.py
# VERSION: 2.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Python-обёртка для C++ модуля базового класса плагинов мониторинга. Обеспечивает единый интерфейс для создания плагинов. Только C++ реализация - Python fallback НЕПРИЕМЛЕМ.
# SCOPE: Абстрактный базовый класс, система метаданных плагинов, протокол приложения мониторинга
# INPUT: Нет (модуль предоставляет классы)
# OUTPUT: Классы BaseMonitorPlugin, PluginMetadata, MonitorAppProtocol
# KEYWORDS: [DOMAIN(9): PluginSystem; DOMAIN(8): CppBinding; CONCEPT(9): NoFallback; TECH(7): PyBind11]
# LINKS: [IMPORTS(9): plugin_base_cpp; EXPORTS(9): BaseMonitorPlugin; EXPORTS(8): PluginMetadata; EXPORTS(8): MonitorAppProtocol]
# LINKS_TO_SPECIFICATION: [Спецификация плагинов мониторинга из docs/cpp_modules/plugin_base_draft_code_plan_v2.md]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 10 [Базовый класс для всех плагинов мониторинга] => BaseMonitorPlugin
# CLASS 8 [Метаданные плагина] => PluginMetadata
# CLASS 7 [Протокол приложения мониторинга] => MonitorAppProtocol
# END_MODULE_MAP
# START_USE_CASES:
# - [BaseMonitorPlugin]: System (PluginLifecycle) -> ProvideBaseInterface -> PluginArchitectureDefined
# - [PluginMetadata]: Plugin (Registration) -> ProvideMetadata -> PluginInfoAvailable
# - [MonitorAppProtocol]: App (Communication) -> DefineProtocol -> InterProcessCommunicationReady
# END_USE_CASES
"""
Модуль plugin_base.py — Python-обёртка для C++ модуля базового класса плагинов мониторинга.

ВНИМАНИЕ: Этот модуль требует наличия скомпилированного C++ модуля plugin_base_cpp.
Python fallback НЕПРЕДУСМОТРЕН - только C++ реализация.

Экспортирует:
    - BaseMonitorPlugin: Базовый класс для всех плагинов мониторинга
    - PluginMetadata: Класс для хранения метаданных плагина
    - MonitorAppProtocol: Класс протокола приложения мониторинга

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
_logger = logging.getLogger("src.monitor._cpp.plugin_base")
if not _logger.handlers:
    _file_handler = _setup_file_logging()
    _logger.addHandler(_file_handler)
    _logger.setLevel(logging.INFO)

# ============================================================================
# ИМПОРТ C++ МОДУЛЯ
# ============================================================================

# START_FUNCTION_IMPORT_CPP_MODULE
# START_CONTRACT:
# PURPOSE: Импорт C++ модуля plugin_base_cpp с жёсткой проверкой доступности
# INPUTS: Нет
# OUTPUTS: Импортированный модуль
# SIDE_EFFECTS: Вызывает ImportError при отсутствии C++ модуля
# KEYWORDS: [PATTERN(9): HardImport; DOMAIN(9): ModuleLoading; TECH(6): Import]
# END_CONTRACT

def _import_cpp_module():
    """
    Импорт C++ модуля plugin_base_cpp.
    
    ВНИМАНИЕ: Это жёсткий импорт. При отсутствии C++ модуля
    выбрасывается ImportError с инструкцией по сборке.
    
    Returns:
        Импортированный C++ модуль plugin_base_cpp
        
    Raises:
        ImportError: Если C++ модуль недоступен
    """
    _logger.info(f"[IMPORT][START] Попытка импорта plugin_base_cpp...")
    
    try:
        import plugin_base_cpp
        _logger.info(f"[IMPORT][SUCCESS] C++ модуль plugin_base_cpp успешно импортирован [SUCCESS]")
        return plugin_base_cpp
    except (ImportError, ModuleNotFoundError) as e:
        _logger.error(f"[IMPORT][CRITICAL] C++ модуль plugin_base_cpp недоступен: {e} [FAIL]")
        
        build_instructions = f"""
================================================================================
ОШИБКА: C++ модуль plugin_base_cpp недоступен
================================================================================

Требуемый модуль: plugin_base_cpp
Описание: Базовый класс плагинов мониторинга

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

Документация: docs/cpp_modules/plugin_base_draft_code_plan_v2.md

================================================================================
"""
        _logger.error(f"[IMPORT][CRITICAL]{build_instructions}")
        raise ImportError(
            f"C++ модуль plugin_base_cpp недоступен. "
            f"Пожалуйста, соберите C++ модуль следуя инструкциям в docs/cpp_modules/plugin_base_draft_code_plan_v2.md"
        )

# END_FUNCTION_IMPORT_CPP_MODULE

# ============================================================================
# ИМПОРТ КЛАССОВ ИЗ C++ МОДУЛЯ
# ============================================================================

# Получаем C++ модуль
_cpp_module = _import_cpp_module()

# Импортируем классы из C++ модуля
try:
    BaseMonitorPlugin = _cpp_module.BaseMonitorPlugin
    _logger.info(f"[IMPORT][SUCCESS] Класс BaseMonitorPlugin импортирован из C++ [SUCCESS]")
except AttributeError as e:
    _logger.error(f"[IMPORT][CRITICAL] Класс BaseMonitorPlugin не найден в C++ модуле: {e} [FAIL]")
    raise ImportError(f"C++ модуль plugin_base_cpp не содержит класса BaseMonitorPlugin: {e}")

try:
    PluginMetadata = _cpp_module.PluginMetadata
    _logger.info(f"[IMPORT][SUCCESS] Класс PluginMetadata импортирован из C++ [SUCCESS]")
except AttributeError as e:
    _logger.error(f"[IMPORT][CRITICAL] Класс PluginMetadata не найден в C++ модуле: {e} [FAIL]")
    raise ImportError(f"C++ модуль plugin_base_cpp не содержит класса PluginMetadata: {e}")

try:
    MonitorAppProtocol = _cpp_module.MonitorAppProtocol
    _logger.info(f"[IMPORT][SUCCESS] Класс MonitorAppProtocol импортирован из C++ [SUCCESS]")
except AttributeError as e:
    _logger.warning(f"[IMPORT][WARNING] Класс MonitorAppProtocol не найден в C++ модуле: {e} [WARNING]")
    # MonitorAppProtocol может быть опциональным
    MonitorAppProtocol = None

# ============================================================================
# ЭКСПОРТ
# ============================================================================

__all__ = [
    # Классы из C++ модуля
    "BaseMonitorPlugin",
    "PluginMetadata",
    "MonitorAppProtocol",
]

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ ПРИ ИМПОРТЕ
# ============================================================================

_logger.info(f"[INIT][SUCCESS] Модуль src.monitor._cpp.plugin_base успешно инициализирован, используется C++ реализация [SUCCESS]")
