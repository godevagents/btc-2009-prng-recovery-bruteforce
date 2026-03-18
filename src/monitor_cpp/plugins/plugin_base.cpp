// FILE: src/monitor_cpp/plugins/plugin_base.cpp
// VERSION: 1.0.0
// START_MODULE_CONTRACT:
// PURPOSE: Реализация базовых классов плагинов мониторинга
// SCOPE: PluginInfo, PluginLogger, BasePlugin, PluginManager
// KEYWORDS: [DOMAIN(9): PluginSystem; TECH(6): C++17]
// END_MODULE_CONTRACT

#include "plugin_base.hpp"

#include <sstream>

//==============================================================================
// PluginInfo Implementation
//==============================================================================

// START_FUNCTION_PluginInfo_to_string
// START_CONTRACT:
// PURPOSE: Преобразование информации о плагине в строку
// OUTPUTS: std::string - строковое представление
// KEYWORDS: [TECH(5): String; CONCEPT(4): Debug]
// END_CONTRACT
std::string PluginInfo::to_string() const {
    std::ostringstream oss;
    oss << "PluginInfo(name=" << name 
        << ", version=" << version 
        << ", description=" << description 
        << ", author=" << author 
        << ", capabilities={realtime=" << (capabilities.supports_realtime ? "true" : "false")
        << ", notifications=" << (capabilities.supports_notifications ? "true" : "false")
        << ", export=" << (capabilities.supports_export ? "true" : "false")
        << "})";
    return oss.str();
}
// END_FUNCTION_PluginInfo_to_string

//==============================================================================
// PluginLogger Implementation
//==============================================================================

// START_FUNCTION_PluginLogger_constructor
// START_CONTRACT:
// PURPOSE: Конструктор логгера плагина
// INPUTS: plugin_name - имя плагина
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
PluginLogger::PluginLogger(const std::string& plugin_name)
    : m_plugin_name(plugin_name) {}
// END_FUNCTION_PluginLogger_constructor

// START_FUNCTION_PluginLogger_current_timestamp
// START_CONTRACT:
// PURPOSE: Получение текущей временной метки
// OUTPUTS: std::string - временная метка в формате ISO
// KEYWORDS: [TECH(5): Time; CONCEPT(4): Timestamp]
// END_CONTRACT
std::string PluginLogger::current_timestamp() {
    auto now = std::time(nullptr);
    auto tm = *std::localtime(&now);
    char buffer[32];
    std::strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", &tm);
    return std::string(buffer);
}
// END_FUNCTION_PluginLogger_current_timestamp

// START_FUNCTION_PluginLogger_level_to_string
// START_CONTRACT:
// PURPOSE: Преобразование уровня логирования в строку
// INPUTS: level - уровень логирования
// OUTPUTS: std::string - строковое представление
// KEYWORDS: [CONCEPT(4): Conversion]
// END_CONTRACT
std::string PluginLogger::level_to_string(Level level) {
    switch (level) {
        case Level::DEBUG: return "DEBUG";
        case Level::INFO: return "INFO";
        case Level::WARNING: return "WARNING";
        case Level::ERROR: return "ERROR";
        case Level::CRITICAL: return "CRITICAL";
        default: return "UNKNOWN";
    }
}
// END_FUNCTION_PluginLogger_level_to_string

// START_FUNCTION_PluginLogger_get_log_file
// START_CONTRACT:
// PURPOSE: Получение ссылки на файл логов
// OUTPUTS: std::ofstream& - ссылка на файл логов
// KEYWORDS: [TECH(5): FileIO; CONCEPT(4): Logging]
// END_CONTRACT
std::ofstream& PluginLogger::get_log_file() {
    static std::ofstream log_file("app.log", std::ios::app);
    return log_file;
}
// END_FUNCTION_PluginLogger_get_log_file

// START_FUNCTION_PluginLogger_log
// START_CONTRACT:
// PURPOSE: Универсальный метод логирования
// INPUTS: level - уровень, message - сообщение
// OUTPUTS: none
// SIDE_EFFECTS: Запись в файл логов
// KEYWORDS: [TECH(5): Logging; CONCEPT(4): IO]
// END_CONTRACT
void PluginLogger::log(Level level, const std::string& message) const {
    auto& file = get_log_file();
    file << "[" << current_timestamp() << "][" 
         << m_plugin_name << "][" 
         << level_to_string(level) << "] " 
         << message << std::endl;
    file.flush();
}
// END_FUNCTION_PluginLogger_log

// START_FUNCTION_PluginLogger_debug
// START_CONTRACT:
// PURPOSE: Логирование отладочного сообщения
// INPUTS: message - сообщение
// OUTPUTS: none
// KEYWORDS: [TECH(5): Debug; CONCEPT(4): Logging]
// END_CONTRACT
void PluginLogger::debug(const std::string& message) const {
    log(Level::DEBUG, message);
}
// END_FUNCTION_PluginLogger_debug

// START_FUNCTION_PluginLogger_info
// START_CONTRACT:
// PURPOSE: Логирование информационного сообщения
// INPUTS: message - сообщение
// OUTPUTS: none
// KEYWORDS: [TECH(5): Info; CONCEPT(4): Logging]
// END_CONTRACT
void PluginLogger::info(const std::string& message) const {
    log(Level::INFO, message);
}
// END_FUNCTION_PluginLogger_info

// START_FUNCTION_PluginLogger_warning
// START_CONTRACT:
// PURPOSE: Логирование предупреждения
// INPUTS: message - сообщение
// OUTPUTS: none
// KEYWORDS: [TECH(5): Warning; CONCEPT(4): Logging]
// END_CONTRACT
void PluginLogger::warning(const std::string& message) const {
    log(Level::WARNING, message);
}
// END_FUNCTION_PluginLogger_warning

// START_FUNCTION_PluginLogger_error
// START_CONTRACT:
// PURPOSE: Логирование ошибки
// INPUTS: message - сообщение
// OUTPUTS: none
// KEYWORDS: [TECH(5): Error; CONCEPT(4): Logging]
// END_CONTRACT
void PluginLogger::error(const std::string& message) const {
    log(Level::ERROR, message);
}
// END_FUNCTION_PluginLogger_error

// START_FUNCTION_PluginLogger_critical
// START_CONTRACT:
// PURPOSE: Логирование критической ошибки
// INPUTS: message - сообщение
// OUTPUTS: none
// KEYWORDS: [TECH(5): Critical; CONCEPT(4): Logging]
// END_CONTRACT
void PluginLogger::critical(const std::string& message) const {
    log(Level::CRITICAL, message);
}
// END_FUNCTION_PluginLogger_critical

//==============================================================================
// IPlugin Default Implementation
//==============================================================================

// START_FUNCTION_IPlugin_on_update
// START_CONTRACT:
// PURPOSE: Обработка обновления (по умолчанию пустая реализация)
// INPUTS: context - контекст обновления
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Callback; DOMAIN(4): Events]
// END_CONTRACT
void IPlugin::on_update(const UpdateContext& context) {
    // По умолчанию ничего не делает
}
// END_FUNCTION_IPlugin_on_update

// START_FUNCTION_IPlugin_on_metrics_update
// START_CONTRACT:
// PURPOSE: Обработка обновления метрик (по умолчанию пустая реализация)
// INPUTS: metrics - метрики
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Callback; DOMAIN(4): Metrics]
// END_CONTRACT
void IPlugin::on_metrics_update(const PluginMetrics& metrics) {
    // По умолчанию ничего не делает
}
// END_FUNCTION_IPlugin_on_metrics_update

// START_FUNCTION_IPlugin_on_match_found
// START_CONTRACT:
// PURPOSE: Обработка найденных совпадений (по умолчанию логирование)
// INPUTS: matches - список совпадений, iteration - номер итерации
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Callback; DOMAIN(4): Match]
// END_CONTRACT
void IPlugin::on_match_found(const MatchList& matches, int iteration) {
    PluginLogger logger("IPlugin");
    logger.info("Found " + std::to_string(matches.size()) + 
                " matches at iteration " + std::to_string(iteration));
}
// END_FUNCTION_IPlugin_on_match_found

// START_FUNCTION_IPlugin_on_start
// START_CONTRACT:
// PURPOSE: Обработчик запуска генератора (по умолчанию пустая реализация)
// INPUTS: selected_list_path - путь к списку
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Callback; DOMAIN(4): Lifecycle]
// END_CONTRACT
void IPlugin::on_start(const std::string& selected_list_path) {
    // По умолчанию ничего не делает
}
// END_FUNCTION_IPlugin_on_start

// START_FUNCTION_IPlugin_on_finish
// START_CONTRACT:
// PURPOSE: Обработчик завершения генерации (по умолчанию пустая реализация)
// INPUTS: final_metrics - финальные метрики
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Callback; DOMAIN(4): Lifecycle]
// END_CONTRACT
void IPlugin::on_finish(const PluginMetrics& final_metrics) {
    // По умолчанию ничего не делает
}
// END_FUNCTION_IPlugin_on_finish

// START_FUNCTION_IPlugin_on_reset
// START_CONTRACT:
// PURPOSE: Обработчик сброса (по умолчанию пустая реализация)
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Callback; DOMAIN(4): Lifecycle]
// END_CONTRACT
void IPlugin::on_reset() {
    // По умолчанию ничего не делает
}
// END_FUNCTION_IPlugin_on_reset

// START_FUNCTION_IPlugin_start
// START_CONTRACT:
// PURPOSE: Запуск плагина
// OUTPUTS: none
// SIDE_EFFECTS: Изменение состояния
// KEYWORDS: [CONCEPT(5): Lifecycle; DOMAIN(4): Control]
// END_CONTRACT
void IPlugin::start() {
    std::unique_lock lock(m_mutex);
    if (m_state.load() == PluginState::INITIALIZING || 
        m_state.load() == PluginState::PAUSED ||
        m_state.load() == PluginState::STOPPED) {
        m_state.store(PluginState::ACTIVE);
    }
}
// END_FUNCTION_IPlugin_start

// START_FUNCTION_IPlugin_stop
// START_CONTRACT:
// PURPOSE: Остановка плагина
// OUTPUTS: none
// SIDE_EFFECTS: Изменение состояния
// KEYWORDS: [CONCEPT(5): Lifecycle; DOMAIN(4): Control]
// END_CONTRACT
void IPlugin::stop() {
    std::unique_lock lock(m_mutex);
    m_state.store(PluginState::STOPPED);
}
// END_FUNCTION_IPlugin_stop

// START_FUNCTION_IPlugin_pause
// START_CONTRACT:
// PURPOSE: Приостановка плагина
// OUTPUTS: none
// SIDE_EFFECTS: Изменение состояния
// KEYWORDS: [CONCEPT(5): Lifecycle; DOMAIN(4): Control]
// END_CONTRACT
void IPlugin::pause() {
    std::unique_lock lock(m_mutex);
    if (m_state.load() == PluginState::ACTIVE) {
        m_state.store(PluginState::PAUSED);
    }
}
// END_FUNCTION_IPlugin_pause

// START_FUNCTION_IPlugin_resume
// START_CONTRACT:
// PURPOSE: Возобновление работы плагина
// OUTPUTS: none
// SIDE_EFFECTS: Изменение состояния
// KEYWORDS: [CONCEPT(5): Lifecycle; DOMAIN(4): Control]
// END_CONTRACT
void IPlugin::resume() {
    std::unique_lock lock(m_mutex);
    if (m_state.load() == PluginState::PAUSED) {
        m_state.store(PluginState::ACTIVE);
    }
}
// END_FUNCTION_IPlugin_resume

// START_FUNCTION_IPlugin_health_check
// START_CONTRACT:
// PURPOSE: Проверка работоспособности плагина
// OUTPUTS: bool - статус работоспособности
// KEYWORDS: [CONCEPT(5): Health; DOMAIN(4): Check]
// END_CONTRACT
bool IPlugin::health_check() const {
    PluginState state = m_state.load();
    return state == PluginState::ACTIVE || 
           state == PluginState::INITIALIZING ||
           state == PluginState::PAUSED;
}
// END_FUNCTION_IPlugin_health_check

// START_FUNCTION_IPlugin_get_config
// START_CONTRACT:
// PURPOSE: Получение конфигурации плагина
// OUTPUTS: PluginConfig - копия конфигурации
// KEYWORDS: [CONCEPT(5): Config; DOMAIN(4): Accessor]
// END_CONTRACT
PluginConfig IPlugin::get_config() const {
    std::shared_lock lock(m_mutex);
    return m_config;
}
// END_FUNCTION_IPlugin_get_config

// START_FUNCTION_IPlugin_set_config
// START_CONTRACT:
// PURPOSE: Установка конфигурации плагина
// INPUTS: config - новая конфигурация
// OUTPUTS: none
// SIDE_EFFECTS: Изменение конфигурации
// KEYWORDS: [CONCEPT(5): Config; DOMAIN(4): Mutator]
// END_CONTRACT
void IPlugin::set_config(const PluginConfig& config) {
    std::unique_lock lock(m_mutex);
    m_config = config;
}
// END_FUNCTION_IPlugin_set_config

//==============================================================================
// BasePlugin Implementation
//==============================================================================

// START_FUNCTION_BasePlugin_constructor
// START_CONTRACT:
// PURPOSE: Конструктор базового плагина
// INPUTS: info - информация о плагине, config - конфигурация
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Initialization]
// END_CONTRACT
BasePlugin::BasePlugin(const PluginInfo& info, const PluginConfig& config)
    : m_info(info)
    , m_logger(info.name)
    , m_initialized(false) {
    m_config = config;
    m_state.store(PluginState::UNINITIALIZED);
}
// END_FUNCTION_BasePlugin_constructor

// START_FUNCTION_BasePlugin_destructor
// START_CONTRACT:
// PURPOSE: Деструктор базового плагина
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Destructor]
// END_CONTRACT
BasePlugin::~BasePlugin() {
    if (m_state.load() != PluginState::STOPPED && 
        m_state.load() != PluginState::UNINITIALIZED) {
        shutdown();
    }
}
// END_FUNCTION_BasePlugin_destructor

// START_FUNCTION_BasePlugin_initialize
// START_CONTRACT:
// PURPOSE: Инициализация плагина
// OUTPUTS: none
// SIDE_EFFECTS: Изменение состояния; вызов initialize_impl
// KEYWORDS: [CONCEPT(5): Lifecycle; DOMAIN(4): Init]
// END_CONTRACT
void BasePlugin::initialize() {
    std::unique_lock lock(m_mutex);
    
    if (m_initialized) {
        m_logger.warning("Plugin already initialized");
        return;
    }
    
    m_state.store(PluginState::INITIALIZING);
    m_logger.info("Initializing plugin: " + m_info.to_string());
    
    try {
        // Вызов специфичной инициализации
        initialize_impl();
        
        m_initialized = true;
        m_state.store(PluginState::ACTIVE);
        m_logger.info("Plugin initialized successfully");
        
    } catch (const std::exception& e) {
        m_state.store(PluginState::ERROR);
        m_logger.error("Failed to initialize plugin: " + std::string(e.what()));
        throw;
    }
}
// END_FUNCTION_BasePlugin_initialize

// START_FUNCTION_BasePlugin_shutdown
// START_CONTRACT:
// PURPOSE: Завершение работы плагина
// OUTPUTS: none
// SIDE_EFFECTS: Изменение состояния; вызов shutdown_impl
// KEYWORDS: [CONCEPT(5): Lifecycle; DOMAIN(4): Shutdown]
// END_CONTRACT
void BasePlugin::shutdown() {
    std::unique_lock lock(m_mutex);
    
    if (!m_initialized) {
        m_logger.warning("Plugin not initialized, nothing to shutdown");
        return;
    }
    
    m_logger.info("Shutting down plugin");
    
    try {
        // Вызов специфичного завершения
        shutdown_impl();
        
        m_initialized = false;
        m_state.store(PluginState::STOPPED);
        m_logger.info("Plugin shutdown complete");
        
    } catch (const std::exception& e) {
        m_state.store(PluginState::ERROR);
        m_logger.error("Error during shutdown: " + std::string(e.what()));
    }
}
// END_FUNCTION_BasePlugin_shutdown

// START_FUNCTION_BasePlugin_get_info
// START_CONTRACT:
// PURPOSE: Получение информации о плагине
// OUTPUTS: PluginInfo - информация о плагине
// KEYWORDS: [CONCEPT(5): Accessor; DOMAIN(4): Info]
// END_CONTRACT
PluginInfo BasePlugin::get_info() const {
    std::shared_lock lock(m_mutex);
    return m_info;
}
// END_FUNCTION_BasePlugin_get_info

// START_FUNCTION_BasePlugin_get_state
// START_CONTRACT:
// PURPOSE: Получение состояния плагина
// OUTPUTS: PluginState - текущее состояние
// KEYWORDS: [CONCEPT(5): Accessor; DOMAIN(4): State]
// END_CONTRACT
PluginState BasePlugin::get_state() const {
    return m_state.load();
}
// END_FUNCTION_BasePlugin_get_state

// START_FUNCTION_BasePlugin_set_state
// START_CONTRACT:
// PURPOSE: Установка состояния плагина
// INPUTS: state - новое состояние
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Mutator; DOMAIN(4): State]
// END_CONTRACT
void BasePlugin::set_state(PluginState state) {
    m_state.store(state);
}
// END_FUNCTION_BasePlugin_set_state

// START_FUNCTION_BasePlugin_on_update
// START_CONTRACT:
// PURPOSE: Обработка обновления
// INPUTS: context - контекст обновления
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Callback; DOMAIN(4): Events]
// END_CONTRACT
void BasePlugin::on_update(const UpdateContext& context) {
    if (m_state.load() != PluginState::ACTIVE) {
        return;
    }
    
    try {
        on_update_impl(context);
    } catch (const std::exception& e) {
        m_logger.error("Error in on_update: " + std::string(e.what()));
    }
}
// END_FUNCTION_BasePlugin_on_update

// START_FUNCTION_BasePlugin_on_metrics_update
// START_CONTRACT:
// PURPOSE: Обработка обновления метрик
// INPUTS: metrics - метрики
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Callback; DOMAIN(4): Metrics]
// END_CONTRACT
void BasePlugin::on_metrics_update(const PluginMetrics& metrics) {
    // По умолчанию создаём контекст и вызываем on_update
    UpdateContext context(0, metrics);
    on_update(context);
}
// END_FUNCTION_BasePlugin_on_metrics_update

// START_FUNCTION_BasePlugin_on_match_found
// START_CONTRACT:
// PURPOSE: Обработка найденных совпадений
// INPUTS: matches - список совпадений, iteration - номер итерации
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Callback; DOMAIN(4): Match]
// END_CONTRACT
void BasePlugin::on_match_found(const MatchList& matches, int iteration) {
    m_logger.info("Found " + std::to_string(matches.size()) + 
                  " matches at iteration " + std::to_string(iteration));
}
// END_FUNCTION_BasePlugin_on_match_found

// START_FUNCTION_BasePlugin_on_start
// START_CONTRACT:
// PURPOSE: Обработка запуска генератора
// INPUTS: selected_list_path - путь к списку
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Callback; DOMAIN(4): Lifecycle]
// END_CONTRACT
void BasePlugin::on_start(const std::string& selected_list_path) {
    m_logger.info("Generator started with list: " + selected_list_path);
}
// END_FUNCTION_BasePlugin_on_start

// START_FUNCTION_BasePlugin_on_finish
// START_CONTRACT:
// PURPOSE: Обработка завершения генерации
// INPUTS: final_metrics - финальные метрики
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Callback; DOMAIN(4): Lifecycle]
// END_CONTRACT
void BasePlugin::on_finish(const PluginMetrics& final_metrics) {
    m_logger.info("Generator finished");
}
// END_FUNCTION_BasePlugin_on_finish

// START_FUNCTION_BasePlugin_on_reset
// START_CONTRACT:
// PURPOSE: Обработка сброса
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Callback; DOMAIN(4): Lifecycle]
// END_CONTRACT
void BasePlugin::on_reset() {
    m_logger.info("Plugin reset");
}
// END_FUNCTION_BasePlugin_on_reset

// START_FUNCTION_BasePlugin_start
// START_CONTRACT:
// PURPOSE: Запуск плагина
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Lifecycle; DOMAIN(4): Control]
// END_CONTRACT
void BasePlugin::start() {
    std::unique_lock lock(m_mutex);
    if (m_initialized) {
        m_state.store(PluginState::ACTIVE);
        m_logger.info("Plugin started");
    }
}
// END_FUNCTION_BasePlugin_start

// START_FUNCTION_BasePlugin_stop
// START_CONTRACT:
// PURPOSE: Остановка плагина
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Lifecycle; DOMAIN(4): Control]
// END_CONTRACT
void BasePlugin::stop() {
    std::unique_lock lock(m_mutex);
    m_state.store(PluginState::STOPPED);
    m_logger.info("Plugin stopped");
}
// END_FUNCTION_BasePlugin_stop

// START_FUNCTION_BasePlugin_pause
// START_CONTRACT:
// PURPOSE: Приостановка плагина
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Lifecycle; DOMAIN(4): Control]
// END_CONTRACT
void BasePlugin::pause() {
    std::unique_lock lock(m_mutex);
    if (m_state.load() == PluginState::ACTIVE) {
        m_state.store(PluginState::PAUSED);
        m_logger.info("Plugin paused");
    }
}
// END_FUNCTION_BasePlugin_pause

// START_FUNCTION_BasePlugin_resume
// START_CONTRACT:
// PURPOSE: Возобновление работы плагина
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Lifecycle; DOMAIN(4): Control]
// END_CONTRACT
void BasePlugin::resume() {
    std::unique_lock lock(m_mutex);
    if (m_state.load() == PluginState::PAUSED) {
        m_state.store(PluginState::ACTIVE);
        m_logger.info("Plugin resumed");
    }
}
// END_FUNCTION_BasePlugin_resume

// START_FUNCTION_BasePlugin_health_check
// START_CONTRACT:
// PURPOSE: Проверка работоспособности
// OUTPUTS: bool - статус
// KEYWORDS: [CONCEPT(5): Health; DOMAIN(4): Check]
// END_CONTRACT
bool BasePlugin::health_check() const {
    return m_initialized && 
           (m_state.load() == PluginState::ACTIVE || 
            m_state.load() == PluginState::PAUSED);
}
// END_FUNCTION_BasePlugin_health_check

// START_FUNCTION_BasePlugin_get_config
// START_CONTRACT:
// PURPOSE: Получение конфигурации
// OUTPUTS: PluginConfig - копия конфигурации
// KEYWORDS: [CONCEPT(5): Accessor; DOMAIN(4): Config]
// END_CONTRACT
PluginConfig BasePlugin::get_config() const {
    std::shared_lock lock(m_mutex);
    return m_config;
}
// END_FUNCTION_BasePlugin_get_config

// START_FUNCTION_BasePlugin_set_config
// START_CONTRACT:
// PURPOSE: Установка конфигурации
// INPUTS: config - новая конфигурация
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Mutator; DOMAIN(4): Config]
// END_CONTRACT
void BasePlugin::set_config(const PluginConfig& config) {
    std::unique_lock lock(m_mutex);
    m_config = config;
}
// END_FUNCTION_BasePlugin_set_config

//==============================================================================
// PluginManager Implementation
//==============================================================================

// START_FUNCTION_PluginManager_instance
// START_CONTRACT:
// PURPOSE: Получение единственного экземпляра менеджера
// OUTPUTS: PluginManager& - ссылка на экземпляр
// KEYWORDS: [PATTERN(8): Singleton; CONCEPT(5): Global]
// END_CONTRACT
PluginManager& PluginManager::instance() {
    static PluginManager manager;
    return manager;
}
// END_FUNCTION_PluginManager_instance

// START_FUNCTION_PluginManager_register_plugin
// START_CONTRACT:
// PURPOSE: Регистрация плагина
// INPUTS: plugin - указатель на плагин
// OUTPUTS: bool - результат регистрации
// KEYWORDS: [CONCEPT(5): Registration; DOMAIN(4): Plugin]
// END_CONTRACT
bool PluginManager::register_plugin(PluginPtr plugin) {
    if (!plugin) {
        return false;
    }
    
    std::unique_lock lock(m_mutex);
    const std::string& name = plugin->get_info().name;
    m_plugins[name] = plugin;
    return true;
}
// END_FUNCTION_PluginManager_register_plugin

// START_FUNCTION_PluginManager_register_factory
// START_CONTRACT:
// PURPOSE: Регистрация фабрики плагинов
// INPUTS: plugin_name - имя плагина, factory - функция фабрики
// OUTPUTS: bool - результат регистрации
// KEYWORDS: [CONCEPT(5): Factory; DOMAIN(4): Registration]
// END_CONTRACT
bool PluginManager::register_factory(const std::string& plugin_name, PluginFactory factory) {
    if (plugin_name.empty() || !factory) {
        return false;
    }
    
    std::unique_lock lock(m_mutex);
    m_factories[plugin_name] = factory;
    return true;
}
// END_FUNCTION_PluginManager_register_factory

// START_FUNCTION_PluginManager_unregister_plugin
// START_CONTRACT:
// PURPOSE: Удаление плагина
// INPUTS: plugin_name - имя плагина
// OUTPUTS: bool - результат удаления
// KEYWORDS: [CONCEPT(5): Unregistration; DOMAIN(4): Plugin]
// END_CONTRACT
bool PluginManager::unregister_plugin(const std::string& plugin_name) {
    std::unique_lock lock(m_mutex);
    auto it = m_plugins.find(plugin_name);
    if (it != m_plugins.end()) {
        m_plugins.erase(it);
        return true;
    }
    return false;
}
// END_FUNCTION_PluginManager_unregister_plugin

// START_FUNCTION_PluginManager_get_plugin
// START_CONTRACT:
// PURPOSE: Получение плагина по имени
// INPUTS: plugin_name - имя плагина
// OUTPUTS: PluginPtr - указатель на плагин или nullptr
// KEYWORDS: [CONCEPT(5): Accessor; DOMAIN(4): Plugin]
// END_CONTRACT
PluginPtr PluginManager::get_plugin(const std::string& plugin_name) const {
    std::shared_lock lock(m_mutex);
    auto it = m_plugins.find(plugin_name);
    if (it != m_plugins.end()) {
        return it->second;
    }
    return nullptr;
}
// END_FUNCTION_PluginManager_get_plugin

// START_FUNCTION_PluginManager_get_all_plugins
// START_CONTRACT:
// PURPOSE: Получение всех плагинов
// OUTPUTS: std::vector<PluginPtr> - вектор плагинов
// KEYWORDS: [CONCEPT(5): Accessor; DOMAIN(4): Plugin]
// END_CONTRACT
std::vector<PluginPtr> PluginManager::get_all_plugins() const {
    std::shared_lock lock(m_mutex);
    std::vector<PluginPtr> plugins;
    for (const auto& pair : m_plugins) {
        plugins.push_back(pair.second);
    }
    // Сортировка по приоритету
    std::sort(plugins.begin(), plugins.end(), 
        [](const PluginPtr& a, const PluginPtr& b) {
            return a->get_config().priority < b->get_config().priority;
        });
    return plugins;
}
// END_FUNCTION_PluginManager_get_all_plugins

// START_FUNCTION_PluginManager_get_enabled_plugins
// START_CONTRACT:
// PURPOSE: Получение включённых плагинов
// OUTPUTS: std::vector<PluginPtr> - вектор плагинов
// KEYWORDS: [CONCEPT(5): Accessor; DOMAIN(4): Plugin]
// END_CONTRACT
std::vector<PluginPtr> PluginManager::get_enabled_plugins() const {
    std::shared_lock lock(m_mutex);
    std::vector<PluginPtr> plugins;
    for (const auto& pair : m_plugins) {
        if (pair.second->get_config().enabled) {
            plugins.push_back(pair.second);
        }
    }
    // Сортировка по приоритету
    std::sort(plugins.begin(), plugins.end(), 
        [](const PluginPtr& a, const PluginPtr& b) {
            return a->get_config().priority < b->get_config().priority;
        });
    return plugins;
}
// END_FUNCTION_PluginManager_get_enabled_plugins

// START_FUNCTION_PluginManager_has_plugin
// START_CONTRACT:
// PURPOSE: Проверка наличия плагина
// INPUTS: plugin_name - имя плагина
// OUTPUTS: bool - результат проверки
// KEYWORDS: [CONCEPT(5): Check; DOMAIN(4): Plugin]
// END_CONTRACT
bool PluginManager::has_plugin(const std::string& plugin_name) const {
    std::shared_lock lock(m_mutex);
    return m_plugins.find(plugin_name) != m_plugins.end();
}
// END_FUNCTION_PluginManager_has_plugin

// START_FUNCTION_PluginManager_count
// START_CONTRACT:
// PURPOSE: Получение количества плагинов
// OUTPUTS: size_t - количество плагинов
// KEYWORDS: [CONCEPT(5): Counter; DOMAIN(4): Plugin]
// END_CONTRACT
size_t PluginManager::count() const {
    std::shared_lock lock(m_mutex);
    return m_plugins.size();
}
// END_FUNCTION_PluginManager_count

// START_FUNCTION_PluginManager_clear
// START_CONTRACT:
// PURPOSE: Очистка всех плагинов
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Cleanup; DOMAIN(4): Plugin]
// END_CONTRACT
void PluginManager::clear() {
    std::unique_lock lock(m_mutex);
    m_plugins.clear();
    m_factories.clear();
}
// END_FUNCTION_PluginManager_clear

// START_FUNCTION_PluginManager_initialize_all
// START_CONTRACT:
// PURPOSE: Инициализация всех плагинов
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Lifecycle; DOMAIN(4): Init]
// END_CONTRACT
void PluginManager::initialize_all() {
    auto plugins = get_all_plugins();
    for (auto& plugin : plugins) {
        if (plugin->get_config().enabled) {
            try {
                plugin->initialize();
            } catch (const std::exception& e) {
                PluginLogger logger(plugin->get_info().name);
                logger.error("Failed to initialize: " + std::string(e.what()));
            }
        }
    }
}
// END_FUNCTION_PluginManager_initialize_all

// START_FUNCTION_PluginManager_shutdown_all
// START_CONTRACT:
// PURPOSE: Завершение всех плагинов
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Lifecycle; DOMAIN(4): Shutdown]
// END_CONTRACT
void PluginManager::shutdown_all() {
    auto plugins = get_all_plugins();
    // Обратный порядок (от низкого приоритета к высокому)
    for (auto it = plugins.rbegin(); it != plugins.rend(); ++it) {
        try {
            (*it)->shutdown();
        } catch (const std::exception& e) {
            PluginLogger logger((*it)->get_info().name);
            logger.error("Error during shutdown: " + std::string(e.what()));
        }
    }
    clear();
}
// END_FUNCTION_PluginManager_shutdown_all

// START_FUNCTION_PluginManager_start_all
// START_CONTRACT:
// PURPOSE: Запуск всех плагинов
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Lifecycle; DOMAIN(4): Control]
// END_CONTRACT
void PluginManager::start_all() {
    auto plugins = get_enabled_plugins();
    for (auto& plugin : plugins) {
        plugin->start();
    }
}
// END_FUNCTION_PluginManager_start_all

// START_FUNCTION_PluginManager_stop_all
// START_CONTRACT:
// PURPOSE: Остановка всех плагинов
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Lifecycle; DOMAIN(4): Control]
// END_CONTRACT
void PluginManager::stop_all() {
    auto plugins = get_all_plugins();
    for (auto& plugin : plugins) {
        plugin->stop();
    }
}
// END_FUNCTION_PluginManager_stop_all

// START_FUNCTION_PluginManager_pause_all
// START_CONTRACT:
// PURPOSE: Приостановка всех плагинов
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Lifecycle; DOMAIN(4): Control]
// END_CONTRACT
void PluginManager::pause_all() {
    auto plugins = get_enabled_plugins();
    for (auto& plugin : plugins) {
        plugin->pause();
    }
}
// END_FUNCTION_PluginManager_pause_all

// START_FUNCTION_PluginManager_resume_all
// START_CONTRACT:
// PURPOSE: Возобновление всех плагинов
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Lifecycle; DOMAIN(4): Control]
// END_CONTRACT
void PluginManager::resume_all() {
    auto plugins = get_enabled_plugins();
    for (auto& plugin : plugins) {
        plugin->resume();
    }
}
// END_FUNCTION_PluginManager_resume_all

// START_FUNCTION_PluginManager_reset_all
// START_CONTRACT:
// PURPOSE: Сброс всех плагинов
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Lifecycle; DOMAIN(4): Reset]
// END_CONTRACT
void PluginManager::reset_all() {
    auto plugins = get_enabled_plugins();
    for (auto& plugin : plugins) {
        plugin->on_reset();
    }
}
// END_FUNCTION_PluginManager_reset_all

// START_FUNCTION_PluginManager_notify_all_metric_update
// START_CONTRACT:
// PURPOSE: Уведомление всех плагинов об обновлении метрик
// INPUTS: metrics - метрики
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Notification; DOMAIN(4): Event]
// END_CONTRACT
void PluginManager::notify_all_metric_update(const PluginMetrics& metrics) {
    auto plugins = get_enabled_plugins();
    for (auto& plugin : plugins) {
        if (plugin->get_state() == PluginState::ACTIVE) {
            plugin->on_metrics_update(metrics);
        }
    }
}
// END_FUNCTION_PluginManager_notify_all_metric_update

// START_FUNCTION_PluginManager_notify_all_update
// START_CONTRACT:
// PURPOSE: Уведомление всех плагинов об обновлении
// INPUTS: context - контекст обновления
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Notification; DOMAIN(4): Event]
// END_CONTRACT
void PluginManager::notify_all_update(const UpdateContext& context) {
    auto plugins = get_enabled_plugins();
    for (auto& plugin : plugins) {
        if (plugin->get_state() == PluginState::ACTIVE) {
            plugin->on_update(context);
        }
    }
}
// END_FUNCTION_PluginManager_notify_all_update

// START_FUNCTION_PluginManager_notify_all_start
// START_CONTRACT:
// PURPOSE: Уведомление всех плагинов о запуске
// INPUTS: selected_list_path - путь к списку
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Notification; DOMAIN(4): Event]
// END_CONTRACT
void PluginManager::notify_all_start(const std::string& selected_list_path) {
    auto plugins = get_enabled_plugins();
    for (auto& plugin : plugins) {
        plugin->on_start(selected_list_path);
    }
}
// END_FUNCTION_PluginManager_notify_all_start

// START_FUNCTION_PluginManager_notify_all_finish
// START_CONTRACT:
// PURPOSE: Уведомление всех плагинов о завершении
// INPUTS: final_metrics - финальные метрики
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Notification; DOMAIN(4): Event]
// END_CONTRACT
void PluginManager::notify_all_finish(const PluginMetrics& final_metrics) {
    auto plugins = get_enabled_plugins();
    for (auto& plugin : plugins) {
        plugin->on_finish(final_metrics);
    }
}
// END_FUNCTION_PluginManager_notify_all_finish

// START_FUNCTION_PluginManager_notify_all_reset
// START_CONTRACT:
// PURPOSE: Уведомление всех плагинов о сбросе
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Notification; DOMAIN(4): Event]
// END_CONTRACT
void PluginManager::notify_all_reset() {
    auto plugins = get_enabled_plugins();
    for (auto& plugin : plugins) {
        plugin->on_reset();
    }
}
// END_FUNCTION_PluginManager_notify_all_reset

// START_FUNCTION_PluginManager_notify_all_match_found
// START_CONTRACT:
// PURPOSE: Уведомление всех плагинов о совпадениях
// INPUTS: matches - список совпадений, iteration - номер итерации
// OUTPUTS: none
// KEYWORDS: [CONCEPT(5): Notification; DOMAIN(4): Event]
// END_CONTRACT
void PluginManager::notify_all_match_found(const MatchList& matches, int iteration) {
    auto plugins = get_enabled_plugins();
    for (auto& plugin : plugins) {
        if (plugin->get_state() == PluginState::ACTIVE) {
            plugin->on_match_found(matches, iteration);
        }
    }
}
// END_FUNCTION_PluginManager_notify_all_match_found

// START_FUNCTION_PluginManager_health_check_all
// START_CONTRACT:
// PURPOSE: Проверка работоспособности всех плагинов
// OUTPUTS: bool - общий статус
// KEYWORDS: [CONCEPT(5): Health; DOMAIN(4): Check]
// END_CONTRACT
bool PluginManager::health_check_all() const {
    auto plugins = get_all_plugins();
    for (const auto& plugin : plugins) {
        if (!plugin->health_check()) {
            return false;
        }
    }
    return true;
}
// END_FUNCTION_PluginManager_health_check_all

//==============================================================================
// PriorityConverter Implementation
//==============================================================================

// START_FUNCTION_PriorityConverter_from_string
// START_CONTRACT:
// PURPOSE: Преобразование строки в приоритет
// INPUTS: str - строка с приоритетом
// OUTPUTS: int - числовое значение приоритета
// KEYWORDS: [CONCEPT(4): Conversion]
// END_CONTRACT
int PriorityConverter::from_string(const std::string& str) {
    if (str == "HIGHEST") return 0;
    if (str == "HIGH") return 25;
    if (str == "NORMAL") return 50;
    if (str == "LOW") return 75;
    if (str == "LOWEST") return 100;
    return 50; // Default
}
// END_FUNCTION_PriorityConverter_from_string

// START_FUNCTION_PriorityConverter_to_string
// START_CONTRACT:
// PURPOSE: Преобразование приоритета в строку
// INPUTS: priority - числовое значение
// OUTPUTS: std::string - строковое представление
// KEYWORDS: [CONCEPT(4): Conversion]
// END_CONTRACT
std::string PriorityConverter::to_string(int priority) {
    if (priority <= 0) return "HIGHEST";
    if (priority <= 25) return "HIGH";
    if (priority <= 50) return "NORMAL";
    if (priority <= 75) return "LOW";
    return "LOWEST";
}
// END_FUNCTION_PriorityConverter_to_string
