"""Tests to ensure high-level functionality and outputs remain consistent.

@author Chris R. vernon
@email chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""
import pkg_resources
import unittest

from cerf.read_config import ReadConfig


class TestReadConfig(unittest.TestCase):
    """Test configuration reader."""

    CONFIG_FILE = pkg_resources.resource_filename('cerf', 'tests/data/config.yml')

    def test_config_reader(self):
        """Tests for configuration reader."""

        # cfg = ReadConfig(config_file=TestReadConfig.CONFIG_FILE)
        #
        # print(cfg.biomass_directory)
        # print(cfg.nuclear_directory)
        pass


if __name__ == '__main__':
    unittest.main()
