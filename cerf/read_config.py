import logging
import os

import yaml

import cerf.package_data as pkg
from cerf.logger import Logger


class ReadConfig(Logger):
    """Read the configuration YAML file to a dictionary. Users can optionally pass in a configuration dictionary
    instead.

        :param config_file:                 Full path with file name and extension to the input config.yml file
        :type config_file:                  str

        :param config_dict:                 Configuration dictionary.
        :type config_dict:                  dict

    """

    # type hints
    config_file: str

    def __init__(self, config_file=None, config_dict={}):

        # inherit logger class attributes
        super(ReadConfig, self).__init__()

        if config_file is None and config_dict is not None:
            self.config = config_dict

        else:

            # yaml config file
            self.config_file = config_file

            # read into dict
            self.config = self.get_yaml()

        # get project level settings
        self.settings_dict = self.config.get('settings')
        self.settings_dict.update(config_dict.get('settings', {}))

        # generate the technology order that will be use for indexing arrays throughout modeling
        self.technology_dict = self.config.get('technology')
        self.technology_dict.update(config_dict.get('technology', {}))

        self.technology_order = list(self.technology_dict.keys())

        # get the expansion plan
        self.expansion_dict = self.config.get('expansion_plan')
        self.expansion_dict.update(config_dict.get('expansion_plan', {}))

        # get the lmp zones settings
        self.lmp_zone_dict = self.config.get('lmp_zones')
        self.lmp_zone_dict.update(config_dict.get('lmp_zones', {}))

        # get the infrastructure settings
        self.infrastructure_dict = self.config.get('infrastructure', {})
        self.infrastructure_dict.update(config_dict.get('infrastructure', {}))

        # get the regions dictionary
        self.regions_dict = self.get_regions_dict()

        # update the settings paths to the package defaults if settings are not declared
        region_raster_file = self.settings_dict.get('region_raster_file', None)
        region_abbrev_to_name_file = self.settings_dict.get('region_abbrev_to_name_file', None)
        region_name_to_id_file = self.settings_dict.get('region_name_to_id_file', None)

        if region_raster_file is None:
            self.settings_dict.update({'region_raster_file': pkg.cerf_regions_raster()})

        if region_abbrev_to_name_file is None:
            self.settings_dict.update({'region_abbrev_to_name_file': pkg.get_region_abbrev_to_name()})

        if region_name_to_id_file is None:
            self.settings_dict.update({'region_name_to_id_file': pkg.get_region_name_to_id()})

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

    def get_regions_dict(self):
        """Get a dictionary of region name to region ID from the YAML file in package data."""

        # in package data {region_name: region_id}
        regions_lookup_file = pkg.get_region_name_to_id()

        return self.read_yaml(regions_lookup_file)

    # TODO
    def validate_file_exists(self):
        """Ensure that files necessary to run the package exists."""

        pass
