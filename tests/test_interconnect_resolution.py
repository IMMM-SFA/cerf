"""Tests for pixel-size-aware interconnection distances (evaluation item 5.2).

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

import os
import tempfile
import unittest

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_origin
from shapely.geometry import LineString, MultiLineString, Point, Polygon

from cerf.interconnect import Interconnection


class TestPixelSizeKm(unittest.TestCase):

    def test_metre_crs(self):
        self.assertEqual((1.0, 1.0), Interconnection.pixel_size_km((1000.0, 1000.0), CRS.from_string("ESRI:102003")))
        self.assertEqual((0.5, 0.25), Interconnection.pixel_size_km((250.0, 500.0), CRS.from_epsg(32617)))  # (row, col)

    def test_negative_resolution_is_absolute(self):
        self.assertEqual((1.0, 1.0), Interconnection.pixel_size_km((1000.0, -1000.0), CRS.from_epsg(32617)))

    def test_foot_crs_is_converted(self):
        # EPSG:2263 (NY Long Island) is in US survey feet
        row_km, col_km = Interconnection.pixel_size_km((1000.0, 1000.0), CRS.from_epsg(2263))
        self.assertAlmostEqual(0.3048006096, row_km, places=9)
        self.assertAlmostEqual(0.3048006096, col_km, places=9)

    def test_geographic_or_missing_crs_rejected(self):
        with self.assertRaises(ValueError):
            Interconnection.pixel_size_km((0.01, 0.01), CRS.from_epsg(4326))
        with self.assertRaises(ValueError):
            Interconnection.pixel_size_km((1000.0, 1000.0), None)


class TestInterconnectionResolution(unittest.TestCase):
    """The same substation on rasters of different resolution must give the same cost in $/yr per location."""

    CRS = CRS.from_string("ESRI:102003")
    ORIGIN = (0.0, 20000.0)          # upper-left corner (x, y) in metres; 20 km x 20 km extent
    EXTENT_M = 20000.0
    TECH_DICT = {1: {'discount_rate': 0.05, 'lifetime_yrs': 20, 'require_pipelines': False}}

    def test_geometries_to_shapes_matches_shapely_mapping(self):
        """4.8: bulk conversion yields the same rasterized result as passing shapely objects, incl. multi-part."""

        geoms = gpd.GeoSeries([Point(2500, 2500),
                               LineString([(0, 1000), (5000, 1000)]),
                               MultiLineString([[(0, 3000), (2000, 3000)], [(3000, 4000), (5000, 4000)]]),
                               Polygon([(500, 500), (1500, 500), (1500, 1500), (500, 1500)]),
                               LineString()], crs=self.CRS)                      # empty geometry is skipped
        values = np.array([1.0, 2.0, 3.0, 4.0, 9.0])

        shapes = list(Interconnection.geometries_to_shapes(geoms.values, values))
        self.assertEqual(4, len(shapes))
        self.assertEqual({'type': 'Point', 'coordinates': [2500.0, 2500.0]}, shapes[0][0])
        self.assertEqual('LineString', shapes[1][0]['type'])
        self.assertEqual('MultiLineString', shapes[2][0]['type'])
        self.assertEqual('Polygon', shapes[3][0]['type'])

        transform = from_origin(0.0, 5000.0, 100.0, 100.0)
        expected = rasterio.features.rasterize(zip(geoms.values[:4], values[:4]), out_shape=(50, 50),
                                               transform=transform, fill=0, dtype='float64')
        got = rasterio.features.rasterize(shapes, out_shape=(50, 50), transform=transform, fill=0, dtype='float64')
        np.testing.assert_array_equal(expected, got)
        self.assertEqual({0.0, 1.0, 2.0, 3.0, 4.0}, set(np.unique(got)))

    def test_only_requested_rasters_are_written(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ic, n = self.build(tmpdir, 1000.0, output_dir=tmpdir, output_dist_file=True)
            written = sorted(f for f in os.listdir(tmpdir) if f.startswith('cerf_transmission_'))
            self.assertEqual(['cerf_transmission_distance_pipelines.tif',
                              'cerf_transmission_distance_substations.tif'], written)

            with rasterio.open(os.path.join(tmpdir, 'cerf_transmission_distance_substations.tif')) as src:
                dist = src.read(1)
                self.assertEqual('float64', src.dtypes[0])
                self.assertTrue(np.isnan(src.nodata))
            np.testing.assert_array_equal(dist, ic.substation_costs)      # '_rval_' is 1.0 so cost == distance

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(NotADirectoryError):
                self.build(tmpdir, 1000.0, output_dir=None, output_cost_file=True)

    @classmethod
    def write_region_raster(cls, path, pixel_m):
        n = int(cls.EXTENT_M / pixel_m)
        transform = from_origin(cls.ORIGIN[0], cls.ORIGIN[1], pixel_m, pixel_m)
        with rasterio.open(path, 'w', driver='GTiff', height=n, width=n, count=1, dtype=rasterio.uint8,
                           crs=cls.CRS, transform=transform, nodata=0) as dst:
            dst.write(np.ones((n, n), dtype=np.uint8), 1)
        return n

    @classmethod
    def build(cls, tmpdir, pixel_m, **kwargs):
        raster = os.path.join(tmpdir, f'regions_{int(pixel_m)}.tif')
        n = cls.write_region_raster(raster, pixel_m)

        # one substation at the centre of the extent; '_rval_' is thous$/km so the cost per km is 1 unit
        substation = os.path.join(tmpdir, f'sub_{int(pixel_m)}.gpkg')
        gpd.GeoDataFrame({'_rval_': [1.0]}, geometry=[Point(cls.EXTENT_M / 2, cls.EXTENT_M / 2)],
                         crs=cls.CRS).to_file(substation)

        # a tiny pipeline segment (length > 0 required) so the packaged CONUS pipeline data is not loaded
        pipeline = os.path.join(tmpdir, f'pipe_{int(pixel_m)}.gpkg')
        gpd.GeoDataFrame({'id': [1]}, geometry=[LineString([(0, 0), (10, 0)])], crs=cls.CRS).to_file(pipeline)

        ic = Interconnection(template_array=np.zeros((1, n, n)),
                             technology_dict=cls.TECH_DICT,
                             technology_order=[1],
                             region_raster_file=raster,
                             region_abbrev_to_name_file=None,
                             region_name_to_id_file=None,
                             substation_file=substation,
                             pipeline_file=pipeline,
                             # explicit cost dicts so no packaged YAML is read (self-contained, no package data)
                             transmission_costs_dict={0: {'min_voltage': -1, 'max_voltage': 9999,
                                                          'thous_dollar_per_km': 1.0}},
                             pipeline_costs_dict={'gas_pipeline_cost': 1.0},
                             **kwargs)
        return ic, n

    def test_cost_is_resolution_independent_in_km(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ic_1km, n1 = self.build(tmpdir, 1000.0)
            ic_500m, n2 = self.build(tmpdir, 500.0)

        self.assertEqual((n1, n1), ic_1km.substation_costs.shape)
        self.assertEqual((2 * n1, 2 * n1), ic_500m.substation_costs.shape)

        # the substation burns into a single cell; the distance at the corner cell is the same physical distance
        #  (in km) irrespective of pixel size, so costs at the same location agree
        far_1km = ic_1km.substation_costs[0, 0]
        far_500m = ic_500m.substation_costs[0, 0]
        # corner-cell centres differ by half a pixel between resolutions, so compare with a tolerance of one 1 km cell
        self.assertAlmostEqual(far_1km, far_500m, delta=1.0)

        # sample the same physical location (5 km, 5 km from origin): row 5 col 5 at 1 km == row 10 col 10 at 500 m
        self.assertAlmostEqual(ic_1km.substation_costs[5, 5], ic_500m.substation_costs[10, 10], delta=0.75)

        # sanity: with the old pixel-count semantics the 500 m raster would be exactly 2x more expensive everywhere
        ratio = ic_500m.substation_costs[10, 10] / ic_1km.substation_costs[5, 5]
        self.assertLess(abs(ratio - 1.0), 0.15)
        self.assertGreater(abs(ratio - 2.0), 0.5)

    def test_one_km_raster_distance_equals_pixel_distance(self):
        """On 1 km pixels the new sampling is bitwise identical to the old pixel-count behaviour."""

        with tempfile.TemporaryDirectory() as tmpdir:
            ic, n = self.build(tmpdir, 1000.0)

        centre = n // 2
        # substation cell has zero distance; its 4-neighbours are exactly 1 km
        self.assertEqual(0.0, ic.substation_costs[centre, centre])
        self.assertEqual(1.0, ic.substation_costs[centre + 1, centre])
        self.assertEqual(1.0, ic.substation_costs[centre, centre - 1])
        self.assertAlmostEqual(np.sqrt(2.0), ic.substation_costs[centre + 1, centre + 1])


if __name__ == '__main__':
    unittest.main()
