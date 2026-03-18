# START_MODULE_CONTRACT:
# PURPOSE: Скрипт для компиляции всех C++ модулей проекта через CMake
# SCOPE: Компиляция, CMake, Python модули
# INPUT: Нет (запускается из командной строки)
# OUTPUT: Скомпилированные .so файлы в папке lib/
# KEYWORDS: [DOMAIN(9): Compilation; DOMAIN(8): CMake; CONCEPT(7): BuildScript; TECH(6): Python]
# END_MODULE_CONTRACT

# START_MODULE_MAP:
# FUNC 10 [Компилирует все C++ модули проекта] => compile_all_modules
# FUNC 8 [Проверяет наличие необходимых зависимостей] => check_dependencies
# FUNC 5 [Копирует скомпилированные модули в папку lib] => copy_modules_to_lib
# END_MODULE_MAP

import os
import sys
import subprocess
import shutil
from pathlib import Path


# START_FUNCTION_compile_all_modules
# START_CONTRACT:
# PURPOSE: Основная функция для компиляции всех C++ модулей проекта
# INPUTS: Нет
# OUTPUTS: None - функция выполняет компиляцию и выводит результаты в консоль
# SIDE_EFFECTS:
# - Создает директорию build если её нет
# - Запускает cmake и make для компиляции
# - Копирует .so файлы в папку lib/
# TEST_CONDITIONS_SUCCESS_CRITERIA:
# - Все модули компилируются без ошибок
# - Файлы .so создаются в директории lib/
# KEYWORDS: [DOMAIN(9): Compilation; CONCEPT(8): CMake; TECH(7): Build]
# END_CONTRACT

def compile_all_modules():
    """
    Компилирует все C++ модули проекта через CMake.
    
    Описание:
        Этот скрипт выполняет полную компиляцию всех Python-совместимых
        C++ модулей проекта. После успешной компиляции файлы .so
        копируются в папку lib/ для дальнейшего использования.
    
    Модули для компиляции:
        1. core_cpp - базовый модуль (rand_add, orchestrator)
        2. getbitmaps_cpp - CPU плагин для bitmap
        3. rand_poll_cpp - CPU плагин для rand_poll
        4. hkey_performance_data_cpp - CPU плагин для hkey
        5. entropy_engine_cpp - основной модуль энтропии
        6. entropy_pipeline_cache_cpp - модуль кэша
        7. batch_gen_cpp - плагин для генерации кошельков
        8. wallet_dat_cpp - плагин для wallet.dat
        9. address_matcher_cpp - плагин для сопоставления адресов
    """
    # Определяем пути
    project_root = Path(__file__).resolve().parent.parent
    build_dir = project_root / "build" / "compilation"
    lib_dir = project_root / "lib"
    cmake_source_dir = project_root  # CMakeLists.txt находится в корне проекта
    
    print("=" * 70)
    print("  КОМПИЛЯЦИЯ C++ МОДУЛЕЙ ПРОЕКТА PRNG-State-Recovery-2009")
    print("=" * 70)
    print()
    
    # Шаг 1: Проверка зависимостей
    print("[1/4] Проверка зависимостей...")
    if not check_dependencies():
        print("ОШИБКА: Не все зависимости установлены!")
        print("Пожалуйста, установите:")
        print("  - CMake (>= 3.18)")
        print("  - Python (>= 3.10) и python3-dev")
        print("  - pybind11")
        print("  - OpenSSL (libssl-dev)")
        print("  - g++ (с поддержкой C++14)")
        sys.exit(1)
    print("Зависимости проверены [OK]")
    print()
    
    # Шаг 2: Создание директории сборки
    print("[2/4] Подготовка директории сборки...")
    if build_dir.exists():
        print(f"  Удаление старой директории: {build_dir}")
        shutil.rmtree(build_dir)
    
    build_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Создана директория: {build_dir}")
    print()
    
    # Шаг 3: Конфигурация CMake
    print("[3/4] Конфигурация CMake...")
    print("  Выполняется: cmake ...")
    
    # Определяем путь к pybind11
    pybind11_path = None
    try:
        import pybind11
        pybind11_path = Path(pybind11.__file__).parent
        print(f"  Найден pybind11 в: {pybind11_path}")
    except ImportError:
        pass
    
    # Формируем список аргументов для cmake
    cmake_args = ["cmake", str(cmake_source_dir), "-B", str(build_dir)]
    
    # Добавляем путь к pybind11 если найден
    if pybind11_path:
        cmake_args.append(f"-DCMAKE_PREFIX_PATH={pybind11_path}")
    
    try:
        result = subprocess.run(
            cmake_args,
            cwd=str(build_dir),
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            print("ОШИБКА при конфигурации CMake!")
            print(result.stdout)
            print(result.stderr)
            sys.exit(1)
        
        print("  CMake конфигурация успешна")
        # Выводим итоговую информацию CMake
        for line in result.stdout.split('\n'):
            if 'WalletDatGenerator' in line or 'Summary' in line or 'Version' in line or 'Python' in line or 'Output' in line:
                print(f"    {line.strip()}")
                
    except subprocess.TimeoutExpired:
        print("ОШИБКА: Превышен таймаут при конфигурации CMake")
        sys.exit(1)
    except FileNotFoundError:
        print("ОШИБКА: CMake не найден! Установите CMake.")
        sys.exit(1)
    
    print()
    
    # Шаг 4: Компиляция
    print("[4/4] Компиляция модулей...")
    print("  Выполняется: cmake --build . --parallel")
    
    try:
        # Определяем количество доступных ядер
        num_cores = os.cpu_count() or 4
        print(f"  Используется ядер: {num_cores}")
        
        result = subprocess.run(
            ["cmake", "--build", ".", "--parallel", str(num_cores)],
            cwd=str(build_dir),
            capture_output=True,
            text=True,
            timeout=600  # 10 минут таймаут
        )
        
        if result.returncode != 0:
            print("ОШИБКА при компиляции!")
            print(result.stdout)
            print(result.stderr)
            sys.exit(1)
        
        # Выводим информацию о скомпилированных модулях
        print("  Компиляция завершена успешно!")
        print()
        print("  Скомпилированные модули:")
        
        # Список модулей для отображения
        modules = [
            "core_cpp",
            "getbitmaps_cpp", 
            "rand_poll_cpp",
            "hkey_performance_data_cpp",
            "entropy_engine_cpp",
            "entropy_pipeline_cache_cpp",
            "batch_gen_cpp",
            "wallet_dat_cpp",
            "address_matcher_cpp"
        ]
        
        for module in modules:
            print(f"    - {module}")
            
    except subprocess.TimeoutExpired:
        print("ОШИБКА: Превышен таймаут при компиляции")
        sys.exit(1)
    
    print()
    
    # Копирование модулей в папку lib
    print("Копирование модулей в папку lib/...")
    copy_modules_to_lib(build_dir, lib_dir)
    
    print()
    print("=" * 70)
    print("  КОМПИЛЯЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 70)
    print()
    print("Скомпилированные модули доступны в: lib/")
    print("Вы можете импортировать их в Python:")
    print("  import entropy_engine_cpp")
    print("  import rand_poll_cpp")
    print("  import getbitmaps_cpp")
    print()


# END_FUNCTION_compile_all_modules

# START_FUNCTION_check_dependencies
# START_CONTRACT:
# PURPOSE: Проверяет наличие необходимых зависимостей для компиляции
# INPUTS: Нет
# OUTPUTS: bool - True если все зависимости установлены, False иначе
# KEYWORDS: [CONCEPT(6): Dependencies; TECH(5): Check]
# END_CONTRACT

def check_dependencies():
    """
    Проверяет наличие необходимых инструментов для компиляции.
    
    Возвращает:
        True если все зависимости найдены, False в противном случае.
    """
    dependencies = ["cmake", "g++"]
    
    missing_deps = []
    for dep in dependencies:
        result = shutil.which(dep)
        if result is None:
            print(f"  WARNING: {dep} не найден в PATH")
            missing_deps.append(dep)
    
    # Проверка версии Python
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 10):
        print(f"  WARNING: Требуется Python >= 3.10, найден {python_version.major}.{python_version.minor}")
        missing_deps.append(f"Python >= 3.10 (текущая: {python_version.major}.{python_version.minor})")
    
    # Проверка наличия pybind11 (через cmake или pip)
    pybind11_found = False
    
    # Проверяем через cmake
    pybind11_cmake = shutil.which("pybind11-config") or shutil.which("pybind11-config.cmake")
    if pybind11_cmake:
        pybind11_found = True
    
    # Проверяем через Python
    try:
        import pybind11
        pybind11_found = True
    except ImportError:
        pass
    
    # Проверяем через pkg-config
    try:
        result = subprocess.run(
            ["pkg-config", "--exists", "pybind11"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            pybind11_found = True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    if not pybind11_found:
        print("  WARNING: pybind11 не найден")
        missing_deps.append("pybind11")
    
    # Проверка OpenSSL
    openssl_found = False
    try:
        result = subprocess.run(
            ["pkg-config", "--exists", "openssl"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            openssl_found = True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Проверяем через cmake
    if not openssl_found:
        openssl_include = Path("/usr/include/openssl/ssl.h")
        if openssl_include.exists():
            openssl_found = True
    
    if not openssl_found:
        print("  WARNING: OpenSSL (libssl-dev) не найден")
        missing_deps.append("OpenSSL (libssl-dev)")
    
    if missing_deps:
        print()
        print("  Недостающие зависимости:")
        for dep in missing_deps:
            print(f"    - {dep}")
        print()
        print("  Для установки в Ubuntu/Debian выполните:")
        print("    sudo apt-get update")
        print("    sudo apt-get install -y cmake g++ python3-dev python3-pip")
        print("    sudo apt-get install -y libssl-dev")
        print("    pip install pybind11")
        print()
        print("  Или используйте conda:")
        print("    conda install -c conda-forge pybind11 cmake")
        return False
    
    return True


# END_FUNCTION_check_dependencies

# START_FUNCTION_copy_modules_to_lib
# START_CONTRACT:
# PURPOSE: Копирует скомпилированные .so файлы в папку lib
# INPUTS:
# - build_dir: Path - директория сборки
# - lib_dir: Path - целевая директория для модулей
# OUTPUTS: None
# KEYWORDS: [CONCEPT(6): FileCopy; TECH(5): Build]
# END_CONTRACT

def copy_modules_to_lib(build_dir: Path, lib_dir: Path):
    """
    Копирует скомпилированные .so файлы в папку lib.
    
    Аргументы:
        build_dir: Директория, где были скомпилированы модули
        lib_dir: Директория для размещения модулей
    """
    # Создаем lib_dir если не существует
    lib_dir.mkdir(parents=True, exist_ok=True)
    
    # Ищем все .so файлы
    so_files = list(build_dir.glob("*.so"))
    
    if not so_files:
        print("  WARNING: Не найдены .so файлы в директории сборки")
        return
    
    copied_count = 0
    for so_file in so_files:
        dest_path = lib_dir / so_file.name
        shutil.copy2(so_file, dest_path)
        print(f"  Скопирован: {so_file.name}")
        copied_count += 1
    
    print(f"  Всего скопировано модулей: {copied_count}")


# END_FUNCTION_copy_modules_to_lib


if __name__ == "__main__":
    compile_all_modules()
