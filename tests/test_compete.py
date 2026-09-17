import copy
import unittest

import numpy as np

from cerf.compete import Competition


class TestCompete(unittest.TestCase):

    EXPANSION_PLAN = {1: {'n_sites': 1, 'tech_name': 'test1'},
                      2: {'n_sites': 1, 'tech_name': 'test2'},
                      3: {'n_sites': 1, 'tech_name': 'test3'}}  # n sites per tech

    SAMPLE_TECH_DICT = {'buffer_in_km': 1,
                        'lifetime_yrs': 60,
                        'operational_life_yrs': 60,
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
                       'operational_life_yrs': [60, 60, 60],
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

        # ensure the remaining-site counts are exposed on the competition object
        self.assertEqual(TestCompete.COMP_EXP_PLAN, comp.expansion_dict)

        # check sited dict match
        self.assertEqual(TestCompete.COMP_SITED_DICT, comp.sited_dict)

    def _run(self, nlc_mask, expansion_plan=None):
        fake_dict, fake_flat_array = self.create_proxy_arrays()
        return Competition(target_region_name='test',
                           settings_dict=TestCompete.SETTINGS_DICT,
                           technology_dict=TestCompete.TECH_DICT,
                           technology_order=TestCompete.TECH_ORDER,
                           expansion_dict=expansion_plan or TestCompete.EXPANSION_PLAN,
                           lmp_dict=fake_dict, generation_dict=fake_dict, operating_cost_dict=fake_dict,
                           nov_dict=fake_dict, ic_dict=fake_dict,
                           nlc_mask=nlc_mask,
                           zones_arr=fake_flat_array.astype(np.int32),
                           xcoords=fake_flat_array, ycoords=fake_flat_array, indices_flat=fake_flat_array,
                           randomize=False, seed_value=0, verbose=False)

    def test_inf_array_input_matches_masked_input(self):
        """A plain float array with +inf for unsuitable cells must give the same result as the masked array."""

        masked = self.create_masked_nlc_array()
        plain = masked.astype(np.float64).filled(np.inf)
        self.assertFalse(np.ma.isMaskedArray(plain))

        comp_masked = self._run(self.create_masked_nlc_array())
        comp_plain = self._run(plain)

        np.testing.assert_array_equal(comp_masked.sited_array, comp_plain.sited_array)
        np.testing.assert_array_equal(TestCompete.COMP_SITED, comp_plain.sited_array)
        self.assertEqual(comp_masked.sited_dict, comp_plain.sited_dict)

        # the working array is always a plain, contiguous float64 array internally
        self.assertFalse(np.ma.isMaskedArray(comp_masked.nlc_mask))
        self.assertEqual(np.float64, comp_masked.nlc_mask.dtype)

    def test_default_layer_wins_only_when_nothing_available(self):
        """Layer 0 (all +inf) is the argmin only for cells where every technology is +inf."""

        plain = self.create_masked_nlc_array().astype(np.float64).filled(np.inf)
        comp = self._run(plain)

        # after competition, every cell is either sited/buffered/unsuitable (0) or has a finite cheapest tech
        finite_any = np.isfinite(comp.nlc_mask[1:]).any(axis=0)
        np.testing.assert_array_equal(comp.cheapest_arr > 0, finite_any)

    def test_exclusion_helpers(self):
        """exclude_cells / exclude_technology set +inf and update_cheapest reflects it."""

        plain = self.create_masked_nlc_array().astype(np.float64).filled(np.inf)
        comp = self._run(plain, expansion_plan={1: {'n_sites': 0, 'tech_name': 'a'},
                                                2: {'n_sites': 0, 'tech_name': 'b'},
                                                3: {'n_sites': 0, 'tech_name': 'c'}})

        # all techs had 0 sites -> every layer excluded before competition -> nothing available
        self.assertTrue(np.isinf(comp.nlc_mask).all())
        self.assertEqual(0, comp.avail_grids)
        self.assertEqual(0, len(comp.sited_dict['tech_id']))

        # fresh object: exclude two flat cells for all techs and check the 2D view aliases the 3D array
        comp = self._run(self.create_masked_nlc_array().astype(np.float64).filled(np.inf))
        comp.nlc_mask[1:] = 1.0
        comp.nlc_mask[0] = np.inf
        ncols = comp.nlc_mask.shape[2]
        comp.exclude_cells(np.array([0, ncols]))                   # flat 0 -> (0, 0); flat ncols -> (1, 0)
        self.assertTrue(np.isinf(comp.nlc_mask[1:, 0, 0]).all())
        self.assertTrue(np.isinf(comp.nlc_mask[1:, 1, 0]).all())
        self.assertEqual(1.0, comp.nlc_mask[1, 0, 1])
        comp.exclude_technology(2)
        self.assertTrue(np.isinf(comp.nlc_mask[2]).all())
        comp.update_cheapest()
        self.assertEqual(0, comp.cheapest_arr[0, 0])
        self.assertEqual(1, comp.cheapest_arr[0, 1])

    def test_metric_views_2d_match_flat_arrays(self):
        """2D region views of the metric arrays give the same sited values as pre-flattened arrays."""

        fake_dict, fake_flat_array = self.create_proxy_arrays()
        nlc_mask = self.create_masked_nlc_array().astype(np.float64).filled(np.inf)

        # distinct per-metric values so a wrong lookup would be visible
        lmp_2d = {i: TestCompete.NLC_ARR[i - 1] * 10.0 for i in fake_dict}
        gen_2d = {i: np.full(TestCompete.NLC_ARR[0].shape, 100.0 * i) for i in fake_dict}   # scalar-like per tech
        flat = lambda d: {i: a.flatten() for i, a in d.items()}
        grid_index = np.arange(fake_flat_array.size)

        comp_2d = Competition(target_region_name='test',
                              settings_dict=TestCompete.SETTINGS_DICT,
                              technology_dict=TestCompete.TECH_DICT,
                              technology_order=TestCompete.TECH_ORDER,
                              expansion_dict=TestCompete.EXPANSION_PLAN,
                              lmp_dict=lmp_2d, generation_dict=gen_2d, operating_cost_dict=gen_2d,
                              nov_dict=lmp_2d, ic_dict=lmp_2d,
                              nlc_mask=nlc_mask.copy(),
                              zones_arr=fake_flat_array.astype(np.int32),
                              xcoords=fake_flat_array, ycoords=fake_flat_array, indices_flat=grid_index,
                              randomize=False, seed_value=0, verbose=False)

        comp_flat = Competition(target_region_name='test',
                                settings_dict=TestCompete.SETTINGS_DICT,
                                technology_dict=TestCompete.TECH_DICT,
                                technology_order=TestCompete.TECH_ORDER,
                                expansion_dict=TestCompete.EXPANSION_PLAN,
                                lmp_dict=flat(lmp_2d), generation_dict=flat(gen_2d), operating_cost_dict=flat(gen_2d),
                                nov_dict=flat(lmp_2d), ic_dict=flat(lmp_2d),
                                nlc_mask=nlc_mask.copy(),
                                zones_arr=fake_flat_array.astype(np.int32),
                                xcoords=fake_flat_array, ycoords=fake_flat_array, indices_flat=grid_index,
                                randomize=False, seed_value=0, verbose=False)

        np.testing.assert_array_equal(TestCompete.COMP_SITED, comp_2d.sited_array)
        self.assertEqual(comp_flat.sited_dict, comp_2d.sited_dict)

        # the reported LMP is the value of the *sited* technology at the sited cell
        for tech_id, ix, lmp in zip(comp_2d.sited_dict['tech_id'], comp_2d.sited_dict['index'],
                                    comp_2d.sited_dict['locational_marginal_price_usd_per_mwh']):
            self.assertEqual(lmp_2d[tech_id].flatten()[int(ix)], lmp)
            self.assertEqual(100.0 * tech_id, comp_2d.metric_at(gen_2d[tech_id], int(ix)))

    def test_competition_does_not_mutate_expansion_plan(self):
        """The caller's expansion plan must be unchanged and a second run must site the same plants."""

        expansion_plan = copy.deepcopy(TestCompete.EXPANSION_PLAN)
        snapshot = copy.deepcopy(expansion_plan)

        results = []
        for _ in range(2):
            comp = Competition(target_region_name='test',
                               settings_dict=TestCompete.SETTINGS_DICT,
                               technology_dict=TestCompete.TECH_DICT,
                               technology_order=TestCompete.TECH_ORDER,
                               expansion_dict=expansion_plan,
                               lmp_dict=self.create_proxy_arrays()[0],
                               generation_dict=self.create_proxy_arrays()[0],
                               operating_cost_dict=self.create_proxy_arrays()[0],
                               nov_dict=self.create_proxy_arrays()[0],
                               ic_dict=self.create_proxy_arrays()[0],
                               nlc_mask=self.create_masked_nlc_array(),
                               zones_arr=self.create_proxy_arrays()[1].astype(np.int32),
                               xcoords=self.create_proxy_arrays()[1],
                               ycoords=self.create_proxy_arrays()[1],
                               indices_flat=self.create_proxy_arrays()[1],
                               randomize=False,
                               seed_value=0,
                               verbose=False)
            results.append(comp)

            # caller's plan untouched; competition's private copy reflects remaining sites
            self.assertEqual(snapshot, expansion_plan)
            self.assertIsNot(expansion_plan, comp.expansion_dict)
            self.assertEqual(TestCompete.COMP_EXP_PLAN, comp.expansion_dict)

        # a second competition with the same (unmutated) plan sites the same plants rather than zero
        np.testing.assert_array_equal(results[0].sited_array, results[1].sited_array)
        np.testing.assert_array_equal(TestCompete.COMP_SITED, results[1].sited_array)


if __name__ == '__main__':
    unittest.main()
