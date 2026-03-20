# PRNG-State-Recovery-2009

PRNG-State-Recovery-2009 — это скрипт подбирающий приватные ключи для заготовленного списка забытых биткоин адрессов из **2009-2011** года. Используется тщательно выверенный портрет раннего криптоэнтузиаста для воссоздания типичных значений системной энтропии в момент первого запуска bitcoin-core 0.1.0, во время которого происходило создание кошелька wallet.dat, через вызовы OpenSSL 0.9.8h в том числе.

Скрипт **с криминалистической точностю** воспроизводит алгоритм генерации BTC кошелька на базе Bitcoin-core 0.1.0, алгоритмов OpenSSL 0.9.8h, системных вызовов Windows XP SP3 и типичной сборки железа раннего криптоэнтузиаста.

---

## Особенности

🔥 **Скорость брутфорса до 3900 кошельков в секунду (или 390 wallet.dat) на Intel Core i7 13620H**

🔥 **Конфиг-эмуляция системной энтропии наиболее популярной сборки железа в 2009 году на базе исследования-аналитики портрета раннего криптоэнтузиаста**
*   Windows XP SP3 / Intel Core 2 Quad Q6600 / 4GB DDR2 RAM
*   Конфиг является ядром генерации диапазонов raw_data, возвращаемых системными вызовами Windows, идущих в энтропийный буффер OpenSSL, проходящие различные алгоритмы смешивания и хэширования с абсолютной точностью оригинальным алгоритмам bitcoin-core 0.1.0 и openssl 0.9.8h.

🔥 **Дамп из 40 тыс. забытых биткоин адрессов с балансом от 25 до 2000+ BTC**
*   Каждый можно проверить на наличие баланса через блокчейн обозреватель
*   В панели выбора списка на запуск брутфорса рекомендуется использовать дамп-список из 16 дней (доступны fulldump & 16 day dump), это наиболее качественный список кошельков по отношению к реализованному алгоритму поиска совпадений

🔥 **Berkley DB формат сохранения совпавшего wallet.dat, совместимость найденного совпадения с Bitcoin 0.1.0+** (а как в кошелёк то заходить будем?🌚)
*   Создание точной конструкции wallet.dat на базе исходников bitcoin-core 0.1.0 💸🫰💵

💻️ **Панель упраления через localhost вкладку в браузере по умолчанию**

## Дерево проекта

```
PRNG-State-Recovery-2009/
│
├── CMakeLists.txt                      # Главный CMake конфигурационный файл
├── README.md                           # Документация проекта (этот файл)
├── requirements.txt                    # Python зависимости проекта
│
├── adr_list/                           # База адресов для сопоставления
│   ├── 09.01.2009_16.09.2009.txt       # Адреса за период 2009
│   ├── full_list.txt                   # Полный список адресов
│   └── totaldump.txt                   # Дамп с метаданными, актуален на 07.01.2025
│
├── cache/                              # Кэш энтропии
│   ├── bindings/
│   │   └── entropy_pipeline_cache_bindings.cpp  # Python биндинги для кэша
│   ├── cache/include/
│   │   └── entropy_pipeline_cache.hpp  # Заголовочный файл кэша
│   ├── include/
│   │   └── entropy_pipeline_cache.hpp  # Публичный заголовочный файл
│   └── src/
│       └── entropy_pipeline_cache.cpp  # Реализация кэша
│
├── quick start/                        # Быстрый старт
│   ├── __init__.py                     # Инициализация пакета
│   ├── compilation.py                  # Скрипт компиляции
│   └── start.py                        # Главный скрипт запуска (ТОЧКА ВХОДА)
│
├── reference/                          # Референсные материалы
│   ├── bitcoin-core 0.1.0/             # Исходный код Bitcoin 2009
│   └── openssl 0.9.8h/                 # Исходный код OpenSSL 0.9.8h
│
└── src/                                # Исходный код проекта
    ├── core/                           # Ядро проекта
    │   ├── __init__.py                 # Инициализация Python пакета
    │   ├── entropy_engine.cpp          # Координатор источников энтропии
    │   ├── entropy_engine.hpp          # Заголовочный файл движка энтропии
    │   ├── entropy_engine_bindings.cpp # Python-C++ биндинги движка
    │   ├── rand_add.cpp                # Репликация ssleay_rand_add()
    │   ├── rand_add.h                  # Заголовочный файл rand_add
    │   ├── orchestrator.cpp            # Оркестрация компонентов
    │   ├── orchestrator.h              # Заголовочный файл оркестратора
    │   ├── entropy_cache.cpp           # Кэширование энтропии
    │   └── pybind11_wrapper.cpp        # Универсальные pybind11 обёртки
    │
    ├── plugins/                        # Плагины системы
    │   ├── cpu/                        # CPU источники энтропии
    │   │   ├── __init__.py
    │   │   ├── rand_poll/              # /dev/urandom энтропия в заданных диапазонах.
    │   │   │   ├── __init__.py
    │   │   │   ├── poll.cpp             # Опрос /dev/urandom
    │   │   │   ├── poll.h               # Заголовочный файл
    │   │   │   ├── rand_poll_fallback.hpp  # Запасная реализация
    │   │   │   └── pybind11_wrapper.cpp # Python биндинги
    │   │   │
    │   │   ├── bitmap/                 # Bitmap энтропия
    │   │   │   ├── __init__.py
    │   │   │   ├── getbitmaps.cpp      # Генерация bitmap данных
    │   │   │   ├── getbitmaps.h        # Заголовочный файл
    │   │   │   ├── bitmap_generator.hpp # Генератор битовых карт
    │   │   │   └── pybind11_wrapper.cpp # Python биндинги
    │   │   │
    │   │   ├── randaddseed/            # HKEY данные производительности
    │   │   │   ├── hkey_performance_data.cpp  # Сбор HKEY данных
    │   │   │   ├── hkey_performance_data.h     # Заголовочный файл
    │   │   │   ├── hkey_performance_data.txt   # Сырые данные
    │   │   │   ├── QueryPerformanceCounter.cpp # Windows API обёртка
    │   │   │   ├── QueryPerformanceCounter.h   # Заголовочный файл
    │   │   │   └── pybind11_wrapper.cpp       # Python биндинги
    │   │   │
    │   │   └── hkey/                   # HKEY совместимость (alias)
    │   │       └── hkey_performance_fallback.hpp # Запасная реализация
    │   │
    │   ├── wallet/                     # Кошелёк Bitcoin
    │   │   ├── wallet_dat/             # Формат wallet.dat (Berkeley DB)
    │   │   │   ├── __init__.py
    │   │   │   ├── wallet_dat.cpp      # Основная логика кошелька
    │   │   │   ├── wallet_dat.h        # Заголовочный файл
    │   │   │   ├── wallet_settings.cpp # Настройки кошелька
    │   │   │   ├── wallet_settings.h    # Заголовочный файл
    │   │   │   ├── wallet_tx.cpp       # Транзакции кошелька
    │   │   │   ├── wallet_tx.h         # Заголовочный файл
    │   │   │   ├── pybind11_wrapper.cpp # Python биндинги
    │   │   │   ├── berkeley_db/        # Berkeley DB интеграция
    │   │   │   │   ├── berkeley_db.cpp # Работа с BDB
    │   │   │   │   └── berkeley_db.h   # Заголовочный файл
    │   │   │   ├── crypto/             # Криптография кошелька
    │   │   │   │   ├── blowfish.cpp    # Шифрование Blowfish
    │   │   │   │   └── blowfish.h       # Заголовочный файл
    │   │   │   └── tests/              # Тесты кошелька
    │   │   │       ├── __init__.py
    │   │   │       ├── test_wallet_dat.py    # Тесты wallet.dat
    │   │   │       └── test_save_matched_wallet.py # Тесты сохранения
    │   │   │
    │   │   ├── batch_gen/              # Пакетная генерация кошельков
    │   │   │   ├── __init__.py
    │   │   │   ├── batch_gen.cpp       # Генерация партий кошельков
    │   │   │   ├── batch_gen.h         # Заголовочный файл
    │   │   │   ├── pybind11_wrapper.cpp # Python биндинги
    │   │   │   └── tests/              # Тесты
    │   │   │       ├── __init__.py
    │   │   │       └── test_batch_gen.py    # Тесты генерации
    │   │   │
    │   │   ├── address_matcher/       # Сопоставление адресов
    │   │   │   ├── __init__.py
    │   │   │   ├── address_matcher.cpp # Логика сопоставления
    │   │   │   ├── address_matcher.h   # Заголовочный файл
    │   │   │   ├── pybind11_wrapper.cpp     # Python биндинги
    │   │   │   └── tests/                   # Тесты
    │   │   │       ├── __init__.py
    │   │   │       └── test_address_matcher.py # Тесты сопоставления
    │   │   │
    │   │   └── monitor/                     # Мониторинг кошельков
    │   │       ├── __init__.py
    │   │       ├── monitor.py               # Основной монитор
    │   │       ├── observer.py              # Наблюдатель за изменениями
    │   │       ├── progress.py              # Отслеживание прогресса
    │   │       └── stats.py                 # Статистика генерации
    │   │
    │   └── crypto/                          # Криптографические функции
    │       └── ecdsa_keys/                  # Генерация ECDSA ключей
    │           ├── __init__.py
    │           ├── ecdsa_keys.cpp           # Генерация ECDSA ключей
    │           ├── ecdsa_keys.h             # Заголовочный файл
    │           ├── ecdsa_keys.py            # Python обёртка
    │           ├── interface.py             # Интерфейс генерации
    │           └── pybind11_wrapper.cpp     # Python биндинги
    │
    ├── wrapper/                             # Python обёртки
    │   ├── __init__.py
    │   ├── core/                            # Базовые компоненты
    │   │   ├── __init__.py
    │   │   ├── base.py                      # Базовый класс
    │   │   ├── exceptions.py                # Исключения
    │   │   └── logger.py                    # Логирование
    │   │
    │   ├── entropy/                         # Python API энтропии
    │   │   ├── __init__.py
    │   │   ├── entropy_engine.py            # Главный класс EntropyEngine
    │   │   ├── rand_poll_source.py          # Источник rand_poll
    │   │   ├── getbitmaps_source.py         # Источник bitmap
    │   │   └── hkey_source.py               # Источник HKEY
    │   │
    │   ├── snapshot/                        # Генерация снапшотов
    │   │   ├── __init__.py
    │   │   ├── constants.py                 # Константы снапшотов
    │   │   ├── gen_log.py                   # Генератор логов
    │   │   ├── gen_snapshot.py              # Генератор снапшотов
    │   │   └── snapshot_io.py               # Ввод/вывод снапшотов
    │   │
    │   └── examples/                        # Примеры использования
    │       └── basic_usage.py               # Базовый пример
    │
    ├── launch/                              # Запуск приложения
    │   └── main_loop.py                     # Главный цикл приложения
    │
    └── monitor/                             # Gradio мониторинг UI
        ├── __init__.py
        ├── app_core.py                      # Ядро приложения мониторинга
        ├── gradio_app.py                    # Gradio интерфейс
        ├── ui_builder.py                    # Построитель UI
        ├── event_handlers.py                # Обработчики событий
        ├── desktop_launcher.py              # Запуск на десктопе
        ├── factories/                       # Фабрики компонентов
        │   ├── __init__.py
        │   └── plugin_factory.py            # Фабрика плагинов
        ├── integrations/                    # Интеграции
        │   ├── __init__.py
        │   └── launch_integration.py        # Интеграция запуска
        ├── plugins/                         # UI плагины
        │   ├── __init__.py
        │   ├── list_selector.py             # Выбор списка
        ├── ui/                              # UI компоненты
        │   ├── __init__.py
        │   ├── components.py                # UI компоненты
        │   └── themes.py                    # Темы оформления
        ├── utils/                           # Утилиты монитора
        │   ├── __init__.py
        │   ├── html_generators.py           # Генераторы HTML
        │   └── signal_handler.py            # Обработчик сигналов
        ├── _cpp/                            # C++ плагины мониторинга (рудимент)
        │   ├── __init__.py
        │   ├── final_stats_plugin_cpp.so    # Финальная статистика
        │   ├── live_stats_plugin_cpp.so     # Живая статистика
        │   ├── match_notifier_plugin_cpp.so # Уведомление о совпадениях
        │   ├── plugin_base_cpp.so           # Базовый плагин
        │   ├── final_stats_wrapper.py       # Python обёртка статистики
        │   ├── live_stats_wrapper.py        # Python обёртка live stats
        │   ├── match_notifier_wrapper.py    # Python обёртка уведомлений
        │   ├── plugin_base_wrapper.py       # Python обёртка базы
        │   ├── metrics_wrapper.py           # Python обёртка метрик
        │   ├── final_stats.py               # Финальная статистика
        │   ├── live_stats.py                # Живая статистика
        │   ├── match_notifier.py            # Уведомления
        │   ├── plugin_base.py               # Базовый класс плагина
        │   ├── build.sh                     # Скрипт сборки
        │   ├── manual_build.sh              # Ручная сборка
        │   ├── CMakeLists.txt               # CMake конфиг
        │   ├── bindings/                    # C++ биндинги
        │   │   ├── final_stats_plugin_bindings.cpp
        │   │   ├── live_stats_plugin_bindings.cpp
        │   │   ├── match_notifier_plugin_bindings.cpp
        │   │   └── plugin_base_bindings.cpp
        │   ├── include/                     # Заголовочные файлы
        │   │   ├── final_stats_plugin.hpp
        │   │   ├── live_stats_plugin.hpp
        │   │   ├── match_notifier_plugin.hpp
        │   │   ├── plugin_base.hpp
        │   │   └── ring_buffer.hpp
        │   └── src/                         # Исходники плагинов
        │       ├── final_stats_plugin.cpp
        │       ├── live_stats_plugin.cpp
        │       ├── match_notifier_plugin.cpp
        │       └── plugin_base.cpp
        │
        └── monitor_cpp/                     # C++ мониторинг (рудимент)
            ├── bindings/                    # Python биндинги
            │   ├── final_stats_plugin_bindings.cpp
            │   ├── live_stats_plugin_bindings.cpp
            │   ├── log_parser_bindings.cpp
            │   ├── match_notifier_plugin_bindings.cpp
            │   ├── metrics_bindings.cpp
            │   └── plugin_base_bindings.cpp
            ├── core/                        # Ядро мониторинга
            │   ├── metrics.cpp
            │   └── metrics.hpp
            ├── integrations/                # Интеграции
            │   ├── log_parser.cpp
            │   └── log_parser.hpp
            └── plugins/                     # C++ плагины
                ├── final_stats_plugin.cpp/hpp
                ├── live_stats_plugin.cpp/hpp
                ├── match_notifier_plugin.cpp/hpp
                └── plugin_base.cpp/hpp
```

---

## Ключевые модули

| Модуль | Назначение | Файл |
|--------|-----------|------|
| `entropy_engine_cpp` | Координатор источников энтропии с поддержкой стратегий XOR/HASH | [`src/core/entropy_engine.cpp`](src/core/entropy_engine.cpp) |
| `rand_add.cpp` | Криминалистическая репликация `ssleay_rand_add()` — точная копия md_rand.c:81-205 | [`src/core/rand_add.cpp`](src/core/rand_add.cpp) |
| `wallet_dat` | Генерация и обработка wallet.dat (формат Berkeley DB) | [`src/plugins/wallet/wallet_dat/`](src/plugins/wallet/wallet_dat/) |
| `batch_gen` | Пакетная генерация кошельков | [`src/plugins/wallet/batch_gen/`](src/plugins/wallet/batch_gen/) |
| `address_matcher` | Сопоставление адресов из базы `adr_list/` | [`src/plugins/wallet/address_matcher/`](src/plugins/wallet/address_matcher/) |
| `rand_poll` | Опрос /dev/urandom для получения энтропии | [`src/plugins/cpu/rand_poll/`](src/plugins/cpu/rand_poll/) |
| `getbitmaps` | Генерация bitmap энтропии | [`src/plugins/cpu/bitmap/`](src/plugins/cpu/bitmap/) |
| `hkey_performance_data` | Сбор HKEY данных производительности Windows | [`src/plugins/cpu/randaddseed/`](src/plugins/cpu/randaddseed/) |
| `ecdsa_keys` | Генерация ECDSA ключей Bitcoin | [`src/plugins/crypto/ecdsa_keys/`](src/plugins/crypto/ecdsa_keys/) |
| `monitor` | Gradio веб-интерфейс мониторинга | [`src/monitor/`](src/monitor/) |

---

## Гайд по запуску

### Quick Start (Рекомендуемый способ)

Запустите проект с помощью скрипта [`quick start/start.py`](quick%20start/start.py) — это главная точка входа:

```bash
cd "PRNG-State-Recovery-2009"
python "quick start/start.py"
```

### Опции командной строки

| Параметр | По умолчанию | Описание |
|----------|--------------|----------|
| `--port` | 7860 | Порт для Gradio |
| `--share` | false | Создать публичную ссылку |
| `--server-name` | 127.0.0.1 | Имя сервера |

### Установка зависимостей

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y cmake g++ python3-dev python3-pip
sudo apt-get install -y libssl-dev libdb++-dev
pip install pybind11 gradio psutil
```

---

### Python зависимости

```
gradio>=4.0.0      # Веб-интерфейс мониторинга
pybind11>=2.10.0   # Python-C++ биндинги
```

### C++/Системные зависимости

| Зависимость | Версия | Назначение |
|------------|--------|------------|
| CMake | >= 3.18 | Система сборки |
| Python | >= 3.10 | Интерпретатор и python3-dev |
| pybind11 | — | Python-C++ биндинги |
| OpenSSL | libssl-dev | Криптографические функции (MD5, SHA) |
| g++ | C++14 | Компилятор |
| Berkeley DB | libdb++-dev | Формат wallet.dat |
| pthread | — | Многопоточность |

---

## Совместимость с ОС

### Подтверждённая поддержка

**Linux (основная платформа)**
- Ubuntu/Debian — полная поддержка
- Скомпилированные модули: `*.cpython-310-x86_64-linux-gnu.so`
- CMake флаги: `-std=c++14`, `-pthread`, `-O3 -fPIC`

### Техническая совместимость

| Компонент | Linux | Windows | macOS |
|-----------|-------|---------|-------|
| CMake сборка | ✅ | ⚠️ WSL | ⚠️ Docker/WSL |
| Python модули (.so) | ✅ | ❌ | ❌ |
| Gradio интерфейс | ✅ | ✅ | ✅ |
| /dev/urandom | ✅ | ❌ | ⚠️ |

### Переменные окружения

- `FORCE_CPU_MODE=1` — принудительный CPU режим (по умолчанию)

