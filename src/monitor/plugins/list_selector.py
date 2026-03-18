# FILE: src/monitor/plugins/list_selector.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Плагин выбора списка адресов для мониторинга. Предоставляет UI для выбора одного из двух доступных списков Bitcoin адресов.
# SCOPE: Этап 1 мониторинга, выбор списка адресов, сканирование файлов
# INPUT: Директория с адресами (adr_list/)
# OUTPUT: UI компоненты для выбора списка, путь к выбранному списку
# KEYWORDS: [DOMAIN(9): ListSelection; DOMAIN(7): FileScanner; TECH(7): Gradio; CONCEPT(6): FileIO]
# LINKS: [USES_API(8): src.monitor.plugins.base; USES_API(6): gradio; USES_API(5): pathlib]
# LINKS_TO_SPECIFICATION: [dev_plan_plugins_list_selector.md]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 10 [Плагин выбора списка адресов] => ListSelectorPlugin
# CONST 8 [Доступные списки адресов] => LIST_OPTIONS
# END_MODULE_MAP
# START_USE_CASES:
# - [ListSelectorPlugin]: User (StartMonitoring) -> SelectAddressList -> ListSelected
# - [initialize]: Plugin (Setup) -> ScanAndBuildUI -> ReadyToSelect
# - [get_selected_list]: System (GetListPath) -> ReturnSelectedPath -> PathReturned
# - [validate_selection]: System (Validation) -> CheckListAvailability -> ValidationResult
# END_USE_CASES
"""
Модуль plugins/list_selector.py — Этап 1: Выбор LIST.
Интерактивный выбор одного из двух списков адресов для поиска совпадений.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Импорт BaseMonitorPlugin - сначала пробуем C++ обёртку
try:
    from src.monitor._cpp.plugin_base_wrapper import BaseMonitorPlugin
except ImportError:
    from src.monitor.plugins.base import BaseMonitorPlugin

import gradio as gr

# Определяем путь к корню проекта для корректной работы с файлами
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# Настройка логирования с FileHandler для app.log
_logger = logging.getLogger(__name__)
if not _logger.handlers:
    _log_file = PROJECT_ROOT / "app.log"
    _file_handler = logging.FileHandler(_log_file, encoding="utf-8")
    _file_handler.setLevel(logging.DEBUG)
    _formatter = logging.Formatter(
        "[%(asctime)s][%(name)s][%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    _file_handler.setFormatter(_formatter)
    _logger.addHandler(_file_handler)
    _logger.setLevel(logging.DEBUG)

logger = _logger


# START_CONSTANTS_LIST_SELECTOR
LIST_OPTIONS = {
    "full_list.txt": {
        "path": "adr_list/full_list.txt",
        "description": "Полный список адресов Bitcoin",
        "size_label": "Полный",
    },
    "09.01.2009_16.09.2009.txt": {
        "path": "adr_list/09.01.2009_16.09.2009.txt",
        "description": "Адреса из диапазона дат (16 дней)",
        "size_label": "16 дней",
    },
}


# END_CONSTANTS_LIST_SELECTOR


# START_CLASS_LIST_SELECTOR_PLUGIN
# START_CONTRACT:
# PURPOSE: Плагин выбора списка адресов для мониторинга. Предоставляет UI для выбора одного из двух доступных списков.
# ATTRIBUTES:
# - Выбранный список => _selected_list: Optional[str]
# - Информация о списках => _list_info: Dict[str, Any]
# - Доступные списки => _available_lists: List[str]
# - Gradio компоненты => _gradio_components: Dict[str, Any]
# METHODS:
# - Инициализация => initialize(app)
# - Сканирование списков => _scan_available_lists()
# - Установка выбора => set_selected_list(list_name)
# - Валидация выбора => validate_selection()
# KEYWORDS: [DOMAIN(9): ListSelection; PATTERN(7): Plugin; TECH(7): Gradio]
# LINKS: [EXTENDS(8): BaseMonitorPlugin]
# END_CONTRACT
class ListSelectorPlugin(BaseMonitorPlugin):
    """
    Плагин выбора списка адресов для мониторинга.
    Предоставляет UI для выбора одного из двух доступных списков.
    """
    
    VERSION = "1.0.0"
    AUTHOR = "Wallet Generator Team"
    DESCRIPTION = "Плагин выбора списка адресов для мониторинга"
    
    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация плагина выбора списка
    # OUTPUTS: Инициализированный объект ListSelectorPlugin
    # SIDE_EFFECTS: Создаёт внутреннее состояние для хранения выбранного списка
    # KEYWORDS: [CONCEPT(5): Initialization]
    # END_CONTRACT
    def __init__(self) -> None:
        # Вызываем базовый конструктор без параметров
        super().__init__(name="list_selector")
        self._selected_list: Optional[str] = None
        self._list_info: Dict[str, Any] = {}
        self._available_lists: List[str] = []
        self._gradio_components: Dict[str, Any] = {}
        self.priority = 10  # Устанавливаем приоритет вручную
        logger.debug(f"[ListSelectorPlugin][INIT][ConditionCheck] Инициализирован плагин выбора списка")
    
    # END_METHOD___init__
    
    # START_METHOD_INITIALIZE
    # START_CONTRACT:
    # PURPOSE: Инициализация плагина и регистрация UI компонентов
    # INPUTS:
    # - app: Any — ссылка на главное приложение мониторинга
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Сканирует доступные списки адресов; регистрирует UI компоненты в главном приложении
    # KEYWORDS: [DOMAIN(8): PluginSetup; CONCEPT(6): Registration]
    # END_CONTRACT
    def initialize(self, app: Any) -> None:
        self._app = app
        
        # START_BLOCK_SCAN_AVAILABLE_LISTS: [Сканирование доступных списков адресов]
        self._scan_available_lists()
        # END_BLOCK_SCAN_AVAILABLE_LISTS
        
        # START_BLOCK_BUILD_UI: [Построение UI компонентов]
        self._build_ui_components()
        # END_BLOCK_BUILD_UI
        
        # START_BLOCK_REGISTER_IN_APP: [Регистрация в главном приложении]
        if hasattr(app, "register_stage"):
            app.register_stage(
                stage_id="list_selection",
                name="Выбор LIST",
                priority=self.priority,
                components=self._gradio_components,
                on_enter=self._on_enter_stage,
            )
        # END_BLOCK_REGISTER_IN_APP
        
        logger.info(f"[ListSelectorPlugin][INITIALIZE][StepComplete] Плагин инициализирован с {len(self._available_lists)} списками")
    
    # END_METHOD_INITIALIZE
    
    # START_METHOD_ON_METRIC_UPDATE
    # START_CONTRACT:
    # PURPOSE: Обработка обновления метрик (не используется на этом этапе)
    # INPUTS:
    # - metrics: Dict[str, Any] — словарь метрик
    # OUTPUTS: Нет
    # KEYWORDS: [DOMAIN(6): Placeholder]
    # END_CONTRACT
    def on_metric_update(self, metrics: Dict[str, Any]) -> None:
        pass
    
    # END_METHOD_ON_METRIC_UPDATE
    
    # START_METHOD_ON_SHUTDOWN
    # START_CONTRACT:
    # PURPOSE: Действия при завершении работы
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Логирует завершение работы плагина
    # KEYWORDS: [CONCEPT(8): Cleanup]
    # END_CONTRACT
    def on_shutdown(self) -> None:
        logger.info(f"[ListSelectorPlugin][ON_SHUTDOWN][StepComplete] Плагин выбора списка остановлен")
    
    # END_METHOD_ON_SHUTDOWN
    
    # START_METHOD_SCAN_AVAILABLE_LISTS
    # START_CONTRACT:
    # PURPOSE: Сканирование доступных списков адресов в директории adr_list
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Заполняет _available_lists найденными файлами; заполняет _list_info информацией о каждом списке
    # KEYWORDS: [DOMAIN(8): FileScanner; CONCEPT(6): Discovery]
    # END_CONTRACT
    def _scan_available_lists(self) -> None:
        adr_list_dir = PROJECT_ROOT / "adr_list"
        
        # START_BLOCK_CHECK_DIRECTORY: [Проверка существования директории]
        if not adr_list_dir.exists():
            logger.warning(f"[ListSelectorPlugin][SCAN_AVAILABLE_LISTS][ConditionCheck] Директория {adr_list_dir} не существует")
            # Используем предустановленные списки из конфига
            self._available_lists = list(LIST_OPTIONS.keys())
            for list_name in self._available_lists:
                self._list_info[list_name] = LIST_OPTIONS[list_name].copy()
            return
        # END_BLOCK_CHECK_DIRECTORY
        
        # START_BLOCK_SCAN_FILES: [Сканирование файлов]
        self._available_lists = []
        for list_name, list_config in LIST_OPTIONS.items():
            list_path = PROJECT_ROOT / list_config["path"]
            if list_path.exists():
                file_size = list_path.stat().st_size
                line_count = self._count_lines(list_path)
                
                self._available_lists.append(list_name)
                self._list_info[list_name] = {
                    "path": str(list_path),
                    "description": list_config["description"],
                    "size_label": list_config["size_label"],
                    "file_size": file_size,
                    "line_count": line_count,
                }
                logger.debug(f"[ListSelectorPlugin][SCAN_AVAILABLE_LISTS][Info] Найден: {list_name} ({line_count} строк)")
            else:
                logger.warning(f"[ListSelectorPlugin][SCAN_AVAILABLE_LISTS][ConditionCheck] Файл не найден: {list_path}")
        # END_BLOCK_SCAN_FILES
        
        logger.info(f"[ListSelectorPlugin][SCAN_AVAILABLE_LISTS][StepComplete] Найдено {len(self._available_lists)} доступных списков")
    
    # END_METHOD_SCAN_AVAILABLE_LISTS
    
    # START_METHOD_COUNT_LINES
    # START_CONTRACT:
    # PURPOSE: Подсчёт количества строк в файле
    # INPUTS:
    # - file_path: Path — путь к файлу
    # OUTPUTS: int — количество строк в файле
    # KEYWORDS: [CONCEPT(6): FileIO]
    # END_CONTRACT
    def _count_lines(self, file_path: Path) -> int:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
        except Exception as e:
            logger.warning(f"[ListSelectorPlugin][COUNT_LINES][ExceptionCaught] Ошибка подсчёта строк: {e}")
            return 0
    
    # END_METHOD_COUNT_LINES
    
    # START_METHOD_BUILD_UI_COMPONENTS
    # START_CONTRACT:
    # PURPOSE: Построение UI компонентов для выбора списка
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Создаёт Gradio-компоненты для выбора списка
    # KEYWORDS: [DOMAIN(8): UIComponents; TECH(7): Gradio]
    # END_CONTRACT
    def _build_ui_components(self) -> None:
        # START_BLOCK_CREATE_RADIO: [Создание компонента Radio для выбора]
        choices = []
        for list_name in self._available_lists:
            info = self._list_info.get(list_name, {})
            size_label = info.get("size_label", "Unknown")
            line_count = info.get("line_count", 0)
            choice_label = f"{size_label} ({line_count:,} адресов)"
            choices.append((choice_label, list_name))
        
        self._gradio_components["radio"] = gr.Radio(
            choices=choices,
            label="Выберите список адресов для поиска",
            value=self._available_lists[0] if self._available_lists else None,
            info="Выберите один из доступных списков адресов Bitcoin",
        )
        # END_BLOCK_CREATE_RADIO
        
        # START_BLOCK_CREATE_INFO_DISPLAY: [Создание компонента отображения информации]
        self._gradio_components["info_html"] = gr.HTML(
            value=self._generate_info_html(),
            label="Информация о выбранном списке",
        )
        # END_BLOCK_CREATE_INFO_DISPLAY
        
        # START_BLOCK_CREATE_CONFIRM_BUTTON: [Создание кнопки подтверждения]
        self._gradio_components["confirm_btn"] = gr.Button(
            value="Подтвердить выбор",
            variant="primary",
        )
        # END_BLOCK_CREATE_CONFIRM_BUTTON
        
        logger.debug(f"[ListSelectorPlugin][BUILD_UI_COMPONENTS][StepComplete] UI компоненты созданы")
    
    # END_METHOD_BUILD_UI_COMPONENTS
    
    # START_METHOD_GENERATE_INFO_HTML
    # START_CONTRACT:
    # PURPOSE: Генерация HTML с информацией о выбранном списке
    # INPUTS:
    # - selected_list: Optional[str] — имя выбранного списка
    # OUTPUTS: str — HTML-строка с информацией
    # KEYWORDS: [CONCEPT(6): HTML; TECH(5): Gradio]
    # END_CONTRACT
    def _generate_info_html(self, selected_list: Optional[str] = None) -> str:
        if not selected_list and self._available_lists:
            selected_list = self._available_lists[0]
        
        if not selected_list:
            return "<p style='color: #212121;'>Нет доступных списков</p>"
        
        info = self._list_info.get(selected_list, {})
        
        file_size_mb = info.get("file_size", 0) / (1024 * 1024)
        line_count = info.get("line_count", 0)
        description = info.get("description", "")
        
        html = f"""
        <div style="padding: 15px; background: #f0f0f0; border-radius: 8px; margin: 10px 0;">
            <h3 style="margin: 0 0 10px 0; color: #212121;">📋 {selected_list}</h3>
            <p style="margin: 5px 0; color: #212121;"><strong style="color: #212121;">Описание:</strong> {description}</p>
            <p style="margin: 5px 0; color: #212121;"><strong style="color: #212121;">Размер файла:</strong> {file_size_mb:.2f} MB</p>
            <p style="margin: 5px 0; color: #212121;"><strong style="color: #212121;">Количество адресов:</strong> {line_count:,}</p>
        </div>
        """
        return html
    
    # END_METHOD_GENERATE_INFO_HTML
    
    # START_METHOD_ON_ENTER_STAGE
    # START_CONTRACT:
    # PURPOSE: Обработчик входа на этап выбора списка
    # OUTPUTS: Нет
    # SIDE_EFFECTS: Логирует вход на этап; сбрасывает выбранный список
    # KEYWORDS: [CONCEPT(7): StageHandler]
    # END_CONTRACT
    def _on_enter_stage(self) -> None:
        logger.info(f"[ListSelectorPlugin][ON_ENTER_STAGE][StepComplete] Вход на этап выбора LIST")
        self._selected_list = None
    
    # END_METHOD_ON_ENTER_STAGE
    
    # START_METHOD_GET_SELECTED_LIST
    # START_CONTRACT:
    # PURPOSE: Получение выбранного списка адресов
    # OUTPUTS: Optional[str] — путь к выбранному списку или None
    # KEYWORDS: [CONCEPT(5): Getter]
    # END_CONTRACT
    def get_selected_list(self) -> Optional[str]:
        if self._selected_list:
            list_info = self._list_info.get(self._selected_list, {})
            return list_info.get("path")
        return None
    
    # END_METHOD_GET_SELECTED_LIST
    
    # START_METHOD_SET_SELECTED_LIST
    # START_CONTRACT:
    # PURPOSE: Установка выбранного списка
    # INPUTS:
    # - list_name: str — имя списка
    # OUTPUTS: bool — True если список установлен успешно
    # SIDE_EFFECTS: Обновляет _selected_list
    # KEYWORDS: [CONCEPT(6): Setter]
    # END_CONTRACT
    def set_selected_list(self, list_name: str) -> bool:
        if list_name in self._available_lists:
            self._selected_list = list_name
            logger.info(f"[ListSelectorPlugin][SET_SELECTED_LIST][StepComplete] Выбран список: {list_name}")
            return True
        else:
            logger.warning(f"[ListSelectorPlugin][SET_SELECTED_LIST][FAIL] Список не найден: {list_name}")
            return False
    
    # END_METHOD_SET_SELECTED_LIST
    
    # START_METHOD_GET_AVAILABLE_LISTS
    # START_CONTRACT:
    # PURPOSE: Получение списка доступных списков адресов
    # OUTPUTS: List[str] — список имён доступных списков
    # KEYWORDS: [CONCEPT(5): Getter]
    # END_CONTRACT
    def get_available_lists(self) -> List[str]:
        return self._available_lists.copy()
    
    # END_METHOD_GET_AVAILABLE_LISTS
    
    # START_METHOD_GET_LIST_INFO
    # START_CONTRACT:
    # PURPOSE: Получение информации о списке
    # INPUTS:
    # - list_name: str — имя списка
    # OUTPUTS: Optional[Dict[str, Any]] — информация о списке или None
    # KEYWORDS: [CONCEPT(5): Getter]
    # END_CONTRACT
    def get_list_info(self, list_name: str) -> Optional[Dict[str, Any]]:
        return self._list_info.get(list_name)
    
    # END_METHOD_GET_LIST_INFO
    
    # START_METHOD_GET_UI_COMPONENTS
    # START_CONTRACT:
    # PURPOSE: Получение UI компонентов плагина
    # OUTPUTS: Dict[str, Any] — словарь UI компонентов
    # KEYWORDS: [CONCEPT(5): Getter]
    # END_CONTRACT
    def get_ui_components(self) -> Dict[str, Any]:
        return self._gradio_components
    
    # END_METHOD_GET_UI_COMPONENTS
    
    # START_METHOD_VALIDATE_SELECTION
    # START_CONTRACT:
    # PURPOSE: Проверка корректности выбора списка
    # OUTPUTS: bool — True если выбор корректен
    # KEYWORDS: [DOMAIN(7): Validation; CONCEPT(6): Checking]
    # END_CONTRACT
    def validate_selection(self) -> bool:
        if not self._selected_list:
            logger.warning(f"[ListSelectorPlugin][VALIDATE_SELECTION][ConditionCheck] Список не выбран")
            return False
        
        if self._selected_list not in self._available_lists:
            logger.warning(f"[ListSelectorPlugin][VALIDATE_SELECTION][ConditionCheck] Выбранный список недоступен")
            return False
        
        list_info = self._list_info.get(self._selected_list, {})
        list_path = list_info.get("path")
        
        if not list_path or not Path(list_path).exists():
            logger.warning(f"[ListSelectorPlugin][VALIDATE_SELECTION][ConditionCheck] Файл списка не существует: {list_path}")
            return False
        
        logger.debug(f"[ListSelectorPlugin][VALIDATE_SELECTION][ConditionCheck] Выбор корректен: {self._selected_list}")
        return True
    
    # END_METHOD_VALIDATE_SELECTION
    
    # START_METHOD_GET_SELECTION_SUMMARY
    # START_CONTRACT:
    # PURPOSE: Получение текстовой сводки о выборе
    # OUTPUTS: str — текстовая сводка
    # KEYWORDS: [CONCEPT(6): Summary]
    # END_CONTRACT
    def get_selection_summary(self) -> str:
        if not self.validate_selection():
            return "Список не выбран или выбор некорректен"
        
        info = self._list_info.get(self._selected_list, {})
        return (
            f"Выбран список: {self._selected_list}\n"
            f"Путь: {info.get('path', 'N/A')}\n"
            f"Адресов: {info.get('line_count', 0):,}"
        )
    
    # END_METHOD_GET_SELECTION_SUMMARY

    # START_METHOD_GET_STATUS
    # START_CONTRACT:
    # PURPOSE: Получение статуса плагина
    # OUTPUTS: Dict[str, Any] - словарь со статусом
    # KEYWORDS: [CONCEPT(5): Status]
    # END_CONTRACT
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса плагина."""
        return {
            "name": self.name,
            "version": self.VERSION,
            "selected_list": self._selected_list,
            "available_lists": self._available_lists,
            "enabled": True,
        }
    
    # END_METHOD_GET_STATUS

    # START_METHOD_PROCESS_EVENT
    # START_CONTRACT:
    # PURPOSE: Обработка события
    # INPUTS:
    # - event_name: str - имя события
    # - event_data: Dict[str, Any] - данные события
    # OUTPUTS: Any - результат обработки
    # KEYWORDS: [CONCEPT(7): EventHandling]
    # END_CONTRACT
    def process_event(self, event_name: str, event_data: Dict[str, Any] = None) -> Any:
        """Обработка события."""
        logger.debug(f"[ListSelectorPlugin][PROCESS_EVENT] Event: {event_name}")
        return None
    
    # END_METHOD_PROCESS_EVENT

    # START_METHOD_SHUTDOWN
    # START_CONTRACT:
    # PURPOSE: Завершение работы плагина
    # OUTPUTS: Нет
    # KEYWORDS: [CONCEPT(8): Cleanup]
    # END_CONTRACT
    def shutdown(self) -> None:
        """Завершение работы плагина."""
        self.on_shutdown()
    
    # END_METHOD_SHUTDOWN


# END_CLASS_LIST_SELECTOR_PLUGIN
