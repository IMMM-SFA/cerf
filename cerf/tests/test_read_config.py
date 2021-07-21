"""Tests to ensure high-level functionality and outputs remain consistent.

@author Chris R. vernon
@email chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""
import unittest


class TestReadConfig(unittest.TestCase):
    """Test configuration reader."""

    # CONFIG_FILE = pkg_resources.resource_filename('cerf', 'tests/data/config.yml')

    def test_config_reader(self):
        """Tests for configuration reader."""

        self.assertEqual(2, 2)
        pass


if __name__ == '__main__':
    unittest.main()
