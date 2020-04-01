"""Model interface for CERF

@author Chris R. vernon
@email chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""
import logging
import os
import datetime
import time
import sys

from cerf.read_config import ReadConfig
from cerf.process_step import ProcessStep


class Model:
    """Run CERF

    :param config_file:                         string. Full path to configuration YAML file with file name and
                                                extension. If not provided by the user, the code will default to the
                                                expectation of alternate arguments.

    """
    def __init__(self, config_file=None):

        # get current time
        self.date_time_string = datetime.datetime.now().strftime('%Y-%m-%d_%Hh%Mm%Ss')

        # read the YAML configuration file
        self.cfg = ReadConfig(config_file=config_file)

        # expose key variables that we want the user to have non-nested access to
        self.discount_rate = 0.12
        self.carbon_tax = 0.0
        self.carbon_tax_escalation = 0.0

        # logfile path
        self.logfile = os.path.join(self.cfg.output_directory, 'logfile_{}_{}.log'.format(self.cfg.scenario,
                                                                                             self.date_time_string))

        # set up time step generator
        self.timestep = self.build_step_generator()

    @staticmethod
    def make_dir(pth):
        """Create dir if not exists."""

        if not os.path.exists(pth):
            os.makedirs(pth)

    def init_log(self):
        """Initialize project-wide logger. The logger outputs to both stdout and a file."""

        log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_level = logging.INFO

        logger = logging.getLogger()
        logger.setLevel(log_level)

        # logger console handler
        c_handler = logging.StreamHandler(sys.stdout)
        c_handler.setLevel(log_level)
        c_handler.setFormatter(log_format)
        logger.addHandler(c_handler)

        # logger file handler
        f_handler = logging.FileHandler(self.logfile)
        c_handler.setLevel(log_level)
        c_handler.setFormatter(log_format)
        logger.addHandler(f_handler)

    def initialize(self):
        """Setup model."""

        # build output directory first to store logfile and other outputs
        self.make_dir(self.cfg.output_directory)

        # initialize logger
        self.init_log()

        logging.info("Start time:  {}".format(time.strftime("%Y-%m-%d %H:%M:%S")))

        # log run parameters
        logging.info("Input parameters:")
        logging.info("\tdiscount_rate = {}".format(self.cfg.discount_rate))
        logging.info("\tcarbon_tax = {}".format(self.cfg.carbon_tax))
        logging.info("\tcarbon_tax_escalation = {}".format(self.cfg.carbon_tax_escalation))

    def build_step_generator(self):
        """Build step generator."""

        for step in self.cfg.steps:

            yield ProcessStep(step, self.cfg)

    def advance_step(self):
        """Advance to next time step.
        Python 3 requires the use of `next()` to wrap the generator.
        """

        next(self.timestep)

    def run_model(self):
        """Downscale rural and urban projection for all input years"""

        # initialize model
        self.initialize()

        # start time
        td = time.time()

        logging.info("Starting downscaling.")

        # process all years
        for _ in self.cfg.steps:
            self.advance_step()

        logging.info("Downscaling completed in {} minutes.".format((time.time() - td) / 60))

        # clean logger
        self.close()

    def close(self):
        """End model run and close log files"""

        logging.info("End time:  {}".format(time.strftime("%Y-%m-%d %H:%M:%S")))

        # Remove logging handlers
        logger = logging.getLogger()

        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

        logging.shutdown()
