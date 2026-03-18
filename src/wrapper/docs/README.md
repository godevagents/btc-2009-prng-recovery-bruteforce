# Python-обёртка для C++ модулей генерации энтропии

## Описание библиотеки

Python-обёртка предоставляет унифицированный интерфейс для работы с C++ модулями генерации энтропии, используемыми в проекте генерации кошельков Bitcoin. Библиотека реализует криминалистическую реконструкцию алгоритма `RAND_poll()` для Windows XP SP3.

### Основные возможности

- **Единый интерфейс** — удобный API для получения энтропии из различных источников
- **Поддержка C++ модулей** — прямое взаимодействие с нативными модулями через ctypes
- **Fallback-режим** — автоматическое переключение на Python-эмуляцию при недоступности модулей
- **Несколько стратегий комбинирования** — XOR, HASH
- **Контекстный менеджер** — автоматическое управление ресурсами
- **Подробное логирование** — все операции записываются в лог-файл

### Поддерживаемые источники энтропии

1. **RandPollSource** — обёртка над `rand_poll_cpp`, реализует 5 фаз сбора энтропии
2. **GetBitmapsSource** — обёртка над `getbitmaps_cpp`, генерация битмапов
3. **HKeyPerformanceSource** — обёртка над `hkey_performance_data_cpp`, данные о производительности

## Установка

### Требования

- Python 3.10+
- ctypes (встроен в Python)
- pytest (для запуска тестов)

### Клонирование репозитория

```bash
git clone <repository_url>
cd WALLET.DAT.GENERATOR
```

### Сборка C++ модулей

Для использования нативных модулей необходимо их собрать:

```bash
./build_all_modules.sh
```

Примечание: Если модули не собраны, библиотека автоматически переключится на Python-эмуляцию (fallback).

## Быстрый старт

### Простой пример

```python
from wrapper import UnifiedEntropyInterface

# Использование контекстного менеджера (рекомендуется)
with UnifiedEntropyInterface() as interface:
    # Получение 32 байт энтропии
    entropy = interface.get_entropy(32)
    print(f"Энтропия: {entropy.hex()}")
    
    # Получение случайного числа в диапазоне
    random_number = interface.get_random_int(1, 100)
    print(f"Случайное число: {random_number}")
    
    # Получение hex-строки
    hex_string = interface.get_random_hex(16)
    print(f"Hex-строка: {hex_string}")
```

### Без контекстного менеджера

```python
from wrapper import UnifiedEntropyInterface

interface = UnifiedEntropyInterface()
entropy = interface.get_entropy(32)
interface.close()
```

### С указанием конфигурации

```python
from wrapper import UnifiedEntropyInterface
from src.src.wrapper.entropy.entropy_engine import STRATEGY_XOR, STRATEGY_HASH

config = {
    "strategy": STRATEGY_HASH,  # Стратегия комбинирования
    "log_level": "DEBUG"       # Уровень логирования
}

with UnifiedEntropyInterface(config) as interface:
    entropy = interface.get_entropy(64)
```

## API документация

### UnifiedEntropyInterface

Основной класс для работы с энтропией.

#### Конструктор

```python
UnifiedEntropyInterface(config: dict = None)
```

Параметры:
- `config` (dict, optional): Словарь конфигурации. Поддерживаемые ключи:
  - `strategy`: Стратегия комбинирования (XOR, HASH). По умолчанию: XOR
  - `log_level`: Уровень логирования (DEBUG, INFO, WARNING, ERROR). По умолчанию: INFO
  - `auto_init`: Автоматическая инициализация источников. По умолчанию: True

#### Методы

##### get_entropy

```python
interface.get_entropy(size: int, source: str = None, strategy: str = "XOR") -> bytes
```

Получает энтропию заданного размера.

Параметры:
- `size` (int): Размер в байтах
- `source` (str, optional): Имя конкретного источника. Если None, используется комбинирование
- `strategy` (str): Стратегия комбинирования (используется если source=None)

Возвращает: bytes — сгенерированная энтропия

##### get_random_bytes

```python
interface.get_random_bytes(size: int) -> bytes
```

Получает случайные байты (алиас для get_entropy).

##### get_random_int

```python
interface.get_random_int(min_val: int, max_val: int) -> int
```

Получает случайное целое число в заданном диапазоне.

Параметры:
- `min_val` (int): Минимальное значение (включительно)
- `max_val` (int): Максимальное значение (включительно)

Возвращает: int — случайное число в диапазоне [min_val, max_val]

##### get_random_hex

```python
interface.get_random_hex(size: int) -> str
```

Получает случайную hex-строку.

Параметры:
- `size` (int): Размер в байтах (количество символов = size * 2)

Возвращает: str — случайная hex-строка

##### get_source_status

```python
interface.get_source_status() -> dict
```

Возвращает статус всех источников энтропии.

Возвращает: dict со статусами источников:
- `total`: Общее количество источников
- `available`: Количество доступных источников
- `sources`: Детали по каждому источнику

##### configure

```python
interface.configure(config: dict) -> None
```

Настраивает конфигурацию интерфейса.

##### close

```python
interface.close() -> None
```

Освобождает ресурсы интерфейса.

### EntropyEngine

Класс для координации источников энтропии.

#### Конструктор

```python
EntropyEngine(sources: List[EntropySource] = None)
```

Параметры:
- `sources` (list, optional): Список источников энтропии. Если None, добавляются источники по умолчанию

#### Методы

##### add_source

```python
engine.add_source(source: EntropySource) -> None
```

Добавляет источник энтропии в координатор.

##### remove_source

```python
engine.remove_source(source_name: str) -> None
```

Удаляет источник энтропии из координатора.

##### get_available_sources

```python
engine.get_available_sources() -> List[str]
```

Возвращает список доступных источников энтропии.

##### get_entropy

```python
engine.get_entropy(size: int, source_name: str = None) -> bytes
```

Получает энтропию от указанного источника.

##### get_combined_entropy

```python
engine.get_combined_entropy(size: int, strategy: str = "XOR") -> bytes
```

Получает комбинированную энтропию из всех доступных источников.

Параметры:
- `size` (int): Размер в байтах
- `strategy` (str): Стратегия комбинирования (XOR, HASH)

##### get_source_status

```python
engine.get_source_status() -> dict
```

Возвращает статус всех источников энтропии.

### RandPollSource

Источник энтропии на основе криминалистической реконструкции RAND_poll().

#### Конструктор

```python
RandPollSource(module_path: str = None, seed: int = 0)
```

Параметры:
- `module_path` (str, optional): Путь к .so модулю. Если None, используется путь по умолчанию
- `seed` (int): Начальное значение для генератора случайных чисел (для воспроизводимости)

#### Методы

##### get_entropy

```python
source.get_entropy(size: int) -> bytes
```

Получает энтропию от источника.

##### is_available

```python
source.is_available() -> bool
```

Проверяет доступность источника энтропии.

## Примеры использования

### Пример 1: Базовое использование

```python
from wrapper import UnifiedEntropyInterface

# Простое получение энтропии
with UnifiedEntropyInterface() as interface:
    # 32 байта случайных данных
    entropy = interface.get_entropy(32)
    print(f"Получено {len(entropy)} байт: {entropy.hex()}")
```

### Пример 2: Работа с отдельными источниками

```python
from src.src.wrapper.entropy.entropy_engine import EntropyEngine
from src.src.wrapper.entropy.rand_poll_source import RandPollSource

# Создание движка с указанием источников
engine = EntropyEngine()

# Добавление источника с seed для воспроизводимости
source = RandPollSource(seed=12345)
engine.add_source(source)

# Получение энтропии
entropy = engine.get_entropy(32)
print(f"Энтропия: {entropy.hex()}")

# Получение списка доступных источников
available = engine.get_available_sources()
print(f"Доступные источники: {available}")
```

### Пример 3: Комбинирование источников

```python
from wrapper import UnifiedEntropyInterface
from src.src.wrapper.entropy.entropy_engine import STRATEGY_XOR, STRATEGY_HASH

with UnifiedEntropyInterface() as interface:
    # XOR комбинирование (по умолчанию)
    entropy_xor = interface.get_entropy(32, strategy=STRATEGY_XOR)
    
    # Хеширование
    entropy_hash = interface.get_entropy(32, strategy=STRATEGY_HASH)
    
    print(f"XOR: {entropy_xor.hex()}")
    print(f"HASH: {entropy_hash.hex()}")
```

### Пример 4: Проверка статуса источников

```python
from wrapper import UnifiedEntropyInterface

with UnifiedEntropyInterface() as interface:
    status = interface.get_source_status()
    
    print(f"Всего источников: {status['total']}")
    print(f"Доступно: {status['available']}")
    
    for name, info in status['sources'].items():
        print(f"  {name}: доступен={info['available']}")
```

### Пример 5: Генерация случайных чисел

```python
from wrapper import UnifiedEntropyInterface

with UnifiedEntropyInterface() as interface:
    # Случайное число от 1 до 100
    number = interface.get_random_int(1, 100)
    print(f"Случайное число: {number}")
    
    # Случайное число от 0 до 255
    byte_value = interface.get_random_int(0, 255)
    print(f"Байт: {byte_value}")
    
    # Hex-строка (16 байт = 32 символа)
    hex_str = interface.get_random_hex(16)
    print(f"Hex: {hex_str}")
```

### Пример 6: Работа с fallback

```python
from src.src.wrapper.entropy.rand_poll_source import RandPollSource

# При недоступности C++ модуля используется fallback
source = RandPollSource(module_path="nonexistent_module.so")

# Проверка режима работы
if source._use_fallback:
    print("Используется Python-эмуляция")
else:
    print("Используется C++ модуль")

# Получение энтропии работает в обоих режимах
entropy = source.get_entropy(32)
print(f"Энтропия: {entropy.hex()}")
```

## Обработка ошибок

### Типы исключений

Библиотека определяет следующие типы исключений:

- `EntropySourceError` — базовое исключение для всех ошибок модуля
- `ModuleLoadError` — ошибка загрузки .so модуля
- `DataValidationError` — ошибка валидации входных данных
- `EntropyGenerationError` — ошибка генерации энтропии

### Пример обработки ошибок

```python
from wrapper import UnifiedEntropyInterface
from src.src.wrapper.core.exceptions import DataValidationError, EntropySourceError

try:
    with UnifiedEntropyInterface() as interface:
        # Попытка получить энтропию
        entropy = interface.get_entropy(32)
        print(f"Успешно: {entropy.hex()}")
        
except DataValidationError as e:
    print(f"Ошибка валидации: {e}")
    
except EntropySourceError as e:
    print(f"Ошибка источника: {e}")
    
except Exception as e:
    print(f"Неожиданная ошибка: {e}")
```

### Частые ошибки и их решения

1. **Ошибка: "Некорректный размер энтропии"**
   - Решение: Размер должен быть в диапазоне 1-1024 байт

2. **Ошибка: "Нет доступных источников энтропии"**
   - Решение: Проверьте, что C++ модули собраны и доступны, или используется fallback

3. **Ошибка: "Неподдерживаемая стратегия"**
   - Решение: Используйте одну из поддерживаемых стратегий: XOR, HASH

## Fallback-режим

Fallback-режим активируется автоматически в следующих случаях:

1. C++ модуль не найден
2. Ошибка загрузки модуля через ctypes
3. Модуль не содержит требуемых функций

При активации fallback:
- Используется Python-эмуляция на основе стандартного random
- Для воспроизводимости можно указать seed
- Функциональность сохраняется полностью

```python
from src.src.wrapper.entropy.rand_poll_source import RandPollSource

# Создание с fallback (seed для воспроизводимости)
source = RandPollSource(module_path="nonexistent.so", seed=42)

# Источник работает
entropy = source.get_entropy(32)
print(f"Энтропия (fallback): {entropy.hex()}")
```

## Логирование

Все операции записываются в лог-файл `app.log` в корне проекта.

### Уровни логирования

- DEBUG: Подробная отладочная информация
- INFO: Общая информация о ходе выполнения
- WARNING: Предупреждения о потенциальных проблемах
- ERROR: Ошибки, не влияющие на работу
- CRITICAL: Критические ошибки

### Настройка уровня логирования

```python
from wrapper import UnifiedEntropyInterface

config = {"log_level": "DEBUG"}

with UnifiedEntropyInterface(config) as interface:
    entropy = interface.get_entropy(32)
```

## Тестирование

Запуск тестов:

```bash
pytest wrapper/tests/test_src.wrapper.py -v
```

Запуск с покрытием:

```bash
pytest wrapper/tests/test_src.wrapper.py --cov=wrapper -v
```

## Версия

Текущая версия: 1.0.0

## Лицензия

Проект является частью генератора кошельков Bitcoin и распространяется в соответствии с лицензией проекта.
