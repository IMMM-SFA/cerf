import copy
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

    def test_config_dict_is_not_mutated(self):
        """The caller's configuration dictionary must be left untouched by ReadConfig."""

        user_config = ReadConfig.read_yaml(self.TEST_CONFIG)
        snapshot = copy.deepcopy(user_config)

        cfg = ReadConfig(config_dict=user_config)

        # ReadConfig injects package-default paths into settings; that must happen on its private copy only
        self.assertEqual(snapshot, user_config)
        self.assertIsNotNone(cfg.settings_dict['region_raster_file'])
        self.assertIsNone(user_config['settings']['region_raster_file'])

        # the model's sub-dictionaries must not alias the caller's
        for key, attr in (('settings', 'settings_dict'),
                          ('technology', 'technology_dict'),
                          ('expansion_plan', 'expansion_dict'),
                          ('lmp_zones', 'lmp_zone_dict')):
            self.assertIsNot(user_config[key], getattr(cfg, attr))

        # mutating the model's expansion plan must not leak back to the caller
        region = next(iter(cfg.expansion_dict))
        tech = next(iter(cfg.expansion_dict[region]))
        cfg.expansion_dict[region][tech]['n_sites'] = -999
        self.assertEqual(snapshot, user_config)

    def test_config_dict_none_with_file(self):
        """`config_dict=None` alongside a config file must behave exactly like no overrides."""

        cfg_none = ReadConfig(config_file=self.TEST_CONFIG, config_dict=None)
        cfg_default = ReadConfig(config_file=self.TEST_CONFIG)
        cfg_empty = ReadConfig(config_file=self.TEST_CONFIG, config_dict={})

        self.assertEqual(cfg_default.settings_dict, cfg_none.settings_dict)
        self.assertEqual(cfg_default.expansion_dict, cfg_none.expansion_dict)
        self.assertEqual(cfg_empty.settings_dict, cfg_none.settings_dict)

    def test_no_config_raises_value_error(self):
        """Neither a file nor a dictionary is an error, not an obscure AttributeError."""

        for empty in (None, {}):
            with self.assertRaises(ValueError):
                ReadConfig(config_dict=empty)

    def test_default_config_dict_is_not_shared(self):
        """The default argument must not be a mutable object shared across instances."""

        first = ReadConfig(config_file=self.TEST_CONFIG)
        first.settings_dict['run_year'] = 1900
        second = ReadConfig(config_file=self.TEST_CONFIG)

        self.assertNotEqual(1900, second.settings_dict['run_year'])

    def test_config_dict_overrides_do_not_mutate_caller(self):
        """Overrides passed alongside a config file must not be written back to the caller's dictionary."""

        overrides = {'settings': {'run_year': 2010}}
        snapshot = copy.deepcopy(overrides)

        cfg = ReadConfig(config_file=self.TEST_CONFIG, config_dict=overrides)

        self.assertEqual(2010, cfg.settings_dict['run_year'])
        self.assertEqual(snapshot, overrides)


if __name__ == '__main__':
    unittest.main()
