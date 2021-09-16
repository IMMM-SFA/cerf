import os
import unittest

from cerf.read_config import ReadConfig


class TestReadConfig(unittest.TestCase):
    """Test configuration reader."""

    TEST_CONFIG = os.path.join(os.path.dirname(__file__), 'data/test_config_2010.yml')

    EXPECTED_REGDICT = {'alabama': 1, 'arizona': 2, 'arkansas': 3, 'california': 4, 'colorado': 5, 'connecticut': 6,
                        'delaware': 7, 'district_of_columbia': 8, 'florida': 9, 'georgia': 10, 'idaho': 11,
                        'illinois': 12, 'indiana': 13, 'iowa': 14, 'kansas': 15, 'kentucky': 16, 'louisiana': 17,
                        'maine': 18, 'maryland': 19, 'massachusetts': 20, 'michigan': 21, 'minnesota': 22,
                        'mississippi': 23, 'missouri': 24, 'montana': 25, 'nebraska': 26, 'nevada': 27,
                        'new_hampshire': 28, 'new_jersey': 29, 'new_mexico': 30, 'new_york': 31, 'north_carolina': 32,
                        'north_dakota': 33, 'ohio': 34, 'oklahoma': 35, 'oregon': 36, 'pennsylvania': 37,
                        'rhode_island': 38, 'south_carolina': 39, 'south_dakota': 40, 'tennessee': 41, 'texas': 42,
                        'utah': 43, 'vermont': 44, 'virginia': 45, 'washington': 46, 'west_virginia': 47,
                        'wisconsin': 48, 'wyoming': 49}

    def test_config_reader(self):
        """Tests for configuration reader."""

        # reading in the config file tests the validation protocol
        cfg = ReadConfig(self.TEST_CONFIG)

        self.assertEqual(TestReadConfig.EXPECTED_REGDICT, cfg.regions_dict)


if __name__ == '__main__':
    unittest.main()
