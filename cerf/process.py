"""Processing module for CERF

@author Chris R. vernon
@email chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

import logging
import os
import time

import pandas as pd
from joblib import Parallel, delayed

import cerf.utils as util
from cerf.model import Model
from cerf.process_region import RegionData, process_region

logger = logging.getLogger(__name__)


def generate_model(config_file=None, config_dict=None, initialize_site_data=None, log_level='info'):
    """Generate model instance for use in parallel applications.

    :param config_file:                 Full path with file name and extension to the input config.yml file
    :type config_file:                  str

    :param config_dict:                 Optional instead of config_file. Configuration dictionary.
    :type config_dict:                  dict

    :param   initialize_site_data:      None if no initialization is required, otherwise either a CSV file or
                                        Pandas DataFrame of siting data bearing the following required fields:

                                        xcoord:  the X coordinate of the site in meters in
                                        USA_Contiguous_Albers_Equal_Area_Conic (EPSG:  102003)

                                        ycoord:  the Y coordinate of the site in meters in
                                        USA_Contiguous_Albers_Equal_Area_Conic (EPSG:  102003)

                                        retirement_year:  the year (int four digit, e.g., 2050) that the power
                                        plant is to be decommissioned

                                        buffer_in_km:  the buffer around the site to apply in kilometers

    :param log_level:                   Log level.  Options are 'info' and 'debug'.  Default 'info'
    :type log_level:                    str

    """

    return Model(config_file, config_dict, initialize_site_data, log_level)


# joblib backends that run tasks in separate processes and therefore pickle every argument per task
PROCESS_BACKENDS = ('loky', 'multiprocessing')


def region_tasks(model, data, method):
    """Yield the `process_region` keyword arguments for every region in the model.

    With an in-process backend (``sequential``, ``threading``) the staged full-grid arrays are shared by reference.
    With a process backend (``loky``, ``multiprocessing``) every argument is pickled per task, so each region is
    cropped to its bounding box in the parent first (see `RegionData.crop`); a region's payload is then proportional
    to its own area (Texas ~11% of the grid, Rhode Island <0.1%) instead of ~4 GB of full-grid arrays per task.

    :param model:                       `cerf.model.Model` (configuration)
    :param data:                        `cerf.stage.Stage` or `RegionData` (staged arrays)
    :param method:                      joblib backend name

    """

    common = dict(settings_dict=model.settings_dict,
                  technology_dict=model.technology_dict,
                  technology_order=model.technology_order,
                  expansion_dict=model.expansion_dict,
                  regions_dict=model.regions_dict,
                  randomize=model.settings_dict.get('randomize', True),
                  seed_value=model.settings_dict.get('seed_value', 0),
                  verbose=model.settings_dict.get('verbose', False),
                  write_output=False)

    region_data = data if isinstance(data, RegionData) else RegionData.from_stage(data)

    crop = method in PROCESS_BACKENDS

    for region_name, region_id in model.regions_dict.items():

        yield dict(common,
                   target_region_name=region_name,
                   data=region_data.crop(region_id) if crop else region_data)


def aggregate_results(results, init_df=None):
    """Combine per-region results into a single sited data frame with the canonical columns and dtypes.

    :param results:                     Iterable of `ProcessRegion` / `EmptyRegionResult` objects (``None`` entries
                                        are tolerated for backwards compatibility)
    :param init_df:                     Optional data frame of still-active sites from a previous run to prepend

    """

    frames = [pd.DataFrame(util.empty_sited_dict()).astype(util.sited_dtypes())]

    if init_df is not None:
        frames.append(init_df)

    frames.extend(i.run_data.sited_df for i in results if i is not None)

    return pd.concat(frames, ignore_index=True)


def cerf_parallel(model, data, write_output=True, n_jobs=-1, method='sequential'):
    """Run all regions in parallel.

    :param model:                       Instantiated CERF model class containing configuration options
    :type model:                        class

    :param data:                        Data from cerf.stage.Stage containing NLC and suitability arrays
    :type data:                         cerf.stage.Stage

    :param write_output:                Write the combined sited CSV to the output directory specified in the config
    :type write_output:                 bool

    :param n_jobs:                      The number of processors to utilize. Default is -1 which uses all processors
                                        (``-2`` is all but one; see joblib).
    :type n_jobs:                       int

    :param method:                      Backend parallelization method used in Joblib.  Default is `sequential` to
                                        manage overhead for local runs.  Options for advanced configurations are:
                                        `loky`, `threading`, and `multiprocessing`. For the process backends each
                                        region is cropped to its bounding box before dispatch so workers receive
                                        only the data they need.
                                        See https://joblib.readthedocs.io/en/latest/parallel.html for details.
    :type method:                       str

    :return:                            A data frame containing each sited power plant and its attributes

    """

    # start time for parallel run
    t0 = time.time()

    # run all regions in parallel
    results = Parallel(n_jobs=n_jobs, backend=method)(delayed(process_region)(**kwargs)
                                                      for kwargs in region_tasks(model, data, method))

    logger.info(f"All regions processed in {round((time.time() - t0), 7)} seconds.")
    logger.info("Aggregating outputs...")

    # combine the outputs for all regions, including active sites from a previous run if provided
    df = aggregate_results(results, init_df=data.init_df if model.initialize_site_data is not None else None)

    if write_output:

        # write output CSV
        out_csv = os.path.join(model.settings_dict.get('output_directory'), f"cerf_sited_{model.settings_dict.get('run_year')}_conus.csv")
        df.to_csv(out_csv, index=False)

    return df


def run(config_file=None, config_dict=None, write_output=True, n_jobs=-1, method='sequential',
            initialize_site_data=None, log_level='info'):
    """Run all CERF regions for the target year.

    :param config_file:                 Full path with file name and extension to the input config.yml file
    :type config_file:                  str

    :param config_dict:                 Optional instead of config_file. Configuration dictionary.
    :type config_dict:                  dict

    :param write_output:                Write output as a raster to the output directory specified in the config file
    :type write_output:                 bool

    :param n_jobs:                      The number of processors to utilize. Default is -1 which uses all processors
                                        (``-2`` is all but one; see joblib).
    :type n_jobs:                       int

    :param method:                      Backend parallelization method used in Joblib.  Default is sequential to
                                        manage overhead for local runs.  Options for advanced configurations are:
                                        loky, threading, and multiprocessing.
                                        See https://joblib.readthedocs.io/en/latest/parallel.html for details.
    :type method:                       str

    :param initialize_site_data:        None if no initialization is required, otherwise either a CSV file or
                                        Pandas DataFrame of siting data bearing the following required fields:

                                        xcoord:  the X coordinate of the site in meters in
                                        USA_Contiguous_Albers_Equal_Area_Conic (EPSG:  102003)

                                        ycoord:  the Y coordinate of the site in meters in
                                        USA_Contiguous_Albers_Equal_Area_Conic (EPSG:  102003)

                                        retirement_year:  the year (int four digit, e.g., 2050) that the power
                                        plant is to be decommissioned

                                        buffer_in_km:  the buffer around the site to apply in kilometers

    :param log_level:                   Log level.  Options are 'info' and 'debug'.  Default 'info'
    :type log_level:                    str

    :return:                            A data frame containing each sited power plant and their attributes

    """

    try:

        # instantiate CERF model
        model = generate_model(config_file,
                               config_dict,
                               initialize_site_data=initialize_site_data,
                               log_level=log_level.lower())

        # process supporting data
        data = model.stage()

        # process all CERF regions in parallel and store the result as a 2D arrays containing sites as
        #  the technology ID per grid cell.  All non-sited grid cells are given the value of NaN.
        df = cerf_parallel(model=model,
                           data=data,
                           write_output=write_output,
                           n_jobs=n_jobs,
                           method=method)

        logger.info(f"CERF model run completed in {round(time.time() - model.start_time, 7)} seconds")

    finally:
        # detach the handlers CERF attached to its own logger; application handlers are left alone
        Model.close_logger()

    return df
