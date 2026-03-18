// FILE: src/core/entropy_cache.cpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Определение глобальной переменной g_entropy_cache для всех модулей.
// SCOPE: Глобальное определение символа g_entropy_cache для解決 undefined symbol error.
// KEYWORDS: [DOMAIN(8): EntropyCache; CONCEPT(7): GlobalVariable]
// END_MODULE_CONTRACT

#include "entropy_pipeline_cache.hpp"
#include <memory>

// Global definition of entropy cache - used by all modules
// This file should be compiled into every .so module to provide the symbol
std::shared_ptr<EntropyPipelineCache> g_entropy_cache;
