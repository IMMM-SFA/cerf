"""Process a region for the target year.

@author Chris R. vernon
@email chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

import copy
import logging
import os
import time

import numpy as np
import pandas as pd
import rasterio

import cerf.utils as util
from cerf.compete import Competition

logger = logging.getLogger(__name__)


class EmptyRegionResult:
    """Result object for a region with no sites in its expansion plan.

    Mirrors the attributes downstream code reads from a `ProcessRegion` result (``target_region_name``,
    ``run_data.sited_df``, ``run_data.sited_dict``, ``run_data.sited_array``, ``run_data.expansion_dict``) so callers
    never have to special-case ``None``.

    """

    class _RunData:

        def __init__(self, expansion_dict):
            self.sited_dict = util.empty_sited_dict()
            self.sited_df = pd.DataFrame(self.sited_dict).astype(util.sited_dtypes())
            self.sited_array = None
            self.expansion_dict = copy.deepcopy(expansion_dict)

    def __init__(self, target_region_name, expansion_dict):
        self.target_region_name = target_region_name
        self.run_data = self._RunData(expansion_dict)

    def __repr__(self):
        return f"EmptyRegionResult(target_region_name={self.target_region_name!r})"


def crop_to_region(region_id, region_bounds, suitability_arr, lmp_arr, generation_arr, operating_cost_arr, nov_arr,
                   ic_arr, nlc_arr, zones_arr, xcoords, ycoords, indices_2d, regions_arr):
    """Crop every staged full-grid array to a region's bounding box for dispatch to a worker process.

    Returns a dictionary of `process_region` keyword arguments holding only the region's bounding box. The cropped
    arrays are contiguous copies (so pickling does not drag along the full grid), and ``region_bounds`` is rewritten
    so the region occupies the whole of each cropped array. Arrays that are constant over the grid (per-technology
    broadcast views such as generation and operating cost) are collapsed to a 1D per-technology vector.

    :param region_id:                   Region ID as in the region raster
    :type region_id:                    int

    :param region_bounds:               ``{region_id: (ymin, ymax, xmin, xmax)}`` from cerf.stage.Stage
    :type region_bounds:                dict

    :return:                            dict of keyword arguments for `process_region`

    """

    ymin, ymax, xmin, xmax = region_bounds[region_id]

    def crop3d(arr):
        if arr.ndim == 1:
            return arr
        if arr.ndim == 3 and arr.strides[1] == 0 and arr.strides[2] == 0:
            # spatially constant per technology: send one value per technology
            return np.ascontiguousarray(arr[:, 0, 0])
        return np.ascontiguousarray(arr[:, ymin:ymax, xmin:xmax])

    def crop2d(arr):
        return np.ascontiguousarray(arr[ymin:ymax, xmin:xmax])

    return dict(suitability_arr=crop3d(suitability_arr),
                lmp_arr=crop3d(lmp_arr),
                generation_arr=crop3d(generation_arr),
                operating_cost_arr=crop3d(operating_cost_arr),
                nov_arr=crop3d(nov_arr),
                ic_arr=crop3d(ic_arr),
                nlc_arr=crop3d(nlc_arr),
                zones_arr=crop2d(zones_arr),
                xcoords=crop2d(xcoords),
                ycoords=crop2d(ycoords),
                indices_2d=crop2d(indices_2d),
                regions_arr=crop2d(regions_arr),
                region_bounds={region_id: (0, ymax - ymin, 0, xmax - xmin)})


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
                 write_output=False,
                 regions_arr=None,
                 region_bounds=None):

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

        # target region name, normalised to the lower-case form used as the key in the regions and expansion dicts
        self.target_region_name = str(target_region_name).lower()

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

        # region ID raster as an array and per-region bounding boxes; both are normally read once in `Stage` and
        #  passed in, but fall back to reading the raster here so the class can still be used standalone
        if regions_arr is None:
            with rasterio.open(self.settings_dict.get('region_raster_file')) as src:
                regions_arr = src.read(1)
        self.regions_arr = regions_arr

        if region_bounds is None:
            region_bounds = {}
        self.region_bounds = region_bounds

        logger.debug(f"Extracting suitable grids for {self.target_region_name}")
        self.suitability_array_region, self.ymin, self.ymax, self.xmin, self.xmax = self.extract_region_suitability()

        logger.debug(f"Creating a NLC region level array for {self.target_region_name}")
        self.suitable_nlc_region = self.mask_nlc()

        logger.debug(f"Generating grid indices for {self.target_region_name}")
        # grid indices for the entire grid in a 2D array
        self.indices_2d = indices_2d
        self.indices_flat_region = self.get_grid_indices()

        logger.debug(f"Get grid coordinates for {self.target_region_name}")
        self.xcoords_region, self.ycoords_region = self.get_grid_coordinates()

        logger.debug(f"Extracting additional metrics for {self.target_region_name}")
        self.lmp_flat_dict, self.generation_flat_dict, self.operating_cost_flat_dict, self.nov_flat_dict, self.ic_flat_dict = self.extract_region_metrics()
        self.zones_flat_arr = self.extract_lmp_zones()

        logger.debug(f"Competing technologies to site expansion for {self.target_region_name}")
        self.run_data = self.competition()

    def get_region_id(self):
        """Look up the region ID for the target region name.

        Names are matched case-insensitively (the registry keys are lower case), so ``'Rhode_Island'`` and
        ``'rhode_island'`` resolve to the same ID.

        :return:                        Corresponding region ID for the user passed region name.

        """

        key = self.target_region_name

        if key in self.regions_dict:
            return self.regions_dict[key]

        msg = (f"Region name `{self.target_region_name}` not in registry. Please select a region name from the "
               f"following:  {sorted(self.regions_dict.keys())}")
        logger.error(msg)

        raise KeyError(msg)

    def get_region_bounds(self):
        """Return the grid-space bounding box ``(ymin, ymax, xmin, xmax)`` of the target region.

        Uses the precomputed bounds from `Stage` when available; otherwise derives them from the region array.

        """

        bounds = self.region_bounds.get(self.target_region_id)

        if bounds is None:

            region_indices = np.where(self.regions_arr == self.target_region_id)

            if region_indices[0].size == 0:
                raise ValueError(f"Region ID {self.target_region_id} (`{self.target_region_name}`) does not occur "
                                 f"in the region raster.")

            bounds = (int(np.min(region_indices[0])), int(np.max(region_indices[0])) + 1,
                      int(np.min(region_indices[1])), int(np.max(region_indices[1])) + 1)

        return bounds

    def extract_region_suitability(self):
        """Extract a single region from the suitability.

        Returns a boolean array ``[layer, row, col]`` over the region's bounding box where ``True`` marks an
        unsuitable cell. Layer 0 is the "no technology" default and is entirely unsuitable; layers ``1..n_tech``
        follow ``technology_order``. Cells outside the target region are unsuitable for every technology.

        """

        ymin, ymax, xmin, xmax = self.get_region_bounds()

        # cells in the bounding box that do not belong to the target region
        outside_region = self.regions_arr[ymin:ymax, xmin:xmax] != self.target_region_id

        # extract region footprint from suitability data; any non-zero value is unsuitable
        n_tech = self.suitability_arr.shape[0]
        unsuitable = np.empty((n_tech + 1, ymax - ymin, xmax - xmin), dtype=bool)
        unsuitable[0] = True
        np.not_equal(self.suitability_arr[:, ymin:ymax, xmin:xmax], 0, out=unsuitable[1:])
        unsuitable[1:] |= outside_region

        return unsuitable, ymin, ymax, xmin, xmax

    def mask_nlc(self):
        """Extract NLC elements for the current region with suitability applied.

        Returns a plain float array where every unsuitable or NaN cell is ``+inf``, and layer 0 (the "no technology"
        default) is entirely ``+inf`` so it is only chosen by ``argmin`` when no technology can site a cell.

        """

        n_tech, nrows, ncols = self.nlc_arr.shape[0], self.ymax - self.ymin, self.xmax - self.xmin

        nlc_region = self.nlc_arr[:, self.ymin:self.ymax, self.xmin:self.xmax]

        # any NaN cost becomes the most expensive option (still available if suitable); the fill value is one more
        #  than the largest cost seen, floored at 0 to match the historical behaviour where an all-zero default
        #  layer took part in the maximum
        fill_value = max(float(np.nanmax(nlc_region)), 0.0) + 1.0

        nlc_arr_region = np.empty((n_tech + 1, nrows, ncols), dtype=np.float64)
        nlc_arr_region[0] = np.inf
        nlc_arr_region[1:] = np.nan_to_num(nlc_region, nan=fill_value)

        # unsuitable cells are unavailable
        nlc_arr_region[self.suitability_array_region] = np.inf

        return nlc_arr_region

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
        """Extract the LMP, generation, operating cost, NOV, and IC arrays for the target region and return them as
        dictionaries where {tech_id: 2D_region_view, ...}.

        The values are views into the staged full-grid arrays (no copies). `Competition` only reads these metrics at
        the handful of cells that are finally sited, so flattening five full technology stacks per region is avoided.
        A metric supplied as a 1D per-technology vector (spatially constant, e.g. generation) is broadcast to the
        region shape without allocating.

        """

        region_shape = (self.ymax - self.ymin, self.xmax - self.xmin)

        def region_views(arr):
            if arr.ndim == 1:
                return {i: np.broadcast_to(arr[ix], region_shape) for ix, i in enumerate(self.technology_order)}
            region = arr[:, self.ymin:self.ymax, self.xmin:self.xmax]
            return {i: region[ix] for ix, i in enumerate(self.technology_order)}

        return (region_views(self.lmp_arr),
                region_views(self.generation_arr),
                region_views(self.operating_cost_arr),
                region_views(self.nov_arr),
                region_views(self.ic_arr))

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
                   write_output=True,
                   regions_arr=None,
                   region_bounds=None):
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

    :param suitability_arr:                     3D array where {tech_id, x, y} for suitability data; 0 is suitable
                                                and any non-zero value is unsuitable
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

    :param regions_arr:                         2D array of region IDs (from cerf.stage.Stage). Read from the region
                                                raster if not provided.
    :type regions_arr:                          ndarray

    :param region_bounds:                       Precomputed ``{region_id: (ymin, ymax, xmin, xmax)}`` grid-space
                                                bounding boxes (from cerf.stage.Stage). Derived if not provided.
    :type region_bounds:                        dict

    :return:                                    `ProcessRegion` holding the competition result in ``run_data``
                                                (``sited_df``, ``sited_dict``, ``sited_array``, ``expansion_dict``);
                                                an `EmptyRegionResult` with the same attributes and an empty
                                                ``sited_df`` if the region has no sites in its expansion plan

    """

    # region names are keyed in lower case throughout the configuration
    target_region_name = str(target_region_name).lower()

    logger.debug(f'Processing region:  {target_region_name}')

    # check to see if region has any sites in the expansion
    region_plan = expansion_dict[target_region_name]
    n_sites = sum(region_plan[k]['n_sites'] for k in region_plan)

    # if there are no sites in the expansion, return an empty result rather than None so callers can treat every
    #  region uniformly
    if n_sites <= 0:
        logger.warning(f"There were no sites expected for any technology in `{target_region_name}`")
        return EmptyRegionResult(target_region_name, region_plan)

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
                                write_output=write_output,
                                regions_arr=regions_arr,
                                region_bounds=region_bounds)

        logger.info(f'Processed `{target_region_name}` in {round(time.time() - region_t0, 7)} seconds')

        return process
