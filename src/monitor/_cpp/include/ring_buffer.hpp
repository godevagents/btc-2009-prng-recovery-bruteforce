// FILE: src/monitor/_cpp/include/ring_buffer.hpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Шаблонный кольцевой буфер (Ring Buffer) для хранения истории метрик с фиксированным максимальным размером.
// SCOPE: Утилиты, контейнеры данных
// INPUT: Тип элемента T, максимальный размер MaxSize
// OUTPUT: Класс кольцевого буфера с операциями push, get_all, clear, size, is_empty
// KEYWORDS: [DOMAIN(8): DataStructure; CONCEPT(7): RingBuffer; TECH(5): Template]
// END_MODULE_CONTRACT

#ifndef WALLET_MONITOR_RING_BUFFER_HPP
#define WALLET_MONITOR_RING_BUFFER_HPP

#include <vector>
#include <algorithm>
#include <stdexcept>

// START_TEMPLATE_RING_BUFFER
// START_CONTRACT:
// PURPOSE: Шаблонный кольцевой буфер для эффективного хранения истории с ограниченным размером.
// ATTRIBUTES:
// - T: Тип хранимых элементов
// - size_t MaxSize: Максимальное количество элементов
// METHODS:
// - push: Добавление элемента с автоматическим удалением старых
// - get_all: Получение всех элементов в векторе
// - clear: Очистка буфера
// - size: Получение текущего количества элементов
// - is_empty: Проверка на пустоту
// - operator[]: Доступ по индексу
// KEYWORDS: [PATTERN(7): Template; DOMAIN(8): Container; CONCEPT(7): CircularBuffer]
// END_CONTRACT

template<typename T, size_t MaxSize>
class RingBuffer {
public:
    // START_CONSTRUCTOR_RING_BUFFER
    // START_CONTRACT:
    // PURPOSE: Конструктор кольцевого буфера
    // OUTPUTS: Пустой буфер
    // KEYWORDS: [CONCEPT(5): Initialization]
    // END_CONTRACT
    RingBuffer() : _data(MaxSize), _head(0), _count(0) {}

    // START_METHOD_PUSH
    // START_CONTRACT:
    // PURPOSE: Добавление элемента в буфер. При заполнении перезаписывает старые элементы.
    // INPUTS:
    // - const T& value: Значение для добавления
    // OUTPUTS: void
    // SIDE_EFFECTS: Обновляет индекс головы и счетчик элементов
    // KEYWORDS: [CONCEPT(6): Enqueue]
    // END_CONTRACT
    void push(const T& value) {
        _data[_head] = value;
        _head = (_head + 1) % MaxSize;
        if (_count < MaxSize) {
            _count++;
        }
    }

    // START_METHOD_GET_ALL
    // START_CONTRACT:
    // PURPOSE: Получение всех элементов буфера в порядке от старых к новым
    // OUTPUTS: std::vector<T> — вектор всех элементов
    // KEYWORDS: [CONCEPT(5): Getter]
    // END_CONTRACT
    std::vector<T> get_all() const {
        std::vector<T> result;
        result.reserve(_count);
        if (_count == 0) {
            return result;
        }
        
        size_t start = (_count < MaxSize) ? 0 : _head;
        for (size_t i = 0; i < _count; ++i) {
            result.push_back(_data[(start + i) % MaxSize]);
        }
        return result;
    }

    // START_METHOD_CLEAR
    // START_CONTRACT:
    // PURPOSE: Очистка буфера
    // OUTPUTS: void
    // KEYWORDS: [CONCEPT(6): Cleanup]
    // END_CONTRACT
    void clear() {
        _head = 0;
        _count = 0;
    }

    // START_METHOD_SIZE
    // START_CONTRACT:
    // PURPOSE: Получение текущего количества элементов
    // OUTPUTS: size_t — количество элементов
    // KEYWORDS: [CONCEPT(5): Getter)]
    // END_CONTRACT
    size_t size() const { return _count; }

    // START_METHOD_IS_EMPTY
    // START_CONTRACT:
    // PURPOSE: Проверка буфера на пустоту
    // OUTPUTS: bool — true если буфер пуст
    // KEYWORDS: [CONCEPT(5): Checker]
    // END_CONTRACT
    bool is_empty() const { return _count == 0; }

    // START_METHOD_AT
    // START_CONTRACT:
    // PURPOSE: Доступ к элементу по индексу (от старых к новым)
    // INPUTS:
    // - size_t index: Индекс элемента
    // OUTPUTS: T& — ссылка на элемент
    // KEYWORDS: [CONCEPT(5): Accessor]
    // END_CONTRACT
    T& at(size_t index) {
        if (index >= _count) {
            throw std::out_of_range("RingBuffer index out of range");
        }
        size_t start = (_count < MaxSize) ? 0 : _head;
        return _data[(start + index) % MaxSize];
    }

    // START_METHOD_LAST
    // START_CONTRACT:
    // PURPOSE: Получение последнего добавленного элемента
    // OUTPUTS: T* — указатель на последний элемент или nullptr
    // KEYWORDS: [CONCEPT(5): Accessor]
    // END_CONTRACT
    T* last() {
        if (_count == 0) return nullptr;
        size_t last_index = (_head + MaxSize - 1) % MaxSize;
        return &_data[last_index];
    }

    // START_METHOD_LAST_CONST
    // START_CONTRACT:
    // PURPOSE: Получение последнего добавленного элемента (const версия)
    // OUTPUTS: const T* — указатель на последний элемент или nullptr
    // KEYWORDS: [CONCEPT(5): Accessor]
    // END_CONTRACT
    const T* last() const {
        if (_count == 0) return nullptr;
        size_t last_index = (_head + MaxSize - 1) % MaxSize;
        return &_data[last_index];
    }

    // START_OPERATOR_BRACKET
    // START_CONTRACT:
    // PURPOSE: Оператор доступа по индексу
    // INPUTS:
    // - size_t index: Индекс
    // OUTPUTS: T& — ссылка на элемент
    // KEYWORDS: [CONCEPT(5): Accessor]
    // END_CONTRACT
    T& operator[](size_t index) {
        size_t start = (_count < MaxSize) ? 0 : _head;
        return _data[(start + index) % MaxSize];
    }

    const T& operator[](size_t index) const {
        size_t start = (_count < MaxSize) ? 0 : _head;
        return _data[(start + index) % MaxSize];
    }

private:
    std::vector<T> _data;
    size_t _head;
    size_t _count;
};
// END_TEMPLATE_RING_BUFFER

#endif // WALLET_MONITOR_RING_BUFFER_HPP
