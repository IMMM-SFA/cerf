"""Process a state for the target year.

@author Chris R. vernon
@email chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

import logger
import numpy as np
import rasterio

from cerf.compete import Competition


class ProcessState:

    def __init__(self, config, data, technology_dict, technology_order, target_state_id=45, seed_value=0,
                 randomize=True, verbose=False):

        self.config = config
        self.technology_dict = technology_dict
        self.technology_order = technology_order
        self.target_state_id = target_state_id
        self.data = data
        self.expansion_plan = config.get('expansion_plan')
        self.seed_value = seed_value
        self.randomize = randomize
        self.verbose = verbose

        self.suitability_array_state, self.ymin, self.ymax, self.xmin, self.xmax = self.extract_state_suitability()

        self.suitable_nlc_state = self.mask_nlc()

    def extract_state_suitability(self):
        """Extract a single state from the suitability."""

        # load the state raster as array
        with rasterio.open(self.config['settings']['state_raster_file']) as src:
            states_arr = src.read(1)

        # get target state indices in grid space
        state_indices = np.where(states_arr == self.target_state_id)

        # get minimum and maximum bounds
        ymin = np.min(state_indices[0])
        ymax = np.max(state_indices[0]) + 1
        xmin = np.min(state_indices[1])
        xmax = np.max(state_indices[1]) + 1

        # extract state and give binary designation
        state_mask = states_arr[ymin:ymax, xmin:xmax].copy()
        state_mask = np.where(state_mask == self.target_state_id, 0, 1)

        # extract state footprint from suitability data
        suitability_array_state = self.data.suitability_array[:, ymin:ymax, xmin:xmax].copy()

        # add in suitability where unsuitable is the highest value of NLC
        suitability_array_state += state_mask

        # at this point, we have all suitable grid cells as 0 and all not as 1
        suitability_array_state = np.where(suitability_array_state == 0, 0, 1)

        # exclude all area for the default dimension
        suitability_array_state = np.insert(suitability_array_state, 0, np.ones_like(suitability_array_state[0, :, :]), axis=0)

        return suitability_array_state, ymin, ymax, xmin, xmax

    def mask_nlc(self):
        """Extract NLC elements for the current state."""

        # extract state footprint from NLC data
        nlc_arr_state = self.data.nlc_arr[:, self.ymin:self.ymax, self.xmin:self.xmax].copy()

        # insert zero array, mask it as index [0, :, :] so the tech_id 0 will always be min if nothing is left to site
        nlc_arr_state = np.insert(nlc_arr_state, 0, np.zeros_like(nlc_arr_state[0, :, :]), axis=0)
        nlc_arr_state = np.nan_to_num(nlc_arr_state, nan=np.max(nlc_arr_state) + 1)

        # apply the mask to NLC data
        return np.ma.masked_array(nlc_arr_state, mask=self.suitability_array_state)

    def compete(self):
        """Compete technologies."""

        comp = Competition(self.expansion_plan,
                           self.suitable_nlc_state,
                           self.technology_dict,
                           randomize=self.randomize,
                           seed_value=self.seed_value,
                           verbose=self.verbose)

        final_array = comp.sited_array.copy()

        # create an output raster of sited techs; 0 is NaN
        final_array = np.where(final_array == 0, np.nan, final_array)

        # place final array back in grid space
        output_arr = np.zeros_like(states_arr) * np.nan
        output_arr[ymin:ymax, xmin:xmax] = final_array




