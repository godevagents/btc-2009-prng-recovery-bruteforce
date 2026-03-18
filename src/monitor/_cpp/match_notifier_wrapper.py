# FILE: src/monitor/_cpp/match_notifier_wrapper.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Python-обёртка для C++ плагина match_notifier_plugin_cpp с интеграцией уведомлений о совпадениях. Обеспечивает real-time уведомления, управление историей совпадений и экспорт данных.
# SCOPE: Уведомления о совпадениях, история совпадений, desktop-уведомления, звуковые уведомления, визуальные уведомления, файловый экспорт
# INPUT: События совпадений от генератора, команды управления уведомлениями
# OUTPUT: UI компоненты для настройки и отображения уведомлений, методы экспорта, система управления уведомлениями
# KEYWORDS: [DOMAIN(9): Notifications; DOMAIN(8): RealTime; TECH(8): CppBinding; CONCEPT(7): Fallback; TECH(7): Gradio]
# LINKS: [USES_API(8): src.monitor._cpp.plugin_base_wrapper; USES_API(7): src.monitor.plugins.match_notifier; USES_API(6): gradio]
# LINKS_TO_SPECIFICATION: [create_match_notifier_wrapper_plan.md]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 10 [Обёртка для C++ MatchNotifierPlugin с Python-friendly интерфейсом] => MatchNotifierPlugin
# CLASS 8 [Данные о совпадении] => MatchInfo
# CLASS 7 [Конфигурация уведомлений] => NotifierConfig
# FUNC 6 [Фабрика плагина уведомлений] => create_match_notifier_plugin
# FUNC 5 [Получение конфигурации по умолчанию] => get_default_config
# END_MODULE_MAP
# START_USE_CASES:
# - [MatchNotifierPlugin]: System (MatchFound) -> NotifyUser -> UserInformed
# - [on_match_found]: Generator (MatchFound) -> ProcessMatch -> NotificationSent
# - [notify_match]: System (Notification) -> SendNotification -> UserAlerted
# - [register_notifier]: System (Integration) -> RegisterHandler -> HandlerReady
# - [export_matches]: Admin (Export) -> SaveMatchesToFile -> FileCreated
# END_USE_CASES
"""
Модуль match_notifier_wrapper.py — Python-обёртка для C++ плагина уведомлений о совпадениях.

Обеспечивает:
- Real-time уведомления о найденных совпадениях
- Интеграцию с Gradio UI
- Управление звуковыми и визуальными уведомлениями
- Историю совпадений с возможностью экспорта
- Fallback на Python реализацию при отсутствии C++ модуля

Пример использования:
    from src.monitor._cpp.match_notifier_wrapper import MatchNotifierPlugin
    
    # Создание плагина
    plugin = MatchNotifierPlugin(config={"priority": 25})
    
    # Инициализация
    plugin.initialize({"app": app})
    
    # Обработка совпадения
    plugin.on_match_found({
        "address": "1abc...",
        "target_address": "1xyz...",
        "iteration": 1000,
        "entropy_used": 256.0,
    })
    
    # Получение истории
    history = plugin.get_match_history()
    
    # Экспорт
    plugin.export_matches("matches.json")
"""

import json
import logging
import subprocess
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Импорт базового класса
from src.monitor._cpp.plugin_base_wrapper import (
    BaseMonitorPlugin,
    EVENT_TYPE_MATCH,
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
_logger = logging.getLogger("src.monitor._cpp.match_notifier_wrapper")
if not _logger.handlers:
    _file_handler = _setup_file_logging()
    _logger.addHandler(_file_handler)
    _logger.setLevel(logging.DEBUG)

logger = _logger

# ============================================================================
# КОНСТАНТЫ
# ============================================================================

# START_CONSTANTS_MATCH_NOTIFIER_WRAPPER
MAX_MATCH_HISTORY = 50
DEFAULT_NOTIFICATION_COOLDOWN = 5.0  # секунд между уведомлениями
SUPPORTED_NOTIFICATION_TYPES = {"desktop", "sound", "log", "ui", "file"}

# Уровни серьёзности совпадений
MATCH_SEVERITY = {
    "info": {"color": "#2196F3", "icon": "ℹ️"},
    "success": {"color": "#4CAF50", "icon": "✅"},
    "warning": {"color": "#FF9800", "icon": "⚠️"},
    "critical": {"color": "#F44336", "icon": "🚨"},
}

# END_CONSTANTS_MATCH_NOTIFIER_WRAPPER

# ============================================================================
# ЗАГРУЗКА C++ МОДУЛЯ С FALLBACK
# ============================================================================

# START_FUNCTION_IMPORT_CPP_MODULE
# START_CONTRACT:
# PURPOSE: Импорт C++ модуля match_notifier_plugin_cpp с fallback на Python
# OUTPUTS:
# - Dict с ключами 'available', 'MatchNotifierPlugin', 'MatchInfo', 'error'
# KEYWORDS: [PATTERN(7): ModuleCheck; DOMAIN(8): ModuleLoading; TECH(6): Import]
# END_CONTRACT

def _import_cpp_module() -> Dict[str, Any]:
    """
    Импорт C++ модуля match_notifier_plugin_cpp с fallback на Python.
    
    Returns:
        Словарь с информацией о доступности модуля и классами
    """
    try:
        from match_notifier_plugin_cpp import (
            MatchNotifierPlugin as _MatchNotifierPlugin,
            MatchInfo as _MatchInfo,
        )
        
        logger.info(f"[_import_cpp_module][MODULE_CHECK] C++ модуль match_notifier_plugin_cpp доступен [SUCCESS]")
        return {
            'available': True,
            'MatchNotifierPlugin': _MatchNotifierPlugin,
            'MatchInfo': _MatchInfo,
        }
    except ImportError as e:
        logger.info(f"[_import_cpp_module][MODULE_CHECK] C++ модуль match_notifier_plugin_cpp недоступен: {e}, используем Python fallback [INFO]")
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

# START_CLASS_MATCH_INFO
# START_CONTRACT:
# PURPOSE: Класс для хранения информации о найденном совпадении
# ATTRIBUTES:
# - timestamp: datetime — время обнаружения совпадения
# - wallet_address: str — адрес найденного кошелька
# - target_address: str — целевой адрес из списка
# - iteration: int — номер итерации
# - entropy_used: float — использованная энтропия
# - metadata: Dict[str, Any] — дополнительные метаданные
# KEYWORDS: [PATTERN(7): DataClass; DOMAIN(9): MatchNotification; CONCEPT(6): Event]
# END_CONTRACT

@dataclass
class MatchInfo:
    """Информация о найденном совпадении."""
    timestamp: datetime = field(default_factory=datetime.now)
    wallet_address: str = ""
    target_address: str = ""
    iteration: int = 0
    entropy_used: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразование в словарь.
        
        Returns:
            Словарь с данными о совпадении
        """
        return {
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            "wallet_address": self.wallet_address,
            "target_address": self.target_address,
            "iteration": self.iteration,
            "entropy_used": self.entropy_used,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MatchInfo":
        """
        Создание из словаря.
        
        Args:
            data: Словарь с данными о совпадении
            
        Returns:
            Экземпляр MatchInfo
        """
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()
            
        return cls(
            timestamp=timestamp,
            wallet_address=data.get("wallet_address", ""),
            target_address=data.get("target_address", ""),
            iteration=data.get("iteration", 0),
            entropy_used=data.get("entropy_used", 0.0),
            metadata=data.get("metadata", {}),
        )
    
    def to_display(self) -> str:
        """
        Форматированное представление для отображения.
        
        Returns:
            Отформатированная строка
        """
        return f"""
=== СОВПАДЕНИЕ НАЙДЕНО ===
Адрес кошелька: {self.wallet_address}
Целевой адрес: {self.target_address}
Итерация: {self.iteration}
Энтропия: {self.entropy_used:.2f} бит
Время: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
"""

# END_CLASS_MATCH_INFO

# START_CLASS_NOTIFIER_CONFIG
# START_CONTRACT:
# PURPOSE: Класс для хранения конфигурации уведомлений
# ATTRIBUTES:
# - sound_enabled: bool — включить звуковые уведомления
# - visual_enabled: bool — включить визуальные уведомления
# - file_enabled: bool — включить запись в файл
# - desktop_enabled: bool — включить desktop-уведомления
# - log_enabled: bool — включить логирование
# - ui_enabled: bool — включить UI уведомления
# - cooldown_seconds: float — кулдаун между уведомлениями
# KEYWORDS: [PATTERN(7): DataClass; DOMAIN(8): Configuration; CONCEPT(6): Settings]
# END_CONTRACT

@dataclass
class NotifierConfig:
    """Конфигурация уведомлений."""
    sound_enabled: bool = False
    visual_enabled: bool = True
    file_enabled: bool = False
    desktop_enabled: bool = True
    log_enabled: bool = True
    ui_enabled: bool = True
    cooldown_seconds: float = DEFAULT_NOTIFICATION_COOLDOWN
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование конфигурации в словарь."""
        return {
            "sound_enabled": self.sound_enabled,
            "visual_enabled": self.visual_enabled,
            "file_enabled": self.file_enabled,
            "desktop_enabled": self.desktop_enabled,
            "log_enabled": self.log_enabled,
            "ui_enabled": self.ui_enabled,
            "cooldown_seconds": self.cooldown_seconds,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NotifierConfig":
        """Создание конфигурации из словаря."""
        return cls(
            sound_enabled=data.get("sound_enabled", False),
            visual_enabled=data.get("visual_enabled", True),
            file_enabled=data.get("file_enabled", False),
            desktop_enabled=data.get("desktop_enabled", True),
            log_enabled=data.get("log_enabled", True),
            ui_enabled=data.get("ui_enabled", True),
            cooldown_seconds=data.get("cooldown_seconds", DEFAULT_NOTIFICATION_COOLDOWN),
        )

# END_CLASS_NOTIFIER_CONFIG

# ============================================================================
# ОСНОВНОЙ КЛАСС MATCH NOTIFIER PLUGIN WRAPPER
# ============================================================================

# START_CLASS_MATCH_NOTIFIER_PLUGIN
# START_CONTRACT:
# PURPOSE: Обёртка для C++ MatchNotifierPlugin с Python-friendly интерфейсом. Обеспечивает real-time уведомления о совпадениях, интеграцию с Gradio UI и fallback на Python реализацию.
# ATTRIBUTES:
# - C++ плагин => _cpp_plugin: Optional[Any]
# - Python плагин => _py_plugin: Optional[Any]
# - Флаг использования C++ => _use_cpp: bool
# - История совпадений => _match_history: Deque[MatchInfo]
# - Общее количество совпадений => _match_count: int
# - Зарегистрированные уведомители => _notifiers: List[Callable]
# - Конфигурация уведомлений => _notification_config: NotifierConfig
# - Время последнего уведомления => _last_notification_time: float
# - Флаг мониторинга => _is_monitoring: bool
# METHODS:
# - Инициализация плагина => initialize(config)
# - Обработка события => process_event(event)
# - Получение статуса => get_status()
# - Завершение работы => shutdown()
# - Обработка совпадения => on_match_found(match_data)
# - Отправка уведомления => notify_match(match_info)
# - Регистрация уведомителя => register_notifier(notifier_func)
# - Удаление регистрации => unregister_notifier()
# - Настройка уведомлений => set_notification_config(config)
# - Получение настроек => get_notification_config()
# - Включение звука => enable_sound_notifications()
# - Отключение звука => disable_sound_notifications()
# - Включение визуальных => enable_visual_notifications()
# - Отключение визуальных => disable_visual_notifications()
# - Включение файловых => enable_file_notifications()
# - Отключение файловых => disable_file_notifications()
# - Получение истории => get_match_history()
# - Очистка истории => clear_match_history()
# - Получение количества => get_match_count()
# - Экспорт совпадений => export_matches(filepath)
# KEYWORDS: [PATTERN(8): Wrapper; DOMAIN(9): Notifications; TECH(8): CppBinding; CONCEPT(7): Fallback]
# LINKS: [EXTENDS(8): BaseMonitorPlugin; USES_API(7): match_notifier.py]
# END_CONTRACT

class MatchNotifierPlugin(BaseMonitorPlugin):
    """
    Обёртка для C++ MatchNotifierPlugin с Python-friendly интерфейсом.
    
    Обеспечивает:
    - Real-time уведомления о найденных совпадениях
    - Интеграцию с Gradio UI
    - Управление звуковыми и визуальными уведомлениями
    - Историю совпадений с возможностью экспорта
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
    
    DESCRIPTION: str = "Обёртка для C++ плагина уведомлений о совпадениях"
    """Описание плагина"""
    
    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация обёртки MatchNotifierPlugin с загрузкой C++ или Python модуля
    # INPUTS:
    # - config: Optional[Dict[str, Any]] — словарь конфигурации плагина
    # OUTPUTS: Инициализированный объект MatchNotifierPlugin
    # SIDE_EFFECTS: Загружает C++ модуль или Python fallback; инициализирует хранилище истории
    # KEYWORDS: [CONCEPT(5): Initialization; DOMAIN(7): PluginSetup]
    # TEST_CONDITIONS_SUCCESS_CRITERIA: Плагин должен корректно определить доступность C++ модуля
    # END_CONTRACT
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Инициализация обёртки MatchNotifierPlugin.
        
        Args:
            config: Словарь конфигурации плагина (опционально)
        """
        # Инициализация базового класса
        super().__init__(name="match_notifier", config=config)
        
        # Получение информации о C++ модуле
        self._cpp_module_info = _get_cpp_module_info()
        self._use_cpp = self._cpp_module_info.get('available', False)
        
        # Инициализация C++ или Python плагина
        self._cpp_plugin = None
        self._py_plugin = None
        
        if self._use_cpp:
            try:
                self._cpp_plugin = self._cpp_module_info['MatchNotifierPlugin']()
                logger.info(f"[MatchNotifierPlugin][INIT][ConditionCheck] Используется C++ плагин [SUCCESS]")
            except Exception as e:
                logger.warning(f"[MatchNotifierPlugin][INIT][ExceptionCaught] Ошибка при создании C++ плагина: {e}, используем Python fallback")
                self._use_cpp = False
        
        if not self._use_cpp:
            # Python реализация не используется - используем встроенную реализацию
            logger.info(f"[MatchNotifierPlugin][INIT][ConditionCheck] Используется встроенная Python реализация [SUCCESS]")
        
        # Инициализация хранилища данных
        self._match_history: Deque[MatchInfo] = deque(maxlen=MAX_MATCH_HISTORY)
        self._match_count: int = 0
        self._notifiers: List[Callable] = []
        self._notification_config = NotifierConfig()
        self._last_notification_time: float = 0
        self._is_monitoring: bool = False
        self._last_match: Optional[MatchInfo] = None
        
        # Конфигурация из параметров
        if config and 'config' in config:
            self._notification_config = NotifierConfig.from_dict(config['config'])
        
        # Логирование
        self._logger.info(f"[MatchNotifierPlugin][INIT][VarCheck] Плагин инициализирован, C++: {self._use_cpp} [VALUE]")
    
    # END_METHOD___init__
    
    # ============================================================================
    # СВОЙСТВА (PROPERTIES)
    # ============================================================================
    
    # START_PROPERTY_SOUND_ENABLED
    @property
    def sound_enabled(self) -> bool:
        """
        Проверка включения звуковых уведомлений.
        
        Returns:
            True если звуковые уведомления включены
        """
        return self._notification_config.sound_enabled
    # END_PROPERTY_SOUND_ENABLED
    
    # START_PROPERTY_VISUAL_ENABLED
    @property
    def visual_enabled(self) -> bool:
        """
        Проверка включения визуальных уведомлений.
        
        Returns:
            True если визуальные уведомления включены
        """
        return self._notification_config.visual_enabled
    # END_PROPERTY_VISUAL_ENABLED
    
    # START_PROPERTY_FILE_OUTPUT_ENABLED
    @property
    def file_output_enabled(self) -> bool:
        """
        Проверка включения записи в файл.
        
        Returns:
            True если запись в файл включена
        """
        return self._notification_config.file_enabled
    # END_PROPERTY_FILE_OUTPUT_ENABLED
    
    # START_PROPERTY_MATCH_COUNT
    @property
    def match_count(self) -> int:
        """
        Получение количества найденных совпадений.
        
        Returns:
            Количество совпадений
        """
        return self._match_count
    # END_PROPERTY_MATCH_COUNT
    
    # START_PROPERTY_LAST_MATCH
    @property
    def last_match(self) -> Optional[MatchInfo]:
        """
        Получение информации о последнем совпадении.
        
        Returns:
            Последнее совпадение или None
        """
        return self._last_match
    # END_PROPERTY_LAST_MATCH
    
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
        self._logger.info(f"[MatchNotifierPlugin][INITIALIZE][StepComplete] Начало инициализации плагина")
        
        # Обработка случая когда config равен None
        if config is None:
            config = {}
        
        # Обновление конфигурации
        if config and 'config' in config:
            self._notification_config = NotifierConfig.from_dict(config['config'])
        
        # Сохранение ссылки на приложение
        self._app = config.get('app')
        
        # Регистрация хука для событий совпадений
        self.register_hook(EVENT_TYPE_MATCH, self._on_match_event_hook)
        
        # Обновление статуса
        self._status["state"] = "initialized"
        self._status["message"] = "Plugin initialized"
        
        self._logger.info(f"[MatchNotifierPlugin][INITIALIZE][StepComplete] Инициализация плагина завершена [SUCCESS]")
    
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
        
        self._logger.debug(f"[MatchNotifierPlugin][PROCESS_EVENT][ConditionCheck] Получено событие типа: {event_type} [VALUE]")
        
        if event_type == EVENT_TYPE_MATCH:
            # Обработка события совпадения
            match_data = event.get('data', {})
            if isinstance(match_data, dict):
                self.on_match_found(match_data)
            
            self._logger.debug(f"[MatchNotifierPlugin][PROCESS_EVENT][StepComplete] Обработано событие совпадения [SUCCESS]")
        
        elif event_type == EVENT_TYPE_METRIC:
            # Обработка события метрики (проверка на совпадения)
            metrics = event.get('data', {})
            if isinstance(metrics, dict):
                match_count = metrics.get("match_count", 0)
                if match_count > self._match_count:
                    # Новые совпадения обнаружены
                    new_matches = match_count - self._match_count
                    for i in range(new_matches):
                        # Генерируем фиктивные данные для примера
                        self._generate_mock_match()
            
            self._logger.debug(f"[MatchNotifierPlugin][PROCESS_EVENT][StepComplete] Обработано событие метрики [SUCCESS]")
        
        elif event_type == EVENT_TYPE_START:
            # Запуск мониторинга
            self._is_monitoring = True
            self._status["state"] = "monitoring"
            self._status["message"] = "Monitoring active"
            self._logger.info(f"[MatchNotifierPlugin][PROCESS_EVENT][StepComplete] Получено событие START [SUCCESS]")
        
        elif event_type == EVENT_TYPE_STOP:
            # Остановка мониторинга
            self._is_monitoring = False
            self._status["state"] = "stopped"
            self._status["message"] = "Monitoring stopped"
            self._logger.info(f"[MatchNotifierPlugin][PROCESS_EVENT][StepComplete] Получено событие STOP [SUCCESS]")
        
        elif event_type == EVENT_TYPE_STATUS:
            # Обработка события статуса
            status_data = event.get('data', {})
            self._logger.debug(f"[MatchNotifierPlugin][PROCESS_EVENT][Info] Событие статуса: {status_data}")
        
        else:
            self._logger.warning(f"[MatchNotifierPlugin][PROCESS_EVENT][ConditionCheck] Неизвестный тип события: {event_type} [FAIL]")
    
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
            "match_count": self._match_count,
            "history_size": len(self._match_history),
            "notification_config": self._notification_config.to_dict(),
        }
        
        self._logger.debug(f"[MatchNotifierPlugin][GET_STATUS][ReturnData] Статус: {status} [VALUE]")
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
        self._logger.info(f"[MatchNotifierPlugin][SHUTDOWN][StepComplete] Начало завершения работы плагина")
        
        # Остановка мониторинга
        self._is_monitoring = False
        
        # Очистка уведомителей
        self._notifiers.clear()
        
        # Обновление статуса
        self._status["state"] = "shutdown"
        self._status["message"] = "Plugin shutdown complete"
        
        self._logger.info(f"[MatchNotifierPlugin][SHUTDOWN][StepComplete] Завершение работы плагина завершено [SUCCESS]")
    
    # END_METHOD_SHUTDOWN
    
    # ============================================================================
    # СПЕЦИФИЧЕСКИЕ МЕТОДЫ УВЕДОМЛЕНИЙ
    # ============================================================================
    
    # START_METHOD_ON_MATCH_FOUND
    # START_CONTRACT:
    # PURPOSE: Обработка найденного совпадения
    # INPUTS:
    # - match_data: Dict[str, Any] — данные о совпадении
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Добавляет совпадение в историю; отправляет уведомления
    # KEYWORDS: [DOMAIN(9): MatchHandler; CONCEPT(7): EventHandler]
    # END_CONTRACT
    def on_match_found(self, match_data: Dict[str, Any]) -> None:
        """
        Обработка найденного совпадения.
        
        Args:
            match_data: Словарь с данными о совпадении
        """
        # START_BLOCK_CHECK_COOLDOWN: [Проверка кулдауна]
        current_time = time.time()
        if current_time - self._last_notification_time < self._notification_config.cooldown_seconds:
            self._logger.debug(f"[MatchNotifierPlugin][ON_MATCH_FOUND][ConditionCheck] Пропуск уведомления (кулдаун)")
            return
        # END_BLOCK_CHECK_COOLDOWN
        
        # Создание объекта MatchInfo
        match_info = MatchInfo(
            timestamp=datetime.now(),
            wallet_address=match_data.get("wallet_address", match_data.get("address", "")),
            target_address=match_data.get("target_address", match_data.get("target", "")),
            iteration=match_data.get("iteration", 0),
            entropy_used=match_data.get("entropy_used", match_data.get("entropy", 0.0)),
            metadata=match_data.get("metadata", {}),
        )
        
        # START_BLOCK_ADD_TO_HISTORY: [Добавление в историю]
        self._match_history.append(match_info)
        self._match_count += 1
        self._last_match = match_info
        # END_BLOCK_ADD_TO_HISTORY
        
        # START_BLOCK_SEND_NOTIFICATION: [Отправка уведомления]
        self.notify_match(match_info)
        # END_BLOCK_SEND_NOTIFICATION
        
        self._last_notification_time = current_time
        
        self._logger.info(f"[MatchNotifierPlugin][ON_MATCH_FOUND][StepComplete] Совпадение обработано: address={match_info.wallet_address} [SUCCESS]")
    
    # END_METHOD_ON_MATCH_FOUND
    
    # START_METHOD_NOTIFY_MATCH
    # START_CONTRACT:
    # PURPOSE: Отправка уведомления о совпадении
    # INPUTS:
    # - match_info: MatchInfo — информация о совпадении
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Отправляет уведомления через все включённые каналы
    # KEYWORDS: [DOMAIN(9): Notification; CONCEPT(7): Broadcasting]
    # END_CONTRACT
    def notify_match(self, match_info: MatchInfo) -> None:
        """
        Отправка уведомления о совпадении.
        
        Args:
            match_info: Информация о совпадении
        """
        # Desktop уведомление
        if self._notification_config.desktop_enabled:
            self._send_desktop_notification(match_info)
        
        # Звуковое уведомление
        if self._notification_config.sound_enabled:
            self._play_sound_notification()
        
        # Логирование
        if self._notification_config.log_enabled:
            self._logger.warning(
                f"[MatchNotifierPlugin][NOTIFY_MATCH][CRITICAL] "
                f"СОВПАДЕНИЕ! Адрес: {match_info.wallet_address}, Итерация: {match_info.iteration}"
            )
        
        # Вызов зарегистрированных уведомителей
        for notifier in self._notifiers:
            try:
                notifier(match_info)
            except Exception as e:
                self._logger.error(f"[MatchNotifierPlugin][NOTIFY_MATCH][ExceptionCaught] Ошибка в уведомителе: {e}")
        
        self._logger.debug(f"[MatchNotifierPlugin][NOTIFY_MATCH][StepComplete] Уведомление отправлено [SUCCESS]")
    
    # END_METHOD_NOTIFY_MATCH
    
    # START_METHOD_REGISTER_NOTIFIER
    # START_CONTRACT:
    # PURPOSE: Регистрация функции уведомления
    # INPUTS:
    # - notifier_func: Callable — функция уведомления
    # OUTPUTS: Нет
    # KEYWORDS: [DOMAIN(8): Subscription; CONCEPT(7): Registration]
    # END_CONTRACT
    def register_notifier(self, notifier_func: Callable) -> None:
        """
        Регистрация функции уведомления.
        
        Args:
            notifier_func: Функция, которая будет вызываться при совпадении
        """
        if notifier_func not in self._notifiers:
            self._notifiers.append(notifier_func)
            self._logger.info(f"[MatchNotifierPlugin][REGISTER_NOTIFIER][StepComplete] Уведомитель зарегистрирован [SUCCESS]")
    
    # END_METHOD_REGISTER_NOTIFIER
    
    # START_METHOD_UNREGISTER_NOTIFIER
    # START_CONTRACT:
    # PURPOSE: Удаление регистрации функции уведомления
    # OUTPUTS: Нет
    # KEYWORDS: [DOMAIN(8): Subscription; CONCEPT(7): Removal]
    # END_CONTRACT
    def unregister_notifier(self) -> None:
        """
        Удаление регистрации функции уведомления.
        """
        self._notifiers.clear()
        self._logger.info(f"[MatchNotifierPlugin][UNREGISTER_NOTIFIER][StepComplete] Уведомители удалены [SUCCESS]")
    
    # END_METHOD_UNREGISTER_NOTIFIER
    
    # START_METHOD_SET_NOTIFICATION_CONFIG
    # START_CONTRACT:
    # PURPOSE: Настройка параметров уведомлений
    # INPUTS:
    # - config: Dict[str, Any] — словарь конфигурации
    # OUTPUTS: Нет
    # KEYWORDS: [CONCEPT(6): Setter; DOMAIN(8): Configuration]
    # END_CONTRACT
    def set_notification_config(self, config: Dict[str, Any]) -> None:
        """
        Настройка параметров уведомлений.
        
        Args:
            config: Словарь конфигурации уведомлений
        """
        self._notification_config = NotifierConfig.from_dict(config)
        self._logger.info(f"[MatchNotifierPlugin][SET_NOTIFICATION_CONFIG][StepComplete] Конфигурация обновлена [SUCCESS]")
    
    # END_METHOD_SET_NOTIFICATION_CONFIG
    
    # START_METHOD_GET_NOTIFICATION_CONFIG
    # START_CONTRACT:
    # PURPOSE: Получение текущих настроек уведомлений
    # OUTPUTS:
    # - Dict[str, Any] — словарь конфигурации
    # KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): Configuration]
    # END_CONTRACT
    def get_notification_config(self) -> Dict[str, Any]:
        """
        Получение текущих настроек уведомлений.
        
        Returns:
            Словарь конфигурации уведомлений
        """
        return self._notification_config.to_dict()
    
    # END_METHOD_GET_NOTIFICATION_CONFIG
    
    # START_METHOD_ENABLE_SOUND_NOTIFICATIONS
    # START_CONTRACT:
    # PURPOSE: Включение звуковых уведомлений
    # OUTPUTS: Нет
    # KEYWORDS: [CONCEPT(6): Enable; DOMAIN(8): Notification]
    # END_CONTRACT
    def enable_sound_notifications(self) -> None:
        """Включение звуковых уведомлений."""
        self._notification_config.sound_enabled = True
        self._logger.info(f"[MatchNotifierPlugin][ENABLE_SOUND_NOTIFICATIONS][StepComplete] Звуковые уведомления включены [SUCCESS]")
    
    # END_METHOD_ENABLE_SOUND_NOTIFICATIONS
    
    # START_METHOD_DISABLE_SOUND_NOTIFICATIONS
    # START_CONTRACT:
    # PURPOSE: Отключение звуковых уведомлений
    # OUTPUTS: Нет
    # KEYWORDS: [CONCEPT(7): Disable; DOMAIN(8): Notification]
    # END_CONTRACT
    def disable_sound_notifications(self) -> None:
        """Отключение звуковых уведомлений."""
        self._notification_config.sound_enabled = False
        self._logger.info(f"[MatchNotifierPlugin][DISABLE_SOUND_NOTIFICATIONS][StepComplete] Звуковые уведомления отключены [SUCCESS]")
    
    # END_METHOD_DISABLE_SOUND_NOTIFICATIONS
    
    # START_METHOD_ENABLE_VISUAL_NOTIFICATIONS
    # START_CONTRACT:
    # PURPOSE: Включение визуальных уведомлений
    # OUTPUTS: Нет
    # KEYWORDS: [CONCEPT(6): Enable; DOMAIN(8): Notification]
    # END_CONTRACT
    def enable_visual_notifications(self) -> None:
        """Включение визуальных уведомлений."""
        self._notification_config.visual_enabled = True
        self._logger.info(f"[MatchNotifierPlugin][ENABLE_VISUAL_NOTIFICATIONS][StepComplete] Визуальные уведомления включены [SUCCESS]")
    
    # END_METHOD_ENABLE_VISUAL_NOTIFICATIONS
    
    # START_METHOD_DISABLE_VISUAL_NOTIFICATIONS
    # START_CONTRACT:
    # PURPOSE: Отключение визуальных уведомлений
    # OUTPUTS: Нет
    # KEYWORDS: [CONCEPT(7): Disable; DOMAIN(8): Notification]
    # END_CONTRACT
    def disable_visual_notifications(self) -> None:
        """Отключение визуальных уведомлений."""
        self._notification_config.visual_enabled = False
        self._logger.info(f"[MatchNotifierPlugin][DISABLE_VISUAL_NOTIFICATIONS][StepComplete] Визуальные уведомления отключены [SUCCESS]")
    
    # END_METHOD_DISABLE_VISUAL_NOTIFICATIONS
    
    # START_METHOD_ENABLE_FILE_NOTIFICATIONS
    # START_CONTRACT:
    # PURPOSE: Включение записи в файл
    # OUTPUTS: Нет
    # KEYWORDS: [CONCEPT(6): Enable; DOMAIN(8): FileOutput]
    # END_CONTRACT
    def enable_file_notifications(self) -> None:
        """Включение записи в файл."""
        self._notification_config.file_enabled = True
        self._logger.info(f"[MatchNotifierPlugin][ENABLE_FILE_NOTIFICATIONS][StepComplete] Запись в файл включена [SUCCESS]")
    
    # END_METHOD_ENABLE_FILE_NOTIFICATIONS
    
    # START_METHOD_DISABLE_FILE_NOTIFICATIONS
    # START_CONTRACT:
    # PURPOSE: Отключение записи в файл
    # OUTPUTS: Нет
    # KEYWORDS: [CONCEPT(7): Disable; DOMAIN(8): FileOutput]
    # END_CONTRACT
    def disable_file_notifications(self) -> None:
        """Отключение записи в файл."""
        self._notification_config.file_enabled = False
        self._logger.info(f"[MatchNotifierPlugin][DISABLE_FILE_NOTIFICATIONS][StepComplete] Запись в файл отключена [SUCCESS]")
    
    # END_METHOD_DISABLE_FILE_NOTIFICATIONS
    
    # ============================================================================
    # МЕТОДЫ ИСТОРИИ СОВПАДЕНИЙ
    # ============================================================================
    
    # START_METHOD_GET_MATCH_HISTORY
    # START_CONTRACT:
    # PURPOSE: Получение истории совпадений
    # OUTPUTS:
    # - List[Dict] — список совпадений
    # KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): History]
    # END_CONTRACT
    def get_match_history(self) -> List[Dict[str, Any]]:
        """
        Получение истории совпадений.
        
        Returns:
            Список словарей с данными о совпадениях
        """
        return [match.to_dict() for match in self._match_history]
    
    # END_METHOD_GET_MATCH_HISTORY
    
    # START_METHOD_CLEAR_MATCH_HISTORY
    # START_CONTRACT:
    # PURPOSE: Очистка истории совпадений
    # OUTPUTS: Нет
    # KEYWORDS: [CONCEPT(7): Cleanup; DOMAIN(8): History]
    # END_CONTRACT
    def clear_match_history(self) -> None:
        """Очистка истории совпадений."""
        self._match_history.clear()
        self._match_count = 0
        self._last_match = None
        self._logger.info(f"[MatchNotifierPlugin][CLEAR_MATCH_HISTORY][StepComplete] История совпадений очищена [SUCCESS]")
    
    # END_METHOD_CLEAR_MATCH_HISTORY
    
    # START_METHOD_GET_MATCH_COUNT
    # START_CONTRACT:
    # PURPOSE: Получение количества найденных совпадений
    # OUTPUTS:
    # - int — количество совпадений
    # KEYWORDS: [CONCEPT(5): Getter; DOMAIN(8): Counter]
    # END_CONTRACT
    def get_match_count(self) -> int:
        """
        Получение количества найденных совпадений.
        
        Returns:
            Количество совпадений
        """
        return self._match_count
    
    # END_METHOD_GET_MATCH_COUNT
    
    # START_METHOD_EXPORT_MATCHES
    # START_CONTRACT:
    # PURPOSE: Экспорт совпадений в файл
    # INPUTS:
    # - filepath: str — путь к файлу
    # OUTPUTS:
    # - bool — True если экспорт успешен
    # SIDE_EFFECTS: Создаёт файл с данными о совпадениях
    # KEYWORDS: [DOMAIN(7): Export; TECH(5): JSON]
    # END_CONTRACT
    def export_matches(self, filepath: str) -> bool:
        """
        Экспорт совпадений в файл.
        
        Args:
            filepath: Путь к файлу для сохранения
            
        Returns:
            True если экспорт успешен
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.get_match_history(), f, indent=2, ensure_ascii=False)
            
            self._logger.info(f"[MatchNotifierPlugin][EXPORT_MATCHES][StepComplete] Экспорт в {filepath} [SUCCESS]")
            return True
        except Exception as e:
            self._logger.error(f"[MatchNotifierPlugin][EXPORT_MATCHES][ExceptionCaught] Ошибка экспорта: {e} [FAIL]")
            return False
    
    # END_METHOD_EXPORT_MATCHES
    
    # ============================================================================
    # ВНУТРЕННИЕ МЕТОДЫ
    # ============================================================================
    
    # START_METHOD_SEND_DESKTOP_NOTIFICATION
    # START_CONTRACT:
    # PURPOSE: Отправка desktop-уведомления в Linux
    # INPUTS:
    # - match_info: MatchInfo — информация о совпадении
    # OUTPUTS: Нет
    # KEYWORDS: [DOMAIN(7): DesktopNotify; TECH(6): notify-send]
    # END_CONTRACT
    def _send_desktop_notification(self, match_info: MatchInfo) -> None:
        """Отправка desktop-уведомления в Linux."""
        try:
            for notify_cmd in ["notify-send", "dunstify", "notify-osd"]:
                result = subprocess.run(
                    [notify_cmd, "Найдено совпадение!", f"Адрес: {match_info.wallet_address}\nИтерация: {match_info.iteration}"],
                    capture_output=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    self._logger.debug(f"[MatchNotifierPlugin][SEND_DESKTOP_NOTIFICATION][Success] Уведомление отправлено через {notify_cmd}")
                    return
        except FileNotFoundError:
            self._logger.debug(f"[MatchNotifierPlugin][SEND_DESKTOP_NOTIFICATION][ConditionCheck] Утилита уведомлений не найдена")
        except Exception as e:
            self._logger.warning(f"[MatchNotifierPlugin][SEND_DESKTOP_NOTIFICATION][ExceptionCaught] Ошибка отправки: {e}")
    
    # END_METHOD_SEND_DESKTOP_NOTIFICATION
    
    # START_METHOD_PLAY_SOUND_NOTIFICATION
    # START_CONTRACT:
    # PURPOSE: Воспроизведение звукового уведомления
    # OUTPUTS: Нет
    # KEYWORDS: [DOMAIN(7): SoundNotify; TECH(5): Audio]
    # END_CONTRACT
    def _play_sound_notification(self) -> None:
        """Воспроизведение звукового уведомления."""
        try:
            # Пробуем разные способы воспроизведения
            for play_cmd in ["paplay", "play", "aplay"]:
                result = subprocess.run(
                    [play_cmd, "/usr/share/sounds/freedesktop/stereo/complete.ogg"],
                    capture_output=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    self._logger.debug(f"[MatchNotifierPlugin][PLAY_SOUND_NOTIFICATION][Success] Звук воспроизведён через {play_cmd}")
                    return
        except FileNotFoundError:
            self._logger.debug(f"[MatchNotifierPlugin][PLAY_SOUND_NOTIFICATION][ConditionCheck] Утилита воспроизведения не найдена")
        except Exception as e:
            self._logger.warning(f"[MatchNotifierPlugin][PLAY_SOUND_NOTIFICATION][ExceptionCaught] Ошибка воспроизведения: {e}")
    
    # END_METHOD_PLAY_SOUND_NOTIFICATION
    
    # START_METHOD_ON_MATCH_EVENT_HOOK
    # START_CONTRACT:
    # PURPOSE: Обработчик хука для событий совпадений
    # INPUTS:
    # - event: Dict[str, Any] — событие
    # OUTPUTS: Нет
    # KEYWORDS: [CONCEPT(7): HookHandler]
    # END_CONTRACT
    def _on_match_event_hook(self, event: Dict[str, Any]) -> None:
        """Обработчик хука для событий совпадений."""
        match_data = event.get('data', {})
        if isinstance(match_data, dict):
            self.on_match_found(match_data)
    
    # END_METHOD_ON_MATCH_EVENT_HOOK
    
    # START_METHOD_GENERATE_MOCK_MATCH
    # START_CONTRACT:
    # PURPOSE: Генерация мок-совпадения для демонстрации
    # OUTPUTS: Нет
    # KEYWORDS: [CONCEPT(7): MockData]
    # END_CONTRACT
    def _generate_mock_match(self) -> None:
        """Генерация мок-совпадения для демонстрации."""
        import random
        import string
        
        # Генерация случайного адреса
        prefix = "1"
        chars = string.ascii_letters + string.digits
        length = random.randint(25, 34)
        wallet_address = prefix + "".join(random.choices(chars, k=length - 1))
        
        # Генерация случайного целевого адреса
        target_address = prefix + "".join(random.choices(chars, k=length - 1))
        
        match_data = {
            "wallet_address": wallet_address,
            "target_address": target_address,
            "iteration": random.randint(1, 100000),
            "entropy_used": random.uniform(128.0, 256.0),
            "metadata": {"source": "mock"},
        }
        
        self.on_match_found(match_data)
    
    # END_METHOD_GENERATE_MOCK_MATCH
    
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
            "match_count": self._match_count,
            "match_history": self.get_match_history(),
            "last_match": self._last_match.to_dict() if self._last_match else None,
            "notification_config": self._notification_config.to_dict(),
            "is_monitoring": self._is_monitoring,
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
        return f"MatchNotifierPlugin(name={self._name}, using_cpp={self._use_cpp}, matches={self._match_count})"
    
    # END_METHOD___repr__
    
    # START_METHOD___str__
    # START_CONTRACT:
    # PURPOSE: Читаемое строковое представление плагина
    # OUTPUTS: str — читаемое представление
    # KEYWORDS: [CONCEPT(5): StringRepr]
    # END_CONTRACT
    def __str__(self) -> str:
        """Читаемое строковое представление плагина."""
        return f"MatchNotifierPlugin '{self._name}' (C++: {self._use_cpp}, совпадений: {self._match_count})"
    
    # END_METHOD___str__


# END_CLASS_MATCH_NOTIFIER_PLUGIN

# ============================================================================
# ФАБРИКА ПЛАГИНА
# ============================================================================

# START_FUNCTION_CREATE_MATCH_NOTIFIER_PLUGIN
# START_CONTRACT:
# PURPOSE: Фабричная функция для создания плагина уведомлений о совпадениях
# INPUTS:
# - config: Optional[Dict[str, Any]] — конфигурация плагина
# OUTPUTS:
# - MatchNotifierPlugin — созданный экземпляр плагина
# KEYWORDS: [PATTERN(7): Factory; DOMAIN(8): PluginCreation]
# END_CONTRACT

def create_match_notifier_plugin(config: Optional[Dict[str, Any]] = None) -> MatchNotifierPlugin:
    """
    Фабричная функция для создания плагина уведомлений о совпадениях.
    
    Args:
        config: Конфигурация плагина (опционально)
        
    Returns:
        Экземпляр MatchNotifierPlugin
    """
    logger.info(f"[create_match_notifier_plugin][ConditionCheck] Создание плагина уведомлений [ATTEMPT]")
    plugin = MatchNotifierPlugin(config=config)
    logger.info(f"[create_match_notifier_plugin][StepComplete] Плагин создан: {plugin} [SUCCESS]")
    return plugin

# END_FUNCTION_CREATE_MATCH_NOTIFIER_PLUGIN

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
        "name": "match_notifier",
        "priority": 25,
        "enabled": True,
        "config": NotifierConfig().to_dict(),
    }

# END_FUNCTION_GET_DEFAULT_CONFIG

# ============================================================================
# ЭКСПОРТ
# ============================================================================

__all__ = [
    # Классы
    "MatchNotifierPlugin",
    "MatchInfo",
    "NotifierConfig",
    # Функции
    "create_match_notifier_plugin",
    "get_default_config",
    # Константы
    "MAX_MATCH_HISTORY",
    "DEFAULT_NOTIFICATION_COOLDOWN",
    "SUPPORTED_NOTIFICATION_TYPES",
    "MATCH_SEVERITY",
]

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ ПРИ ИМПОРТЕ
# ============================================================================

logger.info(f"[INIT] Модуль match_notifier_wrapper.py загружен, C++ модуль доступен: {_get_cpp_module_info().get('available', False)} [INFO]")
