# START_MODULE_CONTRACT:
# PURPOSE: Реализация паттерна Observer для подписки на обновления метрик мониторинга.
# Позволяет другим компонентам системы подписываться на события изменения метрик.
# SCOPE: Наблюдатель, подписки, уведомления
# INPUT: callback - функция обратного вызова для уведомлений
# OUTPUT: Класс MonitorObserver с методами subscribe, unsubscribe, notify
# KEYWORDS: PATTERN(8): Observer; DOMAIN(7): Monitoring; CONCEPT(8): EventDriven
# LINKS: [USES(6): typing]
# LINKS_TO_SPECIFICATION: [Критерий 4: Реализован паттерн observer/subscribe для получения обновлений метрик]
# END_MODULE_CONTRACT

"""
Модуль мониторинга для визуализации прогресса генерации кошельков и поиска совпадений.
"""
import logging
from typing import Callable, List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# START_CLASS_MonitorObserver
# START_CONTRACT:
# PURPOSE: Паттерн Observer для подписки на обновления метрик мониторинга.
# Позволяет другим компонентам подписываться на события изменения метрик и получать уведомления.
# ATTRIBUTES:
# - _subscribers: List[Callable] - список подписанных callback функций
# METHODS:
# - subscribe(callback) - подписка на обновления метрик
# - unsubscribe(callback) - отписка от обновлений метрик
# - notify(metric_name, value) - уведомление подписчиков об изменении метрики
# KEYWORDS: PATTERN(8): Observer; DOMAIN(7): Monitoring; CONCEPT(8): EventDriven
# LINKS: []
# END_CONTRACT


class MonitorObserver:
    """
    Паттерн Observer для мониторинга метрик.
    Позволяет подписываться на обновления метрик и получать уведомления при их изменении.
    """

    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация наблюдателя мониторинга.
    # KEYWORDS: CONCEPT(5): Initialization
    # END_CONTRACT
    def __init__(self) -> None:
        """
        Инициализация наблюдателя мониторинга.
        """
        logger.debug(f"[SelfCheck][MonitorObserver][INIT] Инициализация MonitorObserver [SUCCESS]")
        self._subscribers: List[Callable[[str, Any], None]] = []

    # END_METHOD___init__

    # START_METHOD_subscribe
    # START_CONTRACT:
    # PURPOSE: Подписка на обновления метрик.
    # INPUTS:
    # - callback: Callable[[str, Any], None] - функция обратного вызова, принимающая имя метрики и значение
    # OUTPUTS:
    # - bool - True при успешной подписке
    # SIDE_EFFECTS: Добавляет callback в список подписчиков
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - Callback добавлен в список подписчиков
    # KEYWORDS: PATTERN(7): Observer; DOMAIN(6): Subscribe
    # END_CONTRACT
    def subscribe(self, callback: Callable[[str, Any], None]) -> bool:
        """
        Подписаться на обновления метрик.

        Args:
            callback: Функция обратного вызова, принимающая имя метрики и значение.

        Returns:
            True при успешной подписке.
        """
        logger.debug(f"[VarCheck][MonitorObserver][SUBSCRIBE][Params] Подписка на callback: {callback.__name__ if hasattr(callback, '__name__') else str(callback)} [ATTEMPT]")
        if callback not in self._subscribers:
            self._subscribers.append(callback)
            logger.info(f"[TraceCheck][MonitorObserver][SUBSCRIBE][StepComplete] Подписка успешно оформлена. Всего подписчиков: {len(self._subscribers)} [SUCCESS]")
            return True
        logger.warning(f"[VarCheck][MonitorObserver][SUBSCRIBE][ConditionCheck] Callback уже подписан [FAIL]")
        return False

    # END_METHOD_subscribe

    # START_METHOD_unsubscribe
    # START_CONTRACT:
    # PURPOSE: Отписка от обновлений метрик.
    # INPUTS:
    # - callback: Callable[[str, Any], None] - функция обратного вызова для отписки
    # OUTPUTS:
    # - bool - True при успешной отписке
    # SIDE_EFFECTS: Удаляет callback из списка подписчиков
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - Callback удален из списка подписчиков
    # KEYWORDS: PATTERN(7): Observer; DOMAIN(6): Unsubscribe
    # END_CONTRACT
    def unsubscribe(self, callback: Callable[[str, Any], None]) -> bool:
        """
        Отписаться от обновлений метрик.

        Args:
            callback: Функция обратного вызова для отписки.

        Returns:
            True при успешной отписке.
        """
        logger.debug(f"[VarCheck][MonitorObserver][UNSUBSCRIBE][Params] Отписка от callback: {callback.__name__ if hasattr(callback, '__name__') else str(callback)} [ATTEMPT]")
        if callback in self._subscribers:
            self._subscribers.remove(callback)
            logger.info(f"[TraceCheck][MonitorObserver][UNSUBSCRIBE][StepComplete] Отписка успешна. Всего подписчиков: {len(self._subscribers)} [SUCCESS]")
            return True
        logger.warning(f"[VarCheck][MonitorObserver][UNSUBSCRIBE][ConditionCheck] Callback не найден в подписчиках [FAIL]")
        return False

    # END_METHOD_unsubscribe

    # START_METHOD_notify
    # START_CONTRACT:
    # PURPOSE: Уведомление всех подписчиков об изменении метрики.
    # INPUTS:
    # - metric_name: str - имя изменившейся метрики
    # - value: Any - новое значение метрики
    # OUTPUTS:
    # - None
    # SIDE_EFFECTS: Вызывает все зарегистрированные callback функции
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - Все подписчики получили уведомление
    # KEYWORDS: PATTERN(8): Observer; DOMAIN(7): Notification; CONCEPT(6): Event
    # END_CONTRACT
    def notify(self, metric_name: str, value: Any) -> None:
        """
        Уведомить всех подписчиков об изменении метрики.

        Args:
            metric_name: Имя изменившейся метрики.
            value: Новое значение метрики.
        """
        logger.debug(f"[VarCheck][MonitorObserver][NOTIFY][Params] metric_name={metric_name}, value={value} [ATTEMPT]")
        for callback in self._subscribers:
            try:
                callback(metric_name, value)
                logger.debug(f"[TraceCheck][MonitorObserver][NOTIFY][CallExternal] Вызов callback: {callback.__name__ if hasattr(callback, '__name__') else str(callback)} [SUCCESS]")
            except Exception as e:
                logger.error(f"[CriticalError][MonitorObserver][NOTIFY][ExceptionCaught] Ошибка при вызове callback: {str(e)} [FAIL]")
        logger.debug(f"[VarCheck][MonitorObserver][NOTIFY][ReturnData] Уведомлено подписчиков: {len(self._subscribers)} [VALUE]")

    # END_METHOD_notify

    # START_METHOD_clear
    # START_CONTRACT:
    # PURPOSE: Очистка всех подписок.
    # OUTPUTS:
    # - None
    # SIDE_EFFECTS: Удаляет все callback функции из списка подписчиков
    # KEYWORDS: CONCEPT(5): Cleanup
    # END_CONTRACT
    def clear(self) -> None:
        """
        Очистить все подписки.
        """
        logger.debug(f"[SelfCheck][MonitorObserver][CLEAR] Очистка всех подписок [ATTEMPT]")
        self._subscribers.clear()
        logger.info(f"[TraceCheck][MonitorObserver][CLEAR][StepComplete] Все подписки очищены [SUCCESS]")

    # END_METHOD_clear


# END_CLASS_MonitorObserver
