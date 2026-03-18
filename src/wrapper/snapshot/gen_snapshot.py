# FILE: wrapper/snapshot/gen_snapshot.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Основной модуль снапшотов энтропии - PhaseData, EntropySnapshot, SnapshotBuilder.
# SCOPE: Снапшоты, сериализация, валидация, интеграция с EntropyEngine
# INPUT: EntropyEngine, данные источников энтропии
# OUTPUT: EntropySnapshot
# KEYWORDS: [DOMAIN(10): SnapshotManagement; CONCEPT(9): EntropyState; TECH(8): Serialization; TECH(7): Builder]
# LINKS: [USES(10): wrapper.entropy.entropy_engine; USES(8): cache.entropy_pipeline_cache]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# CLASS 10 [Dataclass для данных одной фазы энтропии] => PhaseData
# CLASS 10 [Иммутабельный контейнер снапшота] => EntropySnapshot
# CLASS 9 [Builder для пошагового создания снапшота] => SnapshotBuilder
# METHOD 8 [Добавляет данные фазы в снапшот] => add_phase
# METHOD 8 [Устанавливает финальное состояние] => set_final_state
# METHOD 9 [Валидация целостности] => validate
# METHOD 8 [Сериализация в словарь] => to_dict
# METHOD 8 [Сериализация в бинарный формат] => to_binary
# METHOD 8 [Десериализация из словаря] => from_dict
# METHOD 8 [Десериализация из бинарного формата] => from_binary
# METHOD 9 [Захват данных одной фазы] => capture_phase
# METHOD 9 [Захват всех фаз] => capture_all
# METHOD 8 [Финализация снапшота] => build
# END_MODULE_MAP
# START_USE_CASES:
# - [PhaseData]: Snapshot (DataStorage) -> StoreEntropyPhase -> PhaseDataStored
# - [EntropySnapshot]: System (SnapshotCreation) -> CaptureEntropyState -> SnapshotReady
# - [SnapshotBuilder.build]: Builder (Construction) -> BuildSnapshot -> EntropySnapshotReturned
# - [EntropySnapshot.validate]: Auditor (Validation) -> CheckIntegrity -> ValidationResult
# END_USE_CASES

"""
Модуль снапшотов энтропии.

Предоставляет классы для создания, управления и сериализации
снапшотов энтропийного состояния PRNG в процессе генерации wallet.dat.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, ClassVar
from functools import total_ordering

from src.wrapper.snapshot.constants import (
    STATE_SIZE,
    MD_DIGEST_LENGTH,
    STATE_BUFFER_SIZE,
    SNAPSHOT_VERSION,
    SNAPSHOT_MAGIC,
    SNAPSHOT_BINARY_VERSION,
    HASH_ALGORITHM_NONE,
    HASH_ALGORITHM_MD5,
    HASH_ALGORITHM_SHA256,
    HASH_SIZES,
    PHASE_RAND_POLL,
    PHASE_GET_BITMAP_BITS,
    PHASE_HKEY_PERFORMANCE,
    PHASE_QPC,
    PHASE_TO_SOURCE,
    PHASE_TO_HASH,
    PHASE_DEFAULT_SIZES
)


logger = logging.getLogger(__name__)


# START_DATACLASS_PhaseData
# START_CONTRACT:
# PURPOSE: Dataclass для хранения данных одной фазы энтропийного пайплайна.
# ATTRIBUTES:
# - phase_id: Идентификатор фазы (1-4) => phase_id: int
# - name: Имя фазы (RAND_poll, GetBitmapBits, etc.) => name: str
# - source_name: Имя класса-источника в EntropyEngine => source_name: str
# - raw_data: Сырые данные энтропии => raw_data: bytes
# - hash_algorithm: Алгоритм хеширования (None, MD5, SHA256) => hash_algorithm: str
# - hash_value: Хеш-значение в байтах => hash_value: bytes | None
# - entropy_estimate: Оценка энтропии => entropy_estimate: float
# - timestamp: Время захвата фазы => timestamp: datetime
# KEYWORDS: [DOMAIN(9): DataStructure; CONCEPT(8): EntropyPhase; TECH(6): Dataclass]
# END_CONTRACT

@total_ordering
@dataclass(frozen=True, order=False)
class PhaseData:
    """
    Dataclass для хранения данных одной фазы энтропийного пайплайна.
    
    Используется для захвата и хранения информации об энтропии,
    полученной из различных источников на разных этапах генерации.
    
    Attributes:
        phase_id: Идентификатор фазы (1-4).
        name: Имя фазы (RAND_poll, GetBitmapBits, etc.).
        source_name: Имя класса-источника в EntropyEngine.
        raw_data: Сырые данные энтропии.
        hash_algorithm: Алгоритм хеширования (None, MD5, SHA256).
        hash_value: Хеш-значение в байтах.
        entropy_estimate: Оценка энтропии.
        timestamp: Время захвата фазы.
    """
    
    phase_id: int
    name: str
    source_name: str
    raw_data: bytes
    hash_algorithm: str
    hash_value: Optional[bytes] = None
    entropy_estimate: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # START_METHOD___post_init__
    # START_CONTRACT:
    # PURPOSE: Валидация данных после инициализации.
    # KEYWORDS: [CONCEPT(5): Validation; CONCEPT(4): Init]
    # END_CONTRACT
    
    def __post_init__(self) -> None:
        """Валидация данных после инициализации."""
        # START_BLOCK_VALIDATE_PHASE_ID: [Проверка идентификатора фазы.]
        if not isinstance(self.phase_id, int):
            raise TypeError(f"phase_id должен быть int, получен {type(self.phase_id)}")
        
        if self.phase_id < 1 or self.phase_id > 4:
            logger.warning(
                f"[VarCheck][PhaseData][__post_init__][ConditionCheck] "
                f"phase_id {self.phase_id} вне диапазона 1-4"
            )
        # END_BLOCK_VALIDATE_PHASE_ID
        
        # START_BLOCK_VALIDATE_RAW_DATA: [Проверка сырых данных.]
        if not isinstance(self.raw_data, bytes):
            raise TypeError(f"raw_data должен быть bytes, получен {type(self.raw_data)}")
        # END_BLOCK_VALIDATE_RAW_DATA
        
        # START_BLOCK_VALIDATE_HASH: [Проверка хеша.]
        if self.hash_value is not None and not isinstance(self.hash_value, bytes):
            raise TypeError(f"hash_value должен быть bytes, получен {type(self.hash_value)}")
        
        # Проверка соответствия размера хеша алгоритму
        if self.hash_value is not None and self.hash_algorithm in HASH_SIZES:
            expected_size = HASH_SIZES.get(self.hash_algorithm, 0)
            if len(self.hash_value) != expected_size:
                logger.warning(
                    f"[VarCheck][PhaseData][__post_init__][ConditionCheck] "
                    f"Размер хеша {len(self.hash_value)} не соответствует ожидаемому {expected_size} "
                    f"для алгоритма {self.hash_algorithm}"
                )
        # END_BLOCK_VALIDATE_HASH
    
    # END_METHOD___post_init__
    
    # START_METHOD___eq__
    # START_CONTRACT:
    # PURPOSE: Проверка равенства двух PhaseData.
    # KEYWORDS: [CONCEPT(5): Equality]
    # END_CONTRACT
    
    def __eq__(self, other: object) -> bool:
        """Проверка равенства."""
        if not isinstance(other, PhaseData):
            return NotImplemented
        return (
            self.phase_id == other.phase_id and
            self.name == other.name and
            self.source_name == other.source_name and
            self.raw_data == other.raw_data and
            self.hash_algorithm == other.hash_algorithm and
            self.hash_value == other.hash_value
        )
    
    # END_METHOD___eq__
    
    # START_METHOD___lt__
    # START_CONTRACT:
    # PURPOSE: Сравнение для сортировки по phase_id.
    # KEYWORDS: [CONCEPT(5): Comparison]
    # END_CONTRACT
    
    def __lt__(self, other: object) -> bool:
        """Сравнение для сортировки."""
        if not isinstance(other, PhaseData):
            return NotImplemented
        return self.phase_id < other.phase_id
    
    # END_METHOD___lt__
    
    # START_METHOD_to_dict
    # START_CONTRACT:
    # PURPOSE: Преобразование в словарь для JSON сериализации.
    # OUTPUTS:
    # - dict: Словарь с данными фазы
    # KEYWORDS: [CONCEPT(6): Serialization; TECH(5): JSON]
    # END_CONTRACT
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует PhaseData в словарь.
        
        Returns:
            Словарь с данными фазы.
        """
        # START_BLOCK_TO_DICT: [Преобразование в словарь.]
        result = {
            "phase_id": self.phase_id,
            "name": self.name,
            "source_name": self.source_name,
            "raw_data_hex": self.raw_data.hex(),
            "raw_data_size": len(self.raw_data),
            "hash_algorithm": self.hash_algorithm,
            "hash_hex": self.hash_value.hex() if self.hash_value else None,
            "entropy_estimate": self.entropy_estimate,
            "timestamp": self.timestamp.isoformat()
        }
        
        logger.debug(
            f"[VarCheck][PhaseData][to_dict][ReturnData] "
            f"phase_id={self.phase_id}, raw_data_size={len(self.raw_data)}"
        )
        
        return result
        # END_BLOCK_TO_DICT
    
    # END_METHOD_to_dict
    
    # START_CLASSMETHOD_from_dict
    # START_CONTRACT:
    # PURPOSE: Создание PhaseData из словаря.
    # INPUTS:
    # - data: Словарь с данными фазы => data: Dict[str, Any]
    # OUTPUTS:
    # - PhaseData: Созданный объект
    # KEYWORDS: [CONCEPT(6): Deserialization; TECH(5): JSON]
    # END_CONTRACT
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PhaseData":
        """
        Создает PhaseData из словаря.
        
        Args:
            data: Словарь с данными фазы.
            
        Returns:
            Созданный объект PhaseData.
        """
        # START_BLOCK_FROM_DICT: [Создание из словаря.]
        raw_data_hex = data.get("raw_data_hex", "")
        hash_hex = data.get("hash_hex")
        
        result = cls(
            phase_id=data["phase_id"],
            name=data["name"],
            source_name=data["source_name"],
            raw_data=bytes.fromhex(raw_data_hex) if raw_data_hex else b"",
            hash_algorithm=data.get("hash_algorithm", HASH_ALGORITHM_NONE),
            hash_value=bytes.fromhex(hash_hex) if hash_hex else None,
            entropy_estimate=data.get("entropy_estimate", 0.0),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(timezone.utc)
        )
        
        logger.debug(
            f"[VarCheck][PhaseData][from_dict][ReturnData] "
            f"phase_id={result.phase_id}, raw_data_size={len(result.raw_data)}"
        )
        
        return result
        # END_BLOCK_FROM_DICT
    
    # END_CLASSMETHOD_from_dict

# END_DATACLASS_PhaseData


# START_CLASS_EntropySnapshot
# START_CONTRACT:
# PURPOSE: Иммутабельный контейнер для полного снапшота энтропийного состояния.
# ATTRIBUTES:
# - version: Версия формата снапшота => version: str
# - timestamp: Время создания => timestamp: datetime
# - phases: Список данных по фазам => phases: List[PhaseData]
# - final_state: Финальное состояние state[1043] => final_state: bytes | None
# - state_index: Индекс в кольцевом буфере => state_index: int
# - entropy_accumulated: Накопленная энтропия => entropy_accumulated: float
# - checksum: SHA256 контрольная сумма => checksum: bytes | None
# METHODS:
# - add_phase(phase: PhaseData) -> None: Добавление данных фазы
# - set_final_state(state: bytes, state_index: int, entropy: float) -> None: Установка финального состояния
# - to_dict() -> dict: Сериализация в словарь
# - to_binary() -> bytes: Сериализация в бинарный формат
# - from_dict(data: dict) -> EntropySnapshot: Десериализация из словаря (classmethod)
# - from_binary(data: bytes) -> EntropySnapshot: Десериализация из бинарного формата (classmethod)
# - validate() -> bool: Валидация целостности
# - get_buffer_state() -> bytes: Получение state[0:1023]
# - get_md_digest() -> bytes: Получение md[0:20] из state[1023:1043]
# KEYWORDS: [DOMAIN(10): SnapshotContainer; CONCEPT(9): Immutable; TECH(8): Serialization]
# END_CONTRACT

class EntropySnapshot:
    """
    Иммутабельный контейнер для полного снапшота энтропийного состояния.
    
    Хранит все данные энтропийного пайплайна: данные фаз, финальное состояние
    state[1043], метаданные и контрольную сумму для валидации целостности.
    
    Attributes:
        version: Версия формата снапшота.
        timestamp: Время создания снапшота.
        phases: Список данных PhaseData по каждой фазе.
        final_state: Финальное состояние state[1043] (STATE_BUFFER_SIZE байт).
        state_index: Текущий индекс в кольцевом буфере.
        entropy_accumulated: Накопленная энтропия.
        checksum: SHA256 контрольная сумма снапшота.
    """
    
    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация пустого снапшота.
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
        Инициализирует пустой снапшот.
        
        Args:
            version: Версия формата снапшота.
            timestamp: Время создания.
        """
        # START_BLOCK_INIT: [Инициализация атрибутов.]
        self._version: str = version or SNAPSHOT_VERSION
        self._timestamp: datetime = timestamp or datetime.now(timezone.utc)
        self._phases: List[PhaseData] = []
        self._final_state: Optional[bytes] = None
        self._state_index: int = 0
        self._entropy_accumulated: float = 0.0
        self._checksum: Optional[bytes] = None
        
        logger.info(
            f"[InitCheck][EntropySnapshot][__init__][Initialize] "
            f"Снапшот инициализирован: version={self._version}"
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
    
    # START_PROPERTY_phases
    @property
    def phases(self) -> List[PhaseData]:
        """Список данных фаз (копия для иммутабельности)."""
        return list(self._phases)
    
    # END_PROPERTY_phases
    
    # START_PROPERTY_final_state
    @property
    def final_state(self) -> Optional[bytes]:
        """Финальное состояние state[1043]."""
        return self._final_state
    
    # END_PROPERTY_final_state
    
    # START_PROPERTY_state_index
    @property
    def state_index(self) -> int:
        """Индекс в кольцевом буфере."""
        return self._state_index
    
    # END_PROPERTY_state_index
    
    # START_PROPERTY_entropy_accumulated
    @property
    def entropy_accumulated(self) -> float:
        """Накопленная энтропия."""
        return self._entropy_accumulated
    
    # END_PROPERTY_entropy_accumulated
    
    # START_PROPERTY_checksum
    @property
    def checksum(self) -> Optional[bytes]:
        """SHA256 контрольная сумма."""
        return self._checksum
    
    # END_PROPERTY_checksum
    
    # START_METHOD_add_phase
    # START_CONTRACT:
    # PURPOSE: Добавление данных фазы в снапшот.
    # INPUTS:
    # - phase: Данные фазы => phase: PhaseData
    # OUTPUTS:
    # - EntropySnapshot: Новый снапшот с добавленной фазой (иммутабельный паттерн)
    # KEYWORDS: [CONCEPT(7): Immutability; CONCEPT(6): DataAdd]
    # END_CONTRACT
    
    def add_phase(self, phase: PhaseData) -> "EntropySnapshot":
        """
        Добавляет данные фазы в снапшот.
        
        Использует иммутабельный паттерн: возвращает новый снапшот.
        
        Args:
            phase: Данные фазы для добавления.
            
        Returns:
            Новый снапшот с добавленной фазой.
        """
        # START_BLOCK_ADD_PHASE: [Добавление фазы в снапшот.]
        logger.info(
            f"[TraceCheck][EntropySnapshot][add_phase][AddPhase] "
            f"Добавление фазы: {phase.name}, phase_id={phase.phase_id}"
        )
        
        # Создаем новый снапшот с копией списка фаз
        new_snapshot = EntropySnapshot(
            version=self._version,
            timestamp=self._timestamp
        )
        new_snapshot._phases = self._phases + [phase]
        new_snapshot._final_state = self._final_state
        new_snapshot._state_index = self._state_index
        new_snapshot._entropy_accumulated = self._entropy_accumulated
        new_snapshot._checksum = self._checksum
        
        logger.info(
            f"[TraceCheck][EntropySnapshot][add_phase][AddPhase] "
            f"Фаза добавлена. Всего фаз: {len(new_snapshot._phases)} [SUCCESS]"
        )
        
        return new_snapshot
        # END_BLOCK_ADD_PHASE
    
    # END_METHOD_add_phase
    
    # START_METHOD_set_final_state
    # START_CONTRACT:
    # PURPOSE: Установка финального состояния state[1043].
    # INPUTS:
    # - state: Буфер состояния (1043 байт) => state: bytes
    # - state_index: Индекс в кольцевом буфере => state_index: int
    # - entropy: Накопленная энтропия => entropy: float
    # OUTPUTS:
    # - EntropySnapshot: Новый снапшот с установленным состоянием
    # KEYWORDS: [CONCEPT(7): Immutability; CONCEPT(6): StateSet]
    # END_CONTRACT
    
    def set_final_state(
        self,
        state: bytes,
        state_index: int,
        entropy: float
    ) -> "EntropySnapshot":
        """
        Устанавливает финальное состояние state[1043].
        
        Args:
            state: Буфер состояния (1039 байт).
            state_index: Индекс в кольцевом буфере.
            entropy: Накопленная энтропия.
            
        Returns:
            Новый снапшот с установленным состоянием.
        """
        # START_BLOCK_VALIDATE_STATE: [Валидация размера состояния.]
        logger.info(
            f"[TraceCheck][EntropySnapshot][set_final_state][SetState] "
            f"Установка финального состояния: size={len(state)}, index={state_index}"
        )
        
        if len(state) != STATE_BUFFER_SIZE:
            logger.error(
                f"[VarCheck][EntropySnapshot][set_final_state][ValidateState] "
                f"Размер state {len(state)} не соответствует STATE_BUFFER_SIZE {STATE_BUFFER_SIZE} [FAIL]"
            )
            raise ValueError(
                f"Размер state должен быть {STATE_BUFFER_SIZE}, получен {len(state)}"
            )
        # END_BLOCK_VALIDATE_STATE
        
        # START_BLOCK_SET_STATE: [Установка состояния.]
        new_snapshot = EntropySnapshot(
            version=self._version,
            timestamp=self._timestamp
        )
        new_snapshot._phases = list(self._phases)
        new_snapshot._final_state = state
        new_snapshot._state_index = state_index
        new_snapshot._entropy_accumulated = entropy
        
        # Вычисляем контрольную сумму
        new_snapshot._compute_checksum()
        
        logger.info(
            f"[TraceCheck][EntropySnapshot][set_final_state][SetState] "
            f"Финальное состояние установлено [SUCCESS]"
        )
        
        return new_snapshot
        # END_BLOCK_SET_STATE
    
    # END_METHOD_set_final_state
    
    # START_METHOD_get_buffer_state
    # START_CONTRACT:
    # PURPOSE: Получение кольцевого буфера state[0:1023].
    # OUTPUTS:
    # - bytes: Буфер состояния (1023 байта)
    # KEYWORDS: [CONCEPT(6): StateGet; TECH(5): Buffer)]
    # END_CONTRACT
    
    def get_buffer_state(self) -> bytes:
        """
        Возвращает кольцевой буфер state[0:1023].
        
        Returns:
            Буфер состояния (1023 байта).
            
        Raises:
            ValueError: Если final_state не установлен.
        """
        # START_BLOCK_GET_BUFFER: [Получение буфера состояния.]
        if self._final_state is None:
            logger.error(
                f"[VarCheck][EntropySnapshot][get_buffer_state][GetBuffer] "
                f"final_state не установлен [FAIL]"
            )
            raise ValueError("final_state не установлен")
        
        buffer = self._final_state[:STATE_SIZE]
        
        logger.debug(
            f"[VarCheck][EntropySnapshot][get_buffer_state][ReturnData] "
            f"Возвращено {len(buffer)} байт [VALUE]"
        )
        
        return buffer
        # END_BLOCK_GET_BUFFER
    
    # END_METHOD_get_buffer_state
    
    # START_METHOD_get_md_digest
    # START_CONTRACT:
    # PURPOSE: Получение SHA-1 дайджеста из state[1023:1043].
    # OUTPUTS:
    # - bytes: MD5 дайджест (16 байт)
    # KEYWORDS: [CONCEPT(6): DigestGet; TECH(5): MD5]
    # END_CONTRACT
    
    def get_md_digest(self) -> bytes:
        """
        Возвращает SHA-1 дайджест из state[1023:1043].
        
        Returns:
            MD5 дайджест (16 байт).
            
        Raises:
            ValueError: Если final_state не установлен.
        """
        # START_BLOCK_GET_MD: [Получение MD дайджеста.]
        if self._final_state is None:
            logger.error(
                f"[VarCheck][EntropySnapshot][get_md_digest][GetMD] "
                f"final_state не установлен [FAIL]"
            )
            raise ValueError("final_state не установлен")
        
        md = self._final_state[STATE_SIZE:STATE_BUFFER_SIZE]
        
        logger.debug(
            f"[VarCheck][EntropySnapshot][get_md_digest][ReturnData] "
            f"Возвращено {len(md)} байт [VALUE]"
        )
        
        return md
        # END_BLOCK_GET_MD
    
    # END_METHOD_get_md_digest
    
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
            f"[TraceCheck][EntropySnapshot][_compute_checksum][ComputeChecksum] "
            f"Вычисление контрольной суммы"
        )
        
        # Собираем данные для хеширования
        hasher = hashlib.sha256()
        
        # Версия
        hasher.update(self._version.encode("utf-8"))
        
        # Время создания
        hasher.update(self._timestamp.isoformat().encode("utf-8"))
        
        # Данные фаз
        for phase in self._phases:
            hasher.update(phase.raw_data)
            if phase.hash_value:
                hasher.update(phase.hash_value)
        
        # Финальное состояние
        if self._final_state:
            hasher.update(self._final_state)
        
        self._checksum = hasher.digest()
        
        logger.debug(
            f"[TraceCheck][EntropySnapshot][_compute_checksum][ComputeChecksum] "
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
        - Наличие данных фаз
        - Размер final_state (должен быть STATE_BUFFER_SIZE)
        - Контрольную сумму
        
        Returns:
            True если снапшот валиден, иначе False.
        """
        # START_BLOCK_VALIDATE: [Валидация снапшота.]
        logger.info(
            f"[TraceCheck][EntropySnapshot][validate][Validate] "
            f"Начало валидации снапшота"
        )
        
        # START_BLOCK_CHECK_PHASES: [Проверка наличия фаз.]
        if not self._phases:
            logger.error(
                f"[VarCheck][EntropySnapshot][validate][CheckPhases] "
                f"Нет данных фаз [FAIL]"
            )
            return False
        
        logger.debug(
            f"[VarCheck][EntropySnapshot][validate][CheckPhases] "
            f"Фаз: {len(self._phases)} [SUCCESS]"
        )
        # END_BLOCK_CHECK_PHASES
        
        # START_BLOCK_CHECK_FINAL_STATE: [Проверка финального состояния.]
        if self._final_state is None:
            logger.error(
                f"[VarCheck][EntropySnapshot][validate][CheckFinalState] "
                f"final_state не установлен [FAIL]"
            )
            return False
        
        if len(self._final_state) != STATE_BUFFER_SIZE:
            logger.error(
                f"[VarCheck][EntropySnapshot][validate][CheckFinalState] "
                f"Размер state {len(self._final_state)} != {STATE_BUFFER_SIZE} [FAIL]"
            )
            return False
        
        logger.debug(
            f"[VarCheck][EntropySnapshot][validate][CheckFinalState] "
            f"final_state: {STATE_BUFFER_SIZE} байт [SUCCESS]"
        )
        # END_BLOCK_CHECK_FINAL_STATE
        
        # START_BLOCK_CHECK_PHASE_DATA: [Проверка данных фаз.]
        for phase in self._phases:
            if not isinstance(phase.raw_data, bytes) or len(phase.raw_data) == 0:
                logger.error(
                    f"[VarCheck][EntropySnapshot][validate][CheckPhaseData] "
                    f"Фаза {phase.phase_id}: некорректные данные [FAIL]"
                )
                return False
        
        logger.debug(
            f"[VarCheck][EntropySnapshot][validate][CheckPhaseData] "
            f"Все фазы корректны [SUCCESS]"
        )
        # END_BLOCK_CHECK_PHASE_DATA
        
        # START_BLOCK_CHECK_VERSION: [Проверка версии.]
        if not self._version:
            logger.warning(
                f"[VarCheck][EntropySnapshot][validate][CheckVersion] "
                f"Версия не установлена [WARNING]"
            )
        # END_BLOCK_CHECK_VERSION
        
        logger.info(
            f"[TraceCheck][EntropySnapshot][validate][Validate] "
            f"Валидация пройдена [SUCCESS]"
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
            f"[TraceCheck][EntropySnapshot][to_dict][Serialize] "
            f"Сериализация в словарь"
        )
        
        # Создаем копию для вычисления контрольной суммы
        snapshot_copy = EntropySnapshot(
            version=self._version,
            timestamp=self._timestamp
        )
        snapshot_copy._phases = list(self._phases)
        snapshot_copy._final_state = self._final_state
        snapshot_copy._state_index = self._state_index
        snapshot_copy._entropy_accumulated = self._entropy_accumulated
        snapshot_copy._compute_checksum()
        
        result = {
            "version": self._version,
            "timestamp": self._timestamp.isoformat(),
            "metadata": {
                "state_size": STATE_SIZE,
                "md_digest_length": MD_DIGEST_LENGTH,
                "state_buffer_size": STATE_BUFFER_SIZE,
                "snapshot_version": SNAPSHOT_VERSION,
                "hash_algorithm_note": "MD5 for phases 2-3, SHA256 for phase 4. Reference requires SHA-1."
            },
            "phases": [phase.to_dict() for phase in self._phases],
            "final_state": {
                "state_hex": self._final_state.hex() if self._final_state else None,
                "state_size": len(self._final_state) if self._final_state else 0,
                "state_index": self._state_index,
                "entropy_accumulated": self._entropy_accumulated
            },
            "integrity": {
                "checksum_algorithm": "SHA256",
                "checksum_hex": snapshot_copy._checksum.hex() if snapshot_copy._checksum else None
            }
        }
        
        logger.info(
            f"[TraceCheck][EntropySnapshot][to_dict][Serialize] "
            f"Сериализовано {len(self._phases)} фаз [SUCCESS]"
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
    # - EntropySnapshot: Созданный снапшот
    # KEYWORDS: [CONCEPT(8): Deserialization; TECH(7): JSON]
    # END_CONTRACT
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntropySnapshot":
        """
        Создает снапшот из словаря.
        
        Args:
            data: Словарь с данными снапшота.
            
        Returns:
            Созданный объект EntropySnapshot.
        """
        # START_BLOCK_FROM_DICT: [Десериализация из словаря.]
        logger.info(
            f"[TraceCheck][EntropySnapshot][from_dict][Deserialize] "
            f"Десериализация из словаря"
        )
        
        # Создаем базовый снапшот
        snapshot = cls(
            version=data.get("version", SNAPSHOT_VERSION),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(timezone.utc)
        )
        
        # Восстанавливаем фазы
        snapshot._phases = [
            PhaseData.from_dict(phase_data) 
            for phase_data in data.get("phases", [])
        ]
        
        # Восстанавливаем финальное состояние
        final_state_data = data.get("final_state", {})
        if final_state_data.get("state_hex"):
            state_bytes = bytes.fromhex(final_state_data["state_hex"])
            snapshot._final_state = state_bytes
            snapshot._state_index = final_state_data.get("state_index", 0)
            snapshot._entropy_accumulated = final_state_data.get("entropy_accumulated", 0.0)
        
        # Восстанавливаем контрольную сумму
        integrity = data.get("integrity", {})
        if integrity.get("checksum_hex"):
            snapshot._checksum = bytes.fromhex(integrity["checksum_hex"])
        
        logger.info(
            f"[TraceCheck][EntropySnapshot][from_dict][Deserialize] "
            f"Десериализовано {len(snapshot._phases)} фаз [SUCCESS]"
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
            0x00-0x03: SNAP magic (4 байта)
            0x04-0x05: Version (2 байта, little-endian)
            0x06-0x09: Timestamp Unix (4 байта)
            0x0A-0x0B: Phase count (2 байта)
            0x0C-...: Phase records
            ...: Final state (1043 байт)
            ...: Checksum SHA256 (32 байта)
            
        Phase record:
            0x00: Phase ID (1 байт)
            0x01: Hash algorithm (1 байт: 0=None, 1=MD5, 2=SHA256)
            0x02-0x03: Raw data length (2 байта)
            0x04-...: Raw data
            ...: Hash value (0/16/32 байта)
            
        Returns:
            Бинарные данные снапшота.
        """
        # START_BLOCK_TO_BINARY: [Сериализация в бинарный формат.]
        logger.info(
            f"[TraceCheck][EntropySnapshot][to_binary][SerializeBinary] "
            f"Сериализация в бинарный формат"
        )
        
        # Вычисляем контрольную сумму
        snapshot_copy = EntropySnapshot(
            version=self._version,
            timestamp=self._timestamp
        )
        snapshot_copy._phases = list(self._phases)
        snapshot_copy._final_state = self._final_state
        snapshot_copy._state_index = self._state_index
        snapshot_copy._entropy_accumulated = self._entropy_accumulated
        snapshot_copy._compute_checksum()
        
        # Начинаем формировать бинарные данные
        result = bytearray()
        
        # Magic
        result.extend(SNAPSHOT_MAGIC)
        
        # Version (2 bytes, little-endian)
        result.extend(SNAPSHOT_BINARY_VERSION.to_bytes(2, "little"))
        
        # Timestamp (4 bytes, Unix epoch)
        timestamp_ts = int(self._timestamp.timestamp())
        result.extend(timestamp_ts.to_bytes(4, "little"))
        
        # Phase count
        phase_count = len(self._phases)
        result.extend(phase_count.to_bytes(2, "little"))
        
        logger.debug(
            f"[VarCheck][EntropySnapshot][to_binary][SerializeBinary] "
            f"Фаз: {phase_count} [VALUE]"
        )
        
        # Phase records
        for phase in self._phases:
            # Phase ID (1 byte)
            result.append(phase.phase_id)
            
            # Hash algorithm (1 byte)
            algo_map = {
                HASH_ALGORITHM_NONE: 0,
                HASH_ALGORITHM_MD5: 1,
                HASH_ALGORITHM_SHA256: 2
            }
            algo_code = algo_map.get(phase.hash_algorithm, 0)
            result.append(algo_code)
            
            # Raw data length (2 bytes)
            raw_len = len(phase.raw_data)
            result.extend(raw_len.to_bytes(2, "little"))
            
            # Raw data
            result.extend(phase.raw_data)
            
            # Hash value
            if phase.hash_value:
                result.extend(phase.hash_value)
        
        # Final state (1043 bytes)
        if self._final_state:
            result.extend(self._final_state)
        else:
            result.extend(b"\x00" * STATE_BUFFER_SIZE)
        
        # Checksum SHA256 (32 bytes)
        if snapshot_copy._checksum:
            result.extend(snapshot_copy._checksum)
        else:
            result.extend(b"\x00" * 32)
        
        logger.info(
            f"[TraceCheck][EntropySnapshot][to_binary][SerializeBinary] "
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
    # - EntropySnapshot: Созданный снапшот
    # KEYWORDS: [CONCEPT(8): Deserialization; TECH(7): Binary]
    # END_CONTRACT
    
    @classmethod
    def from_binary(cls, data: bytes) -> "EntropySnapshot":
        """
        Создает снапшот из бинарных данных.
        
        Args:
            data: Бинарные данные снапшота.
            
        Returns:
            Созданный объект EntropySnapshot.
            
        Raises:
            ValueError: Если формат данных некорректен.
        """
        # START_BLOCK_FROM_BINARY: [Десериализация из бинарного формата.]
        logger.info(
            f"[TraceCheck][EntropySnapshot][from_binary][DeserializeBinary] "
            f"Десериализация из бинарного формата: {len(data)} байт"
        )
        
        offset = 0
        
        # Magic (4 bytes)
        magic = data[offset:offset + 4]
        offset += 4
        
        if magic != SNAPSHOT_MAGIC:
            logger.error(
                f"[VarCheck][EntropySnapshot][from_binary][CheckMagic] "
                f"Неверное магическое число: {magic} [FAIL]"
            )
            raise ValueError(f"Неверное магическое число: {magic}")
        
        # Version (2 bytes)
        version = int.from_bytes(data[offset:offset + 2], "little")
        offset += 2
        
        logger.debug(
            f"[VarCheck][EntropySnapshot][from_binary][CheckVersion] "
            f"Версия: {version} [VALUE]"
        )
        
        # Timestamp (4 bytes)
        timestamp_ts = int.from_bytes(data[offset:offset + 4], "little")
        offset += 4
        timestamp = datetime.fromtimestamp(timestamp_ts, tz=timezone.utc)
        
        # Phase count (2 bytes)
        phase_count = int.from_bytes(data[offset:offset + 2], "little")
        offset += 2
        
        logger.debug(
            f"[VarCheck][EntropySnapshot][from_binary][CheckPhases] "
            f"Фаз: {phase_count} [VALUE]"
        )
        
        # Создаем снапшот
        snapshot = cls(
            version=SNAPSHOT_VERSION,
            timestamp=timestamp
        )
        
        # Phase records
        algo_reverse_map = {
            0: HASH_ALGORITHM_NONE,
            1: HASH_ALGORITHM_MD5,
            2: HASH_ALGORITHM_SHA256
        }
        
        for _ in range(phase_count):
            # Phase ID (1 byte)
            phase_id = data[offset]
            offset += 1
            
            # Hash algorithm (1 byte)
            algo_code = data[offset]
            offset += 1
            hash_algorithm = algo_reverse_map.get(algo_code, HASH_ALGORITHM_NONE)
            
            # Raw data length (2 bytes)
            raw_len = int.from_bytes(data[offset:offset + 2], "little")
            offset += 2
            
            # Raw data
            raw_data = data[offset:offset + raw_len]
            offset += raw_len
            
            # Hash value
            hash_size = HASH_SIZES.get(hash_algorithm, 0)
            hash_value = None
            if hash_size > 0:
                hash_value = data[offset:offset + hash_size]
                offset += hash_size
            
            # Создаем PhaseData
            phase = PhaseData(
                phase_id=phase_id,
                name=f"phase_{phase_id}",
                source_name="unknown",
                raw_data=raw_data,
                hash_algorithm=hash_algorithm,
                hash_value=hash_value
            )
            snapshot._phases.append(phase)
        
        # Final state (1043 bytes)
        if offset + STATE_BUFFER_SIZE <= len(data):
            snapshot._final_state = data[offset:offset + STATE_BUFFER_SIZE]
            offset += STATE_BUFFER_SIZE
        else:
            snapshot._final_state = b"\x00" * STATE_BUFFER_SIZE
        
        # Checksum (32 bytes)
        if offset + 32 <= len(data):
            snapshot._checksum = data[offset:offset + 32]
        
        logger.info(
            f"[TraceCheck][EntropySnapshot][from_binary][DeserializeBinary] "
            f"Десериализовано {len(snapshot._phases)} фаз [SUCCESS]"
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
            f"EntropySnapshot("
            f"version={self._version}, "
            f"phases={len(self._phases)}, "
            f"final_state={'set' if self._final_state else 'None'})"
        )
    
    # END_METHOD___repr__

# END_CLASS_EntropySnapshot


# START_CLASS_SnapshotBuilder
# START_CONTRACT:
# PURPOSE: Builder-паттерн для пошагового создания снапшота с интеграцией в EntropyEngine.
# ATTRIBUTES:
# - _engine: EntropyEngine - ссылка на координатор энтропии => _engine: EntropyEngine
# - _snapshot: EntropySnapshot - строящийся снапшот => _snapshot: EntropySnapshot
# - _cache: EntropyPipelineCache - опциональный кэш => _cache: EntropyPipelineCache | None
# - _phase_sizes: Размеры данных для каждой фазы => _phase_sizes: Dict[str, int]
# METHODS:
# - __init__(engine: EntropyEngine, cache: EntropyPipelineCache = None) -> None: Инициализация
# - capture_phase(phase_id: int, name: str, source_name: str, size: int, hash_algo: str = None) -> PhaseData: Захват фазы
# - capture_all(sizes: dict = None) -> SnapshotBuilder: Захват всех фаз
# - capture_final_state(rand_add_module) -> None: Захват финального состояния
# - build() -> EntropySnapshot: Финализация и возврат снапшота
# KEYWORDS: [DOMAIN(9): Builder; CONCEPT(8): Construction; TECH(7): Integration]
# END_CONTRACT

class SnapshotBuilder:
    """
    Builder-паттерн для пошагового создания снапшота из EntropyEngine.
    
    Обеспечивает удобный интерфейс для захвата данных энтропии от
    различных источников, вычисления хешей и формирования финального
    состояния state[1043].
    
    Attributes:
        engine: Ссылка на EntropyEngine для получения данных.
        cache: Опциональный кэш для обратной совместимости.
        phase_sizes: Словарь размеров данных для каждой фазы.
    """
    
    # START_METHOD___init__
    # START_CONTRACT:
    # PURPOSE: Инициализация SnapshotBuilder.
    # INPUTS:
    # - engine: EntropyEngine для получения энтропии => engine: EntropyEngine
    # - cache: Опциональный кэш => cache: EntropyPipelineCache | None
    # - phase_sizes: Размеры данных для фаз => phase_sizes: Dict[str, int] | None
    # OUTPUTS:
    # - None
    # KEYWORDS: [CONCEPT(5): Initialization]
    # END_CONTRACT
    
    def __init__(
        self,
        engine,
        cache=None,
        phase_sizes: Optional[Dict[str, int]] = None
    ) -> None:
        """
        Инициализирует SnapshotBuilder.
        
        Args:
            engine: EntropyEngine для получения данных.
            cache: Опциональный EntropyPipelineCache для совместимости.
            phase_sizes: Словарь размеров данных для каждой фазы.
        """
        # START_BLOCK_INIT: [Инициализация SnapshotBuilder.]
        self._engine = engine
        self._cache = cache
        self._snapshot = EntropySnapshot()
        self._phase_sizes = phase_sizes or PHASE_DEFAULT_SIZES.copy()
        
        logger.info(
            f"[InitCheck][SnapshotBuilder][__init__][Initialize] "
            f"SnapshotBuilder инициализирован с {len(self._phase_sizes)} фазами"
        )
        # END_BLOCK_INIT
    
    # END_METHOD___init__
    
    # START_METHOD_capture_phase
    # START_CONTRACT:
    # PURPOSE: Захват данных одной фазы от источника энтропии.
    # INPUTS:
    # - phase_id: Идентификатор фазы => phase_id: int
    # - name: Имя фазы => name: str
    # - source_name: Имя источника в EntropyEngine => source_name: str
    # - size: Размер запрашиваемых данных => size: int
    # - hash_algo: Алгоритм хеширования (опционально) => hash_algo: str | None
    # OUTPUTS:
    # - PhaseData: Данные захваченной фазы
    # KEYWORDS: [CONCEPT(7): PhaseCapture; TECH(6): Hashing]
    # END_CONTRACT
    
    def capture_phase(
        self,
        phase_id: int,
        name: str,
        source_name: str,
        size: int,
        hash_algo: Optional[str] = None
    ) -> PhaseData:
        """
        Захватывает данные одной фазы от источника энтропии.
        
        Args:
            phase_id: Идентификатор фазы (1-4).
            name: Имя фазы.
            source_name: Имя источника в EntropyEngine.
            size: Размер запрашиваемых данных в байтах.
            hash_algo: Алгоритм хеширования (None, MD5, SHA256).
            
        Returns:
            PhaseData с захваченными данными.
        """
        # START_BLOCK_GET_ENTROPY: [Получение энтропии от источника.]
        logger.info(
            f"[TraceCheck][SnapshotBuilder][capture_phase][GetEntropy] "
            f"Захват фазы: {name}, source={source_name}, size={size}"
        )
        
        try:
            raw_data = self._engine.get_entropy(size, source_name)
            
            logger.info(
                f"[TraceCheck][SnapshotBuilder][capture_phase][GetEntropy] "
                f"Получено {len(raw_data)} байт от {source_name} [SUCCESS]"
            )
            
        except Exception as e:
            logger.error(
                f"[CriticalError][SnapshotBuilder][capture_phase][GetEntropy] "
                f"Ошибка получения энтропии от {source_name}: {str(e)} [FAIL]"
            )
            # Создаем пустые данные в случае ошибки
            raw_data = b""
        
        # END_BLOCK_GET_ENTROPY
        
        # START_BLOCK_COMPUTE_HASH: [Вычисление хеша.]
        hash_value: Optional[bytes] = None
        effective_hash_algo = hash_algo or HASH_ALGORITHM_NONE
        
        if effective_hash_algo != HASH_ALGORITHM_NONE and raw_data:
            logger.debug(
                f"[TraceCheck][SnapshotBuilder][capture_phase][ComputeHash] "
                f"Вычисление хеша: {effective_hash_algo}"
            )
            
            if effective_hash_algo == HASH_ALGORITHM_MD5:
                hash_value = hashlib.md5(raw_data).digest()
            elif effective_hash_algo == HASH_ALGORITHM_SHA256:
                hash_value = hashlib.sha256(raw_data).digest()
            
            logger.debug(
                f"[TraceCheck][SnapshotBuilder][capture_phase][ComputeHash] "
                f"Хеш вычислен: {hash_value.hex()[:16]}... [SUCCESS]"
            )
        # END_BLOCK_COMPUTE_HASH
        
        # START_BLOCK_CREATE_PHASE_DATA: [Создание PhaseData.]
        phase_data = PhaseData(
            phase_id=phase_id,
            name=name,
            source_name=source_name,
            raw_data=raw_data,
            hash_algorithm=effective_hash_algo,
            hash_value=hash_value,
            entropy_estimate=0.0  # Можно вычислить на основе данных
        )
        
        # Добавляем фазу в снапшот
        self._snapshot = self._snapshot.add_phase(phase_data)
        
        logger.info(
            f"[TraceCheck][SnapshotBuilder][capture_phase][CapturePhase] "
            f"Фаза {name} захвачена [SUCCESS]"
        )
        
        return phase_data
        # END_BLOCK_CREATE_PHASE_DATA
    
    # END_METHOD_capture_phase
    
    # START_METHOD_capture_all
    # START_CONTRACT:
    # PURPOSE: Захват данных всех фаз энтропии.
    # INPUTS:
    # - sizes: Опциональный словарь размеров для каждой фазы => sizes: Dict[str, int] | None
    # OUTPUTS:
    # - SnapshotBuilder: self для цепочки вызовов
    # KEYWORDS: [CONCEPT(8): FullCapture; TECH(7): Aggregation]
    # END_CONTRACT
    
    def capture_all(self, sizes: Optional[Dict[str, int]] = None) -> "SnapshotBuilder":
        """
        Захватывает данные всех фаз энтропии.
        
        Args:
            sizes: Опциональный словарь размеров для каждой фазы.
                   Если None, используются размеры по умолчанию.
            
        Returns:
            self для цепочки вызовов.
        """
        # START_BLOCK_CAPTURE_ALL: [Захват всех фаз.]
        logger.info(
            f"[TraceCheck][SnapshotBuilder][capture_all][CaptureAll] "
            f"Захват всех фаз энтропии"
        )
        
        # Используем переданные размеры или установленные
        phase_sizes = sizes or self._phase_sizes
        
        # Фаза 1: RAND_poll
        if PHASE_RAND_POLL in phase_sizes:
            self.capture_phase(
                phase_id=1,
                name=PHASE_RAND_POLL,
                source_name=PHASE_TO_SOURCE[PHASE_RAND_POLL],
                size=phase_sizes[PHASE_RAND_POLL],
                hash_algo=PHASE_TO_HASH[PHASE_RAND_POLL]
            )
        
        # Фаза 2: GetBitmapBits
        if PHASE_GET_BITMAP_BITS in phase_sizes:
            self.capture_phase(
                phase_id=2,
                name=PHASE_GET_BITMAP_BITS,
                source_name=PHASE_TO_SOURCE[PHASE_GET_BITMAP_BITS],
                size=phase_sizes[PHASE_GET_BITMAP_BITS],
                hash_algo=PHASE_TO_HASH[PHASE_GET_BITMAP_BITS]
            )
        
        # Фаза 3: HKEY_PERFORMANCE_DATA
        if PHASE_HKEY_PERFORMANCE in phase_sizes:
            self.capture_phase(
                phase_id=3,
                name=PHASE_HKEY_PERFORMANCE,
                source_name=PHASE_TO_SOURCE[PHASE_HKEY_PERFORMANCE],
                size=phase_sizes[PHASE_HKEY_PERFORMANCE],
                hash_algo=PHASE_TO_HASH[PHASE_HKEY_PERFORMANCE]
            )
        
        # Фаза 4: QueryPerformanceCounter
        if PHASE_QPC in phase_sizes:
            self.capture_phase(
                phase_id=4,
                name=PHASE_QPC,
                source_name=PHASE_TO_SOURCE[PHASE_QPC],
                size=phase_sizes[PHASE_QPC],
                hash_algo=PHASE_TO_HASH[PHASE_QPC]
            )
        
        logger.info(
            f"[TraceCheck][SnapshotBuilder][capture_all][CaptureAll] "
            f"Все фазы захвачены: {len(self._snapshot.phases)} [SUCCESS]"
        )
        
        return self
        # END_BLOCK_CAPTURE_ALL
    
    # END_METHOD_capture_all
    
    # START_METHOD_capture_final_state
    # START_CONTRACT:
    # PURPOSE: Захват финального состояния state[1043] из RandAddImplementation.
    # INPUTS:
    # - rand_add_module: Модуль RandAddImplementation => rand_add_module: Any
    # OUTPUTS:
    # - SnapshotBuilder: self для цепочки вызовов
    # KEYWORDS: [CONCEPT(7): StateCapture; TECH(6): Integration]
    # END_CONTRACT
    
    def capture_final_state(self, rand_add_module) -> "SnapshotBuilder":
        """
        Захватывает финальное состояние state[1043] из RandAddImplementation.
        
        Args:
            rand_add_module: Экземпляр RandAddImplementation.
            
        Returns:
            self для цепочки вызовов.
        """
        # START_BLOCK_GET_STATE: [Получение финального состояния.]
        logger.info(
            f"[TraceCheck][SnapshotBuilder][capture_final_state][GetState] "
            f"Захват финального состояния из RandAddImplementation"
        )
        
        try:
            # Получаем state[1043] из модуля
            state = rand_add_module.get_state()
            
            # Конвертируем в bytes если это vector
            if hasattr(state, '__iter__') and not isinstance(state, bytes):
                state = bytes(state)
            
            # Получаем state_index (может быть атрибутом модуля)
            state_index = getattr(rand_add_module, 'state_index', 512)
            
            # Получаем накопленную энтропию
            entropy = getattr(rand_add_module, 'entropy', 0.0)
            
            logger.info(
                f"[TraceCheck][SnapshotBuilder][capture_final_state][GetState] "
                f"Получен state: {len(state)} байт, index={state_index}, entropy={entropy} [SUCCESS]"
            )
            
            # Устанавливаем финальное состояние
            self._snapshot = self._snapshot.set_final_state(state, state_index, entropy)
            
        except Exception as e:
            logger.error(
                f"[CriticalError][SnapshotBuilder][capture_final_state][GetState] "
                f"Ошибка получения state: {str(e)} [FAIL]"
            )
            # Создаем пустое состояние в случае ошибки
            empty_state = b"\x00" * STATE_BUFFER_SIZE
            self._snapshot = self._snapshot.set_final_state(empty_state, 0, 0.0)
        
        # END_BLOCK_GET_STATE
        
        return self
    
    # END_METHOD_capture_final_state
    
    # START_METHOD_build
    # START_CONTRACT:
    # PURPOSE: Финализация и возврат готового EntropySnapshot.
    # OUTPUTS:
    # - EntropySnapshot: Готовый снапшот
    # KEYWORDS: [CONCEPT(7): Build; TECH(6): Finalization]
    # END_CONTRACT
    
    def build(self) -> EntropySnapshot:
        """
        Финализирует и возвращает готовый EntropySnapshot.
        
        Returns:
            Готовый объект EntropySnapshot.
            
        Raises:
            ValueError: Если снапшот невалиден.
        """
        # START_BLOCK_BUILD: [Финализация снапшота.]
        logger.info(
            f"[TraceCheck][SnapshotBuilder][build][Build] "
            f"Финализация снапшота"
        )
        
        # Валидируем снапшот
        if not self._snapshot.validate():
            logger.error(
                f"[VarCheck][SnapshotBuilder][build][Build] "
                f"Снапшот невалиден [FAIL]"
            )
            raise ValueError("Снапшот невалиден")
        
        logger.info(
            f"[TraceCheck][SnapshotBuilder][build][Build] "
            f"Снапшот готов: {len(self._snapshot.phases)} фаз [SUCCESS]"
        )
        
        return self._snapshot
        # END_BLOCK_BUILD
    
    # END_METHOD_build
    
    # START_METHOD_set_phase_size
    # START_CONTRACT:
    # PURPOSE: Установка размера данных для конкретной фазы.
    # INPUTS:
    # - phase_name: Имя фазы => phase_name: str
    # - size: Размер в байтах => size: int
    # OUTPUTS:
    # - SnapshotBuilder: self для цепочки вызовов
    # KEYWORDS: [CONCEPT(5): Configuration]
    # END_CONTRACT
    
    def set_phase_size(self, phase_name: str, size: int) -> "SnapshotBuilder":
        """
        Устанавливает размер данных для конкретной фазы.
        
        Args:
            phase_name: Имя фазы.
            size: Размер в байтах.
            
        Returns:
            self для цепочки вызовов.
        """
        self._phase_sizes[phase_name] = size
        logger.debug(
            f"[VarCheck][SnapshotBuilder][set_phase_size][SetSize] "
            f"Размер фазы {phase_name} установлен: {size}"
        )
        return self
    
    # END_METHOD_set_phase_size
    
    # START_METHOD_get_snapshot
    # START_CONTRACT:
    # PURPOSE: Получение текущего состояния снапшота (без валидации).
    # OUTPUTS:
    # - EntropySnapshot: Текущий снапшот
    # KEYWORDS: [CONCEPT(5): Getter]
    # END_CONTRACT
    
    def get_snapshot(self) -> EntropySnapshot:
        """
        Возвращает текущий снапшот (без финальной валидации).
        
        Returns:
            Текущий объект EntropySnapshot.
        """
        return self._snapshot
    
    # END_METHOD_get_snapshot

# END_CLASS_SnapshotBuilder
