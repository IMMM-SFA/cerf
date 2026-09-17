"""Tests for `cerf.process_region.ProcessRegion` on a small synthetic grid (no package data required).

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

import unittest

import numpy as np

from cerf.process_region import ProcessRegion


class TestProcessRegion(unittest.TestCase):

    NROWS, NCOLS = 6, 8
    TECH_ORDER = [1, 2]

    TECH_DICT = {1: {'tech_name': 'a', 'buffer_in_km': 1, 'unit_size_mw': 10, 'operational_life_yrs': 30,
                     'capacity_factor_fraction': 0.5, 'carbon_capture_rate_fraction': 0.0,
                     'fuel_co2_content_tons_per_btu': 0.0, 'fuel_price_usd_per_mmbtu': 1.0,
                     'fuel_price_esc_rate_fraction': 0.0, 'heat_rate_btu_per_kWh': 1.0, 'lifetime_yrs': 30,
                     'variable_om_usd_per_mwh': 1.0, 'variable_om_esc_rate_fraction': 0.0,
                     'carbon_tax_usd_per_ton': 0.0, 'carbon_tax_esc_rate_fraction': 0.0},
                 2: {'tech_name': 'b', 'buffer_in_km': 1, 'unit_size_mw': 20, 'operational_life_yrs': 30,
                     'capacity_factor_fraction': 0.5, 'carbon_capture_rate_fraction': 0.0,
                     'fuel_co2_content_tons_per_btu': 0.0, 'fuel_price_usd_per_mmbtu': 1.0,
                     'fuel_price_esc_rate_fraction': 0.0, 'heat_rate_btu_per_kWh': 1.0, 'lifetime_yrs': 30,
                     'variable_om_usd_per_mwh': 1.0, 'variable_om_esc_rate_fraction': 0.0,
                     'carbon_tax_usd_per_ton': 0.0, 'carbon_tax_esc_rate_fraction': 0.0}}

    @classmethod
    def build(cls, suitability_dtype=np.uint8):
        """Two regions: id 1 on the left half, id 2 on the right half."""

        nrows, ncols = cls.NROWS, cls.NCOLS
        regions = np.ones((nrows, ncols), dtype=np.uint8)
        regions[:, ncols // 2:] = 2

        rng = np.random.default_rng(1)
        n_tech = len(cls.TECH_ORDER)
        shape = (n_tech, nrows, ncols)

        # 0 = suitable, 1 = unsuitable; make tech 2 unsuitable in the top row everywhere
        suitability = np.zeros(shape, dtype=suitability_dtype)
        suitability[1, 0, :] = 1

        lmp = rng.uniform(20, 60, shape)
        ic = rng.uniform(1e5, 5e5, shape)
        nov = rng.uniform(1e5, 9e5, shape)
        nlc = ic - nov
        gen = np.broadcast_to(np.array([1000.0, 2000.0])[:, None, None], shape)
        opc = np.broadcast_to(np.array([5.0, 6.0])[:, None, None], shape)

        xcoords, ycoords = np.meshgrid(np.arange(ncols) * 1000.0, np.arange(nrows) * 1000.0)
        indices_2d = np.arange(nrows * ncols).reshape(nrows, ncols)
        zones = np.ones((nrows, ncols), dtype=np.int32)

        return dict(settings_dict={'run_year': 2010, 'output_directory': None},
                    technology_dict=cls.TECH_DICT,
                    technology_order=cls.TECH_ORDER,
                    expansion_dict={'left': {1: {'tech_name': 'a', 'n_sites': 1}, 2: {'tech_name': 'b', 'n_sites': 1}}},
                    regions_dict={'left': 1, 'right': 2},
                    suitability_arr=suitability, lmp_arr=lmp, generation_arr=gen, operating_cost_arr=opc,
                    nov_arr=nov, ic_arr=ic, nlc_arr=nlc, zones_arr=zones, xcoords=xcoords, ycoords=ycoords,
                    indices_2d=indices_2d, target_region_name='left', randomize=False, seed_value=0,
                    verbose=False, write_output=False, regions_arr=regions, region_bounds=None)

    def test_region_suitability_is_boolean_and_excludes_outside_cells(self):
        kwargs = self.build()
        pr = ProcessRegion(**kwargs)

        unsuitable = pr.suitability_array_region
        self.assertEqual(np.bool_, unsuitable.dtype)
        self.assertEqual((len(self.TECH_ORDER) + 1, self.NROWS, self.NCOLS // 2), unsuitable.shape)
        self.assertTrue(unsuitable[0].all())                       # default layer fully unsuitable
        self.assertTrue(unsuitable[2, 0, :].all())                 # tech 2 top row
        self.assertFalse(unsuitable[1].any())                      # tech 1 suitable everywhere in region
        self.assertEqual((0, self.NROWS, 0, self.NCOLS // 2), (pr.ymin, pr.ymax, pr.xmin, pr.xmax))

        # unsuitable -> +inf in the NLC stack; suitable cells keep their NLC (checked against the pre-siting snapshot
        #  kept by Competition, since the competition excludes cells in the working array as it sites)
        self.assertTrue(np.isinf(pr.suitable_nlc_region[unsuitable]).all())
        np.testing.assert_array_equal(kwargs['nlc_arr'][0, :, :self.NCOLS // 2].flatten(), pr.run_data.nlc_flat_dict[1])

    def test_suitability_dtype_does_not_change_outcome(self):
        """uint8 and float64 (legacy) suitability arrays site the same plants."""

        a = ProcessRegion(**self.build(np.uint8))
        b = ProcessRegion(**self.build(np.float64))
        np.testing.assert_array_equal(a.run_data.sited_array, b.run_data.sited_array)
        self.assertEqual(a.run_data.sited_dict, b.run_data.sited_dict)
        self.assertEqual(2, len(a.run_data.sited_dict['tech_id']))

    def test_metric_views_are_not_copies_and_report_sited_values(self):
        kwargs = self.build()
        pr = ProcessRegion(**kwargs)

        # region metric dicts are 2D views into the staged arrays
        for d, src in ((pr.lmp_flat_dict, kwargs['lmp_arr']), (pr.ic_flat_dict, kwargs['ic_arr'])):
            for ix, tech_id in enumerate(self.TECH_ORDER):
                self.assertEqual(2, d[tech_id].ndim)
                self.assertTrue(np.shares_memory(d[tech_id], src))

        # sited records carry the value of the sited technology at the sited full-grid index
        sd = pr.run_data.sited_dict
        for tech_id, full_ix, lmp, gen, ic, nlc in zip(sd['tech_id'], sd['index'],
                                                       sd['locational_marginal_price_usd_per_mwh'],
                                                       sd['generation_mwh_per_year'],
                                                       sd['interconnection_cost_usd_per_year'],
                                                       sd['net_locational_cost_usd_per_year']):
            row, col = divmod(int(full_ix), self.NCOLS)
            t = self.TECH_ORDER.index(tech_id)
            self.assertLess(col, self.NCOLS // 2)                  # sited inside the left region
            self.assertEqual(kwargs['lmp_arr'][t, row, col], lmp)
            self.assertEqual(kwargs['generation_arr'][t, row, col], gen)
            self.assertEqual(kwargs['ic_arr'][t, row, col], ic)
            self.assertEqual(kwargs['nlc_arr'][t, row, col], nlc)


if __name__ == '__main__':
    unittest.main()
