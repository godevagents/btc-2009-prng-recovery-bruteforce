# FILE: src/monitor/desktop_launcher.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Модуль запуска Gradio-приложения мониторинга в десктопном окне терминала для Ubuntu/Pop!_OS. Создаёт отдельное окно терминала с запущенным Gradio-сервером мониторинга кошельков Bitcoin.
# SCOPE: запуск приложений, десктопная интеграция, управление терминалами
# INPUT: Параметры командной строки (порт, путь к приложению, флаги)
# OUTPUT: Функции: launch_desktop_monitoring, check_port_availability, get_available_port, main
# KEYWORDS: [DOMAIN(9): DesktopIntegration; DOMAIN(8): Terminal; CONCEPT(7): ProcessManagement; TECH(6): Gradio; CONCEPT(5): PortBinding]
# LINKS: [CALLS(8): subprocess.Popen; USES_API(7): os.environ; IMPORTS(6): src.monitor.gradio_app]
# LINKS_TO_SPECIFICATION: [Требования к десктопному запуску мониторинга]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 9 [Класс для запуска мониторинга в десктопном окне] => DesktopLauncher
# FUNC 9 [Запускает Gradio мониторинг в десктопном окне] => launch_desktop_monitoring
# FUNC 7 [Проверяет доступность порта для запуска] => check_port_availability
# FUNC 6 [Находит первый доступный порт в диапазоне] => get_available_port
# FUNC 5 [Точка входа для запуска из CLI] => main
# FUNC 5 [Проверяет доступность C++ модулей] => _check_cpp_modules_available
# FUNC 4 [Запускает через gnome-terminal] => _launch_gnome_terminal
# FUNC 4 [Запускает через xfce4-terminal] => _launch_xfce4_terminal
# FUNC 4 [Запускает через konsole] => _launch_konsole
# FUNC 3 [Универсальный запуск терминала] => _launch_generic_terminal
# END_MODULE_MAP
# START_USE_CASES:
# - [launch_desktop_monitoring]: User (Startup) -> LaunchGradioInTerminal -> MonitoringUIReady
# - [check_port_availability]: System (PreLaunch) -> VerifyPortIsFree -> PortStatusKnown
# - [get_available_port]: System (PreLaunch) -> FindFreePort -> AvailablePortFound
# - [main]: User (CLI) -> ParseArgsAndLaunch -> DesktopMonitoringStarted
# END_USE_CASES

"""
Модуль desktop_launcher.py — Запуск мониторинга в десктопном окне Ubuntu/Pop!_OS.
Создаёт отдельное окно терминала для запуска Gradio-приложения мониторинга.
"""

# START_BLOCK_IMPORT_MODULES: [Импорт необходимых модулей]
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

# Настройка логирования с FileHandler в app.log
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
logger.info(f"[InitModule][desktop_launcher][IMPORT_MODULES][StepComplete] Модуль загружен. app.log: {app_log_path} [SUCCESS]")

# Импорт флагов доступности C++ модулей из src.monitor
# С обратной совместимостью - если модуль недоступен, используем False
try:
    from src.monitor import CPP_AVAILABLE, METRICS_AVAILABLE, __cpp_version__
    logger.info(f"[ImportCheck][desktop_launcher][IMPORT_MODULES][StepComplete] Импортированы C++ флаги: CPP_AVAILABLE={CPP_AVAILABLE}, METRICS_AVAILABLE={METRICS_AVAILABLE}, __cpp_version__={__cpp_version__} [SUCCESS]")
except ImportError as e:
    CPP_AVAILABLE = False
    METRICS_AVAILABLE = False
    __cpp_version__ = False
    logger.warning(f"[ImportCheck][desktop_launcher][IMPORT_MODULES][ExceptionCaught] Не удалось импортировать C++ флаги: {e} [WARNING]")

# END_BLOCK_IMPORT_MODULES


# START_FUNCTION__check_cpp_modules_available
# START_CONTRACT:
# PURPOSE: Проверка доступности C++ модулей мониторинга во время выполнения. Используется для логирования и выбора реализации.
# OUTPUTS:
# - bool — True если C++ модули доступны и используются
# KEYWORDS: [CONCEPT(7): CppCheck; DOMAIN(6): Monitoring; TECH(5): Binding]
# LINKS: [USES(6): CPP_AVAILABLE; USES(6): __cpp_version__]
# END_CONTRACT

def _check_cpp_modules_available() -> bool:
    """
    [Проверка доступности C++ модулей мониторинга.]
    """
    if CPP_AVAILABLE and __cpp_version__:
        logger.debug(f"[VarCheck][_check_cpp_modules_available][ReturnData] C++ модули доступны: __cpp_version__={__cpp_version__} [VALUE]")
        return True
    logger.debug(f"[VarCheck][_check_cpp_modules_available][ReturnData] Используется Python реализация [VALUE]")
    return False


# END_FUNCTION__check_cpp_modules_available


# START_FUNCTION_launch_desktop_monitoring
# START_CONTRACT:
# PURPOSE: Основная функция запуска Gradio-приложения мониторинга в десктопном окне терминала. Автоматически определяет тип десктопной среды и выбирает соответствующий терминал.
# INPUTS:
# - gradio_app_path: str — путь к файлу gradio_app.py относительно корня проекта
# - port: int — номер порта для запуска Gradio-сервера
# - share: bool — флаг создания публичной ссылки через ngrok
# - open_browser: bool — флаг автоматического открытия браузера после запуска
# - server_name: str — IP-адрес для привязки сервера
# OUTPUTS:
# - subprocess.Popen — объект процесса запущенного терминала
# SIDE_EFFECTS:
# - Создаёт новый процесс терминала в операционной системе
# - Запускает Python-процесс с Gradio-приложением
# TEST_CONDITIONS_SUCCESS_CRITERIA:
# - Файл gradio_app_path должен существовать
# - Порт должен быть доступен или функция должна обработать занятый порт
# - Должен быть найден хотя бы один доступный терминал
# KEYWORDS: [PATTERN(7): Factory; DOMAIN(9): DesktopLaunch; TECH(6): Gradio; CONCEPT(8): ProcessSpawning]
# LINKS: [CALLS(8): _launch_gnome_terminal; CALLS(7): _launch_xfce4_terminal; CALLS(7): _launch_konsole; USES_API(6): os.environ]
# END_CONTRACT

def launch_desktop_monitoring(
    gradio_app_path: str = "src/monitor/gradio_app.py",
    port: int = 7860,
    share: bool = False,
    open_browser: bool = True,
    server_name: str = "127.0.0.1",
) -> subprocess.Popen:
    """
    #
    # ИНСТРУКЦИИ ПО ЛОГИРОВАНИЮ:
    #
    # 1. ГЛОБАЛЬНОЕ ПРАВИЛО: ЛОГИРОВАНИЕ В ФАЙЛ
    # - Любая система логирования, которую вы настраиваете или модифицируете,
    #   **обязана** включать файловый обработчик (`logging.FileHandler`),
    #   который пишет логи в файл `app.log` в корне проекта.
    #
    [Запуск Gradio мониторинга в десктопном окне терминала.]
    """

    # START_BLOCK_CHECK_CPP_STATUS: [Проверка и логирование статуса C++ модулей]
    cpp_available = _check_cpp_modules_available()
    if cpp_available:
        logger.info("[launch_desktop_monitoring][CHECK_CPP_STATUS][INFO] Используется C++ реализация мониторинга [SUCCESS]")
    else:
        logger.info("[launch_desktop_monitoring][CHECK_CPP_STATUS][INFO] Используется Python реализация мониторинга [INFO]")
    # END_BLOCK_CHECK_CPP_STATUS

    # START_BLOCK_VALIDATE_PATHS: [Проверка существования файла приложения]
    app_path = Path(gradio_app_path)
    if not app_path.exists():
        app_path = Path.cwd() / gradio_app_path
        if not app_path.exists():
            logger.error(f"[launch_desktop_monitoring][VALIDATE_PATHS][FAIL] Файл не найден: {gradio_app_path}")
            raise FileNotFoundError(f"Файл приложения не найден: {gradio_app_path}")

    logger.info(f"[launch_desktop_monitoring][VALIDATE_PATHS][SUCCESS] Файл приложения найден: {app_path}")
    # END_BLOCK_VALIDATE_PATHS

    # START_BLOCK_BUILD_COMMAND: [Формирование команды запуска]
    python_executable = sys.executable
    
    # Получаем абсолютный путь к корню проекта
    project_root_path = os.path.dirname(os.path.abspath(__file__))
    # Поднимаемся на уровень выше от src/monitor/ к корню проекта
    while os.path.basename(project_root_path) != "WALLET.DAT.GENERATOR":
        project_root_path = os.path.dirname(project_root_path)
    
    # Формируем команду с установкой PYTHONPATH и сменой директории
    # Используем абсолютный путь к файлу приложения
    app_path_abs = str(app_path.resolve())
    
    # BUG_FIX_CONTEXT: Пробелы в пути проекта ломали PYTHONPATH и путь к файлу
    # Добавили кавычки для корректной обработки путей с пробелами
    command_parts = [
        f"cd \"{project_root_path}\" && "
        f"PYTHONPATH=\"{project_root_path}\":$PYTHONPATH "
        f"{python_executable} \"{app_path_abs}\"",
        "--port", str(port),
        "--server-name", server_name,
    ]

    if share:
        command_parts.append("--share")

    if not open_browser:
        command_parts.append("--no-open-browser")

    # Объединяем аргументы для запуска в bash -c
    cmd_str = command_parts[0]
    for arg in command_parts[1:]:
        cmd_str += f" {arg}"
    
    command = cmd_str
    logger.info(f"[launch_desktop_monitoring][BUILD_COMMAND][ReturnData] Команда: {command}")
    # END_BLOCK_BUILD_COMMAND

    # START_BLOCK_DETECT_DESKTOP_ENVIRONMENT: [Определение типа десктопной среды]
    desktop_env = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()

    logger.debug(f"[launch_desktop_monitoring][DETECT_DESKTOP_ENVIRONMENT][ConditionCheck] Desktop: {desktop_env}, Session: {session_type}")
    # END_BLOCK_DETECT_DESKTOP_ENVIRONMENT

    # START_BLOCK_LAUNCH_TERMINAL: [Запуск терминала с приложением]
    launch_result = None

    if "ubuntu" in desktop_env or "pop" in desktop_env:
        # Ubuntu / Pop!_OS - используем gnome-terminal
        try:
            launch_result = _launch_gnome_terminal(command, port, share)
        except Exception as e:
            logger.warning(f"[launch_desktop_monitoring][LAUNCH_TERMINAL][ExceptionCaught] Ошибка gnome-terminal: {e}")
            try:
                launch_result = _launch_xfce4_terminal(command, port, share)
            except Exception as e2:
                logger.warning(f"[launch_desktop_monitoring][LAUNCH_TERMINAL][ExceptionCaught] Ошибка xfce4-terminal: {e2}")
                launch_result = _launch_konsole(command, port, share)
    elif "kde" in desktop_env:
        # KDE - используем konsole
        launch_result = _launch_konsole(command, port, share)
    elif "xfce" in desktop_env:
        # XFCE - используем xfce4-terminal
        launch_result = _launch_xfce4_terminal(command, port, share)
    else:
        # Generic - пробуем разные терминалы
        launch_result = _launch_generic_terminal(command, port, share)

    logger.info(f"[launch_desktop_monitoring][LAUNCH_TERMINAL][StepComplete] Мониторинг запущен в десктопном окне")
    # END_BLOCK_LAUNCH_TERMINAL

    return launch_result


# END_FUNCTION_launch_desktop_monitoring


# START_FUNCTION__launch_gnome_terminal
# START_CONTRACT:
# PURPOSE: Запуск команды через gnome-terminal с настроенным заголовком окна.
# INPUTS:
# - command: str — полная команда для выполнения в терминале
# - port: int — номер порта для отображения в информационном сообщении
# - share: bool — флаг публичной ссылки
# OUTPUTS:
# - subprocess.Popen — запущенный процесс терминала
# SIDE_EFFECTS:
# - Создаёт новый процесс gnome-terminal
# KEYWORDS: [CONCEPT(5): Gnome; TECH(4): Terminal]
# LINKS: [CALLS(6): subprocess.Popen]
# END_CONTRACT

def _launch_gnome_terminal(command: str, port: int, share: bool) -> subprocess.Popen:
    """
    [Запуск через gnome-terminal.]
    """

    title = f"WALLET.DAT.GENERATOR Monitor (port {port})"

    # BUG_FIX_CONTEXT: Проблема - subprocess.run() с --wait блокирует до закрытия терминала
    # Решение - используем subprocess.Popen() без блокировки, gnome-terminal сам управляет процессом
    
    cmd = [
        "gnome-terminal",
        "--title", title,
        "--",
        "bash", "-c",
        f"echo '=== WALLET.DAT.GENERATOR MONITORING ===' && "
        f"echo 'Порт: {port}' && "
        f"echo 'Ссылка: http://127.0.0.1:{port}' && "
        f"echo '======================================' && "
        f"echo '' && "
        f"{command} && bash"
    ]

    logger.debug(f"[launch_gnome_terminal][CallExternal] Запуск: gnome-terminal...")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    logger.info(f"[launch_gnome_terminal][StepComplete] gnome-terminal запущен с PID: {process.pid}")
    return process


# END_FUNCTION__launch_gnome_terminal


# START_FUNCTION__launch_xfce4_terminal
# START_CONTRACT:
# PURPOSE: Запуск команды через xfce4-terminal с настроенным заголовком окна.
# INPUTS:
# - command: str — полная команда для выполнения в терминале
# - port: int — номер порта для отображения в заголовке
# - share: bool — флаг публичной ссылки
# OUTPUTS:
# - subprocess.Popen — запущенный процесс терминала
# SIDE_EFFECTS:
# - Создаёт новый процесс xfce4-terminal
# KEYWORDS: [CONCEPT(5): XFCE; TECH(4): Terminal]
# LINKS: [CALLS(6): subprocess.Popen]
# END_CONTRACT

def _launch_xfce4_terminal(command: str, port: int, share: bool) -> subprocess.Popen:
    """
    [Запуск через xfce4-terminal.]
    """

    title = f"WALLET.DAT.GENERATOR Monitor (port {port})"

    cmd = [
        "xfce4-terminal",
        "--title", title,
        "--command", f"bash -c '{command}; bash'",
    ]

    logger.debug(f"[launch_xfce4_terminal][CallExternal] Запуск: {' '.join(cmd[:4])}...")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    logger.info(f"[launch_xfce4_terminal][StepComplete] xfce4-terminal запущен с PID: {process.pid}")
    return process


# END_FUNCTION__launch_xfce4_terminal


# START_FUNCTION__launch_konsole
# START_CONTRACT:
# PURPOSE: Запуск команды через konsole (KDE) с настроенным заголовком окна.
# INPUTS:
# - command: str — полная команда для выполнения в терминале
# - port: int — номер порта для отображения в заголовке
# - share: bool — флаг публичной ссылки
# OUTPUTS:
# - subprocess.Popen — запущенный процесс терминала
# SIDE_EFFECTS:
# - Создаёт новый процесс konsole
# KEYWORDS: [CONCEPT(5): KDE; TECH(4): Konsole]
# LINKS: [CALLS(6): subprocess.Popen]
# END_CONTRACT

def _launch_konsole(command: str, port: int, share: bool) -> subprocess.Popen:
    """
    [Запуск через konsole (KDE).]
    """

    title = f"WALLET.DAT.GENERATOR Monitor (port {port})"

    cmd = [
        "konsole",
        "--title", title,
        "-e", "bash", "-c",
        f"{command}; bash"
    ]

    logger.debug(f"[launch_konsole][CallExternal] Запуск: {' '.join(cmd[:5])}...")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    logger.info(f"[launch_konsole][StepComplete] konsole запущен с PID: {process.pid}")
    return process


# END_FUNCTION__launch_konsole


# START_FUNCTION__launch_generic_terminal
# START_CONTRACT:
# PURPOSE: Универсальный запуск терминала - последовательно пробует доступные эмуляторы терминала. Используется как резервный вариант при неизвестной десктопной среде.
# INPUTS:
# - command: str — полная команда для выполнения в терминале
# - port: int — номер порта для отображения в информации
# - share: bool — флаг публичной ссылки
# OUTPUTS:
# - subprocess.Popen — запущенный процесс терминала
# SIDE_EFFECTS:
# - Последовательно пытается запустить разные терминалы
# TEST_CONDITIONS_SUCCESS_CRITERIA:
# - Хотя бы один эмулятор терминала должен быть установлен в системе
# KEYWORDS: [CONCEPT(6): Fallback; TECH(5): TerminalEmulator]
# LINKS: [CALLS(6): subprocess.Popen; USES_API(5): FileNotFoundError]
# END_CONTRACT

def _launch_generic_terminal(command: str, port: int, share: bool) -> subprocess.Popen:
    """
    [Универсальный запуск терминала - пробует разные эмуляторы.]
    """

    terminal_emulators = [
        ["gnome-terminal", "--", "bash", "-c"],
        ["xfce4-terminal", "--command"],
        ["konsole", "-e"],
        ["xterm", "-e"],
        ["urxvt", "-e"],
    ]

    for emulator_cmd in terminal_emulators:
        try:
            emulator_name = emulator_cmd[0]
            logger.debug(f"[launch_generic_terminal][Attempt] Пробуем: {emulator_name}")

            if emulator_name in ["gnome-terminal"]:
                cmd = emulator_cmd + [
                    "bash", "-c",
                    f"echo '=== WALLET.DAT.GENERATOR MONITORING ===' && "
                    f"echo 'Порт: {port}' && "
                    f"echo 'Ссылка: http://127.0.0.1:{port}' && "
                    f"echo '======================================' && "
                    f"echo '' && "
                    f"{command} && bash"
                ]
            elif emulator_name == "xterm":
                cmd = emulator_cmd + [f"{command}; bash"]
            else:
                cmd = emulator_cmd + [f"{command}; bash"]

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"[launch_generic_terminal][SUCCESS] Запущен {emulator_name} с PID: {process.pid}")
            return process
        except FileNotFoundError:
            logger.debug(f"[launch_generic_terminal][ConditionCheck] {emulator_name} не найден, пробуем следующий")
            continue
        except Exception as e:
            logger.warning(f"[launch_generic_terminal][ExceptionCaught] Ошибка запуска {emulator_name}: {e}")
            continue

    logger.error(f"[launch_generic_terminal][FAIL] Не удалось запустить ни один терминал")
    raise RuntimeError("Не удалось найти доступный терминал для запуска")


# END_FUNCTION__launch_generic_terminal


# START_FUNCTION_check_port_availability
# START_CONTRACT:
# PURPOSE: Проверка доступности TCP-порта для прослушивания. Используется перед запуском Gradio-сервера для избежания конфликтов.
# INPUTS:
# - port: int — номер порта для проверки
# OUTPUTS:
# - bool — True если порт свободен и может быть использован, False если порт занят
# SIDE_EFFECTS:
# - Создаёт и закрывает сокет для проверки
# KEYWORDS: [CONCEPT(7): PortBinding; TECH(6): Socket; DOMAIN(5): Network]
# LINKS: [USES_API(6): socket.socket]
# END_CONTRACT

def check_port_availability(port: int) -> bool:
    """
    [Проверка доступности порта.]
    """

    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
        sock.close()
        logger.debug(f"[check_port_availability][ConditionCheck] Порт {port} доступен [SUCCESS]")
        return True
    except OSError:
        logger.warning(f"[check_port_availability][ConditionCheck] Порт {port} занят [FAIL]")
        return False


# END_FUNCTION_check_port_availability


# START_FUNCTION_get_available_port
# START_CONTRACT:
# PURPOSE: Поиск первого доступного порта в заданном диапазоне. Используется для автоматического выбора порта при запуске мониторинга.
# INPUTS:
# - start_port: int — начальный порт диапазона поиска (по умолчанию 7860)
# - max_attempts: int — максимальное количество портов для проверки (по умолчанию 10)
# OUTPUTS:
# - int — номер первого доступного порта
# SIDE_EFFECTS:
# - Проверяет доступность нескольких портов
# TEST_CONDITIONS_SUCCESS_CRITERIA:
# - Как минимум один порт в диапазоне должен быть свободен
# KEYWORDS: [CONCEPT(7): PortScanning; TECH(6): Socket; DOMAIN(5): Network]
# LINKS: [CALLS(7): check_port_availability]
# END_CONTRACT

def get_available_port(start_port: int = 7860, max_attempts: int = 10) -> int:
    """
    [Поиск первого доступного порта.]
    """

    for port in range(start_port, start_port + max_attempts):
        if check_port_availability(port):
            logger.info(f"[get_available_port][ReturnData] Найден доступный порт: {port}")
            return port

    logger.error(f"[get_available_port][FAIL] Не найден доступный порт в диапазоне {start_port}-{start_port + max_attempts - 1}")
    raise RuntimeError("Не найден доступный порт")


# END_FUNCTION_get_available_port


# START_FUNCTION_main
# START_CONTRACT:
# PURPOSE: Главная функция точки входа для запуска мониторинга из командной строки. Парсирует аргументы и вызывает функцию запуска десктопного мониторинга.
# INPUTS: Нет (аргументы передаются через sys.argv)
# OUTPUTS: Нет (запускает процесс и не возвращает управление)
# SIDE_EFFECTS:
# - Парсирует аргументы командной строки
# - Запускает десктопное окно с Gradio-мониторингом
# - Процесс остаётся активным до закрытия терминала
# KEYWORDS: [PATTERN(8): CLI_Entry; DOMAIN(7): CommandLine; CONCEPT(6): ArgumentParsing]
# LINKS: [CALLS(8): launch_desktop_monitoring; USES_API(6): argparse.ArgumentParser]
# END_CONTRACT

def main() -> None:
    """
    [Главная функция для запуска мониторинга из командной строки.]
    """

    import argparse

    parser = argparse.ArgumentParser(
        description="Запуск мониторинга генератора кошельков в десктопном окне"
    )
    parser.add_argument(
        "--port", type=int, default=7860,
        help="Порт для Gradio (по умолчанию: 7860)"
    )
    # parser.add_argument(
    #     "--share", action="store_true",
    #     help="Создать публичную ссылку"
    # )  # Закомментировано: убрать кнопку "использовать через api"
    parser.add_argument(
        "--no-browser", action="store_true",
        help="Не открывать браузер автоматически"
    )
    parser.add_argument(
        "--app-path", type=str, default="src/monitor/gradio_app.py",
        help="Путь к файлу gradio_app.py"
    )
    parser.add_argument(
        "--server-name", type=str, default="127.0.0.1",
        help="Имя сервера для привязки"
    )

    args = parser.parse_args()

    # START_BLOCK_CONFIGURE_LOGGING: [Настройка логирования для main]
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(app_log_path),
        ],
    )

    logger.info("=" * 50)
    logger.info("WALLET.DAT.GENERATOR - Desktop Monitoring Launcher")
    logger.info("=" * 50)
    # END_BLOCK_CONFIGURE_LOGGING

    # START_BLOCK_LAUNCH_MONITORING: [Запуск мониторинга]
    try:
        process = launch_desktop_monitoring(
            gradio_app_path=args.app_path,
            port=args.port,
            share=args.share,
            open_browser=not args.no_browser,
            server_name=args.server_name,
        )

        logger.info(f"Мониторинг запущен в десктопном окне (PID: {process.pid})")
        logger.info(f"Откройте http://127.0.0.1:{args.port} в браузере")
        logger.info("Нажмите Ctrl+C для остановки")
        
        # START_BLOCK_WAIT_PROCESS: [Ожидание завершения процесса]
        # BUG_FIX_CONTEXT: gnome-terminal завершается после запуска дочернего процесса Python
        # Python процесс Gradio становится "сиротой" и продолжает работу
        # Поэтому просто выходим - Gradio работает в терминале
        logger.info("Скрипт запуска завершён. Gradio работает в отдельном терминале.")
        # END_BLOCK_WAIT_PROCESS

    except Exception as e:
        logger.error(f"Ошибка запуска мониторинга: {e}")
        sys.exit(1)
    # END_BLOCK_LAUNCH_MONITORING


# END_FUNCTION_main


# START_CLASS_DESKTOP_LAUNCHER
# START_CONTRACT:
# PURPOSE: Класс для запуска мониторинга в десктопном окне. Инкапсулирует логику запуска Gradio-приложения мониторинга в отдельном терминале.
# ATTRIBUTES:
# - gradio_app_path: str — путь к файлу приложения
# - port: int — номер порта
# - share: bool — флаг публичной ссылки
# - open_browser: bool — флаг открытия браузера
# - server_name: str — IP сервера
# - process: Optional[subprocess.Popen] — запущенный процесс
# METHODS:
# - __init__(**kwargs): Инициализация с параметрами
# - check_port() -> bool: Проверка доступности порта
# - find_available_port() -> int: Поиск доступного порта
# - launch() -> subprocess.Popen: Запуск мониторинга
# - stop() -> None: Остановка мониторинга
# - is_running() -> bool: Проверка состояния
# KEYWORDS: [PATTERN(8): Launcher; DOMAIN(9): DesktopIntegration; TECH(6): ProcessManagement]
# LINKS: [CALLS(7): launch_desktop_monitoring; CALLS(6): check_port_availability]
# END_CONTRACT

class DesktopLauncher:
    """
    Класс для запуска мониторинга в десктопном окне.
    """

    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация лаунчера с параметрами запуска
    # INPUTS:
    # - gradio_app_path: str — путь к файлу gradio_app.py
    # - port: int — номер порта для запуска
    # - share: bool — создать публичную ссылку
    # - open_browser: bool — открыть браузер автоматически
    # - server_name: str — IP-адрес сервера
    # KEYWORDS: [CONCEPT(6): Initialization]
    # END_CONTRACT

    def __init__(
        self,
        gradio_app_path: str = "src/monitor/gradio_app.py",
        port: int = 7860,
        share: bool = False,
        open_browser: bool = True,
        server_name: str = "127.0.0.1",
    ) -> None:
        self.gradio_app_path = gradio_app_path
        self.port = port
        self.share = share
        self.open_browser = open_browser
        self.server_name = server_name
        self.process: Optional[subprocess.Popen] = None
        logger.debug(f"[DesktopLauncher][INIT] Лаунчер инициализирован с портом {port}")

    # END_METHOD___init__

    # START_METHOD_CHECK_PORT
    # START_CONTRACT:
    # PURPOSE: Проверка доступности порта для запуска
    # OUTPUTS: bool — True если порт свободен
    # KEYWORDS: [CONCEPT(5): PortCheck]
    # END_CONTRACT

    def check_port(self) -> bool:
        """Проверка доступности порта."""
        return check_port_availability(self.port)

    # END_METHOD_CHECK_PORT

    # START_METHOD_FIND_AVAILABLE_PORT
    # START_CONTRACT:
    # PURPOSE: Поиск первого доступного порта
    # OUTPUTS: int — номер доступного порта
    # KEYWORDS: [CONCEPT(6): PortSearch]
    # END_CONTRACT

    def find_available_port(self) -> int:
        """Поиск доступного порта."""
        port = get_available_port(self.port)
        self.port = port
        logger.info(f"[DesktopLauncher][FIND_AVAILABLE_PORT] Найден порт: {port}")
        return port

    # END_METHOD_FIND_AVAILABLE_PORT

    # START_METHOD_LAUNCH
    # START_CONTRACT:
    # PURPOSE: Запуск мониторинга в десктопном окне
    # OUTPUTS: subprocess.Popen — запущенный процесс
    # KEYWORDS: [CONCEPT(6): Launch]
    # END_CONTRACT

    def launch(self) -> subprocess.Popen:
        """Запуск мониторинга."""
        logger.info(f"[DesktopLauncher][LAUNCH] Запуск мониторинга на порту {self.port}")
        
        self.process = launch_desktop_monitoring(
            gradio_app_path=self.gradio_app_path,
            port=self.port,
            share=self.share,
            open_browser=self.open_browser,
            server_name=self.server_name,
        )
        
        logger.info(f"[DesktopLauncher][LAUNCH] Мониторинг запущен, PID: {self.process.pid}")
        return self.process

    # END_METHOD_LAUNCH

    # START_METHOD_STOP
    # START_CONTRACT:
    # PURPOSE: Остановка запущенного мониторинга
    # OUTPUTS: None
    # KEYWORDS: [CONCEPT(6): Shutdown]
    # END_CONTRACT

    def stop(self) -> None:
        """Остановка мониторинга."""
        if self.process:
            try:
                self.process.terminate()
                logger.info(f"[DesktopLauncher][STOP] Процесс остановлен")
            except Exception as e:
                logger.error(f"[DesktopLauncher][STOP] Ошибка остановки: {e}")

    # END_METHOD_STOP

    # START_METHOD_IS_RUNNING
    # START_CONTRACT:
    # PURPOSE: Проверка состояния мониторинга
    # OUTPUTS: bool — True если процесс запущен
    # KEYWORDS: [CONCEPT(5): StateCheck]
    # END_CONTRACT

    def is_running(self) -> bool:
        """Проверка состояния."""
        if self.process:
            return self.process.poll() is None
        return False

    # END_METHOD_IS_RUNNING


# END_CLASS_DESKTOP_LAUNCHER


if __name__ == "__main__":
    main()
