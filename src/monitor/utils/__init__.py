# FILE: src/monitor/utils/__init__.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Модуль утилит мониторинга. Экспортирует вспомогательные функции и классы для работы с сигналами, обработкой завершения и другими системными функциями.
# SCOPE: Утилиты, обработка сигналов, graceful shutdown
# INPUT: Нет (модуль предоставляет импорты)
# OUTPUT: Класс SignalHandler, функции setup_signal_handler, get_global_handler, create_graceful_shutdown
# KEYWORDS: DOMAIN(9): Utilities; DOMAIN(8): Signal Handling; DOMAIN(7): Shutdown; CONCEPT(6): Graceful Exit; TECH(5): Python
# LINKS: [USES(7): src.monitor.utils.signal_handler]
# LINKS_TO_SPECIFICATION: Требования к обработке сигналов из dev_plan_signal_handler.md
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 10 [Обработчик сигналов для graceful shutdown] => SignalHandler
# FUNC 9 [Устанавливает глобальный обработчик сигналов] => setup_signal_handler
# FUNC 8 [Получает глобальный обработчик сигналов] => get_global_handler
# FUNC 9 [Создаёт обработчик с shutdown callback] => create_graceful_shutdown
# END_MODULE_MAP
# START_USE_CASES:
# - [SignalHandler]: System (Shutdown) -> HandleSignal -> GracefulShutdown
# - [setup_signal_handler]: MonitorApp (Startup) -> SetupSignalHandling -> SignalHandlersActive
# - [create_graceful_shutdown]: MonitorApp (Startup) -> CreateShutdownHandler -> HandlerReady
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
logger.debug(f"[ModuleInit][utils/__init__][SetupLogger] Логгер модуля utils инициализирован [SUCCESS]")

# Экспорт утилит
from src.monitor.utils.signal_handler import (
    SignalHandler,
    setup_signal_handler,
    get_global_handler,
    create_graceful_shutdown,
)

logger.debug(f"[ModuleInit][utils/__init__][Import] Импортированы классы и функции из signal_handler.py [SUCCESS]")

__all__ = [
    "SignalHandler",
    "setup_signal_handler",
    "get_global_handler",
    "create_graceful_shutdown",
]

logger.info(f"[ModuleInit][utils/__init__][StepComplete] Модуль utils инициализирован, экспортировано {len(__all__)} сущностей [SUCCESS]")
