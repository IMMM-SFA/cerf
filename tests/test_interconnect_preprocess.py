"""Tests for the raw infrastructure preprocessing functions in cerf.interconnect.

These build small synthetic shapefiles in a temporary directory so they do not depend on the
HIFLD / EIA source data, but they do use the packaged cost YAML files and CONUS CRS.

"""

import os
import tempfile
import unittest

import geopandas as gpd
import numpy as np
from shapely.geometry import LineString, Point

import cerf.package_data as pkg
from cerf.interconnect import (assign_substation_costs,
                               preprocess_eia_natural_gas_pipelines,
                               preprocess_hifld_substations)


class TestAssignSubstationCosts(unittest.TestCase):

    COSTS = {0: {'min_voltage': -1, 'max_voltage': 99, 'thous_dollar_per_km': 678},
             1: {'min_voltage': 100, 'max_voltage': 119, 'thous_dollar_per_km': 756},
             2: {'min_voltage': 120, 'max_voltage': 149, 'thous_dollar_per_km': 791}}

    def test_bins_voltage_into_cost_classes(self):
        gdf = gpd.GeoDataFrame({'min_volt': [0, 99, 100, 119, 120, 149]},
                               geometry=[Point(0, 0)] * 6)

        out = assign_substation_costs(gdf, self.COSTS)

        self.assertEqual(out['_rval_'].tolist(), [678, 678, 756, 756, 791, 791])

    def test_voltage_outside_all_bins_is_zero(self):
        gdf = gpd.GeoDataFrame({'min_volt': [500]}, geometry=[Point(0, 0)])

        out = assign_substation_costs(gdf, self.COSTS)

        self.assertEqual(out['_rval_'].tolist(), [0])

    def test_missing_voltage_field_raises(self):
        gdf = gpd.GeoDataFrame({'kv': [100]}, geometry=[Point(0, 0)])

        with self.assertRaises(KeyError):
            assign_substation_costs(gdf, self.COSTS)


class TestPreprocessHifldSubstations(unittest.TestCase):

    @staticmethod
    def make_substations():
        """Synthetic HIFLD-like substations in WGS84 with upper-case field names as in the source data."""

        return gpd.GeoDataFrame(
            {
                'TYPE': ['SUBSTATION', 'substation', 'TAP', 'SUBSTATION', 'SUBSTATION', 'SUBSTATION'],
                'STATE': ['WA', 'OR', 'WA', 'AK', 'WA', 'CA'],
                'STATUS': ['IN SERVICE', 'under const', 'IN SERVICE', 'IN SERVICE', 'RETIRED', ' in service '],
                'MIN_VOLT': [115, 500, 115, 115, 115, 69],
            },
            geometry=[Point(-122.3, 47.6), Point(-122.7, 45.5), Point(-122.3, 47.6),
                      Point(-149.9, 61.2), Point(-122.3, 47.6), Point(-118.2, 34.1)],
            crs='EPSG:4326',
        )

    def test_filters_and_assigns_costs(self):
        costs = pkg.costs_per_kv_substation()
        expected_115 = next(v['thous_dollar_per_km'] for v in costs.values()
                            if v['min_voltage'] <= 115 <= v['max_voltage'])
        expected_500 = next(v['thous_dollar_per_km'] for v in costs.values()
                            if v['min_voltage'] <= 500 <= v['max_voltage'])
        expected_69 = next(v['thous_dollar_per_km'] for v in costs.values()
                           if v['min_voltage'] <= 69 <= v['max_voltage'])

        with tempfile.TemporaryDirectory() as tmp:
            in_file = os.path.join(tmp, 'subs.shp')
            out_file = os.path.join(tmp, 'subs_out.shp')
            self.make_substations().to_file(in_file)

            gdf = preprocess_hifld_substations(in_file, output_file=out_file)

            # written output round-trips
            self.assertTrue(os.path.isfile(out_file))
            written = gpd.read_file(out_file)
            self.assertEqual(len(written), len(gdf))

        # kept: WA in service (115 kV), OR under const lower-case (500 kV), CA padded/lower-case status (69 kV)
        # dropped: TAP type, AK (not CONUS), RETIRED status
        self.assertEqual(len(gdf), 3)
        self.assertEqual(sorted(gdf['state'].tolist()), ['CA', 'OR', 'WA'])
        self.assertEqual(gdf.set_index('state')['_rval_'].to_dict(),
                         {'WA': expected_115, 'OR': expected_500, 'CA': expected_69})

        # reprojected to the cerf CRS and column names lower-cased
        self.assertEqual(gdf.crs, pkg.cerf_crs())
        self.assertIn('min_volt', gdf.columns)
        self.assertNotIn('MIN_VOLT', gdf.columns)


class TestPreprocessEiaPipelines(unittest.TestCase):

    def test_filters_operating_nonzero_length(self):
        gdf_in = gpd.GeoDataFrame(
            {'Status': ['Operating', 'OPERATING', 'Proposed', 'Operating']},
            geometry=[LineString([(-100, 40), (-99, 40)]),
                      LineString([(-100, 41), (-99, 41)]),
                      LineString([(-100, 42), (-99, 42)]),
                      LineString([(-100, 43), (-100, 43)])],  # zero length
            crs='EPSG:4326',
        )

        with tempfile.TemporaryDirectory() as tmp:
            in_file = os.path.join(tmp, 'pipes.shp')
            gdf_in.to_file(in_file)

            gdf = preprocess_eia_natural_gas_pipelines(in_file)

        self.assertEqual(len(gdf), 2)
        self.assertTrue((gdf['_rval_'] > 0).all())
        self.assertTrue(np.isfinite(gdf['_rval_']).all())
        self.assertEqual(gdf.crs, pkg.cerf_crs())


if __name__ == '__main__':
    unittest.main()
