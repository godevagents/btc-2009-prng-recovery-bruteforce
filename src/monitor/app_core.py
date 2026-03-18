# FILE: src/monitor/app_core.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Ядро приложения мониторинга. Управляет плагинами, жизненным циклом и координирует работу UI и обработчиков событий.
# SCOPE: управление плагинами, состояние приложения, lifecycle, polling
# INPUT: UIBuilder и EventHandlerRegistry через dependency injection
# OUTPUT: Классы: GradioMonitorAppCore, PluginManager
# KEYWORDS: [DOMAIN(9): Core; DOMAIN(8): Application; CONCEPT(7): PluginManagement; CONCEPT(6): StateMachine; TECH(6): Lifecycle]
# LINKS: [IMPORTS(8): src.monitor.factories; IMPORTS(7): src.monitor.integrations; USES(7): UIBuilder; USES(7): EventHandlerRegistry]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 9 [Ядро приложения мониторинга] => GradioMonitorAppCore
# CLASS 8 [Менеджер плагинов мониторинга] => PluginManager
# METHOD 7 [Установка этапа работы] => set_stage
# METHOD 8 [Запуск генерации] => start_generation
# METHOD 8 [Остановка генерации] => stop_generation
# METHOD 7 [Сброс состояния] => reset
# METHOD 6 [Запуск polling] => start_polling
# METHOD 6 [Остановка polling] => stop_polling
# METHOD 7 [Цикл polling] => _polling_loop
# METHOD 8 [Запуск приложения] => run
# CONST 4 [Этап: Выбор списка] => STAGE_1
# CONST 4 [Этап: Генерация] => STAGE_2
# CONST 4 [Этап: Завершено] => STAGE_3
# CONST 4 [Этап: Ожидание] => STAGE_4
# END_MODULE_MAP
# START_USE_CASES:
# - [run]: System (Startup) -> LaunchApplication -> GradioInterfaceDisplayed
# - [start_generation]: User (ClickStart) -> LaunchGenerator -> GenerationRunning
# - [stop_generation]: User (ClickStop) -> StopGenerator -> StatisticsCollected
# - [reset]: User (ClickReset) -> ResetState -> InitialStateRestored
# END_USE_CASES

"""
Модуль app_core.py — Ядро приложения мониторинга.
Содержит классы GradioMonitorAppCore и PluginManager.
"""

# START_BLOCK_IMPORT_MODULES: [Импорт необходимых модулей]
import logging
import os
import sys
import threading
from typing import Any, Callable, Dict, List, Optional

# Импорт из factories для PluginFactory
from src.monitor.factories.plugin_factory import PluginFactory, PluginCreationError
from src.monitor.factories import PluginConfig, PluginType

# Импорт флага доступности C++ модулей
from src.monitor import CPP_AVAILABLE

# Импорт плагинов
from src.monitor.plugins.list_selector import ListSelectorPlugin
from src.monitor.plugins import LiveStatsPlugin, MatchNotifierPlugin, FinalStatsPlugin

# Импорт остальных модулей
try:
    from src.monitor._cpp.metrics_wrapper import MetricsStore
except ImportError:
    from src.monitor.metrics import MetricsStore

try:
    from src.monitor._cpp.plugin_base_wrapper import BaseMonitorPlugin
except ImportError:
    from src.monitor.plugins.base import BaseMonitorPlugin

from src.monitor.integrations.launch_integration import LaunchIntegration
from src.monitor.ui.themes import get_monitor_theme, get_all_css
from src.monitor.utils.signal_handler import SignalHandler

logger = logging.getLogger(__name__)
# END_BLOCK_IMPORT_MODULES


# START_CLASS_PluginManager
# START_CONTRACT:
# PURPOSE: Менеджер плагинов мониторинга. Управляет регистрацией, получением и уведомлением плагинов о событиях.
# ATTRIBUTES:
# - _plugins: Dict[str, BaseMonitorPlugin] — словарь зарегистрированных плагинов
# - _app: Optional[Any] — ссылка на главное приложение
# METHODS:
# - Регистрация плагина => register_plugin
# - Получение плагина => get_plugin
# - Получение всех плагинов => get_all_plugins
# - Диспетчеризация событий => dispatch_event
# - Установка приложения => set_app
# KEYWORDS: [PATTERN(8): Manager; DOMAIN(9): PluginManagement; CONCEPT(7): EventBus; TECH(6): Observer]
# END_CONTRACT

class PluginManager:
    """
    [Менеджер плагинов мониторинга. Управляет регистрацией, получением и уведомлением плагинов.]
    """

    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация менеджера плагинов.
    # KEYWORDS: [CONCEPT(5): Initialization]
    # END_CONTRACT

    def __init__(self) -> None:
        self._plugins: Dict[str, BaseMonitorPlugin] = {}
        self._app: Optional[Any] = None
        logger.debug(f"[PluginManager][INIT] Менеджер плагинов инициализирован")

    # END_METHOD___init__

    # START_METHOD_register_plugin
    # START_CONTRACT:
    # PURPOSE: Регистрация плагина мониторинга в системе.
    # INPUTS:
    # - plugin: BaseMonitorPlugin — экземпляр плагина для регистрации
    # OUTPUTS: None
    # KEYWORDS: [PATTERN(7): Registry; CONCEPT(6): PluginLoading]
    # END_CONTRACT

    def register_plugin(self, plugin: BaseMonitorPlugin) -> None:
        if plugin.name in self._plugins:
            logger.warning(f"[PluginManager][REGISTER_PLUGIN] Плагин {plugin.name} уже зарегистрирован")
            return

        plugin.initialize(self._app)
        self._plugins[plugin.name] = plugin
        logger.info(f"[PluginManager][REGISTER_PLUGIN] Плагин зарегистрирован: {plugin.name}")

    # END_METHOD_register_plugin

    # START_METHOD_get_plugin
    # START_CONTRACT:
    # PURPOSE: Получение плагина по имени.
    # INPUTS:
    # - name: str — имя зарегистрированного плагина
    # OUTPUTS:
    # - Optional[BaseMonitorPlugin] — экземпляр плагина или None
    # KEYWORDS: [CONCEPT(5): Lookup]
    # END_CONTRACT

    def get_plugin(self, name: str) -> Optional[BaseMonitorPlugin]:
        return self._plugins.get(name)

    # END_METHOD_get_plugin

    # START_METHOD_get_all_plugins
    # START_CONTRACT:
    # PURPOSE: Получение всех зарегистрированных плагинов.
    # INPUTS: None
    # OUTPUTS:
    # - List[BaseMonitorPlugin] — список всех плагинов
    # KEYWORDS: [CONCEPT(5): Enumeration]
    # END_CONTRACT

    def get_all_plugins(self) -> List[BaseMonitorPlugin]:
        return list(self._plugins.values())

    # END_METHOD_get_all_plugins

    # START_METHOD_dispatch_event
    # START_CONTRACT:
    # PURPOSE: Уведомление всех зарегистрированных плагинов о событии.
    # INPUTS:
    # - event_name: str — имя события
    # - *args, **kwargs — аргументы для передачи в метод плагина
    # OUTPUTS: None
    # KEYWORDS: [PATTERN(8): EventBus; CONCEPT(7): PubSub]
    # END_CONTRACT

    def dispatch_event(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        for plugin in self._plugins.values():
            try:
                method = getattr(plugin, event_name, None)
                if method and callable(method):
                    method(*args, **kwargs)
            except Exception as e:
                logger.error(f"[PluginManager][DISPATCH_EVENT] Ошибка в плагине {plugin.name}: {e}")

    # END_METHOD_dispatch_event

    # START_METHOD_set_app
    # START_CONTRACT:
    # PURPOSE: Установка ссылки на главное приложение для всех плагинов.
    # INPUTS:
    # - app: Any — главное приложение
    # OUTPUTS: None
    # KEYWORDS: [CONCEPT(6): DependencyInjection]
    # END_CONTRACT

    def set_app(self, app: Any) -> None:
        self._app = app
        for plugin in self._plugins.values():
            plugin.initialize(app)

    # END_METHOD_set_app


# END_CLASS_PluginManager


# START_CLASS_GradioMonitorAppCore
# START_CONTRACT:
# PURPOSE: Ядро приложения мониторинга. Управляет состоянием, жизненным циклом, плагинами и координацией UI и обработчиков.
# ATTRIBUTES:
# - metrics_store: MetricsStore — хранилище метрик
# - plugin_manager: PluginManager — менеджер плагинов
# - launch_integration: Optional[LaunchIntegration] — интеграция с лаунчером
# - current_stage: str — текущий этап работы
# - is_running: bool — флаг запуска генератора
# - interface: Optional — Gradio-интерфейс
# - signal_handler: SignalHandler — обработчик сигналов
# - use_cpp: bool — использовать C++ плагины
# METHODS:
# - Управление этапами => set_stage
# - Запуск генерации => start_generation
# - Остановка генерации => stop_generation
# - Сброс => reset
# - Polling => start_polling, stop_polling, _polling_loop
# - Запуск => run
# KEYWORDS: [PATTERN(9): Application; DOMAIN(9): Core; CONCEPT(8): StateMachine; TECH(7): Threading]
# END_CONTRACT

class GradioMonitorAppCore:
    """
    [Ядро приложения мониторинга.]
    """

    # Константы этапов работы
    STAGE_1 = "SELECTING_LIST"   # Выбор списка адресов
    STAGE_2 = "GENERATING"       # Генерация кошельков
    STAGE_3 = "FINISHED"         # Генерация завершена
    STAGE_4 = "IDLE"             # Ожидание нового запуска

    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация ядра приложения с параметрами и компонентами.
    # INPUTS:
    # - ui_builder: UIBuilder — строитель UI
    # - event_registry: EventHandlerRegistry — реестр обработчиков
    # - share: bool — создать публичную ссылку
    # - server_name: str — IP сервера
    # - server_port: int — порт сервера
    # KEYWORDS: [CONCEPT(6): Initialization; TECH(5): DependencyInjection]
    # END_CONTRACT

    def __init__(
        self,
        ui_builder,
        event_registry,
        share: bool = False,
        server_name: str = "127.0.0.1",
        server_port: int = 7860,
    ) -> None:
        # Параметры сервера
        self.share = share
        self.server_name = server_name
        self.server_port = server_port

        # Использование C++ плагинов
        self.use_cpp = True

        logger.info(f"[GradioMonitorAppCore][INIT] Инициализация с use_cpp={self.use_cpp}")

        # Основные компоненты
        self.metrics_store = MetricsStore()
        self.plugin_manager = PluginManager()
        self.launch_integration: Optional[LaunchIntegration] = None

        # Фабрика плагинов
        self._plugin_factory = PluginFactory.get_instance()
        self._plugin_factory.set_default_use_cpp(self.use_cpp)

        # Состояние
        self.current_stage = self.STAGE_1
        self.is_running = False
        self.list_confirmed = False
        self._polling_thread: Optional[threading.Thread] = None
        self._stop_polling = threading.Event()

        # UI компоненты (через builder)
        self._ui_builder = ui_builder
        self._event_registry = event_registry

        # Передаём event_registry в UIBuilder
        self._ui_builder._event_registry = event_registry

        self.interface = None

        # Сигнал-обработчик
        self.signal_handler = SignalHandler()

        # Инициализация плагинов
        self._init_plugins()

        # Регистрация shutdown callback
        self.signal_handler.register_shutdown_callback(self._on_shutdown_signal)

        logger.info(f"[GradioMonitorAppCore][INIT] Ядро приложения инициализировано")

    # END_METHOD___init__

    # START_METHOD__init_plugins
    # START_CONTRACT:
    # PURPOSE: Инициализация всех плагинов мониторинга через PluginFactory.
    # INPUTS: None
    # OUTPUTS: None
    # KEYWORDS: [CONCEPT(6): PluginLoading]
    # END_CONTRACT

    def _init_plugins(self) -> None:
        logger.info(f"[GradioMonitorAppCore][INIT_PLUGINS] Использование C++ плагинов: {self.use_cpp}")

        # ListSelectorPlugin создаётся напрямую (Python-only)
        list_selector = ListSelectorPlugin()
        self.plugin_manager.register_plugin(list_selector)
        logger.info(f"[GradioMonitorAppCore][INIT_PLUGINS] Зарегистрирован плагин: list_selector (Python)")

        # LiveStatsPlugin через фабрику
        try:
            live_stats = self._plugin_factory.create_live_stats("live_stats", use_cpp=self.use_cpp)
            self.plugin_manager.register_plugin(live_stats)
            logger.info(f"[GradioMonitorAppCore][INIT_PLUGINS] Зарегистрирован плагин: live_stats")
        except PluginCreationError as e:
            logger.error(f"[GradioMonitorAppCore][INIT_PLUGINS] Ошибка создания live_stats: {e}")
            live_stats = LiveStatsPlugin()
            self.plugin_manager.register_plugin(live_stats)
            logger.warning(f"[GradioMonitorAppCore][INIT_PLUGINS] Использован fallback плагин live_stats (Python)")

        # MatchNotifierPlugin через фабрику
        try:
            match_notifier = self._plugin_factory.create_match_notifier("match_notifier", use_cpp=self.use_cpp)
            self.plugin_manager.register_plugin(match_notifier)
            logger.info(f"[GradioMonitorAppCore][INIT_PLUGINS] Зарегистрирован плагин: match_notifier")
        except PluginCreationError as e:
            logger.error(f"[GradioMonitorAppCore][INIT_PLUGINS] Ошибка создания match_notifier: {e}")
            match_notifier = MatchNotifierPlugin()
            self.plugin_manager.register_plugin(match_notifier)
            logger.warning(f"[GradioMonitorAppCore][INIT_PLUGINS] Использован fallback плагин match_notifier (Python)")

        # FinalStatsPlugin через фабрику
        try:
            final_stats = self._plugin_factory.create_final_stats("final_stats", use_cpp=self.use_cpp)
            self.plugin_manager.register_plugin(final_stats)
            logger.info(f"[GradioMonitorAppCore][INIT_PLUGINS] Зарегистрирован плагин: final_stats")
        except PluginCreationError as e:
            logger.error(f"[GradioMonitorAppCore][INIT_PLUGINS] Ошибка создания final_stats: {e}")
            final_stats = FinalStatsPlugin()
            self.plugin_manager.register_plugin(final_stats)
            logger.warning(f"[GradioMonitorAppCore][INIT_PLUGINS] Использован fallback плагин final_stats (Python)")

        logger.info(f"[GradioMonitorAppCore][INIT_PLUGINS] Зарегистрировано 4 плагина")

    # END_METHOD__init_plugins

    # START_METHOD_set_stage
    # START_CONTRACT:
    # PURPOSE: Установка текущего этапа работы.
    # INPUTS:
    # - stage: str — идентификатор этапа
    # OUTPUTS: None
    # KEYWORDS: [CONCEPT(5): StateManagement]
    # END_CONTRACT

    def set_stage(self, stage: str) -> None:
        """Установка текущего этапа."""
        self.current_stage = stage
        logger.info(f"[GradioMonitorAppCore][SET_STAGE] Установлен этап: {stage}")

    # END_METHOD_set_stage

    # START_METHOD_start_generation
    # START_CONTRACT:
    # PURPOSE: Запуск генератора кошельков.
    # INPUTS:
    # - list_path: str — путь к списку адресов
    # OUTPUTS:
    # - bool — успешность запуска
    # KEYWORDS: [CONCEPT(6): GeneratorLaunch; TECH(5): LaunchIntegration]
    # END_CONTRACT

    def start_generation(self, list_path: str) -> bool:
        """Запуск генератора кошельков."""
        self.launch_integration = LaunchIntegration()

        # Настройка callback для совпадений
        match_notifier = self.plugin_manager.get_plugin("match_notifier")
        if match_notifier and self.launch_integration:
            def on_match_callback(match_data: Dict[str, Any]) -> None:
                match_notifier.on_match_event(match_data)

            self.launch_integration.set_on_match_callback(on_match_callback)

        # Настройка callback для остановки
        if self.launch_integration:
            self.launch_integration.set_on_stop_callback(self._on_generation_stop)

        success = self.launch_integration.start_launcher(list_path)
        return success

    # END_METHOD_start_generation

    # START_METHOD_stop_generation
    # START_CONTRACT:
    # PURPOSE: Остановка генератора и сбор статистики.
    # INPUTS: None
    # OUTPUTS: None
    # KEYWORDS: [CONCEPT(6): GeneratorStop; TECH(5): Cleanup]
    # END_CONTRACT

    def stop_generation(self) -> None:
        """Остановка генератора."""
        logger.info(f"[GradioMonitorAppCore][STOP_GENERATION] Остановка генератора")

        # Остановка polling
        self._stop_polling.set()
        if self._polling_thread and self._polling_thread.is_alive():
            self._polling_thread.join(timeout=5)

        # Остановка генератора
        if self.launch_integration:
            self.launch_integration.stop_launcher()

        # Уведомление плагинов
        self.plugin_manager.dispatch_event("on_shutdown")

    # END_METHOD_stop_generation

    # START_METHOD_reset
    # START_CONTRACT:
    # PURPOSE: Полный сброс состояния мониторинга.
    # INPUTS: None
    # OUTPUTS: None
    # KEYWORDS: [CONCEPT(6): Reset; TECH(5): StateManagement]
    # END_CONTRACT

    def reset(self) -> None:
        """Полный сброс состояния."""
        logger.info(f"[GradioMonitorAppCore][RESET] Начало сброса")

        # Остановка polling
        self._stop_polling.set()
        if self._polling_thread and self._polling_thread.is_alive():
            self._polling_thread.join(timeout=5)

        # Остановка генератора если запущен
        if self.launch_integration and self.launch_integration.is_running():
            self.launch_integration.stop_launcher()

        # Сброс интеграции
        if self.launch_integration:
            self.launch_integration.reset()

        # Сброс метрик
        self.metrics_store.reset()

        # Сброс плагинов
        self.plugin_manager.dispatch_event("on_reset")

        # Сброс состояния
        self.is_running = False
        self.list_confirmed = False
        self.current_stage = self.STAGE_1

        logger.info(f"[GradioMonitorAppCore][RESET] Сброс завершён")

    # END_METHOD_reset

    # START_METHOD_start_polling
    # START_CONTRACT:
    # PURPOSE: Запуск фонового потока для опроса метрик.
    # INPUTS: None
    # OUTPUTS: None
    # KEYWORDS: [CONCEPT(7): Polling; TECH(6): Threading]
    # END_CONTRACT

    def start_polling(self) -> None:
        """Запуск polling потока."""
        self._stop_polling.clear()
        self._polling_thread = threading.Thread(
            target=self._polling_loop,
            name="MetricsPollingThread",
            daemon=True,
        )
        self._polling_thread.start()
        logger.debug(f"[GradioMonitorAppCore][START_POLLING] Polling запущен")

    # END_METHOD_start_polling

    # START_METHOD_stop_polling
    # START_CONTRACT:
    # PURPOSE: Остановка фонового потока опроса метрик.
    # INPUTS: None
    # OUTPUTS: None
    # KEYWORDS: [CONCEPT(6): PollingStop; TECH(5): Threading]
    # END_CONTRACT

    def stop_polling(self) -> None:
        """Остановка polling потока."""
        self._stop_polling.set()
        if self._polling_thread and self._polling_thread.is_alive():
            self._polling_thread.join(timeout=5)
        logger.debug(f"[GradioMonitorAppCore][STOP_POLLING] Polling остановлен")

    # END_METHOD_stop_polling

    # START_METHOD__polling_loop
    # START_CONTRACT:
    # PURPOSE: Цикл polling для периодического обновления метрик.
    # INPUTS: None
    # OUTPUTS: None
    # KEYWORDS: [PATTERN(8): Loop; CONCEPT(7): Polling]
    # END_CONTRACT

    def _polling_loop(self) -> None:
        """Цикл polling для обновления метрик."""
        while not self._stop_polling.is_set():
            try:
                if self.launch_integration:
                    metrics = self.launch_integration.get_current_metrics()
                    if metrics:
                        self.metrics_store.update(metrics)
                        self.plugin_manager.dispatch_event("on_metric_update", metrics)

                self._stop_polling.wait(1.0)

            except Exception as e:
                logger.error(f"[GradioMonitorAppCore][POLLING_LOOP] Ошибка: {e}")
                self._stop_polling.wait(2.0)

        logger.debug(f"[GradioMonitorAppCore][POLLING_LOOP] Polling завершён")

    # END_METHOD__polling_loop

    # START_METHOD__on_generation_stop
    # START_CONTRACT:
    # PURPOSE: Callback при остановке генератора.
    # INPUTS:
    # - final_metrics: Dict[str, Any] — финальные метрики
    # OUTPUTS: None
    # KEYWORDS: [PATTERN(8): Callback; CONCEPT(7): FinalStats]
    # END_CONTRACT

    def _on_generation_stop(self, final_metrics: Dict[str, Any]) -> None:
        """Callback при остановке генератора."""
        logger.info(f"[GradioMonitorAppCore][ON_GENERATION_STOP] Получены финальные метрики")

        final_stats = self.plugin_manager.get_plugin("final_stats")
        if final_stats:
            final_stats.on_finish(final_metrics)
            logger.info(f"[GradioMonitorAppCore][ON_GENERATION_STOP] Финальные метрики сохранены")

    # END_METHOD__on_generation_stop

    # START_METHOD__on_shutdown_signal
    # START_CONTRACT:
    # PURPOSE: Обработчик системного сигнала shutdown.
    # INPUTS: None
    # OUTPUTS: None
    # KEYWORDS: [PATTERN(8): SignalHandler; CONCEPT(7): Cleanup]
    # END_CONTRACT

    def _on_shutdown_signal(self) -> None:
        """Обработчик сигнала shutdown."""
        logger.info(f"[GradioMonitorAppCore][ON_SHUTDOWN] Получен сигнал shutdown")

        if self.is_running:
            self.stop_generation()

        logger.info(f"[GradioMonitorAppCore][ON_SHUTDOWN] Shutdown завершён")

    # END_METHOD__on_shutdown_signal

    # START_METHOD_run
    # START_CONTRACT:
    # PURPOSE: Запуск Gradio сервера мониторинга.
    # INPUTS: None
    # OUTPUTS: None
    # KEYWORDS: [PATTERN(9): Server; TECH(8): Gradio]
    # END_CONTRACT

    def run(self) -> None:
        """Запуск Gradio сервера."""
        logger.info(f"[GradioMonitorAppCore][RUN] Запуск приложения")

        # Построение интерфейса через UIBuilder
        self.interface = self._ui_builder.build(self)

        if not self.interface:
            logger.error(f"[GradioMonitorAppCore][RUN] Интерфейс не построен")
            return

        # Запуск Gradio
        try:
            # Добавляем CSS для скрытия footer "Created with Gradio"
            custom_css = get_all_css() + """
            .gradio-footer {display: none !important;}
            .footer {display: none !important;}
            """
            self.interface.launch(
                server_name=self.server_name,
                server_port=self.server_port,
                share=False,              # Закомментировано: убрать кнопку "использовать через api"
                inbrowser=True,
                theme=get_monitor_theme(),
                css=custom_css,
            )
        except Exception as e:
            logger.error(f"[GradioMonitorAppCore][RUN] Ошибка запуска: {e}")
            raise

    # END_METHOD_run

    # START_METHOD_close_app
    # START_CONTRACT:
    # PURPOSE: Закрытие приложения (аналог Ctrl+C). Останавливает генератор и завершает приложение.
    # INPUTS: None
    # OUTPUTS: None
    # KEYWORDS: [PATTERN(8): Shutdown; CONCEPT(7): Cleanup; TECH(5): Process]
    # END_CONTRACT

    def close_app(self) -> None:
        """Закрытие приложения (аналог Ctrl+C)."""
        logger.info(f"[GradioMonitorAppCore][CLOSE_APP] Начало закрытия приложения")
        
        # Остановка генератора если запущен
        if self.is_running:
            logger.info(f"[GradioMonitorAppCore][CLOSE_APP] Остановка генератора перед закрытием")
            self.stop_generation()
        
        # Остановка polling
        self.stop_polling()
        
        logger.info(f"[GradioMonitorAppCore][CLOSE_APP] Завершение приложения")
        # Завершаем приложение как при Ctrl+C
        os._exit(0)

    # END_METHOD_close_app

    # START_METHOD_get_metrics_store
    # START_CONTRACT:
    # PURPOSE: Получение хранилища метрик.
    # INPUTS: None
    # OUTPUTS:
    # - MetricsStore — хранилище метрик
    # KEYWORDS: [CONCEPT(5): Accessor; TECH(4): Metrics]
    # END_CONTRACT

    def get_metrics_store(self) -> MetricsStore:
        """Получение хранилища метрик."""
        return self.metrics_store

    # END_METHOD_get_metrics_store


# END_CLASS_GradioMonitorAppCore
