#!/bin/bash
# FILE: src/monitor/_cpp/manual_build.sh
# VERSION: 1.0.1
# PURPOSE: Ручная сборка C++ модулей плагинов мониторинга без использования cmake

set -e

# Настройки - используем короткий путь без пробелов
PROJECT_DIR="/tmp/wallet"
CXX="g++"
PYTHON_VERSION="3.10"
PYTHON_INCLUDE="/usr/include/python3.10"
PYBIND11_INCLUDE="/home/lll/.local/lib/python3.10/site-packages/pybind11/include"
SRC_DIR="${PROJECT_DIR}/src/monitor/_cpp"
OUTPUT_DIR="${SRC_DIR}"
BUILD_DIR="${SRC_DIR}/build"

# Создание директории сборки
mkdir -p "$BUILD_DIR"

# Флаги компиляции
CXXFLAGS="-O3 -std=c++17 -fPIC -shared -Wall -Wextra"
PYTHON_INCLUDES="-I${PYTHON_INCLUDE} -I${PYBIND11_INCLUDE}"
LDFLAGS="-lpython3.10"

echo "=== Ручная сборка C++ модулей плагинов мониторинга ==="
echo "Исходная директория: ${SRC_DIR}"
echo "Выходная директория: ${OUTPUT_DIR}"

# Функция для сборки модуля
build_module() {
    local module_name=$1
    local sources=$2
    local output_name=$3
    
    local output_file="${OUTPUT_DIR}/${output_name}.cpython-${PYTHON_VERSION}-x86_64-linux-gnu.so"
    
    echo ""
    echo "Сборка ${module_name}..."
    echo "  Исходные файлы: ${sources}"
    echo "  Выходной файл: ${output_file}"
    
    $CXX $CXXFLAGS $PYTHON_INCLUDES ${sources} $LDFLAGS -o "$output_file"
    
    if [ -f "$output_file" ]; then
        echo "  [УСПЕХ] ${module_name} собран"
    else
        echo "  [ОШИБКА] ${module_name} не собран"
        return 1
    fi
}

# Модуль 1: plugin_base_cpp
build_module "plugin_base_cpp" \
    "${SRC_DIR}/src/plugin_base.cpp ${SRC_DIR}/bindings/plugin_base_bindings.cpp" \
    "plugin_base_cpp"

# Модуль 2: live_stats_plugin_cpp (зависит от plugin_base)
build_module "live_stats_plugin_cpp" \
    "${SRC_DIR}/src/live_stats_plugin.cpp ${SRC_DIR}/bindings/live_stats_plugin_bindings.cpp" \
    "live_stats_plugin_cpp"

# Модуль 3: match_notifier_plugin_cpp (зависит от plugin_base)
build_module "match_notifier_plugin_cpp" \
    "${SRC_DIR}/src/match_notifier_plugin.cpp ${SRC_DIR}/bindings/match_notifier_plugin_bindings.cpp" \
    "match_notifier_plugin_cpp"

# Модуль 4: final_stats_plugin_cpp (зависит от plugin_base)
build_module "final_stats_plugin_cpp" \
    "${SRC_DIR}/src/final_stats_plugin.cpp ${SRC_DIR}/bindings/final_stats_plugin_bindings.cpp" \
    "final_stats_plugin_cpp"

echo ""
echo "=== Сборка завершена ==="
echo "Выходные файлы в: ${OUTPUT_DIR}"
ls -la "${OUTPUT_DIR}"/*.so 2>/dev/null | grep -E "(plugin_base_cpp|live_stats_plugin_cpp|match_notifier_plugin_cpp|final_stats_plugin_cpp)"
