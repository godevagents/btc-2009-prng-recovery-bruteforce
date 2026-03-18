# FILE: src/monitor/integrations/__init__.py
# VERSION: 1.1.0
# START_MODULE_CONTRACT:
# PURPOSE: Модуль интеграций мониторинга. Содержит компоненты для интеграции с генератором кошельков,
# обеспечивая запуск генератора и получение метрик в реальном времени через парсинг логов.
# Использует C++ обёртку log_parser с fallback на Python реализацию.
# SCOPE: Интеграция с внешними модулями, парсинг логов, мониторинг процессов
# INPUT: Нет (значения импортируются из дочерних модулей)
# OUTPUT: Классы LogParser, LaunchIntegration для интеграции с генератором
# KEYWORDS: [DOMAIN(9): Monitoring; DOMAIN(8): Integration; CONCEPT(7): LogParsing; TECH(6): Subprocess; CONCEPT(6): CppBinding]
# LINKS: [USES_API(8): launch_integration; USES_API(8): log_parser; USES_API(7): log_parser_wrapper; FALLBACK_TO(7): src.monitor.integrations.log_parser]
# LINKS_TO_SPECIFICATION: [monitoring_module_architecture.md]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 9 [Парсер лог-файлов для извлечения метрик (C++ с fallback)] => LogParser
# CLASS 9 [Интеграция с модулем запуска src/launch] => LaunchIntegration
# CONST 5 [Флаг доступности C++ модуля log_parser] => LOG_PARSER_AVAILABLE
# FUNC 5 [Получить модуль log_parser с fallback] => get_log_parser_module
# END_MODULE_MAP
# START_USE_CASES:
# - [LogParser]: Monitor (RealTime) -> ParseLogFile -> MetricsAvailable
# - [LaunchIntegration]: System (Startup) -> LaunchGenerator -> MonitoringActive
# END_USE_CASES
"""
Модуль интеграций мониторинга.
Содержит компоненты для интеграции с генератором кошельков.
"""

import logging
import sys
from pathlib import Path

# Настройка логирования в файл app.log
def _setup_file_logging():
    """Настройка файлового логирования для модуля интеграций."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    # Проверяем, уже ли добавлен обработчик
    if not logger.handlers:
        log_path = Path("app.log")
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            "%(asctime)s [%(name)s] %(levelname)s %(message)s"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

logger = _setup_file_logging()

# Экспорт интеграций с поддержкой C++
# Импорт LogParser из C++ обёртки с fallback на Python реализацию
from src.monitor._cpp.log_parser_wrapper import LogParser
from src.monitor._cpp import LOG_PARSER_AVAILABLE, get_log_parser_module

# Импорт LaunchIntegration (пока без изменений)
from src.monitor.integrations.launch_integration import LaunchIntegration

__all__ = [
    # LogParser из C++ обёртки
    "LogParser",
    "LOG_PARSER_AVAILABLE",
    "get_log_parser_module",
    # LaunchIntegration
    "LaunchIntegration",
]

# Логирование информации об используемой реализации
if LOG_PARSER_AVAILABLE:
    logger.info(f"[integrations][INIT][StepComplete] Модуль интеграций инициализирован. Используется C++ реализация LogParser [SUCCESS]")
else:
    logger.info(f"[integrations][INIT][StepComplete] Модуль интеграций инициализирован. Используется Python реализация LogParser (fallback) [INFO]")
