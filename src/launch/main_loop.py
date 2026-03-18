#!/usr/bin/env python3
# FILE: src/launch/main_loop.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Основной цикл генерации кошельков Bitcoin. Бесконечный процесс генерации
# с мониторингом совпадений с адресами из предоставленного списка.
# SCOPE: Генерация кошельков, мониторинг логов, обработка сигналов
# INPUT: Аргументы командной строки (--list путь_к_списку)
# OUTPUT: Логи метрик в logs/infinite_loop.log
# KEYWORDS: [DOMAIN(10): WalletGeneration; DOMAIN(9): InfiniteLoop; CONCEPT(8): SignalHandling]
# LINKS: [USES(10): batch_gen_cpp; USES(9): address_matcher_cpp; USES(8): UnifiedEntropyInterface]
# LINKS_TO_SPECIFICATION: [dev_plan_launch_integration.md]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# FUNC 10 [Точка входа в скрипт] => main
# FUNC 9 [Инициализация генератора] => initialize_generator
# FUNC 9 [Загрузка списка адресов] => load_address_list
# FUNC 10 [Основной цикл генерации] => generation_loop
# FUNC 8 [Обработка сигналов остановки] => signal_handler
# FUNC 8 [Логирование метрик] => log_metrics
# FUNC 7 [Проверка совпадений] => check_matches
# END_MODULE_MAP
# START_USE_CASES:
# - [main]: System (Startup) -> ParseArgs -> GeneratorReady
# - [generation_loop]: Generator (Running) -> GenerateWallets -> MatchesFound
# - [signal_handler]: System (Shutdown) -> HandleSignal -> GracefulStop
# END_USE_CASES
"""
Модуль main_loop.py — Основной цикл генерации кошельков Bitcoin.

Этот скрипт реализует бесконечный цикл генерации кошельков с мониторингом
совпадений с адресами из предоставленного списка. Метрики записываются
в лог-файл logs/infinite_loop.log в формате, совместимом с LogParser.

Пример использования:
    python src/launch/main_loop.py --list adr_list/full_list.txt
"""

import argparse
import logging
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Set

# Настройка пути для импорта модулей проекта
PROJECT_ROOT = Path(__file__).parent.parent.parent
BUILD_DIR = PROJECT_ROOT / "build" / "compilation"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BUILD_DIR))

# Константы
DEFAULT_LOG_FILE = "logs/infinite_loop.log"
DEFAULT_BATCH_SIZE = 1000
STOP_FILE = "stop.flag"


# START_FUNCTION_MAIN
# START_CONTRACT:
# PURPOSE: Точка входа в скрипт генератора. Парсирует аргументы, инициализирует
# генератор и запускает бесконечный цикл.
# INPUTS:
# - Аргументы командной строки: --list путь_к_списку
# OUTPUTS:
# - int: Код завершения (0 - успех, 1 - ошибка)
# SIDE_EFFECTS:
# — Запускает бесконечный цикл генерации
# — Обрабатывает сигналы остановки
# KEYWORDS: [DOMAIN(10): EntryPoint; CONCEPT(9): CLI]
# END_CONTRACT

def main() -> int:
    """
    Точка входа в скрипт генератора кошельков.
    
    INPUTS:
    - Аргументы командной строки (--list)
    
    OUTPUTS:
    - int: Код завершения
    
    SIDE_EFFECTS:
    — Запускает бесконечный цикл генерации
    """
    # START_BLOCK_PARSE_ARGS: [Парсинг аргументов командной строки]
    parser = argparse.ArgumentParser(
        description="Генератор кошельков Bitcoin с мониторингом совпадений"
    )
    parser.add_argument(
        "--list",
        type=str,
        required=True,
        help="Путь к файлу со списком адресов для мониторинга"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Размер батча для генерации (по умолчанию: {DEFAULT_BATCH_SIZE})"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=DEFAULT_LOG_FILE,
        help=f"Путь к лог-файлу (по умолчанию: {DEFAULT_LOG_FILE})"
    )
    
    args = parser.parse_args()
    # END_BLOCK_PARSE_ARGS
    
    # START_BLOCK_VALIDATE_LIST_FILE: [Проверка существования файла списка адресов]
    list_path = Path(args.list)
    if not list_path.exists():
        print(f"Ошибка: Файл списка адресов не найден: {args.list}", file=sys.stderr)
        return 1
    # END_BLOCK_VALIDATE_LIST_FILE
    
    # START_BLOCK_SETUP_LOGGING: [Настройка логирования]
    log_file = Path(args.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("main_loop")
    logger.setLevel(logging.DEBUG)
    
    # Файловый обработчик для логов метрик
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    
    # Формат для LogParser-совместимых логов
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Также выводим в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    # END_BLOCK_SETUP_LOGGING
    
    logger.info(f"[MAIN][START] Генератор кошельков запущен")
    logger.info(f"[MAIN][Config] Список адресов: {args.list}")
    logger.info(f"[MAIN][Config] Размер батча: {args.batch_size}")
    logger.info(f"[MAIN][Config] Лог-файл: {args.log_file}")
    
    # START_BLOCK_INITIALIZE_GENERATOR: [Инициализация генератора]
    # START_BLOCK_INIT_CUDA_BACKEND: [Инициализация CUDA бэкенда]
    # Импорт CUDABackendManager для инструментирования GPU
    try:
        from src.plugins.cuda.fallback import CUDABackendManager, get_backend_manager
        
        cuda_backend = get_backend_manager()
        cuda_initialized = cuda_backend.initialize()
        cuda_status = cuda_backend.get_status()
        
        logger.info(f"[CUDA][INIT] Начало инициализации CUDA бэкенда")
        logger.info(f"[CUDA][INIT] CUDA доступна: {cuda_status.get('cuda_available', False)}")
        logger.info(f"[CUDA][INIT] CUDA активна: {cuda_status.get('cuda_active', False)}")
        
        # Логируем статус модулей
        module_status = cuda_status.get('module_status', {})
        for module_name, is_built in module_status.items():
            status_str = "собран" if is_built else "не собран"
            logger.info(f"[CUDA][INIT] Модуль {module_name}: {status_str}")
        
        # Определяем какой backend используется
        if cuda_status.get('cuda_active', False):
            logger.info(f"[CUDA][INIT] РЕЖИМ: GPU (CUDA) - максимальная производительность")
        else:
            logger.info(f"[CUDA][INIT] РЕЖИМ: CPU (fallback) - сниженная производительность")
            
    except ImportError as e:
        logger.warning(f"[CUDA][INIT] Не удалось импортировать CUDABackendManager: {e}")
        cuda_backend = None
        cuda_initialized = False
    # END_BLOCK_INIT_CUDA_BACKEND
    
    generator = None
    matcher = None
    addresses = []  # Инициализация переменной для адресов
    
    try:
        # Импорт модулей генерации
        from src.wrapper.unified_interface import UnifiedEntropyInterface
        from src.plugins.wallet.batch_gen import BatchWalletGenerator
        from src.plugins.wallet.address_matcher import AddressMatcher
        from src.plugins.wallet.wallet_dat import WalletDatWriter
        
        logger.info(f"[MAIN][INIT] Импорт модулей успешен")
        
        # Инициализация интерфейса энтропии
        entropy_interface = UnifiedEntropyInterface()
        logger.info(f"[MAIN][INIT] UnifiedEntropyInterface инициализирован")
        
        # Инициализация генератора кошельков
        generator = BatchWalletGenerator()
        logger.info(f"[MAIN][INIT] BatchWalletGenerator инициализирован")
        
        # Получение энтропии для инициализации
        entropy_data = entropy_interface.get_entropy(32 * 4)  # 128 байт
        generator.initialize(list(entropy_data))
        
        logger.info(f"[MAIN][INIT] Генератор кошельков инициализирован")
        
        # Инициализация address matcher
        matcher = AddressMatcher()
        logger.info(f"[MAIN][INIT] AddressMatcher инициализирован")
        
        # Загрузка списка адресов через встроенный метод
        try:
            loaded_count = matcher.load_addresses_from_file(str(list_path))
            logger.info(f"[MAIN][INIT] Загружено адресов для мониторинга: {loaded_count}")
            # Загружаем в Python-список для дальнейшего использования
            addresses = load_address_list(list_path)
        except Exception as e:
            logger.warning(f"[MAIN][INIT] Не удалось загрузить адреса через C++ модуль: {e}, используем fallback")
            # Fallback: загружаем вручную
            addresses = load_address_list(list_path)
            if addresses:
                logger.info(f"[MAIN][INIT] Загружено адресов для мониторинга (fallback): {len(addresses)}")
            else:
                logger.warning(f"[MAIN][INIT] Список адресов пуст, мониторинг не активен")
        
    except ImportError as e:
        logger.error(f"[MAIN][INIT] Ошибка импорта модулей: {e}")
        logger.error(f"[MAIN][INIT] Убедитесь, что C++ модули скомпилированы")
        # DYNAMIC_LOG: Выводим трассировку для диагностики
        import traceback
        logger.error(f"[MAIN][INIT] Traceback: {traceback.format_exc()}")
        return 1
    except Exception as e:
        logger.error(f"[MAIN][INIT] Ошибка инициализации: {e}")
        # DYNAMIC_LOG: Выводим трассировку для диагностики
        import traceback
        logger.error(f"[MAIN][INIT] Traceback: {traceback.format_exc()}")
        return 1
    # END_BLOCK_INITIALIZE_GENERATOR
    
    # Проверка успешности загрузки адресов
    if not addresses:
        logger.error("[MAIN][INIT] Не удалось загрузить список адресов для проверки!")
        return 1
    
    # START_BLOCK_SETUP_SIGNALS: [Настройка обработки сигналов]
    stop_event = {"should_stop": False}
    
    def signal_handler(signum, frame):
        """Обработчик сигналов остановки."""
        sig_name = signal.Signals(signum).name
        logger.info(f"[MAIN][SIGNAL] Получен сигнал {sig_name}, инициируем остановку...")
        stop_event["should_stop"] = True
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # END_BLOCK_SETUP_SIGNALS
    
    # START_BLOCK_GENERATION_LOOP: [Основной цикл генерации]
    iteration = 0
    total_wallets = 0
    total_matches = 0
    start_time = time.time()
    
    logger.info(f"[MAIN][LOOP] Начало бесконечного цикла генерации")
    logger.info(f"[STAGE] Generation - Начало генерации")
    
    while not stop_event["should_stop"]:
        iteration += 1
        iteration_start = time.time()
        
        try:
            # Проверка файла остановки
            if Path(STOP_FILE).exists():
                logger.info(f"[MAIN][STOP] Обнаружен файл остановки: {STOP_FILE}")
                break
            
            # Генерация батча кошельков
            # START_BLOCK_LOG_BACKEND_USAGE: [Логирование используемого backend]
            if cuda_backend is not None and iteration == 1:
                # Определяем какой тип модуля используется
                module_type = "unknown"
                if hasattr(generator, '__class__'):
                    class_name = generator.__class__.__name__
                    if 'cuda' in class_name.lower():
                        module_type = "CUDA"
                    else:
                        module_type = "CPU"
                logger.info(f"[CUDA][GENERATE] Тип генератора: {module_type}")
            # END_BLOCK_LOG_BACKEND_USAGE
            
            wallets = generator.generate_wallets(args.batch_size, deterministic=False)
            wallet_count = wallets.size()
            total_wallets += wallet_count
            
            # START_BLOCK_RECORD_CUDA_STATS: [Запись статистики CUDA операций]
            if cuda_backend is not None:
                if cuda_status.get('cuda_active', False):
                    cuda_backend.record_cuda_operation()
                else:
                    cuda_backend.record_cpu_operation()
            # END_BLOCK_RECORD_CUDA_STATS
            
            # Проверка совпадений если есть адреса и matcher
            matches_this_batch = 0
            if matcher and addresses and wallets.size() > 0:
                try:
                    # Получаем реальные адреса сгенерированных кошельков
                    wallet_addresses = []
                    for i in range(wallets.size()):
                        wallet = wallets.get_wallet_at(i)
                        wallet_addresses.append(wallet.address)
                    
                    # Логирование начала проверки
                    logger.info(f"[MAIN][MATCH] Проверка {len(wallet_addresses)} сгенерированных адресов против {len(addresses)} целевых")
                    
                    if wallet_addresses:
                        # Ищем пересечение реальных адресов с целевым списком
                        result = matcher.find_intersection(wallet_addresses, addresses)
                        matches_this_batch = len(result.matches)
                        total_matches += matches_this_batch
                        
                        if matches_this_batch > 0:
                            # Создаём директорию confirmed/ при необходимости
                            confirmed_dir = Path("confirmed")
                            confirmed_dir.mkdir(parents=True, exist_ok=True)
                            
                            for raw_addr in result.matches:
                                # Конвертируем RawAddress в строку Base58
                                match_addr = matcher.encode_base58(raw_addr)
                                logger.warning(f"[MAIN][MATCH] Найдено совпадение! Адрес: {match_addr}")
                                
                                # Сохраняем wallet.dat в директорию confirmed/
                                save_success = save_matched_wallet(wallets, confirmed_dir, match_addr, logger)
                                
                                if save_success:
                                    logger.warning(f"[MAIN][MATCH] Кошелёк сохранён в confirmed/")
                                
                except Exception as e:
                    logger.error(f"[MAIN][MATCH] Ошибка при поиске совпадений: {e}")
                    import traceback
                    logger.error(f"[MAIN][MATCH] Traceback: {traceback.format_exc()}")
            
            # Логирование метрик
            elapsed = time.time() - start_time
            iteration_time = time.time() - iteration_start
            
            # Формируем сообщения в формате LogParser
            logger.info(f"[MAIN][METRICS] Iteration: {iteration}")
            logger.info(f"[MAIN][METRICS] Wallet: {total_wallets}")
            logger.info(f"[MAIN][METRICS] Match: {total_matches}")
            logger.info(f"[MAIN][METRICS] Entropy: {entropy_interface.get_source_status()['available'] * 128}")
            
            # Вычисляем скорость
            if elapsed > 0:
                wallets_per_sec = total_wallets / elapsed
                iterations_per_sec = iteration / elapsed
                logger.info(f"[MAIN][METRICS] Speed: {wallets_per_sec:.2f} wallets/s, {iterations_per_sec:.2f} iter/s")
                logger.info(f"[MAIN][METRICS] IterationTime: {iteration_time:.3f}s")
            
            logger.debug(f"[MAIN][LOOP] Итерация {iteration} завершена: {wallet_count} кошельков, {matches_this_batch} совпадений")
            
        except Exception as e:
            logger.error(f"[MAIN][LOOP] Ошибка в итерации {iteration}: {e}")
            time.sleep(1)  # Пауза перед повторной попыткой
    
    # END_BLOCK_GENERATION_LOOP
    
    # START_BLOCK_CLEANUP: [Очистка ресурсов]
    # START_BLOCK_LOG_CUDA_STATS: [Логирование статистики CUDA]
    if cuda_backend is not None:
        cuda_status = cuda_backend.get_status()
        stats = cuda_status.get('stats', {})
        logger.info(f"[CUDA][STATS] Операций на CUDA: {stats.get('cuda_operations', 0)}")
        logger.info(f"[CUDA][STATS] Операций на CPU: {stats.get('cpu_operations', 0)}")
        logger.info(f"[CUDA][STATS] Fallbacks: {stats.get('fallbacks', 0)}")
        logger.info(f"[CUDA][STATS] Ошибки: {stats.get('errors', 0)}")
    # END_BLOCK_LOG_CUDA_STATS
    
    total_time = time.time() - start_time
    logger.info(f"[MAIN][SHUTDOWN] Генератор остановлен")
    logger.info(f"[MAIN][STATS] Всего итераций: {iteration}")
    logger.info(f"[MAIN][STATS] Всего кошельков: {total_wallets}")
    logger.info(f"[MAIN][STATS] Всего совпадений: {total_matches}")
    logger.info(f"[MAIN][STATS] Общее время: {total_time:.2f}s")
    
    if total_time > 0:
        logger.info(f"[MAIN][STATS] Средняя скорость: {total_wallets / total_time:.2f} кошельков/сек")
    
    logger.info(f"[STAGE] Idle - Генератор остановлен")
    # END_BLOCK_CLEANUP
    
    return 0


# END_FUNCTION_MAIN


# START_FUNCTION_LOAD_ADDRESS_LIST
# START_CONTRACT:
# PURPOSE: Загрузка списка адресов из файла. Поддерживает формат: один адрес на строку.
# INPUTS:
# - list_path: Path — путь к файлу списка адресов
# OUTPUTS:
# - List[str] — список адресов
# SIDE_EFFECTS:
# — Читает файл с диска
# KEYWORDS: [DOMAIN(8): FileIO; CONCEPT(7): AddressList]
# END_CONTRACT

def load_address_list(list_path: Path) -> List[str]:
    """
    Загрузка списка адресов из файла.
    
    INPUTS:
    - list_path: Path — путь к файлу
    
    OUTPUTS:
    - List[str] — список адресов
    
    SIDE_EFFECTS:
    — Читает файл
    """
    addresses = []
    
    try:
        with open(list_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Пропускаем пустые строки и комментарии
                if not line or line.startswith("#"):
                    continue
                
                # Извлекаем адрес (может быть в формате "address,amount" или просто "address")
                address = line.split(",")[0].strip()
                
                if address:
                    addresses.append(address)
        
    except Exception as e:
        logging.getLogger("main_loop").error(f"[MAIN][LOAD_LIST] Ошибка загрузки списка: {e}")
    
    return addresses


# END_FUNCTION_LOAD_ADDRESS_LIST


# START_FUNCTION_SAVE_MATCHED_WALLET
# START_CONTRACT:
# PURPOSE: Сохранение кошелька при обнаружении совпадения с целевым адресом.
# INPUTS:
# - wallets: WalletCollection — коллекция кошельков
# - confirmed_dir: Path — директория для сохранения
# - match_addr: str — адрес совпадения
# - logger: logging.Logger — логгер для записи событий
# OUTPUTS:
# - bool: True при успешном сохранении
# SIDE_EFFECTS:
# — Создаёт файл wallet.dat в директории confirmed/
# KEYWORDS: [DOMAIN(9): WalletSave; CONCEPT(8): MatchFound]
# END_CONTRACT

def save_matched_wallet(wallets, confirmed_dir: Path, match_addr: str, logger) -> bool:
    """
    Сохраняет wallet.dat при обнаружении совпадения.
    
    INPUTS:
    - wallets: WalletCollection — коллекция кошельков
    - confirmed_dir: Path — директория для сохранения
    - match_addr: str — адрес совпадения
    - logger: logging.Logger — логгер
    
    OUTPUTS:
    - bool: True при успешном сохранении
    
    SIDE_EFFECTS:
    — Создаёт файл wallet.dat
    """
    try:
        # Формируем имя файла с timestamp и первыми 8 символами адреса
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Используем только первые 8 символов адреса для имени файла
        addr_prefix = match_addr[:8] if len(match_addr) >= 8 else match_addr
        filename = f"wallet_{addr_prefix}_{timestamp}.dat"
        
        # Инициализируем writer
        writer = WalletDatWriter()
        writer.initialize(str(confirmed_dir))
        writer.create_database(filename)
        
        # Записываем коллекцию кошельков
        result = writer.write_wallet_collection(wallets)
        
        writer.close()
        
        if result:
            logger.warning(f"[MATCH][SAVE] wallet.dat сохранён: {confirmed_dir / filename}")
            return True
        else:
            logger.error(f"[MATCH][SAVE] Ошибка записи wallet.dat")
            return False
            
    except Exception as e:
        logger.error(f"[MATCH][SAVE] Исключение при сохранении: {e}")
        import traceback
        logger.error(f"[MATCH][SAVE] Traceback: {traceback.format_exc()}")
        return False


# END_FUNCTION_SAVE_MATCHED_WALLET


# Точка входа
if __name__ == "__main__":
    sys.exit(main())
