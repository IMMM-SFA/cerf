"""Stage data for CERF run.

@author Chris R. vernon
@email chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

import logging

import numpy as np
import pandas as pd
import pkg_resources
import rasterio

import cerf.utils as util
from cerf.lmp import LocationalMarginalPricing
from cerf.nov import NetOperationalValue
from cerf.interconnect import Interconnection


class Stage:

    # type hints
    settings_dict: dict
    utility_dict: dict
    technology_dict: dict
    technology_order: list

    # dictionary of size kV line needed to connect to power plant unit size in MW
    KV_TO_MW_REQUIREMENT = {230: {'low_mw': 1, 'high_mw': 250},
                            345: {'low_mw': 251, 'high_mw': 500},
                            500: {'low_mw': 501, 'high_mw': 1250},
                            765: {'low_mw': 1251, 'high_mw': 99999999}}

    def __init__(self, settings_dict, utility_dict, technology_dict, technology_order, initialize_site_data):

        # dictionary containing project level settings
        self.settings_dict = settings_dict

        # dictionary containing utility zone information
        self.utility_dict = utility_dict

        # dictionary containing technology specific information
        self.technology_dict = technology_dict

        # order of technologies to process
        self.technology_order = technology_order

        # initialize model with existing site data
        self.initialize_site_data = initialize_site_data

        # tech_id to tech_name dictionary
        self.tech_name_dict = ({k: self.technology_dict[k].get('tech_name') for k in self.technology_dict.keys()})

        # load coordinate data
        self.cerf_stateid_raster_file = pkg_resources.resource_filename('cerf', 'data/cerf_conus_states_albers_1km.tif')
        self.xcoords, self.ycoords = util.raster_to_coord_arrays(self.cerf_stateid_raster_file)

        # generate grid indices in a flat array
        self.indices_flat = np.array(np.arange(self.xcoords.flatten().shape[0]))
        self.indices_2d = self.indices_flat.reshape(self.xcoords.shape)

        # initialization data for siting
        self.init_arr, self.init_df = self.get_sited_data()

        # raster file containing the utility zone per grid cell
        self.zones_arr = self.load_utility_raster()

        # get LMP array per tech [tech_order, x, y]
        logging.debug('Processing locational marginal pricing (LMP)')
        self.lmp_arr = self.calculate_lmp()

        # get interconnection cost per tech [tech_order, x, y]
        logging.debug('Calculating interconnection costs (IC)')
        self.ic_arr = self.calculate_ic()

        # get NOV array per tech [tech_order, x, y]
        logging.debug('Calculating net operational cost (NOV)')
        self.nov_arr = self.calculate_nov()

        # get NLC array per tech [tech_order, x, y]
        logging.debug('Calculating net locational cost (NLC)')
        self.nlc_arr = self.calculate_nlc()

        # combine all suitability rasters into an array
        logging.debug('Building suitability array')
        self.suitability_arr = self.build_suitability_array()

    def load_utility_raster(self):
        """Load the utility zones raster for the CONUS into a 2D array."""

        # raster file containing the utility zone per grid cell
        zones_raster_file = self.utility_dict.get('utility_zone_raster_file', None)

        # use default if none passed
        if zones_raster_file is None:
            zones_raster_file = pkg_resources.resource_filename('cerf', 'data/utility_zones_1km.img')

        logging.info(f"Using 'zones_raster_file':  {zones_raster_file}")

        # read in utility zones raster as a 2D numpy array
        with rasterio.open(zones_raster_file) as src:
            return src.read(1)

    def calculate_lmp(self):
        """Calculate Locational Marginal Pricing."""

        # create technology specific locational marginal price based on capacity factor
        pricing = LocationalMarginalPricing(self.utility_dict,
                                            self.technology_dict,
                                            self.technology_order,
                                            self.zones_arr)
        lmp_arr = pricing.get_lmp()

        # get lmp array per tech [tech_order, x, y]
        return lmp_arr

    def calculate_ic(self):
        """Calculate interconnection costs."""

        # instantiate class
        # TODO:  add options to parameterize this from the config file
        ic = Interconnection(template_array=self.lmp_arr,
                             technology_dict=self.technology_dict,
                             technology_order=self.technology_order,
                             substation_file=None,
                             costs_to_connect_dict=None,
                             pipeline_file=None,
                             output_rasterized_file=False,
                             output_dist_file=False,
                             output_alloc_file=False,
                             output_cost_file=False,
                             transmission_gdf=None,
                             output_dir=None)

        ic_arr = ic.generate_interconnection_costs_array()

        return ic_arr

    def calculate_nov(self):
        """Calculate Net Operational Value."""

        nov_arr = np.zeros_like(self.lmp_arr)

        for index, i in enumerate(self.technology_order):
            econ = NetOperationalValue(discount_rate=self.technology_dict[i]['discount_rate'],
                                       lifetime=self.technology_dict[i]['lifetime'],
                                       unit_size=self.technology_dict[i]['unit_size'],
                                       capacity_factor=self.technology_dict[i]['capacity_factor'],
                                       variable_cost_esc_rate=self.technology_dict[i]['variable_cost_esc_rate'],
                                       fuel_esc_rate=self.technology_dict[i]['fuel_esc_rate'],
                                       carbon_esc_rate=self.technology_dict[i]['carbon_esc_rate'],
                                       variable_om=self.technology_dict[i]['variable_om'],
                                       heat_rate=self.technology_dict[i]['heat_rate'],
                                       fuel_price=self.technology_dict[i]['fuel_price'],
                                       carbon_tax=self.technology_dict[i]['carbon_tax'],
                                       carbon_capture_rate=self.technology_dict[i]['carbon_capture_rate'],
                                       fuel_co2_content=self.technology_dict[i]['fuel_co2_content'],
                                       lmp_arr=self.lmp_arr[index, :, :],
                                       target_year=self.settings_dict.get('run_year'))

            nov_tech_arr = econ.calc_nov()
            nov_arr[index, :, :] = nov_tech_arr

        return nov_arr

    def calculate_nlc(self):
        """Calculate Net Locational Costs."""

        # the most negative number will be the least expensive
        return self.ic_arr - self.nov_arr

    def get_sited_data(self):
        """If initial condition data is provided generate an array to use unsuitable where sites and their buffers
        exists.  Also return a data frame of active sites (not reaching retirement age) to include in the current years
        output.

        """

        # if initial condition data is provided, apply to all technologies
        if self.initialize_site_data is not None:

            # load siting data into a 2D array for the full grid space
            logging.debug("Initializing previous siting data")
            init_arr, init_df = util.ingest_sited_data(run_year=self.settings_dict['run_year'],
                                                       x_array=self.xcoords,
                                                       siting_data=self.initialize_site_data)

            return init_arr, init_df

        else:
            return None, None

    def build_suitability_array(self):
        """Build suitability array for all technologies."""

        # set up holder for suitability array
        suitability_array = np.ones_like(self.nlc_arr)

        # load tech specific rasters
        for index, i in enumerate(self.technology_order):

            # path to the input raster
            tech_suitability_raster_file = self.technology_dict[i].get('suitability_raster_file', None)

            if tech_suitability_raster_file is None:
                tech_suitability_raster_file = pkg_resources.resource_filename('cerf', f'data/suitability_{self.tech_name_dict[i]}.sdat')

            logging.info(f"Using suitability file for '{self.technology_dict[i]['tech_name']}':  {tech_suitability_raster_file}")

            # load raster to array
            with rasterio.open(tech_suitability_raster_file) as src:

                # read to 2D array
                tech_arr = src.read(1)

                if self.initialize_site_data is not None:
                    tech_arr = np.maximum(tech_arr, self.init_arr)

                # add to suitability array avoid overwriting the default dimension
                suitability_array[index, :, :] = tech_arr

        return suitability_array
