# FILE: src/monitor/utils/html_generators.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Утилиты для генерации HTML кода в мониторинге. Централизует HTML шаблоны и стили для заголовков, футеров, статусов этапов и ошибок.
# SCOPE: HTML генерация, шаблоны, стилизация UI
# INPUT: Нет (все методы статические)
# OUTPUT: Класс HTMLGenerator со статическими методами генерации HTML
# KEYWORDS: [DOMAIN(9): UI; DOMAIN(8): HTML; CONCEPT(7): Templates; TECH(6): StaticMethods]
# LINKS: [USED_BY(8): src.monitor.ui_builder; USED_BY(7): src.monitor.event_handlers]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 9 [Генератор HTML для мониторинга] => HTMLGenerator
# METHOD 7 [Генерация заголовка мониторинга] => generate_header
# METHOD 7 [Генерация футера мониторинга] => generate_footer
# METHOD 8 [Генерация HTML этапа работы] => get_stage_html
# METHOD 8 [Генерация HTML ошибки] => get_error_html
# METHOD 8 [Генерация HTML статуса live мониторинга] => get_live_status_html
# METHOD 6 [Генерация HTML настроек уведомлений] => get_notification_config_html
# METHOD 6 [Генерация HTML статуса уведомлений] => get_notification_status_html
# END_MODULE_MAP
# START_USE_CASES:
# - [generate_header]: System (UI) -> GenerateHeader -> HeaderDisplayed
# - [get_stage_html]: System (UI) -> ShowStage -> StageIndicatorDisplayed
# - [get_error_html]: System (UI) -> ShowError -> ErrorMessageDisplayed
# - [get_live_status_html]: System (UI) -> ShowLiveStatus -> LiveStatusDisplayed
# END_USE_CASES

"""
Модуль html_generators.py — Утилиты генерации HTML для мониторинга.
Содержит статические методы для создания заголовков, футеров, статусов и ошибок.
"""

# START_CLASS_HTMLGenerator
# START_CONTRACT:
# PURPOSE: Генератор HTML для мониторинга. Централизует HTML шаблоны и CSS стили для единообразия UI.
# Все методы статические — не требуют создания экземпляра класса.
# ATTRIBUTES:
# - STAGE_COLORS: Dict[str, Tuple[str, str]] — цвета и иконки для этапов
# - STAGE_NAMES: Dict[str, str] — человекочитаемые названия этапов
# METHODS:
# - Генерация заголовка => generate_header
# - Генерация футера => generate_footer
# - Генерация этапа => get_stage_html
# - Генерация ошибки => get_error_html
# - Генерация статуса => get_live_status_html
# KEYWORDS: [PATTERN(8): Generator; DOMAIN(9): UI; CONCEPT(7): Templates; TECH(6): StaticMethods]
# LINKS: [USED_BY(8): UIBuilder; USED_BY(7): EventHandlers]
# END_CONTRACT

class HTMLGenerator:
    """
    [Генератор HTML для мониторинга. Все методы статические.]
    """

    # Константы цветов и иконок для этапов
    STAGE_COLORS: dict = {
        "SELECTING_LIST": ("#2196F3", "1️⃣"),  # Синий
        "GENERATING": ("#4CAF50", "2️⃣"),      # Зелёный
        "FINISHED": ("#FF9800", "3️⃣"),        # Оранжевый
        "IDLE": ("#9E9E9E", "4️⃣"),            # Серый
    }

    STAGE_NAMES: dict = {
        "SELECTING_LIST": "Выбор LIST",
        "GENERATING": "Генерация",
        "FINISHED": "Завершено",
        "IDLE": "Ожидание",
    }

    # START_METHOD_generate_header
    # START_CONTRACT:
    # PURPOSE: Генерация HTML заголовка мониторинга с градиентным фоном и стилизацией.
    # INPUTS: Нет
    # OUTPUTS:
    # - str — HTML код заголовка
    # KEYWORDS: [CONCEPT(5): HTML; TECH(4): Templating]
    # END_CONTRACT

    @staticmethod
    def generate_header() -> str:
        """
        Генерация HTML заголовка мониторинга.

        Returns:
            str: HTML код заголовка с градиентным фоном
        """
        return """
        <div style="
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            margin-bottom: 20px;
            text-align: center;
        ">
            <h1 style="margin: 0; color: white; font-size: 32px;">💰 Wallet Generator Monitor</h1>
            <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.8); font-size: 16px;">
                Мониторинг процесса генерации Bitcoin кошельков
            </p>
        </div>
        """

    # END_METHOD_generate_header

    # START_METHOD_generate_footer
    # START_CONTRACT:
    # PURPOSE: Генерация HTML футера мониторинга.
    # INPUTS: Нет
    # OUTPUTS:
    # - str — HTML код футера
    # KEYWORDS: [CONCEPT(5): HTML; TECH(4): Templating]
    # END_CONTRACT

    @staticmethod
    def generate_footer() -> str:
        """
        Генерация HTML футера мониторинга.

        Returns:
            str: HTML код футера
        """
        return """
        <div style="
            padding: 15px;
            background: #f5f5f5;
            border-radius: 8px;
            margin-top: 20px;
            text-align: center;
            color: #666;
            font-size: 12px;
        ">
            WALLET.DAT.GENERATOR Monitor v1.0.0 | GitHub: Wallet-DAT-Generator
        </div>
        """

    # END_METHOD_generate_footer

    # START_METHOD_get_stage_html
    # START_CONTRACT:
    # PURPOSE: Генерация HTML для отображения текущего этапа работы с цветовой индикацией.
    # INPUTS:
    # - stage: str — идентификатор этапа (STAGE_1, STAGE_2, etc.)
    # OUTPUTS:
    # - str — HTML этапа с иконкой и названием
    # KEYWORDS: [CONCEPT(5): UI; TECH(4): StateDisplay]
    # END_CONTRACT

    @staticmethod
    def get_stage_html(stage: str) -> str:
        """
        Генерация HTML для отображения текущего этапа работы.

        Args:
            stage: Идентификатор этапа (STAGE_1, STAGE_2, etc.)

        Returns:
            str: HTML код с цветовой индикацией этапа
        """
        name = HTMLGenerator.STAGE_NAMES.get(stage, "Неизвестно")
        color, icon = HTMLGenerator.STAGE_COLORS.get(stage, ("#666", "❓"))

        return f"""
        <div style="
            padding: 15px;
            background: {color}15;
            border-left: 4px solid {color};
            border-radius: 8px;
        ">
            <div style="font-size: 14px; color: #666;">Текущий этап</div>
            <div style="font-size: 24px; font-weight: bold; color: {color};">
                {icon} {name}
            </div>
        </div>
        """

    # END_METHOD_get_stage_html

    # START_METHOD_get_error_html
    # START_CONTRACT:
    # PURPOSE: Генерация HTML для отображения сообщений об ошибках с красной цветовой индикацией.
    # INPUTS:
    # - error_message: Optional[str] — текст сообщения об ошибке (None для скрытия)
    # OUTPUTS:
    # - str — HTML код для отображения ошибки
    # KEYWORDS: [CONCEPT(5): UI; TECH(4): ErrorDisplay]
    # END_CONTRACT

    @staticmethod
    def get_error_html(error_message: str = None) -> str:
        """
        Генерация HTML для отображения ошибки.

        Args:
            error_message: Текст ошибки (None для скрытия)

        Returns:
            str: HTML код ошибки или пустая строка
        """
        if error_message is None:
            # Скрываем компонент - возвращаем пустой HTML
            return ""

        return f"""
        <div style="
            padding: 15px;
            background: #ffebee;
            border-left: 4px solid #f44336;
            border-radius: 8px;
            margin-top: 10px;
        ">
            <div style="font-size: 14px; color: #c62828; font-weight: bold;">⚠️ Ошибка</div>
            <div style="font-size: 16px; color: #b71c1c; margin-top: 5px;">
                {error_message}
            </div>
        </div>
        """

    # END_METHOD_get_error_html

    # START_METHOD_get_live_status_html
    # START_CONTRACT:
    # PURPOSE: Генерация HTML для отображения статуса live-мониторинга.
    # INPUTS:
    # - iteration_count: int — количество итераций
    # - is_monitoring: bool — флаг активности мониторинга
    # OUTPUTS:
    # - str — HTML код для отображения статуса
    # KEYWORDS: [CONCEPT(5): UI; TECH(4): StatusDisplay]
    # END_CONTRACT

    @staticmethod
    def get_live_status_html(iteration_count: int = 0, is_monitoring: bool = False) -> str:
        """
        Генерация HTML для статуса live мониторинга.

        Args:
            iteration_count: Количество итераций
            is_monitoring: Флаг активности мониторинга

        Returns:
            str: HTML код статуса
        """
        if is_monitoring:
            status_color = "#4CAF50"  # Зелёный
            status_text = "🟢 Мониторинг активен"
        else:
            status_color = "#FF9800"  # Оранжевый
            status_text = "🔴 Ожидание запуска"

        return f"""
        <div style="padding: 10px; background: {status_color}20; border-radius: 8px; border: 2px solid {status_color};">
            <h3 style="margin: 0; color: {status_color};">{status_text}</h3>
            <p style="margin: 5px 0; color: #212121;">Итераций: <strong style="color: #212121;">{iteration_count:,}</strong></p>
        </div>
        """

    # END_METHOD_get_live_status_html

    # START_METHOD_get_notification_config_html
    # START_CONTRACT:
    # PURPOSE: Генерация HTML для отображения настроек уведомлений.
    # INPUTS:
    # - config: dict — словарь с настройками уведомлений
    # OUTPUTS:
    # - str — HTML код настроек
    # KEYWORDS: [CONCEPT(5): UI; TECH(4): ConfigDisplay]
    # END_CONTRACT

    @staticmethod
    def get_notification_config_html(config: dict = None) -> str:
        """
        Генерация HTML для отображения настроек уведомлений.

        Args:
            config: Словарь с настройками уведомлений

        Returns:
            str: HTML код настроек
        """
        if not config:
            return ""

        return f"""
        <div style='padding: 10px; background: #f5f5f5; border-radius: 8px;'>
            <h3>Настройки уведомлений</h3>
            <ul>
                <li>Звуковые: {'Включены' if config.get('sound_enabled') else 'Отключены'}</li>
                <li>Визуальные: {'Включены' if config.get('visual_enabled') else 'Отключены'}</li>
                <li>Desktop: {'Включены' if config.get('desktop_enabled') else 'Отключены'}</li>
                <li>Логирование: {'Включено' if config.get('log_enabled') else 'Отключено'}</li>
            </ul>
        </div>
        """

    # END_METHOD_get_notification_config_html

    # START_METHOD_get_notification_status_html
    # START_CONTRACT:
    # PURPOSE: Генерация HTML для статуса уведомлений.
    # INPUTS:
    # - is_active: bool — флаг активности
    # OUTPUTS:
    # - str — HTML код статуса
    # KEYWORDS: [CONCEPT(5): UI; TECH(4): StatusDisplay]
    # END_CONTRACT

    @staticmethod
    def get_notification_status_html(is_active: bool = False) -> str:
        """
        Генерация HTML для статуса уведомлений.

        Args:
            is_active: Флаг активности

        Returns:
            str: HTML код статуса
        """
        if is_active:
            return """
            <div style='padding: 10px; background: #4CAF5020; border-radius: 8px;'>
                <h3>🔔 Мониторинг активен</h3>
            </div>
            """
        else:
            return """
            <div style='padding: 10px; background: #9E9E9E20; border-radius: 8px;'>
                <h3>⏸ Ожидание</h3>
            </div>
            """

    # END_METHOD_get_notification_status_html


# END_CLASS_HTMLGenerator
