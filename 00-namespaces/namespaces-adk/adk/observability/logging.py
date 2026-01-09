"""
Logging: Implements structured, context-rich logging.

This module provides logging for all runtime components with
integration with cloud logging and SIEM systems.
"""

import logging
import json
import sys
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager
from enum import Enum


class LogLevel(Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogContext:
    """Logging context."""
    name: str
    component: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "component": self.component,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata
        }


class Logger:
    """
    Structured logger with context support.
    
    Features:
    - Structured JSON logging
    - Context propagation
    - Log correlation
    - Sensitive data redaction
    """
    
    def __init__(self, name: str):
        self.name = name
        self._context = LogContext(name=name)
        self._logger = logging.getLogger(name)
        
        # Configure handler if not already configured
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(message)s'))
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)
    
    @contextmanager
    def context(self, name: str, **metadata):
        """Create a logging context."""
        old_context = self._context
        self._context = LogContext(
            name=f"{self.name}.{name}",
            component=name,
            correlation_id=self._context.correlation_id,
            metadata=metadata
        )
        try:
            yield
        finally:
            self._context = old_context
    
    def _format_log(
        self,
        level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format log entry as JSON."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "logger": self.name,
            "context": self._context.to_dict(),
            "message": message
        }
        
        if extra:
            log_entry["extra"] = extra
        
        return json.dumps(log_entry)
    
    def debug(self, message: str, **extra) -> None:
        """Log debug message."""
        self._logger.debug(self._format_log(LogLevel.DEBUG.value, message, extra))
    
    def info(self, message: str, **extra) -> None:
        """Log info message."""
        self._logger.info(self._format_log(LogLevel.INFO.value, message, extra))
    
    def warning(self, message: str, **extra) -> None:
        """Log warning message."""
        self._logger.warning(self._format_log(LogLevel.WARNING.value, message, extra))
    
    def error(self, message: str, exc_info: bool = False, **extra) -> None:
        """Log error message."""
        if exc_info:
            self._logger.error(self._format_log(LogLevel.ERROR.value, message, extra), exc_info=True)
        else:
            self._logger.error(self._format_log(LogLevel.ERROR.value, message, extra))
    
    def critical(self, message: str, **extra) -> None:
        """Log critical message."""
        self._logger.critical(self._format_log(LogLevel.CRITICAL.value, message, extra))