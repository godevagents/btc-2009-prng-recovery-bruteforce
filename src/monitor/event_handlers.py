# FILE: src/monitor/event_handlers.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Обработчики событий UI и бизнес-логики мониторинга. Централизует управление событиями в мониторинге через паттерн Registry.
# SCOPE: обработка событий, бизнес-логика, UI события
# INPUT: app_core и ui_builder через dependency injection
# OUTPUT: Классы: EventHandler, EventHandlerRegistry, специализированные обработчики
# KEYWORDS: [DOMAIN(9): EventHandling; CONCEPT(8): Registry; PATTERN(7): Command; TECH(6): DependencyInjection]
# LINKS: [IMPORTS(8): src.monitor.app_core; IMPORTS(7): src.monitor.ui_builder; USES(7): src.monitor.utils.html_generators]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 9 [Базовый класс для обработчиков событий] => EventHandler
# CLASS 8 [Реестр обработчиков событий] => EventHandlerRegistry
# CLASS 7 [Обработчик выбора списка адресов] => ListSelectedHandler
# CLASS 7 [Обработчик изменения Radio] => RadioChangeHandler
# CLASS 8 [Обработчик запуска генерации] => StartGenerationHandler
# CLASS 8 [Обработчик остановки генерации] => StopGenerationHandler
# CLASS 7 [Обработчик сброса состояния] => ResetHandler
# CLASS 8 [Обработчик обновления live статистики] => LiveStatsUpdateHandler
# CLASS 6 [Базовый класс для экспорта] => ExportHandler
# CLASS 6 [Обработчик экспорта JSON] => ExportJSONHandler
# CLASS 6 [Обработчик экспорта CSV] => ExportCSVHandler
# CLASS 6 [Обработчик экспорта TXT] => ExportTXTHandler
# END_MODULE_MAP
# START_USE_CASES:
# - [EventHandlerRegistry]: System (EventProcessing) -> RouteEvent -> HandlerExecuted
# - [StartGenerationHandler]: User (ClickStart) -> LaunchGenerator -> GenerationStarted
# - [StopGenerationHandler]: User (ClickStop) -> StopGenerator -> StatisticsCollected
# - [ResetHandler]: User (ClickReset) -> ResetState -> InitialStateRestored
# - [LiveStatsUpdateHandler]: System (Timer) -> UpdateMetrics -> UIRefreshed
# END_USE_CASES

"""
Модуль event_handlers.py — Обработчики событий UI и бизнес-логики.
Содержит классы-обработчики для каждого типа события и реестр для управления ими.
"""

# START_BLOCK_IMPORT_MODULES: [Импорт необходимых модулей]
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable, List, TYPE_CHECKING

import gradio as gr

if TYPE_CHECKING:
    from src.monitor.app_core import GradioMonitorAppCore
    from src.monitor.ui_builder import UIBuilder

logger = logging.getLogger(__name__)
# END_BLOCK_IMPORT_MODULES


# START_CLASS_EventHandler
# START_CONTRACT:
# PURPOSE: Базовый класс для всех обработчиков событий. Обеспечивает доступ к app_core и ui_builder через dependency injection.
# ATTRIBUTES:
# - _app: GradioMonitorAppCore — ссылка на ядро приложения
# - _ui: UIBuilder — ссылка на строитель UI
# METHODS:
# - Обработка события => handle (абстрактный)
# - Доступ к UI компоненту => _get_ui_component
# - Обновление отображения этапа => _update_stage_display
# - Обновление отображения ошибки => _update_error_display
# KEYWORDS: [PATTERN(8): BaseHandler; CONCEPT(7): DependencyInjection; TECH(6): Abstract]
# END_CONTRACT

class EventHandler(ABC):
    """
    [Базовый класс для обработчиков событий с DI.]
    """

    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация обработчика с ссылками на app_core и ui_builder.
    # INPUTS:
    # - app_core: GradioMonitorAppCore — ядро приложения
    # - ui_builder: UIBuilder — строитель UI
    # OUTPUTS: None
    # KEYWORDS: [CONCEPT(5): Initialization; TECH(5): DependencyInjection]
    # END_CONTRACT

    def __init__(self, app_core: 'GradioMonitorAppCore', ui_builder: 'UIBuilder'):
        self._app = app_core
        self._ui = ui_builder

    # END_METHOD___init__

    # START_METHOD_handle
    @abstractmethod
    def handle(self, *args, **kwargs) -> Any:
        """
        Выполнить обработку события.
        """
        pass

    # END_METHOD_handle

    # START_METHOD__get_ui_component
    # START_CONTRACT:
    # PURPOSE: Получение UI компонента по имени.
    # INPUTS:
    # - name: str — имя компонента
    # OUTPUTS:
    # - Optional[Any] — компонент или None
    # KEYWORDS: [CONCEPT(5): UI; TECH(4): ComponentLookup]
    # END_CONTRACT

    def _get_ui_component(self, name: str) -> Optional[Any]:
        """Получить UI компонент по имени."""
        return self._ui.get_component(name)

    # END_METHOD__get_ui_component

    # START_METHOD__update_stage_display
    # START_CONTRACT:
    # PURPOSE: Обновление отображения текущего этапа через HTMLGenerator.
    # INPUTS: None
    # OUTPUTS:
    # - str — HTML код этапа
    # KEYWORDS: [CONCEPT(5): UI; TECH(4): HTMLGeneration]
    # END_CONTRACT

    def _update_stage_display(self) -> str:
        """Обновить отображение этапа."""
        from src.monitor.utils.html_generators import HTMLGenerator
        return HTMLGenerator.get_stage_html(self._app.current_stage)

    # END_METHOD__update_stage_display

    # START_METHOD__update_error_display
    # START_CONTRACT:
    # PURPOSE: Обновление отображения ошибки через HTMLGenerator.
    # INPUTS:
    # - message: Optional[str] — текст ошибки (None для скрытия)
    # OUTPUTS:
    # - str — HTML код ошибки
    # KEYWORDS: [CONCEPT(5): UI; TECH(4): ErrorDisplay]
    # END_CONTRACT

    def _update_error_display(self, message: Optional[str] = None) -> str:
        """Обновить отображение ошибки."""
        from src.monitor.utils.html_generators import HTMLGenerator
        return HTMLGenerator.get_error_html(message)

    # END_METHOD__update_error_display


# END_CLASS_EventHandler


# START_CLASS_ListSelectedHandler
# START_CONTRACT:
# PURPOSE: Обработчик выбора списка адресов. Проверяет валидность выбора и обновляет состояние.
# METHODS:
# - Обработка выбора => handle
# KEYWORDS: [PATTERN(7): Handler; CONCEPT(6): EventHandling]
# END_CONTRACT

class ListSelectedHandler(EventHandler):
    """
    [Обработчик выбора списка адресов.]
    """

    # START_METHOD_handle
    # START_CONTRACT:
    # PURPOSE: Обработка подтверждения выбора списка.
    # INPUTS: None
    # OUTPUTS:
    # - tuple — (stage_html, error_html, start_btn_update, tab_update)
    # KEYWORDS: [CONCEPT(6): Validation; TECH(5): StateUpdate]
    # END_CONTRACT

    def handle(self) -> tuple:
        """Обработка подтверждения выбора списка."""
        list_selector = self._app.plugin_manager.get_plugin("list_selector")

        if list_selector and list_selector.validate_selection():
            logger.info(f"[ListSelectedHandler][SUCCESS] Список выбран: {list_selector.get_selected_list()}")
            self._app.list_confirmed = True
            start_update = gr.update(interactive=True)
            tab_update = self._ui.update_active_tab(self._app.current_stage)
            return (
                self._update_stage_display(),
                self._update_error_display(None),
                start_update,
                tab_update
            )
        else:
            logger.warning(f"[ListSelectedHandler][WARNING] Список не выбран")
            start_update = gr.update(interactive=True)
            tab_update = self._ui.update_active_tab(self._app.current_stage)
            return (
                self._update_stage_display(),
                self._update_error_display("Список адресов не выбран"),
                start_update,
                tab_update
            )

    # END_METHOD_handle


# END_CLASS_ListSelectedHandler


# START_CLASS_RadioChangeHandler
# START_CONTRACT:
# PURPOSE: Обработчик изменения выбора в Radio компоненте. Обновляет информацию о выбранном списке.
# METHODS:
# - Обработка изменения => handle
# KEYWORDS: [PATTERN(7): Handler; CONCEPT(6): EventHandling]
# END_CONTRACT

class RadioChangeHandler(EventHandler):
    """
    [Обработчик изменения выбора в Radio.]
    """

    # START_METHOD_handle
    # START_CONTRACT:
    # PURPOSE: Обновление информации о выбранном списке.
    # INPUTS:
    # - selected_value: Any — новое значение выбора
    # OUTPUTS:
    # - str — HTML обновлённой информации
    # KEYWORDS: [CONCEPT(6): UIUpdate; TECH(5): EventHandling]
    # END_CONTRACT

    def handle(self, selected_value: Any) -> str:
        """Обновление информации о выбранном списке."""
        if selected_value:
            list_selector = self._app.plugin_manager.get_plugin("list_selector")
            if list_selector:
                list_selector.set_selected_list(selected_value)
                logger.info(f"[RadioChangeHandler][SUCCESS] Выбран список: {selected_value}")
                return list_selector._generate_info_html(selected_value)
        return "<p style='color: #212121;'>Выберите список</p>"

    # END_METHOD_handle


# END_CLASS_RadioChangeHandler


# START_CLASS_StartGenerationHandler
# START_CONTRACT:
# PURPOSE: Обработчик запуска генератора кошельков. Инициирует процесс генерации и уведомляет плагины.
# METHODS:
# - Запуск генерации => handle
# - Обработка ошибки => _handle_error
# - Обработка успеха => _handle_success
# KEYWORDS: [PATTERN(8): Workflow; CONCEPT(7): StateTransition]
# END_CONTRACT

class StartGenerationHandler(EventHandler):
    """
    [Обработчик запуска генерации.]
    """

    # START_METHOD_handle
    # START_CONTRACT:
    # PURPOSE: Запуск генератора кошельков с валидацией и уведомлением плагинов.
    # INPUTS: None
    # OUTPUTS:
    # - tuple — (stage_html, error_html, start_btn_update, stop_btn_update, tab_update)
    # KEYWORDS: [CONCEPT(7): GeneratorLaunch; TECH(6): Validation]
    # END_CONTRACT

    def handle(self) -> tuple:
        """Запуск генератора кошельков."""
        # Валидация выбора списка
        list_selector = self._app.plugin_manager.get_plugin("list_selector")
        if not list_selector or not list_selector.validate_selection():
            logger.error(f"[StartGenerationHandler][FAIL] Список не выбран")
            return self._handle_error("Список адресов не выбран")

        selected_list = list_selector.get_selected_list()
        if not selected_list:
            logger.error(f"[StartGenerationHandler][FAIL] Путь к списку пуст")
            return self._handle_error("Путь к списку пуст")

        # Установка этапа
        self._app.set_stage(self._app.STAGE_2)
        logger.info(f"[StartGenerationHandler][STAGE] Переход на этап: {self._app.STAGE_2}")

        # Запуск интеграции
        success = self._app.start_generation(selected_list)

        if not success:
            self._app.set_stage(self._app.STAGE_1)
            logger.error(f"[StartGenerationHandler][FAIL] Ошибка запуска генератора")
            return self._handle_error("Ошибка запуска генератора")

        # Запуск polling
        self._app.start_polling()

        # Уведомление плагинов
        self._app.plugin_manager.dispatch_event("on_start", selected_list)
        self._app.is_running = True
        logger.info(f"[StartGenerationHandler][SUCCESS] Генератор запущен")

        return self._handle_success()

    # END_METHOD_handle

    # START_METHOD__handle_error
    # START_CONTRACT:
    # PURPOSE: Обработка ошибки запуска.
    # INPUTS:
    # - message: str — текст ошибки
    # OUTPUTS:
    # - tuple — (stage_html, error_html, start_btn_update, stop_btn_update, tab_update)
    # KEYWORDS: [CONCEPT(5): ErrorHandling]
    # END_CONTRACT

    def _handle_error(self, message: str) -> tuple:
        """Обработка ошибки запуска."""
        start_update = gr.update(interactive=True)
        stop_update = gr.update(interactive=False)
        close_update = gr.update(interactive=True)
        tab_update = self._ui.update_active_tab(self._app.current_stage)
        return (
            self._update_stage_display(),
            self._update_error_display(message),
            start_update,
            stop_update,
            close_update,
            tab_update
        )

    # END_METHOD__handle_error

    # START_METHOD__handle_success
    # START_CONTRACT:
    # PURPOSE: Обработка успешного запуска.
    # INPUTS: None
    # OUTPUTS:
    # - tuple — (stage_html, error_html, start_btn_update, stop_btn_update, tab_update)
    # KEYWORDS: [CONCEPT(5): SuccessHandling]
    # END_CONTRACT

    def _handle_success(self) -> tuple:
        """Обработка успешного запуска."""
        start_update = gr.update(interactive=False)
        stop_update = gr.update(interactive=True)
        close_update = gr.update(interactive=False)
        tab_update = self._ui.update_active_tab(self._app.current_stage)
        return (
            self._update_stage_display(),
            self._update_error_display(None),
            start_update,
            stop_update,
            close_update,
            tab_update
        )

    # END_METHOD__handle_success


# END_CLASS_StartGenerationHandler


# START_CLASS_StopGenerationHandler
# START_CONTRACT:
# PURPOSE: Обработчик остановки генератора. Останавливает генератор, polling и обновляет статистику.
# METHODS:
    # - Остановка генерации => handle
    # - Формирование ответа => _build_response
# KEYWORDS: [PATTERN(8): Cleanup; CONCEPT(7): ResourceManagement]
# END_CONTRACT

class StopGenerationHandler(EventHandler):
    """
    [Обработчик остановки генерации.]
    """

    # START_METHOD_handle
    # START_CONTRACT:
    # PURPOSE: Остановка генератора и обновление статистики.
    # INPUTS: None
    # OUTPUTS:
    # - tuple — полный набор обновлений UI включая финальную статистику
    # KEYWORDS: [CONCEPT(7): GeneratorStop; TECH(6): Statistics]
    # END_CONTRACT

    def handle(self) -> tuple:
        """Остановка генератора и обновление статистики."""
        logger.info(f"[StopGenerationHandler][INFO] Остановка генератора")

        # Остановка polling и генератора
        self._app.stop_generation()

        # Получение финальной статистики
        final_stats = self._app.plugin_manager.get_plugin("final_stats")
        ui_updates = {}

        if final_stats and self._app.launch_integration:
            final_metrics = self._app.launch_integration.get_current_metrics()
            # Вычисление uptime
            import time as time_module
            if hasattr(self._app.launch_integration, '_start_time') and self._app.launch_integration._start_time:
                computed_uptime = time_module.time() - self._app.launch_integration._start_time
                final_metrics["uptime"] = computed_uptime

            final_stats.on_finish(final_metrics)
            ui_updates = final_stats.update_ui()
            logger.info(f"[StopGenerationHandler][INFO] Получены UI обновления: {ui_updates}")

        # Установка этапа
        self._app.set_stage(self._app.STAGE_4)
        self._app.is_running = False
        logger.info(f"[StopGenerationHandler][STAGE] Переход на этап: {self._app.STAGE_4}")

        return self._build_response(ui_updates)

    # END_METHOD_handle

    # START_METHOD__build_response
    # START_CONTRACT:
    # PURPOSE: Формирование ответа с обновлениями UI.
    # INPUTS:
    # - ui_updates: Dict — обновления от плагина статистики
    # OUTPUTS:
    # - tuple — полный набор обновлений UI
    # KEYWORDS: [CONCEPT(5): UIUpdate; TECH(5): ResponseBuilding]
    # END_CONTRACT

    def _build_response(self, ui_updates: Dict) -> tuple:
        """Формирование ответа с обновлениями UI."""
        start_update = gr.update(interactive=True)
        stop_update = gr.update(interactive=False)
        close_update = gr.update(interactive=True)
        tab_update = self._ui.update_active_tab(self._app.current_stage)

        return (
            self._update_stage_display(),
            self._update_error_display(None),
            start_update,
            stop_update,
            close_update,
            tab_update,
            ui_updates.get("total_iterations", 0),
            ui_updates.get("total_matches", 0),
            ui_updates.get("total_wallets", 0),
            ui_updates.get("runtime", 0),
            ui_updates.get("runtime_formatted", "00:00:00"),
            ui_updates.get("avg_iteration_time", 0),
            ui_updates.get("iterations_per_second", 0),
            ui_updates.get("wallets_per_second", 0),
        )

    # END_METHOD__build_response


# END_CLASS_StopGenerationHandler


# START_CLASS_ResetHandler
# START_CONTRACT:
# PURPOSE: Обработчик сброса состояния мониторинга. Сбрасывает метрики, плагины и возвращает на этап выбора списка.
# METHODS:
# - Сброс состояния => handle
# KEYWORDS: [CONCEPT(6): Reset; TECH(5): StateManagement]
# END_CONTRACT

class ResetHandler(EventHandler):
    """
    [Обработчик сброса состояния.]
    """

    # START_METHOD_handle
    # START_CONTRACT:
    # PURPOSE: Полный сброс мониторинга.
    # INPUTS: None
    # OUTPUTS:
    # - tuple — (stage_html, error_html, start_btn_update, stop_btn_update, tab_update)
    # KEYWORDS: [CONCEPT(6): StateReset; TECH(5): Cleanup]
    # END_CONTRACT

    def handle(self) -> tuple:
        """Полный сброс мониторинга."""
        logger.info(f"[ResetHandler][INFO] Начало полного сброса")
        self._app.reset()

        start_update = gr.update(interactive=True)
        stop_update = gr.update(interactive=False)
        close_update = gr.update(interactive=True)
        tab_update = self._ui.update_active_tab(self._app.current_stage)

        logger.info(f"[ResetHandler][SUCCESS] Полный сброс выполнен")

        return (
            self._update_stage_display(),
            self._update_error_display(None),
            start_update,
            stop_update,
            close_update,
            tab_update
        )

    # END_METHOD_handle


# END_CLASS_ResetHandler


# START_CLASS_CloseAppHandler
# START_CONTRACT:
# PURPOSE: Обработчик закрытия приложения. Останавливает генератор (если запущен) и завершает приложение.
# METHODS:
# - Закрытие приложения => handle
# KEYWORDS: [PATTERN(8): Shutdown; CONCEPT(7): Exit; TECH(5): Process]
# END_CONTRACT

class CloseAppHandler(EventHandler):
    """
    [Обработчик закрытия приложения.]
    """

    # START_METHOD_handle
    # START_CONTRACT:
    # PURPOSE: Закрытие приложения (аналог Ctrl+C).
    # INPUTS: None
    # OUTPUTS:
    # - tuple — обновления UI (не возвращается так как приложение закрывается)
    # KEYWORDS: [CONCEPT(7): ApplicationExit; TECH(5): Process]
    # END_CONTRACT

    def handle(self) -> tuple:
        """Закрытие приложения."""
        logger.info(f"[CloseAppHandler][INFO] Обработка закрытия приложения")
        
        # Закрытие приложения (метод не возвращается)
        self._app.close_app()
        
        # Эти строки никогда не выполнятся так как приложение закроется
        return (
            self._update_stage_display(),
            self._update_error_display(None),
            gr.update(interactive=False),
            gr.update(interactive=False),
            gr.update(interactive=False),
            self._ui.update_active_tab(self._app.current_stage)
        )

    # END_METHOD_handle


# END_CLASS_CloseAppHandler


# START_CLASS_LiveStatsUpdateHandler
# START_CONTRACT:
# PURPOSE: Обработчик обновления live статистики. Получает метрики от генератора и обновляет UI.
# METHODS:
# - Обновление метрик => handle
# KEYWORDS: [PATTERN(8): LiveUpdate; CONCEPT(7): Timer; TECH(6): Metrics]
# END_CONTRACT

class LiveStatsUpdateHandler(EventHandler):
    """
    [Обработчик обновления live статистики.]
    """

    # START_METHOD_handle
    # START_CONTRACT:
    # PURPOSE: Обновление метрик в реальном времени.
    # INPUTS: None
    # OUTPUTS:
    # - tuple — (iteration_count, wallet_count, match_count, elapsed_time, iter_per_sec, wallets_per_sec, status_html)
    # KEYWORDS: [CONCEPT(7): RealTimeUpdate; TECH(6): MetricsPolling]
    # END_CONTRACT

    def handle(self) -> tuple:
        """Обновление метрик в реальном времени."""
        from src.monitor.utils.html_generators import HTMLGenerator

        if not self._app.is_running or not self._app.launch_integration:
            status_html = HTMLGenerator.get_live_status_html(0, False)
            logger.debug(f"[LiveStatsUpdateHandler][CONDITION] Генератор не запущен")
            return (0, 0, 0, 0.0, 0.0, 0.0, status_html)

        try:
            metrics = self._app.launch_integration.get_current_metrics()
            if not metrics:
                status_html = HTMLGenerator.get_live_status_html(0, True)
                logger.debug(f"[LiveStatsUpdateHandler][INFO] Метрики отсутствуют")
                return (0, 0, 0, 0.0, 0.0, 0.0, status_html)
        except Exception as e:
            logger.error(f"[LiveStatsUpdateHandler][EXCEPTION] Ошибка получения метрик: {e}")
            status_html = HTMLGenerator.get_live_status_html(0, True)
            return (0, 0, 0, 0.0, 0.0, 0.0, status_html)

        # Извлечение значений
        iteration_count = metrics.get("iteration_count", 0)
        wallet_count = metrics.get("wallet_count", 0)
        match_count = metrics.get("match_count", 0)
        elapsed_time = self._app.launch_integration.get_uptime()

        # Вычисление скоростей
        iter_per_sec = iteration_count / elapsed_time if elapsed_time > 0 else 0.0
        wallets_per_sec = wallet_count / elapsed_time if elapsed_time > 0 else 0.0

        # Генерация статуса
        is_monitoring = iteration_count > 0
        status_html = HTMLGenerator.get_live_status_html(iteration_count, is_monitoring)

        logger.debug(f"[LiveStatsUpdateHandler][INFO] Итераций: {iteration_count}, Кошельков: {wallet_count}, Время: {elapsed_time:.1f}с")

        return (
            iteration_count,
            wallet_count,
            match_count,
            round(elapsed_time, 1),
            round(iter_per_sec, 2),
            round(wallets_per_sec, 2),
            status_html
        )

    # END_METHOD_handle


# END_CLASS_LiveStatsUpdateHandler


# START_CLASS_ExportHandler
# START_CONTRACT:
# PURPOSE: Базовый класс для обработчиков экспорта статистики.
# METHODS:
# - Универсальный экспорт => _export
# KEYWORDS: [PATTERN(7): Export; CONCEPT(6): FileGeneration]
# END_CONTRACT

class ExportHandler(EventHandler):
    """
    [Базовый класс для обработчиков экспорта.]
    """

    # START_METHOD__export
    # START_CONTRACT:
    # PURPOSE: Универсальный метод экспорта данных в файл.
    # INPUTS:
    # - suffix: str — расширение файла
    # - export_method: str — имя метода экспорта плагина
    # OUTPUTS:
    # - Optional[str] — путь к созданному файлу или None
    # KEYWORDS: [CONCEPT(6): FileExport; TECH(5): TempFile]
    # END_CONTRACT

    def _export(self, suffix: str, export_method: str) -> Any:
        """Универсальный метод экспорта."""
        import tempfile

        final_stats = self._app.plugin_manager.get_plugin("final_stats")
        if not final_stats:
            logger.warning(f"[ExportHandler][WARNING] Плагин финальной статистики не найден")
            return None

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, encoding='utf-8') as tmp:
                tmp_path = tmp.name

            method = getattr(final_stats, export_method)
            success = method(tmp_path)

            return tmp_path if success else None
        except Exception as e:
            logger.error(f"[ExportHandler][EXCEPTION] Ошибка экспорта: {e}")
            return None

    # END_METHOD__export


# END_CLASS_ExportHandler


# START_CLASS_ExportJSONHandler
# START_CONTRACT:
# PURPOSE: Обработчик экспорта статистики в формате JSON.
# METHODS:
# - Экспорт JSON => handle
# KEYWORDS: [PATTERN(7): Export; TECH(5): JSON]
# END_CONTRACT

class ExportJSONHandler(ExportHandler):
    """
    [Обработчик экспорта в JSON.]
    """

    # START_METHOD_handle
    # START_CONTRACT:
    # PURPOSE: Экспорт статистики в формате JSON.
    # INPUTS: None
    # OUTPUTS:
    # - Optional[str] — путь к JSON файлу
    # KEYWORDS: [CONCEPT(5): JSONExport]
    # END_CONTRACT

    def handle(self) -> Any:
        """Экспорт статистики в JSON."""
        logger.info(f"[ExportJSONHandler][INFO] Экспорт в JSON")
        return self._export('.json', 'export_json')

    # END_METHOD_handle


# END_CLASS_ExportJSONHandler


# START_CLASS_ExportCSVHandler
# START_CONTRACT:
# PURPOSE: Обработчик экспорта статистики в формате CSV.
# METHODS:
# - Экспорт CSV => handle
# KEYWORDS: [PATTERN(7): Export; TECH(5): CSV]
# END_CONTRACT

class ExportCSVHandler(ExportHandler):
    """
    [Обработчик экспорта в CSV.]
    """

    # START_METHOD_handle
    # START_CONTRACT:
    # PURPOSE: Экспорт статистики в формате CSV.
    # INPUTS: None
    # OUTPUTS:
    # - Optional[str] — путь к CSV файлу
    # KEYWORDS: [CONCEPT(5): CSVExport]
    # END_CONTRACT

    def handle(self) -> Any:
        """Экспорт статистики в CSV."""
        logger.info(f"[ExportCSVHandler][INFO] Экспорт в CSV")
        return self._export('.csv', 'export_csv')

    # END_METHOD_handle


# END_CLASS_ExportCSVHandler


# START_CLASS_ExportTXTHandler
# START_CONTRACT:
# PURPOSE: Обработчик экспорта статистики в формате TXT.
# METHODS:
# - Экспорт TXT => handle
# KEYWORDS: [PATTERN(7): Export; TECH(5): TXT]
# END_CONTRACT

class ExportTXTHandler(ExportHandler):
    """
    [Обработчик экспорта в TXT.]
    """

    # START_METHOD_handle
    # START_CONTRACT:
    # PURPOSE: Экспорт статистики в формате TXT.
    # INPUTS: None
    # OUTPUTS:
    # - Optional[str] — путь к TXT файлу
    # KEYWORDS: [CONCEPT(5): TXTExport]
    # END_CONTRACT

    def handle(self) -> Any:
        """Экспорт статистики в TXT."""
        logger.info(f"[ExportTXTHandler][INFO] Экспорт в TXT")
        result = self._export('.txt', 'export_txt')
        return result if result and result.endswith('.txt') else None

    # END_METHOD_handle


# END_CLASS_ExportTXTHandler


# START_CLASS_EventHandlerRegistry
# START_CONTRACT:
# PURPOSE: Реестр обработчиков событий. Централизованное управление всеми обработчиками с возможностью регистрации новых.
# ATTRIBUTES:
# - _handlers: Dict[str, EventHandler] — словарь зарегистрированных обработчиков
# - _app_core: Optional[GradioMonitorAppCore] — ссылка на ядро приложения
# - _ui_builder: Optional[UIBuilder] — ссылка на строитель UI
# METHODS:
# - Инициализация => initialize
# - Получение обработчика => get_handler
# - Регистрация => register
# - Вызов => call
# KEYWORDS: [PATTERN(9): Registry; CONCEPT(8): EventBus; TECH(7): CentralizedManagement]
# END_CONTRACT

class EventHandlerRegistry:
    """
    [Реестр обработчиков событий.]
    """

    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация реестра обработчиков.
    # INPUTS: None
    # OUTPUTS: None
    # KEYWORDS: [CONCEPT(5): Initialization]
    # END_CONTRACT

    def __init__(self):
        self._handlers: Dict[str, EventHandler] = {}
        self._app_core: Optional['GradioMonitorAppCore'] = None
        self._ui_builder: Optional['UIBuilder'] = None
        logger.debug(f"[EventHandlerRegistry][INIT] Реестр обработчиков инициализирован")

    # END_METHOD___init__

    # START_METHOD_initialize
    # START_CONTRACT:
    # PURPOSE: Инициализация реестра с созданием всех обработчиков.
    # INPUTS:
    # - app_core: GradioMonitorAppCore — ядро приложения
    # - ui_builder: UIBuilder — строитель UI
    # OUTPUTS: None
    # KEYWORDS: [CONCEPT(6): Setup; TECH(5): DependencyInjection]
    # END_CONTRACT

    def initialize(self, app_core: 'GradioMonitorAppCore', ui_builder: 'UIBuilder') -> None:
        """Инициализация реестра с созданием всех обработчиков."""
        self._app_core = app_core
        self._ui_builder = ui_builder

        # Создание обработчиков
        self._handlers = {
            "list_selected": ListSelectedHandler(app_core, ui_builder),
            "radio_change": RadioChangeHandler(app_core, ui_builder),
            "start": StartGenerationHandler(app_core, ui_builder),
            "stop": StopGenerationHandler(app_core, ui_builder),
            "reset": ResetHandler(app_core, ui_builder),
            "close_app": CloseAppHandler(app_core, ui_builder),
            "live_stats_update": LiveStatsUpdateHandler(app_core, ui_builder),
            "export_json": ExportJSONHandler(app_core, ui_builder),
            "export_csv": ExportCSVHandler(app_core, ui_builder),
            "export_txt": ExportTXTHandler(app_core, ui_builder),
        }
        logger.info(f"[EventHandlerRegistry][INIT] Зарегистрировано {len(self._handlers)} обработчиков")

    # END_METHOD_initialize

    # START_METHOD_get_handler
    # START_CONTRACT:
    # PURPOSE: Получение обработчика по имени события.
    # INPUTS:
    # - event: str — имя события
    # OUTPUTS:
    # - Optional[EventHandler] — обработчик или None
    # KEYWORDS: [CONCEPT(5): Lookup; TECH(4): Retrieval]
    # END_CONTRACT

    def get_handler(self, event: str) -> Optional[EventHandler]:
        """Получить обработчик по имени события."""
        return self._handlers.get(event)

    # END_METHOD_get_handler

    # START_METHOD_register
    # START_CONTRACT:
    # PURPOSE: Регистрация кастомного обработчика.
    # INPUTS:
    # - event: str — имя события
    # - handler: EventHandler — экземпляр обработчика
    # OUTPUTS: None
    # KEYWORDS: [PATTERN(6): Registration; CONCEPT(5): CustomHandler]
    # END_CONTRACT

    def register(self, event: str, handler: EventHandler) -> None:
        """Зарегистрировать кастомный обработчик."""
        self._handlers[event] = handler
        logger.info(f"[EventHandlerRegistry][REGISTER] Зарегистрирован обработчик: {event}")

    # END_METHOD_register

    # START_METHOD_call
    # START_CONTRACT:
    # PURPOSE: Вызов обработчика события.
    # INPUTS:
    # - event: str — имя события
    # - *args, **kwargs — аргументы для передачи в обработчик
    # OUTPUTS:
    # - Any — результат выполнения обработчика
    # KEYWORDS: [CONCEPT(6): EventDispatch; TECH(5): Invocation]
    # END_CONTRACT

    def call(self, event: str, *args: Any, **kwargs: Any) -> Any:
        """Вызвать обработчик события."""
        handler = self._handlers.get(event)
        if handler:
            return handler.handle(*args, **kwargs)
        logger.warning(f"[EventHandlerRegistry][CALL] Обработчик не найден: {event}")
        return None

    # END_METHOD_call


# END_CLASS_EventHandlerRegistry
