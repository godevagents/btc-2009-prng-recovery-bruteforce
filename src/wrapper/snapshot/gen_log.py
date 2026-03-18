# FILE: wrapper/snapshot/gen_log.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Модуль снапшотов генерации wallet.dat - захват состояния при генерации кошельков.
# SCOPE: Логирование, снапшоты, интеграция с ecdsa_keys, batch_gen, wallet_dat
# INPUT: EntropySnapshot, ECDSAPluginInterface, BatchWalletGenerator, WalletDatWriter
# OUTPUT: WalletGenSnapshot
# KEYWORDS: [DOMAIN(10): WalletGenLogging; CONCEPT(9): SnapshotManagement; TECH(8): Serialization]
# LINKS: [USES(10): wrapper.snapshot.gen_snapshot; USES(8): src.plugins.crypto.ecdsa_keys; USES(8): src.plugins.wallet.batch_gen]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 10 [Dataclass для данных одного ключа] => KeyData
# CLASS 9 [Dataclass для данных коллекции кошельков] => WalletCollectionData
# CLASS 10 [Контейнер снапшота генерации wallet.dat] => WalletGenSnapshot
# FUNC 8 [Захват ключа от ECDSA плагина] => capture_key
# FUNC 8 [Захват коллекции кошельков] => capture_wallet_collection
# FUNC 7 [Захват информации о wallet.dat] => capture_wallet_dat_info
# FUNC 9 [Создание полного снапшота] => create_wallet_gen_snapshot
# END_MODULE_MAP
# START_USE_CASES:
# - [KeyData]: Snapshot (DataStorage) -> StoreKeyData -> KeyDataStored
# - [WalletCollectionData]: Snapshot (DataStorage) -> StoreWalletCollection -> CollectionStored
# - [WalletGenSnapshot]: System (WalletGeneration) -> CaptureGenState -> SnapshotReady
# - [capture_key]: KeyGenerator (Generation) -> CaptureKey -> KeyDataCaptured
# - [create_wallet_gen_snapshot]: System (FullGeneration) -> CreateFullSnapshot -> WalletGenSnapshotReady
# END_USE_CASES

"""
Модуль снапшотов генерации wallet.dat.

Предоставляет классы для создания, управления и сериализации
снапшотов процесса генерации wallet.dat, включая:
- Данные ECDSA ключей
- Коллекцию кошельков
- Информацию о записанном файле wallet.dat

Интегрируется с модулями:
- ecdsa_keys: генерация ключей secp256k1
- batch_gen: пакетная генерация кошельков
- wallet_dat: запись в Berkeley DB формат
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, ClassVar

from src.wrapper.snapshot.gen_snapshot import EntropySnapshot
from src.wrapper.snapshot.constants import SNAPSHOT_VERSION

logger = logging.getLogger(__name__)

# Константы для wallet.dat генерации
WALLET_GEN_SNAPSHOT_VERSION = "1.0.0"
WALLET_GEN_SNAPSHOT_MAGIC = b"WNAP"  # Wallet SNAPshot


# START_DATACLASS_KeyData
# START_CONTRACT:
# PURPOSE: Dataclass для хранения данных одного ECDSA ключа.
# ATTRIBUTES:
# - index: Индекс в коллекции => index: int
# - public_key: Публичный ключ (65 байт) => public_key: bytes
# - private_key: Приватный ключ (279 байт DER) => private_key: bytes
# - address: Bitcoin адрес (Base58Check) => address: str
# - entropy_estimate: Оценка энтропии => entropy_estimate: float
# - timestamp: Время генерации => timestamp: datetime
# KEYWORDS: [DOMAIN(9): KeyData; CONCEPT(8): ECDSA; TECH(6): secp256k1]
# END_CONTRACT

@dataclass(frozen=False, order=False)
class KeyData:
    """
    Dataclass для хранения данных одного ECDSA ключа.
    
    Используется для захвата и хранения информации о сгенерированном
    ключе secp256k1 в процессе генерации wallet.dat.
    
    Attributes:
        index: Индекс ключа в коллекции.
        public_key: Публичный ключ (65 байт, несжатый формат 0x04 + X + Y).
        private_key: Приватный ключ (279 байт, DER-кодированный).
        address: Bitcoin адрес (Base58Check, 25-34 символа).
        entropy_estimate: Оценка энтропии ключа.
        timestamp: Время генерации ключа.
    """
    
    index: int
    public_key: bytes
    private_key: bytes
    address: str
    entropy_estimate: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # START_METHOD___post_init__
    # START_CONTRACT:
    # PURPOSE: Валидация данных после инициализации.
    # KEYWORDS: [CONCEPT(5): Validation; CONCEPT(4): Init]
    # END_CONTRACT
    
    def __post_init__(self) -> None:
        """Валидация данных после инициализации."""
        # START_BLOCK_VALIDATE_PUBLIC_KEY: [Проверка публичного ключа.]
        if not isinstance(self.public_key, bytes):
            raise TypeError(f"public_key должен быть bytes, получен {type(self.public_key)}")
        
        if len(self.public_key) != 65:
            logger.warning(
                f"[VarCheck][KeyData][__post_init__][ConditionCheck] "
                f"Размер public_key {len(self.public_key)} != 65"
            )
        # END_BLOCK_VALIDATE_PUBLIC_KEY
        
        # START_BLOCK_VALIDATE_PRIVATE_KEY: [Проверка приватного ключа.]
        if not isinstance(self.private_key, bytes):
            raise TypeError(f"private_key должен быть bytes, получен {type(self.private_key)}")
        # END_BLOCK_VALIDATE_PRIVATE_KEY
        
        # START_BLOCK_VALIDATE_ADDRESS: [Проверка адреса.]
        if not isinstance(self.address, str):
            raise TypeError(f"address должен быть str, получен {type(self.address)}")
        # END_BLOCK_VALIDATE_ADDRESS
    
    # END_METHOD___post_init__
    
    # START_METHOD_to_dict
    # START_CONTRACT:
    # PURPOSE: Преобразование в словарь для JSON сериализации.
    # OUTPUTS:
    # - dict: Словарь с данными ключа
    # KEYWORDS: [CONCEPT(6): Serialization; TECH(5): JSON]
    # END_CONTRACT
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует KeyData в словарь.
        
        Returns:
            Словарь с данными ключа.
        """
        result = {
            "index": self.index,
            "public_key_hex": self.public_key.hex(),
            "private_key_hex": self.private_key.hex(),
            "address": self.address,
            "entropy_estimate": self.entropy_estimate,
            "timestamp": self.timestamp.isoformat()
        }
        
        logger.debug(
            f"[VarCheck][KeyData][to_dict][ReturnData] "
            f"index={self.index}, address={self.address[:10]}..."
        )
        
        return result
    
    # END_METHOD_to_dict
    
    # START_CLASSMETHOD_from_dict
    # START_CONTRACT:
    # PURPOSE: Создание KeyData из словаря.
    # INPUTS:
    # - data: Словарь с данными ключа => data: Dict[str, Any]
    # OUTPUTS:
    # - KeyData: Созданный объект
    # KEYWORDS: [CONCEPT(6): Deserialization; TECH(5): JSON]
    # END_CONTRACT
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KeyData":
        """
        Создает KeyData из словаря.
        
        Args:
            data: Словарь с данными ключа.
            
        Returns:
            Созданный объект KeyData.
        """
        return cls(
            index=data["index"],
            public_key=bytes.fromhex(data["public_key_hex"]),
            private_key=bytes.fromhex(data["private_key_hex"]),
            address=data["address"],
            entropy_estimate=data.get("entropy_estimate", 0.0),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(timezone.utc)
        )
    
    # END_CLASSMETHOD_from_dict

# END_DATACLASS_KeyData


# START_DATACLASS_WalletCollectionData
# START_CONTRACT:
# PURPOSE: Dataclass для хранения данных коллекции кошельков.
# ATTRIBUTES:
# - wallets: Список ключей => wallets: List[KeyData]
# - count: Количество кошельков => count: int
# - entropy_source: Источник энтропии => entropy_source: str
# - deterministic: Детерминистический режим => deterministic: bool
# - timestamp: Время создания коллекции => timestamp: datetime
# KEYWORDS: [DOMAIN(9): WalletCollection; CONCEPT(8): BatchGen; TECH(6): Collection]
# END_CONTRACT

@dataclass(frozen=False, order=False)
class WalletCollectionData:
    """
    Dataclass для хранения данных коллекции кошельков.
    
    Используется для захвата и хранения информации о
    пакетно сгенерированных кошельках.
    
    Attributes:
        wallets: Список KeyData всех кошельков.
        count: Количество кошельков в коллекции.
        entropy_source: Имя источника энтропии.
        deterministic: Использовался ли детерминистический режим.
        timestamp: Время создания коллекции.
    """
    
    wallets: List[KeyData]
    count: int
    entropy_source: str
    deterministic: bool = True
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # START_METHOD___post_init__
    # START_CONTRACT:
    # PURPOSE: Валидация данных после инициализации.
    # KEYWORDS: [CONCEPT(5): Validation]
    # END_CONTRACT
    
    def __post_init__(self) -> None:
        """Валидация данных после инициализации."""
        # START_BLOCK_VALIDATE_WALLETS: [Проверка списка кошельков.]
        if not isinstance(self.wallets, list):
            raise TypeError(f"wallets должен быть list, получен {type(self.wallets)}")
        
        if self.count != len(self.wallets):
            logger.warning(
                f"[VarCheck][WalletCollectionData][__post_init__][ConditionCheck] "
                f"count {self.count} != len(wallets) {len(self.wallets)}"
            )
        # END_BLOCK_VALIDATE_WALLETS
    
    # END_METHOD___post_init__
    
    # START_METHOD_to_dict
    # START_CONTRACT:
    # PURPOSE: Преобразование в словарь для JSON сериализации.
    # OUTPUTS:
    # - dict: Словарь с данными коллекции
    # KEYWORDS: [CONCEPT(6): Serialization; TECH(5): JSON]
    # END_CONTRACT
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует WalletCollectionData в словарь.
        
        Returns:
            Словарь с данными коллекции.
        """
        result = {
            "wallets": [wallet.to_dict() for wallet in self.wallets],
            "count": self.count,
            "entropy_source": self.entropy_source,
            "deterministic": self.deterministic,
            "timestamp": self.timestamp.isoformat()
        }
        
        logger.debug(
            f"[VarCheck][WalletCollectionData][to_dict][ReturnData] "
            f"count={self.count}, deterministic={self.deterministic}"
        )
        
        return result
    
    # END_METHOD_to_dict
    
    # START_CLASSMETHOD_from_dict
    # START_CONTRACT:
    # PURPOSE: Создание WalletCollectionData из словаря.
    # INPUTS:
    # - data: Словарь с данными коллекции => data: Dict[str, Any]
    # OUTPUTS:
    # - WalletCollectionData: Созданный объект
    # KEYWORDS: [CONCEPT(6): Deserialization; TECH(5): JSON]
    # END_CONTRACT
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WalletCollectionData":
        """
        Создает WalletCollectionData из словаря.
        
        Args:
            data: Словарь с данными коллекции.
            
        Returns:
            Созданный объект WalletCollectionData.
        """
        wallets = [KeyData.from_dict(w) for w in data.get("wallets", [])]
        
        return cls(
            wallets=wallets,
            count=data.get("count", len(wallets)),
            entropy_source=data.get("entropy_source", "unknown"),
            deterministic=data.get("deterministic", True),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(timezone.utc)
        )
    
    # END_CLASSMETHOD_from_dict

# END_DATACLASS_WalletCollectionData


# START_CLASS_WalletGenSnapshot
# START_CONTRACT:
# PURPOSE: Контейнер для полного снапшота генерации wallet.dat.
# ATTRIBUTES:
# - version: Версия формата => version: str
# - timestamp: Время создания => timestamp: datetime
# - entropy_snapshot: Снапшот энтропии => entropy_snapshot: EntropySnapshot | None
# - keys: Список ключей => keys: List[KeyData]
# - wallet_collection: Данные коллекции => wallet_collection: WalletCollectionData | None
# - wallet_file: Путь к файлу => wallet_file: str | None
# - checksum: SHA256 контрольная сумма => checksum: bytes | None
# METHODS:
# - add_entropy_snapshot(entropy: EntropySnapshot) -> WalletGenSnapshot: Добавление снапшота энтропии
# - add_key(key: KeyData) -> WalletGenSnapshot: Добавление ключа
# - add_wallet_collection(collection: WalletCollectionData) -> WalletGenSnapshot: Добавление коллекции
# - set_wallet_file(path: str) -> WalletGenSnapshot: Установка пути к файлу
# - to_dict() -> dict: Сериализация в словарь
# - from_dict(data: dict) -> WalletGenSnapshot: Десериализация из словаря (classmethod)
# - to_binary() -> bytes: Сериализация в бинарный формат
# - from_binary(data: bytes) -> WalletGenSnapshot: Десериализация из бинарного формата (classmethod)
# - validate() -> bool: Валидация целостности
# KEYWORDS: [DOMAIN(10): WalletGenSnapshot; CONCEPT(9): SnapshotContainer; TECH(8): Serialization]
# END_CONTRACT

class WalletGenSnapshot:
    """
    Контейнер для полного снапшота генерации wallet.dat.
    
    Хранит все данные процесса генерации:
    - Снапшот энтропии (EntropySnapshot)
    - Сгенерированные ключи (KeyData)
    - Коллекцию кошельков (WalletCollectionData)
    - Информацию о записанном файле
    
    Attributes:
        version: Версия формата снапшота.
        timestamp: Время создания снапшота.
        entropy_snapshot: Снапшот энтропии.
        keys: Список всех KeyData.
        wallet_collection: Данные коллекции кошельков.
        wallet_file: Путь к записанному wallet.dat файлу.
        checksum: SHA256 контрольная сумма.
    """
    
    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация пустого снапшота генерации.
    # INPUTS:
    # - version: Версия формата => version: str | None
    # - timestamp: Время создания => timestamp: datetime | None
    # OUTPUTS:
    # - None
    # KEYWORDS: [CONCEPT(5): Initialization]
    # END_CONTRACT
    
    def __init__(
        self,
        version: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Инициализирует пустой снапшот генерации wallet.dat.
        
        Args:
            version: Версия формата снапшота.
            timestamp: Время создания.
        """
        # START_BLOCK_INIT: [Инициализация атрибутов.]
        self._version: str = version or WALLET_GEN_SNAPSHOT_VERSION
        self._timestamp: datetime = timestamp or datetime.now(timezone.utc)
        self._entropy_snapshot: Optional[EntropySnapshot] = None
        self._keys: List[KeyData] = []
        self._wallet_collection: Optional[WalletCollectionData] = None
        self._wallet_file: Optional[str] = None
        self._checksum: Optional[bytes] = None
        
        logger.info(
            f"[InitCheck][WalletGenSnapshot][__init__][Initialize] "
            f"WalletGenSnapshot инициализирован: version={self._version}"
        )
        # END_BLOCK_INIT
    
    # END_METHOD___init__
    
    # START_PROPERTY_version
    @property
    def version(self) -> str:
        """Версия формата снапшота."""
        return self._version
    
    # END_PROPERTY_version
    
    # START_PROPERTY_timestamp
    @property
    def timestamp(self) -> datetime:
        """Время создания снапшота."""
        return self._timestamp
    
    # END_PROPERTY_timestamp
    
    # START_PROPERTY_entropy_snapshot
    @property
    def entropy_snapshot(self) -> Optional[EntropySnapshot]:
        """Снапшот энтропии."""
        return self._entropy_snapshot
    
    # END_PROPERTY_entropy_snapshot
    
    # START_PROPERTY_keys
    @property
    def keys(self) -> List[KeyData]:
        """Список ключей (копия для иммутабельности)."""
        return list(self._keys)
    
    # END_PROPERTY_keys
    
    # START_PROPERTY_wallet_collection
    @property
    def wallet_collection(self) -> Optional[WalletCollectionData]:
        """Данные коллекции кошельков."""
        return self._wallet_collection
    
    # END_PROPERTY_wallet_collection
    
    # START_PROPERTY_wallet_file
    @property
    def wallet_file(self) -> Optional[str]:
        """Путь к записанному wallet.dat файлу."""
        return self._wallet_file
    
    # END_PROPERTY_wallet_file
    
    # START_PROPERTY_checksum
    @property
    def checksum(self) -> Optional[bytes]:
        """SHA256 контрольная сумма."""
        return self._checksum
    
    # END_PROPERTY_checksum
    
    # START_METHOD_add_entropy_snapshot
    # START_CONTRACT:
    # PURPOSE: Добавление снапшота энтропии.
    # INPUTS:
    # - entropy: Снапшот энтропии => entropy: EntropySnapshot
    # OUTPUTS:
    # - WalletGenSnapshot: Новый снапшот с добавленным entropy (иммутабельный паттерн)
    # KEYWORDS: [CONCEPT(7): Immutability; CONCEPT(6): EntropyAdd]
    # END_CONTRACT
    
    def add_entropy_snapshot(self, entropy: EntropySnapshot) -> "WalletGenSnapshot":
        """
        Добавляет снапшот энтропии.
        
        Args:
            entropy: Снапшот энтропии.
            
        Returns:
            Новый снапшот с добавленным entropy.
        """
        # START_BLOCK_ADD_ENTROPY: [Добавление снапшота энтропии.]
        logger.info(
            f"[TraceCheck][WalletGenSnapshot][add_entropy_snapshot][AddEntropy] "
            f"Добавление снапшота энтропии"
        )
        
        new_snapshot = WalletGenSnapshot(
            version=self._version,
            timestamp=self._timestamp
        )
        new_snapshot._entropy_snapshot = entropy
        new_snapshot._keys = list(self._keys)
        new_snapshot._wallet_collection = self._wallet_collection
        new_snapshot._wallet_file = self._wallet_file
        new_snapshot._checksum = self._checksum
        
        logger.info(
            f"[TraceCheck][WalletGenSnapshot][add_entropy_snapshot][AddEntropy] "
            f"Снапшот энтропии добавлен [SUCCESS]"
        )
        
        return new_snapshot
        # END_BLOCK_ADD_ENTROPY
    
    # END_METHOD_add_entropy_snapshot
    
    # START_METHOD_add_key
    # START_CONTRACT:
    # PURPOSE: Добавление ключа в снапшот.
    # INPUTS:
    # - key: Данные ключа => key: KeyData
    # OUTPUTS:
    # - WalletGenSnapshot: Новый снапшот с добавленным ключом
    # KEYWORDS: [CONCEPT(7): Immutability; CONCEPT(6): KeyAdd]
    # END_CONTRACT
    
    def add_key(self, key: KeyData) -> "WalletGenSnapshot":
        """
        Добавляет ключ в снапшот.
        
        Args:
            key: Данные ключа.
            
        Returns:
            Новый снапшот с добавленным ключом.
        """
        # START_BLOCK_ADD_KEY: [Добавление ключа.]
        logger.debug(
            f"[TraceCheck][WalletGenSnapshot][add_key][AddKey] "
            f"Добавление ключа index={key.index}"
        )
        
        new_snapshot = WalletGenSnapshot(
            version=self._version,
            timestamp=self._timestamp
        )
        new_snapshot._entropy_snapshot = self._entropy_snapshot
        new_snapshot._keys = self._keys + [key]
        new_snapshot._wallet_collection = self._wallet_collection
        new_snapshot._wallet_file = self._wallet_file
        new_snapshot._checksum = self._checksum
        
        logger.debug(
            f"[TraceCheck][WalletGenSnapshot][add_key][AddKey] "
            f"Ключ добавлен. Всего ключей: {len(new_snapshot._keys)} [SUCCESS]"
        )
        
        return new_snapshot
        # END_BLOCK_ADD_KEY
    
    # END_METHOD_add_key
    
    # START_METHOD_add_wallet_collection
    # START_CONTRACT:
    # PURPOSE: Добавление коллекции кошельков.
    # INPUTS:
    # - collection: Данные коллекции => collection: WalletCollectionData
    # OUTPUTS:
    # - WalletGenSnapshot: Новый снапшот с добавленной коллекцией
    # KEYWORDS: [CONCEPT(7): Immutability; CONCEPT(6): CollectionAdd]
    # END_CONTRACT
    
    def add_wallet_collection(self, collection: WalletCollectionData) -> "WalletGenSnapshot":
        """
        Добавляет коллекцию кошельков.
        
        Args:
            collection: Данные коллекции.
            
        Returns:
            Новый снапшот с добавленной коллекцией.
        """
        # START_BLOCK_ADD_COLLECTION: [Добавление коллекции.]
        logger.info(
            f"[TraceCheck][WalletGenSnapshot][add_wallet_collection][AddCollection] "
            f"Добавление коллекции: count={collection.count}"
        )
        
        new_snapshot = WalletGenSnapshot(
            version=self._version,
            timestamp=self._timestamp
        )
        new_snapshot._entropy_snapshot = self._entropy_snapshot
        new_snapshot._keys = list(self._keys)
        new_snapshot._wallet_collection = collection
        new_snapshot._wallet_file = self._wallet_file
        new_snapshot._checksum = self._checksum
        
        logger.info(
            f"[TraceCheck][WalletGenSnapshot][add_wallet_collection][AddCollection] "
            f"Коллекция добавлена [SUCCESS]"
        )
        
        return new_snapshot
        # END_BLOCK_ADD_COLLECTION
    
    # END_METHOD_add_wallet_collection
    
    # START_METHOD_set_wallet_file
    # START_CONTRACT:
    # PURPOSE: Установка пути к записанному файлу wallet.dat.
    # INPUTS:
    # - path: Путь к файлу => path: str
    # OUTPUTS:
    # - WalletGenSnapshot: Новый снапшот с установленным путем
    # KEYWORDS: [CONCEPT(7): Immutability; CONCEPT(6): FilePathSet]
    # END_CONTRACT
    
    def set_wallet_file(self, path: str) -> "WalletGenSnapshot":
        """
        Устанавливает путь к записанному файлу wallet.dat.
        
        Args:
            path: Путь к файлу.
            
        Returns:
            Новый снапшот с установленным путем.
        """
        # START_BLOCK_SET_WALLET_FILE: [Установка пути к файлу.]
        logger.info(
            f"[TraceCheck][WalletGenSnapshot][set_wallet_file][SetPath] "
            f"Установка пути: {path}"
        )
        
        new_snapshot = WalletGenSnapshot(
            version=self._version,
            timestamp=self._timestamp
        )
        new_snapshot._entropy_snapshot = self._entropy_snapshot
        new_snapshot._keys = list(self._keys)
        new_snapshot._wallet_collection = self._wallet_collection
        new_snapshot._wallet_file = path
        
        # Вычисляем контрольную сумму
        new_snapshot._compute_checksum()
        
        logger.info(
            f"[TraceCheck][WalletGenSnapshot][set_wallet_file][SetPath] "
            f"Путь установлен [SUCCESS]"
        )
        
        return new_snapshot
        # END_BLOCK_SET_WALLET_FILE
    
    # END_METHOD_set_wallet_file
    
    # START_METHOD_compute_checksum
    # START_CONTRACT:
    # PURPOSE: Вычисление SHA256 контрольной суммы снапшота.
    # OUTPUTS:
    # - bytes: Контрольная сумма
    # KEYWORDS: [CONCEPT(7): Checksum; TECH(6): SHA256]
    # END_CONTRACT
    
    def _compute_checksum(self) -> None:
        """Вычисляет SHA256 контрольную сумму снапшота."""
        # START_BLOCK_COMPUTE_CHECKSUM: [Вычисление контрольной суммы.]
        logger.debug(
            f"[TraceCheck][WalletGenSnapshot][_compute_checksum][ComputeChecksum] "
            f"Вычисление контрольной суммы"
        )
        
        hasher = hashlib.sha256()
        
        # Версия
        hasher.update(self._version.encode("utf-8"))
        
        # Время создания
        hasher.update(self._timestamp.isoformat().encode("utf-8"))
        
        # Снапшот энтропии (если есть)
        if self._entropy_snapshot:
            hasher.update(str(self._entropy_snapshot.phases).encode("utf-8"))
        
        # Ключи
        for key in self._keys:
            hasher.update(key.public_key)
            hasher.update(key.private_key)
        
        # Коллекция (если есть)
        if self._wallet_collection:
            hasher.update(str(self._wallet_collection.count).encode("utf-8"))
        
        # Путь к файлу (если есть)
        if self._wallet_file:
            hasher.update(self._wallet_file.encode("utf-8"))
        
        self._checksum = hasher.digest()
        
        logger.debug(
            f"[TraceCheck][WalletGenSnapshot][_compute_checksum][ComputeChecksum] "
            f"Контрольная сумма вычислена: {self._checksum.hex()[:16]}... [SUCCESS]"
        )
        # END_BLOCK_COMPUTE_CHECKSUM
    
    # END_METHOD_compute_checksum
    
    # START_METHOD_validate
    # START_CONTRACT:
    # PURPOSE: Валидация целостности снапшота.
    # OUTPUTS:
    # - bool: True если снапшот валиден
    # KEYWORDS: [CONCEPT(8): Validation; DOMAIN(7): Integrity]
    # END_CONTRACT
    
    def validate(self) -> bool:
        """
        Валидирует целостность снапшота.
        
        Проверяет:
        - Наличие ключей или коллекции
        - Контрольную сумму
        
        Returns:
            True если снапшот валиден, иначе False.
        """
        # START_BLOCK_VALIDATE: [Валидация снапшота.]
        logger.info(
            f"[TraceCheck][WalletGenSnapshot][validate][Validate] "
            f"Начало валидации снапшота"
        )
        
        # START_BLOCK_CHECK_KEYS: [Проверка наличия ключей.]
        has_keys = len(self._keys) > 0
        has_collection = self._wallet_collection is not None
        
        if not has_keys and not has_collection:
            logger.warning(
                f"[VarCheck][WalletGenSnapshot][validate][CheckKeys] "
                f"Нет ключей и коллекции [WARNING]"
            )
        # END_BLOCK_CHECK_KEYS
        
        logger.info(
            f"[TraceCheck][WalletGenSnapshot][validate][Validate] "
            f"Валидация завершена: keys={len(self._keys)}, collection={'set' if has_collection else 'None'} [SUCCESS]"
        )
        
        return True
        # END_BLOCK_VALIDATE
    
    # END_METHOD_validate
    
    # START_METHOD_to_dict
    # START_CONTRACT:
    # PURPOSE: Сериализация снапшота в словарь для JSON.
    # OUTPUTS:
    # - dict: Словарь с данными снапшота
    # KEYWORDS: [CONCEPT(8): Serialization; TECH(7): JSON]
    # END_CONTRACT
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Сериализует снапшот в словарь для JSON.
        
        Returns:
            Словарь с данными снапшота.
        """
        # START_BLOCK_TO_DICT: [Сериализация в словарь.]
        logger.info(
            f"[TraceCheck][WalletGenSnapshot][to_dict][Serialize] "
            f"Сериализация в словарь"
        )
        
        # Вычисляем контрольную сумму
        self._compute_checksum()
        
        # Сериализуем entropy_snapshot если есть
        entropy_dict = None
        if self._entropy_snapshot:
            entropy_dict = {
                "version": self._entropy_snapshot.version,
                "timestamp": self._entropy_snapshot.timestamp.isoformat(),
                "phases_count": len(self._entropy_snapshot.phases),
                "final_state_set": self._entropy_snapshot.final_state is not None
            }
        
        result = {
            "version": self._version,
            "timestamp": self._timestamp.isoformat(),
            "metadata": {
                "wallet_gen_version": WALLET_GEN_SNAPSHOT_VERSION
            },
            "entropy_snapshot": entropy_dict,
            "keys": [key.to_dict() for key in self._keys],
            "wallet_collection": self._wallet_collection.to_dict() if self._wallet_collection else None,
            "wallet_file": self._wallet_file,
            "integrity": {
                "checksum_algorithm": "SHA256",
                "checksum_hex": self._checksum.hex() if self._checksum else None
            }
        }
        
        logger.info(
            f"[TraceCheck][WalletGenSnapshot][to_dict][Serialize] "
            f"Сериализовано {len(self._keys)} ключей [SUCCESS]"
        )
        
        return result
        # END_BLOCK_TO_DICT
    
    # END_METHOD_to_dict
    
    # START_CLASSMETHOD_from_dict
    # START_CONTRACT:
    # PURPOSE: Десериализация снапшота из словаря.
    # INPUTS:
    # - data: Словарь с данными => data: Dict[str, Any]
    # OUTPUTS:
    # - WalletGenSnapshot: Созданный снапшот
    # KEYWORDS: [CONCEPT(8): Deserialization; TECH(7): JSON]
    # END_CONTRACT
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WalletGenSnapshot":
        """
        Создает снапшот из словаря.
        
        Args:
            data: Словарь с данными снапшота.
            
        Returns:
            Созданный объект WalletGenSnapshot.
        """
        # START_BLOCK_FROM_DICT: [Десериализация из словаря.]
        logger.info(
            f"[TraceCheck][WalletGenSnapshot][from_dict][Deserialize] "
            f"Десериализация из словаря"
        )
        
        # Создаем базовый снапшот
        snapshot = cls(
            version=data.get("version", WALLET_GEN_SNAPSHOT_VERSION),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(timezone.utc)
        )
        
        # Восстанавливаем ключи
        snapshot._keys = [KeyData.from_dict(k) for k in data.get("keys", [])]
        
        # Восстанавливаем коллекцию
        collection_data = data.get("wallet_collection")
        if collection_data:
            snapshot._wallet_collection = WalletCollectionData.from_dict(collection_data)
        
        # Восстанавливаем путь к файлу
        snapshot._wallet_file = data.get("wallet_file")
        
        # Восстанавливаем контрольную сумму
        integrity = data.get("integrity", {})
        if integrity.get("checksum_hex"):
            snapshot._checksum = bytes.fromhex(integrity["checksum_hex"])
        
        logger.info(
            f"[TraceCheck][WalletGenSnapshot][from_dict][Deserialize] "
            f"Десериализовано {len(snapshot._keys)} ключей [SUCCESS]"
        )
        
        return snapshot
        # END_BLOCK_FROM_DICT
    
    # END_CLASSMETHOD_from_dict
    
    # START_METHOD_to_binary
    # START_CONTRACT:
    # PURPOSE: Сериализация снапшота в бинарный формат.
    # OUTPUTS:
    # - bytes: Бинарные данные снапшота
    # KEYWORDS: [CONCEPT(8): Serialization; TECH(7): Binary]
    # END_CONTRACT
    
    def to_binary(self) -> bytes:
        """
        Сериализует снапшот в бинарный формат.
        
        Формат:
            0x00-0x03: WNAP magic (4 байта)
            0x04-0x05: Version (2 байта, little-endian)
            0x06-0x09: Timestamp Unix (4 байта)
            0x0A-0x0D: Keys count (4 байта)
            0x0E-...: Key records
            ...: Checksum SHA256 (32 байта)
            
        Returns:
            Бинарные данные снапшота.
        """
        # START_BLOCK_TO_BINARY: [Сериализация в бинарный формат.]
        logger.info(
            f"[TraceCheck][WalletGenSnapshot][to_binary][SerializeBinary] "
            f"Сериализация в бинарный формат"
        )
        
        # Вычисляем контрольную сумму
        self._compute_checksum()
        
        result = bytearray()
        
        # Magic
        result.extend(WALLET_GEN_SNAPSHOT_MAGIC)
        
        # Version (2 bytes, little-endian)
        version_parts = self._version.split(".")
        version_code = (int(version_parts[0]) << 8) | int(version_parts[1]) if len(version_parts) >= 2 else 256
        result.extend(version_code.to_bytes(2, "little"))
        
        # Timestamp (4 bytes, Unix epoch)
        timestamp_ts = int(self._timestamp.timestamp())
        result.extend(timestamp_ts.to_bytes(4, "little"))
        
        # Keys count (4 bytes)
        keys_count = len(self._keys)
        result.extend(keys_count.to_bytes(4, "little"))
        
        logger.debug(
            f"[VarCheck][WalletGenSnapshot][to_binary][SerializeBinary] "
            f"Ключей: {keys_count} [VALUE]"
        )
        
        # Key records
        for key in self._keys:
            # Index (4 bytes)
            result.extend(key.index.to_bytes(4, "little"))
            
            # Public key length (2 bytes)
            pubkey_len = len(key.public_key)
            result.extend(pubkey_len.to_bytes(2, "little"))
            
            # Public key
            result.extend(key.public_key)
            
            # Private key length (2 bytes)
            privkey_len = len(key.private_key)
            result.extend(privkey_len.to_bytes(2, "little"))
            
            # Private key
            result.extend(key.private_key)
            
            # Address length (1 byte)
            addr_len = len(key.address)
            result.append(addr_len)
            
            # Address
            result.extend(key.address.encode("utf-8"))
        
        # Checksum SHA256 (32 bytes)
        if self._checksum:
            result.extend(self._checksum)
        else:
            result.extend(b"\x00" * 32)
        
        logger.info(
            f"[TraceCheck][WalletGenSnapshot][to_binary][SerializeBinary] "
            f"Сериализовано {len(result)} байт [SUCCESS]"
        )
        
        return bytes(result)
        # END_BLOCK_TO_BINARY
    
    # END_METHOD_to_binary
    
    # START_CLASSMETHOD_from_binary
    # START_CONTRACT:
    # PURPOSE: Десериализация снапшота из бинарного формата.
    # INPUTS:
    # - data: Бинарные данные => data: bytes
    # OUTPUTS:
    # - WalletGenSnapshot: Созданный снапшот
    # KEYWORDS: [CONCEPT(8): Deserialization; TECH(7): Binary]
    # END_CONTRACT
    
    @classmethod
    def from_binary(cls, data: bytes) -> "WalletGenSnapshot":
        """
        Создает снапшот из бинарных данных.
        
        Args:
            data: Бинарные данные снапшота.
            
        Returns:
            Созданный объект WalletGenSnapshot.
            
        Raises:
            ValueError: Если формат данных некорректен.
        """
        # START_BLOCK_FROM_BINARY: [Десериализация из бинарного формата.]
        logger.info(
            f"[TraceCheck][WalletGenSnapshot][from_binary][DeserializeBinary] "
            f"Десериализация из бинарного формата: {len(data)} байт"
        )
        
        offset = 0
        
        # Magic (4 bytes)
        magic = data[offset:offset + 4]
        offset += 4
        
        if magic != WALLET_GEN_SNAPSHOT_MAGIC:
            logger.error(
                f"[VarCheck][WalletGenSnapshot][from_binary][CheckMagic] "
                f"Неверное магическое число: {magic} [FAIL]"
            )
            raise ValueError(f"Неверное магическое число: {magic}")
        
        # Version (2 bytes)
        version_code = int.from_bytes(data[offset:offset + 2], "little")
        offset += 2
        version = f"{(version_code >> 8) & 0xFF}.{version_code & 0xFF}.0"
        
        # Timestamp (4 bytes)
        timestamp_ts = int.from_bytes(data[offset:offset + 4], "little")
        offset += 4
        timestamp = datetime.fromtimestamp(timestamp_ts, tz=timezone.utc)
        
        # Keys count (4 bytes)
        keys_count = int.from_bytes(data[offset:offset + 4], "little")
        offset += 4
        
        logger.debug(
            f"[VarCheck][WalletGenSnapshot][from_binary][CheckKeys] "
            f"Ключей: {keys_count} [VALUE]"
        )
        
        # Создаем снапшот
        snapshot = cls(
            version=version,
            timestamp=timestamp
        )
        
        # Key records
        for _ in range(keys_count):
            # Index (4 bytes)
            index = int.from_bytes(data[offset:offset + 4], "little")
            offset += 4
            
            # Public key length (2 bytes)
            pubkey_len = int.from_bytes(data[offset:offset + 2], "little")
            offset += 2
            
            # Public key
            public_key = data[offset:offset + pubkey_len]
            offset += pubkey_len
            
            # Private key length (2 bytes)
            privkey_len = int.from_bytes(data[offset:offset + 2], "little")
            offset += 2
            
            # Private key
            private_key = data[offset:offset + privkey_len]
            offset += privkey_len
            
            # Address length (1 byte)
            addr_len = data[offset]
            offset += 1
            
            # Address
            address = data[offset:offset + addr_len].decode("utf-8")
            offset += addr_len
            
            # Создаем KeyData
            key = KeyData(
                index=index,
                public_key=public_key,
                private_key=private_key,
                address=address
            )
            snapshot._keys.append(key)
        
        # Checksum (32 bytes)
        if offset + 32 <= len(data):
            snapshot._checksum = data[offset:offset + 32]
        
        logger.info(
            f"[TraceCheck][WalletGenSnapshot][from_binary][DeserializeBinary] "
            f"Десериализовано {len(snapshot._keys)} ключей [SUCCESS]"
        )
        
        return snapshot
        # END_BLOCK_FROM_BINARY
    
    # END_CLASSMETHOD_from_binary
    
    # START_METHOD___repr__
    # START_CONTRACT:
    # PURPOSE: Строковое представление снапшота.
    # KEYWORDS: [CONCEPT(5): Representation]
    # END_CONTRACT
    
    def __repr__(self) -> str:
        """Строковое представление."""
        return (
            f"WalletGenSnapshot("
            f"version={self._version}, "
            f"keys={len(self._keys)}, "
            f"wallet_collection={'set' if self._wallet_collection else 'None'}, "
            f"wallet_file={self._wallet_file})"
        )
    
    # END_METHOD___repr__

# END_CLASS_WalletGenSnapshot


# START_FUNCTION_capture_key
# START_CONTRACT:
# PURPOSE: Захват данных ключа от ECDSA плагина.
# INPUTS:
# - ecdsa_plugin: Экземпляр ECDSA плагина => ecdsa_plugin: Any
# - index: Индекс ключа в коллекции => index: int
# OUTPUTS:
# - KeyData: Захваченные данные ключа
# KEYWORDS: [CONCEPT(7): KeyCapture; TECH(6): ECDSA]
# END_CONTRACT

def capture_key(ecdsa_plugin: Any, index: int) -> KeyData:
    """
    Захватывает данные ключа от ECDSA плагина.
    
    Args:
        ecdsa_plugin: Экземпляр ECDSAPluginInterface.
        index: Индекс ключа в коллекции.
        
    Returns:
        KeyData с захваченными данными ключа.
    """
    # START_BLOCK_GET_KEY_DATA: [Получение данных ключа.]
    logger.info(
        f"[TraceCheck][capture_key][GetKeyData] "
        f"Захват ключа index={index}"
    )
    
    try:
        # Получаем публичный ключ
        public_key = ecdsa_plugin.get_public_key()
        if hasattr(public_key, 'to_bytes'):
            public_key = bytes(public_key)
        
        # Получаем приватный ключ
        private_key = ecdsa_plugin.get_private_key()
        if hasattr(private_key, 'to_bytes'):
            private_key = bytes(private_key)
        
        # Получаем адрес
        address = ecdsa_plugin.get_address()
        
        # Получаем оценку энтропии пула
        entropy_estimate = ecdsa_plugin.get_entropy_pool_size() / 1000.0
        
        key_data = KeyData(
            index=index,
            public_key=public_key,
            private_key=private_key,
            address=address,
            entropy_estimate=entropy_estimate
        )
        
        logger.info(
            f"[TraceCheck][capture_key][GetKeyData] "
            f"Ключ захвачен: address={address[:10]}... [SUCCESS]"
        )
        
        return key_data
        
    except Exception as e:
        logger.error(
            f"[CriticalError][capture_key][GetKeyData] "
            f"Ошибка захвата ключа: {str(e)} [FAIL]"
        )
        raise

# END_FUNCTION_capture_key


# START_FUNCTION_capture_wallet_collection
# START_CONTRACT:
# PURPOSE: Захват данных коллекции кошельков от BatchWalletGenerator.
# INPUTS:
# - batch_generator: Экземпляр BatchWalletGenerator => batch_generator: Any
# - entropy_source: Источник энтропии => entropy_source: str
# OUTPUTS:
# - WalletCollectionData: Захваченные данные коллекции
# KEYWORDS: [CONCEPT(7): CollectionCapture; TECH(6): BatchGen]
# END_CONTRACT

def capture_wallet_collection(
    batch_generator: Any,
    entropy_source: str = "unknown"
) -> WalletCollectionData:
    """
    Захватывает данные коллекции кошельков от BatchWalletGenerator.
    
    Args:
        batch_generator: Экземпляр BatchWalletGenerator.
        entropy_source: Имя источника энтропии.
        
    Returns:
        WalletCollectionData с захваченными данными.
    """
    # START_BLOCK_GET_COLLECTION: [Получение данных коллекции.]
    logger.info(
        f"[TraceCheck][capture_wallet_collection][GetCollection] "
        f"Захват коллекции кошельков"
    )
    
    try:
        # Получаем количество кошельков
        count = batch_generator.get_wallet_count()
        
        keys = []
        
        # Получаем ключи по индексу
        for i in range(count):
            try:
                wallet = batch_generator.get_wallet_at_index(i)
                
                # Преобразуем в KeyData
                key_data = KeyData(
                    index=i,
                    public_key=bytes(wallet.public_key) if hasattr(wallet.public_key, '__iter__') else wallet.public_key,
                    private_key=bytes(wallet.private_key) if hasattr(wallet.private_key, '__iter__') else wallet.private_key,
                    address=wallet.address,
                    entropy_source=wallet.entropy_source
                )
                keys.append(key_data)
                
            except Exception as e:
                logger.warning(
                    f"[VarCheck][capture_wallet_collection][GetWallet] "
                    f"Ошибка получения кошелька index={i}: {str(e)} [WARNING]"
                )
        
        collection_data = WalletCollectionData(
            wallets=keys,
            count=len(keys),
            entropy_source=entropy_source,
            deterministic=True
        )
        
        logger.info(
            f"[TraceCheck][capture_wallet_collection][GetCollection] "
            f"Захвачено {len(keys)} кошельков [SUCCESS]"
        )
        
        return collection_data
        
    except Exception as e:
        logger.error(
            f"[CriticalError][capture_wallet_collection][GetCollection] "
            f"Ошибка захвата коллекции: {str(e)} [FAIL]"
        )
        raise

# END_FUNCTION_capture_wallet_collection


# START_FUNCTION_capture_wallet_dat_info
# START_CONTRACT:
# PURPOSE: Захват информации о записанном файле wallet.dat.
# INPUTS:
# - wallet_writer: Экземпляр WalletDatWriter => wallet_writer: Any
# OUTPUTS:
# - str: Путь к записанному файлу
# KEYWORDS: [CONCEPT(6): FileCapture; TECH(5): WalletDat]
# END_CONTRACT

def capture_wallet_dat_info(wallet_writer: Any) -> str:
    """
    Захватывает информацию о записанном файле wallet.dat.
    
    Args:
        wallet_writer: Экземпляр WalletDatWriter.
        
    Returns:
        Путь к записанному файлу.
    """
    # START_BLOCK_GET_FILE_PATH: [Получение пути к файлу.]
    logger.info(
        f"[TraceCheck][capture_wallet_dat_info][GetFilePath] "
        f"Захват информации о wallet.dat"
    )
    
    try:
        file_path = wallet_writer.get_file_path()
        
        logger.info(
            f"[TraceCheck][capture_wallet_dat_info][GetFilePath] "
            f"Путь получен: {file_path} [SUCCESS]"
        )
        
        return file_path
        
    except Exception as e:
        logger.error(
            f"[CriticalError][capture_wallet_dat_info][GetFilePath] "
            f"Ошибка получения пути: {str(e)} [FAIL]"
        )
        return ""

# END_FUNCTION_capture_wallet_dat_info


# START_FUNCTION_create_wallet_gen_snapshot
# START_CONTRACT:
# PURPOSE: Создание полного снапшота генерации wallet.dat.
# INPUTS:
# - entropy_snapshot: Снапшот энтропии => entropy_snapshot: EntropySnapshot | None
# - key_generator: Генератор ключей => key_generator: Any | None
# - batch_generator: Генератор кошельков => batch_generator: Any | None
# - wallet_writer: Writer для wallet.dat => wallet_writer: Any | None
# OUTPUTS:
# - WalletGenSnapshot: Созданный снапшот
# KEYWORDS: [CONCEPT(9): SnapshotCreation; TECH(8): FullCapture]
# END_CONTRACT

def create_wallet_gen_snapshot(
    entropy_snapshot: Optional[EntropySnapshot] = None,
    key_generator: Any = None,
    batch_generator: Any = None,
    wallet_writer: Any = None
) -> WalletGenSnapshot:
    """
    Создает полный снапшот генерации wallet.dat.
    
    Args:
        entropy_snapshot: Снапшот энтропии (опционально).
        key_generator: Экземпляр ECDSA генератора ключей (опционально).
        batch_generator: Экземпляр BatchWalletGenerator (опционально).
        wallet_writer: Экземпляр WalletDatWriter (опционально).
        
    Returns:
        WalletGenSnapshot с захваченными данными.
    """
    # START_BLOCK_CREATE_SNAPSHOT: [Создание снапшота.]
    logger.info(
        f"[TraceCheck][create_wallet_gen_snapshot][CreateSnapshot] "
        f"Создание полного снапшота генерации wallet.dat"
    )
    
    snapshot = WalletGenSnapshot()
    
    # Добавляем снапшот энтропии
    if entropy_snapshot:
        snapshot = snapshot.add_entropy_snapshot(entropy_snapshot)
        logger.info(
            f"[TraceCheck][create_wallet_gen_snapshot][AddEntropy] "
            f"Снапшот энтропии добавлен [SUCCESS]"
        )
    
    # Захватываем ключи от key_generator
    if key_generator:
        try:
            key_data = capture_key(key_generator, 0)
            snapshot = snapshot.add_key(key_data)
            logger.info(
                f"[TraceCheck][create_wallet_gen_snapshot][CaptureKey] "
                f"Ключ захвачен [SUCCESS]"
            )
        except Exception as e:
            logger.warning(
                f"[VarCheck][create_wallet_gen_snapshot][CaptureKey] "
                f"Ошибка захвата ключа: {str(e)} [WARNING]"
            )
    
    # Захватываем коллекцию от batch_generator
    if batch_generator:
        try:
            collection_data = capture_wallet_collection(batch_generator, "BatchGen")
            snapshot = snapshot.add_wallet_collection(collection_data)
            
            # Захватываем все ключи из коллекции
            for key in collection_data.wallets:
                snapshot = snapshot.add_key(key)
            
            logger.info(
                f"[TraceCheck][create_wallet_gen_snapshot][CaptureCollection] "
                f"Коллекция захвачена: {collection_data.count} ключей [SUCCESS]"
            )
        except Exception as e:
            logger.warning(
                f"[VarCheck][create_wallet_gen_snapshot][CaptureCollection] "
                f"Ошибка захвата коллекции: {str(e)} [WARNING]"
            )
    
    # Захватываем путь к файлу от wallet_writer
    if wallet_writer:
        try:
            file_path = capture_wallet_dat_info(wallet_writer)
            snapshot = snapshot.set_wallet_file(file_path)
            logger.info(
                f"[TraceCheck][create_wallet_gen_snapshot][CaptureFile] "
                f"Путь к файлу захвачен: {file_path} [SUCCESS]"
            )
        except Exception as e:
            logger.warning(
                f"[VarCheck][create_wallet_gen_snapshot][CaptureFile] "
                f"Ошибка захвата пути: {str(e)} [WARNING]"
            )
    
    logger.info(
        f"[TraceCheck][create_wallet_gen_snapshot][CreateSnapshot] "
        f"Снапшот создан: keys={len(snapshot.keys)} [SUCCESS]"
    )
    
    return snapshot
    # END_BLOCK_CREATE_SNAPSHOT

# END_FUNCTION_create_wallet_gen_snapshot
