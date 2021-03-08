"""Stage data for CERF run.

@author Chris R. vernon
@email chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

import logging
import pkg_resources

import rasterio
import numpy as np

from cerf.lmp import LocationalMarginalPricing
from cerf.nov import NetOperationalValue


class Stage:

    # type hints
    settings_dict: dict
    utility_dict: dict
    technology_dict: dict
    technology_order: list

    def __init__(self, settings_dict, utility_dict, technology_dict, technology_order):

        # dictionary containing project level settings
        self.settings = settings_dict

        # dictionary containing utility zone information
        self.utility_dict = utility_dict

        # dictionary containing technology specific information
        self.technology_dict = technology_dict

        # order of technologies to process
        self.technology_order = technology_order

        # load coordinate data
        self.xcoords = np.load(pkg_resources.resource_filename('cerf', 'data/conus_xcoords_albers_2d.npy'))
        self.ycoords = np.load(pkg_resources.resource_filename('cerf', 'data/conus_ycoords_albers_2d.npy'))

        # raster file containing the utility zone per grid cell
        self.zones_arr = self.load_utility_raster()

        # get LMP array per tech [tech_order, x, y]
        logging.info('Processing locational marginal pricing (LMP)')
        self.lmp_arr = self.calculate_lmp()

        # get interconnection cost per tech [tech_order, x, y]
        logging.info('Calculating interconnection costs (IC)')
        self.ic_arr = self.calculate_ic()

        # get NOV array per tech [tech_order, x, y]
        logging.info('Calculating net operational cost (NOV)')
        self.nov_arr = self.calculate_nov()

        # get NLC array per tech [tech_order, x, y]
        logging.info('Calculating net locational cost (NLC)')
        self.nlc_arr = self.calculate_nlc()

        # combine all suitability rasters into an array
        logging.info('Building suitability array')
        self.suitability_arr = self.build_suitability_array()

    def load_utility_raster(self):
        """Load the utility zones raster for the CONUS into a 2D array."""

        # raster file containing the utility zone per grid cell
        zones_raster_file = self.utility_dict.get('utility_zone_raster_file')

        # read in utility zones raster as a 2D numpy array
        with rasterio.open(zones_raster_file) as src:
            return src.read(1)

    def calculate_lmp(self):
        """Calculate Locational Marginal Pricing."""

        # create technology specific locational marginal price based on capacity factor
        pricing = LocationalMarginalPricing(self.utility_dict, self.technology_dict, self.technology_order, self.zones_arr)
        lmp_arr = pricing.get_lmp()

        # get lmp array per tech [tech_order, x, y]
        return lmp_arr

    def calculate_ic(self):
        """Calculate interconnection costs."""

        # set up array to hold interconnection costs
        ic_arr = np.zeros_like(self.lmp_arr)

        for index, i in enumerate(self.technology_order):

            # load distance to suitable transmission infrastructure raster
            with rasterio.open(self.technology_dict[i].get('interconnection_distance_raster_file')) as src:
                ic_dist_km_arr = src.read(1) / 1000  # convert meters to km

            # calculate interconnection costs per grid cell
            ic_arr[index, :, :] = ic_dist_km_arr * self.technology_dict[i]['interconnection_cost_per_km']

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
                                       target_year=self.settings.get('run_year'))

            nov_tech_arr = econ.calc_nov()
            nov_arr[index, :, :] = nov_tech_arr

        return nov_arr

    def calculate_nlc(self):
        """Calculate Net Locational Costs."""

        # the most negative number will be the least expensive
        return self.ic_arr - self.nov_arr

    def build_suitability_array(self):
        """Build suitability array for all technologies."""

        # set up holder for suitability array
        suitability_array = np.ones_like(self.nlc_arr)

        # load tech specific rasters
        for index, i in enumerate(self.technology_order):

            # path to the input raster
            tech_suitability_raster_file = self.technology_dict[i].get('suitability_raster_file')

            # load raster to array
            with rasterio.open(tech_suitability_raster_file) as src:

                # read to 2D array
                tech_arr = src.read(1)

                # add to suitability array avoid overwriting the default dimension
                suitability_array[index, :, :] = tech_arr

        return suitability_array
