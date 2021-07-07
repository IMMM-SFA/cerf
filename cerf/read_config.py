import logging
import os

import pkg_resources
import yaml

from cerf.logger import Logger


class ReadConfig(Logger):
    """Read the configuration YAML file to a dictionary. Users can optionally pass in individual technology,
    expansion plan, settings, and / or utility zone YAML files that will override the default configuration.

        :param config_file:                 Full path with file name and extension to the input config.yml file
        :type config_file:                  str

    """

    # type hints
    config_file: str

    def __init__(self, config_file):

        # inherit logger class attributes
        super(ReadConfig, self).__init__()

        # yaml config file
        self.config_file = config_file

        # read into dict
        self.config = self.get_yaml()

        # get project level settings
        self.settings_dict = self.config.get('settings')

        # generate the technology order that will be use for indexing arrays throughout modeling
        self.technology_dict = self.config.get('technology')
        self.technology_order = list(self.technology_dict.keys())

        # get the expansion plan
        self.expansion_dict = self.config.get('expansion_plan')

        # get the utility zone data
        self.utility_dict = self.config.get('utility_zones')

        # get the states dictionary
        self.states_dict = self.get_states_dict()

    @staticmethod
    def read_yaml(yaml_file):
        """Read a YAML file."""

        with open(yaml_file, 'r') as yml:
            return yaml.load(yml, Loader=yaml.FullLoader)

    def get_yaml(self):
        """Read the YAML config file.

        :return:                            YAML config object

        """

        # if config file not passed
        if self.config_file is None:
            msg = "Config file must be passed as an argument using:  config_file='<path to config.yml'>"
            logging.error(msg)
            raise AttributeError(msg)

        # check for path exists
        if os.path.isfile(self.config_file):

            return self.read_yaml(self.config_file)

        else:
            msg = f"Config file not found for path:  {self.config_file}"
            logging.error(msg)
            raise FileNotFoundError(msg)

    def get_states_dict(self):
        """Get a dictionary of state name to state ID from the YAML file in package data."""

        # in package data {state_name: state_id}
        states_lookup_file = pkg_resources.resource_filename('cerf', 'data/state-name_to_state-id.yml')

        return self.read_yaml(states_lookup_file)
