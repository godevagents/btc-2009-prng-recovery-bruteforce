# START_MODULE_CONTRACT:
# PURPOSE: Модуль отслеживания прогресса операций с использованием rich.progress.
# Предоставляет прогресс-бары для визуализации выполнения длительных операций.
# SCOPE: Прогресс-бары, визуализация, tracking
# INPUT: total - общее количество шагов, description - описание операции
# OUTPUT: Класс ProgressTracker с методами start, update, finish
# KEYWORDS: DOMAIN(8): ProgressBar; TECH(6): Rich; CONCEPT(7): Tracking
# LINKS: [USES(7): rich.progress]
# LINKS_TO_SPECIFICATION: [Критерий 3: Используется библиотека rich для визуализации]
# END_MODULE_CONTRACT

"""
Модуль отслеживания прогресса операций.
"""
import logging
from typing import Optional
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn, TimeElapsedColumn
from rich.console import Console

logger = logging.getLogger(__name__)


# START_CLASS_ProgressTracker
# START_CONTRACT:
# PURPOSE: Класс для отслеживания прогресса операций с прогресс-барами.
# Использует rich.progress для визуализации выполнения длительных операций.
# ATTRIBUTES:
# - _progress: Optional[Progress] - объект Progress из rich
# - _task_id: Optional[int] - ID текущей задачи
# - _console: Console - объект консоли для вывода
# - _total: int - общее количество шагов
# - _description: str - описание операции
# METHODS:
# - start(total, description) - запуск отслеживания прогресса
# - update(current) - обновление прогресса
# - finish() - завершение отслеживания прогресса
# KEYWORDS: DOMAIN(8): ProgressBar; TECH(6): Rich; CONCEPT(7): Tracking
# LINKS: []
# END_CONTRACT


class ProgressTracker:
    """
    Класс для отслеживания прогресса операций с прогресс-барами.
    Использует библиотеку rich для красивого консольного вывода.
    """

    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация трекера прогресса.
    # INPUTS:
    # - console: Optional[Console] - объект консоли (опционально)
    # KEYWORDS: CONCEPT(5): Initialization
    # END_CONTRACT
    def __init__(self, console: Optional[Console] = None) -> None:
        """
        Инициализация трекера прогресса.

        Args:
            console: Объект консоли для вывода (опционально).
        """
        logger.debug(f"[SelfCheck][ProgressTracker][INIT] Инициализация ProgressTracker [ATTEMPT]")
        self._console = console if console is not None else Console()
        self._progress: Optional[Progress] = None
        self._task_id: Optional[int] = None
        self._total: int = 0
        self._description: str = ""
        logger.info(f"[TraceCheck][ProgressTracker][INIT][StepComplete] ProgressTracker инициализирован [SUCCESS]")

    # END_METHOD___init__

    # START_METHOD_start
    # START_CONTRACT:
    # PURPOSE: Запуск отслеживания прогресса.
    # INPUTS:
    # - total: int - общее количество шагов
    # - description: str - описание операции
    # OUTPUTS:
    # - None
    # SIDE_EFFECTS: Создает и запускает прогресс-бар
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - Прогресс-бар создан и запущен
    # KEYWORDS: DOMAIN(7): Progress; TECH(6): Rich; CONCEPT(6): Start
    # END_CONTRACT
    def start(self, total: int, description: str = "Processing") -> None:
        """
        Запуск отслеживания прогресса.

        Args:
            total: Общее количество шагов.
            description: Описание операции.
        """
        logger.debug(f"[VarCheck][ProgressTracker][START][Params] total={total}, description={description} [ATTEMPT]")
        self._total = total
        self._description = description

        # Создаем прогресс-бар с использованием rich
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self._console
        )

        self._progress.start()
        self._task_id = self._progress.add_task(description, total=total)
        logger.info(f"[TraceCheck][ProgressTracker][START][StepComplete] Прогресс-бар запущен: {description}, total={total} [SUCCESS]")

    # END_METHOD_start

    # START_METHOD_update
    # START_CONTRACT:
    # PURPOSE: Обновление прогресса.
    # INPUTS:
    # - current: int - текущее значение прогресса
    # OUTPUTS:
    # - None
    # SIDE_EFFECTS: Обновляет значение прогресс-бара
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - Прогресс-бар обновлен с новым значением
    # KEYWORDS: DOMAIN(7): Progress; TECH(6): Rich; CONCEPT(7): Update
    # END_CONTRACT
    def update(self, current: int) -> None:
        """
        Обновление прогресса.

        Args:
            current: Текущее значение прогресса.
        """
        logger.debug(f"[VarCheck][ProgressTracker][UPDATE][Params] current={current} [ATTEMPT]")
        if self._progress is not None and self._task_id is not None:
            self._progress.update(self._task_id, completed=current)
            logger.debug(f"[TraceCheck][ProgressTracker][UPDATE][StepComplete] Прогресс обновлен: {current}/{self._total} [SUCCESS]")
        else:
            logger.warning(f"[VarCheck][ProgressTracker][UPDATE][ConditionCheck] Прогресс не запущен [FAIL]")

    # END_METHOD_update

    # START_METHOD_increment
    # START_CONTRACT:
    # PURPOSE: Увеличение прогресса на указанное значение.
    # INPUTS:
    # - advance: int - значение для увеличения (по умолчанию 1)
    # OUTPUTS:
    # - None
    # SIDE_EFFECTS: Увеличивает значение прогресс-бара
    # KEYWORDS: DOMAIN(7): Progress; TECH(6): Rich; CONCEPT(6): Increment
    # END_CONTRACT
    def increment(self, advance: int = 1) -> None:
        """
        Увеличение прогресса на указанное значение.

        Args:
            advance: Значение для увеличения (по умолчанию 1).
        """
        logger.debug(f"[VarCheck][ProgressTracker][INCREMENT][Params] advance={advance} [ATTEMPT]")
        if self._progress is not None and self._task_id is not None:
            self._progress.update(self._task_id, advance=advance)
            logger.debug(f"[TraceCheck][ProgressTracker][INCREMENT][StepComplete] Прогресс увеличен на {advance} [SUCCESS]")
        else:
            logger.warning(f"[VarCheck][ProgressTracker][INCREMENT][ConditionCheck] Прогресс не запущен [FAIL]")

    # END_METHOD_increment

    # START_METHOD_finish
    # START_CONTRACT:
    # PURPOSE: Завершение отслеживания прогресса.
    # OUTPUTS:
    # - None
    # SIDE_EFFECTS: Останавливает и закрывает прогресс-бар
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - Прогресс-бар завершен и закрыт
    # KEYWORDS: DOMAIN(7): Progress; TECH(6): Rich; CONCEPT(6): Finish
    # END_CONTRACT
    def finish(self) -> None:
        """
        Завершение отслеживания прогресса.
        """
        logger.debug(f"[SelfCheck][ProgressTracker][FINISH] Завершение прогресс-бара [ATTEMPT]")
        if self._progress is not None:
            self._progress.stop()
            logger.info(f"[TraceCheck][ProgressTracker][FINISH][StepComplete] Прогресс-бар завершен [SUCCESS]")
            self._progress = None
            self._task_id = None
        else:
            logger.warning(f"[VarCheck][ProgressTracker][FINISH][ConditionCheck] Прогресс не был запущен [FAIL]")

    # END_METHOD_finish

    # START_METHOD_is_active
    # START_CONTRACT:
    # PURPOSE: Проверка активности прогресс-бара.
    # OUTPUTS:
    # - bool - True если прогресс-бар активен
    # KEYWORDS: CONCEPT(6): Status
    # END_CONTRACT
    def is_active(self) -> bool:
        """
        Проверка активности прогресс-бара.

        Returns:
            True если прогресс-бар активен.
        """
        is_active = self._progress is not None and self._task_id is not None
        logger.debug(f"[VarCheck][ProgressTracker][IS_ACTIVE][ReturnData] is_active={is_active} [VALUE]")
        return is_active

    # END_METHOD_is_active


# END_CLASS_ProgressTracker
