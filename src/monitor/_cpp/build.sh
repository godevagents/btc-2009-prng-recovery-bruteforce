#!/bin/bash
# FILE: src/monitor/_cpp/build.sh
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Скрипт сборки всех C++ модулей плагинов мониторинга для Python.
# SCOPE: Компиляция, линковка, установка Python модулей
# INPUT: CMake, pybind11, Python 3.10+
# OUTPUT: .so файлы в директории src/monitor/_cpp/
# KEYWORDS: [DOMAIN(9): BuildScript; TECH(8): CMake; TECH(7): Pybind11]
# END_MODULE_CONTRACT

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Директория скрипта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}=== Сборка C++ модулей плагинов мониторинга ===${NC}"
echo ""

# Проверка наличия CMake
if ! command -v cmake &> /dev/null; then
    echo -e "${RED}ОШИБКА: cmake не найден. Установите cmake.${NC}"
    exit 1
fi

# Проверка наличия Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}ОШИБКА: Python не найден. Установите Python 3.${NC}"
    exit 1
fi

# Определение Python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

PYTHON_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${YELLOW}Версия Python: $PYTHON_VERSION${NC}"

# Проверка наличия pybind11
echo -e "${YELLOW}Проверка pybind11...${NC}"
if $PYTHON_CMD -c "import pybind11" 2>/dev/null; then
    PYBIND11_VERSION=$($PYTHON_CMD -c "import pybind11; print(pybind11.__version__)" 2>/dev/null || echo "unknown")
    echo -e "${GREEN}pybind11 найден: версия $PYBIND11_VERSION${NC}"
else
    echo -e "${RED}ОШИБКА: pybind11 не найден. Установите pybind11: pip install pybind11${NC}"
    exit 1
fi

# Очистка предыдущей сборки
echo ""
echo -e "${YELLOW}Очистка предыдущей сборки...${NC}"
rm -rf CMakeFiles CMakeCache.txt cmake_install.cmake Makefile *.so
rm -rf build 2>/dev/null || true

# Создание директории сборки
mkdir -p build
cd build

# Конфигурация CMake
echo ""
echo -e "${YELLOW}Конфигурация CMake...${NC}"
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DPYTHON_EXECUTABLE=$($PYTHON_CMD -c "import sys; print(sys.executable)") \
    -DCMAKE_LIBRARY_OUTPUT_DIRECTORY="${SCRIPT_DIR}"

# Сборка всех модулей
echo ""
echo -e "${YELLOW}Сборка всех модулей...${NC}"
cmake --build . --config Release -j$(nproc)

# Возврат в директорию скрипта
cd "$SCRIPT_DIR"

# Проверка результатов сборки
echo ""
echo -e "${GREEN}=== Результаты сборки ===${NC}"

MODULES=(
    "plugin_base_cpp"
    "live_stats_plugin_cpp"
    "match_notifier_plugin_cpp"
    "final_stats_plugin_cpp"
)

ALL_BUILT=true
for module in "${MODULES[@]}"; do
    SO_FILE="${module}.cpython-${PYTHON_VERSION}-"*.so
    if [ -f "$SO_FILE" ]; then
        SIZE=$(du -h "$SO_FILE" | cut -f1)
        echo -e "${GREEN}✓${NC} $module: $SO_FILE ($SIZE)"
    else
        # Попробуем найти без версии
        if ls ${module}*.so 1> /dev/null 2>&1; then
            FOUND_FILE=$(ls ${module}*.so | head -1)
            SIZE=$(du -h "$FOUND_FILE" | cut -f1)
            echo -e "${GREEN}✓${NC} $module: $FOUND_FILE ($SIZE)"
        else
            echo -e "${RED}✗${NC} $module: НЕ СОБРАН"
            ALL_BUILT=false
        fi
    fi
done

echo ""

# Копирование .so файлов в директорию src/monitor/_cpp/
echo -e "${YELLOW}Копирование .so файлов в директорию...${NC}"
for module in "${MODULES[@]}"; do
    SO_FILE=$(ls build/${module}*.so 2>/dev/null | head -1)
    if [ -n "$SO_FILE" ]; then
        cp "$SO_FILE" "${SCRIPT_DIR}/"
        echo -e "${GREEN}Скопирован:${NC} $SO_FILE -> ${SCRIPT_DIR}/"
    fi
done

# Проверка Python импорта
echo ""
echo -e "${YELLOW}Проверка импорта в Python...${NC}"

# Добавить текущую директорию в PYTHONPATH
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

for module in "${MODULES[@]}"; do
    MODULE_NAME="${module%%_cpp}"  # Удалить суффикс _cpp
    if $PYTHON_CMD -c "import ${MODULE_NAME}_cpp" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} ${MODULE_NAME}_cpp импортирован успешно"
    else
        echo -e "${RED}✗${NC} ${MODULE_NAME}_cpp: ошибка импорта (возможно, нужны зависимости)"
    fi
done

echo ""
echo -e "${GREEN}=== Сборка завершена ===${NC}"
