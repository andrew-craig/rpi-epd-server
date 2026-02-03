#!/usr/bin/env python3
"""
Centralized logging configuration for rpi-epd-server.
Provides JSON-formatted structured logging for better observability.
"""

import datetime
import json
import logging
import sys


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    # Standard logging record attributes to exclude from metadata
    RESERVED_ATTRS = {
        'name', 'msg', 'args', 'created', 'filename', 'funcName', 'levelname',
        'levelno', 'lineno', 'module', 'msecs', 'message', 'pathname', 'process',
        'processName', 'relativeCreated', 'thread', 'threadName', 'exc_info',
        'exc_text', 'stack_info', 'getMessage', 'getMessage'
    }

    def format(self, record):
        """
        Format log record as JSON.

        Args:
            record: LogRecord instance

        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": "rpi-epd-server",
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add any extra fields that were passed to the logger
        for key, value in record.__dict__.items():
            if key not in self.RESERVED_ATTRS and not key.startswith('_'):
                log_data[key] = value

        return json.dumps(log_data)


def setup_logging(level=logging.INFO):
    """
    Configure structured JSON logging for the application.

    Args:
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    logger = logging.getLogger()
    logger.handlers.clear()  # Remove any existing handlers
    logger.addHandler(handler)
    logger.setLevel(level)

    return logger
