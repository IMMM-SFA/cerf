import pickle
import pkg_resources
import unittest

import numpy as np

from cerf.read_config import ReadConfig
from cerf.lmp import LocationalMarginalPricing


class TestLmp(unittest.TestCase):

    # supporting data
    CONFIG_FILE = pkg_resources.resource_filename('cerf', 'tests/data/config.yml')
    UTILITY_ZONES_RASTER_FILE = pkg_resources.resource_filename('cerf', 'tests/data/inputs/spatial/utility_zones_1km.img')
    TECH_DICT_FILE = pkg_resources.resource_filename('cerf', 'tests/data/comp_data/technology_dict.p')
    TECH_DICT_FULL = pickle.load(open(TECH_DICT_FILE, 'rb'))
    SLIM_LMP_ARRAY = np.load(pkg_resources.resource_filename('cerf', 'tests/data/comp_data/lmp_arr.npy'))
    TECH_ORDER_LIST = ['biomass_conv', 'nuclear']

    @classmethod
    def slim_techs(cls):
        """Only use two technologies to speed up tests."""

        return {k: cls.TECH_DICT_FULL[k] for k in cls.TECH_DICT_FULL.keys() if k in ('biomass_conv', 'nuclear')}

    @staticmethod
    def get_sample(arr):
        """Get a sample from the LMP dictionary to reduce comparison size.  Sample space covers the Southeast U.S."""

        return arr[:, 1500:2000, 3000:4000].copy()

    def test_lmp_outputs(self):
        """Test to make sure LMP outputs match expected."""

        # read in configuration file
        cfg = ReadConfig(TestLmp.CONFIG_FILE)

        # update configuration to use package data for testing
        cfg.utility_dict.update(utility_zone_raster_file=TestLmp.UTILITY_ZONES_RASTER_FILE)

        # create technology specific locational marginal price based on capacity factor
        pricing = LocationalMarginalPricing(cfg.utility_dict, cfg.technology_dict, cfg.technology_order)

        # get lmp array per tech [tech_order, x, y]
        lmp_arr = pricing.get_lmp()

        # trim down LMP array for testing
        slim_lmps = self.get_sample(lmp_arr)

        # test LMP array equality
        np.testing.assert_array_equal(TestLmp.SLIM_LMP_ARRAY, slim_lmps)


if __name__ == '__main__':
    unittest.main()
