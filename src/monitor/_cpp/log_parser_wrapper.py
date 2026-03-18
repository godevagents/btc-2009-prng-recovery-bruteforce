# FILE: src/monitor/_cpp/log_parser_wrapper.py
# VERSION: 1.0.0

# START_MODULE_CONTRACT:
# PURPOSE: Python-обёртка для C++ модуля парсинга логов (log_parser_cpp.so). Обеспечивает единый интерфейс для работы с парсингом логов с автоматическим fallback на Python реализацию.
# SCOPE: парсинг логов, извлечение метрик, real-time мониторинг, фильтрация записей, статистика парсинга
# INPUT: C++ модуль log_parser_cpp или Python модуль src.monitor.integrations.log_parser
# OUTPUT: Класс LogParser с унифицированным API
# KEYWORDS: [DOMAIN(9): LogParsing; DOMAIN(8): Monitoring; CONCEPT(7): CppBinding; TECH(6): Fallback; CONCEPT(5): Regex]
# LINKS: [USES_API(8): log_parser_cpp.so; FALLBACK_TO(7): src.monitor.integrations.log_parser; COMPOSES(6): _cpp_init]
# LINKS_TO_SPECIFICATION: [Требования к единому API парсинга логов с поддержкой C++ бэкенда]
# END_MODULE_CONTRACT

# START_MODULE_MAP:
# CLASS 9 [Унифицированный парсер логов с C++ бэкендом] => LogParser
# DATA_CLASS 7 [Запись распарсенного лога] => LogEntry
# FUNC 5 [Вспомогательная функция импорта C++ модуля] => _import_cpp_module
# FUNC 5 [Создание экземпляра парсера] => create_log_parser
# CONST 5 [Уровень лога DEBUG] => LEVEL_DEBUG
# CONST 5 [Уровень лога INFO] => LEVEL_INFO
# CONST 5 [Уровень лога WARNING] => LEVEL_WARNING
# CONST 5 [Уровень лога ERROR] => LEVEL_ERROR
# END_MODULE_MAP

# START_USE_CASES:
# - [LogParser.parse_line]: Monitor (RealTime) -> ParseSingleLine -> EntryExtracted
# - [LogParser.parse_file]: Monitor (Startup) -> ParseFullLog -> AllEntriesAvailable
# - [LogParser.parse_stream]: System (Streaming) -> ParseStreamData -> EntriesExtracted
# - [LogParser.get_entries_by_level]: Dashboard (Filter) -> FilterByLevel -> FilteredEntries
# - [LogParser.get_entries_by_pattern]: Analyst (Search) -> RegexSearch -> MatchingEntries
# - [LogParser.get_statistics]: Admin (Analysis) -> CalculateStats -> StatsProvided
# END_USE_CASES

"""
Python-обёртка для C++ модуля парсинга логов.

Обеспечивает:
- Адаптацию C++ API к Python-интерфейсу
- Автоматическое преобразование типов
- Обработку исключений
- Логирование операций
- Fallback на Python реализацию при недоступности C++ модуля
- Фильтрацию записей по уровню и паттерну
- Статистику парсинга

Использование:
    from src.monitor._cpp.log_parser_wrapper import LogParser
    
    parser = LogParser(log_path="logs/infinite_loop.log")
    entries = parser.parse_file()
    
    # Фильтрация по уровню
    error_entries = parser.get_entries_by_level("ERROR")
    
    # Поиск по паттерну
    matches = parser.get_entries_by_pattern(r"Iteration: \d+")
    
    # Получение статистики
    stats = parser.get_statistics()
"""

# START_BLOCK_IMPORT_MODULES: [Импорт необходимых модулей]
import logging
import os
import sys
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Iterator
from dataclasses import dataclass, field
from collections import deque

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
logger.info(f"[InitModule][log_parser_wrapper][IMPORT_MODULES][StepComplete] Модуль загружен. app.log: {app_log_path} [SUCCESS]")
# END_BLOCK_IMPORT_MODULES


# START_BLOCK_CONSTANTS: [Определение констант уровней логов]
# Стандартные уровни логов
LEVEL_DEBUG = "DEBUG"
LEVEL_INFO = "INFO"
LEVEL_WARNING = "WARNING"
LEVEL_ERROR = "ERROR"
LEVEL_CRITICAL = "CRITICAL"

# Список всех уровней по возрастанию важности
LOG_LEVELS = [LEVEL_DEBUG, LEVEL_INFO, LEVEL_WARNING, LEVEL_ERROR, LEVEL_CRITICAL]

# Константы для парсинга
DEFAULT_LOG_PATH = "logs/infinite_loop.log"
DEFAULT_MAX_ENTRIES = 10000
# END_BLOCK_CONSTANTS


# START_DATA_CLASS_LOG_ENTRY
# START_CONTRACT:
# PURPOSE: Запись распарсенного лога с структурированными данными. dataclass для хранения
# структурированной информации из строки лога.
# ATTRIBUTES:
# - timestamp: datetime — временная метка записи
# - level: str — уровень лога (DEBUG, INFO, WARNING, ERROR)
# - source: str — источник записи
# - message: str — текст сообщения
# - metadata: Dict[str, Any] — дополнительные метаданные
# KEYWORDS: [PATTERN(6): DataClass; DOMAIN(7): LogData; CONCEPT(5): StructuredLog]
# END_CONTRACT

@dataclass
class LogEntry:
    """
    Запись распарсенного лога с структурированными данными.
    """
    timestamp: datetime
    level: str
    source: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Дополнительные поля для совместимости с Python парсером
    raw_line: str = ""
    iteration_count: Optional[int] = None
    match_count: Optional[int] = None
    wallet_count: Optional[int] = None
    entropy_bits: Optional[float] = None
    stage: Optional[str] = None
    error: Optional[str] = None


# START_FUNCTION__IMPORT_CPP_MODULE
# START_CONTRACT:
# PURPOSE: Импорт C++ модуля парсера логов с обработкой ошибок и fallback.
# INPUTS: Нет
# OUTPUTS:
# - Dict[str, Any] - словарь с информацией о доступности модуля
# SIDE_EFFECTS:
# - Выполняет попытку импорта модуля log_parser_cpp
# KEYWORDS: [PATTERN(7): ModuleImport; DOMAIN(8): CppBinding; TECH(6): DynamicImport]
# END_CONTRACT

def _import_cpp_module() -> Dict[str, Any]:
    """
    Импорт C++ модуля парсера логов с fallback на Python.
    
    Returns:
        Словарь с информацией о доступности модуля:
        - 'available': bool - флаг доступности
        - 'LogParser': класс C++ LogParser (если доступен)
        - 'ParsedEntry': класс C++ ParsedEntry (если доступен)
        - 'error': str - сообщение об ошибке (если недоступен)
    """
    logger.debug(f"[_import_cpp_module][START] Попытка импорта C++ модуля log_parser_cpp")
    
    try:
        # Попытка импорта C++ модуля
        from log_parser_cpp import LogParser as _LogParser
        from log_parser_cpp import ParsedEntry as _ParsedEntry
        
        # Тест работоспособности - создаём тестовый экземпляр
        test_parser = _LogParser("logs/test_buffer.log", 10)
        del test_parser
        
        logger.info(f"[_import_cpp_module][ConditionCheck] C++ модуль log_parser_cpp успешно загружен [SUCCESS]")
        
        return {
            'available': True,
            'LogParser': _LogParser,
            'ParsedEntry': _ParsedEntry,
            'error': None,
        }
        
    except ImportError as e:
        logger.warning(f"[_import_cpp_module][ConditionCheck] C++ модуль log_parser_cpp недоступен: {e} [FAIL]")
        return {
            'available': False,
            'LogParser': None,
            'ParsedEntry': None,
            'error': str(e),
        }
    except Exception as e:
        logger.error(f"[_import_cpp_module][ExceptionCaught] Неожиданная ошибка при импорте C++ модуля: {e} [FAIL]")
        return {
            'available': False,
            'LogParser': None,
            'ParsedEntry': None,
            'error': str(e),
        }

# END_FUNCTION__IMPORT_CPP_MODULE


# START_BLOCK_CPP_MODULE_INITIALIZATION: [Инициализация C++ модуля]
# Попытка импорта C++ модуля при загрузке модуля
_CPP_MODULE = _import_cpp_module()
CPP_AVAILABLE = _CPP_MODULE['available']
# END_BLOCK_CPP_MODULE_INITIALIZATION


# START_FUNCTION__CONVERT_CPP_ENTRY_TO_LOG_ENTRY
# START_CONTRACT:
# PURPOSE: Конвертация C++ записи ParsedEntry в Python LogEntry.
# INPUTS:
# - cpp_entry: Any - C++ запись ParsedEntry
# OUTPUTS:
# - LogEntry - Python представление записи
# SIDE_EFFECTS: Нет
# KEYWORDS: [PATTERN(6): Adapter; CONCEPT(5): Conversion; TECH(4): TypeCast]
# END_CONTRACT

def _convert_cpp_entry_to_log_entry(cpp_entry: Any) -> LogEntry:
    """
    Конвертация C++ записи ParsedEntry в Python LogEntry.
    
    Args:
        cpp_entry: C++ запись ParsedEntry
        
    Returns:
        Python LogEntry объект
    """
    try:
        # Извлечение данных из C++ объекта
        timestamp = datetime.fromtimestamp(cpp_entry.timestamp) if cpp_entry.timestamp else datetime.now()
        
        # Определение уровня на основе содержимого
        level = LEVEL_INFO
        message = cpp_entry.raw_line if hasattr(cpp_entry, 'raw_line') else ""
        
        if cpp_entry.error:
            level = LEVEL_ERROR
            message = cpp_entry.error
        elif "error" in message.lower() or "exception" in message.lower():
            level = LEVEL_ERROR
        elif "warning" in message.lower() or "warn" in message.lower():
            level = LEVEL_WARNING
        elif "debug" in message.lower():
            level = LEVEL_DEBUG
            
        # Сбор метаданных
        metadata = {}
        if cpp_entry.iteration_count is not None:
            metadata['iteration_count'] = cpp_entry.iteration_count
        if cpp_entry.match_count is not None:
            metadata['match_count'] = cpp_entry.match_count
        if cpp_entry.wallet_count is not None:
            metadata['wallet_count'] = cpp_entry.wallet_count
        if cpp_entry.entropy_bits is not None:
            metadata['entropy_bits'] = cpp_entry.entropy_bits
        if cpp_entry.stage is not None:
            metadata['stage'] = cpp_entry.stage
        if cpp_entry.error is not None:
            metadata['error'] = cpp_entry.error
            
        return LogEntry(
            timestamp=timestamp,
            level=level,
            source="log_parser",
            message=message,
            metadata=metadata,
            raw_line=cpp_entry.raw_line if hasattr(cpp_entry, 'raw_line') else "",
            iteration_count=cpp_entry.iteration_count if hasattr(cpp_entry, 'iteration_count') else None,
            match_count=cpp_entry.match_count if hasattr(cpp_entry, 'match_count') else None,
            wallet_count=cpp_entry.wallet_count if hasattr(cpp_entry, 'wallet_count') else None,
            entropy_bits=cpp_entry.entropy_bits if hasattr(cpp_entry, 'entropy_bits') else None,
            stage=cpp_entry.stage if hasattr(cpp_entry, 'stage') else None,
            error=cpp_entry.error if hasattr(cpp_entry, 'error') else None,
        )
        
    except Exception as e:
        logger.error(f"[_convert_cpp_entry_to_log_entry][ExceptionCaught] Ошибка конвертации: {e} [FAIL]")
        # Возвращаем базовую запись в случае ошибки
        return LogEntry(
            timestamp=datetime.now(),
            level=LEVEL_INFO,
            source="log_parser",
            message=str(cpp_entry) if cpp_entry else "",
            metadata={},
        )

# END_FUNCTION__CONVERT_CPP_ENTRY_TO_LOG_ENTRY


# START_FUNCTION__DETECT_LOG_LEVEL
# START_CONTRACT:
# PURPOSE: Определение уровня лога по содержимому строки.
# INPUTS:
# - line: str - строка лога
# OUTPUTS:
# - str - определённый уровень лога
# SIDE_EFFECTS: Нет
# KEYWORDS: [PATTERN(5): Detection; DOMAIN(6): LogLevel; CONCEPT(4): Heuristic]
# END_CONTRACT

def _detect_log_level(line: str) -> str:
    """
    Определение уровня лога по содержимому строки.
    
    Args:
        line: строка лога
        
    Returns:
        Уровень лога (DEBUG, INFO, WARNING, ERROR)
    """
    line_lower = line.lower()
    
    if "error" in line_lower or "exception" in line_lower or "critical" in line_lower:
        return LEVEL_ERROR
    elif "warning" in line_lower or "warn" in line_lower:
        return LEVEL_WARNING
    elif "debug" in line_lower:
        return LEVEL_DEBUG
    else:
        return LEVEL_INFO

# END_FUNCTION__DETECT_LOG_LEVEL


# START_CLASS_LOG_PARSER
# START_CONTRACT:
# PURPOSE: Унифицированный парсер логов с поддержкой C++ бэкенда. Обеспечивает единый интерфейс для работы с парсингом логов независимо от реализации.
# ATTRIBUTES:
# - _cpp_parser: Any - ссылка на C++ парсер (если используется)
# - _py_parser: Any - ссылка на Python парсер (fallback)
# - _use_cpp: bool - флаг использования C++ бэкенда
# - _log_path: str - путь к лог-файлу
# - _entries: Deque[LogEntry] - кэш записей
# - _filter_func: Optional[Callable] - функция фильтрации
# - _statistics: Dict[str, Any] - статистика парсинга
# METHODS:
# - Парсинг => parse_line, parse_file, parse_stream
# - Фильтрация => get_entries_by_level, get_entries_by_pattern, set_filter
# - Доступ к данным => get_entries, clear
# - Статистика => get_statistics
# - Свойства => using_cpp, cpp_available, entry_count
# KEYWORDS: [PATTERN(9): Parser; DOMAIN(9): LogParsing; CONCEPT(8): CppBinding; TECH(7): Fallback; CONCEPT(6): Filtering]
# LINKS: [COMPOSES(6): _cpp_parser; COMPOSES(6): _py_parser; USES_API(7): log_parser_cpp]
# END_CONTRACT

class LogParser:
    """
    Унифицированный парсер логов.
    
    Обеспечивает единый интерфейс для работы с парсингом логов с поддержкой:
    - C++ бэкенда (при наличии log_parser_cpp.so)
    - Python fallback (при недоступности C++ модуля)
    - Фильтрации записей по уровню и паттерну
    - Статистики парсинга
    - Real-time мониторинга
    
    Attributes:
        using_cpp: True если используется C++ бэкенд
        cpp_available: True если C++ модуль доступен
        entry_count: Количество распарсенных записей
    """
    
    # START_METHOD___INIT__
    # START_CONTRACT:
    # PURPOSE: Инициализация парсера логов с выбором бэкенда.
    # INPUTS:
    # - log_path: Optional[str] - путь к лог-файлу (по умолчанию "logs/infinite_loop.log")
    # - max_entries: int - максимальное количество записей в кэше (по умолчанию 10000)
    # OUTPUTS: Инициализированный объект LogParser
    # SIDE_EFFECTS:
    # - Создаёт экземпляр C++ или Python парсера
    # - Инициализирует структуры для хранения записей
    # KEYWORDS: [PATTERN(7): Factory; CONCEPT(6): Initialization; TECH(5): BackendSelection]
    # END_CONTRACT
    
    def __init__(self, log_path: Optional[str] = None, max_entries: int = DEFAULT_MAX_ENTRIES) -> None:
        self._log_path = log_path or DEFAULT_LOG_PATH
        self._max_entries = max_entries
        self._cpp_parser = None
        self._py_parser = None
        self._use_cpp = CPP_AVAILABLE and _CPP_MODULE['available']
        self._entries: Deque[LogEntry] = deque(maxlen=max_entries)
        self._filter_func: Optional[Callable[[LogEntry], bool]] = None
        # Атрибуты для parse_new_lines (real-time мониторинг)
        self._last_file_position: int = 0
        self._last_parse_time: float = 0
        self._is_monitoring: bool = False
        # Текущие метрики
        self._current_iteration: int = 0
        self._current_match: int = 0
        self._current_wallet: int = 0
        self._current_entropy: float = 0.0
        self._current_stage: str = "idle"
        self._statistics: Dict[str, Any] = {
            'total_lines_parsed': 0,
            'total_entries_extracted': 0,
            'parse_time_seconds': 0.0,
            'entries_by_level': {level: 0 for level in LOG_LEVELS},
            'errors_count': 0,
            'last_parse_time': None,
        }
        
        logger.info(f"[LogParser][INIT][START] Инициализация парсера логов с path={self._log_path}, max_entries={max_entries}")
        
        if self._use_cpp:
            # Использование C++ бэкенда
            try:
                self._cpp_parser = _CPP_MODULE['LogParser'](self._log_path, max_entries)
                logger.info(f"[LogParser][INIT][StepComplete] Используется C++ бэкенд [SUCCESS]")
            except Exception as e:
                logger.warning(f"[LogParser][INIT][ExceptionCaught] Ошибка инициализации C++ парсера: {e}, используем fallback")
                self._use_cpp = False
                self._create_python_parser()
        else:
            # Fallback на Python реализацию
            self._create_python_parser()
        
        logger.info(f"[LogParser][INIT][StepComplete] Инициализация завершена. C++ бэкенд: {self._use_cpp} [SUCCESS]")
    
    # END_METHOD___INIT__
    
    # START_METHOD__CREATE_PYTHON_PARSER
    # START_CONTRACT:
    # PURPOSE: Создание Python парсера как fallback.
    # INPUTS: Нет
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Создаёт экземпляр Python парсера логов
    # KEYWORDS: [PATTERN(6): Fallback; CONCEPT(5): Factory]
    # END_CONTRACT
    
    def _create_python_parser(self) -> None:
        """Создание Python парсера логов (fallback)."""
        try:
            from src.monitor.integrations.log_parser import LogParser as PyLogParser
            self._py_parser = PyLogParser(self._log_path, self._max_entries)
            logger.info(f"[LogParser][_CREATE_PYTHON_PARSER][StepComplete] Python парсер создан [SUCCESS]")
        except Exception as e:
            logger.error(f"[LogParser][_CREATE_PYTHON_PARSER][ExceptionCaught] Не удалось создать Python парсер: {e} [FAIL]")
            # Создаём пустой парсер без внешней зависимости
            self._py_parser = None
            logger.warning(f"[LogParser][_CREATE_PYTHON_PARSER][Warning] Используется встроенный Python парсер [INFO]")
    
    # END_METHOD__CREATE_PYTHON_PARSER
    
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
    
    # START_PROPERTY_ENTRY_COUNT
    # START_CONTRACT:
    # PURPOSE: Получение количества распарсенных записей.
    # OUTPUTS:
    # - int - количество записей в кэше
    # KEYWORDS: [PATTERN(5): Property; CONCEPT(4): Accessor]
    # END_CONTRACT
    
    @property
    def entry_count(self) -> int:
        """Возвращает количество распарсенных записей."""
        return len(self._entries)
    
    # END_PROPERTY_ENTRY_COUNT
    
    # START_METHOD_PARSE_LINE
    # START_CONTRACT:
    # PURPOSE: Парсинг одной строки лога.
    # INPUTS:
    # - line: str - строка лога для парсинга
    # OUTPUTS:
    # - Optional[LogEntry] - распарсенная запись или None
    # SIDE_EFFECTS:
    # - Добавляет запись в кэш
    # - Обновляет статистику
    # KEYWORDS: [PATTERN(7): Parser; DOMAIN(8): LogParsing; TECH(6): SingleLine]
    # END_CONTRACT
    
    def parse_line(self, line: str) -> Optional[LogEntry]:
        """
        Парсинг одной строки лога.
        
        Args:
            line: строка лога для парсинга
            
        Returns:
            LogEntry объект или None если строка не содержит данных
        """
        logger.debug(f"[LogParser][PARSE_LINE][Params] line_length={len(line)}")
        
        if not line or not line.strip():
            return None
        
        self._statistics['total_lines_parsed'] += 1
        entry = None
        
        if self._use_cpp and self._cpp_parser:
            # Использование C++ бэкенда
            try:
                cpp_entries = self._cpp_parser.parse_line(line)
                if cpp_entries:
                    # C++ парсер может вернуть список или одну запись
                    if isinstance(cpp_entries, list):
                        if cpp_entries:
                            entry = _convert_cpp_entry_to_log_entry(cpp_entries[0])
                    else:
                        entry = _convert_cpp_entry_to_log_entry(cpp_entries)
            except Exception as e:
                logger.error(f"[LogParser][PARSE_LINE][ExceptionCaught] Ошибка парсинга в C++: {e} [FAIL]")
        else:
            # Использование Python бэкенда
            entry = self._parse_line_python(line)
        
        if entry:
            self._entries.append(entry)
            self._statistics['total_entries_extracted'] += 1
            self._statistics['entries_by_level'][entry.level] = self._statistics['entries_by_level'].get(entry.level, 0) + 1
            
            if entry.level == LEVEL_ERROR:
                self._statistics['errors_count'] += 1
            
            logger.debug(f"[LogParser][PARSE_LINE][StepComplete] Запись добавлена: level={entry.level} [SUCCESS]")
        else:
            logger.debug(f"[LogParser][PARSE_LINE][ConditionCheck] Запись не извлечена [FAIL]")
        
        return entry
    
    # END_METHOD_PARSE_LINE
    
    # START_METHOD__PARSE_LINE_PYTHON
    # START_CONTRACT:
    # PURPOSE: Парсинг строки с использованием Python (fallback).
    # INPUTS:
    # - line: str - строка лога
    # OUTPUTS:
    # - Optional[LogEntry] - распарсенная запись
    # KEYWORDS: [PATTERN(6): Fallback; DOMAIN(7): Python]
    # END_CONTRACT
    
    def _parse_line_python(self, line: str) -> Optional[LogEntry]:
        """
        Парсинг строки с использованием Python (fallback).
        
        Args:
            line: строка лога
            
        Returns:
            LogEntry объект
        """
        try:
            if self._py_parser:
                # Используем Python парсер из модуля
                py_entry = self._py_parser._parse_line(line)
                if py_entry:
                    return self._convert_python_entry_to_log_entry(py_entry)
            else:
                # Встроенный парсер
                return self._parse_line_builtin(line)
        except Exception as e:
            logger.error(f"[LogParser][_PARSE_LINE_PYTHON][ExceptionCaught] Ошибка Python парсинга: {e} [FAIL]")
        
        return None
    
    # END_METHOD__PARSE_LINE_PYTHON
    
    # START_METHOD__PARSE_LINE_BUILTIN
    # START_CONTRACT:
    # PURPOSE: Встроенный парсинг строки без внешних зависимостей.
    # INPUTS:
    # - line: str - строка лога
    # OUTPUTS:
    # - Optional[LogEntry] - распарсенная запись
    # KEYWORDS: [PATTERN(6): Builtin; DOMAIN(7): Parser]
    # END_CONTRACT
    
    def _parse_line_builtin(self, line: str) -> Optional[LogEntry]:
        """
        Встроенный парсинг строки без внешних зависимостей.
        
        Args:
            line: строка лога
            
        Returns:
            LogEntry объект
        """
        import re
        
        timestamp = datetime.now()
        
        # Попытка извлечения timestamp
        ts_patterns = [
            (r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", "%Y-%m-%d %H:%M:%S"),
            (r"(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})", "%m/%d/%Y %H:%M:%S"),
        ]
        
        for pattern, fmt in ts_patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    timestamp = datetime.strptime(match.group(1), fmt)
                except ValueError:
                    pass
                break
        
        # Определение уровня
        level = _detect_log_level(line)
        
        # Извлечение метрик
        metadata = {}
        
        # Iteration
        iter_match = re.search(r"(?:Iteration|iteration|ITERATION)[s]?\s*[:=]?\s*(\d+)", line, re.IGNORECASE)
        if iter_match:
            try:
                metadata['iteration_count'] = int(iter_match.group(1))
            except (ValueError, IndexError):
                pass
        
        # Match
        match_count = re.search(r"(?:Match|match|MATCH)[s]?\s*[:=]?\s*(\d+)", line, re.IGNORECASE)
        if match_count:
            try:
                metadata['match_count'] = int(match_count.group(1))
            except (ValueError, IndexError):
                pass
        
        # Wallet
        wallet_count = re.search(r"(?:Wallet|wallet|WALLET)[s]?\s*[:=]?\s*(\d+)", line, re.IGNORECASE)
        if wallet_count:
            try:
                metadata['wallet_count'] = int(wallet_count.group(1))
            except (ValueError, IndexError):
                pass
        
        # Entropy
        entropy = re.search(r"(?:Entropy|entropy|ENTROPY)[s]?\s*[:=]?\s*(\d+\.?\d*)\s*(?:bits)?", line, re.IGNORECASE)
        if entropy:
            try:
                metadata['entropy_bits'] = float(entropy.group(1))
            except (ValueError, IndexError):
                pass
        
        # Stage
        stage = re.search(r"(?:Stage|stage|STAGE)[s]?\s*[:=]?\s*(\w+)", line, re.IGNORECASE)
        if stage:
            metadata['stage'] = stage.group(1)
        
        # Error
        error = re.search(r"(?:Error|ERROR|Exception|EXCEPTION)[:\s]+(.+)", line, re.IGNORECASE)
        if error:
            metadata['error'] = error.group(1).strip()
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            source="log_parser",
            message=line.strip(),
            metadata=metadata,
            raw_line=line.strip(),
            iteration_count=metadata.get('iteration_count'),
            match_count=metadata.get('match_count'),
            wallet_count=metadata.get('wallet_count'),
            entropy_bits=metadata.get('entropy_bits'),
            stage=metadata.get('stage'),
            error=metadata.get('error'),
        )
    
    # END_METHOD__PARSE_LINE_BUILTIN
    
    # START_METHOD__CONVERT_PYTHON_ENTRY_TO_LOG_ENTRY
    # START_CONTRACT:
    # PURPOSE: Конвертация Python записи из src.monitor.integrations.log_parser в LogEntry.
    # INPUTS:
    # - py_entry: Any - Python запись LogEntry
    # OUTPUTS:
    # - LogEntry - конвертированная запись
    # KEYWORDS: [PATTERN(6): Adapter; CONCEPT(5): Conversion]
    # END_CONTRACT
    
    def _convert_python_entry_to_log_entry(self, py_entry: Any) -> LogEntry:
        """
        Конвертация Python записи в LogEntry.
        
        Args:
            py_entry: Python запись из модуля log_parser
            
        Returns:
            LogEntry объект
        """
        try:
            timestamp = datetime.fromtimestamp(py_entry.timestamp) if py_entry.timestamp else datetime.now()
            level = LEVEL_INFO
            
            if py_entry.error:
                level = LEVEL_ERROR
            elif "error" in py_entry.raw_line.lower():
                level = LEVEL_ERROR
            elif "warning" in py_entry.raw_line.lower():
                level = LEVEL_WARNING
            elif "debug" in py_entry.raw_line.lower():
                level = LEVEL_DEBUG
            
            metadata = {}
            if py_entry.iteration_count is not None:
                metadata['iteration_count'] = py_entry.iteration_count
            if py_entry.match_count is not None:
                metadata['match_count'] = py_entry.match_count
            if py_entry.wallet_count is not None:
                metadata['wallet_count'] = py_entry.wallet_count
            if py_entry.entropy_bits is not None:
                metadata['entropy_bits'] = py_entry.entropy_bits
            if py_entry.stage is not None:
                metadata['stage'] = py_entry.stage
            if py_entry.error is not None:
                metadata['error'] = py_entry.error
            
            return LogEntry(
                timestamp=timestamp,
                level=level,
                source="log_parser",
                message=py_entry.raw_line,
                metadata=metadata,
                raw_line=py_entry.raw_line,
                iteration_count=py_entry.iteration_count,
                match_count=py_entry.match_count,
                wallet_count=py_entry.wallet_count,
                entropy_bits=py_entry.entropy_bits,
                stage=py_entry.stage,
                error=py_entry.error,
            )
        except Exception as e:
            logger.error(f"[LogParser][_CONVERT_PYTHON_ENTRY][ExceptionCaught] Ошибка конвертации: {e} [FAIL]")
            return LogEntry(
                timestamp=datetime.now(),
                level=LEVEL_INFO,
                source="log_parser",
                message=str(py_entry) if py_entry else "",
                metadata={},
            )
    
    # END_METHOD__CONVERT_PYTHON_ENTRY_TO_LOG_ENTRY
    
    # START_METHOD_PARSE_FILE
    # START_CONTRACT:
    # PURPOSE: Полный парсинг лог-файла.
    # INPUTS:
    # - file_path: Optional[str] - путь к файлу (если отличается от указанного при инициализации)
    # OUTPUTS:
    # - List[LogEntry] - список распарсенных записей
    # SIDE_EFFECTS:
    # - Читает весь файл с диска
    # - Обновляет внутренний кэш записей
    # - Обновляет статистику
    # KEYWORDS: [DOMAIN(8): FileIO; CONCEPT(7): FullParse]
    # END_CONTRACT
    
    def parse_file(self, file_path: Optional[str] = None) -> List[LogEntry]:
        """
        Полный парсинг лог-файла.
        
        Args:
            file_path: путь к файлу (по умолчанию используется путь из конструктора)
            
        Returns:
            Список распарсенных записей
        """
        target_path = file_path or self._log_path
        logger.info(f"[LogParser][PARSE_FILE][START] Парсинг файла: {target_path}")
        
        start_time = time.time()
        entries = []
        
        if self._use_cpp and self._cpp_parser:
            # Использование C++ бэкенда
            try:
                # Если передан новый путь - обновляем парсер
                if file_path and file_path != self._log_path:
                    self._cpp_parser.set_log_file(file_path)
                
                cpp_entries = self._cpp_parser.parse_file()
                entries = [_convert_cpp_entry_to_log_entry(e) for e in cpp_entries]
                
                logger.info(f"[LogParser][PARSE_FILE][StepComplete] C++: спарсено записей: {len(entries)} [SUCCESS]")
            except Exception as e:
                logger.error(f"[LogParser][PARSE_FILE][ExceptionCaught] Ошибка C++ парсинга: {e} [FAIL]")
                # Fallback на Python
                entries = self._parse_file_python(target_path)
        else:
            # Использование Python бэкенда
            entries = self._parse_file_python(target_path)
        
        # Обновление кэша и статистики
        self._entries = deque(entries, maxlen=self._max_entries)
        self._statistics['total_entries_extracted'] = len(entries)
        self._statistics['total_lines_parsed'] = len(entries)
        
        # Подсчёт по уровням
        for entry in entries:
            self._statistics['entries_by_level'][entry.level] = self._statistics['entries_by_level'].get(entry.level, 0) + 1
            if entry.level == LEVEL_ERROR:
                self._statistics['errors_count'] += 1
        
        self._statistics['parse_time_seconds'] = time.time() - start_time
        self._statistics['last_parse_time'] = datetime.now().isoformat()
        
        logger.info(f"[LogParser][PARSE_FILE][StepComplete] Всего записей: {len(entries)}, время: {self._statistics['parse_time_seconds']:.3f}s [SUCCESS]")
        
        return entries
    
    # END_METHOD_PARSE_FILE
    
    # START_METHOD__PARSE_FILE_PYTHON
    # START_CONTRACT:
    # PURPOSE: Парсинг файла с использованием Python.
    # INPUTS:
    # - file_path: str - путь к файлу
    # OUTPUTS:
    # - List[LogEntry] - список записей
    # KEYWORDS: [PATTERN(6): Fallback; DOMAIN(7): FileIO]
    # END_CONTRACT
    
    def _parse_file_python(self, file_path: str) -> List[LogEntry]:
        """
        Парсинг файла с использованием Python.
        
        Args:
            file_path: путь к файлу
            
        Returns:
            Список записей
        """
        entries = []
        
        try:
            if self._py_parser:
                # Используем Python парсер из модуля
                py_entries = self._py_parser.parse_file()
                entries = [self._convert_python_entry_to_log_entry(e) for e in py_entries]
            else:
                # Встроенный парсер
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        entry = self._parse_line_builtin(line)
                        if entry:
                            entries.append(entry)
        except Exception as e:
            logger.error(f"[LogParser][_PARSE_FILE_PYTHON][ExceptionCaught] Ошибка Python парсинга: {e} [FAIL]")
        
        return entries
    
    # END_METHOD__PARSE_FILE_PYTHON
    
    # START_METHOD_PARSE_STREAM
    # START_CONTRACT:
    # PURPOSE: Парсинг потока данных (генератора или итератора строк).
    # INPUTS:
    # - stream: Iterator[str] - итератор строк
    # OUTPUTS:
    # - List[LogEntry] - список распарсенных записей
    # SIDE_EFFECTS:
    # - Обрабатывает каждую строку из потока
    # - Обновляет кэш и статистику
    # KEYWORDS: [DOMAIN(8): Streaming; CONCEPT(7): Iterator; TECH(6): Generator]
    # END_CONTRACT
    
    def parse_stream(self, stream: Iterator[str]) -> List[LogEntry]:
        """
        Парсинг потока данных (генератора или итератора строк).
        
        Args:
            stream: итератор строк (генератор, файл, список)
            
        Returns:
            Список распарсенных записей
        """
        logger.info(f"[LogParser][PARSE_STREAM][START] Парсинг потока данных")
        
        entries = []
        
        for line in stream:
            entry = self.parse_line(line)
            if entry:
                entries.append(entry)
        
        logger.info(f"[LogParser][PARSE_STREAM][StepComplete] Обработано строк: {len(entries)} [SUCCESS]")
        
        return entries
    
    # END_METHOD_PARSE_STREAM
    
    # START_METHOD_PARSE_NEW_LINES
    # START_CONTRACT:
    # PURPOSE: Парсинг только новых строк из лог-файла для real-time мониторинга.
    # INPUTS: Нет
    # OUTPUTS:
    # - List[LogEntry] - новые записи лога
    # SIDE_EFFECTS:
    # - Читает только новые строки из файла
    # - Обновляет позицию в файле
    # KEYWORDS: [DOMAIN(9): RealTime; CONCEPT(8): Incremental; TECH(7): Streaming]
    # END_CONTRACT
    
    def parse_new_lines(self) -> List[LogEntry]:
        """
        Парсинг только новых строк из лог-файла для real-time мониторинга.
        
        INPUTS: Нет
        
        OUTPUTS:
        - List[LogEntry] - новые записи лога
        
        SIDE_EFFECTS:
        - Читает только новые строки из файла
        - Обновляет позицию в файле
        """
        import os
        new_entries = []
        
        # START_BLOCK_CHECK_FILE_EXISTS: [Проверка существования файла]
        if not os.path.exists(self._log_path):
            return new_entries
        # END_BLOCK_CHECK_FILE_EXISTS
        
        try:
            file_size = os.path.getsize(self._log_path)
            
            # Если позиция больше размера файла - файл был ротирован
            if self._last_file_position > file_size:
                logger.info(f"[LogParser][PARSE_NEW_LINES][Info] Файл ротирован, сброс позиции")
                self._last_file_position = 0
            
            with open(self._log_path, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(self._last_file_position)
                
                for line in f:
                    entry = self.parse_line(line)
                    if entry:
                        new_entries.append(entry)
                        self._update_metrics(entry)
                        self._entries.append(entry)
                
                self._last_file_position = f.tell()
            
            self._last_parse_time = time.time()
            
            if new_entries:
                logger.debug(f"[LogParser][PARSE_NEW_LINES][StepComplete] Новых записей: {len(new_entries)}")
            
        except Exception as e:
            logger.error(f"[LogParser][PARSE_NEW_LINES][ExceptionCaught] Ошибка: {e}")
        
        return new_entries
    
    # END_METHOD_PARSE_NEW_LINES
    
    # START_METHOD_UPDATE_METRICS
    # START_CONTRACT:
    # PURPOSE: Обновление внутренних метрик из полученной записи.
    # INPUTS:
    # - entry: LogEntry - запись лога
    # OUTPUTS: Нет
    # SIDE_EFFECTS:
    # - Обновляет внутренние метрики
    # KEYWORDS: [CONCEPT(6): StateUpdate; DOMAIN(7): Metrics]
    # END_CONTRACT
    
    def _update_metrics(self, entry: LogEntry) -> None:
        """
        Обновление текущих метрик из записи.
        
        INPUTS:
        - entry: LogEntry - запись лога
        
        OUTPUTS: Нет
        
        SIDE_EFFECTS:
        - Обновляет внутренние метрики
        """
        if entry.iteration_count is not None:
            self._current_iteration = entry.iteration_count
        if entry.match_count is not None:
            self._current_match = entry.match_count
        if entry.wallet_count is not None:
            self._current_wallet = entry.wallet_count
        if entry.entropy_bits is not None:
            self._current_entropy = entry.entropy_bits
        if entry.stage is not None:
            self._current_stage = entry.stage
        
        if self._current_iteration > 0:
            self._is_monitoring = True
    
    # END_METHOD_UPDATE_METRICS
    
    # START_METHOD_GET_ENTRIES
    # START_CONTRACT:
    # PURPOSE: Получение всех распарсенных записей.
    # INPUTS: Нет
    # OUTPUTS:
    # - List[LogEntry] - копия списка записей
    # SIDE_EFFECTS: Нет
    # KEYWORDS: [PATTERN(7): Accessor; CONCEPT(6): Getter]
    # END_CONTRACT
    
    def get_entries(self) -> List[LogEntry]:
        """
        Получение всех распарсенных записей.
        
        Returns:
            Копия списка записей
        """
        logger.debug(f"[LogParser][GET_ENTRIES][Info] Записей в кэше: {len(self._entries)}")
        
        # Применяем фильтр если установлен
        if self._filter_func:
            return [e for e in self._entries if self._filter_func(e)]
        
        return list(self._entries)
    
    # END_METHOD_GET_ENTRIES
    
    # START_METHOD_GET_ENTRIES_BY_LEVEL
    # START_CONTRACT:
    # PURPOSE: Получение записей по уровню лога.
    # INPUTS:
    # - level: str - уровень лога (DEBUG, INFO, WARNING, ERROR)
    # OUTPUTS:
    # - List[LogEntry] - отфильтрованный список записей
    # SIDE_EFFECTS: Нет
    # KEYWORDS: [PATTERN(7): Filter; DOMAIN(7): LogLevel; CONCEPT(6): Selection]
    # END_CONTRACT
    
    def get_entries_by_level(self, level: str) -> List[LogEntry]:
        """
        Получение записей по уровню лога.
        
        Args:
            level: уровень лога (DEBUG, INFO, WARNING, ERROR)
            
        Returns:
            Список записей указанного уровня
        """
        logger.debug(f"[LogParser][GET_ENTRIES_BY_LEVEL][Params] level={level}")
        
        # Нормализация уровня
        level_upper = level.upper()
        
        # Проверяем, является ли уровень допустимым
        if level_upper not in LOG_LEVELS:
            logger.warning(f"[LogParser][GET_ENTRIES_BY_LEVEL][ConditionCheck] Неизвестный уровень: {level} [FAIL]")
            return []
        
        # Фильтрация записей
        filtered = [e for e in self._entries if e.level == level_upper]
        
        logger.debug(f"[LogParser][GET_ENTRIES_BY_LEVEL][ReturnData] Найдено записей: {len(filtered)} [VALUE]")
        
        return filtered
    
    # END_METHOD_GET_ENTRIES_BY_LEVEL
    
    # START_METHOD_GET_ENTRIES_BY_PATTERN
    # START_CONTRACT:
    # PURPOSE: Получение записей по регулярному выражению.
    # INPUTS:
    # - pattern: str - регулярное выражение
    # OUTPUTS:
    # - List[LogEntry] - список匹配的 записей
    # SIDE_EFFECTS: Нет
    # KEYWORDS: [PATTERN(7): Search; CONCEPT(7): Regex; DOMAIN(6): Filter]
    # END_CONTRACT
    
    def get_entries_by_pattern(self, pattern: str) -> List[LogEntry]:
        """
        Получение записей по регулярному выражению.
        
        Args:
            pattern: регулярное выражение для поиска
            
        Returns:
            Список записей, соответствующих паттерну
        """
        logger.debug(f"[LogParser][GET_ENTRIES_BY_PATTERN][Params] pattern={pattern}")
        
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            filtered = []
            
            for entry in self._entries:
                # Проверяем по message и raw_line
                if regex.search(entry.message) or regex.search(entry.raw_line):
                    filtered.append(entry)
            
            logger.debug(f"[LogParser][GET_ENTRIES_BY_PATTERN][ReturnData] Найдено записей: {len(filtered)} [VALUE]")
            return filtered
            
        except re.error as e:
            logger.error(f"[LogParser][GET_ENTRIES_BY_PATTERN][ExceptionCaught] Ошибка regex: {e} [FAIL]")
            return []
    
    # END_METHOD_GET_ENTRIES_BY_PATTERN
    
    # START_METHOD_CLEAR
    # START_CONTRACT:
    # PURPOSE: Очистка всех записей и сброс статистики.
    # INPUTS: Нет
    # OUTPUTS: Нет
    # SIDE_EFFECTS:
    # - Очищает кэш записей
    # - Сбрасывает статистику
    # KEYWORDS: [CONCEPT(6): Cleanup; TECH(5): Reset]
    # END_CONTRACT
    
    def clear(self) -> None:
        """Очистка всех записей и сброс статистики."""
        logger.info(f"[LogParser][CLEAR][START] Очистка всех записей")
        
        self._entries.clear()
        self._statistics = {
            'total_lines_parsed': 0,
            'total_entries_extracted': 0,
            'parse_time_seconds': 0.0,
            'entries_by_level': {level: 0 for level in LOG_LEVELS},
            'errors_count': 0,
            'last_parse_time': None,
        }
        
        logger.info(f"[LogParser][CLEAR][StepComplete] Очистка завершена [SUCCESS]")
    
    # END_METHOD_CLEAR
    
    # START_METHOD_SET_FILTER
    # START_CONTRACT:
    # PURPOSE: Установка функции фильтра записей.
    # INPUTS:
    # - filter_func: Callable[[LogEntry], bool] - функция фильтрации
    # OUTPUTS: Нет
    # SIDE_EFFECTS:
    # - Устанавливает функцию для фильтрации записей
    # KEYWORDS: [PATTERN(7): Filter; CONCEPT(6): Callback; TECH(5): Setter]
    # END_CONTRACT
    
    def set_filter(self, filter_func: Callable[[LogEntry], bool]) -> None:
        """
        Установка функции фильтра записей.
        
        Args:
            filter_func: функция, принимающая LogEntry и возвращающая bool
        """
        logger.info(f"[LogParser][SET_FILTER][START] Установка фильтра")
        
        if filter_func is None:
            self._filter_func = None
            logger.info(f"[LogParser][SET_FILTER][StepComplete] Фильтр сброшен [SUCCESS]")
        else:
            self._filter_func = filter_func
            logger.info(f"[LogParser][SET_FILTER][StepComplete] Фильтр установлен [SUCCESS]")
    
    # END_METHOD_SET_FILTER
    
    # START_METHOD_GET_STATISTICS
    # START_CONTRACT:
    # PURPOSE: Получение статистики парсинга.
    # INPUTS: Нет
    # OUTPUTS:
    # - Dict[str, Any] - словарь со статистикой
    # SIDE_EFFECTS: Нет
    # KEYWORDS: [CONCEPT(7): Statistics; TECH(6): Aggregation; DOMAIN(6): Metrics]
    # END_CONTRACT
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики парсинга.
        
        Returns:
            Словарь со статистикой:
            - total_lines_parsed: общее количество обработанных строк
            - total_entries_extracted: количество извлечённых записей
            - parse_time_seconds: время парсинга в секундах
            - entries_by_level: распределение по уровням
            - errors_count: количество ошибок
            - last_parse_time: время последнего парсинга
            - entry_count: текущее количество записей в кэше
            - using_cpp: используется ли C++ бэкенд
            - cpp_available: доступен ли C++ модуль
        """
        stats = self._statistics.copy()
        stats['entry_count'] = len(self._entries)
        stats['using_cpp'] = self._use_cpp
        stats['cpp_available'] = CPP_AVAILABLE
        
        logger.debug(f"[LogParser][GET_STATISTICS][ReturnData] Статистика: {stats} [VALUE]")
        
        return stats
    
    # END_METHOD_GET_STATISTICS
    
    # START_METHOD_GET_CURRENT_METRICS
    # START_CONTRACT:
    # PURPOSE: Получение текущих метрик (для совместимости с Python API).
    # INPUTS: Нет
    # OUTPUTS:
    # - Dict[str, Any] - словарь с метриками
    # KEYWORDS: [PATTERN(7): Accessor; CONCEPT(6): Compatibility]
    # END_CONTRACT
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Получение текущих метрик (для совместимости с Python API).
        
        Returns:
            Словарь с метриками
        """
        # Ищем последнюю запись с метриками (итерация/кошелёк/матч)
        # Потому что последние записи в логе могут быть SHUTDOWN/STATS без метрик
        if self._entries:
            for entry in reversed(self._entries):
                if entry.iteration_count is not None or entry.wallet_count is not None or entry.match_count is not None:
                    return {
                        'iteration_count': entry.iteration_count or self._current_iteration or 0,
                        'match_count': entry.match_count or self._current_match or 0,
                        'wallet_count': entry.wallet_count or self._current_wallet or 0,
                        'entropy_bits': entry.entropy_bits if entry.entropy_bits is not None else self._current_entropy or 0.0,
                        'stage': entry.stage or self._current_stage or 'idle',
                        'is_monitoring': len(self._entries) > 0,
                        'timestamp': entry.timestamp.timestamp() if entry.timestamp else time.time(),
                    }
            # Если есть хоть какие-то записи, но без метрик - используем _current_* переменные
            return {
                'iteration_count': self._current_iteration,
                'match_count': self._current_match,
                'wallet_count': self._current_wallet,
                'entropy_bits': self._current_entropy,
                'stage': self._current_stage,
                'is_monitoring': self._is_monitoring,
                'timestamp': time.time(),
            }
        
        return {
            'iteration_count': 0,
            'match_count': 0,
            'wallet_count': 0,
            'entropy_bits': 0.0,
            'stage': 'idle',
            'is_monitoring': False,
            'timestamp': time.time(),
        }
    
    # END_METHOD_GET_CURRENT_METRICS
    
    # START_METHOD_RESET
    # START_CONTRACT:
    # PURPOSE: Сброс состояния парсера (для совместимости с Python API).
    # INPUTS: Нет
    # OUTPUTS: Нет
    # KEYWORDS: [CONCEPT(5): Reset; TECH(5): Cleanup]
    # END_CONTRACT
    
    def reset(self) -> None:
        """Сброс состояния парсера (для совместимости с Python API)."""
        self.clear()
        logger.info(f"[LogParser][RESET][StepComplete] Парсер сброшен [SUCCESS]")
    
    # END_METHOD_RESET
    
    # START_METHOD_SET_LOG_FILE
    # START_CONTRACT:
    # PURPOSE: Установка нового пути к лог-файлу (для совместимости с Python API).
    # INPUTS:
    # - log_file_path: str - путь к файлу
    # OUTPUTS:
    # - bool - True если файл существует
    # KEYWORDS: [CONCEPT(5): Setter; DOMAIN(6): Config]
    # END_CONTRACT
    
    def set_log_file(self, log_file_path: str) -> bool:
        """
        Установка нового пути к лог-файлу (для совместимости с Python API).
        
        Args:
            log_file_path: путь к файлу
            
        Returns:
            True если путь установлен
        """
        logger.info(f"[LogParser][SET_LOG_FILE][Params] path={log_file_path}")
        
        self._log_path = log_file_path
        
        if self._use_cpp and self._cpp_parser:
            try:
                return self._cpp_parser.set_log_file(log_file_path)
            except Exception as e:
                logger.error(f"[LogParser][SET_LOG_FILE][ExceptionCaught] Ошибка: {e} [FAIL]")
                return False
        
        return True
    
    # END_METHOD_SET_LOG_FILE
    
    # START_METHOD_GET_FILE_INFO
    # START_CONTRACT:
    # PURPOSE: Получение информации о файле лога (для совместимости с Python API).
    # INPUTS: Нет
    # OUTPUTS:
    # - Dict[str, Any] - информация о файле
    # KEYWORDS: [CONCEPT(6): Accessor; DOMAIN(7): FileInfo]
    # END_CONTRACT
    
    def get_file_info(self) -> Dict[str, Any]:
        """
        Получение информации о файле лога (для совместимости с Python API).
        
        Returns:
            Информация о файле
        """
        import os
        
        if not os.path.exists(self._log_path):
            return {"exists": False}
        
        stat = os.stat(self._log_path)
        
        return {
            "exists": True,
            "path": self._log_path,
            "size_bytes": stat.st_size,
            "size_mb": stat.st_size / (1024 * 1024),
            "modified_time": stat.st_mtime,
            "cached_entries": len(self._entries),
            "last_parse_time": self._statistics.get('last_parse_time'),
        }
    
    # END_METHOD_GET_FILE_INFO
    
    # START_METHOD_GET_ITERATION_RATE
    # START_CONTRACT:
    # PURPOSE: Вычисление скорости итераций (для совместимости с Python API).
    # INPUTS:
    # - window_seconds: int - временное окно в секундах
    # OUTPUTS:
    # - float - скорость итераций
    # KEYWORDS: [CONCEPT(7): RateCalculation; TECH(6): TimeSeries]
    # END_CONTRACT
    
    def get_iteration_rate(self, window_seconds: int = 60) -> float:
        """
        Вычисление скорости итераций (для совместимости с Python API).
        
        Args:
            window_seconds: временное окно в секундах
            
        Returns:
            Скорость итераций в секунду
        """
        if len(self._entries) < 2:
            return 0.0
        
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # Фильтруем записи в окне
        relevant_entries = [
            e for e in self._entries
            if e.timestamp.timestamp() >= window_start and e.iteration_count is not None
        ]
        
        if len(relevant_entries) < 2:
            return 0.0
        
        first = relevant_entries[0]
        last = relevant_entries[-1]
        
        time_diff = last.timestamp.timestamp() - first.timestamp.timestamp()
        if time_diff <= 0:
            return 0.0
        
        iter_diff = (last.iteration_count or 0) - (first.iteration_count or 0)
        return max(0, iter_diff / time_diff)
    
    # END_METHOD_GET_ITERATION_RATE
    
    # START_METHOD_GET_ERRORS
    # START_CONTRACT:
    # PURPOSE: Получение всех ошибок из кэша (для совместимости с Python API).
    # INPUTS: Нет
    # OUTPUTS:
    # - List[Dict[str, Any]] - список ошибок
    # KEYWORDS: [DOMAIN(7): ErrorHandling; CONCEPT(6): Extraction]
    # END_CONTRACT
    
    def get_errors(self) -> List[Dict[str, Any]]:
        """
        Получение всех ошибок из кэша (для совместимости с Python API).
        
        Returns:
            Список ошибок с timestamp
        """
        errors = []
        
        for entry in self._entries:
            if entry.error or entry.level == LEVEL_ERROR:
                errors.append({
                    "timestamp": entry.timestamp.timestamp() if entry.timestamp else None,
                    "error": entry.error or entry.message,
                })
        
        return errors
    
    # END_METHOD_GET_ERRORS
    
    # START_METHOD_GET_STAGES
    # START_CONTRACT:
    # PURPOSE: Получение статистики по стадиям (для совместимости с Python API).
    # INPUTS: Нет
    # OUTPUTS:
    # - Dict[str, int] - словарь стадия: количество
    # KEYWORDS: [DOMAIN(6): Statistics; CONCEPT(5): Aggregation]
    # END_CONTRACT
    
    def get_stages(self) -> Dict[str, int]:
        """
        Получение статистики по стадиям (для совместимости с Python API).
        
        Returns:
            Словарь стадия: количество
        """
        stages = {}
        
        for entry in self._entries:
            if entry.stage:
                stages[entry.stage] = stages.get(entry.stage, 0) + 1
        
        return stages
    
    # END_METHOD_GET_STAGES
    
    # START_METHOD_GET_PROGRESS
    # START_CONTRACT:
    # PURPOSE: Получение последнего значения прогресса (для совместимости с Python API).
    # INPUTS: Нет
    # OUTPUTS:
    # - Optional[float] - прогресс в процентах
    # KEYWORDS: [DOMAIN(7): Progress; CONCEPT(6): Extraction]
    # END_CONTRACT
    
    def get_progress(self) -> Optional[float]:
        """
        Получение последнего значения прогресса (для совместимости с Python API).
        
        Returns:
            Прогресс в процентах или None
        """
        # Ищем паттерн прогресса в последних записях
        for entry in reversed(self._entries):
            match = re.search(r"Progress[:\s]+(\d+\.?\d*)%", entry.raw_line, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, IndexError):
                    pass
        
        return None
    
    # END_METHOD_GET_PROGRESS
    
    # START_METHOD_IS_MONITORING
    # START_CONTRACT:
    # PURPOSE: Проверка состояния мониторинга (для совместимости с Python API).
    # INPUTS: Нет
    # OUTPUTS:
    # - bool - True если идёт мониторинг
    # KEYWORDS: [CONCEPT(5): StateCheck; DOMAIN(6): Status]
    # END_CONTRACT
    
    def is_monitoring(self) -> bool:
        """
        Проверка состояния мониторинга (для совместимости с Python API).
        
        Returns:
            True если есть записи
        """
        return len(self._entries) > 0
    
    # END_METHOD_IS_MONITORING
    
    # START_METHOD_SEARCH_PATTERNS
    # START_CONTRACT:
    # PURPOSE: Поиск записей по регулярному выражению (для совместимости с Python API).
    # INPUTS:
    # - pattern: str - регулярное выражение
    # OUTPUTS:
    # - List[LogEntry] - найденные записи
    # KEYWORDS: [DOMAIN(7): Search; CONCEPT(7): Regex]
    # END_CONTRACT
    
    def search_patterns(self, pattern: str) -> List[LogEntry]:
        """
        Поиск записей по регулярному выражению (для совместимости с Python API).
        
        Args:
            pattern: регулярное выражение
            
        Returns:
            Найденные записи
        """
        return self.get_entries_by_pattern(pattern)
    
    # END_METHOD_SEARCH_PATTERNS
    
    # START_METHOD_GET_CACHED_ENTRIES
    # START_CONTRACT:
    # PURPOSE: Получение кэшированных записей (для совместимости с Python API).
    # INPUTS: Нет
    # OUTPUTS:
    # - List[LogEntry] - список записей
    # KEYWORDS: [CONCEPT(6): Cache; DOMAIN(7): Storage]
    # END_CONTRACT
    
    def get_cached_entries(self) -> List[LogEntry]:
        """
        Получение кэшированных записей (для совместимости с Python API).
        
        Returns:
            Список записей
        """
        return list(self._entries)
    
    # END_METHOD_GET_CACHED_ENTRIES
    
    # START_METHOD_PARSE_MATCH_EVENT
    # START_CONTRACT:
    # PURPOSE: Парсинг события совпадения (для совместимости с Python API).
    # INPUTS:
    # - log_line: str - строка лога
    # OUTPUTS:
    # - Optional[Dict[str, Any]] - данные о совпадении
    # KEYWORDS: [DOMAIN(9): MatchEvent; CONCEPT(8): Parsing; TECH(7): Regex]
    # END_CONTRACT
    
    def parse_match_event(self, log_line: str) -> Optional[Dict[str, Any]]:
        """
        Парсинг события совпадения (для совместимости с Python API).
        
        Args:
            log_line: строка лога
            
        Returns:
            Данные о совпадении или None
        """
        # Проверяем различные паттерны совпадений
        has_match = False
        
        # Паттерн 1: MATCH FOUND address
        if re.search(r"(?:MATCH|FOUND|FOUND_MATCH)[s]?[:\s]+\"?([1A-HJ-NP-Za-km-z]{25,34})\"?", log_line, re.IGNORECASE):
            has_match = True
        # Паттерн 2: Address matched
        elif re.search(r"(?:Address|address|ADDRESS)[s]?[:=]\s*\"?([1A-HJ-NP-Za-km-z]{25,34})\"?", log_line, re.IGNORECASE):
            has_match = True
        # Паттерн 3: Прямое упоминание MATCH
        elif re.search(r"MATCH\s+(?:FOUND|DETECTED)", log_line, re.IGNORECASE):
            has_match = True
        
        if not has_match:
            return None
        
        # Извлечение данных
        result: Dict[str, Any] = {
            "timestamp": time.time(),
            "address": None,
            "wallet_name": None,
            "list_name": None,
            "iteration": self.get_current_metrics().get('iteration_count', 0),
            "raw_line": log_line.strip(),
        }
        
        # Извлечение адреса
        match = re.search(r"(?:MATCH|FOUND|FOUND_MATCH)[s]?[:\s]+\"?([1A-HJ-NP-Za-km-z]{25,34})\"?", log_line, re.IGNORECASE)
        if not match:
            match = re.search(r"(?:Address|address|ADDRESS)[s]?[:=]\s*\"?([1A-HJ-NP-Za-km-z]{25,34})\"?", log_line, re.IGNORECASE)
        
        if match:
            result["address"] = match.group(1)
        
        # Извлечение имени кошелька
        wallet_match = re.search(r"(?:Wallet|wallet|WALLET)[s]?[:=]\s*(\S+)", log_line, re.IGNORECASE)
        if wallet_match:
            result["wallet_name"] = wallet_match.group(1)
        
        # Извлечение имени списка
        list_match = re.search(r"(?:LIST|List|list)[s]?[:=]\s*(\S+)", log_line, re.IGNORECASE)
        if list_match:
            result["list_name"] = list_match.group(1)
        
        # Извлечение timestamp
        ts_match = re.search(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", log_line)
        if ts_match:
            try:
                result["timestamp"] = datetime.strptime(ts_match.group(1), "%Y-%m-%d %H:%M:%S").timestamp()
            except ValueError:
                pass
        
        return result
    
    # END_METHOD_PARSE_MATCH_EVENT


# END_CLASS_LOG_PARSER


# START_FUNCTION_CREATE_LOG_PARSER
# START_CONTRACT:
# PURPOSE: Фабричная функция для создания парсера логов.
# INPUTS:
# - log_path: Optional[str] - путь к лог-файлу
# - max_entries: int - максимальное количество записей
# OUTPUTS:
# - LogParser - созданный парсер
# KEYWORDS: [PATTERN(7): Factory; CONCEPT(6): FactoryFunction]
# END_CONTRACT

def create_log_parser(log_path: Optional[str] = None, max_entries: int = DEFAULT_MAX_ENTRIES) -> LogParser:
    """
    Фабричная функция для создания парсера логов.
    
    Args:
        log_path: путь к лог-файлу (по умолчанию "logs/infinite_loop.log")
        max_entries: максимальное количество записей в кэше
        
    Returns:
        Экземпляр LogParser
    """
    logger.info(f"[create_log_parser][START] Создание парсера с path={log_path}, max_entries={max_entries}")
    parser = LogParser(log_path=log_path, max_entries=max_entries)
    logger.info(f"[create_log_parser][StepComplete] Парсер создан, C++: {parser.using_cpp} [SUCCESS]")
    return parser

# END_FUNCTION_CREATE_LOG_PARSER


# START_BLOCK_EXPORT: [Экспорт публичного API]
__all__ = [
    'LogParser',
    'LogEntry',
    'create_log_parser',
    # Константы уровней
    'LEVEL_DEBUG',
    'LEVEL_INFO',
    'LEVEL_WARNING',
    'LEVEL_ERROR',
    'LEVEL_CRITICAL',
    'LOG_LEVELS',
    # Флаги
    'CPP_AVAILABLE',
]
# END_BLOCK_EXPORT

logger.info(f"[InitModule][log_parser_wrapper][FINALIZE] Модуль полностью загружен. C++ доступен: {CPP_AVAILABLE} [SUCCESS]")
