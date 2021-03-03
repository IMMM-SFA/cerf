"""Process a state for the target year.

@author Chris R. vernon
@email chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

import os
import logging
import pkg_resources
import time

import numpy as np
import pandas as pd
import rasterio

import cerf.utils as util
from cerf.compete import Competition


class ProcessState:

    def __init__(self,
                 settings_dict,
                 technology_dict,
                 technology_order,
                 expansion_dict,
                 states_dict,
                 suitability_arr,
                 nlc_arr,
                 xcoords,
                 ycoords,
                 target_state_name='virginia',
                 randomize=True,
                 seed_value=0,
                 verbose=False,
                 write_output=False):

        # dictionary containing project level settings
        self.settings_dict = settings_dict

        # dictionary containing technology specific information
        self.technology_dict = technology_dict

        # order of technologies to process
        self.technology_order = technology_order

        # dictionary containing the expansion plan
        self.expansion_dict = expansion_dict

        # states dictionary with state name to state ID mapping
        self.states_dict = states_dict

        # target state name
        self.target_state_name = target_state_name

        # the id of the target state as it is represented in the state raster
        self.target_state_id = self.get_state_id()

        # suitability data for the CONUS
        self.suitability_arr = suitability_arr

        # NLC data for the CONUS
        self.nlc_arr = nlc_arr

        # coordinates for each index
        self.xcoords = xcoords
        self.ycoords = ycoords

        # the choice to randomize when a technology has more than one NLC cheapest value
        self.randomize = randomize

        # a random seed value that is used when the user wants to replicate a run exactly
        self.seed_value = seed_value

        # log verbose siting information
        self.verbose = verbose

        # set write outputs flag
        self.write_outputs = write_output

        logging.info(f"Extracting suitable grids for {self.target_state_name}")
        self.suitability_array_state, self.ymin, self.ymax, self.xmin, self.xmax = self.extract_state_suitability()

        logging.info(f"Creating a NLC state level array for {self.target_state_name}")
        self.suitable_nlc_state = self.mask_nlc()

        logging.info(f"Competing technologies to site expansion for {self.target_state_name}")
        self.sited_arr = self.competition()

    def get_state_id(self):
        """Load state name to state id YAML file to a dictionary.

        :return:                        Corresponding state ID for the user passed state name.

        """

        if self.target_state_name in self.states_dict:
            return self.states_dict.get(self.target_state_name.lower())

        else:

            logging.error(f"State name: `{self.target_state_name}` not in registry.")
            logging.error(f"Please select a state name from the following:  {list(self.states_dict.keys())}")

            raise KeyError()

    def extract_state_suitability(self):
        """Extract a single state from the suitability."""

        # load the state raster as array
        state_raster_file = pkg_resources.resource_filename('cerf', 'data/cerf_conus_states_albers_1km.tif')
        with rasterio.open(state_raster_file) as src:
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
        suitability_array_state = self.suitability_arr[:, ymin:ymax, xmin:xmax].copy()

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
        nlc_arr_state = self.nlc_arr[:, self.ymin:self.ymax, self.xmin:self.xmax].copy()

        # insert zero array, mask it as index [0, :, :] so the tech_id 0 will always be min if nothing is left to site
        nlc_arr_state = np.insert(nlc_arr_state, 0, np.zeros_like(nlc_arr_state[0, :, :]), axis=0)
        nlc_arr_state = np.nan_to_num(nlc_arr_state, nan=np.max(nlc_arr_state) + 1)

        # apply the mask to NLC data
        return np.ma.masked_array(nlc_arr_state, mask=self.suitability_array_state)

    def competition(self):
        """Compete technologies."""

        comp = Competition(target_state_name=self.target_state_name,
                           technology_dict=self.technology_dict,
                           technology_order=self.technology_order,
                           expansion_dict=self.expansion_dict[self.target_state_name],
                           nlc_mask=self.suitable_nlc_state,
                           xcoords=self.xcoords,
                           ycoords=self.ycoords,
                           randomize=self.randomize,
                           seed_value=self.seed_value,
                           verbose=self.verbose)

        # create an output raster of sited techs; 0 is NaN
        final_array = np.where(comp.sited_array == 0, np.nan, comp.sited_array)

        # place final array back in grid space for all regions
        sited_arr = np.zeros_like(self.suitability_arr[0, :, :]) * np.nan
        sited_arr[self.ymin:self.ymax, self.xmin:self.xmax] = final_array

        # write outputs if so desired
        if self.write_outputs:

            # create output file path
            raster_file_name = f"cerf_sited_{self.settings_dict['run_year']}_{self.target_state_name}.tif"
            raster_out_file = os.path.join(self.settings_dict.get('output_directory'), raster_file_name)

            # write output using a template to prescribe the metadata
            template_raster = self.technology_dict[self.technology_order[0]]['interconnection_distance_raster_file']
            util.array_to_raster(sited_arr, template_raster, raster_out_file)

            # create output CSV file of coordinate data
            csv_file_name = f"cerf_sited_{self.settings_dict['run_year']}_{self.target_state_name}.csv"
            csv_out_file = os.path.join(self.settings_dict.get('output_directory'), csv_file_name)
            df = pd.DataFrame(comp.sited_dict).to_csv(csv_out_file, index=False)

        return sited_arr


def process_state(target_state_name, settings_dict, technology_dict, technology_order, expansion_dict, states_dict,
                  suitability_arr, nlc_arr, xcoords, ycoords,randomize=True, seed_value=0, verbose=False,
                  write_output=True):
    """Convenience wrapper to log time and site an expansion plan for a target state for the target year.

    :param target_state_name:                   Name of the target state as it is represented in the state raster.
                                                Must be all lower case with spacing separated by an underscore.
    :type target_state_name:                    str

    :param settings_dict:                       Project level setting dictionary from cerf.read_config.ReadConfig
    :type settings_dict:                        dict

    :param technology_dict:                     Technology level data dictionary from cerf.read_config.ReadConfig
    :type technology_dict:                      dict

    :param technology_order:                    Technology processing order to index by from cerf.read_config.ReadConfig
    :type technology_order:                     list

    :param expansion_dict:                      Expansion plan data dictionary from cerf.read_config.ReadConfig
    :type expansion_dict:                       dict

    :param states_dict:                         Mapping from state name to state ID from cerf.read_config.ReadConfig
    :type states_dict:                          dict

    :param suitability_arr:                     3D array where {tech_id, x, y} for suitability data
    :type suitability_arr:                      ndarray

    :param nlc_arr:                             3D array where {tech_id, x, y} for NLC data
    :type nlc_arr:                              ndarray

    :param data:                                Object containing all data (NLC, etc.) to run the expansion. This
                                                data is generated from the cerf.stage.Stage class.
    :type data:                                 class

    :param randomize:                           Choice to randomize when a technology has more than one NLC
                                                cheapest value
    :type randomize:                            bool

    :param seed_value:                          A random seed value that is used when the user wants to replicate
                                                a run exactly
    :type seed_value:                           int

    :param verbose:                             Log verbose siting information
    :type verbose:                               bool

    :param write_output:                        Choice to write output to a file
    :type write_output:                         bool

    :return:                                    2D NumPy array of sited technologies in the CONUS grid space where
                                                grid cell values are in the technology number as provided by the
                                                expansion plan

    """

    logging.info(f'Processing state:  {target_state_name}')

    # check to see if state has any sites in the expansion
    n_sites = sum([expansion_dict[target_state_name][k]['n_sites'] for k in expansion_dict[target_state_name].keys()])

    # if there are no sites in the expansion, return an all NaN 2D array
    if n_sites <= 0:
        logging.warning(f"There were no sites expected for any technology in `{target_state_name}`")
        return nlc_arr[0, :, :] * np.nan

    else:

        # initial time for processing state
        state_t0 = time.time()

        # process expansion plan and competition for a single state for the target year
        process = ProcessState(settings_dict=settings_dict,
                               technology_dict=technology_dict,
                               technology_order=technology_order,
                               expansion_dict=expansion_dict,
                               states_dict=states_dict,
                               suitability_arr=suitability_arr,
                               nlc_arr=nlc_arr,
                               xcoords=xcoords,
                               ycoords=ycoords,
                               target_state_name=target_state_name,
                               randomize=randomize,
                               seed_value=seed_value,
                               verbose=verbose,
                               write_output=write_output)

        logging.info(f'Processed `{target_state_name}` in {round(time.time() - state_t0, 7)} seconds')

        return process.sited_arr
