# START_MODULE_CONTRACT:
# PURPOSE: Точка входа для запуска Gradio мониторинга с автоматической проверкой сборки
# SCOPE: CLI, запуск приложения, мониторинг, компиляция
# INPUT: Аргументы командной строки (port, share, server_name)
# OUTPUT: Запуск Gradio мониторинга
# KEYWORDS: [DOMAIN(9): CLI; DOMAIN(8): EntryPoint; CONCEPT(7): Launcher; TECH(6): Gradio; TECH(5): CMake]
# END_MODULE_CONTRACT

# START_MODULE_MAP:
# FUNC 10 [Главная функция точки входа] => main
# FUNC 8 [Проверяет наличие скомпилированных модулей в lib/] => check_compiled_modules
# FUNC 5 [Очистка лога перед запуском] => clear_infinite_loop_log
# FUNC 7 [Закрывает процесс на указанном порте] => kill_port
# FUNC 7 [Закрывает все процессы Gradio] => kill_all_gradio_ports
# END_MODULE_MAP

# CRITICAL: Проверка рабочей директории ДО импортов gradio
# Gradio вызывает os.getcwd() при импорте, что вызывает FileNotFoundError
# если текущая рабочая директория не существует
import os
import sys

# Ensure current working directory exists before importing any modules
try:
    os.getcwd()
except FileNotFoundError:
    # Set working directory to project root (go up from "quick start" to project root)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    sys.path.insert(0, project_root)

import logging
import argparse
import glob
import signal
import socket
import subprocess
from pathlib import Path

# Настройка sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Список ожидаемых модулей для компиляции
EXPECTED_MODULES = [
    "address_matcher_cpp",
    "batch_gen_cpp",
    "core_cpp",
    "entropy_engine_cpp",
    "entropy_pipeline_cache_cpp",
    "getbitmaps_cpp",
    "hkey_performance_data_cpp",
    "rand_poll_cpp",
    "wallet_dat_cpp"
]

# START_FUNCTION_check_compiled_modules
# START_CONTRACT:
# PURPOSE: Проверяет наличие всех скомпилированных модулей в директории lib/
# INPUTS: Нет
# OUTPUTS: bool - True если все модули присутствуют, False если отсутствуют
# SIDE_EFFECTS: При отсутствии модулей выводит информацию в лог
# KEYWORDS: [DOMAIN(8): Compilation; CONCEPT(7): ModuleCheck; TECH(5): FileIO]
# LINKS: [READS_DATA_FROM(5): lib/]
# END_CONTRACT

def check_compiled_modules() -> bool:
    """
    Проверяет наличие скомпилированных модулей в директории lib/.
    
    Описание:
        Проверяет наличие всех ожидаемых .so файлов в директории lib/.
        Формат имени файла: <module_name>_cpp.cpython-310-x86_64-linux-gnu.so
    
    Возвращает:
        True если все модули присутствуют, False в противном случае.
    """
    lib_dir = project_root / "lib"
    
    # Проверяем существование директории lib
    if not lib_dir.exists():
        logger = logging.getLogger(__name__)
        logger.info(f"[VarCheck][check_compiled_modules][DIR_CHECK] Директория lib/ не существует: {lib_dir} [FAIL]")
        return False
    
    # Ищем все .so файлы в lib/
    so_pattern = str(lib_dir / "*_cpp.cpython-310-x86_64-linux-gnu.so")
    found_files = glob.glob(so_pattern)
    
    # Извлекаем имена модулей из найденных файлов
    found_modules = set()
    for file_path in found_files:
        filename = os.path.basename(file_path)
        # Извлекаем имя модуля (до _cpp)
        module_name = filename.replace("_cpp.cpython-310-x86_64-linux-gnu.so", "")
        found_modules.add(module_name)
    
    # Проверяем наличие всех ожидаемых модулей
    # Нормализуем имена - убираем _cpp суффикс из ожидаемых для сравнения
    expected_modules_normalized = {m.replace("_cpp", "") for m in EXPECTED_MODULES}
    
    missing_modules = []
    for expected_module in expected_modules_normalized:
        if expected_module not in found_modules:
            missing_modules.append(expected_module)
    
    logger = logging.getLogger(__name__)
    
    if missing_modules:
        logger.info(f"[VarCheck][check_compiled_modules][MODULE_CHECK] Отсутствуют модули: {missing_modules} [FAIL]")
        logger.info(f"[VarCheck][check_compiled_modules][MODULE_CHECK] Найдены модули: {sorted(found_modules)} [INFO]")
        return False
    
    logger.info(f"[VarCheck][check_compiled_modules][MODULE_CHECK] Все {len(EXPECTED_MODULES)} модулей присутствуют в lib/ [SUCCESS]")
    return True


# END_FUNCTION_check_compiled_modules

# START_FUNCTION_kill_port
# START_CONTRACT:
# PURPOSE: Закрывает процесс, занимающий указанный порт
# INPUTS:
# - port: int - номер порта
# OUTPUTS:
# - bool - True если процесс был закрыт, False если порт свободен или произошла ошибка
# SIDE_EFFECTS:
# - Убивает процесс через SIGKILL
# KEYWORDS: [DOMAIN(9): ProcessManagement; CONCEPT(7): PortKilling; TECH(6): subprocess]
# LINKS: [USES_API(8): os.kill; USES_API(7): subprocess.run]
# END_CONTRACT

def kill_port(port: int) -> bool:
    """
    Закрывает процесс на указанном порте.
    
    Описание:
        Использует lsof для поиска процесса на порту, затем убивает его.
        Полезно для освобождения портов после падения приложений.
    
    Аргументы:
        port: Номер порта для освобождения.
    
    Возвращает:
        True если процесс был закрыт, False в противном случае.
    """
    logger = logging.getLogger(__name__)
    
    # START_BLOCK_FIND_PROCESS: [Поиск процесса на порту через lsof]
    try:
        result = subprocess.run(
            ['lsof', '-t', f'-i:{port}'],
            capture_output=True,
            text=True
        )
        logger.debug(f"[VarCheck][kill_port][FIND_PROCESS] Результат lsof для порта {port}: returncode={result.returncode}, stdout='{result.stdout.strip()}' [INFO]")
        
        if result.returncode == 0 and result.stdout.strip():
            pid = int(result.stdout.strip())
            logger.info(f"[VarCheck][kill_port][FIND_PROCESS] Найден процесс {pid} на порту {port} [SUCCESS]")
        else:
            logger.info(f"[VarCheck][kill_port][FIND_PROCESS] Процесс на порту {port} не найден [INFO]")
            return False
    except FileNotFoundError:
        logger.error(f"[CriticalError][kill_port][FIND_PROCESS] Команда lsof не найдена. Установите lsof: sudo apt-get install lsof [FAIL]")
        return False
    except Exception as e:
        logger.error(f"[CriticalError][kill_port][FIND_PROCESS] Ошибка при поиске процесса на порту {port}: {e} [FAIL]")
        return False
    # END_BLOCK_FIND_PROCESS
    
    # START_BLOCK_KILL_PROCESS: [Убийство процесса через SIGKILL]
    try:
        os.kill(pid, signal.SIGKILL)
        logger.info(f"[VarCheck][kill_port][KILL_PROCESS] Процесс {pid} на порту {port} завершен [SUCCESS]")
        return True
    except ProcessLookupError:
        logger.warning(f"[VarCheck][kill_port][KILL_PROCESS] Процесс {pid} уже не существует [INFO]")
        return True
    except PermissionError:
        logger.error(f"[CriticalError][kill_port][KILL_PROCESS] Нет прав для завершения процесса {pid}. Запустите с sudo [FAIL]")
        return False
    except Exception as e:
        logger.error(f"[CriticalError][kill_port][KILL_PROCESS] Ошибка при завершении процесса {pid}: {e} [FAIL]")
        return False
    # END_BLOCK_KILL_PROCESS


# END_FUNCTION_kill_port

# START_FUNCTION_kill_all_gradio_ports
# START_CONTRACT:
# PURPOSE: Закрывает все процессы Gradio на стандартных портах
# INPUTS: Нет
# OUTPUTS:
# - bool - True если хотя бы один порт был закрыт, False если ни одного процесса не было найдено
# SIDE_EFFECTS:
# - Убивает все процессы Gradio
# KEYWORDS: [DOMAIN(9): ProcessManagement; CONCEPT(8): BatchPortKilling; TECH(6): Gradio]
# LINKS: [CALLS(7): kill_port]
# END_CONTRACT

def kill_all_gradio_ports() -> bool:
    """
    Закрывает все процессы Gradio на стандартных портах.
    
    Описание:
        Проверяет и закрывает процессы на портах 7860, 7861, 7862.
        Эти порты обычно используются Gradio для запуска веб-интерфейсов.
    
    Возвращает:
        True если хотя бы один процесс был закрыт, False в противном случае.
    """
    logger = logging.getLogger(__name__)
    
    # Стандартные порты Gradio
    gradio_ports = [7860, 7861, 7862]
    
    logger.info(f"[TraceCheck][kill_all_gradio_ports][START] Завершение процессов Gradio на портах {gradio_ports} [ATTEMPT]")
    
    killed_count = 0
    for port in gradio_ports:
        # START_BLOCK_KILL_GRADIO_PORT: [Закрытие процесса на конкретном порту]
        if kill_port(port):
            killed_count += 1
        # END_BLOCK_KILL_GRADIO_PORT
    
    if killed_count > 0:
        logger.info(f"[TraceCheck][kill_all_gradio_ports][COMPLETE] Закрыто процессов: {killed_count}/{len(gradio_ports)} [SUCCESS]")
        return True
    else:
        logger.info(f"[TraceCheck][kill_all_gradio_ports][COMPLETE] Нет процессов Gradio на стандартных портах [INFO]")
        return False


# END_FUNCTION_kill_all_gradio_ports

# Настройка sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Импорт из gradio_app
from src.monitor.gradio_app import (
    GradioMonitorApp,
    create_gradio_app,
    clear_infinite_loop_log
)

# Настройка логирования (аналогично gradio_app.py)
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

# Глобальные переменные для управления ресурсами
open_servers = []
gradio_app_instance = None

def signal_handler(signum, frame):
    """
    Обработчик сигнала SIGINT (Ctrl+C).
    Закрывает все открытые порты и серверы перед выходом.
    """
    print("\n[SignalHandler] Получен сигнал Ctrl+C. Закрываем порты...")
    logger.info("[SignalHandler][SIGINT] Получен сигнал прерывания. Закрываем ресурсы... [INFO]")
    
    # Закрываем Gradio приложение если оно существует
    global gradio_app_instance
    if gradio_app_instance is not None:
        try:
            logger.info("[SignalHandler][GRADIO_CLOSE] Закрытие Gradio приложения... [ATTEMPT]")
            gradio_app_instance.close()
            logger.info("[SignalHandler][GRADIO_CLOSE] Gradio приложение закрыто [SUCCESS]")
        except Exception as e:
            logger.error(f"[SignalHandler][GRADIO_CLOSE] Ошибка при закрытии Gradio: {e} [FAIL]")
    
    # Закрываем все зарегистрированные серверы
    for server in open_servers:
        try:
            if hasattr(server, 'shutdown'):
                server.shutdown(socket.SHUT_RDWR)
            if hasattr(server, 'close'):
                server.close()
            logger.info(f"[SignalHandler][SERVER_CLOSE] Сервер закрыт: {server} [SUCCESS]")
        except Exception as e:
            logger.error(f"[SignalHandler][SERVER_CLOSE] Ошибка при закрытии сервера: {e} [FAIL]")
    
    logger.info("[SignalHandler][EXIT] Все ресурсы закрыты. Выход. [INFO]")
    sys.exit(0)

# Регистрация обработчика сигнала SIGINT
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# START_FUNCTION_main
# START_CONTRACT:
# PURPOSE: Главная функция для запуска мониторинга
# INPUTS:
# - Нет (аргументы передаются через sys.argv)
# OUTPUTS:
# - None - функция запускает Gradio приложение
# SIDE_EFFECTS:
# - Создает и запускает Gradio интерфейс
# - Логирует информацию о запуске в app.log
# KEYWORDS: [DOMAIN(9): CLI; CONCEPT(7): EntryPoint; TECH(6): Gradio]
# LINKS: [CALLS(8): GradioMonitorApp.run; IMPORTS(6): src.monitor.gradio_app]
# END_CONTRACT

def main() -> None:
    """
    Точка входа для запуска мониторинга.
    
    Описание:
        Парсирует аргументы командной строки, настраивает логирование
        и запускает Gradio мониторинг приложения.
    
    Аргументы командной строки:
        --port (int): Порт для Gradio (по умолчанию 7860)
        --share (bool): Создать публичную ссылку
        --server-name (str): Имя сервера (по умолчанию 127.0.0.1)
    """
    # START_BLOCK_CHECK_MODULES: [Проверка наличия скомпилированных модулей]
    logger.info(f"[TraceCheck][main][CHECK_MODULES] Проверка наличия скомпилированных модулей в lib/... [ATTEMPT]")
    
    if not check_compiled_modules():
        logger.warning("[TraceCheck][main][CHECK_MODULES] Скомпилированные модули не найдены! Запуск компиляции... [ATTEMPT]")
        
        # Импортируем функцию компиляции через importlib
        import importlib.util
        import sys
        
        # Загружаем модуль compilation.py динамически
        compilation_path = Path(__file__).parent / "compilation.py"
        spec = importlib.util.spec_from_file_location("compilation_module", compilation_path)
        compilation_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(compilation_module)
        
        compile_all_modules = compilation_module.compile_all_modules
        
        try:
            logger.info("[TraceCheck][main][COMPILATION] Запуск процесса компиляции... [ATTEMPT]")
            compile_all_modules()
            
            # BUG_FIX_CONTEXT: После компиляции рабочая директория оставалась в build/compilation,
            # которая могла быть удалена или недоступна. Возвращаемся в корень проекта.
            os.chdir(str(project_root))
            logger.info(f"[VarCheck][main][COMPILATION] Рабочая директория изменена на: {project_root} [SUCCESS]")
            
            logger.info("[TraceCheck][main][COMPILATION] Компиляция завершена [SUCCESS]")
            
            # Повторная проверка после компиляции
            if not check_compiled_modules():
                logger.error("[CriticalError][main][CHECK_MODULES] Модули отсутствуют после компиляции! [FAIL]")
                sys.exit(1)
                
        except Exception as e:
            logger.error(f"[CriticalError][main][COMPILATION] Ошибка при компиляции: {e} [FAIL]")
            raise
    else:
        logger.info("[TraceCheck][main][CHECK_MODULES] Скомпилированные модули найдены, пропуск компиляции [SUCCESS]")
    # END_BLOCK_CHECK_MODULES
    
    # START_BLOCK_CLEAR_LOG: [Очистка лога перед запуском]
    clear_infinite_loop_log()
    logger.info(f"[VarCheck][main][CLEAR_LOG] Лог очищен перед запуском [SUCCESS]")
    # END_BLOCK_CLEAR_LOG
    
    # START_BLOCK_PARSE_ARGS: [Парсинг аргументов командной строки]
    parser = argparse.ArgumentParser(description="Запуск мониторинга генератора кошельков")
    parser.add_argument("--port", type=int, default=7860, help="Порт для Gradio")
    parser.add_argument("--share", action="store_true", help="Создать публичную ссылку")
    parser.add_argument("--server-name", type=str, default="127.0.0.1", help="Имя сервера")
    
    args = parser.parse_args()
    
    logger.info(f"[VarCheck][main][PARSE_ARGS] Аргументы: port={args.port}, share={args.share}, server_name={args.server_name} [SUCCESS]")
    # END_BLOCK_PARSE_ARGS
    
    # START_BLOCK_LOG_STARTUP: [Логирование информации о запуске]
    logger.info("=" * 60)
    logger.info("WALLET.DAT.GENERATOR MONITOR")
    logger.info(f"Режим: модульная архитектура (v2.0.0)")
    logger.info("=" * 60)
    # END_BLOCK_LOG_STARTUP
    
    # START_BLOCK_CREATE_APP: [Создание и запуск приложения]
    global gradio_app_instance
    app = GradioMonitorApp(
        share=args.share,
        server_name=args.server_name,
        server_port=args.port,
    )
    gradio_app_instance = app
    
    try:
        logger.info(f"[TraceCheck][main][CREATE_APP] Запуск Gradio приложения на {args.server_name}:{args.port} [ATTEMPT]")
        app.run()
        logger.info(f"[TraceCheck][main][RUN_APP] Gradio приложение остановлено [SUCCESS]")
    except KeyboardInterrupt:
        logger.info("[TraceCheck][main][INTERRUPT] Получен сигнал прерывания (Ctrl+C) [INFO]")
    except Exception as e:
        logger.error(f"[CriticalError][main][RUN_APP] Критическая ошибка при запуске: {e} [FAIL]")
        raise
    finally:
        # Гарантированное закрытие ресурсов
        if gradio_app_instance is not None:
            try:
                logger.info("[TraceCheck][main][CLEANUP] Закрытие Gradio приложения в finally блоке... [ATTEMPT]")
                gradio_app_instance.close()
                logger.info("[TraceCheck][main][CLEANUP] Ресурсы освобождены [SUCCESS]")
            except Exception as e:
                logger.error(f"[Error][main][CLEANUP] Ошибка при закрытии ресурсов: {e} [FAIL]")
    # END_BLOCK_CREATE_APP

# END_FUNCTION_main

if __name__ == "__main__":
    main()
