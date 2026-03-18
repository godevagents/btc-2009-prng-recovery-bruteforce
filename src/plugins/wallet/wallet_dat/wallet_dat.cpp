#include "wallet_dat.h"
#include "../batch_gen/batch_gen.h"
#include <fstream>
#include <cstring>
#include <stdexcept>
#include <iostream>
#include <sstream>
#include <iomanip>
#include <ctime>
#include <sys/stat.h>
#include <errno.h>

namespace wallet_dat {

// Константы для сериализации
static const unsigned char VARINT_PREFIX_MASK = 0xF8;
static const unsigned char VARINT_CONTINUE_BIT = 0x80;

// Константы для ключей Berkeley DB
static const std::string KEY_VERSION = "version";
static const std::string KEY_DEFAULTKEY = "defaultkey";
static const std::string KEY_KEY = "key";
static const std::string KEY_NAME = "name";
static const std::string KEY_TX = "tx";
static const std::string KEY_SETTING = "setting";

// Определения констант (чтобы избежать множественного определения)
const char* const WALLET_FILENAME = "wallet.dat";
const char* const WALLET_DB_NAME = "main";

// Логирование в файл
static void logToFile(const std::string& message) {
    std::ofstream log_file("logs/wallet_dat.log", std::ios::app);
    if (log_file.is_open()) {
        // Добавляем timestamp
        std::time_t now = std::time(nullptr);
        char timestamp[64];
        std::strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", std::localtime(&now));
        log_file << "[" << timestamp << "] " << message << std::endl;
        log_file.close();
    }
}

// Helper: Convert bytes to hex string
static std::string bytesToHex(const std::vector<unsigned char>& data) {
    std::ostringstream oss;
    oss << std::hex << std::setfill('0');
    for (unsigned char byte : data) {
        oss << std::setw(2) << static_cast<int>(byte);
    }
    return oss.str();
}

// Проверка существования директории
static bool directoryExists(const std::string& path) {
    struct stat info;
    return (stat(path.c_str(), &info) == 0 && (info.st_mode & S_IFDIR));
}

// Создание директории
static bool createDirectory(const std::string& path) {
    return (mkdir(path.c_str(), 0755) == 0 || errno == EEXIST);
}

// WalletDatWriter implementation
WalletDatWriter::WalletDatWriter()
    : berkeley_db_writer_(nullptr),
      db_path_(""),
      db_filename_(""),
      is_initialized_(false),
      is_database_open_(false),
      output_stream_(nullptr),
      use_simple_file_(true),
      is_encrypted_(false) {
    // Создаем Berkeley DB writer
    berkeley_db_writer_ = std::make_unique<berkeley_db::BerkeleyDBWriter>();
}

WalletDatWriter::~WalletDatWriter() {
    close();
}

// START_METHOD_initialize
// START_CONTRACT:
// PURPOSE: Инициализация Berkeley DB Environment
// INPUTS: const std::string& db_path
// OUTPUTS: bool - результат инициализации
// KEYWORDS: PATTERN(8): Initialization; DOMAIN(9): BerkeleyDB; TECH(7): DB_ENV
// END_CONTRACT
bool WalletDatWriter::initialize(const std::string& db_path) {
    // Создаем директорию для логов если её нет
    if (!directoryExists("logs")) {
        createDirectory("logs");
    }
    // Очищаем лог-файл при старте
    std::ofstream init_log("logs/wallet_dat.log", std::ios::trunc);
    init_log.close();
    
    std::ostringstream oss;
    oss << "[initialize] Начало инициализации с путем: " << db_path;
    logToFile(oss.str());
    
    if (db_path.empty()) {
        logToFile("[initialize] ОШИБКА: Путь к базе данных пуст");
        return false;
    }
    
    db_path_ = db_path;
    
    // Создаем директорию если её нет
    if (!directoryExists(db_path_)) {
        if (!createDirectory(db_path_)) {
            oss.str("");
            oss << "[initialize] ОШИБКА: Не удалось создать директорию: " << db_path_;
            logToFile(oss.str());
            return false;
        }
        oss.str("");
        oss << "[initialize] Создана директория: " << db_path_;
        logToFile(oss.str());
    }
    
    // Инициализируем Berkeley DB writer
    logToFile("[initialize] Используется Berkeley DB эмулятор");
    
    is_initialized_ = true;
    
    logToFile("[initialize] Успешная инициализация");
    return true;
}
// END_METHOD_initialize

// START_METHOD_openDbEnvironment
// START_CONTRACT:
// PURPOSE: Открытие Berkeley DB Environment (заглушка)
// INPUTS: Нет
// OUTPUTS: bool - результат открытия
// KEYWORDS: PATTERN(7): DBEnvOpen; DOMAIN(9): BerkeleyDB; TECH(7): Environment
// END_CONTRACT
bool WalletDatWriter::openDbEnvironment() {
    // Заглушка - не используется в текущей реализации
    logToFile("[openDbEnvironment] Berkeley DB Environment (эмулятор)");
    return true;
}
// END_METHOD_openDbEnvironment

// START_METHOD_closeDbEnvironment
// START_CONTRACT:
// PURPOSE: Закрытие Berkeley DB Environment (заглушка)
// INPUTS: Нет
// OUTPUTS: bool - результат закрытия
// KEYWORDS: PATTERN(7): DBEnvClose; DOMAIN(9): BerkeleyDB; TECH(7): Environment
// END_CONTRACT
bool WalletDatWriter::closeDbEnvironment() {
    // Заглушка - не используется в текущей реализации
    logToFile("[closeDbEnvironment] Berkeley DB Environment закрыт (эмулятор)");
    return true;
}
// END_METHOD_closeDbEnvironment

// START_METHOD_createDatabase
// START_CONTRACT:
// PURPOSE: Создание/открытие базы данных wallet.dat с использованием Berkeley DB эмулятора
// INPUTS: const std::string& filename
// OUTPUTS: bool - результат создания
// KEYWORDS: PATTERN(8): DatabaseCreation; DOMAIN(9): BerkeleyDB; TECH(7): DB_BTREE
// END_CONTRACT
bool WalletDatWriter::createDatabase(const std::string& filename) {
    std::ostringstream oss;
    oss << "[createDatabase] Создание базы данных с именем: " << filename;
    logToFile(oss.str());
    
    if (!is_initialized_) {
        logToFile("[createDatabase] ОШИБКА: База данных не инициализирована");
        return false;
    }
    
    db_filename_ = filename;
    
    // Создаем полный путь к файлу
    std::string full_path = db_path_;
    if (!full_path.empty() && full_path.back() != '/' && full_path.back() != '\\') {
        full_path += "/";
    }
    full_path += db_filename_;
    
    // Открываем Berkeley DB writer
    int flags = static_cast<int>(berkeley_db::OpenFlags::CREATE) |
                 static_cast<int>(berkeley_db::OpenFlags::READ_WRITE) |
                 static_cast<int>(berkeley_db::OpenFlags::TRUNCATE);
    
    if (!berkeley_db_writer_->open(full_path, flags)) {
        oss.str("");
        oss << "[createDatabase] ОШИБКА: Не удалось открыть Berkeley DB: " << full_path;
        logToFile(oss.str());
        return false;
    }
    
    is_database_open_ = true;
    
    std::ostringstream success_oss;
    success_oss << "[createDatabase] Успешно открыт файл: " << full_path;
    logToFile(success_oss.str());
    
    return true;
}
// END_METHOD_createDatabase

// START_METHOD_writeVersion
// START_CONTRACT:
// PURPOSE: Запись версии базы данных в Berkeley DB совместимом формате
// INPUTS: int version
// OUTPUTS: bool - результат записи
// KEYWORDS: PATTERN(7): VersionWrite; DOMAIN(8): Metadata; TECH(6): Serialization
// END_CONTRACT
bool WalletDatWriter::writeVersion(int version) {
    std::ostringstream oss;
    oss << "[writeVersion] Запись версии: " << version << " (десятичное)";
    logToFile(oss.str());
    
    if (!is_database_open_ || !berkeley_db_writer_) {
        logToFile("[writeVersion] ОШИБКА: База данных не открыта");
        return false;
    }
    
    try {
        // Используем Berkeley DB writer для записи версии
        bool result = berkeley_db_writer_->writeVersion(version);
        
        if (!result) {
            logToFile("[writeVersion] ОШИБКА записи версии в Berkeley DB");
            return false;
        }
        
        oss.str("");
        oss << "[writeVersion] Успешно записано. Версия: " << version;
        logToFile(oss.str());
        
        return true;
    } catch (const std::exception& e) {
        std::ostringstream err_oss;
        err_oss << "[writeVersion] ОШИБКА исключения: " << e.what();
        logToFile(err_oss.str());
        return false;
    }
}
// END_METHOD_writeVersion

// START_METHOD_writeDefaultKey
// START_CONTRACT:
// PURPOSE: Запись ключа по умолчанию в Berkeley DB совместимом формате
// INPUTS: const std::vector<unsigned char>& pubkey
// OUTPUTS: bool - результат записи
// KEYWORDS: PATTERN(8): DefaultKeyWrite; DOMAIN(8): Bitcoin; TECH(6): KeyStorage
// END_CONTRACT
bool WalletDatWriter::writeDefaultKey(const std::vector<unsigned char>& pubkey) {
    std::ostringstream oss;
    oss << "[writeDefaultKey] Запись default key. Размер pubkey: " << pubkey.size() << " байт";
    logToFile(oss.str());
    
    if (!is_database_open_ || !berkeley_db_writer_) {
        logToFile("[writeDefaultKey] ОШИБКА: База данных не открыта");
        return false;
    }
    
    if (pubkey.empty()) {
        logToFile("[writeDefaultKey] ОШИБКА: Pubkey пуст");
        return false;
    }
    
    try {
        // Используем Berkeley DB writer для записи default key
        bool result = berkeley_db_writer_->writeDefaultKey(pubkey);
        
        if (!result) {
            logToFile("[writeDefaultKey] ОШИБКА записи default key в Berkeley DB");
            return false;
        }
        
        oss.str("");
        oss << "[writeDefaultKey] Успешно записано. Pubkey hex: " << bytesToHex(pubkey);
        logToFile(oss.str());
        
        return true;
    } catch (const std::exception& e) {
        std::ostringstream err_oss;
        err_oss << "[writeDefaultKey] ОШИБКА исключения: " << e.what();
        logToFile(err_oss.str());
        return false;
    }
}
// END_METHOD_writeDefaultKey

// START_METHOD_writeKeyPair
// START_CONTRACT:
// PURPOSE: Запись ключевой пары в Berkeley DB совместимом формате (Bitcoin 0.1.0)
// INPUTS: const std::vector<unsigned char>& pubkey, const std::vector<unsigned char>& privkey
// OUTPUTS: bool - результат записи
// KEYWORDS: PATTERN(7): KeyPairWrite; DOMAIN(8): PrivateKey; TECH(6): DERFormat
// END_CONTRACT
bool WalletDatWriter::writeKeyPair(const std::vector<unsigned char>& pubkey,
                                   const std::vector<unsigned char>& privkey) {
    std::ostringstream oss;
    oss << "[writeKeyPair] Запись ключевой пары. Размер pubkey: " << pubkey.size() 
       << " байт, privkey: " << privkey.size() << " байт, зашифровано: " << is_encrypted_;
    logToFile(oss.str());
    
    if (!is_database_open_ || !berkeley_db_writer_) {
        logToFile("[writeKeyPair] ОШИБКА: База данных не открыта");
        return false;
    }
    
    if (pubkey.empty() || privkey.empty()) {
        logToFile("[writeKeyPair] ОШИБКА: Pubkey или privkey пуст");
        return false;
    }
    
    try {
        // Если кошелек зашифрован, записываем ckey вместо key
        if (is_encrypted_ && !master_key_.empty()) {
            oss.str("");
            oss << "[writeKeyPair] Запись зашифрованного ключа (ckey)";
            logToFile(oss.str());
            
            // Создаем ckey запись
            std::vector<unsigned char> ckey_data = wallet_crypto::WalletCrypto::CreateCKey(privkey, "");
            
            // Если передан пустой пароль, используем уже установленный мастер-ключ
            if (ckey_data.empty()) {
                // Шифруем приватный ключ вручную
                std::vector<unsigned char> encrypted_key = wallet_crypto::WalletCrypto::EncryptPrivateKey(privkey, master_key_);
                
                // Формат ckey: 1 байт (pubkey size) + pubkey + encrypted_key
                std::vector<unsigned char> ckey_value;
                ckey_value.push_back(static_cast<unsigned char>(pubkey.size()));
                ckey_value.insert(ckey_value.end(), pubkey.begin(), pubkey.end());
                ckey_value.insert(ckey_value.end(), encrypted_key.begin(), encrypted_key.end());
                
                ckey_data = ckey_value;
            }
            
            // Формат ключа: "ckey" + pubkey
            std::vector<unsigned char> ckey_key;
            std::string ckey_str = "ckey";
            ckey_key.insert(ckey_key.end(), ckey_str.begin(), ckey_str.end());
            ckey_key.insert(ckey_key.end(), pubkey.begin(), pubkey.end());
            
            berkeley_db::DbResult result = berkeley_db_writer_->put(ckey_key, ckey_data);
            
            if (result == berkeley_db::DbResult::ERROR) {
                logToFile("[writeKeyPair] ОШИБКА записи ckey в Berkeley DB");
                return false;
            }
            
            oss.str("");
            oss << "[writeKeyPair] Успешно записано ckey. Pubkey: " << bytesToHex(pubkey);
            logToFile(oss.str());
        } else {
            // Используем Berkeley DB writer для записи ключевой пары (незашифрованный формат)
            bool result = berkeley_db_writer_->writeKeyPair(pubkey, privkey);
            
            if (!result) {
                logToFile("[writeKeyPair] ОШИБКА записи ключевой пары в Berkeley DB");
                return false;
            }
            
            oss.str("");
            oss << "[writeKeyPair] Успешно записано. Pubkey: " << bytesToHex(pubkey);
            logToFile(oss.str());
        }
        
        return true;
    } catch (const std::exception& e) {
        std::ostringstream err_oss;
        err_oss << "[writeKeyPair] ОШИБКА исключения: " << e.what();
        logToFile(err_oss.str());
        return false;
    }
}
// END_METHOD_writeKeyPair

// START_METHOD_writeAddressBook
// START_CONTRACT:
// PURPOSE: Запись адресной книги в Berkeley DB совместимом формате
// INPUTS: const std::string& address, const std::string& name
// OUTPUTS: bool - результат записи
// KEYWORDS: PATTERN(8): AddressBookWrite; DOMAIN(7): Contacts; TECH(5): DB
// END_CONTRACT
bool WalletDatWriter::writeAddressBook(const std::string& address,
                                       const std::string& name) {
    std::ostringstream oss;
    oss << "[writeAddressBook] Запись адресной книги. Адрес: " << address << ", Имя: '" << name << "'";
    logToFile(oss.str());
    
    if (!is_database_open_ || !berkeley_db_writer_) {
        logToFile("[writeAddressBook] ОШИБКА: База данных не открыта");
        return false;
    }
    
    if (address.empty()) {
        logToFile("[writeAddressBook] ОШИБКА: Адрес пуст");
        return false;
    }
    
    try {
        // Используем Berkeley DB writer для записи адресной книги
        bool result = berkeley_db_writer_->writeName(address, name);
        
        if (!result) {
            logToFile("[writeAddressBook] ОШИБКА записи адресной книги в Berkeley DB");
            return false;
        }
        
        logToFile("[writeAddressBook] Успешно записано");
        
        return true;
    } catch (const std::exception& e) {
        std::ostringstream err_oss;
        err_oss << "[writeAddressBook] ОШИБКА исключения: " << e.what();
        logToFile(err_oss.str());
        return false;
    }
}
// END_METHOD_writeAddressBook

// START_METHOD_writeSetting
// START_CONTRACT:
// PURPOSE: Запись настройки в Berkeley DB совместимом формате
// INPUTS: const std::string& key, const std::vector<unsigned char>& value
// OUTPUTS: bool - результат записи
// KEYWORDS: PATTERN(7): SettingWrite; DOMAIN(7): Config; TECH(5): DB
// END_CONTRACT
bool WalletDatWriter::writeSetting(const std::string& key,
                                   const std::vector<unsigned char>& value) {
    std::ostringstream oss;
    oss << "[writeSetting] Запись настройки. Ключ: " << key << ", Размер: " << value.size() << " байт";
    logToFile(oss.str());
    
    if (!is_database_open_ || !berkeley_db_writer_) {
        logToFile("[writeSetting] ОШИБКА: База данных не открыта");
        return false;
    }
    
    if (key.empty()) {
        logToFile("[writeSetting] ОШИБКА: Ключ настройки пуст");
        return false;
    }
    
    try {
        // Используем Berkeley DB writer для записи настройки
        bool result = berkeley_db_writer_->writeSetting(key, value);
        
        if (!result) {
            logToFile("[writeSetting] ОШИБКА записи настройки в Berkeley DB");
            return false;
        }
        
        logToFile("[writeSetting] Успешно записано");
        return true;
    } catch (const std::exception& e) {
        std::ostringstream err_oss;
        err_oss << "[writeSetting] ОШИБКА исключения: " << e.what();
        logToFile(err_oss.str());
        return false;
    }
}
// END_METHOD_writeSetting

// START_METHOD_writeTx
// START_CONTRACT:
// PURPOSE: Запись транзакции в Berkeley DB совместимом формате
// INPUTS: const std::vector<unsigned char>& txHash, const std::vector<unsigned char>& txData
// OUTPUTS: bool - результат записи
// KEYWORDS: PATTERN(6): TxWrite; DOMAIN(8): Transaction; TECH(5): DB
// END_CONTRACT
bool WalletDatWriter::writeTx(const std::vector<unsigned char>& txHash,
                              const std::vector<unsigned char>& txData) {
    std::ostringstream oss;
    oss << "[writeTx] Запись транзакции. Размер txHash: " << txHash.size() 
       << " байт, txData: " << txData.size() << " байт";
    logToFile(oss.str());
    
    if (!is_database_open_ || !berkeley_db_writer_) {
        logToFile("[writeTx] ОШИБКА: База данных не открыта");
        return false;
    }
    
    if (txHash.empty()) {
        logToFile("[writeTx] ОШИБКА: Хеш транзакции пуст");
        return false;
    }
    
    try {
        // Используем Berkeley DB writer для записи транзакции
        bool result = berkeley_db_writer_->writeTx(txHash, txData);
        
        if (!result) {
            logToFile("[writeTx] ОШИБКА записи транзакции в Berkeley DB");
            return false;
        }
        
        logToFile("[writeTx] Успешно записано");
        return true;
    } catch (const std::exception& e) {
        std::ostringstream err_oss;
        err_oss << "[writeTx] ОШИБКА исключения: " << e.what();
        logToFile(err_oss.str());
        return false;
    }
}
// END_METHOD_writeTx

// START_METHOD_writeWalletCollection
// START_CONTRACT:
// PURPOSE: Запись полной коллекции кошельков с использованием Berkeley DB эмулятора
// INPUTS: const WalletCollection& collection
// OUTPUTS: bool - результат записи
// KEYWORDS: PATTERN(9): CollectionWrite; DOMAIN(9): BatchWallet; TECH(8): Transaction
// END_CONTRACT
bool WalletDatWriter::writeWalletCollection(const wallet_batch::WalletCollection& collection) {
    std::ostringstream oss;
    oss << "[writeWalletCollection] Начало записи коллекции. Количество кошельков: " << collection.size();
    logToFile(oss.str());
    
    if (!is_database_open_) {
        logToFile("[writeWalletCollection] ОШИБКА: База данных не открыта");
        return false;
    }
    
    if (collection.size() == 0) {
        logToFile("[writeWalletCollection] ОШИБКА: Коллекция пуста");
        return false;
    }
    
    try {
        // Шаг 1: Записываем версию базы данных
        logToFile("[writeWalletCollection] Шаг 1: Запись версии базы данных...");
        if (!writeVersion(WALLET_VERSION)) {
            logToFile("[writeWalletCollection] ОШИБКА: Не удалось записать версию");
            return false;
        }
        logToFile("[writeWalletCollection] Шаг 1: Версия успешно записана");
        
        // Шаг 2: Записываем default key из первого кошелька
        if (collection.size() > 0) {
            logToFile("[writeWalletCollection] Шаг 2: Запись default key...");
            wallet_batch::WalletData first_wallet = collection.getWalletAt(0);
            if (!writeDefaultKey(first_wallet.public_key)) {
                logToFile("[writeWalletCollection] ОШИБКА: Не удалось записать default key");
                return false;
            }
            oss.str("");
            oss << "[writeWalletCollection] Шаг 2: Default key успешно записан (адрес: " << first_wallet.address << ")";
            logToFile(oss.str());
        }
        
        // Шаг 3: Записываем ключевые пары для всех кошельков
        logToFile("[writeWalletCollection] Шаг 3: Запись ключевых пар...");
        size_t key_pairs_written = 0;
        for (size_t i = 0; i < collection.size(); i++) {
            wallet_batch::WalletData wallet = collection.getWalletAt(i);
            
            oss.str("");
            oss << "[writeWalletCollection] Запись ключевой пары " << (i + 1) << "/" << collection.size() 
               << " (адрес: " << wallet.address << ")";
            logToFile(oss.str());
            
            if (!writeKeyPair(wallet.public_key, wallet.private_key)) {
                oss.str("");
                oss << "[writeWalletCollection] ОШИБКА: Не удалось записать ключевую пару для кошелька " << i;
                logToFile(oss.str());
                return false;
            }
            key_pairs_written++;
        }
        oss.str("");
        oss << "[writeWalletCollection] Шаг 3: Успешно записано " << key_pairs_written << " ключевых пар";
        logToFile(oss.str());
        
        // Шаг 4: Записываем адресную книгу (только первые 10 адресов для экономии места)
        logToFile("[writeWalletCollection] Шаг 4: Запись адресной книги...");
        size_t max_addresses = std::min(collection.size(), static_cast<size_t>(10));
        size_t addresses_written = 0;
        for (size_t i = 0; i < max_addresses; i++) {
            wallet_batch::WalletData wallet = collection.getWalletAt(i);
            
            // Используем адрес в качестве метки
            std::string label = "Wallet " + std::to_string(i + 1);
            
            oss.str("");
            oss << "[writeWalletCollection] Запись адресной книги " << (i + 1) << "/" << max_addresses 
               << " (адрес: " << wallet.address << ", метка: " << label << ")";
            logToFile(oss.str());
            
            if (!writeAddressBook(wallet.address, label)) {
                oss.str("");
                oss << "[writeWalletCollection] ОШИБКА: Не удалось записать адресную книгу для " << wallet.address;
                logToFile(oss.str());
                return false;
            }
            addresses_written++;
        }
        oss.str("");
        oss << "[writeWalletCollection] Шаг 4: Успешно записано " << addresses_written << " адресов в адресную книгу";
        logToFile(oss.str());
        
        logToFile("[writeWalletCollection] Завершено успешно");
        
        return true;
    } catch (const std::exception& e) {
        std::ostringstream err_oss;
        err_oss << "[writeWalletCollection] ОШИБКА исключения: " << e.what();
        logToFile(err_oss.str());
        return false;
    }
}
// END_METHOD_writeWalletCollection

// START_METHOD_close
// START_CONTRACT:
// PURPOSE: Закрытие базы данных и освобождение ресурсов
// INPUTS: Нет
// OUTPUTS: bool - результат закрытия
// KEYWORDS: PATTERN(6): DatabaseClose; DOMAIN(7): Cleanup; TECH(5): Resource
// END_CONTRACT
bool WalletDatWriter::close() {
    logToFile("[close] Завершение работы. Лог сохранен.");
    logToFile("[close] Закрытие базы данных...");
    
    // Закрываем Berkeley DB writer
    if (berkeley_db_writer_ && berkeley_db_writer_->isOpen()) {
        berkeley_db_writer_->close();
    }
    
    // Закрываем Berkeley DB Environment
    closeDbEnvironment();
    
    // Закрываем файл
    if (output_stream_ != nullptr) {
        if (output_stream_->is_open()) {
            output_stream_->flush();
            output_stream_->close();
        }
        delete output_stream_;
        output_stream_ = nullptr;
    }
    
    is_database_open_ = false;
    is_initialized_ = false;
    
    logToFile("[close] База данных закрыта");
    return true;
}
// END_METHOD_close

// START_METHOD_readWalletDat
// START_CONTRACT:
// PURPOSE: Чтение всех ключей из существующего wallet.dat
// INPUTS: const std::string& filepath
// OUTPUTS: WalletCollection - коллекция кошельков
// KEYWORDS: PATTERN(8): WalletDatRead; DOMAIN(9): BerkeleyDB; TECH(7): Deserialization
// END_CONTRACT
wallet_batch::WalletCollection WalletDatWriter::readWalletDat(const std::string& filepath) {
    wallet_batch::WalletCollection collection;
    
    logToFile("[readWalletDat] Начало чтения wallet.dat: " + filepath);
    
    try {
        // Создаём новый экземпляр BerkeleyDBWriter для чтения
        auto bdb_reader = std::make_unique<berkeley_db::BerkeleyDBWriter>();
        
        // Открываем файл в режиме чтения
        if (!bdb_reader->open(filepath, static_cast<int>(berkeley_db::OpenFlags::READ_ONLY))) {
            logToFile("[readWalletDat] ОШИБКА: Не удалось открыть файл для чтения");
            return collection;
        }
        
        logToFile("[readWalletDat] Файл успешно открыт через BerkeleyDBWriter");
        
        // Получаем все записи
        auto records = bdb_reader->getAllRecords();
        
        std::ostringstream oss;
        oss << "[readWalletDat] Прочитано записей: " << records.size();
        logToFile(oss.str());
        
        // Обрабатываем каждую запись
        for (const auto& [key, value] : records) {
            // Десериализуем ключ
            std::string key_str(key.begin(), key.end());
            
            oss.str("");
            oss << "[readWalletDat] Обработка записи: ключ='" << key_str << "', размер значения=" << value.size();
            logToFile(oss.str());
            
            // Определяем тип записи
            if (key_str == "version") {
                // Версия базы данных
                if (value.size() >= 4) {
                    int version = deserializeInt(value);
                    oss.str("");
                    oss << "[readWalletDat] Найдена версия: " << version;
                    logToFile(oss.str());
                }
            } else if (key_str == "defaultkey") {
                // Ключ по умолчанию
                wallet_batch::WalletData default_wallet;
                default_wallet.public_key = value;
                default_wallet.index = collection.size();
                default_wallet.entropy_source = "wallet.dat";
                collection.addWallet(default_wallet);
                
                oss.str("");
                oss << "[readWalletDat] Добавлен default wallet с pubkey size: " << value.size();
                logToFile(oss.str());
            } else if (key_str.size() >= 4 && key_str.substr(0, 3) == "key") {
                // Это ключевая пара (key + pubkey = незашифрованный приватный ключ)
                // Формат: "key" + pubkey (3 байта) -> privkey value
                oss.str("");
                oss << "[readWalletDat] Найдена ключевая пара (незашифрованная)";
                logToFile(oss.str());
                
                // Если это "key" + pubkey формат
                if (key_str.size() > 3) {
                    std::vector<unsigned char> pubkey(key_str.begin() + 3, key_str.end());
                    
                    wallet_batch::WalletData wallet;
                    wallet.public_key = pubkey;
                    wallet.private_key = value;
                    wallet.index = collection.size();
                    wallet.entropy_source = "wallet.dat";
                    collection.addWallet(wallet);
                    
                    oss.str("");
                    oss << "[readWalletDat] Добавлен кошелек с pubkey size: " << pubkey.size() << ", privkey size: " << value.size();
                    logToFile(oss.str());
                }
            } else if (key_str.size() >= 5 && key_str.substr(0, 4) == "ckey") {
                // Это зашифрованная ключевая пара (ckey + pubkey)
                oss.str("");
                oss << "[readWalletDat] Найдена зашифрованная ключевая пара (ckey)";
                logToFile(oss.str());
                
                if (key_str.size() > 4) {
                    std::vector<unsigned char> pubkey(key_str.begin() + 4, key_str.end());
                    
                    // Пока не расшифровываем - требуется мастер-ключ
                    wallet_batch::WalletData wallet;
                    wallet.public_key = pubkey;
                    wallet.private_key = value; // Это зашифрованные данные
                    wallet.index = collection.size();
                    wallet.entropy_source = "wallet.dat (encrypted)";
                    collection.addWallet(wallet);
                    
                    oss.str("");
                    oss << "[readWalletDat] Добавлен зашифрованный кошелек с pubkey size: " << pubkey.size();
                    logToFile(oss.str());
                }
            } else if (key_str.size() >= 4 && key_str.substr(0, 4) == "name") {
                // Адресная книга
                oss.str("");
                oss << "[readWalletDat] Найдена запись адресной книги";
                logToFile(oss.str());
            } else if (key_str.size() >= 2 && key_str.substr(0, 2) == "tx") {
                // Транзакция
                oss.str("");
                oss << "[readWalletDat] Найдена транзакция";
                logToFile(oss.str());
            } else if (key_str == "mkey") {
                // Мастер-ключ
                oss.str("");
                oss << "[readWalletDat] Найден мастер-ключ (mkey)";
                logToFile(oss.str());
            } else {
                oss.str("");
                oss << "[readWalletDat] Неизвестный тип записи: '" << key_str << "'";
                logToFile(oss.str());
            }
        }
        
        // Закрываем reader
        bdb_reader->close();
        
        oss.str("");
        oss << "[readWalletDat] Успешно прочитано " << collection.size() << " кошельков";
        logToFile(oss.str());
        
        return collection;
        
    } catch (const std::exception& e) {
        std::ostringstream err_oss;
        err_oss << "[readWalletDat] ОШИБКА исключения: " << e.what();
        logToFile(err_oss.str());
        return collection;
    }
}
// END_METHOD_readWalletDat

// START_METHOD_getFilePath
// START_CONTRACT:
// PURPOSE: Получение пути к текущему файлу
// INPUTS: Нет
// OUTPUTS: std::string - путь к wallet.dat
// KEYWORDS: PATTERN(5): FilePath; DOMAIN(6): Accessor; TECH(4): Getter
// END_CONTRACT
std::string WalletDatWriter::getFilePath() const {
    std::string full_path = db_path_;
    if (!full_path.empty() && full_path.back() != '/' && full_path.back() != '\\') {
        full_path += "/";
    }
    full_path += db_filename_;
    return full_path;
}
// END_METHOD_getFilePath

// START_METHOD_setMasterKey
// START_CONTRACT:
// PURPOSE: Установка мастер-ключа из пароля
// INPUTS: const std::string& password
// OUTPUTS: bool - результат установки
// KEYWORDS: PATTERN(8): MasterKeySet; DOMAIN(9): Cryptography; TECH(7): KeyDerivation
// END_CONTRACT
bool WalletDatWriter::setMasterKey(const std::string& password) {
    std::ostringstream oss;
    oss << "[setMasterKey] Установка мастер-ключа из пароля";
    logToFile(oss.str());
    
    if (password.empty()) {
        logToFile("[setMasterKey] ОШИБКА: Пароль пуст");
        return false;
    }
    
    try {
        // Генерируем соль если её нет
        if (salt_.empty()) {
            salt_ = wallet_crypto::WalletCrypto::GenerateSalt();
            oss.str("");
            oss << "[setMasterKey] Сгенерирована соль: " << bytesToHex(salt_);
            logToFile(oss.str());
        }
        
        // Деривируем мастер-ключ из пароля
        master_key_ = wallet_crypto::WalletCrypto::DeriveKey(password, salt_);
        
        oss.str("");
        oss << "[setMasterKey] Мастер-ключ установлен. Размер: " << master_key_.size() << " байт";
        logToFile(oss.str());
        
        return true;
    } catch (const std::exception& e) {
        std::ostringstream err_oss;
        err_oss << "[setMasterKey] ОШИБКА исключения: " << e.what();
        logToFile(err_oss.str());
        return false;
    }
}
// END_METHOD_setMasterKey

// START_METHOD_encryptWallet
// START_CONTRACT:
// PURPOSE: Включение шифрования кошелька с записью mkey
// INPUTS: const std::string& password
// OUTPUTS: bool - результат операции
// KEYWORDS: PATTERN(9): WalletEncryption; DOMAIN(9): Cryptography; TECH(8): BlowfishECB
// END_CONTRACT
bool WalletDatWriter::encryptWallet(const std::string& password) {
    std::ostringstream oss;
    oss << "[encryptWallet] Включение шифрования кошелька";
    logToFile(oss.str());
    
    if (password.empty()) {
        logToFile("[encryptWallet] ОШИБКА: Пароль пуст");
        return false;
    }
    
    if (!is_database_open_ || !berkeley_db_writer_) {
        logToFile("[encryptWallet] ОШИБКА: База данных не открыта");
        return false;
    }
    
    try {
        // Генерируем соль
        salt_ = wallet_crypto::WalletCrypto::GenerateSalt();
        
        oss.str("");
        oss << "[encryptWallet] Соль сгенерирована: " << bytesToHex(salt_);
        logToFile(oss.str());
        
        // Деривируем мастер-ключ из пароля
        master_key_ = wallet_crypto::WalletCrypto::DeriveKey(password, salt_);
        
        oss.str("");
        oss << "[encryptWallet] Мастер-ключ деривирован. Размер: " << master_key_.size() << " байт";
        logToFile(oss.str());
        
        // Создаем mkey запись
        std::vector<unsigned char> mkey_data = wallet_crypto::WalletCrypto::CreateMKey(password);
        
        // Формат ключа: "mkey" + id (1 байт)
        std::vector<unsigned char> mkey_key;
        std::string mkey_str = "mkey";
        mkey_key.insert(mkey_key.end(), mkey_str.begin(), mkey_str.end());
        mkey_key.push_back(0x01); // MKEY_ID = 1
        
        // Записываем mkey
        berkeley_db::DbResult result = berkeley_db_writer_->put(mkey_key, mkey_data);
        
        if (result == berkeley_db::DbResult::ERROR) {
            logToFile("[encryptWallet] ОШИБКА записи mkey");
            return false;
        }
        
        // Вычисляем контрольную сумму (первый зашифрованный ключ будет содержать эту информацию)
        // Для простоты используем SHA1 от пустых данных с мастер-ключом
        checksum_ = wallet_crypto::WalletCrypto::ComputeChecksum(master_key_);
        
        oss.str("");
        oss << "[encryptWallet] mkey записан. Контрольная сумма: " << bytesToHex(checksum_);
        logToFile(oss.str());
        
        is_encrypted_ = true;
        
        logToFile("[encryptWallet] Шифрование кошелька включено успешно");
        return true;
    } catch (const std::exception& e) {
        std::ostringstream err_oss;
        err_oss << "[encryptWallet] ОШИБКА исключения: " << e.what();
        logToFile(err_oss.str());
        return false;
    }
}
// END_METHOD_encryptWallet

// START_METHOD_isEncrypted
// START_CONTRACT:
// PURPOSE: Проверка состояния шифрования кошелька
// INPUTS: Нет
// OUTPUTS: bool - true если кошелек зашифрован
// KEYWORDS: PATTERN(8): EncryptionCheck; DOMAIN(9): Cryptography; TECH(6): State
// END_CONTRACT
bool WalletDatWriter::isEncrypted() const {
    std::ostringstream oss;
    oss << "[isEncrypted] Проверка состояния шифрования: " << (is_encrypted_ ? "зашифрован" : "не зашифрован");
    logToFile(oss.str());
    return is_encrypted_;
}
// END_METHOD_isEncrypted

// START_METHOD_verifyPassword
// START_CONTRACT:
// PURPOSE: Верификация пароля по контрольной сумме
// INPUTS: const std::string& password
// OUTPUTS: bool - true если пароль корректен
// KEYWORDS: PATTERN(9): PasswordVerify; DOMAIN(9): Authentication; TECH(7): Validation
// END_CONTRACT
bool WalletDatWriter::verifyPassword(const std::string& password) const {
    std::ostringstream oss;
    oss << "[verifyPassword] Проверка пароля";
    logToFile(oss.str());
    
    if (password.empty()) {
        logToFile("[verifyPassword] ОШИБКА: Пароль пуст");
        return false;
    }
    
    if (salt_.empty() || master_key_.empty()) {
        logToFile("[verifyPassword] ОШИБКА: Соль или мастер-ключ не установлены");
        return false;
    }
    
    try {
        // Деривируем ключ из пароля
        std::vector<unsigned char> derived_key = wallet_crypto::WalletCrypto::DeriveKey(password, salt_);
        
        // Вычисляем контрольную сумму
        std::vector<unsigned char> computed_checksum = wallet_crypto::WalletCrypto::ComputeChecksum(derived_key);
        
        // Сравниваем контрольные суммы
        bool is_valid = (computed_checksum.size() >= 4 && checksum_.size() >= 4);
        if (is_valid) {
            is_valid = (computed_checksum[0] == checksum_[0]) &&
                       (computed_checksum[1] == checksum_[1]) &&
                       (computed_checksum[2] == checksum_[2]) &&
                       (computed_checksum[3] == checksum_[3]);
        }
        
        oss.str("");
        oss << "[verifyPassword] Результат проверки: " << (is_valid ? "корректен" : "некорректен");
        logToFile(oss.str());
        
        return is_valid;
    } catch (const std::exception& e) {
        std::ostringstream err_oss;
        err_oss << "[verifyPassword] ОШИБКА исключения: " << e.what();
        logToFile(err_oss.str());
        return false;
    }
}
// END_METHOD_verifyPassword

// START_METHOD_encodeVarint
// START_CONTRACT:
// PURPOSE: Кодирование числа в формат Bitcoin Varint
// INPUTS: uint64_t value
// OUTPUTS: std::vector<unsigned char> - закодированное значение
// KEYWORDS: PATTERN(8): VarintEncode; DOMAIN(7): Serialization; TECH(6): Bitcoin
// END_CONTRACT
std::vector<unsigned char> WalletDatWriter::encodeVarint(uint64_t value) const {
    std::vector<unsigned char> result;
    
    // Varint кодирование для Bitcoin
    // 0-127: 1 байт
    // 128-16383: 2 байта
    // 16384-2097151: 3 байта
    // и т.д.
    
    while (value >= 0x80) {
        // Записываем байт с установленным старшим битом (continue bit)
        result.push_back(static_cast<unsigned char>((value & 0x7F) | 0x80));
        value >>= 7;
    }
    
    // Записываем последний байт без continue bit
    result.push_back(static_cast<unsigned char>(value & 0x7F));
    
    return result;
}
// END_METHOD_encodeVarint

// START_METHOD_decodeVarint
// START_CONTRACT:
// PURPOSE: Декодирование числа из формата Bitcoin Varint
// INPUTS: std::ifstream& stream
// OUTPUTS: uint64_t - декодированное значение
// KEYWORDS: PATTERN(8): VarintDecode; DOMAIN(7): Deserialization; TECH(6): Bitcoin
// END_CONTRACT
uint64_t WalletDatWriter::decodeVarint(std::ifstream& stream) const {
    uint64_t result = 0;
    int shift = 0;
    
    while (true) {
        unsigned char byte;
        if (!stream.read(reinterpret_cast<char*>(&byte), 1)) {
            return 0;
        }
        
        result |= static_cast<uint64_t>(byte & 0x7F) << shift;
        
        // Если старший бит не установлен, это последний байт
        if ((byte & 0x80) == 0) {
            break;
        }
        
        shift += 7;
        
        // Защита от бесконечного цикла
        if (shift > 63) {
            return 0;
        }
    }
    
    return result;
}
// END_METHOD_decodeVarint

// START_METHOD_serializeInt
// START_CONTRACT:
// PURPOSE: Сериализация int в little-endian формат
// INPUTS: int value
// OUTPUTS: std::vector<unsigned char> - сериализованные данные
// KEYWORDS: PATTERN(7): Serialization; DOMAIN(6): Integer; TECH(5): LittleEndian
// END_CONTRACT
std::vector<unsigned char> WalletDatWriter::serializeInt(int value) const {
    std::vector<unsigned char> result(4);
    result[0] = static_cast<unsigned char>(value & 0xFF);
    result[1] = static_cast<unsigned char>((value >> 8) & 0xFF);
    result[2] = static_cast<unsigned char>((value >> 16) & 0xFF);
    result[3] = static_cast<unsigned char>((value >> 24) & 0xFF);
    return result;
}
// END_METHOD_serializeInt

// START_METHOD_serializeString
// START_CONTRACT:
// PURPOSE: Сериализация строки с префиксом varint длины
// INPUTS: const std::string& str
// OUTPUTS: std::vector<unsigned char> - сериализованные данные
// KEYWORDS: PATTERN(7): Serialization; DOMAIN(6): String; TECH(5): VarInt
// END_CONTRACT
std::vector<unsigned char> WalletDatWriter::serializeString(const std::string& str) const {
    std::vector<unsigned char> result;
    // Добавляем varint длину
    std::vector<unsigned char> len_prefix = encodeVarint(str.size());
    result.insert(result.end(), len_prefix.begin(), len_prefix.end());
    // Добавляем данные
    result.insert(result.end(), str.begin(), str.end());
    return result;
}
// END_METHOD_serializeString

// START_METHOD_deserializeInt
// START_CONTRACT:
// PURPOSE: Десериализация int из little-endian формата
// INPUTS: const std::vector<unsigned char>& data
// OUTPUTS: int - десериализованное значение
// KEYWORDS: PATTERN(8): Deserialization; DOMAIN(6): Integer; TECH(5): LittleEndian
// END_CONTRACT
int WalletDatWriter::deserializeInt(const std::vector<unsigned char>& data) const {
    if (data.size() < 4) {
        return 0;
    }
    int result = 0;
    result |= static_cast<int>(data[0]);
    result |= static_cast<int>(data[1]) << 8;
    result |= static_cast<int>(data[2]) << 16;
    result |= static_cast<int>(data[3]) << 24;
    return result;
}
// END_METHOD_deserializeInt

// START_METHOD_deserializeString
// START_CONTRACT:
// PURPOSE: Десериализация строки из формата с varint префиксом
// INPUTS: const std::vector<unsigned char>& data
// OUTPUTS: std::string - десериализованная строка
// KEYWORDS: PATTERN(8): Deserialization; DOMAIN(6): String; TECH(5): VarInt
// END_CONTRACT
std::string WalletDatWriter::deserializeString(const std::vector<unsigned char>& data) const {
    if (data.empty()) {
        return "";
    }
    
    // Читаем varint длину
    uint64_t len = 0;
    size_t pos = 0;
    
    for (size_t i = 0; i < data.size() && i < 10; i++) {
        len |= static_cast<uint64_t>(data[i] & 0x7F) << (i * 7);
        pos++;
        if ((data[i] & 0x80) == 0) {
            break;
        }
    }
    
    if (data.size() < pos + len) {
        return "";
    }
    
    return std::string(data.begin() + pos, data.begin() + pos + len);
}
// END_METHOD_deserializeString

// Фабрика
std::unique_ptr<WalletDatWriterInterface> WalletDatPluginFactory::create() {
    logToFile("[WalletDatPluginFactory::create] Создание нового экземпляра WalletDatWriter");
    return std::make_unique<WalletDatWriter>();
}

std::string WalletDatPluginFactory::getVersion() {
    return "2.0.0";
}

} // namespace wallet_dat
