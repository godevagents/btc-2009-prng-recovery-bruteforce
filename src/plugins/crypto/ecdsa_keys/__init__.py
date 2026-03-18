# FILE: src/plugins/crypto/ecdsa_keys/__init__.py
# VERSION: 1.0.0

"""
ECDSA Keys Plugin Module

Модуль генерации ECDSA ключей secp256k1 для Bitcoin кошельков.
Полностью соответствует алгоритму из оригинального Bitcoin 0.1.0.

Структура модуля:
    - interface.py: Абстрактный интерфейс ECDSAPluginInterface
    - ecdsa_keys.py: Реализация Secp256k1KeyGenerator

Пример использования:
    from ecdsa_keys import Secp256k1KeyGenerator
    
    generator = Secp256k1KeyGenerator()
    generator.generate_key()
    
    private_key = generator.get_private_key()
    public_key = generator.get_public_key()
    address = generator.get_address()
"""

__version__ = "1.0.0"
__author__ = "Wallet DAT Generator Team"

# Пробуем импортировать из Python модулей
try:
    from .interface import (
        ECDSAPluginInterface,
        ECDSAPluginFactory
    )
    
    from .ecdsa_keys import (
        Secp256k1KeyGenerator,
        create,
        get_version
    )
    
    __all__ = [
        # Интерфейсы
        'ECDSAPluginInterface',
        'ECDSAPluginFactory',
        # Классы
        'Secp256k1KeyGenerator',
        # Функции
        'create',
        'get_version',
        # Константы
        'PRIVATE_KEY_SIZE',
        'PUBLIC_KEY_SIZE',
        'SIGNATURE_SIZE',
        'NID_secp256k1'
    ]
    
except ImportError as e:
    # Если Python модули недоступны, предоставляем заглушку
    import warnings
    warnings.warn(f"Could not import Python modules: {e}. Using fallback.")
    
    # Константы
    PRIVATE_KEY_SIZE = 279
    PUBLIC_KEY_SIZE = 65
    SIGNATURE_SIZE = 72
    NID_secp256k1 = 714
    
    class Secp256k1KeyGenerator:
        """Заглушка для генератора ключей."""
        
        PRIVATE_KEY_SIZE = 279
        PUBLIC_KEY_SIZE = 65
        SIGNATURE_SIZE = 72
        NID_secp256k1 = 714
        
        def __init__(self):
            raise NotImplementedError("Python module not available. Check installation.")
        
        def generate_key(self):
            raise NotImplementedError("Python module not available.")
        
        def get_private_key(self):
            raise NotImplementedError("Python module not available.")
        
        def get_public_key(self):
            raise NotImplementedError("Python module not available.")
        
        def set_private_key(self, private_key):
            raise NotImplementedError("Python module not available.")
        
        def set_public_key(self, public_key):
            raise NotImplementedError("Python module not available.")
        
        def add_entropy(self, data):
            raise NotImplementedError("Python module not available.")
        
        def get_address(self):
            raise NotImplementedError("Python module not available.")
        
        def is_valid(self):
            raise NotImplementedError("Python module not available.")
        
        def get_entropy_pool_size(self):
            return 1043
    
    class ECDSAPluginInterface:
        """Заглушка для интерфейса."""
        pass
    
    class ECDSAPluginFactory:
        """Заглушка для фабрики."""
        pass
    
    def create():
        """Создать новый экземпляр генератора."""
        raise NotImplementedError("Python module not available.")
    
    def get_version():
        """Получить версию плагина."""
        return "1.0.0"
    
    __all__ = [
        'ECDSAPluginInterface',
        'ECDSAPluginFactory',
        'Secp256k1KeyGenerator',
        'create',
        'get_version',
        'PRIVATE_KEY_SIZE',
        'PUBLIC_KEY_SIZE',
        'SIGNATURE_SIZE',
        'NID_secp256k1'
    ]
