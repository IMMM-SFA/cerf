"""Tests for CERF utilities.

:author:   Chris R. Vernon
:email:    chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

import os
import tempfile
import unittest

import numpy as np
import pandas as pd
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_origin

import cerf.utils as util


class TestUtils(unittest.TestCase):
    """Tests for the NOV calculations."""

    # comparison data
    COMP_BUFF_FLAT_0 = np.array([[7., 7., 7., 0., 0.],
                                 [7., 7., 7., 0., 0.],
                                 [7., 7., 7., 0., 0.],
                                 [0., 0., 0., 0., 0.]])

    # buffered indices are returned sorted (row-major) as an integer array
    COMP_BUFF_FLAT_0_LIST = [0, 1, 2, 5, 6, 7, 10, 11, 12]

    COMP_BUFF_FLAT_19 = np.array([[0., 0., 0., 0., 0.],
                                  [0., 0., 7., 7., 7.],
                                  [0., 0., 7., 7., 7.],
                                  [0., 0., 7., 7., 7.]])

    COMP_BUFF_FLAT_19_LIST = [7, 8, 9, 12, 13, 14, 17, 18, 19]

    @staticmethod
    def reference_bounds(arr):
        """Per-region bounds derived the way `ProcessRegion` used to (np.where per region)."""

        out = {}
        for rid in np.unique(arr):
            idx = np.where(arr == rid)
            out[int(rid)] = (int(idx[0].min()), int(idx[0].max()) + 1, int(idx[1].min()), int(idx[1].max()) + 1)
        return out

    def test_sited_dtypes_cover_every_sited_column(self):
        """3.11: every column of the sited dictionary has an explicit dtype and nothing extra is declared."""

        self.assertEqual(set(util.empty_sited_dict()), set(util.sited_dtypes()))

        # an empty frame typed with sited_dtypes has no `object` columns except the two string fields
        df = pd.DataFrame(util.empty_sited_dict()).astype(util.sited_dtypes())
        object_cols = [c for c in df.columns if df[c].dtype == object]
        self.assertEqual(['region_name', 'tech_name'], object_cols)

    def test_raster_to_coord_arrays_cell_centres_and_no_open_handle(self):
        """3.9: coordinates are cell centres from the affine transform and the file is closed afterwards."""

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'template.tif')
            transform = from_origin(100.0, 500.0, 10.0, 20.0)   # x0=100, y0=500 (top), 10 m wide, 20 m tall
            with rasterio.open(path, 'w', driver='GTiff', height=3, width=4, count=1, dtype=rasterio.uint8,
                               crs=CRS.from_epsg(32617), transform=transform) as dst:
                dst.write(np.zeros((3, 4), dtype=np.uint8), 1)

            x, y = util.raster_to_coord_arrays(path)

            # the file must not be held open: on every platform a closed dataset can be removed
            os.remove(path)

        self.assertEqual((3, 4), x.shape)
        self.assertEqual((3, 4), y.shape)
        np.testing.assert_array_equal([105.0, 115.0, 125.0, 135.0], x[0])
        np.testing.assert_array_equal([490.0, 470.0, 450.0], y[:, 0])
        self.assertTrue((x == x[0]).all())
        self.assertTrue((y == y[:, [0]]).all())

    def test_region_bounding_boxes_matches_np_where(self):
        """Bounds must equal the per-region np.where derivation, including a 0 background and disjoint regions."""

        arr = np.array([[0, 0, 1, 1, 0],
                        [0, 2, 1, 0, 0],
                        [3, 2, 0, 0, 4],
                        [3, 0, 0, 4, 4],
                        [0, 0, 0, 0, 3]], dtype=np.uint8)   # region 3 is disjoint

        bounds = util.region_bounding_boxes(arr)

        self.assertEqual(self.reference_bounds(arr), bounds)
        self.assertEqual((0, 2, 2, 4), bounds[1])
        self.assertEqual((2, 5, 0, 5), bounds[3])   # spans both disjoint pieces
        self.assertIn(0, bounds)                    # background id is reported too

        # slicing with the bounds captures every cell of the region
        for rid, (ymin, ymax, xmin, xmax) in bounds.items():
            self.assertEqual(np.sum(arr == rid), np.sum(arr[ymin:ymax, xmin:xmax] == rid))

    def test_region_bounding_boxes_random_and_signed(self):
        """Random integer rasters with negative / large ids agree with the reference derivation."""

        rng = np.random.default_rng(0)
        arr = rng.integers(-3, 60, size=(40, 55), dtype=np.int32)
        arr[arr == 7] = 250  # large, sparse id

        self.assertEqual(self.reference_bounds(arr), util.region_bounding_boxes(arr))

    def test_region_bounding_boxes_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            util.region_bounding_boxes(np.zeros((2, 2, 2), dtype=np.int32))
        with self.assertRaises(TypeError):
            util.region_bounding_boxes(np.zeros((2, 2), dtype=np.float64))

    def test_buffer_flat_array(self):
        """Test to make sure the buffer flat array function if working correctly."""

        # create sample array
        arr = np.zeros(shape=(4, 5))

        # flatten array
        arr_1d = arr.flatten()

        # buffer top left corner by two cells and set the value to 7
        arr_1d_0, buff_0 = util.buffer_flat_array(target_index=0,
                                                  arr=arr_1d.copy(),
                                                  nrows=arr.shape[0],
                                                  ncols=arr.shape[1],
                                                  ncells=2,
                                                  set_value=7)

        # reshape to 2D
        arr_2d_0 = arr_1d_0.reshape(arr.shape)

        # compare array
        np.testing.assert_array_equal(TestUtils.COMP_BUFF_FLAT_0, arr_2d_0)

        # compare buffer indices
        self.assertIsInstance(buff_0, np.ndarray)
        self.assertEqual(TestUtils.COMP_BUFF_FLAT_0_LIST, buff_0.tolist())

        # buffer bottom right corner by two cells and set the value to 7
        arr_1d_19, buff_19 = util.buffer_flat_array(target_index=19,
                                                    arr=arr_1d.copy(),
                                                    nrows=arr.shape[0],
                                                    ncols=arr.shape[1],
                                                    ncells=2,
                                                    set_value=7)

        # reshape to 2D
        arr_2d_19 = arr_1d_19.reshape(arr.shape)

        # compare array
        np.testing.assert_array_equal(TestUtils.COMP_BUFF_FLAT_19, arr_2d_19)

        # compare buffer indices
        self.assertEqual(TestUtils.COMP_BUFF_FLAT_19_LIST, buff_19.tolist())

    def test_buffer_window_and_indices_match_reference(self):
        """4.7: window slices / index arrays equal a brute-force neighbourhood for every cell and radius, incl. edges."""

        nrows, ncols = 5, 7
        for ncells in (0, 1, 2, 4, 10):
            for target in range(nrows * ncols):
                r, c = divmod(target, ncols)
                expected = sorted(rr * ncols + cc
                                  for rr in range(max(r - ncells, 0), min(r + ncells + 1, nrows))
                                  for cc in range(max(c - ncells, 0), min(c + ncells + 1, ncols)))

                got = util.buffer_flat_indices(target, nrows, ncols, ncells)
                self.assertEqual(expected, got.tolist(), (target, ncells))
                self.assertEqual(np.intp, got.dtype)

                rows, cols = util.buffer_window(target, nrows, ncols, ncells)
                grid = np.zeros((nrows, ncols), dtype=bool)
                grid[rows, cols] = True
                self.assertEqual(expected, np.flatnonzero(grid).tolist())

        # the last row is buffered correctly (the legacy implementation's `<= ngrids` bounds check was off by one
        #  but harmless; the new one is exact)
        last = nrows * ncols - 1
        self.assertEqual([last - ncols - 1, last - ncols, last - 1, last],
                         util.buffer_flat_indices(last, nrows, ncols, 1).tolist())

        with self.assertRaises(IndexError):
            util.buffer_flat_indices(nrows * ncols, nrows, ncols, 1)
        with self.assertRaises(IndexError):
            util.buffer_flat_indices(-1, nrows, ncols, 1)


if __name__ == '__main__':
    unittest.main()