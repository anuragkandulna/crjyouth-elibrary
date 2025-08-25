"""
Custom Logger Utility.
Handles logging setup for different parts of the application with production-safe paths.

Simple timestamp handling for SQLite compatibility.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from constants.config import APP_ENV


class SimpleFormatter(logging.Formatter):
    """
    Simple formatter for SQLite-compatible timestamps.
    
    Uses naive datetime objects for consistency across the application.
    """
    def formatTime(self, record, datefmt=None):
        """Override formatTime to use simple datetime."""
        dt = datetime.fromtimestamp(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        else:
            try:
                return dt.isoformat()
            except Exception:
                return str(dt)


class CustomLogger:
    def __init__(self, name=__name__, level=logging.DEBUG, log_file='application.log',
                 max_bytes=500000, backup_count=5):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        if not self.logger.handlers:
            # Use /var/log/ in prod
            log_directory = '/var/log/' if APP_ENV == 'prod' else '.'
            full_log_path = os.path.join(log_directory, log_file)

            # Ensure log directory exists
            if APP_ENV == 'prod' and not os.path.exists('/var/log/'):
                raise RuntimeError("Production log directory '/var/log/' does not exist!")

            # Rotating file handler
            file_handler = RotatingFileHandler(full_log_path, maxBytes=max_bytes, backupCount=backup_count)
            file_handler.setLevel(level)

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)

            # Simple formatter: timestamp - LEVEL - [module] - actual log
            formatter = SimpleFormatter(
                '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
                datefmt='%Y-%m-%dT%H:%M:%SZ'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            # Add handlers
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger
