# FILE: src/plugins/wallet/wallet_dat/__init__.py
# VERSION: 1.0.0

"""
Wallet.dat Plugin Module

Модуль создания wallet.dat формата Berkeley DB.
Полностью соответствует оригинальному формату Bitcoin 0.1.0.

Пример использования:
    from wallet_dat import WalletDatWriter
    from batch_gen import BatchWalletGenerator
    
    # Генерация кошельков
    generator = BatchWalletGenerator()
    generator.initialize(entropy_data)
    wallets = generator.generate_wallets(count=1000)
    
    # Запись в wallet.dat
    writer = WalletDatWriter()
    writer.initialize("/path/to/wallet")
    writer.create_database()
    writer.write_wallet_collection(wallets)
    writer.close()
    
    filepath = writer.get_file_path()
"""

__version__ = "1.0.0"
__author__ = "Wallet DAT Generator Team"

# Экспорт основных классов и функций
try:
    from .wallet_dat_cpp import (
        WalletDatWriter,
        WalletDatWriterInterface,
        create,
        get_version,
        WALLET_VERSION,
        WALLET_FILENAME,
        WALLET_DB_NAME
    )
    __all__ = [
        'WalletDatWriter',
        'WalletDatWriterInterface',
        'create',
        'get_version',
        'WALLET_VERSION',
        'WALLET_FILENAME',
        'WALLET_DB_NAME'
    ]
except ImportError as e:
    # Если C++ модуль не скомпилирован, предоставляем заглушку
    import warnings
    warnings.warn(f"Could not import C++ extension: {e}. Using Python fallback.")
    
    class WalletDatWriter:
        """Заглушка для writer'а wallet.dat (требует компиляции C++ модуля)."""
        
        WALLET_VERSION = 10500
        WALLET_FILENAME = "wallet.dat"
        WALLET_DB_NAME = "main"
        
        def __init__(self):
            self.db_path_ = ""
            self.filename_ = "wallet.dat"
        
        def initialize(self, db_path):
            raise NotImplementedError("C++ module not compiled.")
        
        def create_database(self, filename="wallet.dat"):
            raise NotImplementedError("C++ module not compiled.")
        
        def write_version(self, version=10500):
            raise NotImplementedError("C++ module not compiled.")
        
        def write_default_key(self, pubkey):
            raise NotImplementedError("C++ module not compiled.")
        
        def write_key_pair(self, pubkey, privkey):
            raise NotImplementedError("C++ module not compiled.")
        
        def write_address_book(self, address, name):
            raise NotImplementedError("C++ module not compiled.")
        
        def write_wallet_collection(self, collection):
            raise NotImplementedError("C++ module not compiled.")
        
        def close(self):
            pass
        
        def read_wallet_dat(self, filepath):
            raise NotImplementedError("C++ module not compiled.")
        
        def get_file_path(self):
            import os
            return os.path.join(self.db_path_, self.filename_)
    
    class WalletDatWriterInterface:
        """Заглушка для интерфейса wallet.dat."""
        
        def __init__(self):
            pass
    
    def create():
        """Создать новый экземпляр writer'а."""
        return WalletDatWriter()
    
    def get_version():
        """Получить версию плагина."""
        return "1.0.0"
    
    __all__ = [
        'WalletDatWriter',
        'WalletDatWriterInterface',
        'create',
        'get_version',
        'WALLET_VERSION',
        'WALLET_FILENAME',
        'WALLET_DB_NAME'
    ]
