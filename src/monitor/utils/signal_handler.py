# FILE: src/monitor/utils/signal_handler.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Модуль обработки сигналов. Обеспечивает корректное завершение работы приложения при получении сигналов SIGINT/SIGTERM (Ctrl+C, системный сигнал завершения).
# SCOPE: Обработка сигналов, graceful shutdown, callbacks
# INPUT: Нет (модуль предоставляет функции и классы)
# OUTPUT: Класс SignalHandler, класс SignalContext, функции setup_signal_handler, get_global_handler, create_graceful_shutdown, default_shutdown_handler
# KEYWORDS: DOMAIN(9): Signal Handling; DOMAIN(8): Graceful Shutdown; DOMAIN(7): Callbacks; CONCEPT(6): Unix Signals; TECH(5): Python
# LINKS: [USES(6): signal_module; USES(5): threading_module]
# LINKS_TO_SPECIFICATION: Требования к обработке сигналов из dev_plan_signal_handler.md
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 10 [Основной обработчик сигналов для graceful shutdown] => SignalHandler
# METHOD 9 [Инициализация обработчика] => SignalHandler.__init__
# METHOD 8 [Настройка обработчиков SIGINT/SIGTERM] => SignalHandler._setup_signal_handlers
# METHOD 9 [Обработка полученного сигнала] => SignalHandler._handle_signal
# METHOD 8 [Вызов shutdown callbacks] => SignalHandler._invoke_shutdown_callbacks
# METHOD 7 [Восстановление оригинальных обработчиков] => SignalHandler._restore_original_handlers
# METHOD 7 [Регистрация shutdown callback] => SignalHandler.register_shutdown_callback
# METHOD 7 [Удаление shutdown callback] => SignalHandler.unregister_shutdown_callback
# METHOD 6 [Получение списка callbacks] => SignalHandler.get_shutdown_callbacks
# METHOD 6 [Проверка состояния завершения] => SignalHandler.is_shutting_down
# METHOD 6 [Получение полученного сигнала] => SignalHandler.get_received_signal
# METHOD 6 [Сброс состояния] => SignalHandler.reset
# METHOD 6 [Очистка callbacks] => SignalHandler.clear_callbacks
# FUNC 9 [Фабрика для создания обработчика с callback] => create_graceful_shutdown
# FUNC 8 [Создание стандартного shutdown handler] => default_shutdown_handler
# CLASS 8 [Контекстный менеджер для работы с сигналами] => SignalContext
# FUNC 9 [Установка глобального обработчика] => setup_signal_handler
# FUNC 7 [Получение глобального обработчика] => get_global_handler
# END_MODULE_MAP
# START_USE_CASES:
# - [SignalHandler._handle_signal]: System (Shutdown) -> ReceiveSignal -> InvokeCallbacks
# - [setup_signal_handler]: MonitorApp (Startup) -> InstallSignalHandlers -> HandlersActive
# - [create_graceful_shutdown]: MonitorApp (Startup) -> CreateHandler -> HandlerReady
# - [SignalContext]: MonitorApp (Context) -> ManageSignalContext -> ContextManaged
# END_USE_CASES
# За описанием заголовка идет секция импорта

import logging
import signal
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Настройка логирования с FileHandler
def _setup_logger():
    """Настройка логгера модуля с файловым обработчиком."""
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        # FileHandler для записи в app.log
        log_file = Path(__file__).parent.parent.parent / "app.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s] %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger

logger = _setup_logger()
logger.debug(f"[ModuleInit][utils/signal_handler][SetupLogger] Логгер модуля signal_handler инициализирован [SUCCESS]")


# START_CLASS_SIGNAL_HANDLER
# START_CONTRACT:
# PURPOSE: Основной класс обработчика сигналов для graceful shutdown. Перехватывает SIGINT и SIGTERM, вызывает зарегистрированные callbacks при завершении работы.
# ATTRIBUTES:
# - _original_handlers: Dict[signal.Signals, signal.Handler] — сохранённые оригинальные обработчики
# - _shutdown_callbacks: List[Callable] — список callbacks для вызова при shutdown
# - _is_shutting_down: bool — флаг процесса завершения
# - _lock: threading.Lock — блокировка для thread-safety
# - _signal_received: Optional[signal.Signals] — полученный сигнал
# METHODS:
# - __init__(): Инициализация и установка обработчиков
# - _setup_signal_handlers(): Настройка обработчиков SIGINT/SIGTERM
# - _handle_signal(): Обработка полученного сигнала
# - _invoke_shutdown_callbacks(): Вызов всех зарегистрированных callbacks
# - _restore_original_handlers(): Восстановление оригинальных обработчиков
# - register_shutdown_callback(): Регистрация callback
# - unregister_shutdown_callback(): Удаление callback
# - get_shutdown_callbacks(): Получение списка callbacks
# - is_shutting_down(): Проверка состояния завершения
# - get_received_signal(): Получение полученного сигнала
# - reset(): Сброс состояния
# - clear_callbacks(): Очистка всех callbacks
# KEYWORDS: DOMAIN(9): Signal Handling; PATTERN(8): Graceful Shutdown; TECH(6): Thread Safety; CONCEPT(5): Callback Management
# LINKS: [CALLS(5): signal.signal]
# END_CONTRACT

class SignalHandler:
    """
    Обработчик сигналов для graceful shutdown.
    Обеспечивает корректное завершение работы при получении SIGINT/SIGTERM.
    """
    
    # START_METHOD___INIT__
    # START_CONTRACT:
    # PURPOSE: Инициализирует обработчик сигналов, устанавливает обработчики для SIGINT/SIGTERM и регистрирует стандартные callbacks.
    # KEYWORDS: CONCEPT(5): Initialization; DOMAIN(7): Signal Handling
    # END_CONTRACT
    def __init__(self) -> None:
        """Инициализация обработчика сигналов."""
        logger.debug(f"[SignalHandler][INIT][InputParams] Нет параметров [ATTEMPT]")
        
        self._original_handlers: Dict[signal.Signals, signal.Handler] = {}
        self._shutdown_callbacks: List[Callable] = []
        self._is_shutting_down: bool = False
        self._lock = threading.Lock()
        self._signal_received: Optional[signal.Signals] = None
        
        # START_BLOCK_SETUP_HANDLERS: [Установка обработчиков сигналов]
        self._setup_signal_handlers()
        # END_BLOCK_SETUP_HANDLERS
        
        logger.debug(f"[SignalHandler][INIT][ConditionCheck] Обработчик сигналов инициализирован [SUCCESS]")
    
    # END_METHOD___INIT__
    
    # START_METHOD_SETUP_SIGNAL_HANDLERS
    # START_CONTRACT:
    # PURPOSE: Устанавливает обработчики для SIGINT и SIGTERM сигналов. Перехватывает Ctrl+C и системные сигналы завершения.
    # KEYWORDS: CONCEPT(5): Signal Setup; DOMAIN(7): Signal Handling
    # END_CONTRACT
    def _setup_signal_handlers(self) -> None:
        """Настройка обработчиков сигналов."""
        logger.debug(f"[SignalHandler][SetupSignalHandlers][InputParams] Установка обработчиков [ATTEMPT]")
        
        # START_BLOCK_SIGINT: [Обработка SIGINT (Ctrl+C)]
        self._original_handlers[signal.SIGINT] = signal.signal(
            signal.SIGINT,
            self._handle_signal
        )
        logger.debug(f"[SignalHandler][SetupSignalHandlers][SetupHandler] SIGINT обработчик установлен [SUCCESS]")
        # END_BLOCK_SIGINT
        
        # START_BLOCK_SIGTERM: [Обработка SIGTERM (системный сигнал)]
        self._original_handlers[signal.SIGTERM] = signal.signal(
            signal.SIGTERM,
            self._handle_signal
        )
        logger.debug(f"[SignalHandler][SetupSignalHandlers][SetupHandler] SIGTERM обработчик установлен [SUCCESS]")
        # END_BLOCK_SIGTERM
        
        # START_BLOCK_SIGHUP: [Игнорирование SIGHUP (закрытие терминала)]
        try:
            self._original_handlers[signal.SIGHUP] = signal.signal(
                signal.SIGHUP,
                signal.SIG_IGN
            )
            logger.debug(f"[SignalHandler][SetupSignalHandlers][SetupHandler] SIGHUP игнорируется [SUCCESS]")
        except (AttributeError, OSError):
            # SIGHUP может отсутствовать на некоторых платформах
            logger.warning(f"[SignalHandler][SetupSignalHandlers][ConditionCheck] SIGHUP недоступен на этой платформе [FAIL]")
        # END_BLOCK_SIGHUP
        
        logger.info(f"[SignalHandler][SetupSignalHandlers][StepComplete] Обработчики сигналов установлены [SUCCESS]")
    
    # END_METHOD_SETUP_SIGNAL_HANDLERS
    
    # START_METHOD_HANDLE_SIGNAL
    # START_CONTRACT:
    # PURPOSE: Обрабатывает полученный сигнал, вызывает shutdown callbacks, восстанавливает оригинальные обработчики и завершает приложение.
    # INPUTS:
    # - signum: signal.Signals — номер сигнала
    # - frame: Any — стек вызовов
    # KEYWORDS: CONCEPT(5): Signal Handling; DOMAIN(7): Shutdown
    # END_CONTRACT
    def _handle_signal(self, signum: signal.Signals, frame: Any) -> None:
        """Обработка полученного сигнала."""
        logger.debug(f"[SignalHandler][HandleSignal][InputParams] signum={signum} [ATTEMPT]")
        
        # START_BLOCK_CHECK_STATE: [Проверка состояния завершения]
        with self._lock:
            if self._is_shutting_down:
                logger.warning(f"[SignalHandler][HandleSignal][ConditionCheck] Повторный сигнал получен, игнорируем [FAIL]")
                return
            
            self._is_shutting_down = True
            self._signal_received = signum
        # END_BLOCK_CHECK_STATE
        
        # START_BLOCK_LOG_SIGNAL: [Логирование сигнала]
        signal_name = signal.Signals(signum).name
        logger.warning(f"[SignalHandler][HandleSignal][Warning] Получен сигнал: {signal_name} [INFO]")
        # END_BLOCK_LOG_SIGNAL
        
        # START_BLOCK_INVOKE_CALLBACKS: [Вызов shutdown callbacks]
        self._invoke_shutdown_callbacks()
        # END_BLOCK_INVOKE_CALLBACKS
        
        # START_BLOCK_RESTORE_HANDLERS: [Восстановление обработчиков]
        self._restore_original_handlers()
        # END_BLOCK_RESTORE_HANDLERS
        
        # START_BLOCK_EXIT: [Завершение работы приложения]
        logger.info(f"[SignalHandler][HandleSignal][StepComplete] Завершение работы приложения [SUCCESS]")
        
        # Принудительный выход с кодом 130 (Ctrl+C) или 1 (SIGTERM)
        if signum == signal.SIGINT:
            sys.exit(130)
        else:
            sys.exit(1)
        # END_BLOCK_EXIT
    
    # END_METHOD_HANDLE_SIGNAL
    
    # START_METHOD_INVOKE_SHUTDOWN_CALLBACKS
    # START_CONTRACT:
    # PURPOSE: Последовательно вызывает все зарегистрированные shutdown callbacks для корректного завершения работы компонентов.
    # KEYWORDS: CONCEPT(5): Callback Invocation; DOMAIN(7): Shutdown
    # END_CONTRACT
    def _invoke_shutdown_callbacks(self) -> None:
        """Вызов всех зарегистрированных shutdown callbacks."""
        logger.debug(f"[SignalHandler][InvokeCallbacks][InputParams] Кол-во callbacks={len(self._shutdown_callbacks)} [ATTEMPT]")
        
        logger.info(f"[SignalHandler][InvokeCallbacks][Info] Вызов {len(self._shutdown_callbacks)} callbacks [INFO]")
        
        # START_BLOCK_EXECUTE_CALLBACKS: [Выполнение каждого callback]
        for i, callback in enumerate(self._shutdown_callbacks):
            try:
                logger.debug(f"[SignalHandler][InvokeCallbacks][CallExternal] Callback {i + 1}/{len(self._shutdown_callbacks)} [ATTEMPT]")
                callback()
                logger.debug(f"[SignalHandler][InvokeCallbacks][CallExternal] Callback {i + 1} выполнен [SUCCESS]")
            except Exception as e:
                logger.error(f"[SignalHandler][InvokeCallbacks][ExceptionCaught] Ошибка в callback {i + 1}: {e} [ERROR_STATE]")
        # END_BLOCK_EXECUTE_CALLBACKS
        
        logger.info(f"[SignalHandler][InvokeCallbacks][StepComplete] Все callbacks выполнены [SUCCESS]")
    
    # END_METHOD_INVOKE_SHUTDOWN_CALLBACKS
    
    # START_METHOD_RESTORE_ORIGINAL_HANDLERS
    # START_CONTRACT:
    # PURPOSE: Восстанавливает оригинальные обработчики сигналов системы после завершения работы.
    # KEYWORDS: CONCEPT(5): Handler Restoration; DOMAIN(7): Signal Handling
    # END_CONTRACT
    def _restore_original_handlers(self) -> None:
        """Восстановление оригинальных обработчиков сигналов."""
        logger.debug(f"[SignalHandler][RestoreHandlers][InputParams] Восстановление обработчиков [ATTEMPT]")
        
        # START_BLOCK_RESTORE: [Восстановление каждого обработчика]
        for sig, handler in self._original_handlers.items():
            try:
                signal.signal(sig, handler)
                logger.debug(f"[SignalHandler][RestoreHandlers][RestoreHandler] Восстановлен {sig} [SUCCESS]")
            except (OSError, ValueError) as e:
                logger.warning(f"[SignalHandler][RestoreHandlers][ExceptionCaught] Не удалось восстановить {sig}: {e} [FAIL]")
        # END_BLOCK_RESTORE
        
        logger.debug(f"[SignalHandler][RestoreHandlers][StepComplete] Обработчики восстановлены [SUCCESS]")
    
    # END_METHOD_RESTORE_ORIGINAL_HANDLERS
    
    # START_METHOD_REGISTER_SHUTDOWN_CALLBACK
    # START_CONTRACT:
    # PURPOSE: Регистрирует функцию обратного вызова для выполнения при shutdown приложения.
    # INPUTS:
    # - callback: Callable — функция для вызова при завершении
    # KEYWORDS: CONCEPT(5): Registration; DOMAIN(7): Callback
    # END_CONTRACT
    def register_shutdown_callback(self, callback: Callable) -> None:
        """Регистрация callback для shutdown."""
        logger.debug(f"[SignalHandler][RegisterCallback][InputParams] Регистрация callback [ATTEMPT]")
        
        with self._lock:
            if callback not in self._shutdown_callbacks:
                self._shutdown_callbacks.append(callback)
                logger.debug(f"[SignalHandler][RegisterCallback][StepComplete] Callback зарегистрирован [SUCCESS]")
            else:
                logger.warning(f"[SignalHandler][RegisterCallback][ConditionCheck] Callback уже зарегистрирован [FAIL]")
    
    # END_METHOD_REGISTER_SHUTDOWN_CALLBACK
    
    # START_METHOD_UNREGISTER_SHUTDOWN_CALLBACK
    # START_CONTRACT:
    # PURPOSE: Удаляет зарегистрированную функцию обратного вызова из списка callbacks.
    # INPUTS:
    # - callback: Callable — функция для удаления
    # KEYWORDS: CONCEPT(5): Unregistration; DOMAIN(7): Callback
    # END_CONTRACT
    def unregister_shutdown_callback(self, callback: Callable) -> None:
        """Удаление callback для shutdown."""
        logger.debug(f"[SignalHandler][UnregisterCallback][InputParams] Удаление callback [ATTEMPT]")
        
        with self._lock:
            if callback in self._shutdown_callbacks:
                self._shutdown_callbacks.remove(callback)
                logger.debug(f"[SignalHandler][UnregisterCallback][StepComplete] Callback удалён [SUCCESS]")
    
    # END_METHOD_UNREGISTER_SHUTDOWN_CALLBACK
    
    # START_METHOD_GET_SHUTDOWN_CALLBACKS
    # START_CONTRACT:
    # PURPOSE: Возвращает копию списка зарегистрированных shutdown callbacks.
    # OUTPUTS:
    # - List[Callable] — список callbacks
    # KEYWORDS: CONCEPT(5): Enumeration; DOMAIN(7): Callback
    # END_CONTRACT
    def get_shutdown_callbacks(self) -> List[Callable]:
        """Получение списка shutdown callbacks."""
        logger.debug(f"[SignalHandler][GetCallbacks][InputParams] Нет параметров [ATTEMPT]")
        
        return self._shutdown_callbacks.copy()
    
    # END_METHOD_GET_SHUTDOWN_CALLBACKS
    
    # START_METHOD_IS_SHUTTING_DOWN
    # START_CONTRACT:
    # PURPOSE: Возвращает флаг, указывающий идёт ли в данный момент процесс завершения работы.
    # OUTPUTS:
    # - bool — True если идёт завершение
    # KEYWORDS: CONCEPT(5): State Check; DOMAIN(7): Shutdown
    # END_CONTRACT
    def is_shutting_down(self) -> bool:
        """Проверка состояния завершения."""
        logger.debug(f"[SignalHandler][IsShuttingDown][InputParams] Нет параметров [ATTEMPT]")
        
        return self._is_shutting_down
    
    # END_METHOD_IS_SHUTTING_DOWN
    
    # START_METHOD_GET_RECEIVED_SIGNAL
    # START_CONTRACT:
    # PURPOSE: Возвращает сигнал, который был получен и вызвал процесс завершения.
    # OUTPUTS:
    # - Optional[signal.Signals] — сигнал или None
    # KEYWORDS: CONCEPT(5): Signal Retrieval; DOMAIN(7): Signal Handling
    # END_CONTRACT
    def get_received_signal(self) -> Optional[signal.Signals]:
        """Получение полученного сигнала."""
        logger.debug(f"[SignalHandler][GetSignal][InputParams] Нет параметров [ATTEMPT]")
        
        return self._signal_received
    
    # END_METHOD_GET_RECEIVED_SIGNAL
    
    # START_METHOD_RESET
    # START_CONTRACT:
    # PURPOSE: Сбрасывает состояние обработчика для возможности повторного использования после тестирования.
    # KEYWORDS: CONCEPT(5): Reset; DOMAIN(7): State Management
    # END_CONTRACT
    def reset(self) -> None:
        """Сброс состояния обработчика."""
        logger.debug(f"[SignalHandler][Reset][InputParams] Сброс состояния [ATTEMPT]")
        
        with self._lock:
            self._is_shutting_down = False
            self._signal_received = None
        
        logger.debug(f"[SignalHandler][Reset][StepComplete] Состояние сброшено [SUCCESS]")
    
    # END_METHOD_RESET
    
    # START_METHOD_CLEAR_CALLBACKS
    # START_CONTRACT:
    # PURPOSE: Очищает все зарегистрированные shutdown callbacks.
    # KEYWORDS: CONCEPT(5): Cleanup; DOMAIN(7): Callback Management
    # END_CONTRACT
    def clear_callbacks(self) -> None:
        """Очистка всех callbacks."""
        logger.debug(f"[SignalHandler][ClearCallbacks][InputParams] Очистка callbacks [ATTEMPT]")
        
        with self._lock:
            self._shutdown_callbacks.clear()
        
        logger.debug(f"[SignalHandler][ClearCallbacks][StepComplete] Все callbacks очищены [SUCCESS]")
    
    # END_METHOD_CLEAR_CALLBACKS
    
    # START_METHOD___DEL__
    # START_CONTRACT:
    # PURPOSE: Деструктор - восстанавливает оригинальные обработчики при удалении объекта.
    # KEYWORDS: CONCEPT(5): Destructor; DOMAIN(7): Cleanup
    # END_CONTRACT
    def __del__(self) -> None:
        """Деструктор - восстановление обработчиков."""
        logger.debug(f"[SignalHandler][Del][InputParams] Деструктор вызван [ATTEMPT]")
        
        self._restore_original_handlers()


# END_CLASS_SIGNAL_HANDLER


# START_FUNCTION_CREATE_GRACEFUL_SHUTDOWN
# START_CONTRACT:
# PURPOSE: Фабричная функция для создания SignalHandler с опциональным shutdown callback для упрощённого использования.
# INPUTS:
# - on_shutdown: Optional[Callable] — функция для вызова при shutdown
# OUTPUTS:
# - SignalHandler — созданный обработчик
# KEYWORDS: DOMAIN(9): Signal Handling; PATTERN(7): Factory; TECH(5): Simplified API
# LINKS: [CALLS(8): SignalHandler.__init__; CALLS(7): register_shutdown_callback]
# END_CONTRACT

def create_graceful_shutdown(
    on_shutdown: Optional[Callable] = None,
) -> SignalHandler:
    """Фабричная функция для создания обработчика с shutdown callback."""
    logger.debug(f"[create_graceful_shutdown][InputParams] has_callback={on_shutdown is not None} [ATTEMPT]")
    
    # START_BLOCK_CREATE_HANDLER: [Создание обработчика]
    handler = SignalHandler()
    # END_BLOCK_CREATE_HANDLER
    
    # START_BLOCK_REGISTER_CALLBACK: [Регистрация callback если передан]
    if on_shutdown:
        handler.register_shutdown_callback(on_shutdown)
        logger.debug(f"[create_graceful_shutdown][RegisterCallback] Callback зарегистрирован [SUCCESS]")
    # END_BLOCK_REGISTER_CALLBACK
    
    logger.debug(f"[create_graceful_shutdown][ReturnData] Обработчик создан [SUCCESS]")
    
    return handler


# END_FUNCTION_CREATE_GRACEFUL_SHUTDOWN


# START_FUNCTION_DEFAULT_SHUTDOWN_HANDLER
# START_CONTRACT:
# PURPOSE: Создаёт стандартный shutdown handler для мониторинга, который останавливает мониторинг, генератор, сохраняет состояние и закрывает соединения.
# INPUTS:
# - components: Dict[str, Any] — словарь компонентов для завершения (monitor, launcher, state, database)
# OUTPUTS:
# - Callable — функция shutdown
# KEYWORDS: DOMAIN(9): Shutdown; PATTERN(7): Default Handler; TECH(5): Components Management
# LINKS: [CALLS(5): None]
# END_CONTRACT

def default_shutdown_handler(
    components: Dict[str, Any],
) -> Callable:
    """Создание стандартного shutdown handler для мониторинга."""
    logger.debug(f"[default_shutdown_handler][InputParams] components={list(components.keys())} [ATTEMPT]")
    
    # START_BLOCK_CREATE_SHUTDOWN_FUNC: [Создание функции shutdown]
    def shutdown() -> None:
        logger.info(f"[default_shutdown_handler][Execute][Info] Начало graceful shutdown [INFO]")
        
        # START_BLOCK_STOP_MONITOR: [Остановка мониторинга]
        if "monitor" in components:
            try:
                components["monitor"].stop()
                logger.info(f"[default_shutdown_handler][StopMonitor][StepComplete] Мониторинг остановлен [SUCCESS]")
            except Exception as e:
                logger.error(f"[default_shutdown_handler][StopMonitor][ExceptionCaught] Ошибка остановки мониторинга: {e} [ERROR_STATE]")
        # END_BLOCK_STOP_MONITOR
        
        # START_BLOCK_STOP_LAUNCHER: [Остановка генератора]
        if "launcher" in components:
            try:
                components["launcher"].stop()
                logger.info(f"[default_shutdown_handler][StopLauncher][StepComplete] Генератор остановлен [SUCCESS]")
            except Exception as e:
                logger.error(f"[default_shutdown_handler][StopLauncher][ExceptionCaught] Ошибка остановки генератора: {e} [ERROR_STATE]")
        # END_BLOCK_STOP_LAUNCHER
        
        # START_BLOCK_SAVE_STATE: [Сохранение состояния]
        if "state" in components:
            try:
                components["state"].save()
                logger.info(f"[default_shutdown_handler][SaveState][StepComplete] Состояние сохранено [SUCCESS]")
            except Exception as e:
                logger.error(f"[default_shutdown_handler][SaveState][ExceptionCaught] Ошибка сохранения: {e} [ERROR_STATE]")
        # END_BLOCK_SAVE_STATE
        
        # START_BLOCK_CLOSE_CONNECTIONS: [Закрытие соединений]
        if "database" in components:
            try:
                components["database"].close()
                logger.info(f"[default_shutdown_handler][CloseConnections][StepComplete] Соединения закрыты [SUCCESS]")
            except Exception as e:
                logger.error(f"[default_shutdown_handler][CloseConnections][ExceptionCaught] Ошибка закрытия: {e} [ERROR_STATE]")
        # END_BLOCK_CLOSE_CONNECTIONS
        
        logger.info(f"[default_shutdown_handler][Execute][StepComplete] Graceful shutdown завершён [SUCCESS]")
    
    # END_BLOCK_CREATE_SHUTDOWN_FUNC
    
    logger.debug(f"[default_shutdown_handler][ReturnData] Функция shutdown создана [SUCCESS]")
    
    return shutdown


# END_FUNCTION_DEFAULT_SHUTDOWN_HANDLER


# START_CONTEXT_MANAGER_SIGNAL_CONTEXT
# START_CONTRACT:
# PURPOSE: Контекстный менеджер для автоматического управления сигналами. Создаёт SignalHandler при входе в контекст и опционально вызывает callbacks при выходе.
# ATTRIBUTES:
# - _handler: SignalHandler — созданный обработчик
# METHODS:
# - __init__(on_shutdown): Инициализация с опциональным callback
# - __enter__(): Возвращает обработчик при входе в контекст
# - __exit__(): Вызывает callbacks при выходе из контекста
# KEYWORDS: DOMAIN(9): Signal Handling; PATTERN(8): Context Manager; TECH(5): Python
# LINKS: [CALLS(8): create_graceful_shutdown]
# END_CONTRACT

class SignalContext:
    """Контекстный менеджер для работы с сигналами."""
    
    # START_METHOD___INIT__
    # START_CONTRACT:
    # PURPOSE: Инициализирует контекстный менеджер с опциональным shutdown callback.
    # INPUTS:
    # - on_shutdown: Optional[Callable] — callback для shutdown
    # KEYWORDS: CONCEPT(5): Initialization; DOMAIN(7): Context Manager
    # END_CONTRACT
    def __init__(
        self,
        on_shutdown: Optional[Callable] = None,
    ) -> None:
        """Инициализация контекста."""
        logger.debug(f"[SignalContext][INIT][InputParams] has_callback={on_shutdown is not None} [ATTEMPT]")
        
        self._handler = create_graceful_shutdown(on_shutdown)
        
        logger.debug(f"[SignalContext][INIT][StepComplete] Контекст инициализирован [SUCCESS]")
    
    # END_METHOD___INIT__
    
    # START_METHOD___ENTER__
    # START_CONTRACT:
    # PURPOSE: Возвращает SignalHandler при входе в контекст (with block).
    # OUTPUTS:
    # - SignalHandler — обработчик сигналов
    # KEYWORDS: CONCEPT(5): Entry; DOMAIN(7): Context Manager
    # END_CONTRACT
    def __enter__(self) -> SignalHandler:
        """Вход в контекст."""
        logger.debug(f"[SignalContext][Enter][InputParams] Вход в контекст [ATTEMPT]")
        
        return self._handler
    
    # END_METHOD___ENTER__
    
    # START_METHOD___EXIT__
    # START_CONTRACT:
    # PURPOSE: Выполняет shutdown callbacks и восстанавливает обработчики при выходе из контекста.
    # INPUTS:
    # - exc_type: Any — тип исключения
    # - exc_val: Any — значение исключения
    # - exc_tb: Any — traceback
    # KEYWORDS: CONCEPT(5): Exit; DOMAIN(7): Context Manager
    # END_CONTRACT
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Выход из контекста."""
        logger.debug(f"[SignalContext][Exit][InputParams] Выход из контекста [ATTEMPT]")
        
        if self._handler.is_shutting_down():
            self._handler._invoke_shutdown_callbacks()
            self._handler._restore_original_handlers()
            logger.debug(f"[SignalContext][Exit][StepComplete] Callbacks выполнены при выходе [SUCCESS]")


# END_CONTEXT_MANAGER_SIGNAL_CONTEXT


# START_FUNCTION_SETUP_SIGNAL_HANDLER
# START_CONTRACT:
# PURPOSE: Устанавливает глобальный обработчик сигналов для приложения. Позволяет получить доступ к обработчику из любой части кода.
# INPUTS:
# - on_shutdown: Optional[Callable] — callback для shutdown
# OUTPUTS:
# - SignalHandler — созданный обработчик
# KEYWORDS: DOMAIN(9): Signal Handling; PATTERN(7): Global; TECH(5): Singleton Pattern
# LINKS: [CALLS(8): create_graceful_shutdown]
# END_CONTRACT

def setup_signal_handler(
    on_shutdown: Optional[Callable] = None,
) -> SignalHandler:
    """Установка глобального обработчика сигналов."""
    logger.debug(f"[setup_signal_handler][InputParams] has_callback={on_shutdown is not None} [ATTEMPT]")
    
    global _global_signal_handler
    
    # START_BLOCK_CREATE_GLOBAL_HANDLER: [Создание глобального обработчика]
    _global_signal_handler = create_graceful_shutdown(on_shutdown)
    # END_BLOCK_CREATE_GLOBAL_HANDLER
    
    logger.debug(f"[setup_signal_handler][ReturnData] Глобальный обработчик установлен [SUCCESS]")
    
    return _global_signal_handler


# END_FUNCTION_SETUP_SIGNAL_HANDLER


# Глобальный обработчик
_global_signal_handler: Optional[SignalHandler] = None
logger.debug(f"[ModuleInit][utils/signal_handler][CreateGlobal] Глобальная переменная _global_signal_handler создана [SUCCESS]")


# START_FUNCTION_GET_GLOBAL_HANDLER
# START_CONTRACT:
# PURPOSE: Возвращает глобальный обработчик сигналов или None если он не был установлен.
# OUTPUTS:
# - Optional[SignalHandler] — глобальный обработчик
# KEYWORDS: DOMAIN(9): Signal Handling; PATTERN(7): Global; CONCEPT(5): Retrieval
# LINKS: [READS(5): _global_signal_handler]
# END_CONTRACT

def get_global_handler() -> Optional[SignalHandler]:
    """Получение глобального обработчика."""
    logger.debug(f"[get_global_handler][InputParams] Нет параметров [ATTEMPT]")
    
    return _global_signal_handler


# END_FUNCTION_GET_GLOBAL_HANDLER


# Алиас для обратной совместимости (setup_signal_handlers с 's' на конце)
setup_signal_handlers = setup_signal_handler

logger.info(f"[ModuleInit][utils/signal_handler][StepComplete] Модуль signal_handler загружен, определено 2 класса и 5 функций [SUCCESS]")
