# FILE: src/plugins/wallet/batch_gen/__init__.py
# VERSION: 1.0.0

"""
Batch Wallet Generator Plugin Module

Модуль пакетной генерации Bitcoin кошельков.
Генерирует 1000 уникальных кошельков из единого цикла сбора энтропии.

Пример использования:
    from batch_gen import BatchWalletGenerator
    
    generator = BatchWalletGenerator()
    generator.initialize(entropy_data)
    wallets = generator.generate_wallets(count=1000, deterministic=True)
    
    for wallet in wallets.get_all():
        print(f"Address: {wallet.address}")
"""

__version__ = "1.0.0"
__author__ = "Wallet DAT Generator Team"

# Экспорт основных классов и функций
try:
    from .batch_gen_cpp import (
        BatchWalletGenerator,
        BatchWalletGeneratorInterface,
        WalletCollection,
        WalletData,
        WalletDBEntry,
        create,
        get_version,
        DEFAULT_WALLET_COUNT,
        MAX_WALLET_COUNT
    )
    __all__ = [
        'BatchWalletGenerator',
        'BatchWalletGeneratorInterface',
        'WalletCollection',
        'WalletData',
        'WalletDBEntry',
        'create',
        'get_version',
        'DEFAULT_WALLET_COUNT',
        'MAX_WALLET_COUNT'
    ]
except ImportError as e:
    # Если C++ модуль не скомпилирован, предоставляем заглушку
    import warnings
    warnings.warn(f"Could not import C++ extension: {e}. Using Python fallback.")
    
    class WalletData:
        """Заглушка для данных кошелька."""
        def __init__(self):
            self.index = 0
            self.public_key = b''
            self.private_key = b''
            self.address = ''
            self.timestamp = 0
            self.entropy_source = ''
    
    class WalletDBEntry:
        """Заглушка для записи БД."""
        def __init__(self):
            self.key_type = ''
            self.key_data = b''
            self.value_data = b''
    
    class WalletCollection:
        """Заглушка для коллекции кошельков."""
        def __init__(self):
            self.wallets = []
        
        def add_wallet(self, wallet):
            self.wallets.append(wallet)
        
        def get_wallet_at(self, index):
            return self.wallets[index]
        
        def size(self):
            return len(self.wallets)
        
        def clear(self):
            self.wallets = []
        
        def get_all(self):
            return self.wallets
        
        def to_db_entries(self):
            return []
    
    class BatchWalletGenerator:
        """Заглушка для генератора кошельков (требует компиляции C++ модуля)."""
        
        DEFAULT_WALLET_COUNT = 1000
        MAX_WALLET_COUNT = 10000
        
        def __init__(self):
            pass
        
        def initialize(self, entropy_data):
            raise NotImplementedError("C++ module not compiled.")
        
        def generate_wallets(self, count=1000, deterministic=True):
            raise NotImplementedError("C++ module not compiled.")
        
        def get_wallet_at_index(self, index):
            raise NotImplementedError("C++ module not compiled.")
        
        def export_to_db_format(self):
            raise NotImplementedError("C++ module not compiled.")
        
        def get_wallet_count(self):
            return 0
    
    def create():
        """Создать новый экземпляр генератора."""
        return BatchWalletGenerator()
    
    def get_version():
        """Получить версию плагина."""
        return "1.0.0"
    
    __all__ = [
        'BatchWalletGenerator',
        'BatchWalletGeneratorInterface',
        'WalletCollection',
        'WalletData',
        'WalletDBEntry',
        'create',
        'get_version',
        'DEFAULT_WALLET_COUNT',
        'MAX_WALLET_COUNT'
    ]
