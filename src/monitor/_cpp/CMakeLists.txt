# FILE: src/monitor/_cpp/CMakeLists.txt
# VERSION: 2.0.0
# START_MODULE_CONTRACT:
# PURPOSE: CMake конфигурация для сборки Python модулей плагинов мониторинга с использованием pybind11.
# SCOPE: Сборка, компиляция, линковка Python модулей (plugin_base, live_stats, match_notifier, final_stats)
# INPUT: Зависимости: pybind11, Python 3.10+
# OUTPUT: Скомпилированные .so файлы для Python
# KEYWORDS: [DOMAIN(9): CMake; DOMAIN(8): BuildSystem; TECH(7): Pybind11; TECH(6): Plugin]
# END_MODULE_CONTRACT

cmake_minimum_required(VERSION 3.15)
project(monitor_plugins_cpp VERSION 2.0.0 LANGUAGES CXX)

# Настройка стандарта C++
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Настройка позиционно-независимого кода (PIC) для библиотек
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Поиск Python и pybind11
find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

# Настройка выходного каталога
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/src/monitor/_cpp)

# Определение пути к заголовочным файлам
set(MONITOR_CPP_INCLUDE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/include)

# ============================================================================
# Модуль 1: plugin_base_cpp (базовый класс плагинов)
# ============================================================================

# Исходные файлы plugin_base
set(PLUGIN_BASE_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/src/plugin_base.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/bindings/plugin_base_bindings.cpp
)

# Заголовочные файлы plugin_base
set(PLUGIN_BASE_HEADERS
    ${CMAKE_CURRENT_SOURCE_DIR}/include/plugin_base.hpp
    ${CMAKE_CURRENT_SOURCE_DIR}/include/ring_buffer.hpp
)

# Создание библиотеки plugin_base_cpp
add_library(plugin_base_cpp SHARED 
    ${PLUGIN_BASE_SOURCES}
    ${PLUGIN_BASE_HEADERS}
)

# Флаги компиляции для plugin_base
target_compile_options(plugin_base_cpp PRIVATE
    -O3
    -fPIC
    -std=c++17
)

# Include директории для plugin_base
target_include_directories(plugin_base_cpp 
    PUBLIC 
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
        $<BUILD_INTERFACE:${MONITOR_CPP_INCLUDE_DIR}>
    PRIVATE
        ${Python_INCLUDE_DIRS}
)

# Директивы препроцессора
target_compile_definitions(plugin_base_cpp 
    PRIVATE 
        PYBIND11_DETAIL_ABI 
        PYBIND11_PLUGIN_NAME="plugin_base_cpp"
)

# Настройка pybind11 модуля
pybind11_add_module(plugin_base_cpp 
    ${PLUGIN_BASE_SOURCES}
    ${PLUGIN_BASE_HEADERS}
)

# Линковка библиотек
target_link_libraries(plugin_base_cpp 
    PRIVATE 
        pybind11::module 
        pybind11::embed
)

# Свойства модуля plugin_base
set_target_properties(plugin_base_cpp PROPERTIES
    PREFIX ""
    OUTPUT_NAME "plugin_base_cpp"
    SUFFIX ".cpython-${PYTHON_VERSION_MAJOR}${PYTHON_VERSION_MINOR}-${CMAKE_SYSTEM_PROCESSOR}.so"
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
)

# Правила установки
install(TARGETS plugin_base_cpp 
    LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}
)

# ============================================================================
# Модуль 2: live_stats_plugin_cpp (зависит от plugin_base)
# ============================================================================

# Исходные файлы live_stats_plugin
set(LIVE_STATS_PLUGIN_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/src/live_stats_plugin.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/bindings/live_stats_plugin_bindings.cpp
)

# Заголовочные файлы live_stats_plugin
set(LIVE_STATS_PLUGIN_HEADERS
    ${CMAKE_CURRENT_SOURCE_DIR}/include/live_stats_plugin.hpp
)

# Создание библиотеки live_stats_plugin_cpp
add_library(live_stats_plugin_cpp SHARED 
    ${LIVE_STATS_PLUGIN_SOURCES}
    ${LIVE_STATS_PLUGIN_HEADERS}
)

# Флаги компиляции для live_stats_plugin
target_compile_options(live_stats_plugin_cpp PRIVATE
    -O3
    -fPIC
    -std=c++17
)

# Include директории для live_stats_plugin
target_include_directories(live_stats_plugin_cpp 
    PUBLIC 
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
        $<BUILD_INTERFACE:${MONITOR_CPP_INCLUDE_DIR}>
    PRIVATE
        ${Python_INCLUDE_DIRS}
)

# Директивы препроцессора
target_compile_definitions(live_stats_plugin_cpp 
    PRIVATE 
        PYBIND11_DETAIL_ABI 
        PYBIND11_PLUGIN_NAME="live_stats_plugin_cpp"
)

# Настройка pybind11 модуля
pybind11_add_module(live_stats_plugin_cpp 
    ${LIVE_STATS_PLUGIN_SOURCES}
    ${LIVE_STATS_PLUGIN_HEADERS}
)

# Линковка - зависимость от plugin_base_cpp
target_link_libraries(live_stats_plugin_cpp 
    PRIVATE 
        pybind11::module 
        pybind11::embed
        plugin_base_cpp
)

# Свойства модуля live_stats_plugin
set_target_properties(live_stats_plugin_cpp PROPERTIES
    PREFIX ""
    OUTPUT_NAME "live_stats_plugin_cpp"
    SUFFIX ".cpython-${PYTHON_VERSION_MAJOR}${PYTHON_VERSION_MINOR}-${CMAKE_SYSTEM_PROCESSOR}.so"
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
)

# Правила установки
install(TARGETS live_stats_plugin_cpp 
    LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}
)

# ============================================================================
# Модуль 3: match_notifier_plugin_cpp (зависит от plugin_base)
# ============================================================================

# Исходные файлы match_notifier_plugin
set(MATCH_NOTIFIER_PLUGIN_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/src/match_notifier_plugin.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/bindings/match_notifier_plugin_bindings.cpp
)

# Заголовочные файлы match_notifier_plugin
set(MATCH_NOTIFIER_PLUGIN_HEADERS
    ${CMAKE_CURRENT_SOURCE_DIR}/include/match_notifier_plugin.hpp
)

# Создание библиотеки match_notifier_plugin_cpp
add_library(match_notifier_plugin_cpp SHARED 
    ${MATCH_NOTIFIER_PLUGIN_SOURCES}
    ${MATCH_NOTIFIER_PLUGIN_HEADERS}
)

# Флаги компиляции для match_notifier_plugin
target_compile_options(match_notifier_plugin_cpp PRIVATE
    -O3
    -fPIC
    -std=c++17
)

# Include директории для match_notifier_plugin
target_include_directories(match_notifier_plugin_cpp 
    PUBLIC 
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
        $<BUILD_INTERFACE:${MONITOR_CPP_INCLUDE_DIR}>
    PRIVATE
        ${Python_INCLUDE_DIRS}
)

# Директивы препроцессора
target_compile_definitions(match_notifier_plugin_cpp 
    PRIVATE 
        PYBIND11_DETAIL_ABI 
        PYBIND11_PLUGIN_NAME="match_notifier_plugin_cpp"
)

# Настройка pybind11 модуля
pybind11_add_module(match_notifier_plugin_cpp 
    ${MATCH_NOTIFIER_PLUGIN_SOURCES}
    ${MATCH_NOTIFIER_PLUGIN_HEADERS}
)

# Линковка - зависимость от plugin_base_cpp
target_link_libraries(match_notifier_plugin_cpp 
    PRIVATE 
        pybind11::module 
        pybind11::embed
        plugin_base_cpp
)

# Свойства модуля match_notifier_plugin
set_target_properties(match_notifier_plugin_cpp PROPERTIES
    PREFIX ""
    OUTPUT_NAME "match_notifier_plugin_cpp"
    SUFFIX ".cpython-${PYTHON_VERSION_MAJOR}${PYTHON_VERSION_MINOR}-${CMAKE_SYSTEM_PROCESSOR}.so"
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
)

# Правила установки
install(TARGETS match_notifier_plugin_cpp 
    LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}
)

# ============================================================================
# Модуль 4: final_stats_plugin_cpp (зависит от plugin_base)
# ============================================================================

# Исходные файлы final_stats_plugin
set(FINAL_STATS_PLUGIN_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/src/final_stats_plugin.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/bindings/final_stats_plugin_bindings.cpp
)

# Заголовочные файлы final_stats_plugin
set(FINAL_STATS_PLUGIN_HEADERS
    ${CMAKE_CURRENT_SOURCE_DIR}/include/final_stats_plugin.hpp
)

# Создание библиотеки final_stats_plugin_cpp
add_library(final_stats_plugin_cpp SHARED 
    ${FINAL_STATS_PLUGIN_SOURCES}
    ${FINAL_STATS_PLUGIN_HEADERS}
)

# Флаги компиляции для final_stats_plugin
target_compile_options(final_stats_plugin_cpp PRIVATE
    -O3
    -fPIC
    -std=c++17
)

# Include директории для final_stats_plugin
target_include_directories(final_stats_plugin_cpp 
    PUBLIC 
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
        $<BUILD_INTERFACE:${MONITOR_CPP_INCLUDE_DIR}>
    PRIVATE
        ${Python_INCLUDE_DIRS}
)

# Директивы препроцессора
target_compile_definitions(final_stats_plugin_cpp 
    PRIVATE 
        PYBIND11_DETAIL_ABI 
        PYBIND11_PLUGIN_NAME="final_stats_plugin_cpp"
)

# Настройка pybind11 модуля
pybind11_add_module(final_stats_plugin_cpp 
    ${FINAL_STATS_PLUGIN_SOURCES}
    ${FINAL_STATS_PLUGIN_HEADERS}
)

# Линковка - зависимость от plugin_base_cpp
target_link_libraries(final_stats_plugin_cpp 
    PRIVATE 
        pybind11::module 
        pybind11::embed
        plugin_base_cpp
)

# Свойства модуля final_stats_plugin
set_target_properties(final_stats_plugin_cpp PROPERTIES
    PREFIX ""
    OUTPUT_NAME "final_stats_plugin_cpp"
    SUFFIX ".cpython-${PYTHON_VERSION_MAJOR}${PYTHON_VERSION_MINOR}-${CMAKE_SYSTEM_PROCESSOR}.so"
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
)

# Правила установки
install(TARGETS final_stats_plugin_cpp 
    LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}
)

# ============================================================================
# Группы файлов для IDE
# ============================================================================

# plugin_base
source_group("Source Files" FILES ${PLUGIN_BASE_SOURCES})
source_group("Header Files" FILES ${PLUGIN_BASE_HEADERS})

# live_stats_plugin
source_group("Source Files" FILES ${LIVE_STATS_PLUGIN_SOURCES})
source_group("Header Files" FILES ${LIVE_STATS_PLUGIN_HEADERS})

# match_notifier_plugin
source_group("Source Files" FILES ${MATCH_NOTIFIER_PLUGIN_SOURCES})
source_group("Header Files" FILES ${MATCH_NOTIFIER_PLUGIN_HEADERS})

# final_stats_plugin
source_group("Source Files" FILES ${FINAL_STATS_PLUGIN_SOURCES})
source_group("Header Files" FILES ${FINAL_STATS_PLUGIN_HEADERS})

# ============================================================================
# Вывод информации о сборке
# ============================================================================

message(STATUS "=== Building monitor_plugins_cpp ===")
message(STATUS "Python version: ${Python_VERSION}")
message(STATUS "Python include: ${Python_INCLUDE_DIRS}")
message(STATUS "Python library: ${Python_LIBRARY}")
message(STATUS "PyBind11 version: ${pybind11_VERSION}")
message(STATUS "Include directory: ${MONITOR_CPP_INCLUDE_DIR}")
message(STATUS "Output directory: ${CMAKE_CURRENT_SOURCE_DIR}")

# Список модулей для сборки
add_custom_target(build_all_plugins ALL
    DEPENDS 
        plugin_base_cpp
        live_stats_plugin_cpp
        match_notifier_plugin_cpp
        final_stats_plugin_cpp
    COMMENT "Building all monitor plugins"
)

# Цель для сборки только базового плагина
add_custom_target(build_plugin_base
    DEPENDS plugin_base_cpp
    COMMENT "Building plugin_base_cpp"
)

# Цель для сборки всех специфичных плагинов
add_custom_target(build_monitor_plugins
    DEPENDS 
        live_stats_plugin_cpp
        match_notifier_plugin_cpp
        final_stats_plugin_cpp
    COMMENT "Building monitor plugins (excluding base)"
)
