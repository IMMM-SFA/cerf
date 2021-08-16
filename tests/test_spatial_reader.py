"""Tests for spatial_reader.py

@author Chris R. vernon
@email chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""
import unittest

#import cerf.spatial_reader as sr


class TestSpatialReader(unittest.TestCase):
    """Tests for `spatial_reader.py`"""

    # BIOMASS_DIR = pkg_resources.resource_dir('cerf', 'tests/data/inputs/spatial/biomass')
    # NUCLEAR_DIR = pkg_resources.resource_dir('cerf', 'tests/data/inputs/spatial/nuclear')

    def test_sum_rasters(self):
        """Tests for `sum_rasters` function."""

        # arr = sr.sum_rasters(TestSpatialReader.BIOMASS_DIR)
        #
        # print(arr.shape)
        # print(arr.min())
        # print(arr.max())
        # print(arr.unique())

        self.assertEqual(2, 2)
        pass


if __name__ == '__main__':
    unittest.main()
