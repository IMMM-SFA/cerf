import os
import unittest

import pytest

import numpy as np
import pandas as pd
import rasterio

import cerf.package_data as pkg
from cerf.lmp import LocationalMarginalPricing, generate_random_lmp_dataframe
from cerf.read_config import ReadConfig


@pytest.mark.package_data
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
            zones_raster_file = pkg.sample_lmp_zones_raster_file()

        # read in lmp zoness raster as a 2D numpy array
        with rasterio.open(zones_raster_file) as src:
            return src.read(1)

    def test_generate_random_lmp_dataframe_is_seedable_and_local(self):
        np.random.seed(1)
        a = generate_random_lmp_dataframe(n_zones=3, seed=42)
        np.random.seed(2)
        b = generate_random_lmp_dataframe(n_zones=3, seed=42)
        c = generate_random_lmp_dataframe(n_zones=3, seed=43)

        pd.testing.assert_frame_equal(a, b)                       # seed controls output, global state does not
        self.assertFalse(a.drop(columns='hour').equals(c.drop(columns='hour')))
        self.assertEqual((8760, 4), a.shape)
        self.assertEqual(list(range(1, 8761)), a['hour'].tolist())

        # 85 % of values from [low, mid], 15 % from [mid, high]
        vals = a[0].to_numpy()
        self.assertEqual(int(8760 - 8760 * 0.15), int((vals <= 300).sum()))

    def test_zone_lookup_matches_vectorized_dict_get(self):
        """The lookup table must reproduce np.vectorize(dict.get) semantics exactly, including
        NaN for zone IDs absent from the dictionary and for the nodata value."""

        rng = np.random.default_rng(42)

        # zone IDs with gaps (9 and 13 absent from the dict) plus a nodata value of 255
        zones = rng.choice(np.array([1, 2, 3, 9, 13, 255], dtype=np.uint8), size=(40, 60))
        lmp_dict = {1: 10.5, 2: 20.25, 3: 30.125, 255: np.nan}

        expected = np.vectorize(lmp_dict.get)(zones).astype(np.float64)
        result = LocationalMarginalPricing.zone_lookup(zones, lmp_dict)

        self.assertEqual(result.dtype, np.float64)
        self.assertEqual(result.shape, zones.shape)
        np.testing.assert_array_equal(result, expected)

        # zones absent from the dictionary must be NaN
        self.assertTrue(np.all(np.isnan(result[zones == 9])))
        self.assertTrue(np.all(np.isnan(result[zones == 13])))
        self.assertTrue(np.all(np.isnan(result[zones == 255])))

    def test_zone_lookup_handles_negative_and_signed_ids(self):
        """Negative nodata values and signed integer dtypes must be supported."""

        zones = np.array([[-9999, 1, 2], [2, -9999, 1]], dtype=np.int32)
        lmp_dict = {1: 1.0, 2: 2.0, -9999: np.nan}

        expected = np.vectorize(lmp_dict.get)(zones).astype(np.float64)
        result = LocationalMarginalPricing.zone_lookup(zones, lmp_dict)

        np.testing.assert_array_equal(result, expected)

    def test_zone_lookup_rejects_non_integer_zones(self):
        """A float zone raster is a configuration error and must not be silently truncated."""

        zones = np.array([[1.0, 2.0]], dtype=np.float32)

        with self.assertRaises(TypeError):
            LocationalMarginalPricing.zone_lookup(zones, {1: 1.0, 2: 2.0})

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


def test_operational_schedule_uses_chronological_lmp_hours(tmp_path):
    lmp_path = tmp_path / 'lmp.csv'
    schedule_path = tmp_path / 'schedule.csv'
    pd.DataFrame({'hour': np.arange(1, 8761), 1: np.arange(8760)}).to_csv(lmp_path, index=False)

    operational = np.zeros(8760, dtype=int)
    operational[[2, 7]] = 1
    schedule = pd.DataFrame({'hour': np.arange(8760), 'operational': operational})
    schedule.sample(frac=1, random_state=42).to_csv(schedule_path, index=False)

    pricing = LocationalMarginalPricing(
        {'lmp_hourly_data_file': str(lmp_path), 'lmp_zone_raster_nodata_value': 255},
        {1: {'tech_name': 'test', 'capacity_factor_fraction': 0.4,
             'operational_schedule_file': str(schedule_path)}},
        [1],
        np.array([[1]], dtype=np.int16),
    )

    result = pricing.get_lmp()

    assert result[0, 0, 0] == 4.5


@pytest.mark.parametrize('row_count', [8759, 8761])
def test_operational_schedule_requires_8760_rows(tmp_path, row_count):
    schedule_path = tmp_path / 'schedule.csv'
    schedule = pd.DataFrame({'hour': np.arange(row_count), 'operational': np.ones(row_count, dtype=int)})
    schedule.to_csv(schedule_path, index=False)

    with pytest.raises(ValueError, match='exactly 8760 rows'):
        LocationalMarginalPricing.get_operational_hours(schedule_path, 'test')


@pytest.mark.parametrize('invalid_hour', ['duplicate', 'out_of_range', 'fractional'])
def test_operational_schedule_requires_each_zero_based_hour_once(tmp_path, invalid_hour):
    schedule_path = tmp_path / 'schedule.csv'
    schedule = pd.DataFrame({'hour': np.arange(8760, dtype=float), 'operational': np.ones(8760, dtype=int)})
    if invalid_hour == 'duplicate':
        schedule.loc[0, 'hour'] = 1
    elif invalid_hour == 'out_of_range':
        schedule.loc[0, 'hour'] = 8760
    else:
        schedule.loc[0, 'hour'] = 0.5
    schedule.to_csv(schedule_path, index=False)

    with pytest.raises(ValueError, match='each integer from 0 through 8759 exactly once'):
        LocationalMarginalPricing.get_operational_hours(schedule_path, 'test')


@pytest.mark.parametrize('invalid_value', [None, 2, 'invalid'])
def test_operational_schedule_requires_binary_values(tmp_path, invalid_value):
    schedule_path = tmp_path / 'schedule.csv'
    schedule = pd.DataFrame({'hour': np.arange(8760), 'operational': np.ones(8760, dtype=object)})
    schedule.loc[0, 'operational'] = invalid_value
    schedule.to_csv(schedule_path, index=False)

    with pytest.raises(ValueError, match='must be binary 0 or 1'):
        LocationalMarginalPricing.get_operational_hours(schedule_path, 'test')


def test_operational_schedule_requires_both_columns(tmp_path):
    schedule_path = tmp_path / 'schedule.csv'
    pd.DataFrame({'hour': np.arange(8760)}).to_csv(schedule_path, index=False)

    with pytest.raises(ValueError, match='must contain `hour` and `operational` columns'):
        LocationalMarginalPricing.get_operational_hours(schedule_path, 'test')


def test_operational_schedule_with_no_active_hours_raises(tmp_path):
    schedule_path = tmp_path / 'schedule.csv'
    pd.DataFrame({'hour': np.arange(8760), 'operational': np.zeros(8760, dtype=int)}).to_csv(
        schedule_path, index=False)

    with pytest.raises(ValueError, match='No operational hours are set'):
        LocationalMarginalPricing.get_operational_hours(schedule_path, 'test')


@pytest.mark.parametrize('capacity_factor', [0.499, 0.5, 0.501])
def test_missing_operational_schedule_preserves_capacity_factor_selection(tmp_path, capacity_factor):
    lmp_path = tmp_path / 'lmp.csv'
    lmp_values = np.arange(8760)
    pd.DataFrame({'hour': np.arange(1, 8761), 1: lmp_values}).to_csv(lmp_path, index=False)
    pricing = LocationalMarginalPricing(
        {'lmp_hourly_data_file': str(lmp_path), 'lmp_zone_raster_nodata_value': 255},
        {1: {'tech_name': 'test', 'capacity_factor_fraction': capacity_factor}},
        [1],
        np.array([[1]], dtype=np.int16),
    )

    result = pricing.get_lmp()

    start_index, through_index = LocationalMarginalPricing.get_cf_bin(capacity_factor)
    ranked_values = np.sort(lmp_values)[::-1]
    expected = ranked_values[start_index:through_index].mean()
    assert result[0, 0, 0] == expected


def test_nonexistent_operational_schedule_raises_file_not_found(tmp_path):
    lmp_path = tmp_path / 'lmp.csv'
    lmp_values = np.arange(8760)
    pd.DataFrame({'hour': np.arange(1, 8761), 1: lmp_values}).to_csv(lmp_path, index=False)
    pricing = LocationalMarginalPricing(
        {'lmp_hourly_data_file': str(lmp_path), 'lmp_zone_raster_nodata_value': 255},
        {1: {
            'tech_name': 'test',
            'capacity_factor_fraction': 0.4,
            'operational_schedule_file': str(tmp_path / 'missing.csv'),
        }},
        [1],
        np.array([[1]], dtype=np.int16),
    )

    with pytest.raises(FileNotFoundError, match='operational schedule file'):
        pricing.get_lmp()
