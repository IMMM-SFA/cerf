"""Logger for CERF model.

Copyright (c) 2018, Battelle Memorial Institute

Open source under license BSD 2-Clause - see LICENSE and DISCLAIMER

@author:  Chris R. Vernon (chris.vernon@pnnl.gov)

"""

import logging
import sys


class Logger:
    """Manage the package-wide ``cerf`` logger.

    All CERF modules log through ``logging.getLogger(__name__)``, which makes them children of the ``cerf`` logger.
    Handlers are attached to that named logger only, so CERF never modifies the root logger, never changes the level
    of third-party libraries and never removes handlers it did not create. Attaching handlers is idempotent: creating
    several models in one session does not duplicate log lines.

    """

    # name of the package logger; module loggers (``cerf.stage`` etc.) propagate to it
    LOGGER_NAME = 'cerf'

    # handler names used to recognise handlers owned by CERF
    CONSOLE_HANDLER_NAME = 'cerf-console'
    FILE_HANDLER_NAME = 'cerf-file'

    # output format for log string
    LOG_FORMAT_STRING = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    @property
    def log_format(self):
        """Generate log formatter."""

        return logging.Formatter(self.LOG_FORMAT_STRING)

    @property
    def logger(self):
        """The ``cerf`` package logger."""

        return logging.getLogger(self.LOGGER_NAME)

    @staticmethod
    def resolve_level(log_level):
        """Translate the user-facing ``log_level`` string ('info' or 'debug') to a ``logging`` level."""

        if str(log_level).lower() == 'debug':
            return logging.DEBUG

        return logging.INFO

    def initialize_logger(self, log_level='info', log_file=None):
        """Attach the console handler and, optionally, a file handler.

        :param log_level:               Log level.  Options are 'info' and 'debug'.  Default 'info'
        :type log_level:                str

        :param log_file:                Optional path to a log file. If given, log records are also written there.
        :type log_file:                 str

        """

        self.console_handler(log_level)

        if log_file is not None:
            self.file_handler(log_level, log_file)

    def _get_handler(self, name):
        """Return the CERF-owned handler with ``name`` if it is attached, otherwise ``None``."""

        for handler in self.logger.handlers:
            if handler.get_name() == name:
                return handler

        return None

    def _attach_handler(self, handler, name, log_level):
        """Configure ``handler`` and attach it to the ``cerf`` logger, replacing any previous handler of that name."""

        level = self.resolve_level(log_level)

        existing = self._get_handler(name)
        if existing is not None:
            existing.close()
            self.logger.removeHandler(existing)

        handler.set_name(name)
        handler.setLevel(level)
        handler.setFormatter(self.log_format)

        self.logger.addHandler(handler)

        # the logger level must be at least as permissive as the most verbose handler
        if self.logger.level == logging.NOTSET or self.logger.level > level:
            self.logger.setLevel(level)

        return handler

    def console_handler(self, log_level='info'):
        """Attach a stdout handler to the ``cerf`` logger (idempotent)."""

        return self._attach_handler(logging.StreamHandler(sys.stdout), self.CONSOLE_HANDLER_NAME, log_level)

    def file_handler(self, log_level='info', log_file=None):
        """Attach a file handler to the ``cerf`` logger (idempotent)."""

        if log_file is None:
            raise ValueError("`log_file` must be provided to attach a file handler.")

        return self._attach_handler(logging.FileHandler(log_file), self.FILE_HANDLER_NAME, log_level)

    @classmethod
    def close_logger(cls):
        """Detach and close the handlers CERF attached to the ``cerf`` logger.

        Handlers owned by the application (on the root logger or elsewhere) are left untouched.

        """

        logger = logging.getLogger(cls.LOGGER_NAME)

        for handler in logger.handlers[:]:
            if handler.get_name() in (cls.CONSOLE_HANDLER_NAME, cls.FILE_HANDLER_NAME):
                handler.close()
                logger.removeHandler(handler)
