import pickle
import pkg_resources
import unittest

import numpy as np

from cerf.lmp import LocationalMarginalPricing


class TestLmp(unittest.TestCase):

    # supporting data
    UTILITY_ZONES_RASTER_FILE = pkg_resources.resource_filename('cerf', 'tests/data/inputs/spatial/utility_zones_1km.img')
    UTILITY_ZONES_XML_FILE = pkg_resources.resource_filename('cerf', 'tests/data/inputs/xml/powerzones.xml')
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

        pricing = LocationalMarginalPricing(zones_raster_file=TestLmp.UTILITY_ZONES_RASTER_FILE,
                                            zones_xml_file=TestLmp.UTILITY_ZONES_XML_FILE,
                                            technology_dict=self.slim_techs())

        # trim down LMP array for testing
        slim_lmps = self.get_sample(pricing.lmp_arr)

        # test LMP array equality
        np.testing.assert_array_equal(TestLmp.SLIM_LMP_ARRAY, slim_lmps)

        # test tech order list match
        self.assertEqual(TestLmp.TECH_ORDER_LIST, pricing.tech_order)


if __name__ == '__main__':
    unittest.main()
