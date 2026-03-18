# START_MODULE_CONTRACT:
# PURPOSE: Инициализационный пакет точки входа в приложение
# SCOPE: CLI, запуск приложения, мониторинг
# INPUT: Нет (модуль инициализации)
# OUTPUT: Публичные атрибуты пакета
# KEYWORDS: [DOMAIN(9): EntryPoint; CONCEPT(7): Package; TECH(6): Python]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CONST 5 [Версия пакета точки входа] => __version__
# END_MODULE_MAP

"""
Пакет точки входа для запуска Gradio мониторинга приложения WALLET.DAT.GENERATOR.

Этот пакет предоставляет удобную точку входа для запуска мониторинга
через файл start/start.py
"""

__version__ = "1.0.0"
