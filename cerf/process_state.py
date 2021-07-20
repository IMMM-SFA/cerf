"""Process a state for the target year.

@author Chris R. vernon
@email chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

import logging
import os
import time

import numpy as np
import pandas as pd
import pkg_resources
import rasterio

from cerf.compete import Competition


class ProcessState:

    def __init__(self,
                 settings_dict,
                 technology_dict,
                 technology_order,
                 expansion_dict,
                 states_dict,
                 suitability_arr,
                 lmp_arr,
                 nov_arr,
                 ic_arr,
                 nlc_arr,
                 zones_arr,
                 xcoords,
                 ycoords,
                 indices_2d,
                 target_state_name,
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

        # LMP array for the CONUS
        self.lmp_arr = lmp_arr

        # NOV array for the CONUS
        self.nov_arr = nov_arr

        # IC array for the CONUS
        self.ic_arr = ic_arr

        # NLC data for the CONUS
        self.nlc_arr = nlc_arr

        # lmp zoness for the CONUS
        self.zones_arr = zones_arr

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

        logging.debug(f"Extracting suitable grids for {self.target_state_name}")
        self.suitability_array_state, self.ymin, self.ymax, self.xmin, self.xmax = self.extract_state_suitability()

        logging.debug(f"Creating a NLC state level array for {self.target_state_name}")
        self.suitable_nlc_state = self.mask_nlc()

        logging.debug(f"Generating grid indices for {self.target_state_name}")
        # grid indices for the entire grid in a 2D array
        self.indices_2d = indices_2d
        self.indices_flat_state = self.get_grid_indices()

        logging.debug(f"Get grid coordinates for {self.target_state_name}")
        self.xcoords_state, self.ycoords_state = self.get_grid_coordinates()

        logging.debug(f"Extracting additional metrics for {self.target_state_name}")
        self.lmp_flat_dict, self.nov_flat_dict, self.ic_flat_dict = self.extract_state_metrics()
        self.zones_flat_arr = self.extract_lmp_zones()

        logging.debug(f"Competing technologies to site expansion for {self.target_state_name}")
        self.run_data = self.competition()

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

        # make any nan grid cells the most expensive option to exclude
        nlc_arr_state = np.nan_to_num(nlc_arr_state, nan=np.nanmax(nlc_arr_state) + 1)

        # apply the mask to NLC data
        return np.ma.masked_array(nlc_arr_state, mask=self.suitability_array_state)

    def get_grid_indices(self):
        """Generate a 1D array of grid indices the target state to use as a way to map state level outcomes back to the
        full grid space."""

        return self.indices_2d[self.ymin:self.ymax, self.xmin:self.xmax].flatten()

    def get_grid_coordinates(self):
        """Generate 1D arrays of grid coordinates (X, Y) to use for siting based on the bounds of the target state."""

        xcoord_2d_state = self.xcoords[self.ymin:self.ymax, self.xmin:self.xmax].flatten()
        ycoord_2d_state = self.ycoords[self.ymin:self.ymax, self.xmin:self.xmax].flatten()

        return xcoord_2d_state, ycoord_2d_state

    def extract_state_metrics(self):
        """Extract the LMP, NOV, and IC arrays for the target state and return them as dictionaries where
        {tech_id: flat_array, ...}.

        """

        # extract the target state
        lmp_arr_state = self.lmp_arr[:, self.ymin:self.ymax, self.xmin:self.xmax]
        nov_arr_state = self.nov_arr[:, self.ymin:self.ymax, self.xmin:self.xmax]
        ic_arr_state = self.ic_arr[:, self.ymin:self.ymax, self.xmin:self.xmax]

        # create a reference dictionary where {tech_id: flat_state_array, ...}
        lmp_flat_dict = {i: lmp_arr_state[ix, :, :].flatten() for ix, i in enumerate(self.technology_order)}
        nov_flat_dict = {i: nov_arr_state[ix, :, :].flatten() for ix, i in enumerate(self.technology_order)}
        ic_flat_dict = {i: ic_arr_state[ix, :, :].flatten() for ix, i in enumerate(self.technology_order)}

        return lmp_flat_dict, nov_flat_dict, ic_flat_dict

    def extract_lmp_zones(self):
        """Extract the lmp zoness elements for the target state and return as a flat array."""

        return self.zones_arr[self.ymin:self.ymax, self.xmin:self.xmax].flatten()

    def competition(self):
        """Compete technologies."""

        comp = Competition(target_state_name=self.target_state_name,
                           settings_dict=self.settings_dict,
                           technology_dict=self.technology_dict,
                           technology_order=self.technology_order,
                           expansion_dict=self.expansion_dict[self.target_state_name],
                           lmp_dict=self.lmp_flat_dict,
                           nov_dict=self.nov_flat_dict,
                           ic_dict=self.ic_flat_dict,
                           nlc_mask=self.suitable_nlc_state,
                           zones_arr=self.zones_flat_arr,
                           xcoords=self.xcoords_state,
                           ycoords=self.ycoords_state,
                           indices_flat=self.indices_flat_state,
                           randomize=self.randomize,
                           seed_value=self.seed_value,
                           verbose=self.verbose)

        # create data frame of sited data
        df = pd.DataFrame(comp.sited_dict)

        # write outputs if so desired
        if self.write_outputs:

            # create output CSV file of coordinate data
            csv_file_name = f"cerf_sited_{self.settings_dict['run_year']}_{self.target_state_name}.csv"
            csv_out_file = os.path.join(self.settings_dict.get('output_directory'), csv_file_name)

            df.to_csv(csv_out_file, index=False)

        return comp


def process_state(target_state_name, settings_dict, technology_dict, technology_order, expansion_dict, states_dict,
                  suitability_arr, lmp_arr, nov_arr, ic_arr, nlc_arr, zones_arr, xcoords, ycoords, indices_2d,
                  randomize=True, seed_value=0, verbose=False, write_output=True):
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

    logging.debug(f'Processing state:  {target_state_name}')

    # check to see if state has any sites in the expansion
    n_sites = sum([expansion_dict[target_state_name][k]['n_sites'] for k in expansion_dict[target_state_name].keys()])

    # if there are no sites in the expansion, return an all NaN 2D array
    if n_sites <= 0:
        logging.warning(f"There were no sites expected for any technology in `{target_state_name}`")
        return None

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
                               lmp_arr=lmp_arr,
                               nov_arr=nov_arr,
                               ic_arr=ic_arr,
                               nlc_arr=nlc_arr,
                               zones_arr=zones_arr,
                               xcoords=xcoords,
                               ycoords=ycoords,
                               indices_2d=indices_2d,
                               target_state_name=target_state_name,
                               randomize=randomize,
                               seed_value=seed_value,
                               verbose=verbose,
                               write_output=write_output)

        logging.info(f'Processed `{target_state_name}` in {round(time.time() - state_t0, 7)} seconds')

        return process
