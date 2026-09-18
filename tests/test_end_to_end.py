"""End-to-end tests on the packaged 2010 CONUS sample (evaluation item 7.1).

These cover the code paths the unit tests cannot reach without real data: `Stage`, `process.run` / `cerf_parallel`
(every backend), `Model.run_single_region`, `utils.ingest_sited_data` and `outputs.plot_siting`. They require the
Zenodo package-data supplement and take several seconds, so they are marked ``package_data`` and ``slow``; the
sequential result is checked against the seeded reference in ``benchmark/reference`` so this suite doubles as the
regression gate that `benchmark/run_reference.py --compare` provides on the command line.

"""

import importlib.util
import os
import tempfile
import unittest

import matplotlib
import numpy as np
import pandas as pd
import pytest

import cerf
import cerf.utils as util
from cerf.process import cerf_parallel, aggregate_results

matplotlib.use('Agg')

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCE_MODULE = os.path.join(REPO_ROOT, 'benchmark', 'run_reference.py')


def load_reference_module():
    """Import `benchmark/run_reference.py` (not a package) for its config builder and comparison helpers."""

    spec = importlib.util.spec_from_file_location('run_reference', REFERENCE_MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


@pytest.mark.package_data
@pytest.mark.slow
class TestEndToEnd(unittest.TestCase):
    """Full CONUS 2010 run with ``randomize=False, seed_value=0``; staged once for the whole class."""

    @classmethod
    def setUpClass(cls):
        cls.ref = load_reference_module()
        cls.config = cls.ref.build_config()

        cls.model = cerf.Model(config_dict=cls.config, log_level='warning')
        cls.data = cls.model.stage()
        cls.df_sequential = cerf_parallel(model=cls.model, data=cls.data, write_output=False, n_jobs=1,
                                          method='sequential')

    @classmethod
    def tearDownClass(cls):
        cls.model.close_logger()

    def test_sequential_run_matches_seeded_reference(self):
        """The staged + sequential result reproduces the stored reference (1838 sites) exactly."""

        self.assertEqual(len(self.df_sequential), len(pd.read_csv(self.ref.REFERENCE_FILE)))
        self.ref.compare(self.df_sequential)

    def test_threading_backend_matches_sequential(self):
        """Per-competition RNG (5.3) makes the threaded result independent of scheduling."""

        df = cerf_parallel(model=self.model, data=self.data, write_output=False, n_jobs=2, method='threading')

        pd.testing.assert_frame_equal(self.ref.normalize(df), self.ref.normalize(self.df_sequential))

    def test_public_run_writes_csv_and_matches(self):
        """`cerf.run()` (generate_model → stage → cerf_parallel → CSV) end to end."""

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = self.ref.build_config()
            cfg['settings']['output_directory'] = tmpdir

            df = cerf.run(config_dict=cfg, write_output=True, n_jobs=1, method='sequential', log_level='warning')

            out_csv = os.path.join(tmpdir, 'cerf_sited_2010_conus.csv')
            self.assertTrue(os.path.isfile(out_csv))

            written = pd.read_csv(out_csv, dtype=util.sited_dtypes())
            pd.testing.assert_frame_equal(self.ref.normalize(written), self.ref.normalize(df))

        pd.testing.assert_frame_equal(self.ref.normalize(df), self.ref.normalize(self.df_sequential))

    def test_run_single_region_matches_full_run_subset(self):
        """`Model.run_single_region` sites a region exactly as the all-region run does."""

        model = cerf.Model(config_dict=self.config, log_level='warning')
        result = model.run_single_region('rhode_island', write_output=False)

        expected = self.df_sequential.loc[self.df_sequential['region_name'] == 'rhode_island']
        self.assertGreater(len(expected), 0)

        pd.testing.assert_frame_equal(self.ref.normalize(result.run_data.sited_df), self.ref.normalize(expected))

        # the region result also carries the 2D sited technology array for the region's bounding box
        self.assertEqual(int((result.run_data.sited_array > 0).sum()), len(expected))

    def test_ingest_sited_data_marks_sites_and_buffers(self):
        """The initialisation path locates previously sited plants on the grid and buffers them."""

        init_arr, active = util.ingest_sited_data(run_year=2010,
                                                  x_array=self.data.xcoords,
                                                  siting_data=self.df_sequential,
                                                  template_raster_file=self.model.settings_dict['region_raster_file'])

        # all reference sites retire after 2010, so all are active and their coordinates map back to their index
        self.assertEqual(len(active), len(self.df_sequential))
        np.testing.assert_array_equal(active['index'].to_numpy(), self.df_sequential['index'].to_numpy())

        self.assertEqual(init_arr.shape, self.data.xcoords.shape)
        self.assertEqual(init_arr.dtype, np.int8)

        flat = init_arr.ravel()
        self.assertTrue(np.all(flat[self.df_sequential['index'].to_numpy()] == 1))
        self.assertGreater(int(flat.sum()), len(self.df_sequential))  # buffers add cells beyond the sites

        # retired plants are dropped
        _, none_active = util.ingest_sited_data(run_year=2200,
                                                x_array=self.data.xcoords,
                                                siting_data=self.df_sequential,
                                                template_raster_file=self.model.settings_dict['region_raster_file'])
        self.assertEqual(len(none_active), 0)

        # aggregate_results prepends the active sites of a previous run
        combined = aggregate_results([], init_df=active)
        self.assertEqual(len(combined), len(active))

    def test_plot_siting_writes_figure(self):
        """`outputs.plot_siting` renders the result on the packaged boundary / regions layers."""

        with tempfile.TemporaryDirectory() as tmpdir:
            out_png = os.path.join(tmpdir, 'sited.png')

            cerf.plot_siting(self.df_sequential, save_figure=True, output_file=out_png)

            self.assertTrue(os.path.isfile(out_png))
            self.assertGreater(os.path.getsize(out_png), 0)

        with self.assertRaises(ValueError):
            cerf.plot_siting(self.df_sequential, save_figure=True, output_file=None)

        matplotlib.pyplot.close('all')


if __name__ == '__main__':
    unittest.main()
