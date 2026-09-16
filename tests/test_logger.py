"""Tests for the CERF logger.

The model must attach handlers to the ``cerf`` logger only, must not duplicate handlers when several models are
created, must not alter the root logger, and must only remove handlers it created.

"""

import logging
import os
import tempfile
import unittest

from cerf.logger import Logger
from cerf.model import Model


class TestLogger(unittest.TestCase):

    TEST_CONFIG = os.path.join(os.path.dirname(__file__), 'data/test_config_2010.yml')

    def setUp(self):
        Logger.close_logger()
        self.root = logging.getLogger()
        self.root_handlers_before = list(self.root.handlers)
        self.root_level_before = self.root.level

    def tearDown(self):
        Logger.close_logger()

    def _cerf_handlers(self):
        return [h for h in logging.getLogger(Logger.LOGGER_NAME).handlers
                if h.get_name() in (Logger.CONSOLE_HANDLER_NAME, Logger.FILE_HANDLER_NAME)]

    def test_console_handler_is_idempotent(self):
        """Repeated initialisation attaches exactly one console handler."""

        lg = Logger()
        for _ in range(3):
            lg.console_handler('info')

        self.assertEqual(1, len(self._cerf_handlers()))

    def test_root_logger_untouched(self):
        """CERF must not add handlers to, or change the level of, the root logger."""

        Logger().initialize_logger('debug')

        self.assertEqual(self.root_handlers_before, self.root.handlers)
        self.assertEqual(self.root_level_before, self.root.level)

    def test_multiple_models_do_not_duplicate_handlers(self):
        """Instantiating several models in one session yields a single console handler."""

        for _ in range(3):
            Model(config_file=self.TEST_CONFIG)

        self.assertEqual(1, len(self._cerf_handlers()))

    def test_debug_level_applied(self):
        """'debug' sets the handler and logger to DEBUG; 'info' to INFO."""

        lg = Logger()
        handler = lg.console_handler('debug')
        self.assertEqual(logging.DEBUG, handler.level)
        self.assertLessEqual(lg.logger.level, logging.DEBUG)

        handler = lg.console_handler('info')
        self.assertEqual(logging.INFO, handler.level)

    def test_file_handler_writes_log(self):
        """An optional log file receives records emitted through module loggers."""

        with tempfile.TemporaryDirectory() as tmp:
            log_file = os.path.join(tmp, 'cerf.log')
            lg = Logger()
            lg.initialize_logger('info', log_file=log_file)

            logging.getLogger('cerf.some_module').info('hello from cerf')
            Logger.close_logger()

            with open(log_file) as f:
                content = f.read()

        self.assertIn('hello from cerf', content)
        self.assertIn('cerf.some_module', content)

    def test_file_handler_requires_path(self):
        with self.assertRaises(ValueError):
            Logger().file_handler('info')

    def test_close_logger_only_removes_cerf_handlers(self):
        """Handlers the application attached to the cerf logger or the root logger must survive close_logger()."""

        app_handler = logging.NullHandler()
        app_handler.set_name('application')
        cerf_logger = logging.getLogger(Logger.LOGGER_NAME)
        cerf_logger.addHandler(app_handler)

        root_handler = logging.NullHandler()
        self.root.addHandler(root_handler)

        try:
            Logger().initialize_logger('info')
            self.assertEqual(1, len(self._cerf_handlers()))

            Logger.close_logger()

            self.assertEqual(0, len(self._cerf_handlers()))
            self.assertIn(app_handler, cerf_logger.handlers)
            self.assertIn(root_handler, self.root.handlers)

        finally:
            cerf_logger.removeHandler(app_handler)
            self.root.removeHandler(root_handler)

    def test_close_logger_does_not_shutdown_logging(self):
        """Closing CERF's handlers must leave the logging system usable for the host application."""

        Logger().initialize_logger('info')
        Logger.close_logger()

        stream_handler = logging.StreamHandler()
        self.root.addHandler(stream_handler)
        try:
            # would raise if logging had been shut down and handlers closed underneath us
            logging.getLogger('other.app').warning('still alive')
        finally:
            self.root.removeHandler(stream_handler)


if __name__ == '__main__':
    unittest.main()
