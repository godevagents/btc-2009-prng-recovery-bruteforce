# FILE: src/monitor/ui/components.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Модуль переиспользуемых Gradio-компонентов. Содержит готовые UI-компоненты для мониторинга генератора кошельков: карточки статистики, прогресс-бары, алерты, графики, таблицы.
# SCOPE: UI компоненты, Gradio-виджеты, визуализация данных
# INPUT: Нет (модуль предоставляет функции создания компонентов)
# OUTPUT: Gradio компоненты: gr.HTML, gr.Button, gr.LinePlot, gr.BarPlot, gr.JSON, gr.Dataframe, gr.Number, gr.Dropdown, gr.Slider, gr.CheckboxGroup
# KEYWORDS: DOMAIN(9): UI Components; DOMAIN(8): Gradio; DOMAIN(7): Visualization; CONCEPT(6): Reusable Components; TECH(5): Python
# LINKS: [USES(6): gradio; USES(5): numpy]
# LINKS_TO_SPECIFICATION: Требования к UI компонентам из dev_plan_ui_components.md
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# FUNC 10 [Создаёт карточку статистики с иконкой и значением] => create_stats_card
# FUNC 9 [Создаёт прогресс-бар с процентом выполнения] => create_progress_bar
# FUNC 9 [Создаёт alert-компонент для отображения сообщений] => create_alert
# FUNC 8 [Создаёт вкладку с компонентами] => create_tab
# FUNC 7 [Создаёт группу кнопок] => create_button_group
# FUNC 8 [Создаёт линейный график] => create_line_chart
# FUNC 8 [Создаёт столбчатую диаграмму] => create_bar_chart
# FUNC 7 [Создаёт JSON-просмотрщик] => create_json_viewer
# FUNC 7 [Создаёт таблицу данных] => create_data_table
# FUNC 7 [Создаёт строку статистик] => create_stats_row
# FUNC 8 [Создаёт заголовок страницы] => create_header
# FUNC 7 [Создаёт футер страницы] => create_footer
# FUNC 6 [Создаёт разделитель] => create_divider
# FUNC 6 [Создаёт индикатор загрузки] => create_loading_spinner
# FUNC 7 [Обновляет карточку статистики] => update_stats_card
# FUNC 6 [Форматирует число с разделителями] => format_number
# FUNC 7 [Создаёт выпадающий список] => create_dropdown
# FUNC 6 [Создаёт слайдер] => create_slider
# FUNC 6 [Создаёт группу чекбоксов] => create_checkbox_group
# FUNC 8 [Создаёт карточку метрики] => create_metric_card
# FUNC 8 [Создаёт бейдж статуса] => create_status_badge
# END_MODULE_MAP
# START_USE_CASES:
# - [create_stats_card]: MonitorApp (Runtime) -> DisplayStatistics -> StatsCardRendered
# - [create_progress_bar]: MonitorApp (Runtime) -> DisplayProgress -> ProgressBarRendered
# - [create_alert]: MonitorApp (Runtime) -> DisplayAlert -> AlertMessageShown
# - [create_header]: MonitorApp (Startup) -> DisplayHeader -> HeaderRendered
# - [create_line_chart]: MonitorApp (Runtime) -> DisplayChart -> LineChartRendered
# END_USE_CASES
# За описанием заголовка идет секция импорта

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import gradio as gr
import numpy as np

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
logger.debug(f"[ModuleInit][ui/components][SetupLogger] Логгер модуля components инициализирован [SUCCESS]")


# START_FUNCTION_CREATE_STATS_CARD
# START_CONTRACT:
# PURPOSE: Создаёт визуальную карточку статистики с меткой, значением, иконкой и цветом для отображения статистических данных в мониторинге.
# INPUTS:
# - label: str — метка карточки (например: "Всего адресов")
# - value: Any — отображаемое значение (число, строка)
# - icon: str — иконка (emoji) для визуального обозначения
# - color: str — цвет карточки в HEX-формате
# OUTPUTS:
# - gr.HTML — Gradio HTML-компонент карточки
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Components; PATTERN(7): Statistics; TECH(6): Gradio; CONCEPT(5): Card
# LINKS: [CALLS(5): None]
# END_CONTRACT

def create_stats_card(
    label: str,
    value: Any,
    icon: str = "",
    color: str = "#2196F3",
) -> gr.HTML:
    """
    Создание карточки статистики с иконкой и значением.
    """
    logger.debug(f"[create_stats_card][InputParams] label={label}, value={value}, icon={icon}, color={color} [ATTEMPT]")
    
    # START_BLOCK_BUILD_HTML: [Формирование HTML-кода карточки]
    html = f"""
    <div style="
        padding: 15px;
        background: {color}15;
        border-left: 4px solid {color};
        border-radius: 8px;
        margin: 5px;
    ">
        <div style="font-size: 12px; color: #666;">{icon} {label}</div>
        <div style="font-size: 24px; font-weight: bold; color: {color};">{value}</div>
    </div>
    """
    # END_BLOCK_BUILD_HTML
    
    logger.debug(f"[create_stats_card][BuildHTML][ReturnData] HTML карточки создан, длина={len(html)} [SUCCESS]")
    
    result = gr.HTML(value=html, visible=True)
    logger.debug(f"[create_stats_card][ReturnData] Компонент gr.HTML создан [SUCCESS]")
    
    return result


# END_FUNCTION_CREATE_STATS_CARD


# START_FUNCTION_CREATE_PROGRESS_BAR
# START_CONTRACT:
# PURPOSE: Создаёт горизонтальный прогресс-бар с отображением процента выполнения для визуализации прогресса длительных операций.
# INPUTS:
# - value: float — значение прогресса от 0 до 100
# - label: str — метка прогресс-бара
# - color: str — цвет заполнения в HEX-формате
# - show_percentage: bool — флаг отображения процента
# OUTPUTS:
# - gr.HTML — Gradio HTML-компонент прогресс-бара
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Components; PATTERN(7): Progress; TECH(6): Gradio; CONCEPT(5): Visualization
# LINKS: [CALLS(5): None]
# END_CONTRACT

def create_progress_bar(
    value: float,
    label: str = "Прогресс",
    color: str = "#4CAF50",
    show_percentage: bool = True,
) -> gr.HTML:
    """
    Создание прогресс-бара с процентом выполнения.
    """
    logger.debug(f"[create_progress_bar][InputParams] value={value}, label={label}, show_percentage={show_percentage} [ATTEMPT]")
    
    # START_BLOCK_CLAMP_VALUE: [Ограничение значения в диапазоне 0-100]
    percentage = min(max(value, 0), 100)
    logger.debug(f"[create_progress_bar][ClampValue][ConditionCheck] Процент после ограничения: {percentage} [{'SUCCESS' if 0 <= percentage <= 100 else 'FAIL'}]")
    # END_BLOCK_CLAMP_VALUE
    
    # START_BLOCK_BUILD_HTML: [Формирование HTML-кода прогресс-бара]
    html = f"""
    <div style="margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
            <span style="font-weight: bold;">{label}</span>
            {"<span>" + f"{percentage:.1f}%" + "</span>" if show_percentage else ""}
        </div>
        <div style="
            width: 100%;
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
        ">
            <div style="
                width: {percentage}%;
                height: 100%;
                background: linear-gradient(90deg, {color}, {color}dd);
                border-radius: 10px;
                transition: width 0.3s ease;
            "></div>
        </div>
    </div>
    """
    # END_BLOCK_BUILD_HTML
    
    logger.debug(f"[create_progress_bar][BuildHTML][ReturnData] HTML прогресс-бара создан [SUCCESS]")
    
    result = gr.HTML(value=html)
    logger.debug(f"[create_progress_bar][ReturnData] Компонент gr.HTML создан [SUCCESS]")
    
    return result


# END_FUNCTION_CREATE_PROGRESS_BAR


# START_FUNCTION_CREATE_ALERT
# START_CONTRACT:
# PURPOSE: Создаёт alert-компонент для отображения информационных, успешных, предупреждающих или ошибчных сообщений пользователю.
# INPUTS:
# - message: str — текст сообщения
# - alert_type: str — тип алерта (info, success, warning, error)
# - title: Optional[str] — заголовок алерта
# OUTPUTS:
# - gr.HTML — Gradio HTML-компонент алерта
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Components; PATTERN(7): Alert; TECH(6): Gradio; CONCEPT(5): Notification
# LINKS: [CALLS(5): None]
# END_CONTRACT

def create_alert(
    message: str,
    alert_type: str = "info",
    title: Optional[str] = None,
) -> gr.HTML:
    """
    Создание alert-компонента для отображения сообщений.
    """
    logger.debug(f"[create_alert][InputParams] alert_type={alert_type}, has_title={title is not None} [ATTEMPT]")
    
    # START_BLOCK_GET_COLORS: [Определение цветов по типу алерта]
    colors = {
        "info": ("#2196F3", "#E3F2FD"),
        "success": ("#4CAF50", "#E8F5E9"),
        "warning": ("#FF9800", "#FFF3E0"),
        "error": ("#F44336", "#FFEBEE"),
    }
    
    icon = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
    }
    # END_BLOCK_GET_COLORS
    
    # START_BLOCK_BUILD_HTML: [Формирование HTML-кода алерта]
    border_color, bg_color = colors.get(alert_type, colors["info"])
    alert_icon = icon.get(alert_type, icon["info"])
    
    title_html = f"<strong style=\"color: #212121;\">{title}</strong><br>" if title else ""
    
    html = f"""
    <div style="
        padding: 15px;
        background: {bg_color};
        border-left: 4px solid {border_color};
        border-radius: 8px;
        margin: 10px 0;
    ">
        <div>{alert_icon} {title_html}{message}</div>
    </div>
    """
    # END_BLOCK_BUILD_HTML
    
    logger.debug(f"[create_alert][BuildHTML][ReturnData] HTML алерта создан, тип={alert_type} [SUCCESS]")
    
    result = gr.HTML(value=html)
    logger.debug(f"[create_alert][ReturnData] Компонент gr.HTML создан [SUCCESS]")
    
    return result


# END_FUNCTION_CREATE_ALERT


# START_FUNCTION_CREATE_TAB
# START_CONTRACT:
# PURPOSE: Создаёт вкладку (Tab) для группировки компонентов внутри Gradio-интерфейса.
# INPUTS:
# - title: str — заголовок вкладки
# - components: List[Any] — список компонентов внутри вкладки
# OUTPUTS:
# - gr.Tab — Gradio компонент вкладки (возвращает None из-за использования context manager)
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Components; PATTERN(7): Tab; TECH(6): Gradio; CONCEPT(5): Layout
# LINKS: [CALLS(5): None]
# END_CONTRACT

def create_tab(
    title: str,
    components: List[Any],
) -> gr.Tab:
    """
    Создание вкладки с компонентами.
    """
    logger.debug(f"[create_tab][InputParams] title={title}, components_count={len(components)} [ATTEMPT]")
    
    with gr.Tab(title):
        for component in components:
            pass  # Компоненты уже созданы
    
    logger.debug(f"[create_tab][ReturnData] Вкладка создана: {title} [SUCCESS]")
    
    return None  # Возвращаем None, так как with self создаёт компонент


# END_FUNCTION_CREATE_TAB


# START_FUNCTION_CREATE_BUTTON_GROUP
# START_CONTRACT:
# PURPOSE: Создаёт группу кнопок с возможностью обработки кликов для действий пользователя.
# INPUTS:
# - buttons: List[Tuple[str, str]] — список кортежей (label, variant) для создания кнопок
# - on_click: Optional[Callable] — обработчик клика
# OUTPUTS:
# - List[gr.Button] — список созданных кнопок
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Components; PATTERN(7): Button; TECH(6): Gradio; CONCEPT(5): Interaction
# LINKS: [CALLS(5): None]
# END_CONTRACT

def create_button_group(
    buttons: List[Tuple[str, str]],
    on_click: Optional[Callable] = None,
) -> List[gr.Button]:
    """
    Создание группы кнопок.
    """
    logger.debug(f"[create_button_group][InputParams] buttons_count={len(buttons)}, has_handler={on_click is not None} [ATTEMPT]")
    
    result = []
    
    for label, variant in buttons:
        btn = gr.Button(value=label, variant=variant)
        if on_click:
            btn.click(on_click)
        result.append(btn)
    
    logger.debug(f"[create_button_group][ReturnData] Создано кнопок: {len(result)} [SUCCESS]")
    
    return result


# END_FUNCTION_CREATE_BUTTON_GROUP


# START_FUNCTION_CREATE_LINE_CHART
# START_CONTRACT:
# PURPOSE: Создаёт линейный график для визуализации временных рядов или зависимостей между двумя переменными.
# INPUTS:
# - x_data: List[float] — данные по оси X
# - y_data: List[float] — данные по оси Y
# - title: str — заголовок графика
# - x_label: str — метка оси X
# - y_label: str — метка оси Y
# - color: str — цвет линии в HEX-формате
# - height: int — высота графика в пикселях
# OUTPUTS:
# - gr.LinePlot — Gradio компонент линейного графика
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Components; PATTERN(7): Chart; TECH(6): Gradio; CONCEPT(5): Visualization
# LINKS: [CALLS(5): None]
# END_CONTRACT

def create_line_chart(
    x_data: List[float],
    y_data: List[float],
    title: str = "График",
    x_label: str = "X",
    y_label: str = "Y",
    color: str = "#2196F3",
    height: int = 200,
) -> gr.LinePlot:
    """
    Создание линейного графика.
    """
    logger.debug(f"[create_line_chart][InputParams] title={title}, data_points={len(x_data)} [ATTEMPT]")
    
    # START_BLOCK_VALIDATE_DATA: [Проверка и валидация данных]
    if not x_data or not y_data:
        x_data = [0]
        y_data = [0]
        logger.warning(f"[create_line_chart][ValidateData][ConditionCheck] Пустые данные, используем заглушки [FAIL]")
    # END_BLOCK_VALIDATE_DATA
    
    # START_BLOCK_BUILD_CHART: [Создание графика]
    data = {"x": x_data, "y": y_data}
    
    result = gr.LinePlot(
        value=data,
        x="x",
        y="y",
        title=title,
        x_label=x_label,
        y_label=y_label,
        height=height,
    )
    # END_BLOCK_BUILD_CHART
    
    logger.debug(f"[create_line_chart][BuildChart][ReturnData] Линейный график создан: {title} [SUCCESS]")
    
    return result


# END_FUNCTION_CREATE_LINE_CHART


# START_FUNCTION_CREATE_BAR_CHART
# START_CONTRACT:
# PURPOSE: Создаёт столбчатую диаграмму для визуализации категориальных данных и сравнения значений между категориями.
# INPUTS:
# - labels: List[str] — метки категорий
# - values: List[float] — значения для каждой категории
# - title: str — заголовок диаграммы
# - x_label: str — метка оси X
# - y_label: str — метка оси Y
# - color: str — цвет столбцов в HEX-формате
# - height: int — высота диаграммы в пикселях
# OUTPUTS:
# - gr.BarPlot — Gradio компонент столбчатой диаграммы
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Components; PATTERN(7): Chart; TECH(6): Gradio; CONCEPT(5): Visualization
# LINKS: [CALLS(5): None]
# END_CONTRACT

def create_bar_chart(
    labels: List[str],
    values: List[float],
    title: str = "Столбчатая диаграмма",
    x_label: str = "Категория",
    y_label: str = "Значение",
    color: str = "#2196F3",
    height: int = 200,
) -> gr.BarPlot:
    """
    Создание столбчатой диаграммы.
    """
    logger.debug(f"[create_bar_chart][InputParams] title={title}, categories={len(labels)} [ATTEMPT]")
    
    # START_BLOCK_VALIDATE_DATA: [Проверка и валидация данных]
    if not labels or not values:
        labels = ["Нет данных"]
        values = [0]
        logger.warning(f"[create_bar_chart][ValidateData][ConditionCheck] Пустые данные, используем заглушки [FAIL]")
    # END_BLOCK_VALIDATE_DATA
    
    # START_BLOCK_BUILD_CHART: [Создание диаграммы]
    data = {"x": labels, "y": values}
    
    result = gr.BarPlot(
        value=data,
        x="x",
        y="y",
        title=title,
        x_label=x_label,
        y_label=y_label,
        height=height,
    )
    # END_BLOCK_BUILD_CHART
    
    logger.debug(f"[create_bar_chart][BuildChart][ReturnData] Столбчатая диаграмма создана: {title} [SUCCESS]")
    
    return result


# END_FUNCTION_CREATE_BAR_CHART


# START_FUNCTION_CREATE_JSON_VIEWER
# START_CONTRACT:
# PURPOSE: Создаёт JSON-просмотрщик для отображения структурированных данных в формате JSON.
# INPUTS:
# - data: Dict[str, Any] — словарь данных для отображения
# - label: str — метка компонента
# - expanded: bool — флаг разворачивания по умолчанию
# OUTPUTS:
# - gr.JSON — Gradio JSON-компонент
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Components; PATTERN(7): JSON; TECH(6): Gradio; CONCEPT(5): Data Display
# LINKS: [CALLS(5): None]
# END_CONTRACT

def create_json_viewer(
    data: Dict[str, Any],
    label: str = "JSON",
    expanded: bool = True,
) -> gr.JSON:
    """
    Создание JSON-просмотрщика.
    """
    logger.debug(f"[create_json_viewer][InputParams] label={label}, keys_count={len(data)} [ATTEMPT]")
    
    result = gr.JSON(value=data, label=label)
    
    logger.debug(f"[create_json_viewer][ReturnData] JSON-просмотрщик создан: {label} [SUCCESS]")
    
    return result


# END_FUNCTION_CREATE_JSON_VIEWER


# START_FUNCTION_CREATE_DATA_TABLE
# START_CONTRACT:
# PURPOSE: Создаёт таблицу данных для отображения структурированных данных в виде сетки с заголовками.
# INPUTS:
# - data: List[List[Any]] — двумерный массив данных
# - headers: List[str] — заголовки столбцов
# - label: str — метка таблицы
# - max_height: int — максимальная высота в пикселях
# OUTPUTS:
# - gr.Dataframe — Gradio компонент таблицы
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Components; PATTERN(7): Table; TECH(6): Gradio; CONCEPT(5): Data Display
# LINKS: [CALLS(5): None]
# END_CONTRACT

def create_data_table(
    data: List[List[Any]],
    headers: List[str],
    label: str = "Таблица",
    max_height: int = 300,
) -> gr.Dataframe:
    """
    Создание таблицы данных.
    """
    logger.debug(f"[create_data_table][InputParams] label={label}, rows={len(data)}, cols={len(headers)} [ATTEMPT]")
    
    result = gr.Dataframe(
        value=data,
        headers=headers,
        label=label,
        max_height=max_height,
    )
    
    logger.debug(f"[create_data_table][ReturnData] Таблица создана: {label} [SUCCESS]")
    
    return result


# END_FUNCTION_CREATE_DATA_TABLE


# START_FUNCTION_CREATE_STATS_ROW
# START_CONTRACT:
# PURPOSE: Создаёт строку статистических компонентов для отображения набора метрик в одну линию.
# INPUTS:
# - stats: Dict[str, Tuple[Any, str]] — словарь {label: (value, color)}
# OUTPUTS:
# - List[gr.Number] — список числовых компонентов
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Components; PATTERN(7): Statistics; TECH(6): Gradio; CONCEPT(5): Layout
# LINKS: [CALLS(5): None]
# END_CONTRACT

def create_stats_row(
    stats: Dict[str, Tuple[Any, str]],
) -> List[gr.Number]:
    """
    Создание строки статистик.
    """
    logger.debug(f"[create_stats_row][InputParams] stats_count={len(stats)} [ATTEMPT]")
    
    result = []
    
    for label, (value, color) in stats.items():
        component = gr.Number(
            label=label,
            value=value,
            interactive=False,
        )
        result.append(component)
    
    logger.debug(f"[create_stats_row][ReturnData] Создано компонентов: {len(result)} [SUCCESS]")
    
    return result


# END_FUNCTION_CREATE_STATS_ROW


# START_FUNCTION_CREATE_HEADER
# START_CONTRACT:
# PURPOSE: Создаёт визуальный заголовок страницы с градиентным фоном, иконкой и опциональным подзаголовком.
# INPUTS:
# - title: str — основной заголовок
# - subtitle: Optional[str] — подзаголовок
# - icon: str — иконка (emoji)
# OUTPUTS:
# - gr.HTML — Gradio HTML-компонент заголовка
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Components; PATTERN(7): Header; TECH(6): Gradio; CONCEPT(5): Layout
# LINKS: [CALLS(5): None]
# END_CONTRACT

def create_header(
    title: str,
    subtitle: Optional[str] = None,
    icon: str = "📊",
) -> gr.HTML:
    """
    Создание заголовка страницы.
    """
    logger.debug(f"[create_header][InputParams] title={title}, has_subtitle={subtitle is not None} [ATTEMPT]")
    
    # START_BLOCK_BUILD_HTML: [Формирование HTML-заголовка]
    subtitle_html = f'<p style="margin: 5px 0 0 0; font-size: 14px; color: #666;">{subtitle}</p>' if subtitle else ""
    
    html = f"""
    <div style="
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        margin-bottom: 20px;
    ">
        <h1 style="margin: 0; color: white; font-size: 28px;">{icon} {title}</h1>
        {subtitle_html}
    </div>
    """
    # END_BLOCK_BUILD_HTML
    
    logger.debug(f"[create_header][BuildHTML][ReturnData] Заголовок создан: {title} [SUCCESS]")
    
    result = gr.HTML(value=html)
    
    return result


# END_FUNCTION_CREATE_HEADER


# START_FUNCTION_CREATE_FOOTER
# START_CONTRACT:
# PURPOSE: Создаёт футер страницы с информацией о приложении и опциональным текстом.
# INPUTS:
# - text: str — текст футера
# OUTPUTS:
# - gr.HTML — Gradio HTML-компонент футера
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Components; PATTERN(7): Footer; TECH(6): Gradio; CONCEPT(5): Layout
# LINKS: [CALLS(5): None]
# END_CONTRACT

def create_footer(
    text: str = "WALLET.DAT.GENERATOR Monitor",
) -> gr.HTML:
    """
    Создание футера страницы.
    """
    logger.debug(f"[create_footer][InputParams] text={text} [ATTEMPT]")
    
    # START_BLOCK_BUILD_HTML: [Формирование HTML-футера]
    html = f"""
    <div style="
        padding: 15px;
        background: #f5f5f5;
        border-radius: 8px;
        margin-top: 20px;
        text-align: center;
        color: #666;
        font-size: 12px;
    ">
        {text}
    </div>
    """
    # END_BLOCK_BUILD_HTML
    
    logger.debug(f"[create_footer][BuildHTML][ReturnData] Футер создан [SUCCESS]")
    
    result = gr.HTML(value=html)
    
    return result


# END_FUNCTION_CREATE_FOOTER


# START_FUNCTION_CREATE_DIVIDER
# START_CONTRACT:
# PURPOSE: Создаёт визуальный разделитель между секциями интерфейса с опциональной меткой.
# INPUTS:
# - label: Optional[str] — метка разделителя
# OUTPUTS:
# - gr.HTML — Gradio HTML-компонент разделителя
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Components; PATTERN(7): Divider; TECH(6): Gradio; CONCEPT(5): Layout
# LINKS: [CALLS(5): None]
# END_CONTRACT

def create_divider(
    label: Optional[str] = None,
) -> gr.HTML:
    """
    Создание разделителя.
    """
    logger.debug(f"[create_divider][InputParams] has_label={label is not None} [ATTEMPT]")
    
    # START_BLOCK_BUILD_HTML: [Формирование HTML-разделителя]
    if label:
        html = f"""
        <div style="margin: 20px 0; border-top: 1px solid #e0e0e0; position: relative;">
            <span style="
                position: absolute;
                top: -10px;
                left: 50%;
                transform: translateX(-50%);
                background: white;
                padding: 0 10px;
                color: #888;
                font-size: 12px;
            ">{label}</span>
        </div>
        """
    else:
        html = '<hr style="margin: 20px 0; border: none; border-top: 1px solid #e0e0e0;">'
    # END_BLOCK_BUILD_HTML
    
    logger.debug(f"[create_divider][BuildHTML][ReturnData] Разделитель создан [SUCCESS]")
    
    result = gr.HTML(value=html)
    
    return result


# END_FUNCTION_CREATE_DIVIDER


# START_FUNCTION_CREATE_LOADING_SPINNER
# START_CONTRACT:
# PURPOSE: Создаёт анимированный индикатор загрузки с вращающимся спиннером и сообщением.
# INPUTS:
# - message: str — сообщение загрузки
# - color: str — цвет спиннера в HEX-формате
# OUTPUTS:
# - gr.HTML — Gradio HTML-компонент спиннера
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Components; PATTERN(7): Loading; TECH(6): Gradio; CONCEPT(5): Animation
# LINKS: [CALLS(5): None]
# END_CONTRACT

def create_loading_spinner(
    message: str = "Загрузка...",
    color: str = "#2196F3",
) -> gr.HTML:
    """
    Создание индикатора загрузки.
    """
    logger.debug(f"[create_loading_spinner][InputParams] message={message} [ATTEMPT]")
    
    # START_BLOCK_BUILD_HTML: [Формирование HTML-спиннера]
    html = f"""
    <div style="text-align: center; padding: 30px;">
        <div style="
            width: 40px;
            height: 40px;
            border: 4px solid {color}20;
            border-top: 4px solid {color};
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        "></div>
        <p style="margin-top: 15px; color: #666;">{message}</p>
        <style>
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </div>
    """
    # END_BLOCK_BUILD_HTML
    
    logger.debug(f"[create_loading_spinner][BuildHTML][ReturnData] Спиннер создан [SUCCESS]")
    
    result = gr.HTML(value=html)
    
    return result


# END_FUNCTION_CREATE_LOADING_SPINNER


# START_FUNCTION_UPDATE_STATS_CARD
# START_CONTRACT:
# PURPOSE: Обновляет существующую карточку статистики новыми значениями без пересоздания компонента.
# INPUTS:
# - component: gr.HTML — существующий компонент
# - value: Any — новое значение
# - label: Optional[str] — новая метка
# - icon: Optional[str] — новая иконка
# - color: Optional[str] — новый цвет
# OUTPUTS:
# - gr.HTML — обновлённый компонент
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Components; PATTERN(7): Update; TECH(6): Gradio; CONCEPT(5): State
# LINKS: [CALLS(8): create_stats_card]
# END_CONTRACT

def update_stats_card(
    component: gr.HTML,
    value: Any,
    label: Optional[str] = None,
    icon: Optional[str] = None,
    color: Optional[str] = None,
) -> gr.HTML:
    """
    Обновление карточки статистики.
    """
    logger.debug(f"[update_stats_card][InputParams] value={value} [ATTEMPT]")
    
    # Для обновления используется create_stats_card
    result = create_stats_card(
        label=label or "Значение",
        value=value,
        icon=icon or "",
        color=color or "#2196F3",
    )
    
    logger.debug(f"[update_stats_card][ReturnData] Карточка обновлена [SUCCESS]")
    
    return result


# END_FUNCTION_UPDATE_STATS_CARD


# START_FUNCTION_FORMAT_NUMBER
# START_CONTRACT:
# PURPOSE: Форматирует число с разделителями тысяч и опциональными суффиксами (K, M) для удобочитаемости.
# INPUTS:
# - value: float — число для форматирования
# - precision: int — количество знаков после запятой
# - suffix: str — суффикс (например: "адресов", "ключей")
# OUTPUTS:
# - str — отформатированная строка
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(7): Utilities; PATTERN(7): Format; TECH(5): String; CONCEPT(5): Number
# LINKS: [CALLS(5): None]
# END_CONTRACT

def format_number(
    value: float,
    precision: int = 0,
    suffix: str = "",
) -> str:
    """
    Форматирование числа с разделителями.
    """
    logger.debug(f"[format_number][InputParams] value={value}, precision={precision} [ATTEMPT]")
    
    # START_BLOCK_FORMAT: [Форматирование числа]
    if value >= 1_000_000:
        formatted = f"{value / 1_000_000:.{precision}f}M"
    elif value >= 1_000:
        formatted = f"{value / 1_000:.{precision}f}K"
    else:
        formatted = f"{value:.{precision}f}"
    # END_BLOCK_FORMAT
    
    result = formatted + suffix
    
    logger.debug(f"[format_number][ReturnData] Форматированное значение: {result} [SUCCESS]")
    
    return result


# END_FUNCTION_FORMAT_NUMBER


# START_FUNCTION_CREATE_DROPDOWN
# START_CONTRACT:
# PURPOSE: Создаёт выпадающий список (Dropdown) для выбора одного значения из предложенных вариантов.
# INPUTS:
# - choices: List[str] — список вариантов для выбора
# - label: str — метка компонента
# - value: Optional[str] — значение по умолчанию
# - info: Optional[str] — подсказка
# OUTPUTS:
# - gr.Dropdown — Gradio компонент выпадающего списка
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Components; PATTERN(7): Dropdown; TECH(6): Gradio; CONCEPT(5): Selection
# LINKS: [CALLS(5): None]
# END_CONTRACT

def create_dropdown(
    choices: List[str],
    label: str,
    value: Optional[str] = None,
    info: Optional[str] = None,
) -> gr.Dropdown:
    """
    Создание выпадающего списка.
    """
    logger.debug(f"[create_dropdown][InputParams] label={label}, choices={len(choices)} [ATTEMPT]")
    
    result = gr.Dropdown(
        choices=choices,
        label=label,
        value=value,
        info=info,
    )
    
    logger.debug(f"[create_dropdown][ReturnData] Выпадающий список создан: {label} [SUCCESS]")
    
    return result


# END_FUNCTION_CREATE_DROPDOWN


# START_FUNCTION_CREATE_SLIDER
# START_CONTRACT:
# PURPOSE: Создаёт слайдер для выбора числового значения в заданном диапазоне.
# INPUTS:
# - minimum: float — минимальное значение
# - maximum: float — максимальное значение
# - value: float — значение по умолчанию
# - step: float — шаг изменения
# - label: str — метка компонента
# - info: Optional[str] — подсказка
# OUTPUTS:
# - gr.Slider — Gradio компонент слайдера
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Components; PATTERN(7): Slider; TECH(6): Gradio; CONCEPT(5): Input
# LINKS: [CALLS(5): None]
# END_CONTRACT

def create_slider(
    minimum: float = 0,
    maximum: float = 100,
    value: float = 50,
    step: float = 1,
    label: str = "Значение",
    info: Optional[str] = None,
) -> gr.Slider:
    """
    Создание слайдера.
    """
    logger.debug(f"[create_slider][InputParams] label={label}, range=[{minimum}, {maximum}] [ATTEMPT]")
    
    result = gr.Slider(
        minimum=minimum,
        maximum=maximum,
        value=value,
        step=step,
        label=label,
        info=info,
    )
    
    logger.debug(f"[create_slider][ReturnData] Слайдер создан: {label} [SUCCESS]")
    
    return result


# END_FUNCTION_CREATE_SLIDER


# START_FUNCTION_CREATE_CHECKBOX_GROUP
# START_CONTRACT:
# PURPOSE: Создаёт группу чекбоксов для множественного выбора из предложенных вариантов.
# INPUTS:
# - choices: List[str] — список вариантов
# - label: str — метка компонента
# - value: Optional[List[str]] — выбранные значения по умолчанию
# - info: Optional[str] — подсказка
# OUTPUTS:
# - gr.CheckboxGroup — Gradio компонент группы чекбоксов
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Components; PATTERN(7): Checkbox; TECH(6): Gradio; CONCEPT(5): Selection
# LINKS: [CALLS(5): None]
# END_CONTRACT

def create_checkbox_group(
    choices: List[str],
    label: str,
    value: Optional[List[str]] = None,
    info: Optional[str] = None,
) -> gr.CheckboxGroup:
    """
    Создание группы чекбоксов.
    """
    logger.debug(f"[create_checkbox_group][InputParams] label={label}, choices={len(choices)} [ATTEMPT]")
    
    result = gr.CheckboxGroup(
        choices=choices,
        label=label,
        value=value,
        info=info,
    )
    
    logger.debug(f"[create_checkbox_group][ReturnData] Группа чекбоксов создана: {label} [SUCCESS]")
    
    return result


# END_FUNCTION_CREATE_CHECKBOX_GROUP


# START_FUNCTION_CREATE_METRIC_CARD
# START_CONTRACT:
# PURPOSE: Создаёт визуальную карточку метрики с меткой, значением, единицей измерения, иконкой, цветом и опциональным трендом для отображения метрик мониторинга.
# INPUTS:
# - label: str — метка метрики (например: "Итераций/сек")
# - value: Any — значение метрики
# - unit: str — единица измерения (например: "i/s", "MB")
# - icon: str — иконка (emoji) для визуального обозначения
# - color: str — цвет карточки в HEX-формате
# - trend: Optional[str] — тренд (up/down/stable)
# OUTPUTS:
# - gr.HTML — Gradio HTML-компонент карточки метрики
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Components; PATTERN(7): MetricCard; TECH(6): Gradio; CONCEPT(5): Visualization
# END_CONTRACT

def create_metric_card(
    label: str,
    value: Any,
    unit: str = "",
    icon: str = "",
    color: str = "#2196F3",
    trend: Optional[str] = None,
) -> gr.HTML:
    """
    Создание карточки метрики с отображением тренда.
    """
    logger.debug(f"[create_metric_card][InputParams] label={label}, value={value}, unit={unit}, trend={trend} [ATTEMPT]")
    
    # START_BLOCK_GET_TREND: [Определение иконки тренда]
    trend_icons = {
        "up": "📈",
        "down": "📉",
        "stable": "➡️",
    }
    trend_icon = trend_icons.get(trend, "") if trend else ""
    # END_BLOCK_GET_TREND
    
    # START_BLOCK_BUILD_HTML: [Формирование HTML-кода карточки]
    unit_html = f'<span style="font-size: 14px; color: #666;"> {unit}</span>' if unit else ""
    
    html = f"""
    <div style="
        padding: 16px;
        background: {color}10;
        border-left: 4px solid {color};
        border-radius: 8px;
        margin: 5px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    ">
        <div>
            <div style="font-size: 12px; color: #666;">{icon} {label}</div>
            <div style="font-size: 28px; font-weight: bold; color: {color};">
                {value}{unit_html}
            </div>
        </div>
        <div style="font-size: 24px;">{trend_icon}</div>
    </div>
    """
    # END_BLOCK_BUILD_HTML
    
    logger.debug(f"[create_metric_card][BuildHTML][ReturnData] HTML карточки метрики создан [SUCCESS]")
    
    result = gr.HTML(value=html, visible=True)
    logger.debug(f"[create_metric_card][ReturnData] Компонент gr.HTML создан [SUCCESS]")
    
    return result


# END_FUNCTION_CREATE_METRIC_CARD


# START_FUNCTION_CREATE_STATUS_BADGE
# START_CONTRACT:
# PURPOSE: Создаёт визуальный бейдж статуса с цветовым индикатором, текстом и опциональной анимацией пульсации для отображения состояния системы.
# INPUTS:
# - status: str — статус: success/warning/error/info/pending
# - text: str — текст статуса
# - pulse: bool — флаг анимации пульсации
# OUTPUTS:
# - gr.HTML — Gradio HTML-компонент бейджа
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Components; PATTERN(7): StatusBadge; TECH(6): Gradio; CONCEPT(5): Indicator
# END_CONTRACT

def create_status_badge(
    status: str,
    text: str,
    pulse: bool = False,
) -> gr.HTML:
    """
    Создание бейджа статуса с анимацией пульсации.
    """
    logger.debug(f"[create_status_badge][InputParams] status={status}, text={text}, pulse={pulse} [ATTEMPT]")
    
    # START_BLOCK_GET_STATUS_STYLE: [Определение стилей по типу статуса]
    status_styles = {
        "success": ("#4CAF50", "#E8F5E9"),
        "warning": ("#FF9800", "#FFF3E0"),
        "error": ("#F44336", "#FFEBEE"),
        "info": ("#2196F3", "#E3F2FD"),
        "pending": ("#9E9E9E", "#F5F5F5"),
    }
    
    status_icons = {
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "info": "ℹ️",
        "pending": "⏳",
    }
    
    border_color, bg_color = status_styles.get(status, status_styles["info"])
    status_icon = status_icons.get(status, "")
    # END_BLOCK_GET_STATUS_STYLE
    
    # START_BLOCK_BUILD_HTML: [Формирование HTML-кода бейджа]
    animation_style = ""
    if pulse:
        animation_style = """
        animation: pulse 2s infinite;
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        """
    
    html = f"""
    <div style="
        padding: 8px 16px;
        background: {bg_color};
        border: 2px solid {border_color};
        border-radius: 20px;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        font-weight: 500;
        color: {border_color};
        {animation_style}
    ">
        <span>{status_icon}</span>
        <span>{text}</span>
    </div>
    """
    # END_BLOCK_BUILD_HTML
    
    logger.debug(f"[create_status_badge][BuildHTML][ReturnData] HTML бейджа статуса создан [SUCCESS]")
    
    result = gr.HTML(value=html, visible=True)
    logger.debug(f"[create_status_badge][ReturnData] Компонент gr.HTML создан [SUCCESS]")
    
    return result


# END_FUNCTION_CREATE_STATUS_BADGE


logger.info(f"[ModuleInit][ui/components][StepComplete] Модуль components загружен, определено {21} функций [SUCCESS]")
