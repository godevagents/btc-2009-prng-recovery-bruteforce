// FILE: src/monitor_cpp/plugins/match_notifier_plugin.cpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Реализация плагина уведомлений о найденных совпадениях
// SCOPE: Методы класса MatchNotifierPlugin, обработка совпадений, отправка уведомлений
// KEYWORDS: [DOMAIN(9): Notifications; TECH(7): RealTime; TECH(6): C++17]
// END_MODULE_CONTRACT

#include "match_notifier_plugin.hpp"
#include <algorithm>
#include <ctime>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <random>
#include <cstdlib>

//==============================================================================
// IMPLEMENTATION: MatchInfo
//==============================================================================

// START_CONSTRUCTOR_MATCH_INFO_DEFAULT
// START_CONTRACT:
// PURPOSE: Конструктор по умолчанию
// OUTPUTS: Созданный объект MatchInfo
// END_CONTRACT
MatchInfo::MatchInfo()
    : timestamp(std::chrono::system_clock::now())
    , iteration(0)
    , match_number(0)
    , address("")
    , wallet_name("Unknown")
    , list_name("Unknown")
    , priority(NotificationPriority::NORMAL)
{}
// END_CONSTRUCTOR_MATCH_INFO_DEFAULT

// START_CONSTRUCTOR_MATCH_INFO_PARAMS
// START_CONTRACT:
// PURPOSE: Конструктор с основными параметрами
// INPUTS: iter — номер итерации, match_num — номер совпадения, addr — адрес
// OUTPUTS: Созданный объект MatchInfo
// END_CONTRACT
MatchInfo::MatchInfo(int64_t iter, int64_t match_num, const std::string& addr)
    : timestamp(std::chrono::system_clock::now())
    , iteration(iter)
    , match_number(match_num)
    , address(addr)
    , wallet_name("Unknown")
    , list_name("Unknown")
    , priority(NotificationPriority::NORMAL)
{}
// END_CONSTRUCTOR_MATCH_INFO_PARAMS

// START_METHOD_MATCH_INFO_TO_JSON
// START_CONTRACT:
// PURPOSE: Сериализация структуры в JSON строку
// OUTPUTS: std::string — JSON представление структуры
// KEYWORDS: [TECH(5): JSON; CONCEPT(7): Serialization]
// END_CONTRACT
std::string MatchInfo::to_json() const {
    std::ostringstream oss;
    oss << "{";
    oss << "\"timestamp\": \"" << get_timestamp_string() << "\",";
    oss << "\"iteration\": " << iteration << ",";
    oss << "\"match_number\": " << match_number << ",";
    oss << "\"address\": \"" << address << "\",";
    oss << "\"wallet_name\": \"" << wallet_name << "\",";
    oss << "\"list_name\": \"" << list_name << "\",";
    oss << "\"priority\": " << static_cast<int>(priority);
    
    if (private_key.has_value()) {
        oss << ",\"private_key\": \"" << private_key.value() << "\"";
    }
    
    oss << "}";
    return oss.str();
}
// END_METHOD_MATCH_INFO_TO_JSON

// START_METHOD_MATCH_INFO_TO_STRING
// START_CONTRACT:
// PURPOSE: Строковое представление структуры для логирования
// OUTPUTS: std::string — читаемое представление
// KEYWORDS: [CONCEPT(6): Stringify]
// END_CONTRACT
std::string MatchInfo::to_string() const {
    std::ostringstream oss;
    oss << "MatchInfo(match_number=" << match_number
        << ", iteration=" << iteration
        << ", address=" << address
        << ", priority=" << static_cast<int>(priority)
        << ", timestamp=" << get_timestamp_string() << ")";
    return oss.str();
}
// END_METHOD_MATCH_INFO_TO_STRING

// START_METHOD_MATCH_INFO_GET_TIMESTAMP_STRING
// START_CONTRACT:
// PURPOSE: Получение timestamp в читаемом формате ISO
// OUTPUTS: std::string — timestamp в формате ISO 8601
// KEYWORDS: [CONCEPT(6): Formatting]
// END_CONTRACT
std::string MatchInfo::get_timestamp_string() const {
    auto time_t_val = std::chrono::system_clock::to_time_t(timestamp);
    std::tm tm_val = *std::localtime(&time_t_val);
    
    std::ostringstream oss;
    oss << std::put_time(&tm_val, "%Y-%m-%dT%H:%M:%S");
    
    // Добавляем микросекунды
    auto duration = timestamp.time_since_epoch();
    auto micros = std::chrono::duration_cast<std::chrono::microseconds>(duration) % 1000000;
    oss << "." << std::setfill('0') << std::setw(6) << micros.count();
    
    return oss.str();
}
// END_METHOD_MATCH_INFO_GET_TIMESTAMP_STRING

//==============================================================================
// IMPLEMENTATION: MatchNotifierConfig
//==============================================================================

// START_CONSTRUCTOR_MATCH_NOTIFIER_CONFIG_DEFAULT
// START_CONTRACT:
// PURPOSE: Конструктор по умолчанию с настройками по умолчанию
// OUTPUTS: Созданный объект MatchNotifierConfig
// END_CONTRACT
MatchNotifierConfig::MatchNotifierConfig()
    : desktop_enabled(true)
    , sound_enabled(false)
    , log_enabled(true)
    , ui_enabled(true)
    , cooldown_seconds(5.0)
    , min_priority(NotificationPriority::LOW)
    , enabled_channels({NotificationChannel::CONSOLE, NotificationChannel::FILE})
{}
// END_CONSTRUCTOR_MATCH_NOTIFIER_CONFIG_DEFAULT

// START_CONSTRUCTOR_MATCH_NOTIFIER_CONFIG_PARAMS
// START_CONTRACT:
// PURPOSE: Конструктор с параметрами
// INPUTS: desktop, sound, log, ui — флаги включения, cooldown — кулдаун
// OUTPUTS: Созданный объект MatchNotifierConfig
// END_CONTRACT
MatchNotifierConfig::MatchNotifierConfig(bool desktop, bool sound, bool log, bool ui, double cooldown)
    : desktop_enabled(desktop)
    , sound_enabled(sound)
    , log_enabled(log)
    , ui_enabled(ui)
    , cooldown_seconds(cooldown)
    , min_priority(NotificationPriority::LOW)
    , enabled_channels({NotificationChannel::CONSOLE, NotificationChannel::FILE})
{}
// END_CONSTRUCTOR_MATCH_NOTIFIER_CONFIG_PARAMS

// START_METHOD_MATCH_NOTIFIER_CONFIG_IS_ANY_ENABLED
// START_CONTRACT:
// PURPOSE: Проверка включён ли хотя бы один тип уведомлений
// OUTPUTS: bool — true если хотя бы один тип включён
// KEYWORDS: [CONCEPT(5): Check]
// END_CONTRACT
bool MatchNotifierConfig::is_any_enabled() const {
    return desktop_enabled || sound_enabled || log_enabled || ui_enabled;
}
// END_METHOD_MATCH_NOTIFIER_CONFIG_IS_ANY_ENABLED

// START_METHOD_MATCH_NOTIFIER_CONFIG_RESET
// START_CONTRACT:
// PURPOSE: Сброс конфигурации к значениям по умолчанию
// OUTPUTS: void
// KEYWORDS: [CONCEPT(7): Reset]
// END_CONTRACT
void MatchNotifierConfig::reset() {
    desktop_enabled = true;
    sound_enabled = false;
    log_enabled = true;
    ui_enabled = true;
    cooldown_seconds = 5.0;
    min_priority = NotificationPriority::LOW;
    enabled_channels = {NotificationChannel::CONSOLE, NotificationChannel::FILE};
}
// END_METHOD_MATCH_NOTIFIER_CONFIG_RESET

// START_METHOD_MATCH_NOTIFIER_CONFIG_TO_STRING
// START_CONTRACT:
// PURPOSE: Строковое представление конфигурации
// OUTPUTS: std::string — читаемое представление
// KEYWORDS: [CONCEPT(6): Stringify]
// END_CONTRACT
std::string MatchNotifierConfig::to_string() const {
    std::ostringstream oss;
    oss << "MatchNotifierConfig(desktop=" << desktop_enabled
        << ", sound=" << sound_enabled
        << ", log=" << log_enabled
        << ", ui=" << ui_enabled
        << ", cooldown=" << cooldown_seconds << "s"
        << ", priority=" << static_cast<int>(min_priority) << ")";
    return oss.str();
}
// END_METHOD_MATCH_NOTIFIER_CONFIG_TO_STRING

//==============================================================================
// IMPLEMENTATION: MatchHistoryEntry
//==============================================================================

// START_CONSTRUCTOR_MATCH_HISTORY_ENTRY_DEFAULT
// START_CONTRACT:
// PURPOSE: Конструктор по умолчанию
// OUTPUTS: Созданный объект MatchHistoryEntry
// END_CONTRACT
MatchHistoryEntry::MatchHistoryEntry()
    : entry_id(0)
    , match()
    , notification_sent(false)
    , timestamp(std::chrono::system_clock::now())
{}
// END_CONSTRUCTOR_MATCH_HISTORY_ENTRY_DEFAULT

// START_CONSTRUCTOR_MATCH_HISTORY_ENTRY_PARAMS
// START_CONTRACT:
// PURPOSE: Конструктор с параметрами
// INPUTS: id — ID записи, info — информация о совпадении
// OUTPUTS: Созданный объект MatchHistoryEntry
// END_CONTRACT
MatchHistoryEntry::MatchHistoryEntry(uint64_t id, const MatchInfo& info)
    : entry_id(id)
    , match(info)
    , notification_sent(false)
    , timestamp(std::chrono::system_clock::now())
{}
// END_CONSTRUCTOR_MATCH_HISTORY_ENTRY_PARAMS

//==============================================================================
// IMPLEMENTATION: MatchNotifierPlugin
//==============================================================================

// START_FUNCTION_MATCH_NOTIFIER_PLUGIN_CONSTRUCTOR
// START_CONTRACT:
// PURPOSE: Конструктор плагина уведомлений
// OUTPUTS: Инициализированный объект MatchNotifierPlugin
// SIDE_EFFECTS: Создаёт логгер; инициализирует структуры данных
// TEST_CONDITIONS:
// - Объект должен быть готов к initialize()
// - История должна быть пустой
// END_CONTRACT
MatchNotifierPlugin::MatchNotifierPlugin()
    : m_info(PluginInfo(
        MATCH_NOTIFIER_PLUGIN_NAME,
        MATCH_NOTIFIER_PLUGIN_VERSION,
        "Match notifier plugin for wallet generation monitoring",
        "Wallet Generator Team"
    ))
    , m_logger("MatchNotifierPlugin")
{
    m_logger.debug("MatchNotifierPlugin constructed");
}
// END_FUNCTION_MATCH_NOTIFIER_PLUGIN_CONSTRUCTOR

// START_FUNCTION_MATCH_NOTIFIER_PLUGIN_DESTRUCTOR
// START_CONTRACT:
// PURPOSE: Деструктор плагина
// SIDE_EFFECTS: Вызывает shutdown() для корректного завершения
// END_CONTRACT
MatchNotifierPlugin::~MatchNotifierPlugin() {
    if (m_state.load() != PluginState::STOPPED && 
        m_state.load() != PluginState::UNINITIALIZED) {
        shutdown();
    }
}
// END_FUNCTION_MATCH_NOTIFIER_PLUGIN_DESTRUCTOR

//==============================================================================
// IPlugin Implementation
//==============================================================================

// START_FUNCTION_INITIALIZE
// START_CONTRACT:
// PURPOSE: Инициализация плагина
// SIDE_EFFECTS: Переводит плагин в состояние ACTIVE
// TEST_CONDITIONS: Плагин должен успешно инициализироваться
// END_CONTRACT
void MatchNotifierPlugin::initialize() {
    m_logger.info("Initializing MatchNotifierPlugin");
    m_state.store(PluginState::ACTIVE);
    m_logger.info("MatchNotifierPlugin initialized successfully");
}
// END_FUNCTION_INITIALIZE

// START_FUNCTION_SHUTDOWN
// START_CONTRACT:
// PURPOSE: Завершение работы плагина
// SIDE_EFFECTS: Переводит плагин в состояние STOPPED
// END_CONTRACT
void MatchNotifierPlugin::shutdown() {
    m_logger.info("MatchNotifierPlugin shutdown complete");
    m_state.store(PluginState::STOPPED);
}
// END_FUNCTION_SHUTDOWN

// START_FUNCTION_GET_INFO
// START_CONTRACT:
// PURPOSE: Получение информации о плагине
// OUTPUTS: PluginInfo — структура с информацией о плагине
// END_CONTRACT
PluginInfo MatchNotifierPlugin::get_info() const {
    return m_info;
}
// END_FUNCTION_GET_INFO

// START_FUNCTION_GET_STATE
// START_CONTRACT:
// PURPOSE: Получения состояния плагина
// OUTPUTS: PluginState — текущее состояние
// END_CONTRACT
PluginState MatchNotifierPlugin::get_state() const {
    return m_state.load();
}
// END_FUNCTION_GET_STATE

//==============================================================================
// Event Handlers
//==============================================================================

// START_FUNCTION_ON_METRICS_UPDATE
// START_CONTRACT:
// PURPOSE: Обработка обновления метрик от генератора
// INPUTS: const PluginMetrics& metrics — метрики
// OUTPUTS: void
// KEYWORDS: [DOMAIN(9): MetricsProcessing]
// END_CONTRACT
void MatchNotifierPlugin::on_metrics_update(const PluginMetrics& metrics) {
    // Извлечение метрик из словаря
    int64_t match_count = 0;
    int64_t iteration_count = 0;
    
    auto match_it = metrics.find("match_count");
    if (match_it != metrics.end()) {
        const auto& value = match_it->second;
        if (std::holds_alternative<int64_t>(value)) {
            match_count = std::get<int64_t>(value);
        }
    }
    
    auto iter_it = metrics.find("iteration_count");
    if (iter_it != metrics.end()) {
        const auto& value = iter_it->second;
        if (std::holds_alternative<int64_t>(value)) {
            iteration_count = std::get<int64_t>(value);
        }
    }
    
    m_logger.debug("Metrics update: match_count=" + std::to_string(match_count) + 
                   ", iteration_count=" + std::to_string(iteration_count));
    
    // Проверка новых совпадений
    if (match_count > m_total_matches.load()) {
        int64_t new_matches_count = match_count - m_total_matches.load();
        
        m_logger.info("Обнаружено " + std::to_string(new_matches_count) + " новых совпадений");
        
        // Генерируем записи о совпадениях
        for (int64_t i = 0; i < new_matches_count; ++i) {
            int64_t current_total = m_total_matches.fetch_add(1);
            MatchInfo info = generate_match_info(iteration_count, current_total + 1);
            add_match(info);
        }
    }
    
    m_is_monitoring = (iteration_count > 0);
}
// END_FUNCTION_ON_METRICS_UPDATE

// START_FUNCTION_ON_MATCH_FOUND
// START_CONTRACT:
// PURPOSE: Обработка обнаружения совпадений
// INPUTS: const MatchList& matches — список совпадений, int iteration — итерация
// OUTPUTS: void
// SIDE_EFFECTS: Добавление в историю; отправка уведомлений
// KEYWORDS: [DOMAIN(9): MatchHandling; CONCEPT(7): EventHandler]
// END_CONTRACT
void MatchNotifierPlugin::on_match_found(const MatchList& matches, int iteration) {
    m_logger.info("on_match_found called with " + std::to_string(matches.size()) + " matches");
    
    for (const auto& match_dict : matches) {
        MatchInfo info;
        info.iteration = iteration;
        info.match_number = m_total_matches.fetch_add(1) + 1;
        info.priority = determine_priority(iteration);
        info.timestamp = std::chrono::system_clock::now();
        
        // Извлечение данных из словаря
        auto addr_it = match_dict.find("address");
        if (addr_it != match_dict.end()) {
            const auto& addr_var = addr_it->second;
            if (std::holds_alternative<std::string>(addr_var)) {
                info.address = std::get<std::string>(addr_var);
            }
        }
        
        auto wallet_it = match_dict.find("wallet_name");
        if (wallet_it != match_dict.end()) {
            const auto& wallet_var = wallet_it->second;
            if (std::holds_alternative<std::string>(wallet_var)) {
                info.wallet_name = std::get<std::string>(wallet_var);
            }
        }
        
        auto pk_it = match_dict.find("private_key");
        if (pk_it != match_dict.end()) {
            const auto& pk_var = pk_it->second;
            if (std::holds_alternative<std::string>(pk_var)) {
                info.private_key = std::get<std::string>(pk_var);
            }
        }
        
        add_match(info);
    }
}
// END_FUNCTION_ON_MATCH_FOUND

// START_FUNCTION_ON_START
// START_CONTRACT:
// PURPOSE: Обработчик запуска генератора кошельков
// INPUTS: const std::string& selected_list_path — путь к списку адресов
// SIDE_EFFECTS: Сброс истории; установка флага мониторинга
// END_CONTRACT
void MatchNotifierPlugin::on_start(const std::string& selected_list_path) {
    m_logger.info("Starting match notifier with list: " + selected_list_path);
    
    std::lock_guard<std::mutex> lock(m_data_mutex);
    m_match_history.clear();
    m_total_matches = 0;
    m_is_monitoring = true;
    m_current_list_path = selected_list_path;
    m_entry_counter = 0;
    
    m_logger.info("Match notifier session started");
}
// END_FUNCTION_ON_START

// START_FUNCTION_ON_FINISH
// START_CONTRACT:
// PURPOSE: Обработчик завершения генерации кошельков
// INPUTS: const PluginMetrics& final_metrics — финальные метрики
// OUTPUTS: void
// KEYWORDS: [DOMAIN(9): Finalization]
// END_CONTRACT
void MatchNotifierPlugin::on_finish(const PluginMetrics& final_metrics) {
    m_logger.info("Generation finished - match notifier completing");
    
    std::lock_guard<std::mutex> lock(m_data_mutex);
    m_is_monitoring = false;
    
    int64_t final_match_count = 0;
    auto match_it = final_metrics.find("match_count");
    if (match_it != final_metrics.end()) {
        const auto& value = match_it->second;
        if (std::holds_alternative<int64_t>(value)) {
            final_match_count = std::get<int64_t>(value);
        }
    }
    
    m_logger.info("Final match count: " + std::to_string(final_match_count));
}
// END_FUNCTION_ON_FINISH

// START_FUNCTION_ON_RESET
// START_CONTRACT:
// PURPOSE: Обработчик сброса генератора
// OUTPUTS: void
// SIDE_EFFECTS: Сброс внутреннего состояния
// END_CONTRACT
void MatchNotifierPlugin::on_reset() {
    m_logger.info("Resetting match notifier plugin");
    reset_notifications();
}
// END_FUNCTION_ON_RESET

//==============================================================================
// Методы получения данных
//==============================================================================

// START_FUNCTION_GET_MATCH_HISTORY
// START_CONTRACT:
// PURPOSE: Получение полной истории совпадений
// OUTPUTS: std::vector<MatchHistoryEntry> — вектор всех записей
// END_CONTRACT
std::vector<MatchHistoryEntry> MatchNotifierPlugin::get_match_history() const {
    std::lock_guard<std::mutex> lock(m_data_mutex);
    return std::vector<MatchHistoryEntry>(m_match_history.begin(), m_match_history.end());
}
// END_FUNCTION_GET_MATCH_HISTORY

// START_FUNCTION_GET_LATEST_MATCH
// START_CONTRACT:
// PURPOSE: Получение последнего найденного совпадения
// OUTPUTS: std::optional<MatchHistoryEntry> — последнее совпадение или nullopt
// END_CONTRACT
std::optional<MatchHistoryEntry> MatchNotifierPlugin::get_latest_match() const {
    std::lock_guard<std::mutex> lock(m_data_mutex);
    if (!m_match_history.empty()) {
        return m_match_history.back();
    }
    return std::nullopt;
}
// END_FUNCTION_GET_LATEST_MATCH

// START_FUNCTION_GET_TOTAL_MATCHES
// START_CONTRACT:
// PURPOSE: Получение общего количества найденных совпадений
// OUTPUTS: int64_t — общее количество совпадений
// END_CONTRACT
int64_t MatchNotifierPlugin::get_total_matches() const {
    return m_total_matches.load();
}
// END_FUNCTION_GET_TOTAL_MATCHES

// START_FUNCTION_IS_MONITORING
// START_CONTRACT:
// PURPOSE: Проверка активности мониторинга
// OUTPUTS: bool — true если мониторинг активен
// END_CONTRACT
bool MatchNotifierPlugin::is_monitoring() const {
    return m_is_monitoring.load();
}
// END_FUNCTION_IS_MONITORING

//==============================================================================
// Методы экспорта
//==============================================================================

// START_FUNCTION_EXPORT_MATCHES
// START_CONTRACT:
// PURPOSE: Экспорт истории совпадений в JSON файл
// INPUTS: const std::string& file_path — путь к файлу
// OUTPUTS: bool — успешность экспорта
// KEYWORDS: [DOMAIN(7): Export; TECH(5): JSON]
// END_CONTRACT
bool MatchNotifierPlugin::export_matches(const std::string& file_path) const {
    std::lock_guard<std::mutex> lock(m_data_mutex);
    
    try {
        std::ofstream file(file_path, std::ios::out | std::ios::binary);
        if (!file.is_open()) {
            m_logger.error("Failed to open file for export: " + file_path);
            return false;
        }
        
        // Генерация JSON
        file << "[\n";
        for (size_t i = 0; i < m_match_history.size(); ++i) {
            const auto& entry = m_match_history[i];
            file << "  {\n";
            file << "    \"entry_id\": " << entry.entry_id << ",\n";
            file << "    \"timestamp\": \"" << entry.match.get_timestamp_string() << "\",\n";
            file << "    \"iteration\": " << entry.match.iteration << ",\n";
            file << "    \"match_number\": " << entry.match.match_number << ",\n";
            file << "    \"address\": \"" << entry.match.address << "\",\n";
            file << "    \"wallet_name\": \"" << entry.match.wallet_name << "\",\n";
            file << "    \"list_name\": \"" << entry.match.list_name << "\",\n";
            file << "    \"priority\": " << static_cast<int>(entry.match.priority) << ",\n";
            file << "    \"notification_sent\": " << (entry.notification_sent ? "true" : "false") << "\n";
            file << "  }";
            if (i < m_match_history.size() - 1) file << ",";
            file << "\n";
        }
        file << "]\n";
        
        file.close();
        m_logger.info("Exported matches to JSON: " + file_path);
        return true;
        
    } catch (const std::exception& e) {
        m_logger.error(std::string("Export exception: ") + e.what());
        return false;
    }
}
// END_FUNCTION_EXPORT_MATCHES

//==============================================================================
// Управление уведомлениями
//==============================================================================

// START_FUNCTION_RESET_NOTIFICATIONS
// START_CONTRACT:
// PURPOSE: Сброс истории совпадений и счётчиков
// OUTPUTS: void
// SIDE_EFFECTS: Очищает историю; сбрасывает счётчики
// END_CONTRACT
void MatchNotifierPlugin::reset_notifications() {
    std::lock_guard<std::mutex> lock(m_data_mutex);
    m_match_history.clear();
    m_total_matches = 0;
    m_is_monitoring = false;
    m_entry_counter = 0;
    m_last_notification_time = std::chrono::system_clock::time_point::min();
    m_logger.info("Notifications reset complete");
}
// END_FUNCTION_RESET_NOTIFICATIONS

// START_FUNCTION_GET_NOTIFICATION_CONFIG
// START_CONTRACT:
// PURPOSE: Получение текущей конфигурации уведомлений
// OUTPUTS: const MatchNotifierConfig& — конфигурация
// END_CONTRACT
const MatchNotifierConfig& MatchNotifierPlugin::get_notification_config() const {
    return m_config;
}
// END_FUNCTION_GET_NOTIFICATION_CONFIG

// START_FUNCTION_SET_NOTIFICATION_CONFIG
// START_CONTRACT:
// PURPOSE: Установка новой конфигурации уведомлений
// INPUTS: const MatchNotifierConfig& config — новая конфигурация
// OUTPUTS: void
// END_CONTRACT
void MatchNotifierPlugin::set_notification_config(const MatchNotifierConfig& config) {
    m_config = config;
    m_logger.info("Notification config updated: " + m_config.to_string());
}
// END_FUNCTION_SET_NOTIFICATION_CONFIG

// START_FUNCTION_GET_NOTIFICATION_SUMMARY
// START_CONTRACT:
// PURPOSE: Получение текстовой сводки о состоянии уведомлений
// OUTPUTS: std::string — форматированная сводка
// END_CONTRACT
std::string MatchNotifierPlugin::get_notification_summary() const {
    std::lock_guard<std::mutex> lock(m_data_mutex);
    
    std::ostringstream oss;
    oss << "=================================================\n";
    oss << "СВОДКА УВЕДОМЛЕНИЙ О СОВПАДЕНИЯХ\n";
    oss << "=================================================\n";
    oss << "Всего совпадений: " << m_total_matches.load() << "\n";
    oss << "История: " << m_match_history.size() << " записей\n";
    oss << "Мониторинг: " << (m_is_monitoring.load() ? "активен" : "неактивен") << "\n";
    oss << "Desktop уведомления: " << (m_config.desktop_enabled ? "включены" : "выключены") << "\n";
    oss << "Логирование: " << (m_config.log_enabled ? "включено" : "выключено") << "\n";
    oss << "Кулдаун: " << m_config.cooldown_seconds << " сек\n";
    oss << "=================================================\n";
    
    return oss.str();
}
// END_FUNCTION_GET_NOTIFICATION_SUMMARY

// START_FUNCTION_REGISTER_MATCH_CALLBACK
// START_CONTRACT:
// PURPOSE: Регистрация callback функции для уведомления о совпадениях
// INPUTS: MatchCallback callback — функция обратного вызова
// OUTPUTS: void
// KEYWORDS: [DOMAIN(7): Callback; CONCEPT(6): Registration]
// END_CONTRACT
void MatchNotifierPlugin::register_match_callback(MatchCallback callback) {
    std::lock_guard<std::mutex> lock(m_data_mutex);
    m_match_callbacks.push_back(callback);
    m_logger.debug("Match callback registered");
}
// END_FUNCTION_REGISTER_MATCH_CALLBACK

//==============================================================================
// Отправка уведомлений
//==============================================================================

// START_FUNCTION_SEND_NOTIFICATION
// START_CONTRACT:
// PURPOSE: Отправка уведомления о совпадении
// INPUTS: const MatchInfo& match_info — информация о совпадении
// OUTPUTS: bool — успешность отправки
// KEYWORDS: [DOMAIN(9): Notification]
// END_CONTRACT
bool MatchNotifierPlugin::send_notification(const MatchInfo& match_info) {
    if (!should_process_notification()) {
        m_logger.debug("Notification skipped (cooldown)");
        return false;
    }
    
    bool success = false;
    
    // Desktop уведомление
    if (m_config.desktop_enabled) {
        // Попытка отправить через notify-send
        std::string title = "Найдено совпадение!";
        std::string message = "Совпадение #" + std::to_string(match_info.match_number) 
                           + " на итерации " + std::to_string(match_info.iteration);
        
        std::string cmd = "notify-send \"" + title + "\" \"" + message + "\" > /dev/null 2>&1";
        int result = system(cmd.c_str());
        
        if (result == 0) {
            m_logger.info("Desktop notification sent");
            success = true;
        }
    }
    
    // Логирование
    if (m_config.log_enabled) {
        log_match(match_info);
    }
    
    // Обновление времени последнего уведомления
    m_last_notification_time = std::chrono::system_clock::now();
    
    return success;
}
// END_FUNCTION_SEND_NOTIFICATION

// START_FUNCTION_LOG_MATCH
// START_CONTRACT:
// PURPOSE: Логирование совпадения
// INPUTS: const MatchInfo& match_info — информация о совпадении
// OUTPUTS: void
// KEYWORDS: [DOMAIN(7): Logging]
// END_CONTRACT
void MatchNotifierPlugin::log_match(const MatchInfo& match_info) {
    std::string priority_str;
    switch (match_info.priority) {
        case NotificationPriority::LOW: priority_str = "LOW"; break;
        case NotificationPriority::NORMAL: priority_str = "NORMAL"; break;
        case NotificationPriority::HIGH: priority_str = "HIGH"; break;
        case NotificationPriority::CRITICAL: priority_str = "CRITICAL"; break;
    }
    
    m_logger.warning("СОВПАДЕНИЕ! #" + std::to_string(match_info.match_number) + 
                     " на итерации " + std::to_string(match_info.iteration) +
                     ", адрес: " + match_info.address +
                     ", приоритет: " + priority_str);
}
// END_FUNCTION_LOG_MATCH

//==============================================================================
// Приватные методы
//==============================================================================

// START_FUNCTION_ADD_MATCH
// START_CONTRACT:
// PURPOSE: Добавление совпадения в историю
// INPUTS: const MatchInfo& match_info — информация о совпадении
// OUTPUTS: void
// SIDE_EFFECTS: Добавляет в ring buffer; вызывает send_notifications; вызывает callbacks
// KEYWORDS: [DOMAIN(8): MatchHandling]
// END_CONTRACT
void MatchNotifierPlugin::add_match(const MatchInfo& match_info) {
    std::lock_guard<std::mutex> lock(m_data_mutex);
    
    // Ring buffer behavior
    if (m_match_history.size() >= MAX_MATCH_HISTORY) {
        m_match_history.pop_front();
    }
    
    m_entry_counter++;
    MatchHistoryEntry entry(m_entry_counter, match_info);
    m_match_history.push_back(entry);
    
    // Отправка уведомлений
    send_notifications(match_info);
    
    // Вызов callbacks
    for (const auto& callback : m_match_callbacks) {
        try {
            callback(match_info);
        } catch (const std::exception& e) {
            m_logger.error(std::string("Callback exception: ") + e.what());
        }
    }
    
    m_logger.debug("Match added to history: " + match_info.to_string());
}
// END_FUNCTION_ADD_MATCH

// START_FUNCTION_SEND_NOTIFICATIONS
// START_CONTRACT:
// PURPOSE: Отправка уведомлений через все каналы
// INPUTS: const MatchInfo& match_info — информация о совпадении
// OUTPUTS: void
// KEYWORDS: [DOMAIN(9): Notification]
// END_CONTRACT
void MatchNotifierPlugin::send_notifications(const MatchInfo& match_info) {
    // Проверка приоритета
    if (match_info.priority < m_config.min_priority) {
        m_logger.debug("Notification skipped due to low priority");
        return;
    }
    
    // Отправка уведомления
    bool sent = send_notification(match_info);
    
    // Обновление статуса отправки в истории
    if (!m_match_history.empty()) {
        m_match_history.back().notification_sent = sent;
    }
}
// END_FUNCTION_SEND_NOTIFICATIONS

// START_FUNCTION_SHOULD_PROCESS_NOTIFICATION
// START_CONTRACT:
// PURPOSE: Проверка возможности отправки уведомления (кулдаун)
// OUTPUTS: bool — true если можно отправлять уведомление
// KEYWORDS: [CONCEPT(7): Cooldown]
// END_CONTRACT
bool MatchNotifierPlugin::should_process_notification() const {
    auto now = std::chrono::system_clock::now();
    auto elapsed = std::chrono::duration<double>(now - m_last_notification_time).count();
    return elapsed >= m_config.cooldown_seconds;
}
// END_FUNCTION_SHOULD_PROCESS_NOTIFICATION

// START_FUNCTION_DETERMINE_PRIORITY
// START_CONTRACT:
// PURPOSE: Определение приоритета на основе итерации
// INPUTS: int64_t iteration — номер итерации
// OUTPUTS: NotificationPriority — определённый приоритет
// KEYWORDS: [DOMAIN(8): Priority; CONCEPT(7): Classification]
// END_CONTRACT
NotificationPriority MatchNotifierPlugin::determine_priority(int64_t iteration) const {
    return ::determine_priority_level(iteration);
}
// END_FUNCTION_DETERMINE_PRIORITY

// START_FUNCTION_GENERATE_MATCH_INFO
// START_CONTRACT:
// PURPOSE: Генерация тестовой записи совпадения
// INPUTS: int64_t iteration — номер итерации, int64_t match_number — номер совпадения
// OUTPUTS: MatchInfo — сгенерированная запись
// KEYWORDS: [CONCEPT(7): MockData]
// END_CONTRACT
MatchInfo MatchNotifierPlugin::generate_match_info(int64_t iteration, int64_t match_number) const {
    MatchInfo info;
    info.iteration = iteration;
    info.match_number = match_number;
    info.priority = determine_priority(iteration);
    info.timestamp = std::chrono::system_clock::now();
    
    // Генерация случайного адреса для демонстрации
    const char chars[] = "0123456789abcdefABCDEFGHIJKLMNOPQRSTUVWXYZ";
    std::string addr = "1";
    for (int i = 0; i < 30; ++i) {
        addr += chars[rand() % (sizeof(chars) - 1)];
    }
    info.address = addr;
    info.wallet_name = "Generated";
    info.list_name = m_current_list_path.empty() ? "Unknown" : m_current_list_path;
    
    return info;
}
// END_FUNCTION_GENERATE_MATCH_INFO
