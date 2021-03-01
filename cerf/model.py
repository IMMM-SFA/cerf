"""Model interface for CERF

@author Chris R. vernon
@email chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""


import logging
import time

from cerf.read_config import ReadConfig
from cerf.stage import Stage

from cerf.process_state import process_state


class Model(ReadConfig):

    # type hints
    config_file: str

    def __init__(self, config_file):

        # inherit the configuration reader class attributes
        super(Model, self).__init__(config_file)

        # initialize console handler for logger
        self.console_handler()

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

    def run_all_states(self, write_output=True):
        """Execute model."""

        # prepare all data for state level run
        data = self.stage()

        # run all states
        state_list = ['virginia', 'florida']

        for target_state_name in state_list:

            sited_arr = process_state(target_state_name=target_state_name,
                                      settings_dict=self.settings_dict,
                                      technology_dict=self.technology_dict,
                                      technology_order=self.technology_order,
                                      expansion_dict=self.expansion_dict,
                                      data=data,
                                      randomize=self.settings_dict.get('randomize', True),
                                      seed_value=self.settings_dict.get('seed_value', 0),
                                      verbose=self.settings_dict.get('verbose', False),
                                      write_output=write_output)

        self.close_logger()

    def run_single_state(self, target_state_name, write_output=True):
        """Execute a single state."""

        # prepare all data for state level run
        data = self.stage()

        sited_arr = process_state(target_state_name=target_state_name,
                                  settings_dict=self.settings_dict,
                                  technology_dict=self.technology_dict,
                                  technology_order=self.technology_order,
                                  expansion_dict=self.expansion_dict,
                                  data=data,
                                  randomize=self.settings_dict.get('randomize', True),
                                  seed_value=self.settings_dict.get('seed_value', 0),
                                  verbose=self.settings_dict.get('verbose', False),
                                  write_output=write_output)

        self.close_logger()

        return sited_arr

