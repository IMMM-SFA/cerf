import unittest

import numpy as np

from cerf.compete import Competition


class TestCompete(unittest.TestCase):

    EXPANSION_PLAN = {1: {'n_sites': 1, 'tech_name': 'test1'},
                      2: {'n_sites': 1, 'tech_name': 'test2'},
                      3: {'n_sites': 1, 'tech_name': 'test3'}}  # n sites per tech

    SAMPLE_TECH_DICT = {'buffer_in_km': 1,
                        'lifetime_yrs': 60,
                        'tech_name': 'test',
                        'unit_size_mw': 80,
                        'capacity_factor_fraction': 0.1,
                        'carbon_capture_rate_fraction': 0.0,
                        'fuel_co2_content_tons_per_btu': 0.1,
                        'fuel_price_usd_per_mmbtu': 1.0,
                        'fuel_price_esc_rate_fraction': 1.0,
                        'heat_rate_btu_per_kWh': 1.0,
                        'variable_om_usd_per_mwh': 1.0,
                        'variable_om_esc_rate_fraction': 1.0,
                        'carbon_tax_usd_per_ton': 0.0,
                        'carbon_tax_esc_rate_fraction': 1.0}

    TECH_DICT = {1: SAMPLE_TECH_DICT,
                 2: SAMPLE_TECH_DICT,
                 3: SAMPLE_TECH_DICT}  # buffer per tech

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

    # trimmed down settings dictionary
    SETTINGS_DICT = {'run_year': 2010}

    # expected outcome
    COMP_SITED = np.array([[0, 2, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0, 0],
                           [0, 1, 0, 3, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0, 0]])

    COMP_EXP_PLAN = {1: {'n_sites': 0, 'tech_name': 'test1'},
                     2: {'n_sites': 0, 'tech_name': 'test2'},
                     3: {'n_sites': 0, 'tech_name': 'test3'}}

    COMP_SITED_DICT = {'region_name': ['test', 'test', 'test'],
                       'index': [2.4, 3.2, 3.2],
                       'capacity_factor_fraction': [0.1, 0.1, 0.1],
                       'carbon_capture_rate_fraction': [0.0, 0.0, 0.0],
                       'carbon_tax_esc_rate_fraction': [1.0, 1.0, 1.0],
                       'carbon_tax_usd_per_ton': [0.0, 0.0, 0.0],
                       'fuel_co2_content_tons_per_btu': [0.1, 0.1, 0.1],
                       'fuel_price_esc_rate_fraction': [1.0, 1.0, 1.0],
                       'fuel_price_usd_per_mmbtu': [1.0, 1.0, 1.0],
                       'generation_mwh_per_year': [2.4, 1.0, 3.2],
                       'lifetime_yrs': [60, 60, 60],
                       'heat_rate_btu_per_kWh': [1.0, 1.0, 1.0],
                       'tech_id': [1, 2, 3],
                       'tech_name': ['test', 'test', 'test'],
                       'unit_size_mw': [80, 80, 80],
                       'xcoord': [2.4, 3.2, 3.2],
                       'ycoord': [2.4, 3.2, 3.2],
                       'buffer_in_km': [1, 1, 1],
                       'sited_year': [2010, 2010, 2010],
                       'retirement_year': [2070, 2070, 2070],
                       'lmp_zone': [2, 3, 3],
                       'variable_om_esc_rate_fraction': [1.0, 1.0, 1.0],
                       'variable_om_usd_per_mwh': [1.0, 1.0, 1.0],
                       'operating_cost_usd_per_year': [2.4, 1.0, 3.2],
                       'locational_marginal_price_usd_per_mwh': [2.4, 1.0, 3.2],
                       'net_operational_value_usd_per_year': [2.4, 1.0, 3.2],
                       'interconnection_cost_usd_per_year': [2.4, 1.0, 3.2],
                       'net_locational_cost_usd_per_year': [2.4, 1.0, 3.2]}

    @classmethod
    def create_masked_nlc_array(cls):
        """Create a masked NLC array by suitability to use in testing."""

        # insert zero array and mask it as index [0, :, :] so the tech_id 0 will always be min if nothing is left to site
        arr = np.insert(cls.NLC_ARR, 0, np.zeros_like(cls.NLC_ARR[0, :, :]), axis=0)

        # exclude all area for the proxy dimension
        exc = np.insert(cls.SUIT_ARR, 0, np.ones_like(cls.SUIT_ARR[0, :, :]), axis=0)

        # apply exclusion
        return np.ma.masked_array(arr, exc)

    @classmethod
    def create_proxy_arrays(cls):
        """Create fake arrays to feed into the class."""

        # fake dictionary
        fake_dict = {i + 1: cls.NLC_ARR[i, :, :].flatten() for i in range(cls.NLC_ARR.shape[0])}

        # fake flat array
        fake_flat_arr = fake_dict[1].flatten()

        return fake_dict, fake_flat_arr

    def test_competition(self):
        """Ensure that the competition algorithm performs as expected."""

        # create a fake NLC masked array to use for testing
        nlc_arr = self.create_masked_nlc_array()

        # proxy dictionary and arrays
        fake_dict, fake_flat_array = self.create_proxy_arrays()

        comp = Competition(target_region_name='test',
                           settings_dict=TestCompete.SETTINGS_DICT,
                           technology_dict=TestCompete.TECH_DICT,
                           technology_order=TestCompete.TECH_ORDER,
                           expansion_dict=TestCompete.EXPANSION_PLAN,
                           lmp_dict=fake_dict,
                           generation_dict=fake_dict,
                           operating_cost_dict=fake_dict,
                           nov_dict=fake_dict,
                           ic_dict=fake_dict,
                           nlc_mask=nlc_arr,
                           zones_arr=fake_flat_array.astype(np.int32),
                           xcoords=fake_flat_array,
                           ycoords=fake_flat_array,
                           indices_flat=fake_flat_array,
                           randomize=False,
                           seed_value=0,
                           verbose=False)

        # test output equality
        np.testing.assert_array_equal(TestCompete.COMP_SITED, comp.sited_array)

        # ensure the expansion plan was updated
        self.assertEqual(TestCompete.COMP_EXP_PLAN, comp.expansion_dict)

        # check sited dict match
        self.assertEqual(TestCompete.COMP_SITED_DICT, comp.sited_dict)


if __name__ == '__main__':
    unittest.main()
