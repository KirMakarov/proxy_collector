# -*- coding: utf-8 -*-

"""Logging module.

:Logger: Writes system state to log files
"""

import os

from logging import Formatter, getLogger, FileHandler, StreamHandler
from logging import INFO, DEBUG


class Logger:
    """Writes system state to log files."""

    def __init__(self, name=None):
        self.__name = name
        self.__loggers = {'file': self.__file_logger,
                          'console': self.__console_logger
                          }
        self.__log_level = {'info': INFO, 'debug': DEBUG}
        self.__mode = None
        self.__logs_path = ''
        self.__common_log_handler = None
        self.__console_log_handler = None
        self.__log_format = None

        self.__logger = getLogger(self.__name)

        self.info = self.__logger.info
        self.debug = self.__logger.debug
        self.warning = self.__logger.warning
        self.error = self.__logger.error
        self.critical = self.__logger.critical

    def set_logs(self, mode=None, message_level='info', logs_path=None):
        """Set logger handlers."""
        if not self.__mode and mode:
            if mode not in self.__loggers:
                raise ValueError('Mode "{}" is not support'.format(mode))
            self.__mode = mode
        if mode == 'file':
            if not logs_path:
                raise ValueError('"logs_path" should not be None')
            self.__logs_path = logs_path

        self.__logger.setLevel(self.__log_level[message_level])

        message_format = '%(levelname)-8s %(asctime)s (%(filename)s:%(lineno)d) %(message)-40s'
        self.__log_format = Formatter(fmt=message_format, datefmt="%y-%m-%d %H:%M:%S")
        self.__loggers.get(self.__mode).__call__()

    def __file_logger(self):
        """Create and start loggers file handler."""
        log_file = '{0}/{1}.log'.format(self.__logs_path, self.__name)

        # Existing log rewriting
        if os.path.exists(log_file):
            os.remove(log_file)

        self.__common_log_handler = FileHandler(log_file, mode='w', encoding='utf-8')
        self.__common_log_handler.setFormatter(self.__log_format)

        self.__logger.addHandler(self.__common_log_handler)

    def __console_logger(self):
        """Create and start loggers console handler."""
        self.__console_log_handler = StreamHandler()
        self.__console_log_handler.setFormatter(self.__log_format)
        self.__logger.addHandler(self.__console_log_handler)

    def close_logs(self):
        """Close logger handlers."""
        if self.__mode == 'file':
            self.__common_log_handler.close()
            self.__logger.removeHandler(self.__common_log_handler)
        elif self.__mode == 'console':
            self.__console_log_handler.close()
            self.__logger.removeHandler(self.__console_log_handler)

        self.__mode = None
