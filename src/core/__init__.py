# FILE: src/core/__init__.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: Ядро проекта ENTROPY. Содержит алгоритм RAND_add и оркестратор.
# SCOPE: Криминалистическая репликация OpenSSL RAND_add, оркестрация сбора энтропии.
# KEYWORDS: [DOMAIN(10): OpenSSL_Clone; DOMAIN(10): Entropy_Mixing]
# END_MODULE_CONTRACT

from .rand_add import RandAddImplementation
from .orchestrator import EntropyXPOrchestrator

__all__ = ['RandAddImplementation', 'EntropyXPOrchestrator']
