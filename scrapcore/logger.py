#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging
import sys


class Logger():

    level = logging.INFO
    logger = None

    def setup_logger(self, level=logging.INFO):
        """Configure global log settings"""
        if isinstance(level, int):
            self.level = logging.getLevelName(level)

        self.logger = logging.getLogger()
        self.logger.setLevel(self.level)

        if not len(self.logger.handlers):
            ch = logging.StreamHandler(stream=sys.stderr)
            logformat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            formatter = logging.Formatter(logformat)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def get_logger(self):
        return self.logger
