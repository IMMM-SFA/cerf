import os
import logging

import yaml


class ReadConfig:
    """Read the configuration YAML file to a dictionary.

        :param config_file:                 Full path with file name and extension to the input config.yml file
        :type config_file:                  str

    """

    def __init__(self, config_file):

        # yaml config file
        self.config_file = config_file

        # read into dict
        self.config = self.get_yaml()

        # generate the technology order that will be use for indexing arrays throughout modeling
        technology_dict = self.config.get('technology')
        self.technology_order = list(technology_dict.keys())

    def get_yaml(self):
        """Read the YAML config file.

        :return:                            YAML config object

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


# m = ReadConfig('/Users/d3y010/Desktop/config.yml')
#
# print(m.technology_order)


