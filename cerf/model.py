"""Model interface for CERF

@author Chris R. vernon
@email chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""


import logging
import time

from cerf.process_state import process_state
from cerf.read_config import ReadConfig
from cerf.stage import Stage


class Model(ReadConfig):
    """Model wrapper for CERF.

    :param config_file:                 Full path with file name and extension to the input config.yml file
    :type config_file:                  str

    """

    # type hints
    config_file: str

    def __init__(self, config_file):

        # start time for model run
        self.start_time = time.time()

        # initialize console handler for logger
        self.console_handler()

        logging.info("Starting CERF model")

        # inherit the configuration reader class attributes
        super(Model, self).__init__(config_file)

    def stage(self):
        """Execute model."""

        # prepare data for use in siting an expansion per state for a target year
        logging.info('Staging data...')

        # initial time for staging data
        staging_t0 = time.time()

        # prepare all data for state level run
        data = Stage(self.settings_dict, self.utility_dict, self.technology_dict, self.technology_order)

        logging.info(f'Staged data in {round((time.time() - staging_t0), 7)} seconds')

        return data

    def run_single_state(self, target_state_name, write_output=True):
        """Execute a single state."""

        # prepare all data for state level run
        data = self.stage()

        sited_arr = process_state(target_state_name=target_state_name,
                                  settings_dict=self.settings_dict,
                                  technology_dict=self.technology_dict,
                                  technology_order=self.technology_order,
                                  expansion_dict=self.expansion_dict,
                                  states_dict=self.states_dict,
                                  suitability_arr=data.suitability_arr,
                                  nlc_arr=data.nlc_arr,
                                  xcoords=data.xcoords,
                                  ycoords=data.ycoords,
                                  randomize=self.settings_dict.get('randomize', True),
                                  seed_value=self.settings_dict.get('seed_value', 0),
                                  verbose=self.settings_dict.get('verbose', False),
                                  write_output=write_output)

        logging.info(f"CERF model run completed in {round(time.time() - self.start_time, 7)}")

        self.close_logger()

        return sited_arr


if __name__ == '__main__':

    import pkg_resources

    c = pkg_resources.resource_filename('cerf', 'tests/data/config.yml')
    m = Model(c).run_single_state(target_state_name='virginia')
