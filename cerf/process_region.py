"""Process a region for the target year.

@author Chris R. vernon
@email chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

import logging
import os
import time

import numpy as np
import pandas as pd
import rasterio

import cerf.package_data as pkg
from cerf.compete import Competition


class ProcessRegion:

    def __init__(self,
                 settings_dict,
                 technology_dict,
                 technology_order,
                 expansion_dict,
                 regions_dict,
                 suitability_arr,
                 lmp_arr,
                 generation_arr,
                 operating_cost_arr,
                 nov_arr,
                 ic_arr,
                 nlc_arr,
                 zones_arr,
                 xcoords,
                 ycoords,
                 indices_2d,
                 target_region_name,
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

        # regions dictionary with region name to region ID mapping
        self.regions_dict = regions_dict

        # target region name
        self.target_region_name = target_region_name

        # the id of the target region as it is represented in the region raster
        self.target_region_id = self.get_region_id()

        # suitability data for the CONUS
        self.suitability_arr = suitability_arr

        # LMP array for the CONUS
        self.lmp_arr = lmp_arr

        # generation array for the CONUS
        self.generation_arr = generation_arr

        # operating cost array for the CONUS
        self.operating_cost_arr = operating_cost_arr

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

        logging.debug(f"Extracting suitable grids for {self.target_region_name}")
        self.suitability_array_region, self.ymin, self.ymax, self.xmin, self.xmax = self.extract_region_suitability()

        logging.debug(f"Creating a NLC region level array for {self.target_region_name}")
        self.suitable_nlc_region = self.mask_nlc()

        logging.debug(f"Generating grid indices for {self.target_region_name}")
        # grid indices for the entire grid in a 2D array
        self.indices_2d = indices_2d
        self.indices_flat_region = self.get_grid_indices()

        logging.debug(f"Get grid coordinates for {self.target_region_name}")
        self.xcoords_region, self.ycoords_region = self.get_grid_coordinates()

        logging.debug(f"Extracting additional metrics for {self.target_region_name}")
        self.lmp_flat_dict, self.generation_flat_dict, self.operating_cost_flat_dict, self.nov_flat_dict, self.ic_flat_dict = self.extract_region_metrics()
        self.zones_flat_arr = self.extract_lmp_zones()

        logging.debug(f"Competing technologies to site expansion for {self.target_region_name}")
        self.run_data = self.competition()

    def get_region_id(self):
        """Load region name to region id YAML file to a dictionary.

        :return:                        Corresponding region ID for the user passed region name.

        """

        if self.target_region_name in self.regions_dict:
            return self.regions_dict.get(self.target_region_name.lower())

        else:

            logging.error(f"State name: `{self.target_region_name}` not in registry.")
            logging.error(f"Please select a region name from the following:  {list(self.regions_dict.keys())}")

            raise KeyError()

    def extract_region_suitability(self):
        """Extract a single region from the suitability."""

        # load the region raster as array
        region_raster_file = self.settings_dict.get('region_raster_file')

        with rasterio.open(region_raster_file) as src:
            regions_arr = src.read(1)

        # get target region indices in grid space
        region_indices = np.where(regions_arr == self.target_region_id)

        # get minimum and maximum bounds
        ymin = np.min(region_indices[0])
        ymax = np.max(region_indices[0]) + 1
        xmin = np.min(region_indices[1])
        xmax = np.max(region_indices[1]) + 1

        # extract region and give binary designation
        region_mask = regions_arr[ymin:ymax, xmin:xmax].copy()
        region_mask = np.where(region_mask == self.target_region_id, 0, 1)

        # extract region footprint from suitability data
        suitability_array_region = self.suitability_arr[:, ymin:ymax, xmin:xmax].copy()

        # add in suitability where unsuitable is the highest value of NLC
        suitability_array_region += region_mask

        # at this point, we have all suitable grid cells as 0 and all not as 1
        suitability_array_region = np.where(suitability_array_region == 0, 0, 1)

        # exclude all area for the default dimension
        suitability_array_region = np.insert(suitability_array_region, 0, np.ones_like(suitability_array_region[0, :, :]), axis=0)

        return suitability_array_region, ymin, ymax, xmin, xmax

    def mask_nlc(self):
        """Extract NLC elements for the current region."""

        # extract region footprint from NLC data
        nlc_arr_region = self.nlc_arr[:, self.ymin:self.ymax, self.xmin:self.xmax].copy()

        # insert zero array, mask it as index [0, :, :] so the tech_id 0 will always be min if nothing is left to site
        nlc_arr_region = np.insert(nlc_arr_region, 0, np.zeros_like(nlc_arr_region[0, :, :]), axis=0)

        # make any nan grid cells the most expensive option to exclude
        nlc_arr_region = np.nan_to_num(nlc_arr_region, nan=np.nanmax(nlc_arr_region) + 1)

        # apply the mask to NLC data
        return np.ma.masked_array(nlc_arr_region, mask=self.suitability_array_region)

    def get_grid_indices(self):
        """Generate a 1D array of grid indices the target region to use as a way to map region level outcomes back to the
        full grid space."""

        return self.indices_2d[self.ymin:self.ymax, self.xmin:self.xmax].flatten()

    def get_grid_coordinates(self):
        """Generate 1D arrays of grid coordinates (X, Y) to use for siting based on the bounds of the target region."""

        xcoord_2d_region = self.xcoords[self.ymin:self.ymax, self.xmin:self.xmax].flatten()
        ycoord_2d_region = self.ycoords[self.ymin:self.ymax, self.xmin:self.xmax].flatten()

        return xcoord_2d_region, ycoord_2d_region

    def extract_region_metrics(self):
        """Extract the LMP, NOV, and IC arrays for the target region and return them as dictionaries where
        {tech_id: flat_array, ...}.

        """

        # extract the target region
        lmp_arr_region = self.lmp_arr[:, self.ymin:self.ymax, self.xmin:self.xmax]
        generation_arr_region = self.generation_arr[:, self.ymin:self.ymax, self.xmin:self.xmax]
        operating_cost_arr_region = self.operating_cost_arr[:, self.ymin:self.ymax, self.xmin:self.xmax]
        nov_arr_region = self.nov_arr[:, self.ymin:self.ymax, self.xmin:self.xmax]
        ic_arr_region = self.ic_arr[:, self.ymin:self.ymax, self.xmin:self.xmax]

        # create a reference dictionary where {tech_id: flat_region_array, ...}
        lmp_flat_dict = {i: lmp_arr_region[ix, :, :].flatten() for ix, i in enumerate(self.technology_order)}
        generation_flat_dict = {i: generation_arr_region[ix, :, :].flatten() for ix, i in enumerate(self.technology_order)}
        operating_cost_flat_dict = {i: operating_cost_arr_region[ix, :, :].flatten() for ix, i in enumerate(self.technology_order)}
        nov_flat_dict = {i: nov_arr_region[ix, :, :].flatten() for ix, i in enumerate(self.technology_order)}
        ic_flat_dict = {i: ic_arr_region[ix, :, :].flatten() for ix, i in enumerate(self.technology_order)}

        return lmp_flat_dict, generation_flat_dict, operating_cost_flat_dict, nov_flat_dict, ic_flat_dict

    def extract_lmp_zones(self):
        """Extract the lmp zones elements for the target region and return as a flat array."""

        return self.zones_arr[self.ymin:self.ymax, self.xmin:self.xmax].flatten()

    def competition(self):
        """Compete technologies."""

        comp = Competition(target_region_name=self.target_region_name,
                           settings_dict=self.settings_dict,
                           technology_dict=self.technology_dict,
                           technology_order=self.technology_order,
                           expansion_dict=self.expansion_dict[self.target_region_name],
                           lmp_dict=self.lmp_flat_dict,
                           generation_dict=self.generation_flat_dict,
                           operating_cost_dict=self.operating_cost_flat_dict,
                           nov_dict=self.nov_flat_dict,
                           ic_dict=self.ic_flat_dict,
                           nlc_mask=self.suitable_nlc_region,
                           zones_arr=self.zones_flat_arr,
                           xcoords=self.xcoords_region,
                           ycoords=self.ycoords_region,
                           indices_flat=self.indices_flat_region,
                           randomize=self.randomize,
                           seed_value=self.seed_value,
                           verbose=self.verbose)

        # create data frame of sited data
        df = pd.DataFrame(comp.sited_dict)

        # write outputs if so desired
        if self.write_outputs:

            # create output CSV file of coordinate data
            csv_file_name = f"cerf_sited_{self.settings_dict['run_year']}_{self.target_region_name}.csv"
            csv_out_file = os.path.join(self.settings_dict.get('output_directory'), csv_file_name)

            df.to_csv(csv_out_file, index=False)

        return comp


def process_region(target_region_name,
                   settings_dict,
                   technology_dict,
                   technology_order,
                   expansion_dict,
                   regions_dict,
                   suitability_arr,
                   lmp_arr,
                   generation_arr,
                   operating_cost_arr,
                   nov_arr,
                   ic_arr,
                   nlc_arr,
                   zones_arr,
                   xcoords,
                   ycoords,
                   indices_2d,
                   randomize=True,
                   seed_value=0,
                   verbose=False,
                   write_output=True):
    """Convenience wrapper to log time and site an expansion plan for a target region for the target year.

    :param target_region_name:                   Name of the target region as it is represented in the region raster.
                                                Must be all lower case with spacing separated by an underscore.
    :type target_region_name:                    str

    :param settings_dict:                       Project level setting dictionary from cerf.read_config.ReadConfig
    :type settings_dict:                        dict

    :param technology_dict:                     Technology level data dictionary from cerf.read_config.ReadConfig
    :type technology_dict:                      dict

    :param technology_order:                    Technology processing order to index by from cerf.read_config.ReadConfig
    :type technology_order:                     list

    :param expansion_dict:                      Expansion plan data dictionary from cerf.read_config.ReadConfig
    :type expansion_dict:                       dict

    :param regions_dict:                         Mapping from region name to region ID from cerf.read_config.ReadConfig
    :type regions_dict:                          dict

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

    logging.debug(f'Processing region:  {target_region_name}')

    # check to see if region has any sites in the expansion
    n_sites = sum([expansion_dict[target_region_name][k]['n_sites'] for k in expansion_dict[target_region_name].keys()])

    # if there are no sites in the expansion, return an all NaN 2D array
    if n_sites <= 0:
        logging.warning(f"There were no sites expected for any technology in `{target_region_name}`")
        return None

    else:

        # initial time for processing region
        region_t0 = time.time()

        # process expansion plan and competition for a single region for the target year
        process = ProcessRegion(settings_dict=settings_dict,
                                technology_dict=technology_dict,
                                technology_order=technology_order,
                                expansion_dict=expansion_dict,
                                regions_dict=regions_dict,
                                suitability_arr=suitability_arr,
                                lmp_arr=lmp_arr,
                                generation_arr=generation_arr,
                                operating_cost_arr=operating_cost_arr,
                                nov_arr=nov_arr,
                                ic_arr=ic_arr,
                                nlc_arr=nlc_arr,
                                zones_arr=zones_arr,
                                xcoords=xcoords,
                                ycoords=ycoords,
                                indices_2d=indices_2d,
                                target_region_name=target_region_name,
                                randomize=randomize,
                                seed_value=seed_value,
                                verbose=verbose,
                                write_output=write_output)

        logging.info(f'Processed `{target_region_name}` in {round(time.time() - region_t0, 7)} seconds')

        return process
