# FILE: src/plugins/cpu/rand_poll/__init__.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT:
# PURPOSE: CPU плагин RAND_poll. Реконструкция RAND_poll() для Windows XP SP3.
# SCOPE: Эмуляция 5 фаз сбора энтропии: NetAPI, CryptoAPI, User32, Toolhelp32, Kernel32.
# KEYWORDS: [DOMAIN(10): Forensics; DOMAIN(9): OpenSSL_Legacy; TECH(8): Windows_API]
# END_MODULE_CONTRACT

from .poll import RandPollReconstructorXP, cuda_execute_poll, cuda_check_availability

__all__ = ['RandPollReconstructorXP', 'cuda_execute_poll', 'cuda_check_availability']
