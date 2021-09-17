import os
import unittest

import numpy as np

from cerf.read_config import ReadConfig
from cerf.interconnect import Interconnection


class TestInterconnection(unittest.TestCase):

    # supporting data
    TEST_CONFIG = os.path.join(os.path.dirname(__file__), 'data/test_config_2010.yml')
    EXPECTED_SUBSET = np.load(os.path.join(os.path.dirname(__file__), 'data/test_ic_arr.npy'))

    @staticmethod
    def get_sample(arr):
        """Get a sample to reduce comparison size.  Sample space covers the Southeast U.S."""

        return arr[:, 1500:2000, 3000:4000].copy()

    def test_interconnection_run(self):
        """Test to make sure interconnection outputs run."""

        # read in configuration file
        cfg = ReadConfig(TestInterconnection.TEST_CONFIG)

        # unpack configuration and assign defaults
        substation_file = cfg.infrastructure_dict.get('substation_file', None)
        transmission_costs_file = cfg.infrastructure_dict.get('transmission_costs_file', None)
        pipeline_costs_file = cfg.infrastructure_dict.get('pipeline_costs_file', None)
        pipeline_file = cfg.infrastructure_dict.get('pipeline_file', None)
        output_rasterized_file = cfg.infrastructure_dict.get('output_rasterized_file', False)
        output_alloc_file = cfg.infrastructure_dict.get('output_alloc_file', False)
        output_cost_file = cfg.infrastructure_dict.get('output_cost_file', False)
        output_dist_file = cfg.infrastructure_dict.get('output_dist_file', False)
        interconnection_cost_file = cfg.infrastructure_dict.get('interconnection_cost_file', None)

        template_array = np.zeros(shape=(1, 2999, 4693))

        technology_dict_subset = {9: cfg.technology_dict[9]}
        technology_order_subset = [cfg.technology_order[0]]

        # instantiate class
        ic = Interconnection(template_array=template_array,
                             technology_dict=technology_dict_subset,
                             technology_order=technology_order_subset,
                             region_raster_file=cfg.settings_dict.get('region_raster_file'),
                             region_abbrev_to_name_file=cfg.settings_dict.get('region_abbrev_to_name_file'),
                             region_name_to_id_file=cfg.settings_dict.get('region_name_to_id_file'),
                             substation_file=substation_file,
                             transmission_costs_file=transmission_costs_file,
                             pipeline_costs_file=pipeline_costs_file,
                             pipeline_file=pipeline_file,
                             output_rasterized_file=output_rasterized_file,
                             output_dist_file=output_dist_file,
                             output_alloc_file=output_alloc_file,
                             output_cost_file=output_cost_file,
                             interconnection_cost_file=interconnection_cost_file,
                             output_dir=cfg.settings_dict.get('output_directory', None))

        ic_arr = ic.generate_interconnection_costs_array()

        ic_arr_subset = self.get_sample(ic_arr)

        np.testing.assert_array_equal(TestInterconnection.EXPECTED_SUBSET, ic_arr_subset)


if __name__ == '__main__':
    unittest.main()
