# FILE: src/monitor/gradio_app.py
# VERSION: 2.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Главное Gradio-приложение мониторинга (Фасад). Управляет UI, жизненным циклом плагинов, маршрутизацией событий и этапами работы. Является фасадом для модульной архитектуры.
# SCOPE: мониторинг, UI, управление плагинами, Gradio-интерфейс
# INPUT: Параметры командной строки (порт, share, server_name)
# OUTPUT: Классы: GradioMonitorApp (фасад), PluginManager; Функции: main, create_gradio_app
# KEYWORDS: [DOMAIN(9): Gradio; DOMAIN(8): Monitoring; CONCEPT(7): Facade; TECH(6): UI]
# LINKS: [IMPORTS(8): app_core; IMPORTS(8): ui_builder; IMPORTS(7): event_handlers; USES(7): GradioMonitorAppCore]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 9 [Фасад приложения мониторинга] => GradioMonitorApp
# CLASS 8 [Менеджер плагинов] => PluginManager
# FUNC 9 [Фабрика для создания Gradio приложения] => create_gradio_app
# FUNC 5 [Очистка лог-файла infinite_loop.log] => clear_infinite_loop_log
# FUNC 5 [Точка входа для запуска] => main
# CONST 4 [Этап: Выбор списка] => STAGE_1
# CONST 4 [Этап: Генерация] => STAGE_2
# CONST 4 [Этап: Завершено] => STAGE_3
# CONST 4 [Этап: Ожидание] => STAGE_4
# END_MODULE_MAP
# START_USE_CASES:
# - [GradioMonitorApp]: User (Runtime) -> UseFacade -> ApplicationOrchestrated
# - [main]: User (CLI) -> LaunchGradioApp -> MonitoringUIAvailable
# - [create_gradio_app]: System (Factory) -> CreateApp -> AppInstanceReturned
# END_USE_CASES

"""
Модуль gradio_app.py — Главное Gradio приложение мониторинга (Фасад).
Является точкой входа и фасадом для модульной архитектуры.
Координирует работу UIBuilder, EventHandlerRegistry и GradioMonitorAppCore.
"""

# START_BLOCK_PROJECT_ROOT: [Добавление корня проекта в sys.path]
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
# END_BLOCK_PROJECT_ROOT

# START_BLOCK_IMPORT_MODULES: [Импорт необходимых модулей]
import logging
import os
from typing import Any, List, Optional

# Импорт новых модулей (модульная архитектура)
from src.monitor.app_core import GradioMonitorAppCore, PluginManager
from src.monitor.ui_builder import UIBuilder
from src.monitor.event_handlers import EventHandlerRegistry
from src.monitor.utils.html_generators import HTMLGenerator

# Импорт для совместимости
import gradio as gr

from src.monitor._cpp.plugin_base_wrapper import BaseMonitorPlugin

# Настройка логирования
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
logger.info(f"[InitModule][gradio_app][IMPORT_MODULES][StepComplete] Модуль загружен (модульная архитектура). app.log: {app_log_path} [SUCCESS]")
# END_BLOCK_IMPORT_MODULES


# START_CLASS_GradioMonitorApp
# START_CONTRACT:
# PURPOSE: Фасад приложения мониторинга. Координирует работу всех модулей: UIBuilder, EventHandlerRegistry и GradioMonitorAppCore.
# ATTRIBUTES:
# - _html_gen: HTMLGenerator — генератор HTML
# - _ui_builder: UIBuilder — строитель UI
# - _event_registry: EventHandlerRegistry — реестр обработчиков
# - _core: GradioMonitorAppCore — ядро приложения
# METHODS:
# - Инициализация => __init__
# - Запуск => run
# KEYWORDS: [PATTERN(9): Facade; DOMAIN(9): Gradio; CONCEPT(8): Coordination]
# END_CONTRACT

class GradioMonitorApp:
    """
    [Фасад приложения мониторинга. Координирует работу всех модулей.]
    """

    # Константы этапов работы (для совместимости)
    STAGE_1 = "SELECTING_LIST"
    STAGE_2 = "GENERATING"
    STAGE_3 = "FINISHED"
    STAGE_4 = "IDLE"

    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация фасада с созданием всех компонентов.
    # INPUTS:
    # - share: bool — создать публичную ссылку
    # - server_name: str — IP сервера
    # - server_port: int — порт сервера
    # KEYWORDS: [CONCEPT(6): Initialization; TECH(5): Facade]
    # END_CONTRACT

    def __init__(
        self,
        share: bool = False,
        server_name: str = "127.0.0.1",
        server_port: int = 7860,
    ) -> None:
        logger.info(f"[GradioMonitorApp][INIT][Info] Инициализация фасада")

        # Создание компонентов
        self._html_gen = HTMLGenerator()
        self._ui_builder = UIBuilder(self._html_gen)
        self._event_registry = EventHandlerRegistry()

        # Создание ядра приложения
        self._core = GradioMonitorAppCore(
            ui_builder=self._ui_builder,
            event_registry=self._event_registry,
            share=share,
            server_name=server_name,
            server_port=server_port,
        )

        # Инициализация EventHandlerRegistry
        self._event_registry.initialize(self._core, self._ui_builder)

        # Делегирование атрибутов для совместимости
        self.plugin_manager = self._core.plugin_manager
        self.metrics_store = self._core.metrics_store
        self.share = share
        self.server_name = server_name
        self.server_port = server_port

        logger.info(f"[GradioMonitorApp][INIT][ConditionCheck] Фасад инициализирован")

    # END_METHOD___init__

    # START_METHOD_run
    # START_CONTRACT:
    # PURPOSE: Запуск Gradio сервера мониторинга.
    # INPUTS: None
    # OUTPUTS: None
    # KEYWORDS: [PATTERN(9): Server; TECH(8): Gradio]
    # END_CONTRACT

    def run(self) -> None:
        """Запуск приложения."""
        self._core.run()

    # END_METHOD_run


# END_CLASS_GradioMonitorApp


# START_FUNCTION_clear_infinite_loop_log
# START_CONTRACT:
# PURPOSE: Очистка лог-файла infinite_loop.log перед запуском приложения.
#          Предотвращает накопление данных (173MB+) и освобождает место на диске.
# INPUTS: None
# OUTPUTS: None
# SIDE_EFFECTS:
# - Очищает содержимое файла logs/infinite_loop.log
# - Создает директорию logs/ если она не существует
# - Логирует результат операции
# TEST_CONDITIONS_SUCCESS_CRITERIA:
# - Файл существует и очищен: логируется INFO
# - Файл не существует: логируется DEBUG, продолжаем работу
# - Ошибка доступа: логируется WARNING, продолжаем работу
# KEYWORDS: [DOMAIN(8): Logging; CONCEPT(7): Cleanup; TECH(6): FileIO]
# LINKS: [ACCESSES_FILE(9): logs/infinite_loop.log; CALLS_FROM(8): main]
# END_CONTRACT

def clear_infinite_loop_log() -> None:
    """
    [Очистка лог-файла infinite_loop.log перед запуском приложения.]
    
    Использует truncate-метод для безопасной очистки файла без удаления.
    Обрабатывает случаи отсутствия файла, директории и проблем с правами доступа.
    """
    # START_BLOCK_DEFINE_PATH: [Определение пути к лог-файлу]
    project_root = Path(__file__).resolve().parent.parent.parent
    log_dir = project_root / "logs"
    log_file = log_dir / "infinite_loop.log"
    
    logger.debug(f"[clear_infinite_loop_log][DEFINE_PATH] Путь к лог-файлу: {log_file} [ATTEMPT]")
    # END_BLOCK_DEFINE_PATH
    
    # START_BLOCK_ENSURE_DIRECTORY: [Создание директории logs/ если необходимо]
    if not log_dir.exists():
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"[clear_infinite_loop_log][ENSURE_DIRECTORY] Создана директория: {log_dir} [SUCCESS]")
        except OSError as e:
            logger.warning(f"[clear_infinite_loop_log][ENSURE_DIRECTORY] Не удалось создать директорию: {e} [FAIL]")
            return
    # END_BLOCK_ENSURE_DIRECTORY
    
    # START_BLOCK_CHECK_FILE: [Проверка существования файла]
    if not log_file.exists():
        logger.debug(f"[clear_infinite_loop_log][CHECK_FILE] Файл не существует: {log_file} [INFO]")
        return
    
    # Получаем размер файла перед очисткой для логирования
    try:
        file_size = log_file.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        logger.info(f"[clear_infinite_loop_log][CHECK_FILE] Размер файла перед очисткой: {file_size_mb:.2f} MB [VALUE]")
    except OSError as e:
        logger.warning(f"[clear_infinite_loop_log][CHECK_FILE] Не удалось получить размер файла: {e} [FAIL]")
        file_size_mb = 0
    # END_BLOCK_CHECK_FILE
    
    # START_BLOCK_TRUNCATE_FILE: [Очистка файла методом truncate]
    try:
        # Используем 'w' mode для truncate (очистки содержимого)
        with open(log_file, 'w', encoding='utf-8') as f:
            pass  # Просто открываем в режиме записи - это очищает файл
        
        logger.info(f"[clear_infinite_loop_log][TRUNCATE_FILE] Файл успешно очищен. Освобождено: {file_size_mb:.2f} MB [SUCCESS]")
        
    except PermissionError as e:
        # Файл может быть занят другим процессом (например, запущенным генератором)
        logger.warning(f"[clear_infinite_loop_log][TRUNCATE_FILE] Нет доступа к файлу (возможно, занят): {e} [FAIL]")
        
    except OSError as e:
        # Другие ошибки ввода-вывода
        logger.error(f"[clear_infinite_loop_log][TRUNCATE_FILE] Ошибка при очистке файла: {e} [ERROR_STATE]")
        
    # END_BLOCK_TRUNCATE_FILE

# END_FUNCTION_clear_infinite_loop_log


# START_FUNCTION_main
# START_CONTRACT:
# PURPOSE: Главная функция точки входа для запуска Gradio мониторинга.
#          Теперь включает очистку infinite_loop.log перед запуском.
# INPUTS: Нет (аргументы через sys.argv)
# OUTPUTS: None (блокирующий вызов)
# KEYWORDS: [PATTERN(8): CLI_Entry; DOMAIN(7): CommandLine; CONCEPT(6): Cleanup]
# END_CONTRACT

def main() -> None:
    """Главная функция для запуска мониторинга."""
    
    # START_BLOCK_CLEAR_LOGS_ON_STARTUP: [Очистка infinite_loop.log перед запуском]
    # Вызываем очистку ДО создания логгеров и парсеров аргументов
    # для освобождения места и предотвращения накопления данных
    clear_infinite_loop_log()
    # END_BLOCK_CLEAR_LOGS_ON_STARTUP
    
    import argparse

    parser = argparse.ArgumentParser(description="Запуск мониторинга генератора кошельков")
    parser.add_argument("--port", type=int, default=7860, help="Порт для Gradio")
    # parser.add_argument("--share", action="store_true", help="Создать публичную ссылку")  # Закомментировано: убрать кнопку "использовать через api"
    parser.add_argument("--server-name", type=str, default="127.0.0.1", help="Имя сервера")

    args = parser.parse_args()

    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(app_log_path),
        ],
    )

    logger.info("=" * 60)
    logger.info("WALLET.DAT.GENERATOR MONITOR")
    logger.info(f"Режим: модульная архитектура (v2.0.0)")
    logger.info("=" * 60)

    # Создание и запуск приложения
    app = GradioMonitorApp(
        share=False,              # Закомментировано: убрать возможность создать публичную ссылку
        server_name=args.server_name,
        server_port=args.port,
    )

    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise


# END_FUNCTION_main


# START_FUNCTION_CREATE_GRADIO_APP
# START_CONTRACT:
# PURPOSE: Фабричная функция для создания Gradio мониторинг приложения.
# INPUTS:
# - share: bool — создать публичную ссылку
# - server_name: str — IP сервера
# - server_port: int — порт сервера
# - theme: Optional[Any] — тема Gradio (не используется, для совместимости)
# - plugins: Optional[List[BaseMonitorPlugin]] — кастомные плагины
# OUTPUTS:
# - GradioMonitorApp — созданное приложение
# KEYWORDS: [PATTERN(7): Factory; DOMAIN(9): Gradio]
# END_CONTRACT

def create_gradio_app(
    share: bool = False,
    server_name: str = "127.0.0.1",
    server_port: int = 7860,
    theme: Optional[Any] = None,
    plugins: Optional[List[BaseMonitorPlugin]] = None,
) -> GradioMonitorApp:
    """
    Фабричная функция для создания Gradio мониторинг приложения.

    Пример использования:
        app = create_gradio_app(server_port=7860)
        app.run()
    """
    logger.debug(f"[create_gradio_app][InputParams] share={share}, server_port={server_port} [ATTEMPT]")

    # Создание приложения
    app = GradioMonitorApp(
        share=share,
        server_name=server_name,
        server_port=server_port,
    )

    # Регистрация кастомных плагинов
    if plugins:
        for plugin in plugins:
            app.plugin_manager.register_plugin(plugin)
        logger.info(f"[create_gradio_app][RegisterPlugins] Зарегистрировано {len(plugins)} кастомных плагинов")

    logger.info(f"[create_gradio_app][ReturnData] Приложение создано [SUCCESS]")

    return app


# END_FUNCTION_CREATE_GRADIO_APP


if __name__ == "__main__":
    main()
