"""
Logging Module
Provides structured logging with verbosity levels
"""

import logging
import sys
from typing import Optional


class VibeGuardLogger:
    """Custom logger for VibeGuard with GitHub Actions support"""
    
    def __init__(self, name: str = "vibeguard", level: str = "INFO"):
        """
        Initialize logger
        
        Args:
            name: Logger name
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
    
    def debug(self, message: str) -> None:
        """Log debug message"""
        self.logger.debug(f"🔍 {message}")
    
    def info(self, message: str) -> None:
        """Log info message"""
        self.logger.info(f"📝 {message}")
    
    def warning(self, message: str, file: Optional[str] = None, 
                line: Optional[int] = None) -> None:
        """
        Log warning message with optional GitHub annotation
        
        Args:
            message: Warning message
            file: Optional file path for GitHub annotation
            line: Optional line number for GitHub annotation
        """
        if file:
            location = f"file={file}"
            if line:
                location += f",line={line}"
            print(f"::warning {location}::{message}", file=sys.stdout)
        else:
            self.logger.warning(f"⚠️  {message}")
    
    def error(self, message: str, file: Optional[str] = None, 
              line: Optional[int] = None) -> None:
        """
        Log error message with optional GitHub annotation
        
        Args:
            message: Error message
            file: Optional file path for GitHub annotation
            line: Optional line number for GitHub annotation
        """
        if file:
            location = f"file={file}"
            if line:
                location += f",line={line}"
            print(f"::error {location}::{message}", file=sys.stdout)
        else:
            self.logger.error(f"❌ {message}")
    
    def critical(self, message: str) -> None:
        """Log critical message"""
        self.logger.critical(f"💀 {message}")
    
    def group_start(self, title: str) -> None:
        """
        Start a collapsible group in GitHub Actions
        
        Args:
            title: Group title
        """
        print(f"::group::{title}", file=sys.stdout)
    
    def group_end(self) -> None:
        """End a collapsible group in GitHub Actions"""
        print("::endgroup::", file=sys.stdout)
    
    def set_level(self, level: str) -> None:
        """
        Change logging level
        
        Args:
            level: New logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger.setLevel(getattr(logging, level.upper()))
        for handler in self.logger.handlers:
            handler.setLevel(getattr(logging, level.upper()))


def create_logger(verbose: bool = False, quiet: bool = False) -> VibeGuardLogger:
    """
    Create a configured logger instance
    
    Args:
        verbose: Enable verbose (DEBUG) logging
        quiet: Enable quiet mode (ERROR only)
    
    Returns:
        Configured VibeGuardLogger instance
    """
    if verbose:
        level = "DEBUG"
    elif quiet:
        level = "ERROR"
    else:
        level = "INFO"
    
    return VibeGuardLogger(level=level)
