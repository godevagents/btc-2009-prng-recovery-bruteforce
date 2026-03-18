# FILE: src/monitor/ui/themes.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Модуль тем оформления Gradio. Определяет и предоставляет темы для Gradio-интерфейса мониторинга, включая стандартные и кастомные CSS-стили.
# SCOPE: Темы оформления, Gradio Themes, CSS-стили
# INPUT: Нет (модуль предоставляет функции и классы)
# OUTPUT: Gradio темы (gr.themes.Soft, gr.themes.Dark, gr.themes.Base), CSS-строки, класс реестра тем
# KEYWORDS: DOMAIN(9): UI Themes; DOMAIN(8): Gradio; DOMAIN(7): CSS Styles; CONCEPT(6): Theme Registry; TECH(5): Python
# LINKS: [USES(7): gradio]
# LINKS_TO_SPECIFICATION: Требования к темам из dev_plan_ui_themes.md
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# FUNC 10 [Возвращает стандартную тему мониторинга Soft] => get_monitor_theme
# FUNC 9 [Возвращает тёмную тему Dark] => get_dark_theme
# FUNC 8 [Создаёт кастомную тему с указанными цветами] => get_custom_theme
# CLASS 9 [Реестр для управления темами] => ThemeRegistry
# METHOD 9 [Регистрирует новую тему в реестре] => ThemeRegistry.register
# METHOD 8 [Получает тему по имени] => ThemeRegistry.get
# METHOD 7 [Список доступных тем] => ThemeRegistry.list_themes
# FUNC 8 [Получает тему по имени из реестра] => get_theme
# FUNC 7 [Возвращает список доступных тем] => list_available_themes
# FUNC 7 [Возвращает опции тем для dropdown] => get_theme_options
# CLASS 8 [CSS-стили для мониторинга] => CSSStyles
# STATIC_METHOD 8 [Возвращает кастомные CSS стили] => CSSStyles.get_custom_css
# STATIC_METHOD 7 [Возвращает CSS анимации] => CSSStyles.get_animated_css
# FUNC 8 [Объединяет все CSS стили] => get_all_css
# FUNC 7 [Получает тему с кастомным CSS] => get_theme_with_custom_css
# END_MODULE_MAP
# START_USE_CASES:
# - [get_monitor_theme]: MonitorApp (Startup) -> ApplyDefaultTheme -> ThemeApplied
# - [get_dark_theme]: MonitorApp (Runtime) -> SwitchToDarkTheme -> DarkThemeApplied
# - [get_theme]: MonitorApp (Runtime) -> SelectTheme -> ThemeChanged
# - [ThemeRegistry.register]: Admin (Setup) -> RegisterCustomTheme -> ThemeAvailable
# - [get_all_css]: MonitorApp (Startup) -> ApplyCustomStyles -> StylesApplied
# END_USE_CASES
# За описанием заголовка идет секция импорта

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import gradio as gr

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
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger

logger = _setup_logger()
logger.debug(f"[ModuleInit][ui/themes][SetupLogger] Логгер модуля themes инициализирован [SUCCESS]")


# START_FUNCTION_GET_MONITOR_THEME
# START_CONTRACT:
# PURPOSE: Создаёт и возвращает стандартную тему мониторинга на основе Gradio Soft theme с настроенными цветами и размерами.
# INPUTS: Нет
# OUTPUTS:
# - gr.themes.Soft — настроенная тема Soft
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Themes; PATTERN(7): Gradio; TECH(6): Soft; CONCEPT(5): Default Theme
# LINKS: [CALLS(5): None]
# END_CONTRACT

def get_monitor_theme() -> gr.themes.Soft:
    """
    Получение стандартной темы мониторинга (Soft theme).
    
    Примечание: В gradio 4.0+ изменились параметры метода set().
    - primary_color -> color_accent
    - secondary_color -> удалён
    """
    logger.debug(f"[get_monitor_theme][InputParams] Нет входных параметров [ATTEMPT]")
    
    # START_BLOCK_CREATE_THEME: [Создание темы Soft]
    theme = gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="gray",
    )
    # END_BLOCK_CREATE_THEME
    
    # START_BLOCK_CONFIGURE_THEME: [Настройка цветов темы]
    # Обновлённые параметры для gradio 4.0+
    theme.set(
        # Основные цвета
        color_accent="#2196F3",
        background_fill_primary="#FFFFFF",
        background_fill_secondary="#F5F5F5",
        
        # Цвета текста
        body_text_color="#212121",
        body_text_color_subdued="#757575",
        
        # Цвета кнопок
        button_primary_background_fill="#2196F3",
        button_primary_background_fill_hover="#1976D2",
        button_primary_text_color="#FFFFFF",
        
        button_secondary_background_fill="#E0E0E0",
        button_secondary_background_fill_hover="#BDBDBD",
        
        # Границы и тени
        border_color_primary="#E0E0E0",
        shadow_drop_lg="0 4px 6px rgba(0, 0, 0, 0.1)",
        
        # Радиусы
        button_large_radius="8px",
        button_small_radius="6px",
        input_radius="8px",
    )
    # END_BLOCK_CONFIGURE_THEME
    
    logger.debug(f"[get_monitor_theme][ReturnData] Тема Soft создана [SUCCESS]")
    
    return theme


# END_FUNCTION_GET_MONITOR_THEME


# START_FUNCTION_GET_DARK_THEME
# START_CONTRACT:
# PURPOSE: Создаёт и возвращает тёмную тему мониторинга на основе Gradio Base theme для использования в ночное время.
# INPUTS: Нет
# OUTPUTS:
# - gr.themes.Base — тёмная тема
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Themes; PATTERN(7): Gradio; TECH(6): Dark; CONCEPT(5): Night Mode
# LINKS: [CALLS(5): None]
# END_CONTRACT

def get_dark_theme() -> gr.themes.Base:
    """
    Получение тёмной темы для ночного режима.
    
    Примечание: В gradio 4.0+ класс gr.themes.Dark был удалён.
    Используем gr.themes.Base с настроенными цветами для тёмной темы.
    - primary_color -> color_accent
    - secondary_color -> удалён
    """
    logger.debug(f"[get_dark_theme][InputParams] Нет входных параметров [ATTEMPT]")
    
    # START_BLOCK_CREATE_THEME: [Создание тёмной темы на основе Base]
    # В gradio 4.0+ нет gr.themes.Dark, используем Base с кастомными настройками
    theme = gr.themes.Base(
        primary_hue="blue",
    )
    # END_BLOCK_CREATE_THEME
    
    # START_BLOCK_CONFIGURE_THEME: [Настройка цветов тёмной темы]
    # Обновлённые параметры для gradio 4.0+
    theme.set(
        color_accent="#2196F3",
        background_fill_primary="#121212",
        background_fill_primary_dark="#121212",
        background_fill_secondary="#1E1E1E",
        background_fill_secondary_dark="#1E1E1E",
        body_text_color="#E0E0E0",
        body_text_color_dark="#E0E0E0",
        body_text_color_subdued="#9E9E9E",
        body_text_color_subdued_dark="#9E9E9E",
        border_color_primary="#333333",
        border_color_primary_dark="#333333",
    )
    # END_BLOCK_CONFIGURE_THEME
    
    logger.debug(f"[get_dark_theme][ReturnData] Тёмная тема создана [SUCCESS]")
    
    return theme


# END_FUNCTION_GET_DARK_THEME


# START_FUNCTION_GET_CUSTOM_THEME
# START_CONTRACT:
# PURPOSE: Создаёт кастомную тему с указанными пользователем цветами для брендирования или персонализации интерфейса.
# INPUTS:
# - primary_color: str — основной цвет в HEX-формате
# - background_color: str — цвет фона в HEX-формате
# - text_color: str — цвет текста в HEX-формате
# - accent_color: str — акцентный цвет в HEX-формате
# OUTPUTS:
# - gr.themes.Base — кастомная тема
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Themes; PATTERN(7): Custom; TECH(6): Branding; CONCEPT(5): Personalization
# LINKS: [CALLS(5): None]
# END_CONTRACT

def get_custom_theme(
    primary_color: str = "#2196F3",
    background_color: str = "#FFFFFF",
    text_color: str = "#212121",
    accent_color: str = "#FF5722",
) -> gr.themes.Base:
    """
    Создание кастомной темы с указанными цветами.
    
    Примечание: В gradio 4.0+ изменились параметры:
    - primary_color -> color_accent
    - accent_color -> удалён (используется color_accent)
    """
    logger.debug(f"[get_custom_theme][InputParams] primary={primary_color}, bg={background_color} [ATTEMPT]")
    
    # START_BLOCK_CREATE_THEME: [Создание базовой кастомной темы]
    theme = gr.themes.Base(
        primary_hue="blue",
    )
    # END_BLOCK_CREATE_THEME
    
    # START_BLOCK_CONFIGURE_THEME: [Настройка кастомных цветов]
    # Обновлённые параметры для gradio 4.0+
    theme.set(
        color_accent=primary_color,
        background_fill_primary=background_color,
        background_fill_secondary=f"{background_color}F5",
        body_text_color=text_color,
    )
    # END_BLOCK_CONFIGURE_THEME
    
    logger.debug(f"[get_custom_theme][ReturnData] Кастомная тема создана: primary={primary_color} [SUCCESS]")
    
    return theme


# END_FUNCTION_GET_CUSTOM_THEME


# START_THEME_REGISTRY
# START_CONTRACT:
# PURPOSE: Класс реестра для управления доступными темами. Позволяет регистрировать, получать и перечислять темы по имени.
# ATTRIBUTES:
# - _themes: Dict[str, gr.themes.Base] — словарь зарегистрированных тем
# METHODS:
# - _register_default_themes(): Регистрирует стандартные темы при инициализации
# - register(name: str, theme: gr.themes.Base): Регистрирует новую тему
# - get(name: str): Получает тему по имени
# - list_themes(): Возвращает список доступных тем
# KEYWORDS: DOMAIN(9): UI Themes; PATTERN(8): Registry; TECH(5): Singleton; CONCEPT(5): Theme Management
# LINKS: [CALLS(7): get_monitor_theme; CALLS(7): get_dark_theme]
# END_CONTRACT

class ThemeRegistry:
    """
    Реестр доступных тем для управления ими.
    """
    
    # START_METHOD___INIT__
    # START_CONTRACT:
    # PURPOSE: Инициализирует реестр тем и регистрирует стандартные темы.
    # KEYWORDS: CONCEPT(5): Initialization; DOMAIN(7): Registry
    # END_CONTRACT
    def __init__(self) -> None:
        """Инициализация реестра тем."""
        logger.debug(f"[ThemeRegistry][INIT][InputParams] Нет параметров [ATTEMPT]")
        
        self._themes: Dict[str, gr.themes.Base] = {}
        self._register_default_themes()
        
        logger.debug(f"[ThemeRegistry][INIT][ConditionCheck] Реестр тем инициализирован [SUCCESS]")
    
    # END_METHOD___INIT__
    
    # START_METHOD_REGISTER_DEFAULT_THEMES
    # START_CONTRACT:
    # PURPOSE: Регистрирует стандартные темы (soft, dark, default) при создании реестра.
    # KEYWORDS: CONCEPT(5): Registration; DOMAIN(7): Themes
    # END_CONTRACT
    def _register_default_themes(self) -> None:
        """Регистрация стандартных тем."""
        logger.debug(f"[ThemeRegistry][RegisterDefaults][InputParams] Регистрация стандартных тем [ATTEMPT]")
        
        self.register("soft", get_monitor_theme())
        self.register("dark", get_dark_theme())
        self.register("default", get_monitor_theme())
        
        logger.debug(f"[ThemeRegistry][RegisterDefaults][StepComplete] Стандартные темы зарегистрированы [SUCCESS]")
    
    # END_METHOD_REGISTER_DEFAULT_THEMES
    
    # START_METHOD_REGISTER
    # START_CONTRACT:
    # PURPOSE: Регистрирует новую тему в реестре под указанным именем для последующего использования.
    # INPUTS:
    # - name: str — имя темы для регистрации
    # - theme: gr.themes.Base — объект темы Gradio
    # OUTPUTS: Нет
    # KEYWORDS: CONCEPT(5): Registration; DOMAIN(7): Themes; TECH(5): Storage
    # END_CONTRACT
    def register(self, name: str, theme: gr.themes.Base) -> None:
        """Регистрация темы в реестре."""
        logger.debug(f"[ThemeRegistry][Register][InputParams] name={name} [ATTEMPT]")
        
        self._themes[name] = theme
        
        logger.debug(f"[ThemeRegistry][Register][StepComplete] Тема зарегистрирована: {name} [SUCCESS]")
    
    # END_METHOD_REGISTER
    
    # START_METHOD_GET
    # START_CONTRACT:
    # PURPOSE: Получает тему по имени из реестра или возвращает None если тема не найдена.
    # INPUTS:
    # - name: str — имя темы для получения
    # OUTPUTS:
    # - Optional[gr.themes.Base] — тема или None
    # KEYWORDS: CONCEPT(5): Retrieval; DOMAIN(7): Themes
    # END_CONTRACT
    def get(self, name: str) -> Optional[gr.themes.Base]:
        """Получение темы по имени."""
        logger.debug(f"[ThemeRegistry][Get][InputParams] name={name} [ATTEMPT]")
        
        theme = self._themes.get(name)
        
        if not theme:
            logger.warning(f"[ThemeRegistry][Get][ConditionCheck] Тема не найдена: {name} [FAIL]")
        else:
            logger.debug(f"[ThemeRegistry][Get][ReturnData] Тема найдена: {name} [SUCCESS]")
        
        return theme
    
    # END_METHOD_GET
    
    # START_METHOD_LIST_THEMES
    # START_CONTRACT:
    # PURPOSE: Возвращает список всех зарегистрированных в реестре имён тем.
    # OUTPUTS:
    # - list — список имён тем
    # KEYWORDS: CONCEPT(5): Enumeration; DOMAIN(7): Themes
    # END_CONTRACT
    def list_themes(self) -> list:
        """Получение списка доступных тем."""
        logger.debug(f"[ThemeRegistry][ListThemes][InputParams] Нет параметров [ATTEMPT]")
        
        result = list(self._themes.keys())
        
        logger.debug(f"[ThemeRegistry][ListThemes][ReturnData] Найдено тем: {len(result)} [SUCCESS]")
        
        return result
    
    # END_METHOD_LIST_THEMES


# END_THEME_REGISTRY


# Глобальный экземпляр реестра
_theme_registry = ThemeRegistry()
logger.debug(f"[ModuleInit][ui/themes][CreateRegistry] Глобальный реестр тем создан [SUCCESS]")


# START_FUNCTION_GET_THEME
# START_CONTRACT:
# PURPOSE: Получает тему по имени из глобального реестра или возвращает стандартную тему мониторинга если имя не найдено.
# INPUTS:
# - name: str — имя темы для получения
# OUTPUTS:
# - gr.themes.Base — тема из реестра или стандартная
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Themes; PATTERN(7): Registry; TECH(5): Lookup; CONCEPT(5): Fallback
# LINKS: [CALLS(8): _theme_registry.get; CALLS(8): get_monitor_theme]
# END_CONTRACT

def get_theme(name: str = "soft") -> gr.themes.Base:
    """
    Получение темы по имени из реестра.
    """
    logger.debug(f"[get_theme][InputParams] name={name} [ATTEMPT]")
    
    # START_BLOCK_LOOKUP_THEME: [Поиск темы в реестре]
    theme = _theme_registry.get(name)
    # END_BLOCK_LOOKUP_THEME
    
    if theme is None:
        logger.warning(f"[get_theme][Fallback] Тема {name} не найдена, используем default [FAIL]")
        return get_monitor_theme()
    
    logger.debug(f"[get_theme][ReturnData] Тема получена: {name} [SUCCESS]")
    
    return theme


# END_FUNCTION_GET_THEME


# START_FUNCTION_LIST_AVAILABLE_THEMES
# START_CONTRACT:
# PURPOSE: Возвращает список всех доступных тем из глобального реестра для отображения пользователю.
# OUTPUTS:
# - list — список имён доступных тем
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Themes; PATTERN(7): Registry; CONCEPT(5): Enumeration
# LINKS: [CALLS(8): _theme_registry.list_themes]
# END_CONTRACT

def list_available_themes() -> list:
    """
    Получение списка доступных тем.
    """
    logger.debug(f"[list_available_themes][InputParams] Нет параметров [ATTEMPT]")
    
    result = _theme_registry.list_themes()
    
    logger.debug(f"[list_available_themes][ReturnData] Доступно тем: {len(result)} [SUCCESS]")
    
    return result


# END_FUNCTION_LIST_AVAILABLE_THEMES


# START_FUNCTION_GET_THEME_OPTIONS
# START_CONTRACT:
# PURPOSE: Возвращает список опций тем в формате для Gradio Dropdown (кортежи (label, value)).
# OUTPUTS:
# - list — список кортежей (название, значение) для dropdown
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Themes; PATTERN(7): Dropdown; CONCEPT(5): Options
# LINKS: [CALLS(8): _theme_registry.list_themes]
# END_CONTRACT

def get_theme_options() -> list:
    """
    Получение списка опций для выбора темы.
    """
    logger.debug(f"[get_theme_options][InputParams] Нет параметров [ATTEMPT]")
    
    themes = _theme_registry.list_themes()
    result = [(t.capitalize(), t) for t in themes]
    
    logger.debug(f"[get_theme_options][ReturnData] Опций для dropdown: {len(result)} [SUCCESS]")
    
    return result


# END_FUNCTION_GET_THEME_OPTIONS


# START_CLASS_CSS_STYLES
# START_CONTRACT:
# PURPOSE: Класс для управления кастомными CSS-стилями для мониторинга. Предоставляет методы для получения основных стилей и анимаций.
# ATTRIBUTES: Нет
# METHODS:
# - get_custom_css(): Возвращает основные CSS стили для мониторинга
# - get_animated_css(): Возвращает CSS анимации
# KEYWORDS: DOMAIN(9): UI Themes; PATTERN(8): CSS; TECH(5): Styling; CONCEPT(5): Custom Styles
# LINKS: [CALLS(5): None]
# END_CONTRACT

class CSSStyles:
    """
    Кастомные CSS стили для мониторинга.
    """
    
    # START_STATIC_METHOD_GET_CUSTOM_CSS
    # START_CONTRACT:
    # PURPOSE: Возвращает строку с кастомными CSS-стилями для карточек, алертов, прогресс-баров, кнопок и других элементов мониторинга.
    # OUTPUTS:
    # - str — CSS-стили
    # KEYWORDS: DOMAIN(9): UI Themes; PATTERN(7): CSS; CONCEPT(5): Custom Styles
    # END_CONTRACT
    @staticmethod
    def get_custom_css() -> str:
        """Получение кастомных CSS стилей."""
        logger.debug(f"[CSSStyles][GetCustomCSS][InputParams] Нет параметров [ATTEMPT]")
        
        result = """
        /* Основные стили */
        .monitor-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            color: white;
        }
        
        /* Gradio HTML компоненты с тёмным текстом на светлом фоне */
        .gradio-container .prose {
            color: #212121 !important;
        }
        
        .gradio-html p {
            color: #212121 !important;
        }
        
        .gradio-html h1, .gradio-html h2, .gradio-html h3, .gradio-html h4 {
            color: #212121 !important;
        }
        
        /* Карточки статистики */
        .stats-card {
            padding: 15px;
            border-left: 4px solid;
            border-radius: 8px;
            margin: 5px;
            transition: transform 0.2s;
        }
        
        .stats-card:hover {
            transform: translateY(-2px);
        }
        
        /* Стили для метрик */
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #212121;
        }
        
        .metric-label {
            font-size: 12px;
            color: #666;
        }
        
        /* Стили для alerts */
        .alert-info {
            background: #E3F2FD;
            border-left: 4px solid #2196F3;
        }
        
        .alert-success {
            background: #E8F5E9;
            border-left: 4px solid #4CAF50;
        }
        
        .alert-warning {
            background: #FFF3E0;
            border-left: 4px solid #FF9800;
        }
        
        .alert-error {
            background: #FFEBEE;
            border-left: 4px solid #F44336;
        }
        
        /* Прогресс бар */
        .progress-container {
            width: 100%;
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
        }
        
        .progress-bar {
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        
        /* Анимация загрузки */
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .loading-spinner {
            animation: spin 1s linear infinite;
        }
        
        /* Стили для вкладок */
        .tab-header {
            font-weight: bold;
            padding: 10px;
        }
        
        /* Стили для кнопок */
        .btn-primary {
            background: #2196F3;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
        }
        
        .btn-primary:hover {
            background: #1976D2;
        }
        
        /* Стили для логов */
        .log-container {
            background: #1E1E1E;
            color: #E0E0E0;
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .log-entry {
            margin: 5px 0;
            padding: 3px;
        }
        
        .log-entry.error {
            color: #F44336;
        }
        
        .log-entry.warning {
            color: #FF9800;
        }
        
        .log-entry.info {
            color: #2196F3;
        }
        
        /* Стили для сетки */
        .grid-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            padding: 10px;
        }
        
        /* Адаптивные стили */
        @media (max-width: 768px) {
            .grid-container {
                grid-template-columns: 1fr;
            }
        }
        """
        
        logger.debug(f"[CSSStyles][GetCustomCSS][ReturnData] CSS стили получены, длина={len(result)} [SUCCESS]")
        
        return result
    
    # END_STATIC_METHOD_GET_CUSTOM_CSS
    
    # START_STATIC_METHOD_GET_ANIMATED_CSS
    # START_CONTRACT:
    # PURPOSE: Возвращает CSS-анимации для fadeIn, slideIn и pulse эффектов.
    # OUTPUTS:
    # - str — CSS анимации
    # KEYWORDS: DOMAIN(9): UI Themes; PATTERN(7): Animation; CONCEPT(5): CSS
    # END_CONTRACT
    @staticmethod
    def get_animated_css() -> str:
        """Получение CSS анимаций."""
        logger.debug(f"[CSSStyles][GetAnimatedCSS][InputParams] Нет параметров [ATTEMPT]")
        
        result = """
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes slideIn {
            from { transform: translateY(-20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .animate-fade-in {
            animation: fadeIn 0.3s ease-in;
        }
        
        .animate-slide-in {
            animation: slideIn 0.3s ease-out;
        }
        
        .animate-pulse {
            animation: pulse 2s infinite;
        }
        """
        
        logger.debug(f"[CSSStyles][GetAnimatedCSS][ReturnData] Анимации получены, длина={len(result)} [SUCCESS]")
        
        return result
    
    # END_STATIC_METHOD_GET_ANIMATED_CSS


# END_CLASS_CSS_STYLES


# START_FUNCTION_GET_ALL_CSS
# START_CONTRACT:
# PURPOSE: Объединяет основные CSS-стили и анимации в одну строку для применения к Gradio-интерфейсу.
# OUTPUTS:
# - str — объединённые CSS стили
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Themes; PATTERN(7): CSS; CONCEPT(5): Aggregation
# LINKS: [CALLS(8): CSSStyles.get_custom_css; CALLS(8): CSSStyles.get_animated_css]
# END_CONTRACT

def get_all_css() -> str:
    """Получение всех CSS стилей."""
    logger.debug(f"[get_all_css][InputParams] Нет параметров [ATTEMPT]")
    
    # START_BLOCK_COMBINE_CSS: [Объединение CSS]
    result = CSSStyles.get_custom_css() + "\n" + CSSStyles.get_animated_css()
    # END_BLOCK_COMBINE_CSS
    
    logger.debug(f"[get_all_css][ReturnData] Объединённые CSS, длина={len(result)} [SUCCESS]")
    
    return result


# END_FUNCTION_GET_ALL_CSS


# START_FUNCTION_GET_THEME_WITH_CUSTOM_CSS
# START_CONTRACT:
# PURPOSE: Возвращает тему вместе с кастомным CSS для применения к Gradio-интерфейсу. Может добавлять дополнительный CSS.
# INPUTS:
# - theme_name: str — имя темы для получения
# - additional_css: Optional[str] — дополнительный CSS для добавления
# OUTPUTS:
# - Tuple[gr.themes.Base, str] — кортеж (тема, CSS)
# SIDE_EFFECTS: Нет
# KEYWORDS: DOMAIN(9): UI Themes; PATTERN(7): Combined; CONCEPT(5): Theme + CSS
# LINKS: [CALLS(8): get_theme; CALLS(8): get_all_css]
# END_CONTRACT

def get_theme_with_custom_css(
    theme_name: str = "soft",
    additional_css: Optional[str] = None,
) -> Tuple[gr.themes.Base, str]:
    """Получение темы с кастомным CSS."""
    logger.debug(f"[get_theme_with_custom_css][InputParams] theme_name={theme_name} [ATTEMPT]")
    
    # START_BLOCK_GET_THEME: [Получение темы]
    theme = get_theme(theme_name)
    # END_BLOCK_GET_THEME
    
    # START_BLOCK_GET_CSS: [Получение CSS]
    css = get_all_css()
    
    if additional_css:
        css += "\n" + additional_css
    # END_BLOCK_GET_CSS
    
    logger.debug(f"[get_theme_with_custom_css][ReturnData] Тема: {theme_name}, CSS длина: {len(css)} [SUCCESS]")
    
    return theme, css


# END_FUNCTION_GET_THEME_WITH_CUSTOM_CSS


logger.info(f"[ModuleInit][ui/themes][StepComplete] Модуль themes загружен, определено 8 функций и 2 класса [SUCCESS]")
