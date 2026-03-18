// FILE: src/plugins/wallet/wallet_dat/crypto/blowfish.cpp
// VERSION: 1.0.0

#include "blowfish.h"
#include <openssl/evp.h>
#include <openssl/sha.h>
#include <openssl/blowfish.h>
#include <openssl/rand.h>
#include <stdexcept>
#include <sstream>
#include <iomanip>
#include <iostream>
#include <fstream>
#include <ctime>
#include <cstring>

#ifndef BF_BLOCK_SIZE
#define BF_BLOCK_SIZE 8
#endif

namespace wallet_crypto {

const std::string WalletCrypto::LOG_FILE = "wallet_crypto.log";

WalletCrypto::WalletCrypto() {}
WalletCrypto::~WalletCrypto() {}

std::vector<unsigned char> WalletCrypto::DeriveKey(const std::string& password,
                                                    const std::vector<unsigned char>& salt) {
    const int key_len = 32;
    const int iv_len = 16;
    std::vector<unsigned char> derived_key(key_len + iv_len);
    
    int rounds = 1;
    int count = EVP_BytesToKey(EVP_bf_ecb(), EVP_sha1(), 
                                salt.empty() ? nullptr : salt.data(),
                                reinterpret_cast<const unsigned char*>(password.data()),
                                password.length(),
                                rounds,
                                derived_key.data(),
                                nullptr);
    
    if (count == 0) {
        throw std::runtime_error("Key derivation failed");
    }
    return derived_key;
}

std::vector<unsigned char> WalletCrypto::GenerateSalt() {
    std::vector<unsigned char> salt(SALT_SIZE);
    if (RAND_bytes(salt.data(), SALT_SIZE) != 1) {
        throw std::runtime_error("Salt generation failed");
    }
    return salt;
}

std::vector<unsigned char> WalletCrypto::EncryptPrivateKey(const std::vector<unsigned char>& private_key,
                                                            const std::vector<unsigned char>& master_key) {
    if (master_key.size() < 32) {
        throw std::runtime_error("Invalid master key size");
    }
    std::vector<unsigned char> key = master_key;
    key.resize(32);
    BF_KEY bf_key;
    BF_set_key(&bf_key, key.size(), key.data());
    std::vector<unsigned char> padded = AddPadding(private_key, BF_BLOCK_SIZE);
    std::vector<unsigned char> encrypted(padded.size());
    for (size_t i = 0; i < padded.size(); i += BF_BLOCK_SIZE) {
        BF_ecb_encrypt(padded.data() + i, encrypted.data() + i, &bf_key, BF_ENCRYPT);
    }
    return encrypted;
}

std::optional<std::vector<unsigned char>> WalletCrypto::DecryptPrivateKey(
    const std::vector<unsigned char>& encrypted_key,
    const std::vector<unsigned char>& master_key) {
    if (master_key.size() < 32) {
        return std::nullopt;
    }
    try {
        std::vector<unsigned char> key = master_key;
        key.resize(32);
        BF_KEY bf_key;
        BF_set_key(&bf_key, key.size(), key.data());
        std::vector<unsigned char> decrypted(encrypted_key.size());
        for (size_t i = 0; i < encrypted_key.size(); i += BF_BLOCK_SIZE) {
            BF_ecb_encrypt(encrypted_key.data() + i, decrypted.data() + i, &bf_key, BF_DECRYPT);
        }
        decrypted = RemovePadding(decrypted, BF_BLOCK_SIZE);
        return decrypted;
    } catch (const std::exception&) {
        return std::nullopt;
    }
}

std::vector<unsigned char> WalletCrypto::ComputeChecksum(const std::vector<unsigned char>& encrypted_key) {
    std::vector<unsigned char> sha1_hash(SHA_DIGEST_LENGTH);
    SHA1(encrypted_key.data(), encrypted_key.size(), sha1_hash.data());
    std::vector<unsigned char> checksum(sha1_hash.begin(), sha1_hash.begin() + CHECKSUM_SIZE);
    return checksum;
}

bool WalletCrypto::VerifyPassword(const std::vector<unsigned char>& encrypted_key,
                                 const std::vector<unsigned char>& master_key,
                                 const std::vector<unsigned char>& checksum) {
    if (encrypted_key.empty() || master_key.size() < 32 || encrypted_key.size() % BF_BLOCK_SIZE != 0) {
        return false;
    }
    return true;
}

std::vector<unsigned char> WalletCrypto::CreateCKey(const std::vector<unsigned char>& private_key,
                                                     const std::string& password) {
    std::vector<unsigned char> salt = GenerateSalt();
    std::vector<unsigned char> master_key = DeriveKey(password, salt);
    std::vector<unsigned char> encrypted_key = EncryptPrivateKey(private_key, master_key);
    std::vector<unsigned char> checksum = ComputeChecksum(encrypted_key);
    std::vector<unsigned char> result;
    result.insert(result.end(), encrypted_key.begin(), encrypted_key.end());
    result.insert(result.end(), checksum.begin(), checksum.end());
    return result;
}

std::vector<unsigned char> WalletCrypto::CreateMKey(const std::string& password) {
    std::vector<unsigned char> salt = GenerateSalt();
    std::vector<unsigned char> master_key = DeriveKey(password, salt);
    std::vector<unsigned char> checksum = ComputeChecksum(master_key);
    std::vector<unsigned char> result;
    std::vector<unsigned char> version_bytes = serializeInt(MKEY_VERSION);
    result.insert(result.end(), version_bytes.begin(), version_bytes.end());
    std::vector<unsigned char> deriv_method = serializeInt(MKEY_DERIVATION_METHOD);
    result.insert(result.end(), deriv_method.begin(), deriv_method.end());
    result.insert(result.end(), salt.begin(), salt.end());
    result.insert(result.end(), master_key.begin(), master_key.end());
    result.insert(result.end(), checksum.begin(), checksum.end());
    return result;
}

std::vector<unsigned char> WalletCrypto::EncryptData(const std::vector<unsigned char>& data,
                                                      const std::vector<unsigned char>& key) {
    if (key.size() < 32) {
        throw std::runtime_error("Invalid key size");
    }
    std::vector<unsigned char> key_data = key;
    key_data.resize(32);
    BF_KEY bf_key;
    BF_set_key(&bf_key, key_data.size(), key_data.data());
    std::vector<unsigned char> padded = AddPadding(data, BF_BLOCK_SIZE);
    std::vector<unsigned char> encrypted(padded.size());
    for (size_t i = 0; i < padded.size(); i += BF_BLOCK_SIZE) {
        BF_ecb_encrypt(padded.data() + i, encrypted.data() + i, &bf_key, BF_ENCRYPT);
    }
    return encrypted;
}

std::optional<std::vector<unsigned char>> WalletCrypto::DecryptData(
    const std::vector<unsigned char>& encrypted_data,
    const std::vector<unsigned char>& key) {
    if (key.size() < 32) {
        return std::nullopt;
    }
    try {
        std::vector<unsigned char> key_data = key;
        key_data.resize(32);
        BF_KEY bf_key;
        BF_set_key(&bf_key, key_data.size(), key_data.data());
        std::vector<unsigned char> decrypted(encrypted_data.size());
        for (size_t i = 0; i < encrypted_data.size(); i += BF_BLOCK_SIZE) {
            BF_ecb_encrypt(encrypted_data.data() + i, decrypted.data() + i, &bf_key, BF_DECRYPT);
        }
        decrypted = RemovePadding(decrypted, BF_BLOCK_SIZE);
        return decrypted;
    } catch (const std::exception&) {
        return std::nullopt;
    }
}

void WalletCrypto::logToFile(const std::string& message) {
    std::ofstream log_file(LOG_FILE, std::ios::app);
    if (log_file.is_open()) {
        std::time_t now = std::time(nullptr);
        char timestamp[64];
        std::strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", std::localtime(&now));
        log_file << "[" << timestamp << "] " << message << std::endl;
        log_file.close();
    }
}

std::vector<unsigned char> WalletCrypto::serializeInt(int value) {
    std::vector<unsigned char> result(4);
    result[0] = static_cast<unsigned char>(value & 0xFF);
    result[1] = static_cast<unsigned char>((value >> 8) & 0xFF);
    result[2] = static_cast<unsigned char>((value >> 16) & 0xFF);
    result[3] = static_cast<unsigned char>((value >> 24) & 0xFF);
    return result;
}

std::vector<unsigned char> WalletCrypto::computeSha1(const std::vector<unsigned char>& data) {
    std::vector<unsigned char> hash(SHA_DIGEST_LENGTH);
    SHA1(data.data(), data.size(), hash.data());
    return hash;
}

std::string WalletCrypto::bytesToHex(const std::vector<unsigned char>& bytes) {
    std::ostringstream oss;
    for (unsigned char b : bytes) {
        oss << std::hex << std::setfill('0') << std::setw(2) << static_cast<int>(b);
    }
    return oss.str();
}

std::vector<unsigned char> WalletCrypto::AddPadding(const std::vector<unsigned char>& data, size_t block_size) {
    size_t padding_len = block_size - (data.size() % block_size);
    if (padding_len == 0) padding_len = block_size;
    std::vector<unsigned char> result = data;
    result.resize(data.size() + padding_len, static_cast<unsigned char>(padding_len));
    return result;
}

std::vector<unsigned char> WalletCrypto::RemovePadding(const std::vector<unsigned char>& data, size_t block_size) {
    if (data.empty()) {
        throw std::runtime_error("Empty data");
    }
    size_t padding_len = data.back();
    if (padding_len == 0 || padding_len > block_size) {
        throw std::runtime_error("Invalid padding");
    }
    for (size_t i = data.size() - padding_len; i < data.size(); i++) {
        if (data[i] != padding_len) {
            throw std::runtime_error("Invalid padding bytes");
        }
    }
    return std::vector<unsigned char>(data.begin(), data.end() - padding_len);
}

std::unique_ptr<WalletCrypto> WalletCryptoFactory::create() {
    return std::make_unique<WalletCrypto>();
}

std::string WalletCryptoFactory::getVersion() {
    return "1.0.0";
}

} // namespace wallet_crypto
