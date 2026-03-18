# START_MODULE_CONTRACT:
# PURPOSE: Модуль отображения статистики в табличном формате с использованием rich.table.
# Предоставляет табличное представление метрик для визуализации в консоли.
# SCOPE: Статистика, таблицы, визуализация
# INPUT: metrics - словарь метрик для отображения
# OUTPUT: Класс StatsDisplay с методами update, render
# KEYWORDS: DOMAIN(7): Statistics; TECH(6): Rich; CONCEPT(7): TableView
# LINKS: [USES(7): rich.table]
# LINKS_TO_SPECIFICATION: [Критерий 3: Используется библиотека rich для визуализации]
# END_MODULE_CONTRACT

"""
Модуль отображения статистики в табличном формате.
"""
import logging
from typing import Dict, Any, Optional
from rich.table import Table
from rich.console import Console
from rich.text import Text

logger = logging.getLogger(__name__)


# START_CLASS_StatsDisplay
# START_CONTRACT:
# PURPOSE: Класс для отображения статистики в табличном формате.
# Использует rich.table.Table для создания красивых таблиц в консоли.
# ATTRIBUTES:
# - _console: Console - объект консоли для вывода
# - _metrics: Dict[str, Any] - словарь текущих метрик
# - _title: str - заголовок таблицы
# METHODS:
# - update(metrics) - обновление данных статистики
# - render() - отрисовка таблицы статистики
# - get_metrics() - получение текущих метрик
# KEYWORDS: DOMAIN(7): Statistics; TECH(6): Rich; CONCEPT(7): TableView
# LINKS: []
# END_CONTRACT


class StatsDisplay:
    """
    Класс для отображения статистики в табличном формате.
    Использует библиотеку rich для создания красивых таблиц в консоли.
    """

    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация отображения статистики.
    # INPUTS:
    # - console: Optional[Console] - объект консоли (опционально)
    # - title: str - заголовок таблицы (опционально)
    # KEYWORDS: CONCEPT(5): Initialization
    # END_CONTRACT
    def __init__(self, console: Optional[Console] = None, title: str = "Статистика мониторинга") -> None:
        """
        Инициализация отображения статистики.

        Args:
            console: Объект консоли для вывода (опционально).
            title: Заголовок таблицы (опционально).
        """
        logger.debug(f"[SelfCheck][StatsDisplay][INIT] Инициализация StatsDisplay [ATTEMPT]")
        self._console = console if console is not None else Console()
        self._title = title
        self._metrics: Dict[str, Any] = {
            "wallets_generated": 0,
            "matches_found": 0
        }
        logger.info(f"[TraceCheck][StatsDisplay][INIT][StepComplete] StatsDisplay инициализирован [SUCCESS]")

    # END_METHOD___init__

    # START_METHOD_update
    # START_CONTRACT:
    # PURPOSE: Обновление данных статистики.
    # INPUTS:
    # - metrics: Dict[str, Any] - словарь метрик для обновления
    # OUTPUTS:
    # - None
    # SIDE_EFFECTS: Обновляет внутренний словарь метрик
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - Словарь метрик обновлен
    # KEYWORDS: DOMAIN(7): Statistics; TECH(6): Rich; CONCEPT(7): Update
    # END_CONTRACT
    def update(self, metrics: Dict[str, Any]) -> None:
        """
        Обновление данных статистики.

        Args:
            metrics: Словарь метрик для обновления.
        """
        logger.debug(f"[VarCheck][StatsDisplay][UPDATE][Params] metrics={metrics} [ATTEMPT]")
        self._metrics.update(metrics)
        logger.info(f"[TraceCheck][StatsDisplay][UPDATE][StepComplete] Метрики обновлены: {self._metrics} [SUCCESS]")

    # END_METHOD_update

    # START_METHOD_update_wallets_count
    # START_CONTRACT:
    # PURPOSE: Обновление количества сгенерированных кошельков.
    # INPUTS:
    # - count: int - количество кошельков
    # OUTPUTS:
    # - None
    # KEYWORDS: DOMAIN(6): Wallets; CONCEPT(6): Counter
    # END_CONTRACT
    def update_wallets_count(self, count: int) -> None:
        """
        Обновление количества сгенерированных кошельков.

        Args:
            count: Количество кошельков.
        """
        logger.debug(f"[VarCheck][StatsDisplay][UPDATE_WALLETS_COUNT][Params] count={count} [ATTEMPT]")
        self._metrics["wallets_generated"] = count
        logger.info(f"[TraceCheck][StatsDisplay][UPDATE_WALLETS_COUNT][StepComplete] Обновлено wallets_generated={count} [SUCCESS]")

    # END_METHOD_update_wallets_count

    # START_METHOD_update_matches_count
    # START_CONTRACT:
    # PURPOSE: Обновление количества найденных совпадений.
    # INPUTS:
    # - count: int - количество совпадений
    # OUTPUTS:
    # - None
    # KEYWORDS: DOMAIN(6): Matches; CONCEPT(6): Counter
    # END_CONTRACT
    def update_matches_count(self, count: int) -> None:
        """
        Обновление количества найденных совпадений.

        Args:
            count: Количество совпадений.
        """
        logger.debug(f"[VarCheck][StatsDisplay][UPDATE_MATCHES_COUNT][Params] count={count} [ATTEMPT]")
        self._metrics["matches_found"] = count
        logger.info(f"[TraceCheck][StatsDisplay][UPDATE_MATCHES_COUNT][StepComplete] Обновлено matches_found={count} [SUCCESS]")

    # END_METHOD_update_matches_count

    # START_METHOD_render
    # START_CONTRACT:
    # PURPOSE: Отрисовка таблицы статистики.
    # OUTPUTS:
    # - Table - объект таблицы rich
    # SIDE_EFFECTS: Выводит таблицу в консоль
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - Таблица отображена в консоли
    # KEYWORDS: DOMAIN(7): Statistics; TECH(6): Rich; CONCEPT(6): Render
    # END_CONTRACT
    def render(self) -> Table:
        """
        Отрисовка таблицы статистики.

        Returns:
            Table: Объект таблицы rich.
        """
        logger.debug(f"[SelfCheck][StatsDisplay][RENDER] Создание таблицы статистики [ATTEMPT]")

        # Создаем таблицу
        table = Table(title=self._title, show_header=True, header_style="bold magenta")

        # Добавляем колонки
        table.add_column("Метрика", style="cyan", width=30)
        table.add_column("Значение", style="green", width=20, justify="right")

        # Добавляем строки с метриками
        for key, value in self._metrics.items():
            # Форматируем имя метрики для отображения
            display_key = self._format_metric_name(key)
            table.add_row(display_key, str(value))

        logger.info(f"[TraceCheck][StatsDisplay][RENDER][StepComplete] Таблица создана с {len(self._metrics)} метриками [SUCCESS]")
        return table

    # END_METHOD_render

    # START_METHOD_display
    # START_CONTRACT:
    # PURPOSE: Отображение таблицы статистики в консоли.
    # OUTPUTS:
    # - None
    # SIDE_EFFECTS: Выводит таблицу в консоль
    # KEYWORDS: TECH(6): Rich; CONCEPT(6): Display
    # END_CONTRACT
    def display(self) -> None:
        """
        Отображение таблицы статистики в консоли.
        """
        logger.debug(f"[SelfCheck][StatsDisplay][DISPLAY] Отображение таблицы в консоли [ATTEMPT]")
        table = self.render()
        self._console.print(table)
        logger.info(f"[TraceCheck][StatsDisplay][DISPLAY][StepComplete] Таблица отображена в консоли [SUCCESS]")

    # END_METHOD_display

    # START_METHOD_get_metrics
    # START_CONTRACT:
    # PURPOSE: Получение текущих метрик.
    # OUTPUTS:
    # - Dict[str, Any] - словарь текущих метрик
    # KEYWORDS: CONCEPT(6): Getter
    # END_CONTRACT
    def get_metrics(self) -> Dict[str, Any]:
        """
        Получение текущих метрик.

        Returns:
            Словарь текущих метрик.
        """
        logger.debug(f"[VarCheck][StatsDisplay][GET_METRICS][ReturnData] Возврат метрик: {self._metrics} [VALUE]")
        return self._metrics.copy()

    # END_METHOD_get_metrics

    # START_METHOD_reset
    # START_CONTRACT:
    # PURPOSE: Сброс метрик к начальным значениям.
    # OUTPUTS:
    # - None
    # SIDE_EFFECTS: Сбрасывает все метрики до 0
    # KEYWORDS: CONCEPT(6): Reset
    # END_CONTRACT
    def reset(self) -> None:
        """
        Сброс метрик к начальным значениям.
        """
        logger.debug(f"[SelfCheck][StatsDisplay][RESET] Сброс метрик [ATTEMPT]")
        self._metrics = {
            "wallets_generated": 0,
            "matches_found": 0
        }
        logger.info(f"[TraceCheck][StatsDisplay][RESET][StepComplete] Метрики сброшены [SUCCESS]")

    # END_METHOD_reset

    # START_METHOD_format_metric_name
    # START_CONTRACT:
    # PURPOSE: Форматирование имени метрики для отображения.
    # INPUTS:
    # - name: str - имя метрики
    # OUTPUTS:
    # - str - отформатированное имя метрики
    # KEYWORDS: CONCEPT(7): Formatting
    # END_CONTRACT
    def _format_metric_name(self, name: str) -> str:
        """
        Форматирование имени метрики для отображения.

        Args:
            name: Имя метрики.

        Returns:
            Отформатированное имя метрики.
        """
        # Заменяем underscores на пробелы и делаем первую букву заглавной
        formatted = name.replace("_", " ").title()
        logger.debug(f"[VarCheck][StatsDisplay][FORMAT_METRIC_NAME][ReturnData] {name} -> {formatted} [VALUE]")
        return formatted

    # END_METHOD_format_metric_name


# END_CLASS_StatsDisplay
