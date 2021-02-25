import os
import logging

import yaml


class ReadConfig:

    def __init__(self, **kwargs):

        # yaml config file
        self.config_file = kwargs.get('config_file', None)

        # read into dict
        self.config = self.get_yaml()

    def get_yaml(self):
        """Read the YAML config file.

        :param config_file:                 Full path with file name and extension to the input config.yml file
        :type config_file:                  str

        :return:                    YAML config object

        """

        # if config file not passed
        if self.config_file is None:
            msg = "Config file must be passed as an argument using:  config_file='<path to config.yml'>"
            logging.info(msg)
            raise AttributeError(msg)

        # check for path exists
        if os.path.isfile(self.config_file):

            with open(self.config_file, 'r') as yml:
                return yaml.load(yml, Loader=yaml.FullLoader)

        else:
            msg = f"Config file not found for path:  {self.config_file}"
            logging.info(msg)
            raise FileNotFoundError(msg)
