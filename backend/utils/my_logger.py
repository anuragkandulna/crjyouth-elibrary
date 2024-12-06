"""
Logger model.
"""

import logging
from logging.handlers import RotatingFileHandler

class CustomLogger:
    def __init__(self, name=__name__, level=logging.DEBUG, log_file='application.log', max_bytes=500000, backup_count=5):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Check if handlers are already added to avoid duplicate logs
        if not self.logger.handlers:
            # Create a rotating file handler
            file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
            file_handler.setLevel(level)

            # Create a console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)

            # Create a formatter and set it for both handlers
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            # Add the handlers to the logger
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger