# FILE: src/monitor/_cpp/match_notifier.py
# VERSION: 2.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Python-обёртка для C++ модуля плагина уведомлений о совпадениях мониторинга. Обеспечивает оповещение при обнаружении совпадений адресов. Только C++ реализация - Python fallback НЕПРИЕМЛЕМ.
# SCOPE: Плагин уведомлений, совпадения, настройки уведомлений, типы и уровни важности
# INPUT: Нет (модуль предоставляет классы)
# OUTPUT: Классы MatchNotifierPlugin, MatchEntry, NotificationSettings, MatchSeverity, NotificationType
# KEYWORDS: [DOMAIN(9): MatchNotifier; DOMAIN(8): CppBinding; CONCEPT(9): NoFallback; TECH(7): PyBind11; TECH(6): Notification]
# LINKS: [IMPORTS(9): match_notifier_plugin_cpp; EXPORTS(9): MatchNotifierPlugin; EXPORTS(8): MatchEntry; EXPORTS(8): NotificationSettings; EXPORTS(8): MatchSeverity; EXPORTS(8): NotificationType]
# LINKS_TO_SPECIFICATION: [Спецификация match_notifier из docs/cpp_modules/match_notifier_plugin_draft_code_plan_v2.md]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 10 [Плагин уведомлений о совпадениях мониторинга] => MatchNotifierPlugin
# CLASS 8 [Запись о найденном совпадении] => MatchEntry
# CLASS 7 [Настройки уведомлений] => NotificationSettings
# CLASS 6 [Уровень важности совпадения] => MatchSeverity
# CLASS 5 [Тип уведомления] => NotificationType
# END_MODULE_MAP
# START_USE_CASES:
# - [MatchNotifierPlugin]: System (MatchAlert) -> NotifyOnMatch -> UserAlerted
# - [MatchEntry]: Plugin (MatchDetection) -> RecordMatch -> MatchStored
# - [NotificationSettings]: User (Configuration) -> ConfigureNotifications -> SettingsApplied
# - [MatchSeverity]: System (Priority) -> ClassifyMatch -> SeverityAssigned
# - [NotificationType]: System (Delivery) -> ChooseDeliveryMethod -> NotificationSent
# END_USE_CASES
"""
Модуль match_notifier.py — Python-обёртка для C++ модуля плагина уведомлений о совпадениях мониторинга.

ВНИМАНИЕ: Этот модуль требует наличия скомпилированного C++ модуля match_notifier_plugin_cpp.
Python fallback НЕПРЕДУСМОТРЕН - только C++ реализация.

Экспортирует:
    - MatchNotifierPlugin: Плагин для отправки уведомлений о совпадениях адресов
    - MatchEntry: Класс для хранения информации о найденном совпадении
    - NotificationSettings: Класс для настроек уведомлений
    - MatchSeverity: Перечисление уровней важности совпадений
    - NotificationType: Перечисление типов уведомлений

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
_logger = logging.getLogger("src.monitor._cpp.match_notifier")
if not _logger.handlers:
    _file_handler = _setup_file_logging()
    _logger.addHandler(_file_handler)
    _logger.setLevel(logging.INFO)

# ============================================================================
# ИМПОРТ C++ МОДУЛЯ
# ============================================================================

# START_FUNCTION_IMPORT_CPP_MODULE
# START_CONTRACT:
# PURPOSE: Импорт C++ модуля match_notifier_plugin_cpp с жёсткой проверкой доступности
# INPUTS: Нет
# OUTPUTS: Импортированный модуль
# SIDE_EFFECTS: Вызывает ImportError при отсутствии C++ модуля
# KEYWORDS: [PATTERN(9): HardImport; DOMAIN(9): ModuleLoading; TECH(6): Import]
# END_CONTRACT

def _import_cpp_module():
    """
    Импорт C++ модуля match_notifier_plugin_cpp.
    
    ВНИМАНИЕ: Это жёсткий импорт. При отсутствии C++ модуля
    выбрасывается ImportError с инструкцией по сборке.
    
    Returns:
        Импортированный C++ модуль match_notifier_plugin_cpp
        
    Raises:
        ImportError: Если C++ модуль недоступен
    """
    _logger.info(f"[IMPORT][START] Попытка импорта match_notifier_plugin_cpp...")
    
    try:
        import match_notifier_plugin_cpp
        _logger.info(f"[IMPORT][SUCCESS] C++ модуль match_notifier_plugin_cpp успешно импортирован [SUCCESS]")
        return match_notifier_plugin_cpp
    except (ImportError, ModuleNotFoundError) as e:
        _logger.error(f"[IMPORT][CRITICAL] C++ модуль match_notifier_plugin_cpp недоступен: {e} [FAIL]")
        
        build_instructions = f"""
================================================================================
ОШИБКА: C++ модуль match_notifier_plugin_cpp недоступен
================================================================================

Требуемый модуль: match_notifier_plugin_cpp
Описание: Плагин уведомлений о совпадениях мониторинга

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

Документация: docs/cpp_modules/match_notifier_plugin_draft_code_plan_v2.md

================================================================================
"""
        _logger.error(f"[IMPORT][CRITICAL]{build_instructions}")
        raise ImportError(
            f"C++ модуль match_notifier_plugin_cpp недоступен. "
            f"Пожалуйста, соберите C++ модуль следуя инструкциям в docs/cpp_modules/match_notifier_plugin_draft_code_plan_v2.md"
        )

# END_FUNCTION_IMPORT_CPP_MODULE

# ============================================================================
# ИМПОРТ КЛАССОВ ИЗ C++ МОДУЛЯ
# ============================================================================

# Получаем C++ модуль
_cpp_module = _import_cpp_module()

# Импортируем классы из C++ модуля
try:
    MatchNotifierPlugin = _cpp_module.MatchNotifierPlugin
    _logger.info(f"[IMPORT][SUCCESS] Класс MatchNotifierPlugin импортирован из C++ [SUCCESS]")
except AttributeError as e:
    _logger.error(f"[IMPORT][CRITICAL] Класс MatchNotifierPlugin не найден в C++ модуле: {e} [FAIL]")
    raise ImportError(f"C++ модуль match_notifier_plugin_cpp не содержит класса MatchNotifierPlugin: {e}")

try:
    MatchEntry = _cpp_module.MatchEntry
    _logger.info(f"[IMPORT][SUCCESS] Класс MatchEntry импортирован из C++ [SUCCESS]")
except AttributeError as e:
    _logger.error(f"[IMPORT][CRITICAL] Класс MatchEntry не найден в C++ модуле: {e} [FAIL]")
    raise ImportError(f"C++ модуль match_notifier_plugin_cpp не содержит класса MatchEntry: {e}")

try:
    NotificationSettings = _cpp_module.NotificationSettings
    _logger.info(f"[IMPORT][SUCCESS] Класс NotificationSettings импортирован из C++ [SUCCESS]")
except AttributeError as e:
    _logger.error(f"[IMPORT][CRITICAL] Класс NotificationSettings не найден в C++ модуле: {e} [FAIL]")
    raise ImportError(f"C++ модуль match_notifier_plugin_cpp не содержит класса NotificationSettings: {e}")

try:
    MatchSeverity = _cpp_module.MatchSeverity
    _logger.info(f"[IMPORT][SUCCESS] Класс MatchSeverity импортирован из C++ [SUCCESS]")
except AttributeError as e:
    _logger.error(f"[IMPORT][CRITICAL] Класс MatchSeverity не найден в C++ модуле: {e} [FAIL]")
    raise ImportError(f"C++ модуль match_notifier_plugin_cpp не содержит класса MatchSeverity: {e}")

try:
    NotificationType = _cpp_module.NotificationType
    _logger.info(f"[IMPORT][SUCCESS] Класс NotificationType импортирован из C++ [SUCCESS]")
except AttributeError as e:
    _logger.error(f"[IMPORT][CRITICAL] Класс NotificationType не найден в C++ модуле: {e} [FAIL]")
    raise ImportError(f"C++ модуль match_notifier_plugin_cpp не содержит класса NotificationType: {e}")

# ============================================================================
# ЭКСПОРТ
# ============================================================================

__all__ = [
    # Классы из C++ модуля
    "MatchNotifierPlugin",
    "MatchEntry",
    "NotificationSettings",
    "MatchSeverity",
    "NotificationType",
]

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ ПРИ ИМПОРТЕ
# ============================================================================

_logger.info(f"[INIT][SUCCESS] Модуль src.monitor._cpp.match_notifier успешно инициализирован, используется C++ реализация [SUCCESS]")
