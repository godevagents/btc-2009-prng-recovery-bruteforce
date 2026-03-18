# FILE: src/plugins/crypto/ecdsa_keys/interface.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Python интерфейс плагина генерации ECDSA ключей secp256k1.
# Определяет абстрактный контракт для всех реализаций генератора ключей.
# SCOPE: Криптография, ECDSA, secp256k1, Bitcoin адреса, Base58Check
# INPUT: Нет (интерфейс не имеет входных данных)
# OUTPUT: Абстрактный класс ECDSAPluginInterface с определением методов
# KEYWORDS: [DOMAIN(10): Cryptography; DOMAIN(9): ECDSA; TECH(8): secp256k1; PATTERN(7): Interface]
# LINKS: [IMPLEMENTS(9): C++ ECDSAPluginInterface из ecdsa_keys.h]
# END_MODULE_CONTRACT

from abc import ABC, abstractmethod
from typing import List, Optional


# START_CLASS_ECDSAPluginInterface
# START_CONTRACT:
# PURPOSE: Абстрактный интерфейс плагина генерации ECDSA ключей
# ATTRIBUTES:
# - PRIVATE_KEY_SIZE: int - размер DER-кодированного приватного ключа (279 байт)
# - PUBLIC_KEY_SIZE: int - размер несжатого публичного ключа (65 байт)
# - SIGNATURE_SIZE: int - размер DER-кодированной ECDSA подписи (72 байта)
# - NID_secp256k1: int - идентификатор кривой secp256k1 (714)
# METHODS:
# - generate_key() - генерация новой ключевой пары ECDSA
# - get_private_key() - получение приватного ключа в DER-формате
# - get_public_key() - получение публичного ключа в несжатом формате
# - set_private_key(private_key) - установка приватного ключа из DER-формата
# - set_public_key(public_key) - установка публичного ключа
# - add_entropy(data) - добавление энтропии в OpenSSL пул
# - get_address() - получение Bitcoin адреса из публичного ключа
# - is_valid() - проверка валидности ключа
# - get_entropy_pool_size() - получение размера пула энтропии
# KEYWORDS: [PATTERN(10): AbstractInterface; DOMAIN(9): PluginArchitecture; TECH(8): ECDSA]
# LINKS: [IMPLEMENTS(9): wallet::crypto::ECDSAPluginInterface]
# END_CONTRACT

class ECDSAPluginInterface(ABC):
    """
    Абстрактный интерфейс плагина генерации ECDSA ключей secp256k1.
    
    Соответствует интерфейсу ECDSAPluginInterface из C++ реализации.
    Полностью совместим с оригинальным алгоритмом Bitcoin 0.1.0.
    
    Пример использования:
        class MyECDSAPlugin(ECDSAPluginInterface):
            def generate_key(self) -> bool:
                ...
    """
    
    # Константы из референса Bitcoin 0.1.0
    PRIVATE_KEY_SIZE: int = 279  # DER-encoded
    PUBLIC_KEY_SIZE: int = 65    # Несжатый формат
    SIGNATURE_SIZE: int = 72     # DER-encoded ECDSA
    NID_secp256k1: int = 714     # NID кривой secp256k1
    
    # START_METHOD_generate_key
    # START_CONTRACT:
    # PURPOSE: Генерация новой ключевой пары ECDSA на кривой secp256k1
    # INPUTS: Нет
    # OUTPUTS: bool - результат генерации (true при успехе)
    # SIDE_EFFECTS: Создает новую ключевую пару
    # TEST_CONDITIONS_SUCCESS_CRITERIA: Ключ генерируется без ошибок
    # KEYWORDS: [PATTERN(8): KeyGeneration; DOMAIN(9): ECDSA; TECH(7): secp256k1]
    # LINKS: [CALLS(8): EC_KEY_generate_key]
    # END_CONTRACT
    @abstractmethod
    def generate_key(self) -> bool:
        """Генерация новой ключевой пары ECDSA.
        
        Использует кривую secp256k1 (NID_secp256k1).
        Соответствует оригинальному CKey::MakeNewKey() из Bitcoin 0.1.0.
        
        Returns:
            bool: True если ключ успешно сгенерирован
            
        Raises:
            KeyError: При ошибке генерации
        """
        pass
    # END_METHOD_generate_key
    
    # START_METHOD_get_private_key
    # START_CONTRACT:
    # PURPOSE: Получение приватного ключа в DER-формате
    # INPUTS: Нет
    # OUTPUTS: List[int] - DER-кодированный приватный ключ (279 байт)
    # KEYWORDS: [PATTERN(7): DEREncoding; DOMAIN(8): PrivateKey; TECH(6): OpenSSL]
    # END_CONTRACT
    @abstractmethod
    def get_private_key(self) -> List[int]:
        """Получение приватного ключа в DER-формате.
        
        Формат: 30 <len> 02 01 <privkey_len> 04 <privkey> 30 <pubkey_len> 04 <pubkey_x> 04 <pubkey_y>
        Размер: 279 байт (PRIVATE_KEY_SIZE)
        
        Returns:
            List[int]: DER-кодированный приватный ключ (279 байт)
            
        Raises:
            KeyError: Если ключ не сгенерирован
        """
        pass
    # END_METHOD_get_private_key
    
    # START_METHOD_get_public_key
    # START_CONTRACT:
    # PURPOSE: Получение публичного ключа в несжатом формате
    # INPUTS: Нет
    # OUTPUTS: List[int] - публичный ключ (65 байт)
    # KEYWORDS: [PATTERN(7): PublicKey; DOMAIN(8): ECDSA; TECH(6): Uncompressed]
    # END_CONTRACT
    @abstractmethod
    def get_public_key(self) -> List[int]:
        """Получение публичного ключа в несжатом формате.
        
        Формат: 0x04 + X (32 байта) + Y (32 байта) = 65 байт
        
        Returns:
            List[int]: Публичный ключ (65 байт)
            
        Raises:
            KeyError: Если ключ не сгенерирован
        """
        pass
    # END_METHOD_get_public_key
    
    # START_METHOD_set_private_key
    # START_CONTRACT:
    # PURPOSE: Установка приватного ключа из DER-формата
    # INPUTS: private_key - DER-кодированный приватный ключ
    # OUTPUTS: bool - результат установки
    # KEYWORDS: [PATTERN(6): KeySet; DOMAIN(7): PrivateKey; TECH(5): DER]
    # END_CONTRACT
    @abstractmethod
    def set_private_key(self, private_key: List[int]) -> bool:
        """Установка приватного ключа из DER-формата.
        
        Args:
            private_key: DER-кодированный приватный ключ
            
        Returns:
            bool: True при успешной установке
        """
        pass
    # END_METHOD_set_private_key
    
    # START_METHOD_set_public_key
    # START_CONTRACT:
    # PURPOSE: Установка публичного ключа
    # INPUTS: public_key - публичный ключ (65 байт)
    # OUTPUTS: bool - результат установки
    # KEYWORDS: [PATTERN(6): KeySet; DOMAIN(7): PublicKey; TECH(5): ECDSA]
    # END_CONTRACT
    @abstractmethod
    def set_public_key(self, public_key: List[int]) -> bool:
        """Установка публичного ключа.
        
        Args:
            public_key: Публичный ключ (65 байт)
            
        Returns:
            bool: True при успешной установке
        """
        pass
    # END_METHOD_set_public_key
    
    # START_METHOD_add_entropy
    # START_CONTRACT:
    # PURPOSE: Добавление энтропии в OpenSSL пул
    # INPUTS: data - данные энтропии
    # OUTPUTS: None
    # KEYWORDS: [PATTERN(7): EntropyInjection; DOMAIN(8): Randomness; TECH(6): OpenSSL]
    # END_CONTRACT
    @abstractmethod
    def add_entropy(self, data: bytes) -> None:
        """Добавление энтропии в OpenSSL пул RAND.
        
        Используется для передачи собранной энтропии в OpenSSL RNG.
        Соответствует оригинальному RandAddSeed() из Bitcoin 0.1.0.
        
        Args:
            data: Данные энтропии для добавления
        """
        pass
    # END_METHOD_add_entropy
    
    # START_METHOD_get_address
    # START_CONTRACT:
    # PURPOSE: Генерация Bitcoin адреса из публичного ключа
    # INPUTS: Нет
    # OUTPUTS: str - Base58Check адрес
    # KEYWORDS: [PATTERN(8): Base58Check; DOMAIN(9): BitcoinAddress; TECH(7): RIPEMD160]
    # END_CONTRACT
    @abstractmethod
    def get_address(self) -> str:
        """Получение адреса из публичного ключа (Base58Check).
        
        Алгоритм: Base58Check(0x00 + RIPEMD160(SHA256(PubKey)))
        
        Returns:
            str: Base58Check адрес Bitcoin
            
        Raises:
            KeyError: Если ключ не сгенерирован
        """
        pass
    # END_METHOD_get_address
    
    # START_METHOD_is_valid
    # START_CONTRACT:
    # PURPOSE: Проверка валидности ключа
    # INPUTS: Нет
    # OUTPUTS: bool - true если ключ валиден
    # KEYWORDS: [PATTERN(6): Validation; DOMAIN(7): Key; TECH(5): Check]
    # END_CONTRACT
    @abstractmethod
    def is_valid(self) -> bool:
        """Проверка валидности ключа.
        
        Returns:
            bool: True если ключ валиден
        """
        pass
    # END_METHOD_is_valid
    
    # START_METHOD_get_entropy_pool_size
    # START_CONTRACT:
    # PURPOSE: Получение размера пула энтропии OpenSSL
    # INPUTS: Нет
    # OUTPUTS: int - размер пула (1043 байта)
    # KEYWORDS: [PATTERN(5): EntropyPool; DOMAIN(6): OpenSSL; TECH(4): Size]
    # END_CONTRACT
    @abstractmethod
    def get_entropy_pool_size(self) -> int:
        """Получение константы пула энтропии OpenSSL.
        
        Returns:
            int: Размер состояния пула (1043 байта для OpenSSL RAND_poll)
        """
        pass
    # END_METHOD_get_entropy_pool_size


# END_CLASS_ECDSAPluginInterface


# START_CLASS_ECDSAPluginFactory
# START_CONTRACT:
# PURPOSE: Фабрика для создания экземпляров плагина ECDSA ключей
# ATTRIBUTES: Нет
# METHODS:
# - create() - создание нового экземпляра плагина
# - get_version() - получение версии плагина
# KEYWORDS: [PATTERN(7): Factory; DOMAIN(8): PluginCreation]
# END_CONTRACT

class ECDSAPluginFactory:
    """
    Фабрика для создания экземпляров плагина генерации ECDSA ключей.
    
    Предоставляет статические методы для создания и получения информации о плагине.
    """
    
    # START_METHOD_create
    # START_CONTRACT:
    # PURPOSE: Создание нового экземпляра плагина
    # INPUTS: Нет
    # OUTPUTS: ECDSAPluginInterface - экземпляр плагина
    # KEYWORDS: [PATTERN(8): FactoryMethod; DOMAIN(7): Creation]
    # END_CONTRACT
    @staticmethod
    def create() -> ECDSAPluginInterface:
        """Создать новый экземпляр плагина.
        
        Returns:
            ECDSAPluginInterface: Новый экземпляр плагина
        """
        raise NotImplementedError("Реализация должна переопределить этот метод")
    # END_METHOD_create
    
    # START_METHOD_get_version
    # START_CONTRACT:
    # PURPOSE: Получение версии плагина
    # INPUTS: Нет
    # OUTPUTS: str - версия в формате "major.minor.patch"
    # KEYWORDS: [PATTERN(5): Version; DOMAIN(4): Info]
    # END_CONTRACT
    @staticmethod
    def get_version() -> str:
        """Получить версию плагина.
        
        Returns:
            str: Версия в формате "major.minor.patch"
        """
        raise NotImplementedError("Реализация должна переопределить этот метод")
    # END_METHOD_get_version


# END_CLASS_ECDSAPluginFactory
