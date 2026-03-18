# FILE: wrapper/examples/basic_usage.py
# VERSION: 1.0.0
"""
Примеры использования Python-обёртки для генерации энтропии.

Этот файл содержит рабочие примеры, демонстрирующие основные
возможности библиотеки для работы с энтропией.

Запуск примеров:
    python wrapper/examples/basic_usage.py
"""
import sys
import os

# Добавляем путь к корню проекта
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from wrapper import UnifiedEntropyInterface
from src.wrapper.entropy.entropy_engine import EntropyEngine, STRATEGY_XOR, STRATEGY_HASH
from src.wrapper.entropy.rand_poll_source import RandPollSource
from src.wrapper.core.exceptions import DataValidationError, EntropySourceError


def print_separator(title: str) -> None:
    """Печатает разделитель с заголовком."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def example_1_basic_usage():
    """Пример 1: Базовое использование UnifiedEntropyInterface."""
    print_separator("Пример 1: Базовое использование")
    
    # Использование контекстного менеджера (рекомендуется)
    with UnifiedEntropyInterface() as interface:
        # Получение 32 байт энтропии
        entropy = interface.get_entropy(32)
        print(f"Энтропия ({len(entropy)} байт): {entropy.hex()}")


def example_2_random_numbers():
    """Пример 2: Генерация случайных чисел."""
    print_separator("Пример 2: Генерация случайных чисел")
    
    with UnifiedEntropyInterface() as interface:
        # Случайное число от 1 до 100
        number = interface.get_random_int(1, 100)
        print(f"Случайное число (1-100): {number}")
        
        # Случайное число от 0 до 255
        byte_value = interface.get_random_int(0, 255)
        print(f"Случайный байт (0-255): {byte_value}")
        
        # Hex-строка (16 байт = 32 символа)
        hex_str = interface.get_random_hex(16)
        print(f"Hex-строка (16 байт): {hex_str}")


def example_3_config():
    """Пример 3: Использование с конфигурацией."""
    print_separator("Пример 3: Конфигурация интерфейса")
    
    config = {
        "strategy": STRATEGY_HASH,
        "log_level": "INFO"
    }
    
    with UnifiedEntropyInterface(config) as interface:
        entropy = interface.get_entropy(32)
        print(f"Энтропия (HASH стратегия): {entropy.hex()}")
        
        # Изменение стратегии
        interface.configure({"strategy": STRATEGY_XOR})
        entropy_xor = interface.get_entropy(32)
        print(f"Энтропия (XOR стратегия): {entropy_xor.hex()}")


def example_4_combining_strategies():
    """Пример 4: Различные стратегии комбинирования."""
    print_separator("Пример 4: Стратегии комбинирования")
    
    strategies = [
        ("XOR", STRATEGY_XOR),
        ("HASH", STRATEGY_HASH)
    ]
    
    with UnifiedEntropyInterface() as interface:
        for name, strategy in strategies:
            entropy = interface.get_entropy(32, strategy=strategy)
            print(f"{name}: {entropy.hex()[:32]}...")


def example_5_source_status():
    """Пример 5: Проверка статуса источников."""
    print_separator("Пример 5: Статус источников")
    
    with UnifiedEntropyInterface() as interface:
        status = interface.get_source_status()
        
        print(f"Всего источников: {status['total']}")
        print(f"Доступно: {status['available']}")
        
        print("\nДетали источников:")
        for name, info in status['sources'].items():
            print(f"  {name}:")
            print(f"    - Доступен: {info['available']}")
            print(f"    - Инициализирован: {info.get('initialized', 'N/A')}")


def example_6_direct_source():
    """Пример 6: Работа с источниками напрямую."""
    print_separator("Пример 6: Прямая работа с источниками")
    
    # Создание источника с seed для воспроизводимости
    source = RandPollSource(seed=42)
    
    print(f"Источник доступен: {source.is_available()}")
    print(f"Режим fallback: {source._use_fallback}")
    
    # Получение энтропии
    entropy = source.get_entropy(32)
    print(f"Энтропия: {entropy.hex()}")
    
    # Получение информации о фазах
    phases_info = source.get_phases_info()
    print(f"Фаз выполнено: {sum(1 for p in phases_info.values() if p.get('executed'))}")


def example_7_entropy_engine():
    """Пример 7: Использование EntropyEngine."""
    print_separator("Пример 7: EntropyEngine")
    
    # Создание движка
    engine = EntropyEngine()
    
    # Добавление источника
    new_source = RandPollSource(seed=123)
    engine.add_source(new_source)
    
    # Получение энтропии от конкретного источника
    available = engine.get_available_sources()
    if available:
        entropy = engine.get_entropy(32, available[0])
        print(f"Энтропия от {available[0]}: {entropy.hex()}")
    
    # Комбинированная энтропия
    combined = engine.get_combined_entropy(32, STRATEGY_XOR)
    print(f"Комбинированная энтропия: {combined.hex()}")
    
    # Удаление источника
    engine.remove_source("RandPollSource")
    print(f"Доступные источники после удаления: {engine.get_available_sources()}")


def example_8_error_handling():
    """Пример 8: Обработка ошибок."""
    print_separator("Пример 8: Обработка ошибок")
    
    with UnifiedEntropyInterface() as interface:
        try:
            # Попытка получить энтропию с некорректным размером
            entropy = interface.get_entropy(0)
        except DataValidationError as e:
            print(f"Ошибка валидации: {e}")
        
        try:
            # Некорректный диапазон
            number = interface.get_random_int(100, 1)
        except DataValidationError as e:
            print(f"Ошибка диапазона: {e}")
        
        try:
            # Некорректная стратегия
            interface.configure({"strategy": "INVALID"})
        except DataValidationError as e:
            print(f"Ошибка стратегии: {e}")
    
    print("Ошибки обработаны корректно")


def example_9_fallback_mode():
    """Пример 9: Fallback режим."""
    print_separator("Пример 9: Fallback режим")
    
    # Создание источника с несуществующим модулем
    source = RandPollSource(module_path="nonexistent_module.so", seed=999)
    
    print(f"Используется fallback: {source._use_fallback}")
    print(f"Источник доступен: {source.is_available()}")
    
    # Получение энтропии работает в fallback режиме
    entropy = source.get_entropy(32)
    print(f"Энтропия (fallback): {entropy.hex()}")
    
    # Воспроизводимость с тем же seed
    source2 = RandPollSource(module_path="nonexistent_module.so", seed=999)
    entropy2 = source2.get_entropy(32)
    print(f"Энтропия с тем же seed: {entropy.hex() == entropy2.hex()}")


def example_10_multiple_calls():
    """Пример 10: Множественные вызовы."""
    print_separator("Пример 10: Множественные вызовы")
    
    with UnifiedEntropyInterface() as interface:
        # Генерация нескольких порций энтропии
        entropies = []
        for i in range(5):
            entropy = interface.get_entropy(16)
            entropies.append(entropy)
            print(f"Вызов {i+1}: {entropy.hex()}")
        
        # Проверка уникальности
        unique = len(set(entropies))
        print(f"\nУникальных значений: {unique} из {len(entropies)}")


def example_11_reproducible():
    """Пример 11: Воспроизводимые результаты."""
    print_separator("Пример 11: Воспроизводимые результаты")
    
    # Первый прогон
    with UnifiedEntropyInterface() as interface1:
        entropy1 = interface1.get_entropy(32, strategy=STRATEGY_XOR)
    
    # Второй прогон с теми же параметрами
    with UnifiedEntropyInterface() as interface2:
        entropy2 = interface2.get_entropy(32, strategy=STRATEGY_XOR)
    
    # Note: Результаты будут разными, так как entropy gathering включает случайные факторы
    # Однако с фиксированным seed в источниках можно получить воспроизводимость
    print(f"Прогон 1: {entropy1.hex()[:32]}...")
    print(f"Прогон 2: {entropy2.hex()[:32]}...")
    
    # Для полной воспроизводимости используйте источники с фиксированным seed
    print("\nС фиксированным seed:")
    source1 = RandPollSource(seed=42)
    source2 = RandPollSource(seed=42)
    ent1 = source1.get_entropy(32)
    ent2 = source2.get_entropy(32)
    print(f"Одинаковые: {ent1 == ent2}")


def main():
    """Запуск всех примеров."""
    print("=" * 60)
    print("  Демонстрация возможностей Python-обёртки")
    print("  генерации энтропии")
    print("=" * 60)
    
    examples = [
        example_1_basic_usage,
        example_2_random_numbers,
        example_3_config,
        example_4_combining_strategies,
        example_5_source_status,
        example_6_direct_source,
        example_7_entropy_engine,
        example_8_error_handling,
        example_9_fallback_mode,
        example_10_multiple_calls,
        example_11_reproducible,
    ]
    
    for i, example in enumerate(examples, 1):
        try:
            example()
        except Exception as e:
            print(f"Ошибка в примере {i}: {e}")
    
    print("\n" + "=" * 60)
    print("  Все примеры выполнены")
    print("=" * 60)


if __name__ == "__main__":
    main()
