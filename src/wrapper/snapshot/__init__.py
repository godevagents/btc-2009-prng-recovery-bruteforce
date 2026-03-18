# FILE: wrapper/snapshot/__init__.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Модуль создания и управления снапшотами энтропийного состояния PRNG.
# SCOPE: Снапшоты, сериализация, валидация
# INPUT: EntropyEngine, данные источников энтропии
# OUTPUT: EntropySnapshot, PhaseData, SnapshotBuilder
# KEYWORDS: [DOMAIN(10): SnapshotManagement; CONCEPT(9): EntropyState; TECH(8): Serialization]
# LINKS: [USES(10): wrapper.entropy.entropy_engine; USES(8): cache.entropy_pipeline_cache]
# END_MODULE_CONTRACT

"""
Модуль снапшотов энтропии.

Предоставляет инструменты для создания, сериализации и валидации
снапшотов энтропийного состояния PRNG в процессе генерации wallet.dat.

Основные классы:
    - PhaseData: dataclass для данных одной фазы энтропии
    - EntropySnapshot: иммутабельный контейнер снапшота
    - SnapshotBuilder: Builder-паттерн для пошагового создания снапшота

Пример использования:
    from src.wrapper.snapshot import SnapshotBuilder
    from src.wrapper.entropy import EntropyEngine
    
    engine = EntropyEngine()
    builder = SnapshotBuilder(engine)
    snapshot = builder.capture_all().build()
    
    # Сериализация
    snapshot.to_dict()  # JSON
    snapshot.to_binary()  # Binary
"""

from src.wrapper.snapshot.constants import (
    STATE_SIZE,
    MD_DIGEST_LENGTH,
    STATE_BUFFER_SIZE,
    SNAPSHOT_VERSION,
    SNAPSHOT_MAGIC
)

from src.wrapper.snapshot.gen_snapshot import (
    PhaseData,
    EntropySnapshot,
    SnapshotBuilder
)

from src.wrapper.snapshot.snapshot_io import (
    save_snapshot,
    load_snapshot,
    compare_snapshots
)

from src.wrapper.snapshot.gen_log import (
    KeyData,
    WalletCollectionData,
    WalletGenSnapshot,
    capture_key,
    capture_wallet_collection,
    capture_wallet_dat_info,
    create_wallet_gen_snapshot
)

__all__ = [
    # Константы
    "STATE_SIZE",
    "MD_DIGEST_LENGTH", 
    "STATE_BUFFER_SIZE",
    "SNAPSHOT_VERSION",
    "SNAPSHOT_MAGIC",
    # Классы энтропии
    "PhaseData",
    "EntropySnapshot",
    "SnapshotBuilder",
    # Функции IO
    "save_snapshot",
    "load_snapshot",
    "compare_snapshots",
    # Классы wallet.dat генерации
    "KeyData",
    "WalletCollectionData",
    "WalletGenSnapshot",
    # Функции захвата
    "capture_key",
    "capture_wallet_collection",
    "capture_wallet_dat_info",
    "create_wallet_gen_snapshot"
]
