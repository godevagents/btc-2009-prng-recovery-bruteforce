# FILE: src/monitor/_cpp/metrics_wrapper.py
# VERSION: 1.0.0

# START_MODULE_CONTRACT:
# PURPOSE: Python-обёртка для C++ модуля метрик (metrics_cpp.so). Обеспечивает единый интерфейс для работы с метриками производительности с автоматическим fallback на Python реализацию.
# SCOPE: метрики производительности, хранилище данных, статистика, мониторинг, тайминги операций
# INPUT: C++ модуль metrics_cpp или Python модуль src.monitor.metrics
# OUTPUT: Класс MetricsStore с унифицированным API
# KEYWORDS: [DOMAIN(9): Metrics; DOMAIN(8): Performance; CONCEPT(7): CppBinding; TECH(6): Fallback; CONCEPT(5): TimeSeries]
# LINKS: [USES_API(8): metrics_cpp.so; FALLBACK_TO(7): src.monitor.metrics; COMPOSES(6): _cpp_init]
# LINKS_TO_SPECIFICATION: [Требования к единому API метрик с поддержкой C++ бэкенда]
# END_MODULE_CONTRACT

# START_MODULE_MAP:
# CLASS 9 [Унифицированное хранилище метрик с C++ бэкендом] => MetricsStore
# FUNC 5 [Вспомогательная функция импорта C++ модуля] => _import_cpp_module
# FUNC 5 [Создание экземпляра хранилища] => create_metrics_store
# CONST 5 [Количество итераций] => ITERATION_COUNT
# CONST 5 [Количество совпадений] => MATCH_COUNT
# CONST 5 [Количество кошельков] => WALLET_COUNT
# CONST 5 [Прошедшее время] => ELAPSED_TIME
# CONST 5 [Итераций в секунду] => ITERATIONS_PER_SECOND
# CONST 5 [Кошельков в секунду] => WALLETS_PER_SECOND
# END_MODULE_MAP
# START_USE_CASES:
# - [MetricsStore.add_metric]: System (Monitoring) -> RecordMetric -> MetricStored
# - [MetricsStore.get_metric]: UI (Display) -> RequestMetric -> ValueProvided
# - [MetricsStore.get_stats]: Analytics (Analysis) -> CalculateStatistics -> StatsProvided
# - [MetricsStore.record_timing]: System (Performance) -> RecordOperationTime -> TimingStored
# - [MetricsStore.get_average_timing]: System (Analysis) -> GetAverageTime -> ValueProvided
# END_USE_CASES

"""
Python-обёртка для C++ модуля метрик.

Обеспечивает:
- Адаптацию C++ API к Python-интерфейсу
- Автоматическое преобразование типов
- Обработку исключений
- Логирование операций
- Fallback на Python реализацию при недоступности C++ модуля

Использование:
    from src.monitor._cpp.metrics_wrapper import MetricsStore
    
    store = MetricsStore(max_history_size=10000)
    store.add_metric("iterations", 1000)
    value = store.get_metric("iterations")
"""

# START_BLOCK_IMPORT_MODULES: [Импорт необходимых модулей]
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional, Callable

# Настройка логирования с FileHandler в app.log
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
logger.info(f"[InitModule][metrics_wrapper][IMPORT_MODULES][StepComplete] Модуль загружен. app.log: {app_log_path} [SUCCESS]")
# END_BLOCK_IMPORT_MODULES


# START_BLOCK_CONSTANTS: [Определение констант метрик]
# Стандартные имена метрик
ITERATION_COUNT = "iteration_count"
MATCH_COUNT = "match_count"
WALLET_COUNT = "wallet_count"
ELAPSED_TIME = "elapsed_time"
ENTROPY_DATA = "entropy_data"
ADDRESSES_EXTRACTED = "addresses_extracted"
MATCHES_FOUND = "matches_found"
ITERATIONS_PER_SECOND = "iterations_per_second"
WALLETS_PER_SECOND = "wallets_per_second"

# Константы для таймингов
TIMING_PREFIX = "timing_"
# END_BLOCK_CONSTANTS


# START_FUNCTION__IMPORT_CPP_MODULE
# START_CONTRACT:
# PURPOSE: Импорт C++ модуля метрик с обработкой ошибок и fallback.
# INPUTS: Нет
# OUTPUTS:
# - Dict[str, Any] - словарь с информацией о доступности модуля
# SIDE_EFFECTS:
# - Выполняет попытку импорта модуля metrics_cpp
# KEYWORDS: [PATTERN(7): ModuleImport; DOMAIN(8): CppBinding; TECH(6): DynamicImport]
# END_CONTRACT

def _import_cpp_module() -> Dict[str, Any]:
    """
    Импорт C++ модуля метрик с fallback на Python.
    
    Returns:
        Словарь с информацией о доступности модуля:
        - 'available': bool - флаг доступности
        - 'MetricsStore': класс C++ MetricsStore (если доступен)
        - 'error': str - сообщение об ошибке (если недоступен)
    """
    logger.debug(f"[_import_cpp_module][START] Попытка импорта C++ модуля metrics_cpp")
    
    try:
        # Попытка импорта C++ модуля
        from metrics_cpp import MetricsStore as _MetricsStore
        
        # Тест работоспособности - создаём тестовый экземпляр
        test_store = _MetricsStore(10)
        del test_store
        
        logger.info(f"[_import_cpp_module][ConditionCheck] C++ модуль metrics_cpp успешно загружен [SUCCESS]")
        
        return {
            'available': True,
            'MetricsStore': _MetricsStore,
            'error': None,
        }
        
    except ImportError as e:
        logger.warning(f"[_import_cpp_module][ConditionCheck] C++ модуль metrics_cpp недоступен: {e} [FAIL]")
        return {
            'available': False,
            'MetricsStore': None,
            'error': str(e),
        }
    except Exception as e:
        logger.error(f"[_import_cpp_module][ExceptionCaught] Неожиданная ошибка при импорте C++ модуля: {e} [FAIL]")
        return {
            'available': False,
            'MetricsStore': None,
            'error': str(e),
        }

# END_FUNCTION__IMPORT_CPP_MODULE


# START_CLASS_IN_MEMORY_METRICS_STORE
# START_CONTRACT:
# PURPOSE: Встроенное Python хранилище метрик для fallback, когда C++ и Python модули недоступны.
# ATTRIBUTES:
# - _metrics: Dict[str, Any] - хранилище метрик
# - _history: Dict[str, List] - история метрик
# - _max_history_size: int - максимальный размер истории
# METHODS:
# - Обновление метрик => update
# - Получение метрик => get_current, get_history
# - Сброс => reset
# KEYWORDS: [PATTERN(6): Fallback; DOMAIN(9): Metrics; TECH(5): InMemory]
# END_CONTRACT

class _InMemoryMetricsStore:
    """Встроенное Python хранилище метрик для fallback."""
    
    def __init__(self, max_history_size: int = 10000) -> None:
        self._max_history_size = max_history_size
        self._metrics: Dict[str, Any] = {}
        self._history: Dict[str, List] = {}
        self._subscribers: List[Callable] = []
    
    def update(self, metrics: Dict[str, Any]) -> None:
        """Обновление метрик."""
        for name, value in metrics.items():
            self._metrics[name] = value
            if name not in self._history:
                self._history[name] = []
            self._history[name].append(value)
            if len(self._history[name]) > self._max_history_size:
                self._history[name] = self._history[name][-self._max_history_size:]
    
    def get_current(self) -> Dict[str, Any]:
        """Получение текущих метрик."""
        return self._metrics.copy()
    
    def get_history(self, name: str, limit: Optional[int] = None) -> List:
        """Получение истории метрики."""
        history = self._history.get(name, [])
        if limit:
            return history[-limit:]
        return history.copy()
    
    def reset(self) -> None:
        """Сброс всех метрик."""
        self._metrics = {}
        self._history = {}
    
    def subscribe(self, callback: Callable) -> None:
        """Подписка на обновления."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable) -> None:
        """Отписка от обновлений."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    def get_summary(self) -> Dict[str, Any]:
        """Получение сводки метрик."""
        return {
            'metrics': self._metrics.copy(),
            'history_sizes': {k: len(v) for k, v in self._history.items()},
        }
    
    def get_snapshot(self) -> Dict[str, Any]:
        """Получение снимка метрик."""
        return {
            'metrics': self._metrics.copy(),
            'history': {k: v.copy() for k, v in self._history.items()},
            'timestamp': time.time(),
        }
    
    def compute_rate(self, metric_name: str, window_seconds: int = 60) -> float:
        """Вычисление скорости изменения метрики."""
        history = self._history.get(metric_name, [])
        if len(history) < 2:
            return 0.0
        return history[-1] - history[0] if len(history) > 0 else 0.0


# END_CLASS_IN_MEMORY_METRICS_STORE


# START_BLOCK_CPP_MODULE_INITIALIZATION: [Инициализация C++ модуля]
# Попытка импорта C++ модуля при загрузке модуля
_CPP_MODULE = _import_cpp_module()
CPP_AVAILABLE = _CPP_MODULE['available']
# END_BLOCK_CPP_MODULE_INITIALIZATION


# START_CLASS_METRICS_STORE
# START_CONTRACT:
# PURPOSE: Унифицированное хранилище метрик производительности с поддержкой C++ бэкенда. Обеспечивает единый интерфейс для работы с метриками независимо от реализации.
# ATTRIBUTES:
# - _cpp_store: Any - ссылка на C++ хранилище (если используется)
# - _py_store: Any - ссылка на Python хранилище (fallback)
# - _use_cpp: bool - флаг использования C++ бэкенда
# - _max_history_size: int - максимальный размер истории
# - _operation_timings: Dict[str, List[float]] - история таймингов операций
# - _timing_lock: Any - блокировка для thread-safety таймингов
# METHODS:
# - Управление метриками => add_metric, get_metric, get_all_metrics, clear_metrics, get_metric_history
# - Статистика => get_stats, get_all_stats
# - Тайминги => record_timing, get_average_timing, get_operation_timings
# - Свойства => using_cpp, cpp_available
# KEYWORDS: [PATTERN(9): Repository; DOMAIN(9): Metrics; CONCEPT(8): CppBinding; TECH(7): Fallback; CONCEPT(6): Threading]
# LINKS: [COMPOSES(6): _cpp_store; COMPOSES(6): _py_store; USES_API(7): threading]
# END_CONTRACT

class MetricsStore:
    """
    Унифицированное хранилище метрик производительности.
    
    Обеспечивает единый интерфейс для работы с метриками с поддержкой:
    - C++ бэкенда (при наличии metrics_cpp.so)
    - Python fallback (при недоступности C++ модуля)
    - Таймингов операций
    - Статистических вычислений
    
    Attributes:
        using_cpp: True если используется C++ бэкенд
        cpp_available: True если C++ модуль доступен
    """
    
    # START_METHOD___INIT__
    # START_CONTRACT:
    # PURPOSE: Инициализация хранилища метрик с выбором бэкенда.
    # INPUTS:
    # - max_history_size: int - максимальное количество записей истории для каждой метрики (по умолчанию 10000)
    # OUTPUTS: Инициализированный объект MetricsStore
    # SIDE_EFFECTS:
    # - Создаёт экземпляр C++ или Python хранилища
    # - Инициализирует структуры для таймингов
    # KEYWORDS: [PATTERN(7): Factory; CONCEPT(6): Initialization; TECH(5): BackendSelection]
    # END_CONTRACT
    
    def __init__(self, max_history_size: int = 10000) -> None:
        self._max_history_size = max_history_size
        self._cpp_store = None
        self._py_store = None
        self._operation_timings: Dict[str, List[float]] = {}
        self._use_cpp = CPP_AVAILABLE and _CPP_MODULE['available']
        
        logger.info(f"[MetricsStore][INIT][START] Инициализация хранилища метрик с max_history_size={max_history_size}")
        
        if self._use_cpp:
            # Использование C++ бэкенда
            try:
                self._cpp_store = _CPP_MODULE['MetricsStore'](max_history_size)
                logger.info(f"[MetricsStore][INIT][StepComplete] Используется C++ бэкенд [SUCCESS]")
            except Exception as e:
                logger.warning(f"[MetricsStore][INIT][ExceptionCaught] Ошибка инициализации C++ хранилища: {e}, используем fallback")
                self._use_cpp = False
                self._create_python_store()
        else:
            # Fallback на Python реализацию
            self._create_python_store()
        
        logger.info(f"[MetricsStore][INIT][StepComplete] Инициализация завершена. C++ бэкенд: {self._use_cpp} [SUCCESS]")
    
    # END_METHOD___INIT__
    
    # START_METHOD__CREATE_PYTHON_STORE
    # START_CONTRACT:
    # PURPOSE: Создание Python хранилища как fallback.
    # INPUTS: Нет
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Создаёт экземпляр Python хранилища метрик
    # KEYWORDS: [PATTERN(6): Fallback; CONCEPT(5): Factory]
    # END_CONTRACT
    
    def _create_python_store(self) -> None:
        """Создание Python хранилища метрик (fallback)."""
        try:
            from src.monitor.metrics import MetricsStore as PyMetricsStore
            self._py_store = PyMetricsStore(self._max_history_size)
            logger.info(f"[MetricsStore][_CREATE_PYTHON_STORE][StepComplete] Python хранилище создано [SUCCESS]")
        except ImportError:
            # Python модуль недоступен - создаём встроенный fallback
            logger.warning(f"[MetricsStore][_CREATE_PYTHON_STORE][Warning] Python модуль недоступен, используем встроенный fallback")
            self._py_store = _InMemoryMetricsStore(self._max_history_size)
            logger.info(f"[MetricsStore][_CREATE_PYTHON_STORE][StepComplete] Встроенное Python хранилище создано [SUCCESS]")
        except Exception as e:
            logger.error(f"[MetricsStore][_CREATE_PYTHON_STORE][ExceptionCaught] Не удалось создать Python хранилище: {e} [FAIL]")
            raise
    
    # END_METHOD__CREATE_PYTHON_STORE
    
    # START_PROPERTY_USING_CPP
    # START_CONTRACT:
    # PURPOSE: Проверка использования C++ бэкенда.
    # OUTPUTS:
    # - bool - True если используется C++ бэкенд
    # KEYWORDS: [PATTERN(5): Property; CONCEPT(4): Accessor]
    # END_CONTRACT
    
    @property
    def using_cpp(self) -> bool:
        """Возвращает True если используется C++ бэкенд."""
        return self._use_cpp
    
    # END_PROPERTY_USING_CPP
    
    # START_PROPERTY_CPP_AVAILABLE
    # START_CONTRACT:
    # PURPOSE: Проверка доступности C++ модуля.
    # OUTPUTS:
    # - bool - True если C++ модуль доступен
    # KEYWORDS: [PATTERN(5): Property; CONCEPT(4): Accessor]
    # END_CONTRACT
    
    @property
    def cpp_available(self) -> bool:
        """Возвращает True если C++ модуль доступен."""
        return CPP_AVAILABLE
    
    # END_PROPERTY_CPP_AVAILABLE
    
    # START_METHOD_ADD_METRIC
    # START_CONTRACT:
    # PURPOSE: Добавление метрики с записью в историю.
    # INPUTS:
    # - name: str - имя метрики
    # - value: Any - значение метрики
    # - timestamp: Optional[float] - временная метка (None = текущее время)
    # OUTPUTS: Нет
    # SIDE_EFFECTS:
    # - Обновляет значение метрики в хранилище
    # - Записывает значение в историю
    # KEYWORDS: [PATTERN(8): Repository; CONCEPT(7): WriteOperation; TECH(6): TimeSeries]
    # END_CONTRACT
    
    def add_metric(self, name: str, value: Any, timestamp: Optional[float] = None) -> None:
        """
        Добавление метрики с записью в историю.
        
        Args:
            name: Имя метрики
            value: Значение метрики
            timestamp: Временная метка (по умолчанию текущее время)
        """
        logger.debug(f"[MetricsStore][ADD_METRIC][Params] name={name}, value={value}, timestamp={timestamp}")
        
        # Подготовка данных метрики
        metric_data = {name: value}
        
        if self._use_cpp and self._cpp_store:
            # Использование C++ бэкенда
            try:
                self._cpp_store.update(metric_data)
                logger.debug(f"[MetricsStore][ADD_METRIC][StepComplete] Метрика добавлена через C++ бэкенд [SUCCESS]")
            except Exception as e:
                logger.error(f"[MetricsStore][ADD_METRIC][ExceptionCaught] Ошибка добавления метрики в C++: {e} [FAIL]")
        else:
            # Использование Python бэкенда
            try:
                self._py_store.update(metric_data)
                logger.debug(f"[MetricsStore][ADD_METRIC][StepComplete] Метрика добавлена через Python бэкенд [SUCCESS]")
            except Exception as e:
                logger.error(f"[MetricsStore][ADD_METRIC][ExceptionCaught] Ошибка добавления метрики в Python: {e} [FAIL]")
    
    # END_METHOD_ADD_METRIC
    
    # START_METHOD_GET_METRIC
    # START_CONTRACT:
    # PURPOSE: Получение метрики по имени.
    # INPUTS:
    # - name: str - имя метрики
    # OUTPUTS:
    # - Any - значение метрики или None если не найдена
    # KEYWORDS: [PATTERN(7): Accessor; CONCEPT(6): Getter]
    # END_CONTRACT
    
    def get_metric(self, name: str) -> Any:
        """
        Получение метрики по имени.
        
        Args:
            name: Имя метрики
            
        Returns:
            Значение метрики или None если не найдена
        """
        logger.debug(f"[MetricsStore][GET_METRIC][Params] name={name}")
        
        if self._use_cpp and self._cpp_store:
            try:
                current = self._cpp_store.get_current()
                value = current.get(name)
                logger.debug(f"[MetricsStore][GET_METRIC][ReturnData] value={value} [VALUE]")
                return value
            except Exception as e:
                logger.error(f"[MetricsStore][GET_METRIC][ExceptionCaught] Ошибка получения метрики из C++: {e} [FAIL]")
                return None
        else:
            try:
                current = self._py_store.get_current()
                value = current.get(name)
                logger.debug(f"[MetricsStore][GET_METRIC][ReturnData] value={value} [VALUE]")
                return value
            except Exception as e:
                logger.error(f"[MetricsStore][GET_METRIC][ExceptionCaught] Ошибка получения метрики из Python: {e} [FAIL]")
                return None
    
    # END_METHOD_GET_METRIC
    
    # START_METHOD_GET_ALL_METRICS
    # START_CONTRACT:
    # PURPOSE: Получение всех метрик.
    # INPUTS: Нет
    # OUTPUTS:
    # - Dict[str, Any] - словарь всех метрик
    # KEYWORDS: [PATTERN(7): Accessor; CONCEPT(6): Getter]
    # END_CONTRACT
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Получение всех метрик.
        
        Returns:
            Словарь всех текущих метрик
        """
        logger.debug(f"[MetricsStore][GET_ALL_METRICS][START] Запрос всех метрик")
        
        if self._use_cpp and self._cpp_store:
            try:
                current = self._cpp_store.get_current()
                # Удаляем служебные метки
                result = {k: v for k, v in current.items() if not k.startswith('_')}
                logger.debug(f"[MetricsStore][GET_ALL_METRICS][ReturnData] Количество метрик: {len(result)} [VALUE]")
                return result
            except Exception as e:
                logger.error(f"[MetricsStore][GET_ALL_METRICS][ExceptionCaught] Ошибка получения метрик из C++: {e} [FAIL]")
                return {}
        else:
            try:
                current = self._py_store.get_current()
                result = {k: v for k, v in current.items() if not k.startswith('_')}
                logger.debug(f"[MetricsStore][GET_ALL_METRICS][ReturnData] Количество метрик: {len(result)} [VALUE]")
                return result
            except Exception as e:
                logger.error(f"[MetricsStore][GET_ALL_METRICS][ExceptionCaught] Ошибка получения метрик из Python: {e} [FAIL]")
                return {}
    
    # END_METHOD_GET_ALL_METRICS
    
    # START_METHOD_CLEAR_METRICS
    # START_CONTRACT:
    # PURPOSE: Очистка всех метрик и истории.
    # INPUTS: Нет
    # OUTPUTS: Нет
    # SIDE_EFFECTS:
    # - Сбрасывает все метрики в начальные значения
    # - Очищает историю метрик
    # KEYWORDS: [CONCEPT(6): Cleanup; TECH(5): Reset]
    # END_CONTRACT
    
    def clear_metrics(self) -> None:
        """Очистка всех метрик и истории."""
        logger.info(f"[MetricsStore][CLEAR_METRICS][START] Очистка всех метрик")
        
        if self._use_cpp and self._cpp_store:
            try:
                self._cpp_store.reset()
                logger.info(f"[MetricsStore][CLEAR_METRICS][StepComplete] Метрики очищены через C++ бэкенд [SUCCESS]")
            except Exception as e:
                logger.error(f"[MetricsStore][CLEAR_METRICS][ExceptionCaught] Ошибка очистки в C++: {e} [FAIL]")
        else:
            try:
                self._py_store.reset()
                logger.info(f"[MetricsStore][CLEAR_METRICS][StepComplete] Метрики очищены через Python бэкенд [SUCCESS]")
            except Exception as e:
                logger.error(f"[MetricsStore][CLEAR_METRICS][ExceptionCaught] Ошибка очистки в Python: {e} [FAIL]")
    
    # END_METHOD_CLEAR_METRICS
    
    # START_METHOD_GET_METRIC_HISTORY
    # START_CONTRACT:
    # PURPOSE: Получение истории значений метрики.
    # INPUTS:
    # - name: str - имя метрики
    # - limit: Optional[int] - максимальное количество записей (None = все)
    # OUTPUTS:
    # - List[Any] - список значений истории
    # KEYWORDS: [CONCEPT(7): TimeSeries; TECH(6): History]
    # END_CONTRACT
    
    def get_metric_history(self, name: str, limit: Optional[int] = None) -> List[Any]:
        """
        Получение истории значений метрики.
        
        Args:
            name: Имя метрики
            limit: Максимальное количество записей (по умолчанию все)
            
        Returns:
            Список значений истории метрики
        """
        logger.debug(f"[MetricsStore][GET_METRIC_HISTORY][Params] name={name}, limit={limit}")
        
        if self._use_cpp and self._cpp_store:
            try:
                history = self._cpp_store.get_history(name, limit)
                values = [entry.value for entry in history]
                logger.debug(f"[MetricsStore][GET_METRIC_HISTORY][ReturnData] Количество записей: {len(values)} [VALUE]")
                return values
            except Exception as e:
                logger.error(f"[MetricsStore][GET_METRIC_HISTORY][ExceptionCaught] Ошибка получения истории из C++: {e} [FAIL]")
                return []
        else:
            try:
                history = self._py_store.get_history(name, limit)
                values = [entry.value for entry in history]
                logger.debug(f"[MetricsStore][GET_METRIC_HISTORY][ReturnData] Количество записей: {len(values)} [VALUE]")
                return values
            except Exception as e:
                logger.error(f"[MetricsStore][GET_METRIC_HISTORY][ExceptionCaught] Ошибка получения истории из Python: {e} [FAIL]")
                return []
    
    # END_METHOD_GET_METRIC_HISTORY
    
    # START_METHOD_GET_STATS
    # START_CONTRACT:
    # PURPOSE: Получение статистики по метрике (min, max, avg, count).
    # INPUTS:
    # - name: str - имя метрики
    # OUTPUTS:
    # - Dict[str, float] - словарь со статистикой (min, max, avg, count)
    # KEYWORDS: [CONCEPT(7): Statistics; TECH(6): Aggregation]
    # END_CONTRACT
    
    def get_stats(self, name: str) -> Dict[str, float]:
        """
        Получение статистики по метрике.
        
        Args:
            name: Имя метрики
            
        Returns:
            Словарь со статистикой: min, max, avg, count
        """
        logger.debug(f"[MetricsStore][GET_STATS][Params] name={name}")
        
        history = self.get_metric_history(name)
        
        if not history:
            logger.debug(f"[MetricsStore][GET_STATS][ConditionCheck] Нет данных для статистики: {name} [FAIL]")
            return {"min": 0.0, "max": 0.0, "avg": 0.0, "count": 0}
        
        # Фильтрация числовых значений
        numeric_values = []
        for v in history:
            try:
                numeric_values.append(float(v))
            except (TypeError, ValueError):
                continue
        
        if not numeric_values:
            logger.debug(f"[MetricsStore][GET_STATS][ConditionCheck] Нет числовых значений для статистики: {name} [FAIL]")
            return {"min": 0.0, "max": 0.0, "avg": 0.0, "count": 0}
        
        stats = {
            "min": min(numeric_values),
            "max": max(numeric_values),
            "avg": sum(numeric_values) / len(numeric_values),
            "count": len(numeric_values),
        }
        
        logger.debug(f"[MetricsStore][GET_STATS][ReturnData] stats={stats} [VALUE]")
        return stats
    
    # END_METHOD_GET_STATS
    
    # START_METHOD_GET_ALL_STATS
    # START_CONTRACT:
    # PURPOSE: Получение статистики по всем метрикам.
    # INPUTS: Нет
    # OUTPUTS:
    # - Dict[str, Dict[str, float]] - словарь статистик по всем метрикам
    # KEYWORDS: [CONCEPT(7): Statistics; TECH(6): Aggregation]
    # END_CONTRACT
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Получение статистики по всем метрикам.
        
        Returns:
            Словарь статистик для каждой метрики
        """
        logger.debug(f"[MetricsStore][GET_ALL_STATS][START] Запрос статистики всех метрик")
        
        all_metrics = self.get_all_metrics()
        all_stats = {}
        
        for name in all_metrics.keys():
            # Пропускаем служебные метрики
            if name.startswith('_'):
                continue
            stats = self.get_stats(name)
            if stats["count"] > 0:
                all_stats[name] = stats
        
        logger.debug(f"[MetricsStore][GET_ALL_STATS][ReturnData] Количество метрик со статистикой: {len(all_stats)} [VALUE]")
        return all_stats
    
    # END_METHOD_GET_ALL_STATS
    
    # START_METHOD_RECORD_TIMING
    # START_CONTRACT:
    # PURPOSE: Запись времени выполнения операции.
    # INPUTS:
    # - operation_name: str - имя операции
    # - duration_ms: float - продолжительность в миллисекундах
    # OUTPUTS: Нет
    # SIDE_EFFECTS:
    # - Добавляет время в историю таймингов операции
    # - Автоматически ограничивает размер истории (последние 1000 записей)
    # KEYWORDS: [CONCEPT(7): Performance; TECH(6): Timing; DOMAIN(8): Monitoring]
    # END_CONTRACT
    
    def record_timing(self, operation_name: str, duration_ms: float) -> None:
        """
        Запись времени выполнения операции.
        
        Args:
            operation_name: Имя операции
            duration_ms: Продолжительность в миллисекундах
        """
        logger.debug(f"[MetricsStore][RECORD_TIMING][Params] operation={operation_name}, duration_ms={duration_ms}")
        
        # Формируем имя метрики для тайминга
        timing_name = f"{TIMING_PREFIX}{operation_name}"
        
        # Используем внутреннее хранилище таймингов
        if timing_name not in self._operation_timings:
            self._operation_timings[timing_name] = []
        
        self._operation_timings[timing_name].append(duration_ms)
        
        # Ограничиваем размер истории (последние 1000 записей)
        if len(self._operation_timings[timing_name]) > 1000:
            self._operation_timings[timing_name] = self._operation_timings[timing_name][-1000:]
        
        # Также записываем как метрику
        self.add_metric(timing_name, duration_ms)
        
        logger.debug(f"[MetricsStore][RECORD_TIMING][StepComplete] Тайминг записан: {operation_name}={duration_ms}ms [SUCCESS]")
    
    # END_METHOD_RECORD_TIMING
    
    # START_METHOD_GET_AVERAGE_TIMING
    # START_CONTRACT:
    # PURPOSE: Получение среднего времени выполнения операции.
    # INPUTS:
    # - operation_name: str - имя операции
    # OUTPUTS:
    # - float - среднее время в миллисекундах (0.0 если нет данных)
    # KEYWORDS: [CONCEPT(7): Performance; TECH(6): Aggregation]
    # END_CONTRACT
    
    def get_average_timing(self, operation_name: str) -> float:
        """
        Получение среднего времени выполнения операции.
        
        Args:
            operation_name: Имя операции
            
        Returns:
            Среднее время в миллисекундах
        """
        logger.debug(f"[MetricsStore][GET_AVERAGE_TIMING][Params] operation={operation_name}")
        
        timing_name = f"{TIMING_PREFIX}{operation_name}"
        
        if timing_name not in self._operation_timings or not self._operation_timings[timing_name]:
            logger.debug(f"[MetricsStore][GET_AVERAGE_TIMING][ConditionCheck] Нет данных для {operation_name} [FAIL]")
            return 0.0
        
        timings = self._operation_timings[timing_name]
        avg_timing = sum(timings) / len(timings)
        
        logger.debug(f"[MetricsStore][GET_AVERAGE_TIMING][ReturnData] average={avg_timing}ms [VALUE]")
        return avg_timing
    
    # END_METHOD_GET_AVERAGE_TIMING
    
    # START_METHOD_GET_OPERATION_TIMINGS
    # START_CONTRACT:
    # PURPOSE: Получение всех таймингов операций.
    # INPUTS: Нет
    # OUTPUTS:
    # - Dict[str, List[float]] - словарь таймингов по операциям
    # KEYWORDS: [CONCEPT(7): Performance; TECH(6): Accessor]
    # END_CONTRACT
    
    def get_operation_timings(self) -> Dict[str, List[float]]:
        """
        Получение всех таймингов операций.
        
        Returns:
            Словарь списков таймингов для каждой операции
        """
        logger.debug(f"[MetricsStore][GET_OPERATION_TIMINGS][START] Запрос всех таймингов")
        
        # Возвращаем копию словаря
        result = {k: v.copy() for k, v in self._operation_timings.items()}
        
        logger.debug(f"[MetricsStore][GET_OPERATION_TIMINGS][ReturnData] Количество операций: {len(result)} [VALUE]")
        return result
    
    # END_METHOD_GET_OPERATION_TIMINGS
    
    # START_METHOD_GET_CURRENT
    # START_CONTRACT:
    # PURPOSE: Получение текущих метрик (включая служебные).
    # INPUTS: Нет
    # OUTPUTS:
    # - Dict[str, Any] - словарь текущих метрик
    # KEYWORDS: [PATTERN(7): Accessor; CONCEPT(6): Getter]
    # END_CONTRACT
    
    def get_current(self) -> Dict[str, Any]:
        """
        Получение текущих метрик (включая служебные).
        
        Returns:
            Словарь текущих метрик
        """
        if self._use_cpp and self._cpp_store:
            try:
                return self._cpp_store.get_current()
            except Exception as e:
                logger.error(f"[MetricsStore][GET_CURRENT][ExceptionCaught] Ошибка получения из C++: {e} [FAIL]")
                return {}
        else:
            try:
                return self._py_store.get_current()
            except Exception as e:
                logger.error(f"[MetricsStore][GET_CURRENT][ExceptionCaught] Ошибка получения из Python: {e} [FAIL]")
                return {}
    
    # END_METHOD_GET_CURRENT
    
    # START_METHOD_UPDATE
    # START_CONTRACT:
    # PURPOSE: Обновление нескольких метрик одновременно.
    # INPUTS:
    # - metrics: Dict[str, Any] - словарь метрик для обновления
    # OUTPUTS: Нет
    # KEYWORDS: [PATTERN(8): Repository; CONCEPT(7): BulkWrite]
    # END_CONTRACT
    
    def update(self, metrics: Dict[str, Any]) -> None:
        """
        Обновление нескольких метрик одновременно.
        
        Args:
            metrics: Словарь метрик {name: value, ...}
        """
        logger.debug(f"[MetricsStore][UPDATE][Params] Количество метрик: {len(metrics)}")
        
        if self._use_cpp and self._cpp_store:
            try:
                self._cpp_store.update(metrics)
                logger.debug(f"[MetricsStore][UPDATE][StepComplete] Метрики обновлены через C++ [SUCCESS]")
            except Exception as e:
                logger.error(f"[MetricsStore][UPDATE][ExceptionCaught] Ошибка обновления в C++: {e} [FAIL]")
        else:
            try:
                self._py_store.update(metrics)
                logger.debug(f"[MetricsStore][UPDATE][StepComplete] Метрики обновлены через Python [SUCCESS]")
            except Exception as e:
                logger.error(f"[MetricsStore][UPDATE][ExceptionCaught] Ошибка обновления в Python: {e} [FAIL]")
    
    # END_METHOD_UPDATE
    
    # START_METHOD_GET_SUMMARY
    # START_CONTRACT:
    # PURPOSE: Получение полной сводки метрик.
    # INPUTS: Нет
    # OUTPUTS:
    # - Dict[str, Any] - словарь со сводкой метрик
    # KEYWORDS: [CONCEPT(7): Aggregation; TECH(6): Summary]
    # END_CONTRACT
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Получение полной сводки метрик.
        
        Returns:
            Словарь со сводкой: текущие значения, скорости, статистика, метаданные
        """
        logger.debug(f"[MetricsStore][GET_SUMMARY][START] Запрос сводки метрик")
        
        if self._use_cpp and self._cpp_store:
            try:
                return self._cpp_store.get_summary()
            except Exception as e:
                logger.error(f"[MetricsStore][GET_SUMMARY][ExceptionCaught] Ошибка получения сводки из C++: {e} [FAIL]")
                return {}
        else:
            try:
                return self._py_store.get_summary()
            except Exception as e:
                logger.error(f"[MetricsStore][GET_SUMMARY][ExceptionCaught] Ошибка получения сводки из Python: {e} [FAIL]")
                return {}
    
    # END_METHOD_GET_SUMMARY
    
    # START_METHOD_SUBSCRIBE
    # START_CONTRACT:
    # PURPOSE: Подписка на обновления метрик.
    # INPUTS:
    # - callback: Callable - функция обратного вызова
    # OUTPUTS: Нет
    # KEYWORDS: [PATTERN(7): Observer; CONCEPT(6): Subscription]
    # END_CONTRACT
    
    def subscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Подписка на обновления метрик.
        
        Args:
            callback: Функция, вызываемая при каждом обновлении метрик
        """
        logger.debug(f"[MetricsStore][SUBSCRIBE][START] Регистрация подписки")
        
        if self._use_cpp and self._cpp_store:
            try:
                self._cpp_store.subscribe(callback)
                logger.debug(f"[MetricsStore][SUBSCRIBE][StepComplete] Подписка зарегистрирована в C++ [SUCCESS]")
            except Exception as e:
                logger.error(f"[MetricsStore][SUBSCRIBE][ExceptionCaught] Ошибка подписки в C++: {e} [FAIL]")
        else:
            try:
                self._py_store.subscribe(callback)
                logger.debug(f"[MetricsStore][SUBSCRIBE][StepComplete] Подписка зарегистрирована в Python [SUCCESS]")
            except Exception as e:
                logger.error(f"[MetricsStore][SUBSCRIBE][ExceptionCaught] Ошибка подписки в Python: {e} [FAIL]")
    
    # END_METHOD_SUBSCRIBE
    
    # START_METHOD_UNSUBSCRIBE
    # START_CONTRACT:
    # PURPOSE: Отписка от обновлений метрик.
    # INPUTS:
    # - callback: Callable - функция обратного вызова для удаления
    # OUTPUTS: Нет
    # KEYWORDS: [CONCEPT(6): Unsubscription]
    # END_CONTRACT
    
    def unsubscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Отписка от обновлений метрик.
        
        Args:
            callback: Функция для удаления из подписчиков
        """
        logger.debug(f"[MetricsStore][UNSUBSCRIBE][START] Удаление подписки")
        
        if self._use_cpp and self._cpp_store:
            try:
                self._cpp_store.unsubscribe(callback)
                logger.debug(f"[MetricsStore][UNSUBSCRIBE][StepComplete] Подписка удалена из C++ [SUCCESS]")
            except Exception as e:
                logger.warning(f"[MetricsStore][UNSUBSCRIBE][ExceptionCaught] Ошибка отписки в C++: {e}")
        else:
            try:
                self._py_store.unsubscribe(callback)
                logger.debug(f"[MetricsStore][UNSUBSCRIBE][StepComplete] Подписка удалена из Python [SUCCESS]")
            except Exception as e:
                logger.warning(f"[MetricsStore][UNSUBSCRIBE][ExceptionCaught] Ошибка отписки в Python: {e}")
    
    # END_METHOD_UNSUBSCRIBE
    
    # START_METHOD_GET_SNAPSHOT
    # START_CONTRACT:
    # PURPOSE: Получение атомарного снимка всех метрик.
    # INPUTS: Нет
    # OUTPUTS:
    # - Dict[str, Any] - полный снимок метрик
    # KEYWORDS: [PATTERN(8): Snapshot; CONCEPT(7): Atomic]
    # END_CONTRACT
    
    def get_snapshot(self) -> Dict[str, Any]:
        """
        Получение атомарного снимка всех метрик.
        
        Returns:
            Словарь со снимком: текущие метрики, история, временная метка, счётчик обновлений
        """
        logger.debug(f"[MetricsStore][GET_SNAPSHOT][START] Запрос снимка метрик")
        
        if self._use_cpp and self._cpp_store:
            try:
                return self._cpp_store.get_snapshot()
            except Exception as e:
                logger.error(f"[MetricsStore][GET_SNAPSHOT][ExceptionCaught] Ошибка получения снимка из C++: {e} [FAIL]")
                return {}
        else:
            try:
                return self._py_store.get_snapshot()
            except Exception as e:
                logger.error(f"[MetricsStore][GET_SNAPSHOT][ExceptionCaught] Эшибка получения снимка из Python: {e} [FAIL]")
                return {}
    
    # END_METHOD_GET_SNAPSHOT
    
    # START_METHOD_RESET
    # START_CONTRACT:
    # PURPOSE: Сброс всех метрик в начальное состояние.
    # INPUTS: Нет
    # OUTPUTS: Нет
    # KEYWORDS: [CONCEPT(6): Reset; TECH(5): Cleanup]
    # END_CONTRACT
    
    def reset(self) -> None:
        """Сброс всех метрик в начальное состояние."""
        logger.info(f"[MetricsStore][RESET][START] Сброс всех метрик")
        self.clear_metrics()
        self._operation_timings = {}
        logger.info(f"[MetricsStore][RESET][StepComplete] Сброс выполнен [SUCCESS]")
    
    # END_METHOD_RESET
    
    # START_METHOD_GET_METRIC_NAMES
    # START_CONTRACT:
    # PURPOSE: Получение списка всех имён метрик.
    # INPUTS: Нет
    # OUTPUTS:
    # - List[str] - список имён метрик
    # KEYWORDS: [CONCEPT(5): Enumeration]
    # END_CONTRACT
    
    def get_metric_names(self) -> List[str]:
        """
        Получение списка всех имён метрик.
        
        Returns:
            Список имён метрик
        """
        logger.debug(f"[MetricsStore][GET_METRIC_NAMES][START] Запрос имён метрик")
        
        all_metrics = self.get_all_metrics()
        names = list(all_metrics.keys())
        
        logger.debug(f"[MetricsStore][GET_METRIC_NAMES][ReturnData] Количество метрик: {len(names)} [VALUE]")
        return names
    
    # END_METHOD_GET_METRIC_NAMES
    
    # START_METHOD_COMPUTE_RATE
    # START_CONTRACT:
    # PURPOSE: Вычисление скорости изменения метрики.
    # INPUTS:
    # - metric_name: str - имя метрики
    # - window_seconds: int - временное окно в секундах (по умолчанию 60)
    # OUTPUTS:
    # - float - скорость изменения (единиц в секунду)
    # KEYWORDS: [CONCEPT(7): RateCalculation; TECH(6): SlidingWindow]
    # END_CONTRACT
    
    def compute_rate(self, metric_name: str, window_seconds: int = 60) -> float:
        """
        Вычисление скорости изменения метрики.
        
        Args:
            metric_name: Имя метрики
            window_seconds: Временное окно в секундах
            
        Returns:
            Скорость изменения (единиц в секунду)
        """
        logger.debug(f"[MetricsStore][COMPUTE_RATE][Params] metric={metric_name}, window={window_seconds}s")
        
        if self._use_cpp and self._cpp_store:
            try:
                rate = self._cpp_store.compute_rate(metric_name, window_seconds)
                logger.debug(f"[MetricsStore][COMPUTE_RATE][ReturnData] rate={rate} [VALUE]")
                return rate
            except Exception as e:
                logger.error(f"[MetricsStore][COMPUTE_RATE][ExceptionCaught] Ошибка вычисления в C++: {e} [FAIL]")
                return 0.0
        else:
            try:
                rate = self._py_store.compute_rate(metric_name, window_seconds)
                logger.debug(f"[MetricsStore][COMPUTE_RATE][ReturnData] rate={rate} [VALUE]")
                return rate
            except Exception as e:
                logger.error(f"[MetricsStore][COMPUTE_RATE][ExceptionCaught] Ошибка вычисления в Python: {e} [FAIL]")
                return 0.0
    
    # END_METHOD_COMPUTE_RATE


# END_CLASS_METRICS_STORE


# START_FUNCTION_CREATE_METRICS_STORE
# START_CONTRACT:
# PURPOSE: Фабричная функция для создания хранилища метрик.
# INPUTS:
# - max_history_size: int - максимальный размер истории (по умолчанию 10000)
# OUTPUTS:
# - MetricsStore - созданное хранилище метрик
# KEYWORDS: [PATTERN(7): Factory; CONCEPT(6): FactoryFunction]
# END_CONTRACT

def create_metrics_store(max_history_size: int = 10000) -> MetricsStore:
    """
    Фабричная функция для создания хранилища метрик.
    
    Args:
        max_history_size: Максимальный размер истории для каждой метрики
        
    Returns:
        Экземпляр MetricsStore
    """
    logger.info(f"[create_metrics_store][START] Создание хранилища метрик с max_history_size={max_history_size}")
    store = MetricsStore(max_history_size=max_history_size)
    logger.info(f"[create_metrics_store][StepComplete] Хранилище создано, C++: {store.using_cpp} [SUCCESS]")
    return store

# END_FUNCTION_CREATE_METRICS_STORE


# START_BLOCK_EXPORT: [Экспорт публичного API]
__all__ = [
    'MetricsStore',
    'create_metrics_store',
    # Константы
    'ITERATION_COUNT',
    'MATCH_COUNT',
    'WALLET_COUNT',
    'ELAPSED_TIME',
    'ENTROPY_DATA',
    'ADDRESSES_EXTRACTED',
    'MATCHES_FOUND',
    'ITERATIONS_PER_SECOND',
    'WALLETS_PER_SECOND',
    # Флаги
    'CPP_AVAILABLE',
]
# END_BLOCK_EXPORT

logger.info(f"[InitModule][metrics_wrapper][FINALIZE] Модуль полностью загружен. C++ доступен: {CPP_AVAILABLE} [SUCCESS]")
