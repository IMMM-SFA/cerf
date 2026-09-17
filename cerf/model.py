"""Model interface for CERF

@author Chris R. vernon
@email chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""


import logging
import time

from cerf.process_region import process_region
from cerf.read_config import ReadConfig
from cerf.stage import Stage

logger = logging.getLogger(__name__)


class Model(ReadConfig):
    """Model wrapper for CERF.

    :param config_file:                 Full path with file name and extension to the input config.yml file
    :type config_file:                  str

    :param config_dict:                 Optional instead of config_file. Configuration dictionary.
    :type config_dict:                  dict

    :param initialize_site_data:        None if no initialization is required, otherwise either a CSV file or
                                        Pandas DataFrame of siting data bearing the following required fields:

                                        xcoord:  the X coordinate of the site in meters in
                                        USA_Contiguous_Albers_Equal_Area_Conic (EPSG:  102003)

                                        ycoord:  the Y coordinate of the site in meters in
                                        USA_Contiguous_Albers_Equal_Area_Conic (EPSG:  102003)

                                        retirement_year:  the year (int four digit, e.g., 2050) that the power
                                        plant is to be decommissioned

                                        buffer_in_km:  the buffer around the site to apply in kilometers

    :param log_level:                   Log level.  Options are 'info' and 'debug'.  Default 'info'
    :type log_level:                    str

    :param log_file:                    Optional path to a log file to write to in addition to stdout.
    :type log_file:                     str

    """

    def __init__(self, config_file=None, config_dict=None, initialize_site_data=None, log_level='info',
                 log_file=None):

        # start time for model run
        self.start_time = time.time()

        # attach CERF's handlers to the `cerf` logger (idempotent; never touches the root logger)
        self.initialize_logger(log_level=log_level, log_file=log_file)

        logger.info("Starting CERF model")

        # inherit the configuration reader class attributes
        super(Model, self).__init__(config_file, config_dict)

        # siting data to use as the initial condition
        self.initialize_site_data = initialize_site_data

    def stage(self):
        """run model."""

        # prepare data for use in siting an expansion per region for a target year
        logger.info('Staging data...')

        # initial time for staging data
        staging_t0 = time.time()

        # prepare all data for region level run
        data = Stage(self.settings_dict,
                     self.lmp_zone_dict,
                     self.technology_dict,
                     self.technology_order,
                     self.infrastructure_dict,
                     self.initialize_site_data)

        logger.info(f'Staged data in {round((time.time() - staging_t0), 7)} seconds')

        return data

    def run_single_region(self, target_region_name, write_output=True):
        """run a single region."""

        # prepare all data for region level run
        data = self.stage()

        process = process_region(target_region_name=target_region_name,
                                 settings_dict=self.settings_dict,
                                 technology_dict=self.technology_dict,
                                 technology_order=self.technology_order,
                                 expansion_dict=self.expansion_dict,
                                 regions_dict=self.regions_dict,
                                 suitability_arr=data.suitability_arr,
                                 lmp_arr=data.lmp_arr,
                                 generation_arr=data.generation_arr,
                                 operating_cost_arr=data.operating_cost_arr,
                                 nov_arr=data.nov_arr,
                                 ic_arr=data.ic_arr,
                                 nlc_arr=data.nlc_arr,
                                 zones_arr=data.zones_arr,
                                 xcoords=data.xcoords,
                                 ycoords=data.ycoords,
                                 indices_2d=data.indices_2d,
                                 randomize=self.settings_dict.get('randomize', True),
                                 seed_value=self.settings_dict.get('seed_value', 0),
                                 verbose=self.settings_dict.get('verbose', False),
                                 write_output=write_output,
                                 regions_arr=data.regions_arr,
                                 region_bounds=data.region_bounds)

        logger.info(f"CERF model run completed in {round(time.time() - self.start_time, 7)} seconds")

        self.close_logger()

        return process
