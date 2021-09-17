import logging
import os

import yaml

import cerf.utils as utils
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

        # update the settings paths to the package defaults if settings are not declared
        region_raster_file = self.settings_dict.get('region_raster_file', None)
        region_abbrev_to_name_file = self.settings_dict.get('region_abbrev_to_name_file', None)
        region_name_to_id_file = self.settings_dict.get('region_name_to_id_file', None)

        if region_raster_file is None:
            self.settings_dict.update({'region_raster_file': pkg.cerf_regions_raster()})

        if region_abbrev_to_name_file is None:
            self.settings_dict.update({'region_abbrev_to_name_file': pkg.get_region_abbrev_to_name_file()})

        if region_name_to_id_file is None:
            self.settings_dict.update({'region_name_to_id_file': pkg.get_region_name_to_id()})

        # validate file existence
        self.validate_settings_files()
        self.validate_lmp_files()
        self.validate_technology_files()
        self.validate_infrastructure_files()

        # get the regions dictionary
        self.regions_dict = self.get_regions_dict()

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
            msg = f"""Config file not found for path:  {self.config_file}. If using defaults, please download the package data. 
            See https://immm-sfa.github.io/cerf/getting_started.html#install-package-data"""

            logging.error(msg)
            raise FileNotFoundError(msg)

    def get_regions_dict(self):
        """Get a dictionary of region name to region ID from the YAML file in package data."""

        # in package data {region_name: region_id}
        regions_lookup_file = self.settings_dict.get('region_name_to_id_file')

        return self.read_yaml(regions_lookup_file)

    def validate_settings_files(self):
        """Ensure that files necessary files exists for settings."""

        # expected files from settings
        settings_files = [self.settings_dict['region_raster_file'],
                          self.settings_dict['region_abbrev_to_name_file'],
                          self.settings_dict['region_name_to_id_file']]

        for i in settings_files:
            if not os.path.isfile(i):
                msg = f"""Cannot find the settings file for: {i}.  If using defaults, please download the package data. 
                See https://immm-sfa.github.io/cerf/getting_started.html#install-package-data"""

                raise FileNotFoundError(msg)

    def validate_technology_files(self):
        """Ensure that files necessary files exists for technology."""

        # expected files from technology
        suitability_file_dict = utils.default_suitabiity_files()

        for i in self.technology_dict.keys():

            suitability_raster = self.technology_dict[i]['suitability_raster_file']
            tech_name = self.technology_dict[i]['tech_name']

            # see if the default suitability file exists in the data directory
            if suitability_raster is None:

                suit_path = os.path.join(pkg.get_data_directory(), suitability_file_dict[tech_name])

                if not os.path.isfile(suit_path):
                    msg = f"""Cannot find the default suitability raster: {suit_path}.  Please download the package data. 
                    See https://immm-sfa.github.io/cerf/getting_started.html#install-package-data"""

                    raise FileNotFoundError(msg)

            # if user provides suitability data, validate
            else:

                if not os.path.isfile(suitability_raster):
                    msg = f"Cannot find the suitability raster: {suitability_raster}.  Confirm existence and retry."

                    raise FileNotFoundError(msg)

    def validate_lmp_files(self):
        """Ensure that files necessary files exists for LMP zones."""

        lmp_zone_raster_file = self.lmp_zone_dict.get('lmp_zone_raster_file', None)
        lmp_hourly_data_file = self.lmp_zone_dict.get('lmp_hourly_data_file', None)

        if lmp_zone_raster_file is None:
            lmp_zone_raster_file = pkg.sample_lmp_zones_raster_file()

        if lmp_hourly_data_file is None:
            lmp_hourly_data_file = pkg.get_sample_lmp_file()

        lmp_files = [lmp_zone_raster_file, lmp_hourly_data_file]

        for i in lmp_files:

            if not os.path.isfile(i):
                msg = f"""Cannot find the LMP file for: {i}.  If using defaults, please download the package data. 
                See https://immm-sfa.github.io/cerf/getting_started.html#install-package-data"""

                raise FileNotFoundError(msg)

    def validate_infrastructure_files(self):
        """Ensure that files necessary files exists for infrastructure."""

        # expected files from lmp_zones
        infrastructure_files = [self.infrastructure_dict.get('substation_file', pkg.get_substation_file()),
                                self.infrastructure_dict.get('pipeline_file', pkg.get_default_gas_pipelines()),
                                self.infrastructure_dict.get('transmission_costs_file', pkg.get_costs_per_kv_substation_file()),
                                self.infrastructure_dict.get('pipeline_costs_file', pkg.get_costs_gas_pipeline())]

        substation_file = self.infrastructure_dict.get('substation_file', None)
        pipeline_file = self.infrastructure_dict.get('pipeline_file', None)
        transmission_costs_file = self.infrastructure_dict.get('transmission_costs_file', None)
        pipeline_costs_file = self.infrastructure_dict.get('pipeline_costs_file', None)

        if substation_file is None:
            substation_file = pkg.get_substation_file()

        if pipeline_file is None:
            pipeline_file = pkg.get_default_gas_pipelines()

        if transmission_costs_file is None:
            transmission_costs_file = pkg.get_costs_per_kv_substation_file()

        if pipeline_costs_file is None:
            pipeline_costs_file = pkg.get_costs_gas_pipeline()

        infrastructure_files = [substation_file, pipeline_file, transmission_costs_file, pipeline_costs_file]

        for i in infrastructure_files:

            if not os.path.isfile(i):
                msg = f"""Cannot find the infrastructure file for: {i}.  If using defaults, please download the package data. 
                See https://immm-sfa.github.io/cerf/getting_started.html#install-package-data"""

                raise FileNotFoundError(msg)
