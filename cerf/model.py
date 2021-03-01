"""Model interface for CERF

@author Chris R. vernon
@email chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""


import logging
import time

from joblib import Parallel, delayed

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
                                  randomize=self.settings_dict.get('randomize', True),
                                  seed_value=self.settings_dict.get('seed_value', 0),
                                  verbose=self.settings_dict.get('verbose', False),
                                  write_output=write_output)

        self.close_logger()

        return sited_arr


def run_state_parallel(config_file, target_state_name):
    """Initialize the parallel runs."""

    sited_arr = Model(config_file).run_single_state(target_state_name)


def run_all_states(config_file):
    """Run all states in parallel"""

    state_dict = ReadConfig.read_yaml(pkg_resources.resource_filename('cerf', 'data/state-name_to_state-id.yml'))

    results = Parallel(n_jobs=-1, backend='loky')(delayed(run_state_parallel)(config_file, i) for i in ['virginia', 'west_virginia', 'new_jersey', 'kentucky', 'florida', 'new_york', 'georgia', 'oregon', 'rhode_island'])


if __name__ == '__main__':

    import pkg_resources

    c = pkg_resources.resource_filename('cerf', 'tests/data/config.yml')
    # m = Model(c).run_single_state(target_state_name='oregon')
    # m = Model(c).run_all_states()

    run_all_states(c)


