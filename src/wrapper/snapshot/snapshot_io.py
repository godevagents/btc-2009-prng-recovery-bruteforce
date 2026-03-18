# FILE: wrapper/snapshot/snapshot_io.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Утилиты ввода-вывода для снапшотов - сохранение, загрузка, сравнение.
# SCOPE: Сериализация, файловый ввод-вывод, сравнение
# INPUT: EntropySnapshot, пути к файлам
# OUTPUT: EntropySnapshot
# KEYWORDS: [DOMAIN(9): IOSerialization; CONCEPT(8): FileIO; TECH(7): Comparison]
# LINKS: [USES(10): wrapper.snapshot.gen_snapshot]
# END_MODULE_CONTRACT
# START_MODULE_MAP:
# FUNC 8 [Сохранение снапшота в файл] => save_snapshot
# FUNC 8 [Загрузка снапшота из файла] => load_snapshot
# FUNC 7 [Сравнение двух снапшотов] => compare_snapshots
# END_MODULE_MAP
# START_USE_CASES:
# - [save_snapshot]: User (Persistence) -> SaveToFile -> SnapshotStored
# - [load_snapshot]: User (Restoration) -> LoadFromFile -> SnapshotLoaded
# - [compare_snapshots]: Auditor (Audit) -> CompareSnapshots -> DifferencesFound
# END_USE_CASES

"""
Утилиты ввода-вывода для снапшотов энтропии.

Предоставляет функции для сохранения, загрузки и сравнения
снапшотов энтропийного состояния в различных форматах.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from src.wrapper.snapshot.gen_snapshot import EntropySnapshot

logger = logging.getLogger(__name__)


# START_FUNCTION_save_snapshot
# START_CONTRACT:
# PURPOSE: Сохранение снапшота в файл в указанном формате.
# INPUTS:
# - snapshot: Снапшот для сохранения => snapshot: EntropySnapshot
# - path: Путь к файлу => path: str
# - format: Формат сохранения ('json' или 'binary') => format: str
# OUTPUTS:
# - None
# SIDE_EFFECTS:
# - Создает файл по указанному пути
# - Перезаписывает существующий файл
# TEST_CONDITIONS_SUCCESS_CRITERIA:
# - Файл создан
# - Файл содержит корректные данные
# KEYWORDS: [DOMAIN(9): Persistence; CONCEPT(7): FileIO; TECH(6): JSON; TECH(6): Binary]
# END_CONTRACT

def save_snapshot(
    snapshot: EntropySnapshot,
    path: str,
    format: str = "json"
) -> None:
    """
    Сохраняет снапшот в файл.
    
    Поддерживает форматы:
    - 'json': Человекочитаемый JSON-формат
    - 'binary': Компактный бинарный формат
    
    Args:
        snapshot: Снапшот для сохранения.
        path: Путь к файлу.
        format: Формат сохранения ('json' или 'binary').
        
    Raises:
        ValueError: Если формат не поддерживается.
        IOError: Если файл не может быть записан.
    """
    # START_BLOCK_VALIDATE_FORMAT: [Валидация формата.]
    logger.info(
        f"[TraceCheck][save_snapshot][ValidateFormat] "
        f"Сохранение снапшота в {path}, формат={format}"
    )
    
    format = format.lower()
    if format not in ("json", "binary"):
        error_msg = f"Неподдерживаемый формат: {format}. Используйте 'json' или 'binary'."
        logger.error(
            f"[VarCheck][save_snapshot][ValidateFormat] "
            f"{error_msg} [FAIL]"
        )
        raise ValueError(error_msg)
    # END_BLOCK_VALIDATE_FORMAT
    
    # START_BLOCK_SAVE: [Сохранение в файл.]
    try:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            # Сериализация в JSON
            data = snapshot.to_dict()
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(
                f"[TraceCheck][save_snapshot][SaveJSON] "
                f"Снапшот сохранен в JSON: {path} [SUCCESS]"
            )
            
        else:  # binary
            # Сериализация в бинарный формат
            binary_data = snapshot.to_binary()
            
            with open(file_path, "wb") as f:
                f.write(binary_data)
            
            logger.info(
                f"[TraceCheck][save_snapshot][SaveBinary] "
                f"Снапшот сохранен в binary: {path} ({len(binary_data)} байт) [SUCCESS]"
            )
            
    except Exception as e:
        logger.error(
            f"[CriticalError][save_snapshot][Save] "
            f"Ошибка сохранения снапшота: {str(e)} [FAIL]"
        )
        raise IOError(f"Не удалось сохранить снапшот: {str(e)}")
    
    # END_BLOCK_SAVE

# END_FUNCTION_save_snapshot


# START_FUNCTION_load_snapshot
# START_CONTRACT:
# PURPOSE: Загрузка снапшота из файла.
# INPUTS:
# - path: Путь к файлу => path: str
# - format: Формат файла ('json' или 'binary') => format: str | None
# OUTPUTS:
# - EntropySnapshot: Загруженный снапшот
# SIDE_EFFECTS:
# - Читает файл с диска
# TEST_CONDITIONS_SUCCESS_CRITERIA:
# - Файл существует
# - Формат корректен
# - Снапшот успешно десериализован
# KEYWORDS: [DOMAIN(9): Restoration; CONCEPT(7): FileIO; TECH(6): JSON; TECH(6): Binary]
# END_CONTRACT

def load_snapshot(
    path: str,
    format: Optional[str] = None
) -> EntropySnapshot:
    """
    Загружает снапшот из файла.
    
    Автоматически определяет формат по расширению файла,
    если формат не указан явно.
    
    Args:
        path: Путь к файлу.
        format: Формат файла ('json' или 'binary').
                Если None, определяется по расширению.
                
    Returns:
        Загруженный объект EntropySnapshot.
        
    Raises:
        FileNotFoundError: Если файл не существует.
        ValueError: Если формат не может быть определен.
        IOError: Если файл не может быть прочитан.
    """
    # START_BLOCK_DETECT_FORMAT: [Определение формата.]
    logger.info(
        f"[TraceCheck][load_snapshot][DetectFormat] "
        f"Загрузка снапшота из {path}"
    )
    
    file_path = Path(path)
    
    if not file_path.exists():
        error_msg = f"Файл не найден: {path}"
        logger.error(
            f"[VarCheck][load_snapshot][DetectFormat] "
            f"{error_msg} [FAIL]"
        )
        raise FileNotFoundError(error_msg)
    
    # Определяем формат
    if format is None:
        suffix = file_path.suffix.lower()
        if suffix in (".json",):
            format = "json"
        elif suffix in (".bin", ".snapshot"):
            format = "binary"
        else:
            # Пробуем определить по содержимому
            with open(file_path, "rb") as f:
                first_bytes = f.read(4)
                if first_bytes == b"SNAP":
                    format = "binary"
                else:
                    format = "json"
    
    format = format.lower()
    logger.info(
        f"[TraceCheck][load_snapshot][DetectFormat] "
        f"Определен формат: {format}"
    )
    # END_BLOCK_DETECT_FORMAT
    
    # START_BLOCK_LOAD: [Загрузка из файла.]
    try:
        if format == "json":
            # Десериализация из JSON
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            snapshot = EntropySnapshot.from_dict(data)
            
            logger.info(
                f"[TraceCheck][load_snapshot][LoadJSON] "
                f"Снапшот загружен из JSON: {path} [SUCCESS]"
            )
            
        elif format == "binary":
            # Десериализация из бинарного формата
            with open(file_path, "rb") as f:
                binary_data = f.read()
            
            snapshot = EntropySnapshot.from_binary(binary_data)
            
            logger.info(
                f"[TraceCheck][load_snapshot][LoadBinary] "
                f"Снапшот загружен из binary: {path} ({len(binary_data)} байт) [SUCCESS]"
            )
            
        else:
            error_msg = f"Неподдерживаемый формат: {format}"
            logger.error(
                f"[VarCheck][load_snapshot][Load] "
                f"{error_msg} [FAIL]"
            )
            raise ValueError(error_msg)
        
        return snapshot
        
    except Exception as e:
        logger.error(
            f"[CriticalError][load_snapshot][Load] "
            f"Ошибка загрузки снапшота: {str(e)} [FAIL]"
        )
        raise IOError(f"Не удалось загрузить снапшот: {str(e)}")
    
    # END_BLOCK_LOAD

# END_FUNCTION_load_snapshot


# START_FUNCTION_compare_snapshots
# START_CONTRACT:
# PURPOSE: Сравнение двух снапшотов и вывод различий.
# INPUTS:
# - a: Первый снапшот => a: EntropySnapshot
# - b: Второй снапшот => b: EntropySnapshot
# OUTPUTS:
# - dict: Словарь с различиями
# SIDE_EFFECTS:
# - None
# TEST_CONDITIONS_SUCCESS_CRITERIA:
# - Оба снапшота валидны
# - Возвращается словарь с результатами сравнения
# KEYWORDS: [DOMAIN(8): Comparison; CONCEPT(7): Diff; TECH(5): Audit]
# END_CONTRACT

def compare_snapshots(
    a: EntropySnapshot,
    b: EntropySnapshot
) -> Dict[str, Any]:
    """
    Сравнивает два снапшота и возвращает различия.
    
    Args:
        a: Первый снапшот.
        b: Второй снапшот.
        
    Returns:
        Словарь с результатами сравнения:
        {
            "identical": bool,
            "differences": [
                {
                    "field": str,
                    "value_a": Any,
                    "value_b": Any
                }
            ],
            "phase_comparison": [
                {
                    "phase_id": int,
                    "identical": bool,
                    "differences": dict
                }
            ]
        }
    """
    # START_BLOCK_COMPARE: [Сравнение снапшотов.]
    logger.info(
        f"[TraceCheck][compare_snapshots][Compare] "
        f"Сравнение снапшотов"
    )
    
    result = {
        "identical": True,
        "differences": [],
        "phase_comparison": []
    }
    
    # START_BLOCK_COMPARE_METADATA: [Сравнение метаданных.]
    # Сравнение версии
    if a.version != b.version:
        result["identical"] = False
        result["differences"].append({
            "field": "version",
            "value_a": a.version,
            "value_b": b.version
        })
        logger.debug(
            f"[VarCheck][compare_snapshots][CompareMetadata] "
            f"version: {a.version} != {b.version}"
        )
    
    # Сравнение timestamp
    if a.timestamp != b.timestamp:
        result["identical"] = False
        result["differences"].append({
            "field": "timestamp",
            "value_a": a.timestamp.isoformat(),
            "value_b": b.timestamp.isoformat()
        })
        logger.debug(
            f"[VarCheck][compare_snapshots][CompareMetadata] "
            f"timestamp: {a.timestamp} != {b.timestamp}"
        )
    # END_BLOCK_COMPARE_METADATA
    
    # START_BLOCK_COMPARE_PHASES: [Сравнение фаз.]
    phases_a = {p.phase_id: p for p in a.phases}
    phases_b = {p.phase_id: p for p in b.phases}
    
    all_phase_ids = set(phases_a.keys()) | set(phases_b.keys())
    
    for phase_id in sorted(all_phase_ids):
        phase_a = phases_a.get(phase_id)
        phase_b = phases_b.get(phase_id)
        
        phase_diff = {
            "phase_id": phase_id,
            "identical": True,
            "differences": {}
        }
        
        if phase_a is None:
            phase_diff["identical"] = False
            phase_diff["differences"]["missing_in_a"] = True
            result["identical"] = False
            
        elif phase_b is None:
            phase_diff["identical"] = False
            phase_diff["differences"]["missing_in_b"] = True
            result["identical"] = False
            
        else:
            # Сравнение данных фаз
            if phase_a.raw_data != phase_b.raw_data:
                phase_diff["identical"] = False
                phase_diff["differences"]["raw_data"] = {
                    "size_a": len(phase_a.raw_data),
                    "size_b": len(phase_b.raw_data)
                }
                result["identical"] = False
            
            if phase_a.hash_value != phase_b.hash_value:
                phase_diff["identical"] = False
                phase_diff["differences"]["hash_value"] = "different"
                result["identical"] = False
            
            if phase_a.entropy_estimate != phase_b.entropy_estimate:
                phase_diff["identical"] = False
                phase_diff["differences"]["entropy_estimate"] = {
                    "a": phase_a.entropy_estimate,
                    "b": phase_b.entropy_estimate
                }
                result["identical"] = False
        
        result["phase_comparison"].append(phase_diff)
    
    # END_BLOCK_COMPARE_PHASES
    
    # START_BLOCK_COMPARE_FINAL_STATE: [Сравнение финального состояния.]
    if a.final_state is None or b.final_state is None:
        if a.final_state != b.final_state:
            result["identical"] = False
            result["differences"].append({
                "field": "final_state",
                "value_a": "None" if a.final_state is None else f"{len(a.final_state)} bytes",
                "value_b": "None" if b.final_state is None else f"{len(b.final_state)} bytes"
            })
    else:
        if a.final_state != b.final_state:
            result["identical"] = False
            result["differences"].append({
                "field": "final_state",
                "value_a": a.final_state.hex()[:32] + "...",
                "value_b": b.final_state.hex()[:32] + "..."
            })
            
            # Сравнение буфера состояния
            if a.get_buffer_state() != b.get_buffer_state():
                result["differences"].append({
                    "field": "buffer_state",
                    "value_a": "different",
                    "value_b": "different"
                })
            
            # Сравнение MD дайджеста
            if a.get_md_digest() != b.get_md_digest():
                result["differences"].append({
                    "field": "md_digest",
                    "value_a": "different",
                    "value_b": "different"
                })
    # END_BLOCK_COMPARE_FINAL_STATE
    
    logger.info(
        f"[TraceCheck][compare_snapshots][Compare] "
        f"Сравнение завершено: identical={result['identical']} [INFO]"
    )
    
    return result
    # END_BLOCK_COMPARE

# END_FUNCTION_compare_snapshots
