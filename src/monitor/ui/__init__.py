# FILE: src/monitor/ui/__init__.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Модуль UI компонентов мониторинга. Экспортирует переиспользуемые Gradio-компоненты и темы оформления для построения интерфейса мониторинга генератора кошельков.
# SCOPE: UI компоненты, темы оформления, Gradio-интерфейс
# INPUT: Нет (модуль предоставляет импорты)
# OUTPUT: Переиспользуемые компоненты (create_stats_card, create_progress_bar, create_alert и др.) и темы (get_monitor_theme, get_dark_theme, get_custom_theme)
# KEYWORDS: DOMAIN(9): UI Components; DOMAIN(8): Gradio; DOMAIN(7): Themes; CONCEPT(6): Reusable Components; TECH(5): Python
# LINKS: [USES(7): src.monitor.ui.components; USES(7): src.monitor.ui.themes]
# LINKS_TO_SPECIFICATION: Требования к UI мониторинга из dev_plan_monitor_init.md
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# FUNC 10 [Экспорт карточки статистики] => create_stats_card
# FUNC 9 [Экспорт прогресс-бара] => create_progress_bar
# FUNC 9 [Экспорт alert-компонента] => create_alert
# FUNC 8 [Экспорт заголовка] => create_header
# FUNC 8 [Экспорт футера] => create_footer
# FUNC 7 [Экспорт линейного графика] => create_line_chart
# FUNC 7 [Экспорт столбчатой диаграммы] => create_bar_chart
# FUNC 7 [Экспорт JSON-просмотрщика] => create_json_viewer
# FUNC 7 [Экспорт таблицы данных] => create_data_table
# FUNC 9 [Экспорт темы мониторинга] => get_monitor_theme
# FUNC 9 [Экспорт тёмной темы] => get_dark_theme
# FUNC 8 [Экспорт кастомной темы] => get_custom_theme
# FUNC 8 [Экспорт темы по имени] => get_theme
# FUNC 6 [Экспорт всех CSS стилей] => get_all_css
# END_MODULE_MAP
# START_USE_CASES:
# - [create_stats_card]: MonitorApp (Runtime) -> DisplayStatistics -> StatsCardRendered
# - [create_progress_bar]: MonitorApp (Runtime) -> DisplayProgress -> ProgressBarRendered
# - [get_monitor_theme]: MonitorApp (Startup) -> ApplyTheme -> ThemeApplied
# END_USE_CASES
# За описанием заголовка идет секция импорта

import logging
from pathlib import Path

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
        # Console handler для отладки
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger

logger = _setup_logger()
logger.debug(f"[ModuleInit][ui/__init__][SetupLogger] Логгер модуля ui инициализирован [SUCCESS]")

# Экспорт компонентов
from src.monitor.ui.components import (
    create_stats_card,
    create_progress_bar,
    create_alert,
    create_header,
    create_footer,
    create_line_chart,
    create_bar_chart,
    create_json_viewer,
    create_data_table,
)

logger.debug(f"[ModuleInit][ui/__init__][Import] Импортированы компоненты из components.py [SUCCESS]")

# Экспорт тем
from src.monitor.ui.themes import (
    get_monitor_theme,
    get_dark_theme,
    get_custom_theme,
    get_theme,
    get_all_css,
)

logger.debug(f"[ModuleInit][ui/__init__][Import] Импортированы темы из themes.py [SUCCESS]")

__all__ = [
    # Components
    "create_stats_card",
    "create_progress_bar",
    "create_alert",
    "create_header",
    "create_footer",
    "create_line_chart",
    "create_bar_chart",
    "create_json_viewer",
    "create_data_table",
    # Themes
    "get_monitor_theme",
    "get_dark_theme",
    "get_custom_theme",
    "get_theme",
    "get_all_css",
]

logger.info(f"[ModuleInit][ui/__init__][StepComplete] Модуль ui инициализирован, экспортировано {len(__all__)} сущностей [SUCCESS]")
