"""Tests for the public package namespace (evaluation item 6.4).

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

import re
import unittest
import warnings

import cerf


class TestPublicApi(unittest.TestCase):

    def test_all_names_resolve_and_nothing_leaks(self):
        for name in cerf.__all__:
            self.assertTrue(hasattr(cerf, name), name)

        # no third-party or stdlib modules re-exported by star imports
        for leaked in ('os', 'np', 'pd', 'gpd', 'logging', 'rasterio', 'yaml', 'plt'):
            self.assertNotIn(leaked, cerf.__all__)
            self.assertFalse(hasattr(cerf, leaked), leaked)

    def test_documented_entry_points_present(self):
        for name in ('run', 'Model', 'install_package_data', 'config_file', 'load_sample_config', 'plot_siting',
                     'sample_lmp_zones_raster_file', 'list_available_suitability_files', 'get_sample_lmp_data',
                     'costs_per_kv_substation', 'cerf_parallel', 'generate_model'):
            self.assertIn(name, cerf.__all__)

    def test_version_is_pep440_and_from_metadata(self):
        self.assertRegex(cerf.__version__, r'^\d+\.\d+\.\d+([.+\-][0-9A-Za-z.+\-]+)?$')
        # there must be no hard-coded release version duplicated in the package (the "0.0.0+unknown" fallback for
        #  uninstalled source trees is allowed)
        import inspect
        src = inspect.getsource(cerf)
        self.assertIsNone(re.search(r'__version__\s*=\s*["\'](?!0\.0\.0\+unknown)\d', src))

    def test_misspelled_suitability_helper_is_deprecated_alias(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            self.assertEqual(cerf.default_suitability_files(), cerf.default_suitabiity_files())
        self.assertTrue(any(issubclass(w.category, DeprecationWarning) for w in caught))


if __name__ == '__main__':
    unittest.main()
