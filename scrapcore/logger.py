#!/usr/bin/python3
import logging
import sys


class Logger:
    """Configures and provides a global logger instance."""

    def __init__(self):
        self.level = logging.INFO
        self.logger = None

    def setup_logger(self, level: int = logging.INFO):
        """Configure global log settings."""
        if isinstance(level, int):
            self.level = level
        elif isinstance(level, str):
            self.level = logging.getLevelName(level.upper())
        else:
            self.level = logging.INFO

        self.logger = logging.getLogger()
        self.logger.setLevel(self.level)

        if not self.logger.handlers:
            ch = logging.StreamHandler(stream=sys.stderr)
            logformat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            formatter = logging.Formatter(logformat)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def get_logger(self) -> logging.Logger:
        return self.logger
