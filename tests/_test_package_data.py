import unittest

from cerf.package_data import *


class TestPackageData(unittest.TestCase):
    """Tests for package data matching to confirm load function modification does not happen."""

    def test_config_file(self):
        """Ensure package data functions do not get modified."""

        yr = 2010

        comp = pkg_resources.resource_filename('cerf', f'data/config_{yr}.yml')
        val = config_file(yr)

        self.assertEqual(comp, val)

    def test_cerf_regions_shapefile(self):
        """Ensure package data functions do not get modified."""

        comp = gpd.read_file(pkg_resources.resource_filename('cerf', 'data/cerf_conus_states_albers.zip'))
        val = cerf_regions_shapefile()

        pd.testing.assert_frame_equal(comp, val)

    def test_cerf_boundary_shapefile(self):
        """Ensure package data functions do not get modified."""

        comp = gpd.read_file(pkg_resources.resource_filename('cerf', 'data/cerf_conus_boundary_albers.zip'))
        val = cerf_boundary_shapefile()

        pd.testing.assert_frame_equal(comp, val)

    def test_cerf_crs(self):
        """Ensure package data functions do not get modified."""

        comp = cerf_regions_shapefile().crs
        val = cerf_crs()

        self.assertEqual(comp, val)

    def test_costs_per_kv_substation(self):
        """Ensure package data functions do not get modified."""

        f = pkg_resources.resource_filename('cerf', 'data/costs_per_kv_substation.yml')

        with open(f, 'r') as yml:
            comp = yaml.load(yml, Loader=yaml.FullLoader)

        val = costs_per_kv_substation()

        self.assertEqual(comp, val)

    def test_load_sample_config(self):
        """Ensure package data functions do not get modified."""

        yr = 2010

        available_years = list(range(2010, 2055, 5))

        if yr not in available_years:
            raise KeyError(f"Year '{yr}' not available as a default configuration file.  Must be in {available_years}")

        f = pkg_resources.resource_filename('cerf', f'data/config_{yr}.yml')

        with open(f, 'r') as yml:
            comp =  yaml.load(yml, Loader=yaml.FullLoader)

        val = load_sample_config(yr)

        self.assertEqual(comp, val)

    def test_list_available_suitability_files(self):
        """Ensure package data functions do not get modified."""

        root_dir = pkg_resources.resource_filename('cerf', 'data')

        comp = [os.path.join(root_dir, i) for i in os.listdir(root_dir) if
                (i.split('_')[0] == 'suitability') and
                (os.path.splitext(i)[-1] == '.sdat')]

        val = list_available_suitability_files()

        self.assertEqual(comp, val)

    def test_sample_lmp_zones_raster_file(self):
        """Ensure package data functions do not get modified."""

        comp = pkg_resources.resource_filename('cerf', 'data/lmp_zones_1km.img')
        val = sample_lmp_zones_raster_file()

        self.assertEqual(comp, val)

    def test_get_sample_lmp_data(self):
        """Ensure package data functions do not get modified."""

        comp = pd.read_csv(pkg_resources.resource_filename('cerf', 'data/illustrative_lmp_8760-per-zone_dollars-per-mwh.zip'))
        val = get_sample_lmp_data()

        pd.testing.assert_frame_equal(comp, val)

    def test_get_region_abbrev_to_name(self):
        """Ensure package data functions do not get modified."""

        regions_file = pkg_resources.resource_filename('cerf', 'data/region-abbrev_to_region-name.yml')

        with open(regions_file, 'r') as yml:
            comp = yaml.load(yml, Loader=yaml.FullLoader)

        val = get_region_abbrev_to_name()

        self.assertEqual(comp, val)

    def test_get_data_directory(self):
        """Ensure package data functions do not get modified."""

        comp = pkg_resources.resource_filename('cerf', 'data')
        val = get_data_directory()

        self.assertEqual(comp, val)


if __name__ == '__main__':
    unittest.main()
