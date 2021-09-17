import os
import unittest

import numpy as np
import pkg_resources
import rasterio

from cerf.lmp import LocationalMarginalPricing
from cerf.read_config import ReadConfig


class TestLmp(unittest.TestCase):

    # supporting data
    SLIM_LMP_ARRAY = np.load(os.path.join(os.path.dirname(__file__), 'data/test_lmp_arr.npy'))
    LMP_FILE = os.path.join(os.path.dirname(__file__), 'data/illustrative_lmp_8760-per-zone_dollars-per-mwh.zip')
    TEST_CONFIG = os.path.join(os.path.dirname(__file__), 'data/test_config_2010.yml')

    @staticmethod
    def get_sample(arr):
        """Get a sample from the LMP dictionary to reduce comparison size.  Sample space covers the Southeast U.S."""

        return arr[:, 1500:2000, 3000:4000].copy()

    @staticmethod
    def load_lmp_zone_raster(lmp_zone_dict):
        """Load the lmp zones raster for the CONUS into a 2D array."""

        # raster file containing the lmp zones per grid cell
        zones_raster_file = lmp_zone_dict.get('lmp_zone_raster_file')

        if zones_raster_file is None:
            zones_raster_file = pkg_resources.resource_filename('cerf', 'data/lmp_zones_1km.img')

        # read in lmp zoness raster as a 2D numpy array
        with rasterio.open(zones_raster_file) as src:
            return src.read(1)

    def test_lmp_outputs(self):
        """Test to make sure LMP outputs match expected."""

        # set seed for reproducibility
        np.random.seed(0)

        # read in configuration file
        cfg = ReadConfig(self.TEST_CONFIG)

        # read in zones array
        zones_arr = self.load_lmp_zone_raster(cfg.lmp_zone_dict)

        # create technology specific locational marginal price based on capacity factor
        pricing = LocationalMarginalPricing(cfg.lmp_zone_dict,
                                            cfg.technology_dict,
                                            cfg.technology_order,
                                            zones_arr)

        # get lmp array per tech [tech_order, x, y]
        lmp_arr = pricing.get_lmp()

        # trim down LMP array for testing
        slim_lmps = self.get_sample(lmp_arr)

        # test LMP array equality
        np.testing.assert_array_equal(np.around(TestLmp.SLIM_LMP_ARRAY, 4), np.around(slim_lmps, 4))


if __name__ == '__main__':
    unittest.main()
