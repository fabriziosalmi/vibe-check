"""
VibeGuard Source Package
Modular code quality scanner
"""

from .rules import RulesManager
from .scanner import CodeScanner, GitScanner, Violation
from .reporter import Reporter
from .logger import create_logger, VibeGuardLogger

__all__ = [
    'RulesManager',
    'CodeScanner',
    'GitScanner',
    'Violation',
    'Reporter',
    'create_logger',
    'VibeGuardLogger'
]

__version__ = '1.4.0'
