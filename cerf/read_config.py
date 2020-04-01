"""Configuration reader for CERF

@author Chris R. vernon
@email chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""
import yaml


class ReadConfig:
    """Read configuration data either provided in the configuration YAML file or as passed in via arguments.
    :param config_file:                         string. Full path to configuration YAML file with file name and
                                                extension. If not provided by the user, the code will default to the
                                                expectation of alternate arguments.

    """

    def __init__(self, config_file=None, biomass_directory=None, nuclear_directory=None):

        if config_file is None:

            self.biomass_directory = biomass_directory
            self.nuclear_directory = nuclear_directory

        else:

            # extract config file to YAML object
            cfg = self.get_yaml(config_file)

            cfg_suitability = self.validate_key(cfg, 'suitability')

            self.biomass_directory = cfg_suitability['biomass_directory']
            self.nuclear_directory = cfg_suitability['nuclear_directory']

    @staticmethod
    def validate_key(yaml_object, key):
        """Check to see if key is in YAML file, if not return None"""
        try:
            return yaml_object[key]
        except KeyError:
            return None

    @staticmethod
    def get_yaml(config_file):
        """Read the YAML config file
        :param config_file:         Full path with file name and extension to the input config.yml file
        :return:                    YAML config object
        """
        with open(config_file, 'r') as yml:
            return yaml.load(yml)
