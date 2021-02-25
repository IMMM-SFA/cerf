"""Stage data for CERF run.

@author Chris R. vernon
@email chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

import logger
import numpy as np
import rasterio

from cerf.lmp import LocationalMarginalPricing
from cerf.nov import NetOperationalValue


class Stage:

    def __init__(self, config, technology_dict, technology_order):

        self.config = config
        self.technology_dict = technology_dict
        self.technology_order = technology_order

        # get LMP array per tech [tech_order, x, y]
        self.lmp_arr = self.calculate_lmp()

        # get interconnection cost per tech [tech_order, x, y]
        self.ic_arr = self.calculate_ic()

        # get NOV array per tech [tech_order, x, y]
        self.nov_arr = self.calculate_nov()

        # get NLC array per tech [tech_order, x, y]
        self.nlc_arr = self.calculate_nlc()

        # combine all suitability rasters into an array
        self.suitability_arr = self.build_suitability_array()

    def calculate_lmp(self):
        """Calculate Locational Marginal Pricing."""

        # create technology specific locational marginal price based on capacity factor
        pricing = LocationalMarginalPricing(self.config, self.technology_order)

        # get lmp array per tech [tech_order, x, y]
        return pricing.lmp_arr

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
                                       target_year=self.config['settings']['run_year'])

            nov_arr[index, :, :] = econ.nov

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
