// FILE: src/core/entropy_engine.cpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Реализация координатора источников энтропии.
// SCOPE: Управление источниками, координация, комбинирование энтропии
// INPUT: Вызовы методов из Python или C++ кода
// OUTPUT: Энтропия в виде вектора байтов
// KEYWORDS: [DOMAIN(10): EntropyCoordination; CONCEPT(9): SourceManagement; CONCEPT(8): EntropyCombining]
// END_MODULE_CONTRACT

#include "entropy_engine.hpp"
#include <algorithm>
#include <cstring>
#include "poll.h"
#include "hkey_performance_data.h"

// START_CONSTRUCTOR_EntropyEngine
// START_CONTRACT:
// PURPOSE: Конструктор по умолчанию - инициализация координатора.
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
EntropyEngine::EntropyEngine() : initialized(false) {
    // Инициализация выполняется в конструкторе
    initialized = true;
    
    // Регистрируем источники энтропии
    register_default_sources();
}
// END_CONSTRUCTOR_EntropyEngine

// START_METHOD_register_default_sources
// START_CONTRACT:
// PURPOSE: Регистрация источников энтропии по умолчанию.
// KEYWORDS: [CONCEPT(5): Initialization; CONCEPT(7): Registration]
// END_CONTRACT
void EntropyEngine::register_default_sources() {
    // Регистрируем RandPoll источник через fallback
    add_source("rand_poll", [](size_t size) -> std::vector<uint8_t> {
        RandPollFallback poll(0);
        return poll.get_entropy(size);
    });
    
    // Регистрируем HKey источник
    add_source("hkey", [](size_t size) -> std::vector<uint8_t> {
        auto data = generate_hkey_performance_data_legacy(0);
        // Обрезаем или дополняем до нужного размера
        if (data.size() >= size) {
            return std::vector<uint8_t>(data.begin(), data.begin() + size);
        }
        // Дополняем повторением
        std::vector<uint8_t> result;
        while (result.size() < size) {
            result.insert(result.end(), data.begin(), data.end());
        }
        return std::vector<uint8_t>(result.begin(), result.begin() + size);
    });
    
    // Регистрируем bitmap источник (использует rand_poll)
    add_source("bitmap", [](size_t size) -> std::vector<uint8_t> {
        RandPollFallback poll(0);
        return poll.get_entropy(size);
    });
}
// END_METHOD_register_default_sources

// START_METHOD_add_source
// START_CONTRACT:
// PURPOSE: Добавление источника энтропии в координатор.
// KEYWORDS: [DOMAIN(9): SourceManagement; CONCEPT(7): Registration]
// END_CONTRACT
void EntropyEngine::add_source(const std::string& name, EntropyGenerator generator) {
    std::lock_guard<std::mutex> lock(m_mutex);
    
    // Проверяем, не существует ли уже такой источник
    if (sources.find(name) != sources.end()) {
        // Заменяем существующий источник
        sources[name] = std::move(generator);
        return;
    }
    
    // Добавляем новый источник
    sources[name] = std::move(generator);
}
// END_METHOD_add_source

// START_METHOD_remove_source
// START_CONTRACT:
// PURPOSE: Удаление источника энтропии из координатора.
// KEYWORDS: [DOMAIN(9): SourceManagement; CONCEPT(7): Deregistration]
// END_CONTRACT
void EntropyEngine::remove_source(const std::string& source_name) {
    std::lock_guard<std::mutex> lock(m_mutex);
    
    auto it = sources.find(source_name);
    if (it != sources.end()) {
        sources.erase(it);
    }
}
// END_METHOD_remove_source

// START_METHOD_get_available_sources
// START_CONTRACT:
// PURPOSE: Получение списка доступных источников энтропии.
// KEYWORDS: [DOMAIN(8): SourceDiscovery; CONCEPT(6): Introspection]
// END_CONTRACT
std::vector<std::string> EntropyEngine::get_available_sources() const {
    std::lock_guard<std::mutex> lock(m_mutex);
    
    std::vector<std::string> available;
    for (const auto& pair : sources) {
        available.push_back(pair.first);
    }
    return available;
}
// END_METHOD_get_available_sources

// START_METHOD_get_entropy
// START_CONTRACT:
// PURPOSE: Получение энтропии от указанного источника.
// KEYWORDS: [DOMAIN(10): EntropyGeneration; CONCEPT(8): SourceAccess]
// END_CONTRACT
std::vector<uint8_t> EntropyEngine::get_entropy(size_t size, const std::string& source_name) {
    std::lock_guard<std::mutex> lock(m_mutex);
    
    // Если имя источника указано, ищем конкретный источник
    if (!source_name.empty()) {
        auto it = sources.find(source_name);
        if (it == sources.end()) {
            throw std::runtime_error("Источник " + source_name + " не найден");
        }
        
        // Вызываем генератор
        return it->second(size);
    }
    
    // Берем первый доступный источник
    if (sources.empty()) {
        throw std::runtime_error("Нет доступных источников энтропии");
    }
    
    auto it = sources.begin();
    return it->second(size);
}
// END_METHOD_get_entropy

// START_METHOD_get_combined_entropy
// START_CONTRACT:
// PURPOSE: Получение комбинированной энтропии из всех доступных источников.
// KEYWORDS: [DOMAIN(10): EntropyCombining; CONCEPT(9): Aggregation]
// END_CONTRACT
std::vector<uint8_t> EntropyEngine::get_combined_entropy(size_t size, CombineStrategy strategy) {
    std::lock_guard<std::mutex> lock(m_mutex);
    
    if (sources.empty()) {
        throw std::runtime_error("Нет доступных источников энтропии для комбинирования");
    }
    
    // Сбор энтропии от всех источников
    std::vector<std::vector<uint8_t>> entropy_list;
    
    for (const auto& pair : sources) {
        try {
            auto entropy = pair.second(size);
            entropy_list.push_back(std::move(entropy));
        } catch (...) {
            // Пропускаем источники с ошибками
            continue;
        }
    }
    
    if (entropy_list.empty()) {
        throw std::runtime_error("Не удалось получить энтропию ни от одного источника");
    }
    
    // Комбинирование согласно стратегии
    if (strategy == CombineStrategy::XOR) {
        return combine_xor(entropy_list, size);
    } else {
        return combine_hash(entropy_list, size);
    }
}
// END_METHOD_get_combined_entropy

// START_METHOD_get_source_status
// START_CONTRACT:
// PURPOSE: Получение статуса всех источников энтропии.
// KEYWORDS: [CONCEPT(6): Introspection; DOMAIN(8): StatusReporting]
// END_CONTRACT
std::vector<SourceStatus> EntropyEngine::get_source_status() const {
    std::lock_guard<std::mutex> lock(m_mutex);
    
    std::vector<SourceStatus> status_list;
    
    for (const auto& pair : sources) {
        SourceStatus status;
        status.name = pair.first;
        status.available = true;  // Если источник в словаре, он доступен
        status.initialized = initialized;
        status_list.push_back(status);
    }
    
    return status_list;
}
// END_METHOD_get_source_status

// START_METHOD_is_initialized
// START_CONTRACT:
// PURPOSE: Проверка состояния инициализации движка.
// KEYWORDS: [PATTERN(5): Getter; CONCEPT(5): State]
// END_CONTRACT
bool EntropyEngine::is_initialized() const {
    return initialized;
}
// END_METHOD_is_initialized

// START_METHOD_source_count
// START_CONTRACT:
// PURPOSE: Получение количества зарегистрированных источников.
// KEYWORDS: [PATTERN(5): Getter; CONCEPT(5): Count]
// END_CONTRACT
size_t EntropyEngine::source_count() const {
    std::lock_guard<std::mutex> lock(m_mutex);
    return sources.size();
}
// END_METHOD_source_count

// START_METHOD_combine_xor
// START_CONTRACT:
// PURPOSE: Комбинирование энтропии с использованием операции XOR.
// KEYWORDS: [CONCEPT(8): XOR; TECH(6): BitwiseOperation]
// END_CONTRACT
std::vector<uint8_t> EntropyEngine::combine_xor(const std::vector<std::vector<uint8_t>>& entropy_list, size_t size) {
    // Инициализация результата нулями
    std::vector<uint8_t> result(size, 0);
    
    // XOR всех источников
    for (const auto& entropy : entropy_list) {
        // Дополняем или обрезаем до нужного размера
        auto padded = pad_to_size(entropy, size);
        
        for (size_t i = 0; i < size; ++i) {
            result[i] ^= padded[i];
        }
    }
    
    return result;
}
// END_METHOD_combine_xor

// START_METHOD_combine_hash
// START_CONTRACT:
// PURPOSE: Комбинирование энтропии через хеширование.
// KEYWORDS: [CONCEPT(9): Hashing; TECH(7): SHA256]
// END_CONTRACT
std::vector<uint8_t> EntropyEngine::combine_hash(const std::vector<std::vector<uint8_t>>& entropy_list, size_t size) {
    // Конкатенация всех источников
    std::vector<uint8_t> combined;
    for (const auto& entropy : entropy_list) {
        combined.insert(combined.end(), entropy.begin(), entropy.end());
    }
    
    // Вычисление SHA-256 хеша
    std::vector<uint8_t> hash_result(SHA256_DIGEST_LENGTH);
    SHA256(combined.data(), combined.size(), hash_result.data());
    
    // Обрезаем до нужного размера
    if (size <= SHA256_DIGEST_LENGTH) {
        return std::vector<uint8_t>(hash_result.begin(), hash_result.begin() + size);
    }
    
    // Если запрошенный размер больше, чем SHA256, дополняем
    std::vector<uint8_t> result(size);
    size_t offset = 0;
    
    while (offset < size) {
        size_t remaining = size - offset;
        size_t to_copy = (remaining >= SHA256_DIGEST_LENGTH) ? SHA256_DIGEST_LENGTH : remaining;
        
        // Пересчитываем хеш счетчиком для получения дополнительных данных
        std::vector<uint8_t> counter_data = combined;
        // Добавляем счетчик к данным
        uint8_t counter_bytes[4];
        counter_bytes[0] = (offset >> 24) & 0xFF;
        counter_bytes[1] = (offset >> 16) & 0xFF;
        counter_bytes[2] = (offset >> 8) & 0xFF;
        counter_bytes[3] = offset & 0xFF;
        counter_data.insert(counter_data.end(), counter_bytes, counter_bytes + 4);
        
        std::vector<uint8_t> hash_chunk(SHA256_DIGEST_LENGTH);
        SHA256(counter_data.data(), counter_data.size(), hash_chunk.data());
        
        std::copy(hash_chunk.begin(), hash_chunk.begin() + to_copy, result.begin() + offset);
        offset += to_copy;
    }
    
    return result;
}
// END_METHOD_combine_hash

// START_METHOD_pad_to_size
// START_CONTRACT:
// PURPOSE: Дополнение данных до нужного размера.
// KEYWORDS: [CONCEPT(6): Padding; TECH(5): DataProcessing]
// END_CONTRACT
std::vector<uint8_t> EntropyEngine::pad_to_size(const std::vector<uint8_t>& data, size_t size) const {
    if (data.size() >= size) {
        return std::vector<uint8_t>(data.begin(), data.begin() + size);
    }
    
    // Дополняем повторением данных
    std::vector<uint8_t> result(size);
    size_t offset = 0;
    
    while (offset < size) {
        size_t remaining = size - offset;
        size_t chunk_size = (remaining >= data.size()) ? data.size() : remaining;
        
        std::copy(data.begin(), data.begin() + chunk_size, result.begin() + offset);
        offset += chunk_size;
    }
    
    return result;
}
// END_METHOD_pad_to_size
