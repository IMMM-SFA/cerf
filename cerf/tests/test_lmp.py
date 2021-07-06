import unittest

import numpy as np
import pkg_resources
import rasterio

from cerf.lmp import LocationalMarginalPricing
from cerf.read_config import ReadConfig
from cerf.package_data import config_file


class TestLmp(unittest.TestCase):

    # supporting data
    SLIM_LMP_ARRAY = np.load(pkg_resources.resource_filename('cerf', 'tests/data/comp_data/lmp_arr.npy'))
    TECH_ORDER_LIST = ['biomass_conv', 'nuclear']
    LMP_FILE = pkg_resources.resource_filename('cerf', 'data/illustrative_lmp_8760-per-zone_dollars-per-mwh.zip')

    @classmethod
    def slim_techs(cls):
        """Only use two technologies to speed up tests."""

        return {k: cls.TECH_DICT_FULL[k] for k in cls.TECH_DICT_FULL.keys() if k in ('biomass_conv', 'nuclear')}

    @staticmethod
    def get_sample(arr):
        """Get a sample from the LMP dictionary to reduce comparison size.  Sample space covers the Southeast U.S."""

        return arr[:, 1500:2000, 3000:4000].copy()

    @staticmethod
    def load_utility_raster(utility_dict):
        """Load the utility zones raster for the CONUS into a 2D array."""

        # raster file containing the utility zone per grid cell
        zones_raster_file = utility_dict.get('utility_zone_raster_file')

        if zones_raster_file == 'None':
            zones_raster_file = pkg_resources.resource_filename('cerf', 'data/utility_zones_1km.img')

        # read in utility zones raster as a 2D numpy array
        with rasterio.open(zones_raster_file) as src:
            return src.read(1)

    def test_lmp_outputs(self):
        """Test to make sure LMP outputs match expected."""

        # read in configuration file
        cfg_file = config_file(yr=2010)
        cfg = ReadConfig(cfg_file)

        # read in zones array
        zones_arr = self.load_utility_raster(cfg.utility_dict)

        # create technology specific locational marginal price based on capacity factor
        pricing = LocationalMarginalPricing(cfg.utility_dict,
                                            cfg.technology_dict,
                                            cfg.technology_order,
                                            zones_arr,
                                            TestLmp.LMP_FILE)

        # get lmp array per tech [tech_order, x, y]
        lmp_arr = pricing.get_lmp()

        # trim down LMP array for testing
        slim_lmps = self.get_sample(lmp_arr)

        # test LMP array equality
        np.testing.assert_array_equal(np.around(TestLmp.SLIM_LMP_ARRAY, 4), np.around(slim_lmps, 4))


if __name__ == '__main__':
    unittest.main()
