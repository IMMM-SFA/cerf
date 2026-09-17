"""Tests for CERF utilities.

:author:   Chris R. Vernon
:email:    chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

import unittest

import numpy as np

import cerf.utils as util


class TestUtils(unittest.TestCase):
    """Tests for the NOV calculations."""

    # comparison data
    COMP_BUFF_FLAT_0 = np.array([[7., 7., 7., 0., 0.],
                                 [7., 7., 7., 0., 0.],
                                 [7., 7., 7., 0., 0.],
                                 [0., 0., 0., 0., 0.]])

    COMP_BUFF_FLAT_0_LIST = [0, 1, 2, 5, 6, 7, 10, 11, 12]

    COMP_BUFF_FLAT_19 = np.array([[0., 0., 0., 0., 0.],
                                  [0., 0., 7., 7., 7.],
                                  [0., 0., 7., 7., 7.],
                                  [0., 0., 7., 7., 7.]])

    COMP_BUFF_FLAT_19_LIST = [17, 18, 19, 12, 13, 14, 7, 8, 9]

    @staticmethod
    def reference_bounds(arr):
        """Per-region bounds derived the way `ProcessRegion` used to (np.where per region)."""

        out = {}
        for rid in np.unique(arr):
            idx = np.where(arr == rid)
            out[int(rid)] = (int(idx[0].min()), int(idx[0].max()) + 1, int(idx[1].min()), int(idx[1].max()) + 1)
        return out

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
        self.assertEqual(TestUtils.COMP_BUFF_FLAT_0_LIST, buff_0)

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
        self.assertEqual(TestUtils.COMP_BUFF_FLAT_19_LIST, buff_19)


if __name__ == '__main__':
    unittest.main()