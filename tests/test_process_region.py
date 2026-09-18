"""Tests for `cerf.process_region.ProcessRegion` and dispatch helpers on a small synthetic grid (no package data).

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

import unittest

import numpy as np

import pandas as pd
from joblib import Parallel, delayed

import cerf.utils as util
from cerf.process import aggregate_results, region_tasks
from cerf.compete import Competition
from cerf.process_region import EmptyRegionResult, ProcessRegion, RegionData, crop_to_region, process_region
from cerf.stage import Stage


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
    def build(cls, suitability_dtype=np.uint8, tied_nlc=False):
        """Two regions: id 1 on the left half, id 2 on the right half.

        With ``tied_nlc`` every cell has the same NLC per technology so site choice is entirely down to the random
        tie-break, which makes RNG behaviour observable.

        """

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
        if tied_nlc:
            nlc = np.broadcast_to(np.array([-1.0, -2.0])[:, None, None], shape).copy()
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

    def test_region_with_no_sites_returns_empty_result_not_none(self):
        """5.5: a zero-site region yields an EmptyRegionResult that aggregates like any other region."""

        kwargs = self.build()
        kwargs['expansion_dict'] = {'left': {1: {'tech_name': 'a', 'n_sites': 0}, 2: {'tech_name': 'b', 'n_sites': 0}}}

        result = process_region(**kwargs)
        self.assertIsInstance(result, EmptyRegionResult)
        self.assertEqual('left', result.target_region_name)
        self.assertEqual(0, len(result.run_data.sited_df))
        self.assertEqual(list(util.empty_sited_dict()), list(result.run_data.sited_df.columns))
        self.assertIsNone(result.run_data.sited_array)
        self.assertEqual(kwargs['expansion_dict']['left'], result.run_data.expansion_dict)
        self.assertIsNot(kwargs['expansion_dict']['left'], result.run_data.expansion_dict)

        # aggregates alongside real results without None checks
        real = ProcessRegion(**self.build())
        df = aggregate_results([result, real])
        self.assertEqual(len(real.run_data.sited_df), len(df))

    def test_unsuitable_from_raster_honours_nodata(self):
        """5.6: declared nodata is unsuitable even when it is 0; NaN nodata handled; 0/1 encoding unchanged."""

        arr = np.array([[0, 1, 0],
                        [255, 0, 1]], dtype=np.uint8)

        # plain 0/1 encoding, no nodata: only the 1s (and the 255) are unsuitable
        np.testing.assert_array_equal([[False, True, False], [True, False, True]],
                                      Stage.unsuitable_from_raster(arr, nodata=None))

        # declared nodata 255 -> still unsuitable (already non-zero) and explicitly flagged
        np.testing.assert_array_equal([[False, True, False], [True, False, True]],
                                      Stage.unsuitable_from_raster(arr, nodata=255))

        # a raster whose nodata is 0 must not make missing cells look suitable
        np.testing.assert_array_equal(np.ones_like(arr, dtype=bool), Stage.unsuitable_from_raster(arr, nodata=0))

        # float raster with NaN nodata
        farr = np.array([[0.0, np.nan], [1.0, 0.0]])
        np.testing.assert_array_equal([[False, True], [True, False]], Stage.unsuitable_from_raster(farr, nodata=np.nan))

    def test_get_region_id_is_case_insensitive_and_reports_choices(self):
        """3.10: mixed-case names resolve; unknown names raise a KeyError that lists the valid names."""

        kwargs = self.build()
        mixed = ProcessRegion(**dict(kwargs, target_region_name='Left'))
        lower = ProcessRegion(**kwargs)
        self.assertEqual(1, mixed.target_region_id)
        self.assertEqual(lower.run_data.sited_dict, mixed.run_data.sited_dict)

        with self.assertRaises(KeyError) as ctx:
            ProcessRegion(**dict(kwargs, target_region_name='nowhere'))
        self.assertIn('nowhere', str(ctx.exception))
        self.assertIn("'left'", str(ctx.exception))
        self.assertIn("'right'", str(ctx.exception))

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


    def test_crop_to_region_matches_full_grid_result(self):
        """Dispatching a cropped bounding box gives exactly the same sited plants as the full grid."""

        kwargs = self.build()
        full = ProcessRegion(**kwargs)

        region_bounds = {1: (0, self.NROWS, 0, self.NCOLS // 2), 2: (0, self.NROWS, self.NCOLS // 2, self.NCOLS)}
        array_keys = ['suitability_arr', 'lmp_arr', 'generation_arr', 'operating_cost_arr', 'nov_arr', 'ic_arr',
                      'nlc_arr', 'zones_arr', 'xcoords', 'ycoords', 'indices_2d', 'regions_arr']
        cropped = crop_to_region(1, region_bounds, **{k: kwargs[k] for k in array_keys})

        # arrays are cut to the bbox, contiguous, and broadcast (spatially constant) metrics collapse to 1D
        self.assertEqual((2, self.NROWS, self.NCOLS // 2), cropped['nlc_arr'].shape)
        self.assertTrue(cropped['nlc_arr'].flags.c_contiguous)
        self.assertEqual((2,), cropped['generation_arr'].shape)
        self.assertEqual((2,), cropped['operating_cost_arr'].shape)
        self.assertEqual({1: (0, self.NROWS, 0, self.NCOLS // 2)}, cropped['region_bounds'])
        self.assertEqual((self.NROWS, self.NCOLS // 2), cropped['indices_2d'].shape)

        other = {k: v for k, v in kwargs.items() if k not in array_keys and k != 'region_bounds'}
        part = ProcessRegion(**other, **cropped)

        np.testing.assert_array_equal(full.run_data.sited_array, part.run_data.sited_array)
        self.assertEqual(full.run_data.sited_dict, part.run_data.sited_dict)   # incl. full-grid index and coords

    def test_region_tasks_crops_only_for_process_backends(self):
        kwargs = self.build()

        class Data:
            pass

        class ModelStub:
            pass

        data = Data()
        for k in ['suitability_arr', 'lmp_arr', 'generation_arr', 'operating_cost_arr', 'nov_arr', 'ic_arr',
                  'nlc_arr', 'zones_arr', 'xcoords', 'ycoords', 'indices_2d', 'regions_arr']:
            setattr(data, k, kwargs[k])
        data.region_bounds = {1: (0, self.NROWS, 0, self.NCOLS // 2), 2: (0, self.NROWS, self.NCOLS // 2, self.NCOLS)}
        data.init_df = None

        model = ModelStub()
        model.settings_dict = kwargs['settings_dict']
        model.technology_dict = kwargs['technology_dict']
        model.technology_order = kwargs['technology_order']
        model.expansion_dict = {'left': kwargs['expansion_dict']['left'],
                                'right': {1: {'tech_name': 'a', 'n_sites': 0}, 2: {'tech_name': 'b', 'n_sites': 1}}}
        model.regions_dict = {'left': 1, 'right': 2}
        model.initialize_site_data = None

        seq = list(region_tasks(model, data, 'sequential'))
        lok = list(region_tasks(model, data, 'loky'))

        self.assertEqual(['left', 'right'], [t['target_region_name'] for t in seq])
        self.assertIsInstance(seq[0]['data'], RegionData)
        self.assertIs(data.nlc_arr, seq[0]['data'].nlc_arr)                        # shared by reference in-process
        self.assertIs(seq[0]['data'], seq[1]['data'])                              # one RegionData for all regions
        self.assertEqual((2, self.NROWS, self.NCOLS // 2), lok[0]['data'].nlc_arr.shape)   # cropped for processes
        self.assertEqual((2, self.NROWS, self.NCOLS - self.NCOLS // 2), lok[1]['data'].nlc_arr.shape)

        # both dispatch modes produce identical sited plants
        for a, b in zip(seq, lok):
            ra, rb = process_region(**a), process_region(**b)
            self.assertEqual(ra.run_data.sited_dict, rb.run_data.sited_dict)

    def test_aggregate_results_single_concat(self):
        kwargs = self.build()
        pr = ProcessRegion(**kwargs)

        df = aggregate_results([pr, None, pr])
        self.assertEqual(2 * len(pr.run_data.sited_df), len(df))
        self.assertEqual(list(util.empty_sited_dict().keys()), list(df.columns))
        self.assertTrue((df.index == np.arange(len(df))).all())

        init = pd.DataFrame(util.empty_sited_dict()).astype(util.sited_dtypes())
        self.assertEqual(0, len(aggregate_results([None], init_df=init)))
        # dtypes survive the concat (string columns are pandas `object`)
        expected = pd.DataFrame(util.empty_sited_dict()).astype(util.sited_dtypes()).dtypes
        for col in util.sited_dtypes():
            self.assertEqual(expected[col], df[col].dtype, col)


    def _model_and_data(self, tied_nlc):
        kwargs = self.build(tied_nlc=tied_nlc)

        class Obj:
            pass

        data = Obj()
        for k in ['suitability_arr', 'lmp_arr', 'generation_arr', 'operating_cost_arr', 'nov_arr', 'ic_arr',
                  'nlc_arr', 'zones_arr', 'xcoords', 'ycoords', 'indices_2d', 'regions_arr']:
            setattr(data, k, kwargs[k])
        data.region_bounds = {1: (0, self.NROWS, 0, self.NCOLS // 2), 2: (0, self.NROWS, self.NCOLS // 2, self.NCOLS)}
        data.init_df = None

        model = Obj()
        model.settings_dict = dict(kwargs['settings_dict'], randomize=False, seed_value=7)
        model.technology_dict = kwargs['technology_dict']
        model.technology_order = kwargs['technology_order']
        model.expansion_dict = {'left': {1: {'tech_name': 'a', 'n_sites': 3}, 2: {'tech_name': 'b', 'n_sites': 2}},
                                'right': {1: {'tech_name': 'a', 'n_sites': 2}, 2: {'tech_name': 'b', 'n_sites': 3}}}
        model.regions_dict = {'left': 1, 'right': 2}
        model.initialize_site_data = None
        return model, data

    def test_region_data_object_and_keyword_arrays_are_equivalent(self):
        """6.2: passing a RegionData or the individual array keyword arguments gives the same result."""

        kwargs = self.build()
        via_kwargs = ProcessRegion(**kwargs)

        data, rest = RegionData.from_kwargs(kwargs)
        self.assertEqual(set(RegionData.field_names()), set(kwargs) - set(rest))
        self.assertNotIn('nlc_arr', rest)
        via_data = ProcessRegion(data=data, **rest)

        self.assertEqual(via_kwargs.run_data.sited_dict, via_data.run_data.sited_dict)
        self.assertIs(data, via_data.data)
        self.assertIs(data.nlc_arr, via_data.nlc_arr)          # accessor properties delegate to the data object

        # from_stage works on anything exposing the field names; crop() round-trips through crop_to_region
        class StageStub:
            pass
        stub = StageStub()
        for k, v in data.as_kwargs().items():
            setattr(stub, k, v)
        stub.region_bounds = {1: (0, self.NROWS, 0, self.NCOLS // 2), 2: (0, self.NROWS, self.NCOLS // 2, self.NCOLS)}
        rd = RegionData.from_stage(stub)
        cropped = rd.crop(1)
        self.assertIsInstance(cropped, RegionData)
        self.assertEqual((2, self.NROWS, self.NCOLS // 2), cropped.nlc_arr.shape)
        self.assertEqual({1: (0, self.NROWS, 0, self.NCOLS // 2)}, cropped.region_bounds)

        # unknown keyword arguments are rejected rather than silently ignored
        with self.assertRaises(TypeError):
            ProcessRegion(data=data, bogus=1, **rest)

    def test_construction_is_separate_from_run(self):
        """6.1: ProcessRegion and Competition can be built for inspection and run explicitly; run() is idempotent."""

        pr = ProcessRegion(**self.build(), auto_run=False)
        self.assertIsNone(pr.run_data)
        self.assertEqual((3, self.NROWS, self.NCOLS // 2), pr.suitable_nlc_region.shape)   # prepared state visible

        self.assertIs(pr, pr.run())
        first = pr.run_data
        self.assertIsNotNone(first)
        self.assertIs(first, pr.run().run_data)                  # idempotent
        self.assertEqual(ProcessRegion(**self.build()).run_data.sited_dict, first.sited_dict)

        comp = Competition(target_region_name='left',
                           settings_dict=pr.settings_dict,
                           technology_dict=pr.technology_dict,
                           technology_order=pr.technology_order,
                           expansion_dict=pr.expansion_dict['left'],
                           lmp_dict=pr.lmp_flat_dict, generation_dict=pr.generation_flat_dict,
                           operating_cost_dict=pr.operating_cost_flat_dict, nov_dict=pr.nov_flat_dict,
                           ic_dict=pr.ic_flat_dict, nlc_mask=pr.mask_nlc(), zones_arr=pr.zones_flat_arr,
                           xcoords=pr.xcoords_region, ycoords=pr.ycoords_region, indices_flat=pr.indices_flat_region,
                           randomize=False, seed_value=0, verbose=False, auto_run=False)
        self.assertIsNone(comp.sited_df)
        self.assertGreater(comp.avail_grids, 0)                  # cheapest map computed at construction
        self.assertEqual(0, len(comp.sited_dict['tech_id']))
        comp.run()
        self.assertEqual(first.sited_dict, comp.sited_dict)
        n = len(comp.sited_dict['tech_id'])
        comp.run()
        self.assertEqual(n, len(comp.sited_dict['tech_id']))    # no double siting

    def test_seeded_results_identical_across_backends_and_order(self):
        """With a local per-competition RNG, seeded siting is independent of backend, thread scheduling and order."""

        model, data = self._model_and_data(tied_nlc=True)

        def run(method, n_jobs, reverse=False):
            tasks = list(region_tasks(model, data, method))
            if reverse:
                tasks = tasks[::-1]
            results = Parallel(n_jobs=n_jobs, backend=method)(delayed(process_region)(**t) for t in tasks)
            df = aggregate_results(results)
            return df.sort_values(['region_name', 'tech_id', 'index']).reset_index(drop=True)

        seq = run('sequential', 1)
        self.assertEqual(10, len(seq))

        # perturb the global RNG between runs; it must have no effect
        np.random.seed(3)
        pd.testing.assert_frame_equal(seq, run('sequential', 1, reverse=True))

        # repeated threaded runs are identical to the sequential run (previously nondeterministic via global seed)
        for _ in range(3):
            pd.testing.assert_frame_equal(seq, run('threading', 2))


if __name__ == '__main__':
    unittest.main()
