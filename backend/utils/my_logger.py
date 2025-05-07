"""
Custom Logger Utility.
Handles logging setup for different parts of the application with production-safe paths.
"""

import logging
from logging.handlers import RotatingFileHandler
import os


class CustomLogger:
    def __init__(self, name=__name__, level=logging.DEBUG, log_file='application.log',
                 max_bytes=500000, backup_count=5):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        if not self.logger.handlers:
            # Use /var/log/ in production
            log_directory = '/var/log/' if os.getenv('FLASK_ENV') == 'production' else '.'
            full_log_path = os.path.join(log_directory, log_file)

            # Ensure log directory exists
            if os.getenv('FLASK_ENV') == 'production' and not os.path.exists('/var/log/'):
                raise RuntimeError("Production log directory '/var/log/' does not exist!")

            # Rotating file handler
            file_handler = RotatingFileHandler(full_log_path, maxBytes=max_bytes, backupCount=backup_count)
            file_handler.setLevel(level)

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)

            # Formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            # Add handlers
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger
