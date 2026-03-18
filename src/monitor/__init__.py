# FILE: src/monitor/__init__.py
# VERSION: 1.1.0
# START_MODULE_CONTRACT:
# PURPOSE: Модуль мониторинга генератора кошельков Bitcoin. Предоставляет Gradio-интерфейс для мониторинга процесса генерации и управления плагинами мониторинга. Поддерживает C++ бэкенд с автоматическим fallback на Python.
# SCOPE: мониторинг, метрики, плагины, Gradio-интерфейс, C++ бэкенд
# INPUT: Нет (модуль предоставляет интерфейсы и константы)
# OUTPUT: Константы __version__, __author__, __cpp_version__; Классы MetricsStore, BaseMonitorPlugin; Флаги CPP_AVAILABLE, METRICS_AVAILABLE, PLUGIN_BASE_AVAILABLE
# KEYWORDS: [DOMAIN(9): Monitoring; DOMAIN(8): Metrics; CONCEPT(7): Plugins; TECH(6): Gradio; CONCEPT(6): CppBinding; CONCEPT(5): Fallback]
# LINKS: [USES_API(7): logging_module; IMPORTS(6): src.monitor.metrics; IMPORTS(6): src.monitor.plugins.base; IMPORTS(7): src.monitor._cpp]
# LINKS_TO_SPECIFICATION: [Требования к модулю мониторинга из ТЗ]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CONST 5 [Версия модуля мониторинга] => __version__
# CONST 3 [Автор модуля] => __author__
# CONST 4 [Флаг использования C++ бэкенда] => __cpp_version__
# CONST 5 [Флаг доступности C++ модулей] => CPP_AVAILABLE
# CONST 5 [Флаг доступности C++ модуля метрик] => METRICS_AVAILABLE
# CONST 5 [Флаг доступности C++ модуля базового плагина] => PLUGIN_BASE_AVAILABLE
# CLASS 9 [Хранилище метрик процесса генерации] => MetricsStore
# CLASS 8 [Базовый класс для плагинов мониторинга] => BaseMonitorPlugin
# END_MODULE_MAP
# START_USE_CASES:
# - [MetricsStore]: System (Runtime) -> CollectAndStoreMetrics -> PerformanceDataAvailable
# - [BaseMonitorPlugin]: Developer (Extension) -> ImplementCustomPlugin -> CustomMonitoringEnabled
# - [C++ Backend]: System (Optimization) -> UseCppModule -> PerformanceImproved
# END_USE_CASES

"""
Модуль мониторинга генератора кошельков Bitcoin.
Предоставляет Gradio-интерфейс для мониторинга процесса генерации.
"""

# START_BLOCK_CONFIGURE_LOGGING: [Настройка системы логирования с записью в app.log]
import logging
import os
import sys

# Добавляем корень проекта в путь для корректного импорта
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Настройка логирования с обязательным FileHandler в app.log
# Согласно требованиям: логирование должно вестись в app.log в корне проекта
log_dir = os.path.join(project_root, "logs")
os.makedirs(log_dir, exist_ok=True)
app_log_path = os.path.join(project_root, "app.log")

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(app_log_path),
    ],
)

logger = logging.getLogger(__name__)
logger.info(f"[InitModule][src.monitor][CONFIGURE_LOGGING][StepComplete] Логирование настроено. Путь к app.log: {app_log_path} [SUCCESS]")
# END_BLOCK_CONFIGURE_LOGGING

# START_BLOCK_DEFINE_CONSTANTS: [Определение констант модуля]
__version__ = "1.0.0"
__author__ = "Wallet Generator Team"

logger.debug(f"[VarCheck][src.monitor][DEFINE_CONSTANTS][ReturnData] Версия модуля: {__version__}, Автор: {__author__} [VALUE]")
# END_BLOCK_DEFINE_CONSTANTS

# START_BLOCK_EXPORT_COMPONENTS: [Экспорт основных классов для внешнего использования с поддержкой C++ бэкенда]
# Импорт флагов доступности и функций получения модулей из _cpp
try:
    from src.monitor._cpp import (
        CPP_AVAILABLE,
        METRICS_AVAILABLE,
        PLUGIN_BASE_AVAILABLE,
        get_metrics_module,
        get_plugin_base_module,
    )
    logger.info(f"[ImportCheck][src.monitor][EXPORT_COMPONENTS][StepComplete] Импортированы флаги из src.monitor._cpp: CPP_AVAILABLE={CPP_AVAILABLE}, METRICS_AVAILABLE={METRICS_AVAILABLE}, PLUGIN_BASE_AVAILABLE={PLUGIN_BASE_AVAILABLE} [SUCCESS]")
except ImportError as e:
    logger.warning(f"[ImportCheck][src.monitor][EXPORT_COMPONENTS][ExceptionCaught] Не удалось импортировать флаги из _cpp: {e} [WARNING]")
    CPP_AVAILABLE = False
    METRICS_AVAILABLE = False
    PLUGIN_BASE_AVAILABLE = False
    get_metrics_module = None
    get_plugin_base_module = None

# Попытка импорта C++ обёрток, с fallback на Python реализацию
try:
    from src.monitor._cpp.metrics_wrapper import MetricsStore
    from src.monitor._cpp.plugin_base_wrapper import BaseMonitorPlugin
    _USE_CPP = True
    logger.info(f"[ImportCheck][src.monitor][EXPORT_COMPONENTS][StepComplete] Используются C++ обёртки для MetricsStore и BaseMonitorPlugin [SUCCESS]")
except ImportError as e:
    logger.warning(f"[ImportCheck][src.monitor][EXPORT_COMPONENTS][ExceptionCaught] C++ обёртки недоступны: {e}, используем Python fallback [WARNING]")
    from src.monitor.metrics import MetricsStore
    from src.monitor.plugins.base import BaseMonitorPlugin
    _USE_CPP = False
    logger.info(f"[ImportCheck][src.monitor][EXPORT_COMPONENTS][StepComplete] Используются Python реализации для MetricsStore и BaseMonitorPlugin [INFO]")

# Определение типа реализации (C++ или Python)
__cpp_version__ = _USE_CPP

logger.debug(f"[VarCheck][src.monitor][EXPORT_COMPONENTS][ReturnData] Импортированы: MetricsStore, BaseMonitorPlugin, _USE_CPP={_USE_CPP} [VALUE]")

__all__ = [
    # Константы версии
    "__version__",
    "__author__",
    # Флаги C++ доступности
    "__cpp_version__",
    "CPP_AVAILABLE",
    "METRICS_AVAILABLE",
    "PLUGIN_BASE_AVAILABLE",
    # Классы
    "MetricsStore",
    "BaseMonitorPlugin",
]

logger.info(f"[InitModule][src.monitor][EXPORT_COMPONENTS][StepComplete] Модуль мониторинга инициализирован. Экспортируемые сущности: {__all__}, C++ используется: {__cpp_version__} [SUCCESS]")
# END_BLOCK_EXPORT_COMPONENTS
