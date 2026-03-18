# START_MODULE_CONTRACT:
# PURPOSE: Главный модуль мониторинга, экспортирует основные классы для работы с мониторингом.
# Предоставляет единую точку входа для импорта классов Monitor, ProgressTracker, StatsDisplay, MonitorObserver.
# SCOPE: Экспорт, мониторинг, интерфейс
# INPUT: Нет
# OUTPUT: Экспорт классов Monitor, ProgressTracker, StatsDisplay, MonitorObserver
# KEYWORDS: DOMAIN(8): Monitoring; CONCEPT(7): Export; TECH(5): Interface
# LINKS: [USES(6): monitor; USES(6): progress; USES(6): stats; USES(6): observer]
# LINKS_TO_SPECIFICATION: [Критерий 1: Модуль мониторинга создается в директории src/plugins/wallet/monitor/, Критерий 5: Модуль должен импортироваться как from src.plugins.wallet.monitor import Monitor]
# END_MODULE_CONTRACT

"""
Модуль мониторинга для визуализации прогресса генерации кошельков и поиска совпадений.

Основные классы:
- Monitor: Главный класс мониторинга
- ProgressTracker: Отслеживание прогресса операций
- StatsDisplay: Отображение статистики в табличном формате
- MonitorObserver: Паттерн Observer для подписки на метрики

Пример использования:
    from src.plugins.wallet.monitor import Monitor

    monitor = Monitor()
    monitor.update_wallets_count(100)
    monitor.update_matches_count(5)
    monitor.display()
"""

import logging

# Настройка логирования для модуля мониторинга
# Логирование должно вестись в файл app.log согласно требованиям проекта
monitor_logger = logging.getLogger(__name__)
if not monitor_logger.handlers:
    # Используем уже настроенный logging из корневого модуля
    pass

# Экспорт основных классов
from .monitor import Monitor
from .progress import ProgressTracker
from .stats import StatsDisplay
from .observer import MonitorObserver

# START_MODULE_MAP:
# CLASS 10 [Главный класс мониторинга для визуализации прогресса] => Monitor
# CLASS 7 [Класс для отслеживания прогресса операций с прогресс-барами] => ProgressTracker
# CLASS 7 [Класс для отображения статистики в табличном формате] => StatsDisplay
# CLASS 6 [Паттерн Observer для подписки на обновления метрик] => MonitorObserver
# END_MODULE_MAP

# START_USE_CASES:
# [Monitor - основной класс]: System (WalletGeneration) -> TrackProgressAndDisplay -> RealTimeMonitoring
# [Monitor - подписка]: Plugin (BatchGen) -> SubscribeToMetrics -> AutomaticUpdates
# [ProgressTracker - прогресс]: System (LongOperation) -> ShowProgressBar -> UserAwareness
# [StatsDisplay - таблица]: System (MetricsUpdate) -> RenderTable -> ConsoleOutput
# [MonitorObserver - события]: Plugin (AddressMatcher) -> Subscribe -> GetNotified
# END_USE_CASES

# Версия модуля
__version__ = "1.0.0"
__all__ = [
    "Monitor",
    "ProgressTracker",
    "StatsDisplay",
    "MonitorObserver",
]
