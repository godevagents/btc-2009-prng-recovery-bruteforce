# START_MODULE_CONTRACT:
# PURPOSE: Главный модуль мониторинга для визуализации прогресса генерации кошельков и поиска совпадений.
# Координирует работу ProgressTracker, StatsDisplay и MonitorObserver для комплексного мониторинга.
# SCOPE: Мониторинг, метрики, визуализация
# INPUT: console - объект консоли, show_progress - флаг показа прогресс-бара
# OUTPUT: Класс Monitor с методами update_wallets_count, update_matches_count, start, stop, display
# KEYWORDS: DOMAIN(9): Monitoring; TECH(7): Rich; CONCEPT(8): Coordination
# LINKS: [USES(7): ProgressTracker; USES(7): StatsDisplay; USES(8): MonitorObserver]
# LINKS_TO_SPECIFICATION: [Критерий 1: Модуль мониторинга создается в директории src/plugins/wallet/monitor/, Критерий 2: Класс Monitor имеет методы update_wallets_count() и update_matches_count()]
# END_MODULE_CONTRACT

"""
Главный модуль мониторинга для визуализации прогресса.
"""
import logging
from typing import Optional, Callable, Any
from rich.console import Console

from .progress import ProgressTracker
from .stats import StatsDisplay
from .observer import MonitorObserver

logger = logging.getLogger(__name__)


# START_CLASS_Monitor
# START_CONTRACT:
# PURPOSE: Основной класс мониторинга, управляющий отображением метрик генерации кошельков и поиска совпадений.
# Интегрирует ProgressTracker, StatsDisplay и MonitorObserver в единую систему мониторинга.
# ATTRIBUTES:
# - _console: Console - объект консоли для вывода
# - _progress_tracker: ProgressTracker - трекер прогресса
# - _stats_display: StatsDisplay - отображение статистики
# - _observer: MonitorObserver - наблюдатель для подписки на метрики
# - _show_progress: bool - флаг показа прогресс-бара
# - _is_running: bool - флаг состояния мониторинга
# - _wallets_count: int - количество сгенерированных кошельков
# - _matches_count: int - количество найденных совпадений
# METHODS:
# - __init__(console, show_progress) - инициализация монитора
# - update_wallets_count(count) - обновить количество кошельков
# - update_matches_count(count) - обновить количество совпадений
# - start() - запустить мониторинг
# - stop() - остановить мониторинг
# - display() - отобразить метрики
# - subscribe(callback) - подписаться на обновления
# KEYWORDS: DOMAIN(9): Monitoring; TECH(7): Rich; CONCEPT(8): Coordination
# LINKS: []
# END_CONTRACT


class Monitor:
    """
    Основной класс мониторинга для визуализации прогресса генерации кошельков и поиска совпадений.
    Интегрирует все компоненты мониторинга в единую систему.
    """

    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация монитора с настройками отображения.
    # INPUTS:
    # - console: Optional[Console] - объект консоли (опционально)
    # - show_progress: bool - флаг показа прогресс-бара (опционально, по умолчанию True)
    # KEYWORDS: CONCEPT(5): Initialization
    # END_CONTRACT
    def __init__(self, console: Optional[Console] = None, show_progress: bool = True) -> None:
        """
        Инициализация монитора с настройками отображения.

        Args:
            console: Объект консоли для вывода (опционально).
            show_progress: Флаг показа прогресс-бара (опционально, по умолчанию True).
        """
        logger.debug(f"[SelfCheck][Monitor][INIT] Инициализация Monitor [ATTEMPT]")
        self._console = console if console is not None else Console()
        self._show_progress = show_progress
        self._is_running = False

        # Инициализация компонентов
        self._progress_tracker = ProgressTracker(console=self._console)
        self._stats_display = StatsDisplay(console=self._console)
        self._observer = MonitorObserver()

        # Метрики
        self._wallets_count: int = 0
        self._matches_count: int = 0

        logger.info(f"[TraceCheck][Monitor][INIT][StepComplete] Monitor инициализирован. show_progress={show_progress} [SUCCESS]")

    # END_METHOD___init__

    # START_METHOD_update_wallets_count
    # START_CONTRACT:
    # PURPOSE: Обновление количества сгенерированных кошельков.
    # INPUTS:
    # - count: int - количество сгенерированных кошельков
    # OUTPUTS:
    # - None
    # SIDE_EFFECTS: Обновляет внутренний счетчик и уведомляет подписчиков
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - Счетчик кошельков обновлен
    # - Подписчики уведомлены
    # KEYWORDS: DOMAIN(7): Wallets; CONCEPT(7): Counter; TECH(5): Update
    # LINKS_TO_SPECIFICATION: [Критерий 2: Класс Monitor имеет метод update_wallets_count()]
    # END_CONTRACT
    def update_wallets_count(self, count: int) -> None:
        """
        Обновить количество сгенерированных кошельков.

        Args:
            count: Количество сгенерированных кошельков.
        """
        logger.debug(f"[VarCheck][Monitor][UPDATE_WALLETS_COUNT][Params] count={count} [ATTEMPT]")
        self._wallets_count = count
        self._stats_display.update_wallets_count(count)
        self._observer.notify("wallets_generated", count)
        logger.info(f"[TraceCheck][Monitor][UPDATE_WALLETS_COUNT][StepComplete] Обновлено количество кошельков: {count} [SUCCESS]")

    # END_METHOD_update_wallets_count

    # START_METHOD_update_matches_count
    # START_CONTRACT:
    # PURPOSE: Обновление количества найденных совпадений.
    # INPUTS:
    # - count: int - количество найденных совпадений
    # OUTPUTS:
    # - None
    # SIDE_EFFECTS: Обновляет внутренний счетчик и уведомляет подписчиков
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - Счетчик совпадений обновлен
    # - Подписчики уведомлены
    # KEYWORDS: DOMAIN(7): Matches; CONCEPT(7): Counter; TECH(5): Update
    # LINKS_TO_SPECIFICATION: [Критерий 2: Класс Monitor имеет метод update_matches_count()]
    # END_CONTRACT
    def update_matches_count(self, count: int) -> None:
        """
        Обновить количество найденных совпадений.

        Args:
            count: Количество найденных совпадений.
        """
        logger.debug(f"[VarCheck][Monitor][UPDATE_MATCHES_COUNT][Params] count={count} [ATTEMPT]")
        self._matches_count = count
        self._stats_display.update_matches_count(count)
        self._observer.notify("matches_found", count)
        logger.info(f"[TraceCheck][Monitor][UPDATE_MATCHES_COUNT][StepComplete] Обновлено количество совпадений: {count} [SUCCESS]")

    # END_METHOD_update_matches_count

    # START_METHOD_start
    # START_CONTRACT:
    # PURPOSE: Запуск мониторинга.
    # INPUTS:
    # - total_wallets: int - ожидаемое общее количество кошельков (опционально)
    # OUTPUTS:
    # - None
    # SIDE_EFFECTS: Запускает прогресс-бар если он включен
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - Мониторинг запущен
    # KEYWORDS: DOMAIN(7): Monitoring; CONCEPT(6): Start; TECH(5): Rich
    # LINKS_TO_SPECIFICATION: [Критерий 3: Используется библиотека rich для визуализации]
    # END_CONTRACT
    def start(self, total_wallets: Optional[int] = None) -> None:
        """
        Запустить мониторинг.

        Args:
            total_wallets: Ожидаемое общее количество кошельков (опционально).
        """
        logger.debug(f"[SelfCheck][Monitor][START] Запуск мониторинга [ATTEMPT]")
        if self._show_progress and total_wallets is not None:
            self._progress_tracker.start(total_wallets, "Генерация кошельков")
        self._is_running = True
        logger.info(f"[TraceCheck][Monitor][START][StepComplete] Мониторинг запущен [SUCCESS]")

    # END_METHOD_start

    # START_METHOD_stop
    # START_CONTRACT:
    # PURPOSE: Остановка мониторинга.
    # OUTPUTS:
    # - None
    # SIDE_EFFECTS: Останавливает прогресс-бар
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - Мониторинг остановлен
    # KEYWORDS: DOMAIN(7): Monitoring; CONCEPT(6): Stop; TECH(5): Rich
    # END_CONTRACT
    def stop(self) -> None:
        """
        Остановить мониторинг.
        """
        logger.debug(f"[SelfCheck][Monitor][STOP] Остановка мониторинга [ATTEMPT]")
        if self._progress_tracker.is_active():
            self._progress_tracker.finish()
        self._is_running = False
        logger.info(f"[TraceCheck][Monitor][STOP][StepComplete] Мониторинг остановлен [SUCCESS]")

    # END_METHOD_stop

    # START_METHOD_display
    # START_CONTRACT:
    # PURPOSE: Отображение текущих метрик в консоли.
    # OUTPUTS:
    # - None
    # SIDE_EFFECTS: Выводит статистику в консоль
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - Статистика отображена в консоли
    # KEYWORDS: DOMAIN(7): Display; TECH(6): Rich; CONCEPT(7): Output
    # LINKS_TO_SPECIFICATION: [Критерий 3: Используется rich.table для статистики]
    # END_CONTRACT
    def display(self) -> None:
        """
        Отобразить текущие метрики в консоли.
        """
        logger.debug(f"[SelfCheck][Monitor][DISPLAY] Отображение метрик [ATTEMPT]")
        self._console.print("\n")
        self._stats_display.display()
        self._console.print("\n")
        logger.info(f"[TraceCheck][Monitor][DISPLAY][StepComplete] Метрики отображены [SUCCESS]")

    # END_METHOD_display

    # START_METHOD_subscribe
    # START_CONTRACT:
    # PURPOSE: Подписка на обновления метрик.
    # INPUTS:
    # - callback: Callable[[str, Any], None] - функция обратного вызова
    # OUTPUTS:
    # - bool - True при успешной подписке
    # KEYWORDS: PATTERN(8): Observer; DOMAIN(6): Subscribe; CONCEPT(7): Event
    # LINKS_TO_SPECIFICATION: [Критерий 4: Реализован паттерн observer/subscribe]
    # END_CONTRACT
    def subscribe(self, callback: Callable[[str, Any], None]) -> bool:
        """
        Подписаться на обновления метрик.

        Args:
            callback: Функция обратного вызова.

        Returns:
            True при успешной подписке.
        """
        logger.debug(f"[VarCheck][Monitor][SUBSCRIBE][Params] callback={callback.__name__ if hasattr(callback, '__name__') else str(callback)} [ATTEMPT]")
        result = self._observer.subscribe(callback)
        logger.info(f"[TraceCheck][Monitor][SUBSCRIBE][ReturnData] Результат подписки: {result} [VALUE]")
        return result

    # END_METHOD_subscribe

    # START_METHOD_unsubscribe
    # START_CONTRACT:
    # PURPOSE: Отписка от обновлений метрик.
    # INPUTS:
    # - callback: Callable[[str, Any], None] - функция обратного вызова
    # OUTPUTS:
    # - bool - True при успешной отписке
    # KEYWORDS: PATTERN(8): Observer; DOMAIN(7): Unsubscribe
    # END_CONTRACT
    def unsubscribe(self, callback: Callable[[str, Any], None]) -> bool:
        """
        Отписаться от обновлений метрик.

        Args:
            callback: Функция обратного вызова.

        Returns:
            True при успешной отписке.
        """
        logger.debug(f"[VarCheck][Monitor][UNSUBSCRIBE][Params] callback={callback.__name__ if hasattr(callback, '__name__') else str(callback)} [ATTEMPT]")
        result = self._observer.unsubscribe(callback)
        logger.info(f"[TraceCheck][Monitor][UNSUBSCRIBE][ReturnData] Результат отписки: {result} [VALUE]")
        return result

    # END_METHOD_unsubscribe

    # START_METHOD_get_wallets_count
    # START_CONTRACT:
    # PURPOSE: Получение текущего количества сгенерированных кошельков.
    # OUTPUTS:
    # - int - количество сгенерированных кошельков
    # KEYWORDS: CONCEPT(6): Getter
    # END_CONTRACT
    def get_wallets_count(self) -> int:
        """
        Получить текущее количество сгенерированных кошельков.

        Returns:
            Количество сгенерированных кошельков.
        """
        logger.debug(f"[VarCheck][Monitor][GET_WALLETS_COUNT][ReturnData] wallets_count={self._wallets_count} [VALUE]")
        return self._wallets_count

    # END_METHOD_get_wallets_count

    # START_METHOD_get_matches_count
    # START_CONTRACT:
    # PURPOSE: Получение текущего количества найденных совпадений.
    # OUTPUTS:
    # - int - количество найденных совпадений
    # KEYWORDS: CONCEPT(6): Getter
    # END_CONTRACT
    def get_matches_count(self) -> int:
        """
        Получить текущее количество найденных совпадений.

        Returns:
            Количество найденных совпадений.
        """
        logger.debug(f"[VarCheck][Monitor][GET_MATCHES_COUNT][ReturnData] matches_count={self._matches_count} [VALUE]")
        return self._matches_count

    # END_METHOD_get_matches_count

    # START_METHOD_is_running
    # START_CONTRACT:
    # PURPOSE: Проверка состояния мониторинга.
    # OUTPUTS:
    # - bool - True если мониторинг запущен
    # KEYWORDS: CONCEPT(6): Status
    # END_CONTRACT
    def is_running(self) -> bool:
        """
        Проверить состояние мониторинга.

        Returns:
            True если мониторинг запущен.
        """
        is_running = self._is_running
        logger.debug(f"[VarCheck][Monitor][IS_RUNNING][ReturnData] is_running={is_running} [VALUE]")
        return is_running

    # END_METHOD_is_running

    # START_METHOD_reset
    # START_CONTRACT:
    # PURPOSE: Сброс всех метрик к начальным значениям.
    # OUTPUTS:
    # - None
    # KEYWORDS: CONCEPT(6): Reset
    # END_CONTRACT
    def reset(self) -> None:
        """
        Сбросить все метрики к начальным значениям.
        """
        logger.debug(f"[SelfCheck][Monitor][RESET] Сброс метрик [ATTEMPT]")
        self._wallets_count = 0
        self._matches_count = 0
        self._stats_display.reset()
        logger.info(f"[TraceCheck][Monitor][RESET][StepComplete] Метрики сброшены [SUCCESS]")

    # END_METHOD_reset


# END_CLASS_Monitor
