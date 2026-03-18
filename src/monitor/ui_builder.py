# FILE: src/monitor/ui_builder.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Конструирование Gradio UI интерфейса мониторинга. Отвечает заентов, вклад создание всех компонок и привязку событий.
# SCOPE: UI конструирование, компоненты Gradio, макет интерфейса
# INPUT: app_core через dependency injection для делегирования событий
# OUTPUT: Класс UIBuilder с методами построения UI
# KEYWORDS: [DOMAIN(9): UI; DOMAIN(8): Gradio; CONCEPT(7): BuilderPattern; TECH(6): Components: [IMPOR]
# LINKSTS(8): src.monitor.utils.html_generators; IMPORTS(7): gradio; USES(7): EventHandlerRegistry]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 9 [Строитель Gradio UI интерфейса] => UIBuilder
# METHOD 8 [Построение интерфейса] => build
# METHOD 7 [Создание кнопок управления] => _build_control_buttons
# METHOD 7 [Создание вкладок] => _build_tabs
# METHOD 6 [Вкладка выбора списка] => _build_tab_list_selection
# METHOD 6 [Вкладка live мониторинга] => _build_tab_live_monitoring
# METHOD 6 [Вкладка уведомлений] => _build_tab_notifications
# METHOD 6 [Вкладка финальной статистики] => _build_tab_final_stats
# METHOD 6 [Создание таймера] => _build_timer
# METHOD 7 [Получение компонентов] => get_components
# METHOD 7 [Получение компонента по имени] => get_component
# METHOD 7 [Обновление состояния кнопок] => update_button_states
# METHOD 7 [Обновление активной вкладки] => update_active_tab
# END_MODULE_MAP
# START_USE_CASES:
# - [build]: System (Startup) -> ConstructUI -> GradioInterfaceReady
# - [_build_tabs]: System (UI) -> CreateTabs -> TabsDisplayed
# - [get_component]: System (Event) -> GetComponent -> ComponentReferenceReturned
# END_USE_CASES

"""
Модуль ui_builder.py — Строитель Gradio UI интерфейса мониторинга.
Содержит класс UIBuilder для создания всех UI компонентов и вкладок.
"""

# START_BLOCK_IMPORT_MODULES: [Импорт необходимых модулей]
import logging
from typing import Any, Dict, Optional, TYPE_CHECKING, Tuple

import gradio as gr

if TYPE_CHECKING:
    from src.monitor.app_core import GradioMonitorAppCore

logger = logging.getLogger(__name__)
# END_BLOCK_IMPORT_MODULES


# START_CLASS_UIBuilder
# START_CONTRACT:
# PURPOSE: Строитель UI интерфейса мониторинга. Отвечает за создание всех UI компонентов, организацию вкладок и layout.
# ATTRIBUTES:
# - _html_gen: HTMLGenerator — генератор HTML
# - _components: Dict[str, Any] — словарь UI компонентов
# - _app_core: Optional[GradioMonitorAppCore] — ссылка на ядро приложения
# - _event_registry: Optional — реестр обработчиков событий
# METHODS:
# - Построение UI => build
# - Создание кнопок => _build_control_buttons
# - Создание вкладок => _build_tabs
# - Доступ к компонентам => get_component, get_components
# - Обновление состояний => update_button_states, update_active_tab
# KEYWORDS: [PATTERN(9): Builder; DOMAIN(9): UI; CONCEPT(8): GradioComponents; TECH(7): Layout]
# END_CONTRACT

class UIBuilder:
    """
    [Строитель UI интерфейса мониторинга.]
    """

    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация UIBuilder с получением HTMLGenerator.
    # INPUTS:
    # - html_generator: HTMLGenerator — генератор HTML для заголовков и статусов
    # OUTPUTS: None
    # KEYWORDS: [CONCEPT(5): Initialization; TECH(5): DependencyInjection]
    # END_CONTRACT

    def __init__(self, html_generator, event_registry=None):
        """
        Args:
            html_generator: Генератор HTML для заголовков и статусов
            event_registry: Реестр обработчиков событий (опционально)
        """
        self._html_gen = html_generator
        self._components: Dict[str, Any] = {}
        self._app_core: Optional['GradioMonitorAppCore'] = None
        self._event_registry = event_registry
        logger.debug(f"[UIBuilder][INIT] UIBuilder инициализирован")

    # END_METHOD___init__

    # START_METHOD_build
    # START_CONTRACT:
    # PURPOSE: Построение полного Gradio интерфейса мониторинга.
    # INPUTS:
    # - app_core: GradioMonitorAppCore — ссылка на ядро приложения для делегирования событий
    # OUTPUTS:
    # - gr.Blocks — готовый Gradio интерфейс
    # KEYWORDS: [PATTERN(8): UIConstruction; TECH(7): Gradio; CONCEPT(6): LayoutBuilding]
    # END_CONTRACT

    def build(self, app_core: 'GradioMonitorAppCore') -> gr.Blocks:
        """
        Построение полного интерфейса.

        Args:
            app_core: Ссылка на ядро приложения для делегирования событий

        Returns:
            gr.Blocks: Готовый Gradio интерфейс
        """
        self._app_core = app_core
        logger.info(f"[UIBuilder][BUILD] Начало построения интерфейса")

        # CSS для скрытия кнопки API
        css = """
        .api-button, button[data-testid="api-button"] {
            display: none !important;
        }
        """

        with gr.Blocks(title="Wallet Generator Monitor", css=css) as blocks:
            # Заголовок
            gr.HTML(value=self._html_gen.generate_header())

            # Статус этапа
            with gr.Row():
                self._components["stage_display"] = gr.HTML(
                    value=self._html_gen.get_stage_html(app_core.current_stage),
                    label="Текущий этап"
                )

            # Компонент для отображения ошибок
            with gr.Row():
                self._components["error_display"] = gr.HTML(
                    value=self._html_gen.get_error_html(None),
                    label="Ошибки",
                    visible=False,
                )

            # Кнопки управления
            self._build_control_buttons()

            # Вкладки
            self._build_tabs()

            # Таймер
            self._build_timer()

            # Футер
            gr.HTML(value=self._html_gen.generate_footer())

            # Привязка обработчиков событий
            self._bind_events()

        logger.info(f"[UIBuilder][BUILD] Интерфейс построен")
        return blocks

    # END_METHOD_build

    # START_METHOD__build_control_buttons
    # START_CONTRACT:
    # PURPOSE: Создание кнопок управления (Запустить, Остановить, Сброс).
    # INPUTS: None
    # OUTPUTS: None (заполняет _components)
    # KEYWORDS: [CONCEPT(5): UI; TECH(4): ButtonCreation]
    # END_CONTRACT

    def _build_control_buttons(self) -> None:
        """Создание кнопок управления."""
        with gr.Row():
            self._components["start_btn"] = gr.Button(
                "🚀 Запустить генератор",
                variant="primary",
                size="lg",
                interactive=True
            )
            self._components["stop_btn"] = gr.Button(
                "⏹ Остановить",
                variant="primary",
                size="lg",
                interactive=False
            )
            self._components["reset_btn"] = gr.Button(
                "🔄 Сброс",
                variant="secondary",
                size="lg",
                interactive=True
            )
            self._components["close_btn"] = gr.Button(
                "❌ Закрыть приложение",
                variant="stop",
                size="lg",
                interactive=True
            )
        logger.debug(f"[UIBuilder][BUILD_BUTTONS] Кнопки управления созданы")

    # END_METHOD__build_control_buttons

    # START_METHOD__build_tabs
    # START_CONTRACT:
    # PURPOSE: Создание вкладок (Выбор LIST, Live мониторинг, Уведомления, Финальная статистика).
    # INPUTS: None
    # OUTPUTS: None (заполняет _components)
    # KEYWORDS: [CONCEPT(5): UI; TECH(4): TabCreation]
    # END_CONTRACT

    def _build_tabs(self) -> None:
        """Создание вкладок."""
        self._components["tabs"] = gr.Tabs()

        with self._components["tabs"]:
            # Вкладка 1: Выбор LIST
            self._build_tab_list_selection()

            # Вкладка 2: Live мониторинг
            self._build_tab_live_monitoring()

            # Вкладка 3: Уведомления
            self._build_tab_notifications()

            # Вкладка 4: Финальная статистика
            self._build_tab_final_stats()

        logger.debug(f"[UIBuilder][BUILD_TABS] Вкладки созданы")

    # END_METHOD__build_tabs

    # START_METHOD__build_tab_list_selection
    # START_CONTRACT:
    # PURPOSE: Создание вкладки выбора списка адресов.
    # INPUTS: None
    # OUTPUTS: None (заполняет _components)
    # KEYWORDS: [CONCEPT(5): UI; TECH(4): TabContent]
    # END_CONTRACT

    def _build_tab_list_selection(self) -> None:
        """Вкладка выбора списка."""
        with gr.Tab("Выбор LIST", id="tab_stage_1"):
            gr.HTML(value="<h2>Выберите список адресов для поиска</h2>")

            if self._app_core:
                list_selector = self._app_core.plugin_manager.get_plugin("list_selector")
                if list_selector:
                    components = list_selector.get_ui_components()
                    radio_component = components.get("radio")

                    # Получаем info_html
                    info_component = components.get("info_html")
                    if info_component:
                        self._components["info_html"] = info_component
                        try:
                            info_component.render()
                        except Exception as e:
                            logger.warning(f"[UIBuilder][TAB_LIST] Ошибка рендеринга info_html: {e}")

                    if radio_component:
                        self._components["radio"] = radio_component
                        default_value = radio_component.value
                        if default_value:
                            list_selector.set_selected_list(default_value)
                            logger.info(f"[UIBuilder][TAB_LIST] Установлен выбор по умолчанию: {default_value}")
                        try:
                            radio_component.render()
                        except Exception as e:
                            logger.warning(f"[UIBuilder][TAB_LIST] Ошибка рендеринга radio: {e}")

                    confirm_component = components.get("confirm_btn")
                    if confirm_component:
                        self._components["confirm_btn"] = confirm_component
                        try:
                            confirm_component.render()
                        except Exception as e:
                            logger.warning(f"[UIBuilder][TAB_LIST] Ошибка рендеринга confirm_btn: {e}")

        logger.debug(f"[UIBuilder][TAB_LIST] Вкладка выбора списка создана")

    # END_METHOD__build_tab_list_selection

    # START_METHOD__build_tab_live_monitoring
    # START_CONTRACT:
    # PURPOSE: Создание вкладки live мониторинга с метриками.
    # INPUTS: None
    # OUTPUTS: None (заполняет _components)
    # KEYWORDS: [CONCEPT(5): UI; TECH(4): TabContent; TECH(5): Metrics]
    # END_CONTRACT

    def _build_tab_live_monitoring(self) -> None:
        """Вкладка live мониторинга."""
        with gr.Tab("Live мониторинг", id="tab_stage_2"):
            gr.HTML(value="<h2>Мониторинг процесса генерации</h2>")

            # Метрики: iteration_count, wallet_count, match_count
            with gr.Row():
                self._components["iteration_count"] = gr.Number(
                    label="Итерации",
                    value=0,
                    interactive=False,
                )
                self._components["wallet_count"] = gr.Number(
                    label="Кошельки",
                    value=0,
                    interactive=False,
                )
                self._components["match_count"] = gr.Number(
                    label="Совпадения",
                    value=0,
                    interactive=False,
                )

            with gr.Row():
                self._components["elapsed_time"] = gr.Number(
                    label="Прошло времени (сек)",
                    value=0,
                    interactive=False,
                )
                self._components["iter_per_sec"] = gr.Number(
                    label="Итераций/сек",
                    value=0,
                    interactive=False,
                )
                self._components["wallets_per_sec"] = gr.Number(
                    label="Кошельков/сек",
                    value=0,
                    interactive=False,
                )

            # HTML статус мониторинга
            self._components["status"] = gr.HTML(
                value="<div style='padding: 10px; background: #FFF3E020; border-radius: 8px; border: 2px solid #FF9800;'><h3 style='margin: 0; color: #FF9800;'>🔴 Ожидание запуска</h3></div>",
                label="Статус",
            )

        logger.debug(f"[UIBuilder][TAB_LIVE] Вкладка live мониторинга создана")

    # END_METHOD__build_tab_live_monitoring

    # START_METHOD__build_tab_notifications
    # START_CONTRACT:
    # PURPOSE: Создание вкладки уведомлений о совпадениях.
    # INPUTS: None
    # OUTPUTS: None (заполняет _components)
    # KEYWORDS: [CONCEPT(5): UI; TECH(4): TabContent]
    # END_CONTRACT

    def _build_tab_notifications(self) -> None:
        """Вкладка уведомлений."""
        with gr.Tab("Уведомления", id="tab_notifications"):
            gr.HTML(value="<h2>Уведомления о совпадениях</h2>")

            if self._app_core:
                match_notifier = self._app_core.plugin_manager.get_plugin("match_notifier")
                if match_notifier:
                    components = match_notifier.get_ui_components()
                    match_count = components.get("match_count", 0)
                    is_monitoring = components.get("is_monitoring", False)
                    notification_config = components.get("notification_config", {})

                    # Генерация HTML для конфигурации
                    config_html = self._html_gen.get_notification_config_html(notification_config)
                    status_html = self._html_gen.get_notification_status_html(is_monitoring)

                    self._components["match_notification_status"] = gr.HTML(
                        value=status_html,
                        label="Статус уведомлений",
                    )
                    self._components["match_notification_config"] = gr.HTML(
                        value=config_html,
                        label="Конфигурация",
                    )
                    self._components["match_count_display"] = gr.Number(
                        value=match_count,
                        label="Найдено совпадений",
                        interactive=False,
                    )

        logger.debug(f"[UIBuilder][TAB_NOTIFICATIONS] Вкладка уведомлений создана")

    # END_METHOD__build_tab_notifications

    # START_METHOD__build_tab_final_stats
    # START_CONTRACT:
    # PURPOSE: Создание вкладки финальной статистики с кнопками экспорта.
    # INPUTS: None
    # OUTPUTS: None (заполняет _components)
    # KEYWORDS: [CONCEPT(5): UI; TECH(4): TabContent; TECH(5): Statistics]
    # END_CONTRACT

    def _build_tab_final_stats(self) -> None:
        """Вкладка финальной статистики."""
        with gr.Tab("Финальная статистика", id="tab_stage_3"):
            gr.HTML(value="<h2>Итоговые результаты</h2>")

            # Компоненты для финальной статистики
            with gr.Row():
                self._components["total_iterations"] = gr.Number(
                    label="Всего итераций",
                    value=0,
                    interactive=False,
                )
                self._components["total_matches"] = gr.Number(
                    label="Всего совпадений",
                    value=0,
                    interactive=False,
                )
                self._components["total_wallets"] = gr.Number(
                    label="Всего кошельков",
                    value=0,
                    interactive=False,
                )

            with gr.Row():
                self._components["runtime"] = gr.Number(
                    label="Время работы (сек)",
                    value=0,
                    interactive=False,
                )
                self._components["runtime_formatted"] = gr.Textbox(
                    label="Время работы (формат)",
                    value="00:00:00",
                    interactive=False,
                )

            with gr.Row():
                self._components["avg_iteration_time"] = gr.Number(
                    label="Среднее время итерации (мс)",
                    value=0,
                    interactive=False,
                )
                self._components["iterations_per_second"] = gr.Number(
                    label="Итераций/сек",
                    value=0,
                    interactive=False,
                )
                self._components["wallets_per_second"] = gr.Number(
                    label="Кошельков/сек",
                    value=0,
                    interactive=False,
                )

            # Кнопки экспорта
            with gr.Row():
                gr.HTML(value="<h3>Экспорт статистики</h3>")

            with gr.Row():
                self._components["btn_export_json"] = gr.Button(
                    value="📥 Export JSON",
                    variant="secondary",
                    size="lg",
                )
                self._components["btn_export_csv"] = gr.Button(
                    value="📥 Export CSV",
                    variant="secondary",
                    size="lg",
                )
                self._components["btn_export_txt"] = gr.Button(
                    value="📥 Export TXT",
                    variant="secondary",
                    size="lg",
                )

            with gr.Row():
                self._components["download_file"] = gr.File(
                    label="Скачать файл",
                    file_count="single",
                    file_types=[".json", ".csv", ".txt"],
                    interactive=False,
                )

        logger.debug(f"[UIBuilder][TAB_FINAL] Вкладка финальной статистики создана")

    # END_METHOD__build_tab_final_stats

    # START_METHOD__build_timer
    # START_CONTRACT:
    # PURPOSE: Создание таймера для live обновлений UI.
    # INPUTS: None
    # OUTPUTS: None (заполняет _components)
    # KEYWORDS: [CONCEPT(5): UI; TECH(5): Timer]
    # END_CONTRACT

    def _build_timer(self) -> None:
        """Создание таймера для live обновлений."""
        self._components["update_timer"] = gr.Timer(value=2.0, active=True)
        logger.debug(f"[UIBuilder][TIMER] Таймер создан")

    # END_METHOD__build_timer

    # START_METHOD__bind_events
    # START_CONTRACT:
    # PURPOSE: Привязка обработчиков событий к UI компонентам.
    # INPUTS: None
    # OUTPUTS: None
    # KEYWORDS: [CONCEPT(6): EventBinding; TECH(5): Gradio]
    # END_CONTRACT

    def _bind_events(self) -> None:
        """Привязка обработчиков событий к UI компонентам."""
        logger.info(f"[UIBuilder][BIND_EVENTS] Начало привязки обработчиков")

        # Кнопка Start
        start_btn = self._components.get("start_btn")
        if start_btn and self._event_registry:
            start_btn.click(
                fn=lambda: self._event_registry.call("start"),
                outputs=[
                    self._components.get("stage_display"),
                    self._components.get("error_display"),
                    self._components.get("start_btn"),
                    self._components.get("stop_btn"),
                    self._components.get("close_btn"),
                    self._components.get("tabs"),
                ],
            )
            logger.debug(f"[UIBuilder][BIND] Обработчик Start привязан")

        # Кнопка Stop
        stop_btn = self._components.get("stop_btn")
        if stop_btn and self._event_registry:
            stop_btn.click(
                fn=lambda: self._event_registry.call("stop"),
                outputs=[
                    self._components.get("stage_display"),
                    self._components.get("error_display"),
                    self._components.get("start_btn"),
                    self._components.get("stop_btn"),
                    self._components.get("close_btn"),
                    self._components.get("tabs"),
                    self._components.get("total_iterations"),
                    self._components.get("total_matches"),
                    self._components.get("total_wallets"),
                    self._components.get("runtime"),
                    self._components.get("runtime_formatted"),
                    self._components.get("avg_iteration_time"),
                    self._components.get("iterations_per_second"),
                    self._components.get("wallets_per_second"),
                ],
            )
            logger.debug(f"[UIBuilder][BIND] Обработчик Stop привязан")

        # Кнопка Reset
        reset_btn = self._components.get("reset_btn")
        if reset_btn and self._event_registry:
            reset_btn.click(
                fn=lambda: self._event_registry.call("reset"),
                outputs=[
                    self._components.get("stage_display"),
                    self._components.get("error_display"),
                    self._components.get("start_btn"),
                    self._components.get("stop_btn"),
                    self._components.get("close_btn"),
                    self._components.get("tabs"),
                ],
            )
            logger.debug(f"[UIBuilder][BIND] Обработчик Reset привязан")

        # Кнопка Close App
        close_btn = self._components.get("close_btn")
        if close_btn and self._event_registry:
            close_btn.click(
                fn=lambda: self._event_registry.call("close_app"),
                outputs=[
                    self._components.get("stage_display"),
                    self._components.get("error_display"),
                    self._components.get("start_btn"),
                    self._components.get("stop_btn"),
                    self._components.get("reset_btn"),
                    self._components.get("close_btn"),
                ],
            )
            logger.debug(f"[UIBuilder][BIND] Обработчик Close App привязан")

        # Radio change
        radio = self._components.get("radio")
        if radio and self._event_registry:
            radio.change(
                fn=lambda val: self._event_registry.call("radio_change", val),
                inputs=[radio],
                outputs=[self._components.get("info_html")],
            )
            logger.debug(f"[UIBuilder][BIND] Обработчик Radio change привязан")

        # Confirm button
        confirm_btn = self._components.get("confirm_btn")
        if confirm_btn and self._event_registry:
            confirm_btn.click(
                fn=lambda: self._event_registry.call("list_selected"),
                outputs=[
                    self._components.get("stage_display"),
                    self._components.get("error_display"),
                    self._components.get("start_btn"),
                    self._components.get("tabs"),
                ],
            )
            logger.debug(f"[UIBuilder][BIND] Обработчик Confirm привязан")

        # Timer для live updates
        timer = self._components.get("update_timer")
        if timer and self._event_registry:
            timer.tick(
                fn=lambda: self._event_registry.call("live_stats_update"),
                outputs=[
                    self._components.get("iteration_count"),
                    self._components.get("wallet_count"),
                    self._components.get("match_count"),
                    self._components.get("elapsed_time"),
                    self._components.get("iter_per_sec"),
                    self._components.get("wallets_per_sec"),
                    self._components.get("status"),
                ],
            )
            logger.debug(f"[UIBuilder][BIND] Обработчик Timer привязан")

        # Кнопки экспорта
        btn_export_json = self._components.get("btn_export_json")
        if btn_export_json and self._event_registry:
            btn_export_json.click(
                fn=lambda: self._event_registry.call("export_json"),
                outputs=[self._components.get("download_file")],
            )
            logger.debug(f"[UIBuilder][BIND] Обработчик Export JSON привязан")

        btn_export_csv = self._components.get("btn_export_csv")
        if btn_export_csv and self._event_registry:
            btn_export_csv.click(
                fn=lambda: self._event_registry.call("export_csv"),
                outputs=[self._components.get("download_file")],
            )
            logger.debug(f"[UIBuilder][BIND] Обработчик Export CSV привязан")

        btn_export_txt = self._components.get("btn_export_txt")
        if btn_export_txt and self._event_registry:
            btn_export_txt.click(
                fn=lambda: self._event_registry.call("export_txt"),
                outputs=[self._components.get("download_file")],
            )
            logger.debug(f"[UIBuilder][BIND] Обработчик Export TXT привязан")

        logger.info(f"[UIBuilder][BIND_EVENTS] Все обработчики привязаны")

    # END_METHOD__bind_events

    # START_METHOD_get_components
    # START_CONTRACT:
    # PURPOSE: Получение словаря всех UI компонентов.
    # INPUTS: None
    # OUTPUTS:
    # - Dict[str, Any] — копия словаря компонентов
    # KEYWORDS: [CONCEPT(5): Accessor; TECH(4): ComponentLookup]
    # END_CONTRACT

    def get_components(self) -> Dict[str, Any]:
        """Получение словаря всех UI компонентов."""
        return self._components.copy()

    # END_METHOD_get_components

    # START_METHOD_get_component
    # START_CONTRACT:
    # PURPOSE: Получение конкретного компонента по имени.
    # INPUTS:
    # - name: str — имя компонента
    # OUTPUTS:
    # - Optional[Any] — компонент или None
    # KEYWORDS: [CONCEPT(5): Accessor; TECH(4): ComponentLookup]
    # END_CONTRACT

    def get_component(self, name: str) -> Optional[Any]:
        """Получение конкретного компонента по имени."""
        return self._components.get(name)

    # END_METHOD_get_component

    # START_METHOD_update_button_states
    # START_CONTRACT:
    # PURPOSE: Генерация gr.update для кнопок управления.
    # INPUTS:
    # - start_active: bool — активна ли кнопка запуска
    # - stop_active: bool — активна ли кнопка остановки
    # - confirm_active: bool — активна ли кнопка подтверждения
    # OUTPUTS:
    # - tuple — (start_update, stop_update, confirm_update)
    # KEYWORDS: [CONCEPT(5): UIUpdate; TECH(4): GradioUpdate]
    # END_CONTRACT

    def update_button_states(self, start_active: bool, stop_active: bool, confirm_active: bool) -> tuple:
        """Генерация gr.update для кнопок."""
        return (
            gr.update(interactive=start_active) if "start_btn" in self._components else None,
            gr.update(interactive=stop_active) if "stop_btn" in self._components else None,
            gr.update(interactive=confirm_active) if "confirm_btn" in self._components else None,
        )

    # END_METHOD_update_button_states

    # START_METHOD_update_active_tab
    # START_CONTRACT:
    # PURPOSE: Генерация gr.update для переключения вкладки.
    # INPUTS:
    # - stage: str — текущий этап
    # OUTPUTS:
    # - gr.update — обновление для переключения вкладки
    # KEYWORDS: [CONCEPT(5): TabNavigation; TECH(4): GradioUpdate]
    # END_CONTRACT

    def update_active_tab(self, stage: str) -> Any:
        """Генерация gr.update для переключения вкладки."""
        stage_to_tab = {
            "SELECTING_LIST": "tab_stage_1",
            "GENERATING": "tab_stage_2",
            "FINISHED": "tab_stage_3",
            "IDLE": "tab_stage_3",
        }
        return gr.update(selected=stage_to_tab.get(stage, "tab_stage_1"))

    # END_METHOD_update_active_tab


# END_CLASS_UIBuilder
