"""
Custom Logger Utility.
Handles logging setup for different parts of the application with production-safe paths.

OWASP Compliance: All log timestamps use UTC timezone for security incident correlation
and consistency across distributed systems.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from constants.config import APP_ENV


class UTCFormatter(logging.Formatter):
    """
    OWASP-compliant formatter that enforces UTC timestamps.
    
    Ensures all log timestamps use UTC timezone regardless of system timezone,
    meeting OWASP security logging requirements for incident correlation.
    """
    def formatTime(self, record, datefmt=None):
        """Override formatTime to always use UTC timezone."""
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        if datefmt:
            return dt.strftime(datefmt)
        else:
            return dt.isoformat()


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

            # OWASP-compliant UTC formatter: timestamp - LEVEL - [module] - actual log
            formatter = UTCFormatter(
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
