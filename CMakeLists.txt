cmake_minimum_required(VERSION 3.18)
project(WalletDatGenerator LANGUAGES CXX)

# =============================================================================
# VERSION
# =============================================================================
set(ENTROPY_VERSION_MAJOR 1)
set(ENTROPY_VERSION_MINOR 0)
set(ENTROPY_VERSION_PATCH 0)
set(ENTROPY_VERSION "${ENTROPY_VERSION_MAJOR}.${ENTROPY_VERSION_MINOR}.${ENTROPY_VERSION_PATCH}")

# =============================================================================
# OUTPUT DIRECTORY
# =============================================================================
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/build/compilation)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/build/compilation)

# =============================================================================
# PYTHON CONFIGURATION
# =============================================================================
find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

# =============================================================================
# OPENSSL CONFIGURATION
# =============================================================================
find_package(OpenSSL REQUIRED)

# =============================================================================
# CORE MODULES (rand_add, orchestrator, pybind11_wrapper)
# =============================================================================
pybind11_add_module(core_cpp
    src/core/pybind11_wrapper.cpp
    src/core/rand_add.cpp
    src/core/orchestrator.cpp
)

target_include_directories(core_cpp PRIVATE
    ${OpenSSL_INCLUDE_DIR}
    ${Python_INCLUDE_DIRS}
    ${CMAKE_CURRENT_SOURCE_DIR}/src/core
    ${CMAKE_CURRENT_SOURCE_DIR}/src/plugins/cpu/rand_poll
    ${CMAKE_CURRENT_SOURCE_DIR}/src/plugins/cpu/bitmap
    ${CMAKE_CURRENT_SOURCE_DIR}/src/plugins/cpu/randaddseed
    ${CMAKE_CURRENT_SOURCE_DIR}/cache
    ${CMAKE_CURRENT_SOURCE_DIR}/cache/include
)

target_link_libraries(core_cpp PRIVATE
    ${OpenSSL_LIBRARIES}
)

target_compile_options(core_cpp PRIVATE
    -O3
    -fPIC
    -std=c++14
    -pthread
)

# =============================================================================
# CPU PLUGINS: bitmap (CPU with pybind11)
# =============================================================================
pybind11_add_module(getbitmaps_cpp
    src/plugins/cpu/bitmap/pybind11_wrapper.cpp
)

target_include_directories(getbitmaps_cpp PRIVATE
    ${Python_INCLUDE_DIRS}
    ${CMAKE_CURRENT_SOURCE_DIR}/src/core
    ${CMAKE_CURRENT_SOURCE_DIR}/src/plugins/cpu/bitmap
    ${CMAKE_CURRENT_SOURCE_DIR}/src/plugins/cpu/randaddseed
    ${CMAKE_CURRENT_SOURCE_DIR}/cache/include
)

target_link_libraries(getbitmaps_cpp PRIVATE
    ${OPENSSL_LIBRARIES}
)

target_compile_options(getbitmaps_cpp PRIVATE
    -O3
    -fPIC
    -std=c++14
)

# =============================================================================
# CPU PLUGINS: rand_poll (CPU with pybind11)
# =============================================================================
pybind11_add_module(rand_poll_cpp
    src/plugins/cpu/rand_poll/pybind11_wrapper.cpp
    src/plugins/cpu/rand_poll/poll.cpp
    src/core/rand_add.cpp
    src/core/entropy_cache.cpp
    src/plugins/cpu/randaddseed/hkey_performance_data.cpp
)

target_include_directories(rand_poll_cpp PRIVATE
    ${OpenSSL_INCLUDE_DIR}
    ${Python_INCLUDE_DIRS}
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/src/core
    ${CMAKE_CURRENT_SOURCE_DIR}/src/plugins/cpu/rand_poll
    ${CMAKE_CURRENT_SOURCE_DIR}/src/plugins/cpu/randaddseed
    ${CMAKE_CURRENT_SOURCE_DIR}/cache/include
)

target_link_libraries(rand_poll_cpp PRIVATE
    ${OpenSSL_LIBRARIES}
    crypto
)

target_compile_options(rand_poll_cpp PRIVATE
    -O3
    -fPIC
    -std=c++14
    -pthread
)

# =============================================================================
# CPU PLUGINS: hkey_performance_data (CPU with pybind11)
# =============================================================================
pybind11_add_module(hkey_performance_data_cpp
    src/plugins/cpu/randaddseed/pybind11_wrapper.cpp
    src/plugins/cpu/randaddseed/hkey_performance_data.cpp
    src/plugins/cpu/randaddseed/QueryPerformanceCounter.cpp
    src/core/rand_add.cpp
    src/core/entropy_cache.cpp
)

target_include_directories(hkey_performance_data_cpp PRIVATE
    ${OpenSSL_INCLUDE_DIR}
    ${Python_INCLUDE_DIRS}
    ${CMAKE_SOURCE_DIR}/src/core
    ${CMAKE_SOURCE_DIR}/src/plugins/cpu/randaddseed
    ${CMAKE_SOURCE_DIR}/cache
    ${CMAKE_SOURCE_DIR}/cache/include
)

target_link_libraries(hkey_performance_data_cpp PRIVATE
    ${OpenSSL_LIBRARIES}
    crypto
)

target_compile_options(hkey_performance_data_cpp PRIVATE
    -O3
    -fPIC
    -std=c++14
    -pthread
)

# =============================================================================
# ENTROPY ENGINE MODULE: EntropyEngine (CPU with pybind11)
# Full version with all entropy sources (rand_poll, bitmap, hkey)
# =============================================================================
pybind11_add_module(entropy_engine_cpp
    src/core/entropy_engine_bindings.cpp
    src/core/entropy_engine.cpp
    src/plugins/cpu/rand_poll/poll.cpp
    src/core/rand_add.cpp
    src/core/entropy_cache.cpp
    src/plugins/cpu/randaddseed/hkey_performance_data.cpp
)

target_include_directories(entropy_engine_cpp PRIVATE
    ${OpenSSL_INCLUDE_DIR}
    ${Python_INCLUDE_DIRS}
    ${CMAKE_CURRENT_SOURCE_DIR}/src/core
    ${CMAKE_CURRENT_SOURCE_DIR}/src/plugins/cpu/rand_poll
    ${CMAKE_CURRENT_SOURCE_DIR}/src/plugins/cpu/bitmap
    ${CMAKE_CURRENT_SOURCE_DIR}/src/plugins/cpu/randaddseed
    ${CMAKE_CURRENT_SOURCE_DIR}/cache
    ${CMAKE_CURRENT_SOURCE_DIR}/cache/include
)

target_link_libraries(entropy_engine_cpp PRIVATE
    ${OpenSSL_LIBRARIES}
    crypto
)

target_compile_options(entropy_engine_cpp PRIVATE
    -O3
    -fPIC
    -std=c++14
    -pthread
)

# =============================================================================
# CACHE MODULE: EntropyPipelineCache (CPU with pybind11)
# =============================================================================
pybind11_add_module(entropy_pipeline_cache_cpp
    cache/bindings/entropy_pipeline_cache_bindings.cpp
    cache/src/entropy_pipeline_cache.cpp
)

target_include_directories(entropy_pipeline_cache_cpp PRIVATE
    ${Python_INCLUDE_DIRS}
    ${CMAKE_CURRENT_SOURCE_DIR}/cache/include
)

target_compile_options(entropy_pipeline_cache_cpp PRIVATE
    -O3
    -fPIC
    -std=c++11
)

# =============================================================================
# WALLET PLUGINS: batch_gen (Python with pybind11)
# =============================================================================
pybind11_add_module(batch_gen_cpp
    src/plugins/wallet/batch_gen/pybind11_wrapper.cpp
    src/plugins/wallet/batch_gen/batch_gen.cpp
    src/plugins/crypto/ecdsa_keys/ecdsa_keys.cpp
)

target_include_directories(batch_gen_cpp PRIVATE
    ${OpenSSL_INCLUDE_DIR}
    ${Python_INCLUDE_DIRS}
    ${CMAKE_CURRENT_SOURCE_DIR}/src/plugins/wallet/batch_gen
    ${CMAKE_CURRENT_SOURCE_DIR}/src/plugins/crypto/ecdsa_keys
)

target_link_libraries(batch_gen_cpp PRIVATE
    ${OpenSSL_LIBRARIES}
)

target_compile_options(batch_gen_cpp PRIVATE
    -O3
    -fPIC
    -std=c++14
)

# =============================================================================
# WALLET PLUGINS: wallet_dat (Python with pybind11)
# =============================================================================
pybind11_add_module(wallet_dat_cpp
    src/plugins/wallet/wallet_dat/pybind11_wrapper.cpp
    src/plugins/wallet/wallet_dat/wallet_dat.cpp
)

target_include_directories(wallet_dat_cpp PRIVATE
    ${OpenSSL_INCLUDE_DIR}
    ${Python_INCLUDE_DIRS}
    ${CMAKE_CURRENT_SOURCE_DIR}/src/plugins/wallet/wallet_dat
)

target_link_libraries(wallet_dat_cpp PRIVATE
    ${OpenSSL_LIBRARIES}
)

target_compile_options(wallet_dat_cpp PRIVATE
    -O3
    -fPIC
    -std=c++17
)

# =============================================================================
# WALLET PLUGINS: address_matcher (Python with pybind11)
# =============================================================================
pybind11_add_module(address_matcher_cpp
    src/plugins/wallet/address_matcher/pybind11_wrapper.cpp
    src/plugins/wallet/address_matcher/address_matcher.cpp
)

target_include_directories(address_matcher_cpp PRIVATE
    ${OpenSSL_INCLUDE_DIR}
    ${Python_INCLUDE_DIRS}
    ${CMAKE_CURRENT_SOURCE_DIR}/src/plugins/wallet/address_matcher
)

target_link_libraries(address_matcher_cpp PRIVATE
    ${OpenSSL_LIBRARIES}
)

target_compile_options(address_matcher_cpp PRIVATE
    -O3
    -fPIC
    -std=c++14
)

# =============================================================================
# INSTALLATION
# =============================================================================
install(
    TARGETS core_cpp getbitmaps_cpp rand_poll_cpp hkey_performance_data_cpp 
            entropy_pipeline_cache_cpp batch_gen_cpp wallet_dat_cpp address_matcher_cpp
            entropy_engine_cpp
    DESTINATION build/compilation
)

# =============================================================================
# SUMMARY
# =============================================================================
message(STATUS "==============================================")
message(STATUS "WalletDatGenerator CMake Configuration Summary")
message(STATUS "==============================================")
message(STATUS "Version: ${ENTROPY_VERSION}")
message(STATUS "Python: ${Python_VERSION}")
message(STATUS "OpenSSL: ${OpenSSL_VERSION}")
message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "Output Directory: ${CMAKE_LIBRARY_OUTPUT_DIRECTORY}")
message(STATUS "==============================================")
