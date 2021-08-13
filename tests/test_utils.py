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