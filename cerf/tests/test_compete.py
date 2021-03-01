import unittest

import numpy as np

from cerf.compete import Competition


class TestCompete(unittest.TestCase):

    EXPANSION_PLAN = {1: 1, 2: 1, 3: 1}  # n sites per tech
    TECH_DICT = {1: {'buffer_in_km': 1}, 2: {'buffer_in_km': 1}, 3: {'buffer_in_km': 1}}  # buffer per tech
    TECH_ORDER = [1, 2, 3]

    # proxy NLC array
    NLC_ARR = np.array([[[1.2, 3.2, 3, 3.2, 3, 3.2, 3],
                         [2.4, 5, 2.4, 3.2, 3, 3.2, 3],
                         [7, 2.4, 9, 3.2, 3, 3.2, 3],
                         [2.4, 5, 2.4, 3.2, 3, 3.2, 3]],
                        [[2, 1, 1.4, 3.2, 3, 3.2, 3],
                         [5, 5, 7, 3.2, 3, 3.2, 3],
                         [1, 9, 3, 3.2, 3, 3.2, 3],
                         [2.4, 5, 2.4, 3.2, 3, 3.2, 3]],
                        [[0, 1, 0, 3.2, 3, 3.2, 3],
                         [5, 4, 7, 3.2, 3, 3.2, 3],
                         [1, 9, 9, 3.2, 3, 3.2, 3],
                         [2.4, 5, 2.4, 3.2, 3, 3.2, 3]]])

    # excluded by suitability 1=not suitable, 0=suitable
    SUIT_ARR = np.array([[[0, 0, 1, 0, 1, 0, 1], [1, 0, 1, 0, 1, 0, 1], [0, 0, 1, 0, 1, 0, 1], [1, 0, 1, 0, 1, 0, 1]],
                        [[1, 0, 1, 0, 1, 0, 1], [1, 0, 1, 0, 1, 0, 1], [1, 0, 0, 0, 1, 0, 1], [1, 0, 1, 0, 1, 0, 1]],
                        [[0, 0, 0, 0, 1, 0, 1], [0, 0, 0, 0, 1, 0, 1], [1, 1, 1, 0, 1, 0, 1], [1, 0, 1, 0, 1, 0, 1]]])

    # expected outcome
    COMP_SITED = np.array([[0, 2, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 3, 0],
                           [0, 1, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0, 0]])

    COMP_EXP_PLAN = {1: 0, 2: 0, 3: 0}

    @classmethod
    def create_masked_nlc_array(cls):
        """Create a masked NLC array by suitability to use in testing."""

        # insert zero array and mask it as index [0, :, :] so the tech_id 0 will always be min if nothing is left to site
        arr = np.insert(cls.NLC_ARR, 0, np.zeros_like(cls.NLC_ARR[0, :, :]), axis=0)

        # exclude all area for the proxy dimension
        exc = np.insert(cls.SUIT_ARR, 0, np.ones_like(cls.SUIT_ARR[0, :, :]), axis=0)

        # apply exclusion
        return np.ma.masked_array(arr, exc)

    def test_competetion(self):
        """Ensure that the competition algorithm performs as expected."""

        # create a fake NLC masked array to use for testing
        nlc_arr = self.create_masked_nlc_array()

        comp = Competition(technology_dict=TestCompete.TECH_DICT,
                           technology_order=TestCompete.TECH_ORDER,
                           expansion_dict=TestCompete.EXPANSION_PLAN,
                           nlc_mask=nlc_arr,
                           randomize=False,
                           seed_value=0,
                           verbose=False)

        # test output equality
        np.testing.assert_array_equal(TestCompete.COMP_SITED, comp.sited_array)

        # ensure the expansion plan was updated
        self.assertEqual(TestCompete.COMP_EXP_PLAN, comp.expansion_dict)


if __name__ == '__main__':
    unittest.main()
