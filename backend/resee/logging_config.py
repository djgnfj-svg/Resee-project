"""
Structured JSON logging configuration for Resee application.

This module provides JSON-formatted logging for better log aggregation and analysis.
"""
import json
import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Outputs logs in JSON format for easy parsing by log aggregation tools.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as JSON.

        Args:
            record: LogRecord instance

        Returns:
            JSON-formatted log string
        """
        log_data: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception information if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'value': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }

        # Add custom fields from extra parameter
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'ip_address'):
            log_data['ip_address'] = record.ip_address
        if hasattr(record, 'endpoint'):
            log_data['endpoint'] = record.endpoint
        if hasattr(record, 'method'):
            log_data['method'] = record.method
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        if hasattr(record, 'duration'):
            log_data['duration_ms'] = record.duration

        # Add any other extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'message', 'pathname', 'process', 'processName',
                          'relativeCreated', 'thread', 'threadName', 'exc_info',
                          'exc_text', 'stack_info', 'user_id', 'request_id',
                          'ip_address', 'endpoint', 'method', 'status_code', 'duration']:
                if not key.startswith('_'):
                    # Only add JSON serializable values
                    try:
                        json.dumps(value)
                        log_data[key] = value
                    except (TypeError, ValueError):
                        # Skip non-serializable objects (WSGIRequest, etc.)
                        log_data[key] = str(type(value).__name__)

        return json.dumps(log_data)


class StructuredLogger:
    """
    Wrapper for structured logging with contextual information.

    Usage:
        logger = StructuredLogger('myapp.views')
        logger.info("User logged in", user_id=123, ip_address="127.0.0.1")
    """

    def __init__(self, name: str):
        """
        Initialize structured logger.

        Args:
            name: Logger name (usually module name)
        """
        self.logger = logging.getLogger(name)

    def _log(
        self,
        level: int,
        message: str,
        exc_info: bool = False,
        **kwargs
    ) -> None:
        """
        Internal logging method with extra context.

        Args:
            level: Logging level
            message: Log message
            exc_info: Whether to include exception info
            **kwargs: Additional contextual fields
        """
        self.logger.log(level, message, exc_info=exc_info, extra=kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with context"""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message with context"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with context"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log error message with context"""
        self._log(logging.ERROR, message, exc_info=exc_info, **kwargs)

    def critical(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log critical message with context"""
        self._log(logging.CRITICAL, message, exc_info=exc_info, **kwargs)


def get_structured_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)
