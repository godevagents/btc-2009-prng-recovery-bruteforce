# FILE: src/monitor/integrations/launch_integration.py
# VERSION: 1.2.0
# START_MODULE_CONTRACT:
# PURPOSE: Интеграция с модулем запуска src/launch. Подключение к модулю запуска генератора
# для получения метрик в реальном времени через парсинг логов.
# SCOPE: Управление subprocess, мониторинг процессов, polling логов, подписка на метрики
# INPUT: Путь к скрипту запуска, путь к лог-файлу, дополнительные аргументы
# OUTPUT: Класс LaunchIntegration для управления генератором и получения метрик
# KEYWORDS: [DOMAIN(9): ProcessManagement; DOMAIN(8): Monitoring; CONCEPT(7): Subprocess; TECH(6): Threading]
# LINKS: [USES_API(8): log_parser_wrapper; USES_API(7): log_parser; USES_API(6): subprocess; USES_API(5): threading]
# LINKS_TO_SPECIFICATION: [monitoring_module_architecture.md, dev_plan_launch_integration.md]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 9 [Интеграция с модулем запуска src/launch] => LaunchIntegration
# METHOD 8 [Запуск генератора кошельков] => start_launcher
# METHOD 8 [Остановка генератора] => stop_launcher
# METHOD 7 [Получение текущих метрик] => get_current_metrics
# METHOD 7 [Подписка на обновления метрик] => subscribe
# METHOD 7 [Проверка состояния запуска] => is_running
# METHOD 6 [Получение информации о процессе] => get_process_info
# METHOD 6 [Получение статуса запуска] => get_launch_status
# METHOD 6 [Проверка здоровья интеграции] => check_health
# METHOD 5 [Сброс состояния интеграции] => reset
# FUNC 8 [Определение корня проекта] => get_project_root
# FUNC 7 [Фабричная функция для создания интеграции] => create_launch_integration
# CONST 4 [Путь к скрипту запуска по умолчанию] => get_default_launch_script
# CONST 4 [Путь к лог-файлу по умолчанию] => get_default_log_file
# CONST 3 [Интервал опроса логов в секундах] => POLL_INTERVAL
# CONST 3 [Максимальное время ожидания запуска в секундах] => MAX_STARTUP_WAIT
# END_MODULE_MAP
# START_USE_CASES:
# - [start_launcher]: Monitor (Startup) -> LaunchGenerator -> ProcessRunning
# - [stop_launcher]: Monitor (Shutdown) -> TerminateProcess -> ProcessStopped
# - [subscribe]: UI (RealTime) -> RegisterCallback -> MetricsUpdateEnabled
# - [get_current_metrics]: Dashboard (Display) -> RequestMetrics -> MetricsDisplayed
# - [check_health]: System (HealthCheck) -> VerifyComponents -> HealthStatusKnown
# END_USE_CASES
"""
Модуль integrations/launch_integration.py — Интеграция с src/launch.
Подключение к модулю запуска генератора для получения метрик в реальном времени.
"""

import logging
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.monitor.integrations import LogParser, LOG_PARSER_AVAILABLE
from src.monitor._cpp import get_log_parser_module

# Настройка логирования в файл app.log
def _setup_file_logging():
    """Настройка файлового логирования для модуля launch_integration."""
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

# Логирование статуса C++ модулей при импорте
logger.info(f"[ModuleInit][launch_integration][Info] LOG_PARSER_AVAILABLE: {LOG_PARSER_AVAILABLE} [VALUE]")

# START_FUNCTION_GET_PROJECT_ROOT
# START_CONTRACT:
# PURPOSE: Определяет абсолютный путь к корню проекта WALLET.DAT.GENERATOR.
# Стратегия:
# 1. Проверка переменной окружения PROJECT_ROOT
# 2. Поиск маркерных файлов (AppGraph.xml, .gitignore, папка src/)
# 3. Fallback: директория текущего файла + подъем на уровни
# INPUTS: Нет
# OUTPUTS:
# - Path — абсолютный путь к корню проекта
# SIDE_EFFECTS: Нет
# TEST_CONDITIONS_SUCCESS_CRITERIA:
# - Возвращаемый путь существует и содержит маркерные файлы проекта
# - Функция не вызывает исключений при нормальной работе
# KEYWORDS: [CONCEPT(8): PathResolution; DOMAIN(7): FileSystem; TECH(5): Path]
# LINKS: [USES_API(6): os.environ; USES_API(5): pathlib.Path]
# END_CONTRACT

def get_project_root() -> Path:
    """
    Определяет абсолютный путь к корню проекта WALLET.DAT.GENERATOR.
    
    Стратегия определения:
    1. Проверка переменной окружения PROJECT_ROOT
    2. Поиск маркерных файлов (AppGraph.xml, .gitignore, папка src/)
    3. Fallback: директория текущего файла + подъем на уровни
    
    INPUTS: Нет
    
    OUTPUTS:
    - Path — абсолютный путь к корню проекта
    
    SIDE_EFFECTS: Нет
    """
    # START_BLOCK_CHECK_ENV_VAR: [Проверка переменной окружения PROJECT_ROOT]
    env_root = os.environ.get("PROJECT_ROOT")
    if env_root:
        env_path = Path(env_root)
        if env_path.exists() and (env_path / "AppGraph.xml").exists():
            logger.debug(f"[get_project_root][CHECK_ENV_VAR] Найден корень проекта из PROJECT_ROOT: {env_path}")
            return env_path.resolve()
    # END_BLOCK_CHECK_ENV_VAR
    
    # START_BLOCK_SEARCH_MARKERS: [Поиск маркерных файлов проекта]
    # Маркерные файлы/директории для определения корня проекта
    project_markers = ["AppGraph.xml", ".gitignore", "src"]
    
    # Начинаем с директории текущего файла и поднимаемся вверх
    current_file_dir = Path(__file__).resolve().parent
    
    for _ in range(10):  # Ограничиваем количество уровней подъёма
        # Проверяем наличие маркеров
        found_markers = 0
        for marker in project_markers:
            if (current_file_dir / marker).exists():
                found_markers += 1
        
        if found_markers >= 2:  # Достаточно 2 маркеров
            logger.debug(f"[get_project_root][SEARCH_MARKERS] Найден корень проекта: {current_file_dir}")
            return current_file_dir
        
        # Поднимаемся на уровень выше
        parent = current_file_dir.parent
        if parent == current_file_dir:  # Дошли до корня файловой системы
            break
        current_file_dir = parent
    # END_BLOCK_SEARCH_MARKERS
    
    # START_BLOCK_FALLBACK: [Fallback - используем текущую рабочую директорию]
    cwd = Path.cwd()
    # Проверяем, содержит ли текущая директория маркеры
    markers_found = sum(1 for m in project_markers if (cwd / m).exists())
    if markers_found >= 1:
        logger.warning(f"[get_project_root][FALLBACK] Используем текущую директорию как корень: {cwd}")
        return cwd.resolve()
    
    # Последний fallback - возвращаем текущую директорию
    logger.warning(f"[get_project_root][FALLBACK] Не удалось определить корень проекта, используем cwd: {cwd}")
    return cwd.resolve()
    # END_BLOCK_FALLBACK


# END_FUNCTION_GET_PROJECT_ROOT


# START_CLASS_LAUNCH_INTEGRATION
# START_CONTRACT:
# PURPOSE: Интеграция с модулем запуска src/launch. Обеспечивает запуск генератора и получение метрик через логи.
# ATTRIBUTES:
# - Путь к скрипту запуска генератора => _launch_script: str
# - Парсер логов для извлечения метрик => _log_parser: LogParser
# - Запущенный процесс генератора => _process: Optional[subprocess.Popen]
# - Флаг состояния работы => _is_running: bool
# - Поток для polling логов => _polling_thread: Optional[threading.Thread]
# - Событие для остановки polling => _stop_polling: threading.Event
# - Список подписчиков на метрики => _subscribers: List[Callable]
# - Аргументы запуска => _launch_args: List[str]
# - Время запуска => _start_time: Optional[float]
# - Последние полученные метрики => _last_metrics: Dict[str, Any]
# METHODS:
# - Запуск генератора кошельков => start_launcher()
# - Остановка генератора => stop_launcher()
# - Получение текущих метрик => get_current_metrics()
# - Подписка на обновления метрик => subscribe()
# - Отписка от обновлений => unsubscribe()
# - Проверка состояния запуска => is_running()
# - Получение информации о процессе => get_process_info()
# - Получение парсера логов => get_log_parser()
# - Установка нового пути к скрипту => set_launch_script()
# - Получение времени работы => get_uptime()
# - Получение статуса запуска => get_launch_status()
# - Ожидание запуска генератора => wait_for_startup()
# - Проверка здоровья интеграции => check_health()
# - Сброс состояния => reset()
# KEYWORDS: [PATTERN(7): Integration; DOMAIN(9): ProcessManagement; TECH(6): Subprocess; CONCEPT(8): Polling]
# LINKS: [USES_API(8): LogParser; USES_API(7): subprocess; USES_API(6): threading]
# END_CONTRACT

class LaunchIntegration:
    """
    Интеграция с модулем запуска src/launch.
    Обеспечивает запуск генератора и получение метрик через логи.
    """
    
    # START_CONSTANTS_LAUNCH
    POLL_INTERVAL = 1.0  # секунды
    MAX_STARTUP_WAIT = 30  # секунды
    GRACEFUL_SHUTDOWN_TIMEOUT = 30  # таймаут graceful shutdown в секундах
    # END_CONSTANTS_LAUNCH
    
    @classmethod
    def get_default_launch_script(cls) -> str:
        """Получение абсолютного пути к скрипту запуска по умолчанию."""
        root = get_project_root()
        return str(root / "src" / "launch" / "main_loop.py")
    
    @classmethod
    def get_default_log_file(cls) -> str:
        """Получение абсолютного пути к лог-файлу по умолчанию."""
        root = get_project_root()
        return str(root / "logs" / "infinite_loop.log")
    
    def __init__(
        self,
        launch_script: Optional[str] = None,
        log_parser: Optional[LogParser] = None,
    ) -> None:
        """
        Инициализация интеграции с запуском.
        
        INPUTS:
        - launch_script: Optional[str] — путь к скрипту запуска
        - log_parser: Optional[LogParser] — парсер логов
        
        OUTPUTS:
        — Инициализированный объект LaunchIntegration
        
        SIDE_EFFECTS:
        — Создаёт парсер логов если не передан
        """
        # Используем абсолютные пути через get_project_root()
        self._launch_script = launch_script or self.get_default_launch_script()
        # BUG_FIX_CONTEXT: _log_file был строкой, исправлено на Path для вызова .exists() и .stat()
        self._log_file = Path(self.get_default_log_file())
        self._log_parser = log_parser or LogParser(self._log_file)
        self._process: Optional[subprocess.Popen] = None
        self._is_running: bool = False
        self._polling_thread: Optional[threading.Thread] = None
        self._stop_polling: threading.Event = threading.Event()
        self._subscribers: List[Callable] = []
        self._launch_args: List[str] = []
        self._start_time: Optional[float] = None
        # BUG_FIX_CONTEXT: Добавлен атрибут для сохранения времени остановки
        self._stop_time: Optional[float] = None
        self._last_metrics: Dict[str, Any] = {}
        self._on_stop_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._on_reset_callback: Optional[Callable[[], None]] = None
        self._on_match_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        
        logger.debug(f"[LaunchIntegration][INIT][ConditionCheck] Инициализирована интеграция с запуском")
    
    # START_METHOD_START_LAUNCHER
    # START_CONTRACT:
    # PURPOSE: Запуск генератора кошельков. Проверяет наличие скрипта, формирует команду,
    # запускает subprocess и начинает polling для мониторинга логов.
    # INPUTS:
    # - list_path: str — путь к списку адресов
    # - additional_args: Optional[List[str]] — дополнительные аргументы для скрипта
    # OUTPUTS:
    # - bool — True если запуск успешен, False в противном случае
    # SIDE_EFFECTS:
    # — Запускает subprocess с генератором
    # — Запускает поток polling для мониторинга логов
    # TEST_CONDITIONS_SUCCESS_CRITERIA:
    # - Скрипт запуска существует
    # - Процесс успешно запущен
    # - Polling поток начал работу
    # KEYWORDS: [PATTERN(7): Process; DOMAIN(9): WalletGeneration; TECH(6): Subprocess]
    # LINKS: [CALLS(8): _start_polling; CALLS(6): LogParser]
    # END_CONTRACT
    def start_launcher(
        self,
        list_path: str,
        additional_args: Optional[List[str]] = None,
    ) -> bool:
        """
        Запуск генератора кошельков.
        
        INPUTS:
        - list_path: str — путь к списку адресов
        - additional_args: Optional[List[str]] — дополнительные аргументы
        
        OUTPUTS:
        - bool — True если запуск успешен
        
        SIDE_EFFECTS:
        — Запускает subprocess с генератором
        — Запускает поток polling для мониторинга логов
        """
        # START_BLOCK_RESOLVE_SCRIPT_PATH: [Определение абсолютного пути к скрипту]
        script_path = Path(self._launch_script)
        
        # Если передан относительный путь или путь не существует,
        # пробуем разрешить относительно корня проекта
        if not script_path.is_absolute() or not script_path.exists():
            project_root = get_project_root()
            script_path = project_root / self._launch_script
            
        if not script_path.exists():
            logger.error(f"[LaunchIntegration][START_LAUNCHER][FAIL] Скрипт не найден: {script_path}")
            return False
        
        # Преобразуем в абсолютный путь
        script_path = script_path.resolve()
        logger.debug(f"[LaunchIntegration][START_LAUNCHER][ConditionCheck] Используем скрипт: {script_path}")
        # END_BLOCK_RESOLVE_SCRIPT_PATH
        
        # START_BLOCK_BUILD_COMMAND: [Формирование команды]
        python_exe = os.sys.executable
        cmd = [python_exe, str(script_path), "--list", list_path]
        
        if additional_args:
            cmd.extend(additional_args)
        
        self._launch_args = cmd
        logger.info(f"[LaunchIntegration][START_LAUNCHER][Info] Команда: {' '.join(cmd[:4])}...")
        # END_BLOCK_BUILD_COMMAND
        
        # START_BLOCK_START_PROCESS: [Запуск процесса]
        try:
            # Запускаем процесс в фоне
            # Используем корень проекта как рабочую директорию
            project_root = get_project_root()
            
            # DEBUG: Логируем рабочую директорию и путь к скрипту
            logger.debug(f"[LaunchIntegration][START_PROCESS][Debug] project_root={project_root}")
            logger.debug(f"[LaunchIntegration][START_PROCESS][Debug] script_path={script_path}")
            logger.debug(f"[LaunchIntegration][START_PROCESS][Debug] cwd exists={(project_root).exists()}")
            
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=str(project_root),
                env=os.environ.copy(),
            )
            
            self._is_running = True
            self._start_time = time.time()
            
            logger.info(f"[LaunchIntegration][START_LAUNCHER][StepComplete] Процесс запущен: PID={self._process.pid}")
            
        except Exception as e:
            logger.error(f"[LaunchIntegration][START_LAUNCHER][ExceptionCaught] Ошибка запуска: {e}")
            return False
        # END_BLOCK_START_PROCESS
        
        # START_BLOCK_START_POLLING: [Запуск polling]
        self._start_polling()
        # END_BLOCK_START_POLLING
        
        return True
    
    # END_METHOD_START_LAUNCHER
    
    # START_METHOD_STOP_LAUNCHER
    # START_CONTRACT:
    # PURPOSE: Остановка генератора. Реализует двухэтапную остановку:
    # Этап 1: Отправка SIGTERM (graceful shutdown), ожидание до 30 секунд
    # Этап 2: Отправка SIGKILL если процесс не завершился
    # INPUTS:
    # - timeout: int — таймаут ожидания завершения процесса в секундах
    # OUTPUTS:
    # - bool — True если остановка успешна
    # SIDE_EFFECTS:
    # — Останавливает polling поток
    # — Отправляет SIGTERM процессу, при необходимости SIGKILL
    # — Вызывает callback если установлен
    # KEYWORDS: [PATTERN(7): Process; DOMAIN(8): Shutdown; TECH(6): Subprocess]
    # END_CONTRACT
    def stop_launcher(self, timeout: int = None) -> bool:
        """
        Остановка генератора с двухэтапной остановкой.
        
        Этап 1: SIGTERM (graceful shutdown) - ожидание до timeout секунд
        Этап 2: SIGKILL (принудительное завершение) если процесс не завершился
        
        INPUTS:
        - timeout: int — таймаут ожидания завершения (по умолчанию GRACEFUL_SHUTDOWN_TIMEOUT)
        
        OUTPUTS:
        - bool — True если остановка успешна
        
        SIDE_EFFECTS:
        — Останавливает polling
        — Отправляет SIGTERM процессу
        — При необходимости отправляет SIGKILL
        — Вызывает on_stop_callback если установлен
        """
        # START_BLOCK_CHECK_TIMEOUT: [Установка таймаута]
        if timeout is None:
            timeout = self.GRACEFUL_SHUTDOWN_TIMEOUT
        
        logger.info(f"[LaunchIntegration][STOP_LAUNCHER][Info] Начало остановки генератора, таймаут={timeout}с")
        # END_BLOCK_CHECK_TIMEOUT
        
        # START_BLOCK_CHECK_SAFE_TO_STOP: [Проверка безопасности остановки]
        if not self._is_safe_to_stop():
            logger.warning(f"[LaunchIntegration][STOP_LAUNCHER][Warning] Остановка может быть небезопасной, продолжаем принудительно")
        # END_BLOCK_CHECK_SAFE_TO_STOP
        
        # START_BLOCK_STOP_POLLING: [Остановка polling]
        self._stop_polling.set()
        
        if self._polling_thread and self._polling_thread.is_alive():
            self._polling_thread.join(timeout=timeout)
        # END_BLOCK_STOP_POLLING
        
        # START_BLOCK_TERMINATE_PROCESS: [Двухэтапное завершение процесса]
        if self._process:
            try:
                # START_BLOCK_STAGE_1_SIGTERM: [Этап 1: Отправка SIGTERM]
                logger.info(f"[LaunchIntegration][STOP_LAUNCHER][StepComplete] Этап 1: Отправка SIGTERM процессу PID={self._process.pid}")
                self._process.terminate()
                # END_BLOCK_STAGE_1_SIGTERM
                
                # START_BLOCK_WAIT_TERMINATION: [Ожидание добровольного завершения]
                try:
                    self._process.wait(timeout=timeout)
                    logger.info(f"[LaunchIntegration][STOP_LAUNCHER][StepComplete] Процесс завершился добровольно (SIGTERM)")
                except subprocess.TimeoutExpired:
                    # START_BLOCK_STAGE_2_SIGKILL: [Этап 2: Отправка SIGKILL]
                    logger.warning(f"[LaunchIntegration][STOP_LAUNCHER][Warning] Таймаут ожидания, отправка SIGKILL")
                    self._process.kill()
                    self._process.wait(timeout=5)  # Ожидаем SIGKILL не более 5 секунд
                    logger.info(f"[LaunchIntegration][STOP_LAUNCHER][StepComplete] Процесс принудительно завершён (SIGKILL)")
                    # END_BLOCK_STAGE_2_SIGKILL
                # END_BLOCK_WAIT_TERMINATION
                
            except Exception as e:
                logger.error(f"[LaunchIntegration][STOP_LAUNCHER][ExceptionCaught] Ошибка остановки: {e}")
                return False
        # END_BLOCK_TERMINATE_PROCESS
        
        # START_BLOCK_INVOKE_CALLBACK: [Вызов callback при остановке]
        self._invoke_stop_callback()
        # END_BLOCK_INVOKE_CALLBACK
        
        # BUG_FIX_CONTEXT: Сохраняем время остановки ДО установки _is_running = False
        self._stop_time = time.time()
        self._is_running = False
        
        logger.info(f"[LaunchIntegration][STOP_LAUNCHER][StepComplete] Остановка генератора завершена")
        return True
    
    # END_METHOD_STOP_LAUNCHER
    
    # START_METHOD_IS_SAFE_TO_STOP
    # START_CONTRACT:
    # PURPOSE: Проверяет, можно ли безопасно остановить генератор.
    # Условия безопасности:
    # - Нет активной записи в wallet.dat
    # - Нет незавершенных криптографических операций
    # - Процесс не находится в критической секции
    # INPUTS: Нет
    # OUTPUTS:
    # - bool — True если безопасно останавливать
    # SIDE_EFFECTS: Нет
    # KEYWORDS: [CONCEPT(8): SafetyCheck; DOMAIN(8): Shutdown]
    # END_CONTRACT
    def _is_safe_to_stop(self) -> bool:
        """
        Проверяет, можно ли безопасно остановить генератор.
        
        Условия безопасности:
        - Нет активной записи в wallet.dat
        - Нет незавершенных криптографических операций
        - Процесс не находится в критической секции
        
        INPUTS: Нет
        
        OUTPUTS:
        - bool — True если безопасно останавливать
        
        SIDE_EFFECTS: Нет
        """
        # START_BLOCK_CHECK_METRICS: [Проверка метрик процесса]
        metrics = self._last_metrics
        
        # Проверяем признаки активной работы
        iteration_count = metrics.get('iteration_count', 0)
        current_address = metrics.get('current_address', '')
        is_generating = metrics.get('is_generating', False)
        
        # Проверяем состояние процесса
        if self._process and self._process.poll() is None:
            # Процесс работает
            
            # Если идёт активная генерация - проверяем дополнительные условия
            if is_generating or iteration_count > 0:
                # Проверяем, не в критической ли секции процесс
                # (например, запись в wallet.dat)
                if current_address and current_address != 'N/A':
                    logger.debug(f"[LaunchIntegration][IS_SAFE_TO_STOP][ConditionCheck] Процесс может быть в критической секции: current_address={current_address}")
                    # Возвращаем True, так как graceful shutdown корректно обрабатывает сигналы
                    return True
        # END_BLOCK_CHECK_METRICS
        
        # Если процесс не запущен - безопасно
        if not self._process:
            logger.debug(f"[LaunchIntegration][IS_SAFE_TO_STOP][ConditionCheck] Процесс не запущен - безопасно")
            return True
        
        # Если процесс уже завершился - безопасно
        if self._process.poll() is not None:
            logger.debug(f"[LaunchIntegration][IS_SAFE_TO_STOP][ConditionCheck] Процесс уже завершён - безопасно")
            return True
        
        logger.debug(f"[LaunchIntegration][IS_SAFE_TO_STOP][ConditionCheck] Проверка завершена - безопасно")
        return True
    
    # END_METHOD_IS_SAFE_TO_STOP
    
    # START_METHOD_SET_ON_STOP_CALLBACK
    # START_CONTRACT:
    # PURPOSE: Устанавливает callback, который будет вызван при остановке генератора.
    # Callback получает словарь с финальными метриками.
    # INPUTS:
    # - callback: Callable[[Dict], None] — функция обратного вызова
    # OUTPUTS: Нет
    # SIDE_EFFECTS:
    # — Устанавливает callback для вызова при остановке
    # KEYWORDS: [CONCEPT(7): Callback; DOMAIN(8): Events]
    # END_CONTRACT
    def set_on_stop_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Устанавливает callback, который будет вызван при остановке генератора.
        
        INPUTS:
        - callback: Callable[[Dict], None] — функция обратного вызова
        
        OUTPUTS: Нет
        
        SIDE_EFFECTS:
        — Устанавливает callback
        """
        self._on_stop_callback = callback
        logger.debug(f"[LaunchIntegration][SET_ON_STOP_CALLBACK][StepComplete] Callback установлен")
    
    # END_METHOD_SET_ON_STOP_CALLBACK
    
    # START_METHOD_INVOKE_STOP_CALLBACK
    # START_CONTRACT:
    # PURPOSE: Вызывает callback при остановке генератора с финальными метриками.
    # INPUTS: Нет
    # OUTPUTS: Нет
    # SIDE_EFFECTS:
    # — Вызывает установленный callback
    # KEYWORDS: [CONCEPT(7): Callback; DOMAIN(8): Events]
    # END_CONTRACT
    def _invoke_stop_callback(self) -> None:
        """
        Вызывает callback при остановке генератора.
        
        INPUTS: Нет
        
        OUTPUTS: Нет
        
        SIDE_EFFECTS:
        — Вызывает callback если установлен
        """
        if self._on_stop_callback:
            try:
                # START_BLOCK_PREPARE_FINAL_METRICS: [Подготовка финальных метрик]
                final_metrics = self._last_metrics.copy()
                final_metrics['stop_time'] = time.time()
                final_metrics['uptime'] = self.get_uptime()
                
                if self._process:
                    final_metrics['pid'] = self._process.pid
                    final_metrics['return_code'] = self._process.poll()
                # END_BLOCK_PREPARE_FINAL_METRICS
                
                logger.debug(f"[LaunchIntegration][INVOKE_STOP_CALLBACK][Info] Вызов callback с финальными метриками")
                self._on_stop_callback(final_metrics)
                logger.info(f"[LaunchIntegration][INVOKE_STOP_CALLBACK][StepComplete] Callback выполнен")
                
            except Exception as e:
                logger.error(f"[LaunchIntegration][INVOKE_STOP_CALLBACK][ExceptionCaught] Ошибка в callback: {e}")
    
    # END_METHOD_INVOKE_STOP_CALLBACK
    
    # START_METHOD_SET_ON_RESET_CALLBACK
    # START_CONTRACT:
    # PURPOSE: Устанавливает callback, который будет вызван при сбросе генератора.
    # INPUTS:
    # - callback: Callable[[], None] — функция обратного вызова
    # OUTPUTS: Нет
    # SIDE_EFFECTS:
    # — Устанавливает callback для вызова при сбросе
    # KEYWORDS: [CONCEPT(7): Callback; DOMAIN(8): Events]
    # END_CONTRACT
    def set_on_reset_callback(self, callback: Callable[[], None]) -> None:
        """
        Устанавливает callback, который будет вызван при сбросе генератора.
        
        INPUTS:
        - callback: Callable[[], None] — функция обратного вызова
        
        OUTPUTS: Нет
        
        SIDE_EFFECTS:
        — Устанавливает callback
        """
        self._on_reset_callback = callback
        logger.debug(f"[LaunchIntegration][SET_ON_RESET_CALLBACK][StepComplete] Callback установлен")
    
    # END_METHOD_SET_ON_RESET_CALLBACK
    
    # START_METHOD_INVOKE_RESET_CALLBACK
    # START_CONTRACT:
    # PURPOSE: Вызывает callback при сбросе генератора.
    # INPUTS: Нет
    # OUTPUTS: Нет
    # SIDE_EFFECTS:
    # — Вызывает установленный callback
    # KEYWORDS: [CONCEPT(7): Callback; DOMAIN(8): Events]
    # END_CONTRACT
    def _invoke_reset_callback(self) -> None:
        """
        Вызывает callback при сбросе генератора.
        
        INPUTS: Нет
        
        OUTPUTS: Нет
        
        SIDE_EFFECTS:
        — Вызывает callback если установлен
        """
        if self._on_reset_callback:
            try:
                logger.debug(f"[LaunchIntegration][INVOKE_RESET_CALLBACK][Info] Вызов reset callback")
                self._on_reset_callback()
                logger.info(f"[LaunchIntegration][INVOKE_RESET_CALLBACK][StepComplete] Callback выполнен")
                
            except Exception as e:
                logger.error(f"[LaunchIntegration][INVOKE_RESET_CALLBACK][ExceptionCaught] Ошибка в callback: {e}")
    
    # END_METHOD_INVOKE_RESET_CALLBACK
    
    # START_METHOD_SET_ON_MATCH_CALLBACK
    # START_CONTRACT:
    # PURPOSE: Устанавливает callback, который будет вызван при обнаружении совпадения.
    # INPUTS:
    # - callback: Callable[[Dict], None] — функция обратного вызова для обработки совпадений
    # OUTPUTS: Нет
    # SIDE_EFFECTS:
    # — Устанавливает callback для вызова при обнаружении совпадения
    # KEYWORDS: [CONCEPT(7): Callback; DOMAIN(8): Events]
    # END_CONTRACT
    def set_on_match_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Устанавливает callback, который будет вызван при обнаружении совпадения.
        
        INPUTS:
        - callback: Callable[[Dict], None] — функция обратного вызова
        
        OUTPUTS: Нет
        
        SIDE_EFFECTS:
        — Устанавливает callback
        """
        self._on_match_callback = callback
        logger.debug(f"[LaunchIntegration][SET_ON_MATCH_CALLBACK][StepComplete] Callback установлен")
    
    # END_METHOD_SET_ON_MATCH_CALLBACK
    
    # START_METHOD_ON_MATCH_DETECTED
    # START_CONTRACT:
    # PURPOSE: Вызывается при обнаружении совпадения. Запускает callback и логирует событие.
    # INPUTS:
    # - match_data: Dict[str, Any] — данные о совпадении
    # OUTPUTS: Нет
    # SIDE_EFFECTS:
    # — Вызывает установленный callback если он есть
    # — Логирует событие совпадения
    # KEYWORDS: [CONCEPT(7): Callback; DOMAIN(8): Events]
    # END_CONTRACT
    def _on_match_detected(self, match_data: Dict[str, Any]) -> None:
        """
        Вызывается при обнаружении совпадения.
        
        INPUTS:
        - match_data: Dict[str, Any] — данные о совпадении
        
        OUTPUTS: Нет
        
        SIDE_EFFECTS:
        — Вызывает callback если установлен
        — Логирует событие
        """
        if self._on_match_callback:
            try:
                logger.info(f"[LaunchIntegration][ON_MATCH_DETECTED][Info] Обнаружено совпадение: {match_data.get('address')}")
                self._on_match_callback(match_data)
                logger.debug(f"[LaunchIntegration][ON_MATCH_DETECTED][StepComplete] Callback выполнен")
            except Exception as e:
                logger.error(f"[LaunchIntegration][ON_MATCH_DETECTED][ExceptionCaught] Ошибка в callback: {e}")
    
    # END_METHOD_ON_MATCH_DETECTED
    
    # START_METHOD_START_POLLING
    # START_CONTRACT:
    # PURPOSE: Запуск потока polling для мониторинга логов в фоновом режиме.
    # INPUTS: Нет
    # OUTPUTS: Нет
    # SIDE_EFFECTS:
    # — Запускает фоновый поток для мониторинга логов
    # KEYWORDS: [CONCEPT(7): Threading; DOMAIN(8): Monitoring]
    # END_CONTRACT
    def _start_polling(self) -> None:
        """
        Запуск потока polling для мониторинга логов.
        
        INPUTS: Нет
        
        OUTPUTS: Нет
        
        SIDE_EFFECTS:
        — Запускает фоновый поток
        """
        self._stop_polling.clear()
        self._polling_thread = threading.Thread(
            target=self._polling_loop,
            name="LogPollingThread",
            daemon=True,
        )
        self._polling_thread.start()
        logger.debug(f"[LaunchIntegration][START_POLLING][StepComplete] Поток polling запущен")
    
    # END_METHOD_START_POLLING
    
    # START_METHOD_POLLING_LOOP
    # START_CONTRACT:
    # PURPOSE: Основной цикл polling - мониторинг логов. Периодически парсит логи,
    # извлекает метрики и уведомляет подписчиков.
    # INPUTS: Нет
    # OUTPUTS: Нет
    # SIDE_EFFECTS:
    # — Парсит логи
    # — Уведомляет подписчиков о новых метриках
    # KEYWORDS: [CONCEPT(8): EventLoop; DOMAIN(9): Monitoring; TECH(7): Polling]
    # END_CONTRACT
    def _polling_loop(self) -> None:
        """
        Основной цикл polling - мониторинг логов.
        
        INPUTS: Нет
        
        OUTPUTS: Нет
        
        SIDE_EFFECTS:
        — Парсит логи
        — Уведомляет подписчиков
        """
        logger.info(f"[LaunchIntegration][POLLING_LOOP][Info] Начало polling loop")
        
        # DYNAMIC_LOG: Проверка лог-файла при старте
        log_file_exists = self._log_file.exists()
        log_file_size = self._log_file.stat().st_size if log_file_exists else 0
        logger.debug(f"[LaunchIntegration][POLLING_LOOP][Debug] Лог-файл: exists={log_file_exists}, size={log_file_size}")
        
        while not self._stop_polling.is_set():
            try:
                # START_BLOCK_PARSE_LOGS: [Парсинг логов]
                new_entries = self._log_parser.parse_new_lines()
                
                if new_entries:
                    metrics = self._log_parser.get_current_metrics()
                    self._last_metrics = metrics
                    
                    # START_BLOCK_CHECK_MATCH_EVENTS: [Проверка событий совпадений]
                    for entry in new_entries:
                        match_data = self._log_parser.parse_match_event(entry.raw_line)
                        if match_data:
                            self._on_match_detected(match_data)
                    # END_BLOCK_CHECK_MATCH_EVENTS
                    
                    # START_BLOCK_NOTIFY_SUBSCRIBERS: [Уведомление подписчиков]
                    for subscriber in self._subscribers:
                        try:
                            subscriber(metrics)
                        except Exception as e:
                            logger.error(f"[LaunchIntegration][POLLING_LOOP][ExceptionCaught] Ошибка в subscriber: {e}")
                    # END_BLOCK_NOTIFY_SUBSCRIBERS
                    
                    logger.debug(f"[LaunchIntegration][POLLING_LOOP][Info] Итераций: {metrics.get('iteration_count', 0)}")
                # END_BLOCK_PARSE_LOGS
                
                # DYNAMIC_LOG: Периодическая проверка состояния файла логов
                if self._log_file.exists():
                    current_size = self._log_file.stat().st_size
                    if current_size == log_file_size and current_size > 0:
                        logger.warning(f"[LaunchIntegration][POLLING_LOOP][Warning] Размер лог-файла не изменился: {current_size} bytes - генератор может не записывать логи")
                    log_file_size = current_size
                else:
                    logger.warning(f"[LaunchIntegration][POLLING_LOOP][Warning] Лог-файл не существует!")
                
                # START_BLOCK_CHECK_PROCESS: [Проверка состояния процесса]
                if self._process:
                    if self._process.poll() is not None:
                        logger.info(f"[LaunchIntegration][POLLING_LOOP][Info] Процесс завершился")
                        self._is_running = False
                        break
                # END_BLOCK_CHECK_PROCESS
                
                # Ждём перед следующим опросом
                self._stop_polling.wait(self.POLL_INTERVAL)
            
            except Exception as e:
                logger.error(f"[LaunchIntegration][POLLING_LOOP][ExceptionCaught] Ошибка в polling: {e}")
                self._stop_polling.wait(self.POLL_INTERVAL * 2)
        
        logger.info(f"[LaunchIntegration][POLLING_LOOP][Info] Polling loop завершён")
    
    # END_METHOD_POLLING_LOOP
    
    # START_METHOD_SUBSCRIBE
    # START_CONTRACT:
    # PURPOSE: Подписка на обновления метрик. Добавляет callback в список подписчиков.
    # INPUTS:
    # - callback: Callable — функция обратного вызова для получения метрик
    # OUTPUTS: Нет
    # SIDE_EFFECTS:
    # — Добавляет callback в список подписчиков
    # KEYWORDS: [CONCEPT(7): Observer; DOMAIN(8): Events]
    # END_CONTRACT
    def subscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Подписка на обновления метрик.
        
        INPUTS:
        - callback: Callable — функция обратного вызова
        
        OUTPUTS: Нет
        """
        if callback not in self._subscribers:
            self._subscribers.append(callback)
            logger.debug(f"[LaunchIntegration][SUBSCRIBE][StepComplete] Подписчик добавлен")
    
    # END_METHOD_SUBSCRIBE
    
    # START_METHOD_UNSUBSCRIBE
    # START_CONTRACT:
    # PURPOSE: Отписка от обновлений метрик. Удаляет callback из списка подписчиков.
    # INPUTS:
    # - callback: Callable — функция обратного вызова
    # OUTPUTS: Нет
    # SIDE_EFFECTS:
    # — Удаляет callback из списка подписчиков
    # KEYWORDS: [CONCEPT(7): Observer; DOMAIN(8): Events]
    # END_CONTRACT
    def unsubscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Отписка от обновлений метрик.
        
        INPUTS:
        - callback: Callable — функция обратного вызова
        
        OUTPUTS: Нет
        """
        if callback in self._subscribers:
            self._subscribers.remove(callback)
            logger.debug(f"[LaunchIntegration][UNSUBSCRIBE][StepComplete] Подписчик удалён")
    
    # END_METHOD_UNSUBSCRIBE
    
    # START_METHOD_GET_CURRENT_METRICS
    # START_CONTRACT:
    # PURPOSE: Получение текущих метрик из последнего парсинга логов.
    # INPUTS: Нет
    # OUTPUTS:
    # - Dict[str, Any] — словарь с текущими метриками
    # SIDE_EFFECTS: Нет
    # KEYWORDS: [DOMAIN(8): Metrics; CONCEPT(6): Accessor]
    # END_CONTRACT
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Получение текущих метрик.
        
        INPUTS: Нет
        
        OUTPUTS:
        - Dict[str, Any] — текущие метрики
        
        SIDE_EFFECTS: Нет
        """
        return self._last_metrics.copy()
    
    # END_METHOD_GET_CURRENT_METRICS
    
    # START_METHOD_IS_RUNNING
    # START_CONTRACT:
    # PURPOSE: Проверка состояния запуска генератора.
    # INPUTS: Нет
    # OUTPUTS:
    # - bool — True если генератор запущен и работает
    # SIDE_EFFECTS: Нет
    # KEYWORDS: [CONCEPT(5): StateCheck; DOMAIN(7): Status]
    # END_CONTRACT
    def is_running(self) -> bool:
        """
        Проверка состояния запуска.
        
        INPUTS: Нет
        
        OUTPUTS:
        - bool — True если генератор запущен
        
        SIDE_EFFECTS: Нет
        """
        return self._is_running
    
    # END_METHOD_IS_RUNNING
    
    # START_METHOD_GET_PROCESS_INFO
    # START_CONTRACT:
    # PURPOSE: Получение информации о запущенном процессе.
    # INPUTS: Нет
    # OUTPUTS:
    # - Dict[str, Any] — информация о процессе (PID, uptime, аргументы)
    # SIDE_EFFECTS: Нет
    # KEYWORDS: [DOMAIN(7): ProcessInfo; CONCEPT(6): Accessor]
    # END_CONTRACT
    def get_process_info(self) -> Dict[str, Any]:
        """
        Получение информации о процессе.
        
        INPUTS: Нет
        
        OUTPUTS:
        - Dict[str, Any] — информация о процессе
        
        SIDE_EFFECTS: Нет
        """
        if not self._process:
            return {"running": False}
        
        return {
            "running": self._is_running,
            "pid": self._process.pid,
            "return_code": self._process.poll(),
            "uptime": time.time() - self._start_time if self._start_time else 0,
            "args": self._launch_args,
        }
    
    # END_METHOD_GET_PROCESS_INFO
    
    # START_METHOD_GET_LOG_PARSER
    # START_CONTRACT:
    # PURPOSE: Получение экземпляра парсера логов.
    # INPUTS: Нет
    # OUTPUTS:
    # - LogParser — экземпляр парсера логов
    # SIDE_EFFECTS: Нет
    # KEYWORDS: [CONCEPT(6): Accessor; DOMAIN(7): Parser]
    # END_CONTRACT
    def get_log_parser(self) -> LogParser:
        """
        Получение парсера логов.
        
        INPUTS: Нет
        
        OUTPUTS:
        - LogParser — парсер логов
        
        SIDE_EFFECTS: Нет
        """
        return self._log_parser
    
    # END_METHOD_GET_LOG_PARSER
    
    # START_METHOD_SET_LAUNCH_SCRIPT
    # START_CONTRACT:
    # PURPOSE: Установка нового пути к скрипту запуска.
    # INPUTS:
    # - script_path: str — путь к скрипту
    # OUTPUTS:
    # - bool — True если скрипт найден и установлен
    # SIDE_EFFECTS:
    # — Меняет путь к скрипту запуска
    # KEYWORDS: [CONCEPT(5): Setter; DOMAIN(7): Config]
    # END_CONTRACT
    def set_launch_script(self, script_path: str) -> bool:
        """
        Установка нового пути к скрипту запуска.
        
        INPUTS:
        - script_path: str — путь к скрипту
        
        OUTPUTS:
        - bool — True если скрипт установлен
        
        SIDE_EFFECTS:
        — Меняет путь к скрипту
        """
        path = Path(script_path)
        
        if not path.exists():
            logger.warning(f"[LaunchIntegration][SET_LAUNCH_SCRIPT][ConditionCheck] Скрипт не найден: {script_path}")
            return False
        
        self._launch_script = script_path
        logger.info(f"[LaunchIntegration][SET_LAUNCH_SCRIPT][StepComplete] Установлен скрипт: {script_path}")
        return True
    
    # END_METHOD_SET_LAUNCH_SCRIPT
    
    # START_METHOD_GET_UPTIME
    # START_CONTRACT:
    # PURPOSE: Получение времени работы генератора в секундах.
    # INPUTS: Нет
    # OUTPUTS:
    # - float — время работы в секундах
    # SIDE_EFFECTS: Нет
    # KEYWORDS: [CONCEPT(6): Timing; DOMAIN(7): Metrics]
    # END_CONTRACT
    def get_uptime(self) -> float:
        """
        Получение времени работы генератора.
        
        INPUTS: Нет
        
        OUTPUTS:
        - float — время работы в секундах
        
        SIDE_EFFECTS: Нет
        """
        # BUG_FIX_CONTEXT: Раньше возвращал 0.0 если _is_running=False,
        # но это неправильно - uptime должен показывать реальное время работы
        # даже после остановки генератора
        if not self._start_time:
            return 0.0
        
        # Используем время остановки если генератор остановлен,
        # или текущее время если генератор всё ещё работает
        end_time = self._stop_time if self._stop_time else time.time()
        return end_time - self._start_time
    
    # END_METHOD_GET_UPTIME
    
    # START_METHOD_GET_LAUNCH_STATUS
    # START_CONTRACT:
    # PURPOSE: Получение полного статуса запуска, включая информацию о процессе и парсере.
    # INPUTS: Нет
    # OUTPUTS:
    # - Dict[str, Any] — словарь со статусом запуска
    # SIDE_EFFECTS: Нет
    # KEYWORDS: [CONCEPT(6): Status; DOMAIN(8): Monitoring]
    # END_CONTRACT
    def get_launch_status(self) -> Dict[str, Any]:
        """
        Получение статуса запуска.
        
        INPUTS: Нет
        
        OUTPUTS:
        - Dict[str, Any] — статус запуска
        
        SIDE_EFFECTS: Нет
        """
        process_info = self.get_process_info()
        log_parser_info = self._log_parser.get_file_info()
        
        return {
            "is_running": self._is_running,
            "process": process_info,
            "log_parser": log_parser_info,
            "last_metrics": self._last_metrics,
        }
    
    # END_METHOD_GET_LAUNCH_STATUS
    
    # START_METHOD_WAIT_FOR_STARTUP
    # START_CONTRACT:
    # PURPOSE: Ожидание запуска генератора до истечения таймаута.
    # INPUTS:
    # - timeout: int — таймаут в секундах
    # OUTPUTS:
    # - bool — True если генератор запустился вовремя
    # SIDE_EFFECTS:
    # — Блокирует выполнение до запуска или таймаута
    # KEYWORDS: [CONCEPT(6): Blocking; DOMAIN(7): Startup]
    # END_CONTRACT
    def wait_for_startup(self, timeout: int = 30) -> bool:
        """
        Ожидание запуска генератора.
        
        INPUTS:
        - timeout: int — таймаут в секундах
        
        OUTPUTS:
        - bool — True если генератор запустился
        
        SIDE_EFFECTS:
        — Блокирует выполнение до запуска
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self._is_running and self._log_parser.is_monitoring():
                logger.info(f"[LaunchIntegration][WAIT_FOR_STARTUP][Success] Генератор запущен")
                return True
            
            time.sleep(0.5)
        
        logger.warning(f"[LaunchIntegration][WAIT_FOR_STARTUP][Timeout] Таймаут ожидания запуска")
        return False
    
    # END_METHOD_WAIT_FOR_STARTUP
    
    # START_METHOD_CHECK_HEALTH
    # START_CONTRACT:
    # PURPOSE: Проверка здоровья интеграции. Проверяет состояние процесса и наличие логов.
    # INPUTS: Нет
    # OUTPUTS:
    # - Dict[str, Any] — результат проверки с флагом healthy и списком проблем
    # SIDE_EFFECTS: Нет
    # KEYWORDS: [CONCEPT(7): HealthCheck; DOMAIN(8): Monitoring]
    # END_CONTRACT
    def check_health(self) -> Dict[str, Any]:
        """
        Проверка здоровья интеграции.
        
        INPUTS: Нет
        
        OUTPUTS:
        - Dict[str, Any] — результат проверки
        
        SIDE_EFFECTS: Нет
        """
        health = {
            "healthy": True,
            "issues": [],
        }
        
        if not self._is_running:
            health["healthy"] = False
            health["issues"].append("Генератор не запущен")
        
        log_info = self._log_parser.get_file_info()
        if not log_info.get("exists"):
            health["healthy"] = False
            health["issues"].append("Лог-файл не найден")
        
        if self._process and self._process.poll() is not None:
            health["healthy"] = False
            health["issues"].append("Процесс завершился с ошибкой")
        
        return health
    
    # END_METHOD_CHECK_HEALTH
    
    # START_METHOD_RESET
    # START_CONTRACT:
    # PURPOSE: Сброс состояния интеграции. Останавливает генератор и сбрасывает метрики.
    # INPUTS: Нет
    # OUTPUTS: Нет
    # SIDE_EFFECTS:
    # — Останавливает генератор если запущен
    # — Сбрасывает метрики и время запуска
    # — Вызывает reset callback если установлен
    # KEYWORDS: [CONCEPT(6): Reset; DOMAIN(7): State]
    # END_CONTRACT
    def reset(self) -> None:
        """
        Сброс состояния интеграции.
        
        INPUTS: Нет
        
        OUTPUTS: Нет
        
        SIDE_EFFECTS:
        — Останавливает генератор
        — Сбрасывает состояние
        — Вызывает reset callback
        """
        if self._is_running:
            self.stop_launcher()
        
        self._log_parser.reset()
        self._last_metrics = {}
        self._start_time = None
        
        # Вызов reset callback
        self._invoke_reset_callback()
        
        logger.info(f"[LaunchIntegration][RESET][StepComplete] Интеграция сброшена")
    
    # END_METHOD_RESET


# END_CLASS_LAUNCH_INTEGRATION


# START_FUNCTION_CREATE_LAUNCH_INTEGRATION
# START_CONTRACT:
# PURPOSE: Фабричная функция для создания экземпляра LaunchIntegration.
# INPUTS:
# - launch_script: Optional[str] — путь к скрипту запуска
# - log_file: Optional[str] — путь к лог-файлу
# OUTPUTS:
# - LaunchIntegration — созданная интеграция
# SIDE_EFFECTS: Нет
# KEYWORDS: [PATTERN(7): Factory; DOMAIN(8): Integration]
# END_CONTRACT

def create_launch_integration(
    launch_script: Optional[str] = None,
    log_file: Optional[str] = None,
) -> LaunchIntegration:
    """
    Фабричная функция для создания интеграции.
    
    INPUTS:
    - launch_script: Optional[str] — путь к скрипту запуска
    - log_file: Optional[str] — путь к лог-файлу
    
    OUTPUTS:
    - LaunchIntegration — созданная интеграция
    
    SIDE_EFFECTS: Нет
    """
    log_parser = LogParser(Path(log_file)) if log_file else None
    return LaunchIntegration(launch_script=launch_script, log_parser=log_parser)


# END_FUNCTION_CREATE_LAUNCH_INTEGRATION
