# FILE: src/plugins/wallet/address_matcher/__init__.py
# VERSION: 1.0.0
# PURPOSE: Python package initialization for address matcher plugin.

"""
Address Matcher Plugin

C++ implementation of Bitcoin address list comparison using switch-mode algorithm.

The module provides functionality for:
- Loading Bitcoin addresses from files
- Converting between Base58 and binary formats
- Finding intersections between address lists
- Generating address lists from entropy

Usage:
    import address_matcher_cpp as am
    
    # Create instance
    matcher = am.create()
    
    # Load addresses from file
    list2 = matcher.load_addresses_from_file("adr_list/full_list.txt")
    
    # Generate LIST_1 from entropy
    entropy = [0x00] * 32  # 32 bytes of entropy
    list1 = matcher.generate_list1(entropy)
    
    # Find intersections
    result = matcher.find_intersection(list1, list2)
    
    print(f"Matches found: {len(result.matches)}")
    print(f"Mode used: {result.mode_used}")
    print(f"Execution time: {result.execution_time_ms} ms")
"""

# Экспорт основных классов
try:
    from .address_matcher_cpp import (
        AddressMatcher,
        AddressMatcherInterface,
        RawAddress,
        MatchResult,
        create,
        get_version,
        RAW_ADDRESS_SIZE,
        DEFAULT_LIST1_SIZE,
        MAX_LIST_SIZE
    )
except ImportError as e:
    # Если C++ модуль не скомпилирован, предоставляем заглушку
    import warnings
    warnings.warn(f"Could not import C++ extension: {e}. Using Python fallback.")
    
    class RawAddress:
        """Заглушка для сырого адреса."""
        def __init__(self, data: bytes = b''):
            self.data = data
    
    class MatchResult:
        """Заглушка для результата поиска."""
        def __init__(self):
            self.matches = []
            self.mode_used = "none"
            self.execution_time_ms = 0.0
    
    class AddressMatcher:
        """Заглушка для AddressMatcher (требует компиляции C++ модуля)."""
        
        DEFAULT_LIST1_SIZE = 1000
        MAX_LIST_SIZE = 1000000
        
        def __init__(self):
            pass
        
        def load_addresses_from_file(self, filepath: str):
            raise NotImplementedError("C++ module not compiled.")
        
        def generate_list1(self, entropy: list):
            raise NotImplementedError("C++ module not compiled.")
        
        def find_intersection(self, list1: list, list2: set):
            # Простой Python fallback
            result = MatchResult()
            result.matches = [addr for addr in list1 if addr in list2]
            result.mode_used = "python_fallback"
            result.execution_time_ms = 0.0
            return result
    
    class AddressMatcherInterface:
        """Заглушка для интерфейса AddressMatcher."""
        def __init__(self):
            pass
    
    def create():
        """Создать новый экземпляр matcher'а."""
        return AddressMatcher()
    
    def get_version():
        """Получить версию плагина."""
        return "1.0.0"
    
    RAW_ADDRESS_SIZE = 25
    DEFAULT_LIST1_SIZE = 1000
    MAX_LIST_SIZE = 1000000

__version__ = get_version()
__all__ = [
    'AddressMatcher',
    'AddressMatcherInterface',
    'RawAddress',
    'MatchResult',
    'create',
    'get_version',
    'RAW_ADDRESS_SIZE',
    'DEFAULT_LIST1_SIZE',
    'MAX_LIST_SIZE'
]
