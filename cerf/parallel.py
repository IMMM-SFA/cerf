"""Parallelization module for CERF

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
from cerf.process_state import process_state


def generate_model(config_file, initialize_site_data=None):
    """Generate model instance for use in parallel applications.

    :param config_file:                 Full path with file name and extension to the input config.yml file
    :type config_file:                  str

    :param   initialize_site_data:      None if no initialization is required, otherwise either a CSV file or
                                        Pandas DataFrame of siting data bearing the following required fields:

                                        xcoord:  the X coordinate of the site in meters in
                                        USA_Contiguous_Albers_Equal_Area_Conic (EPSG:  102003)

                                        ycoord:  the Y coordinate of the site in meters in
                                        USA_Contiguous_Albers_Equal_Area_Conic (EPSG:  102003)

                                        retirement_year:  the year (int four digit, e.g., 2050) that the power
                                        plant is to be decommissioned

                                        buffer_in_km:  the buffer around the site to apply in kilometers

    """

    return Model(config_file, initialize_site_data)


def cerf_parallel(model, data, write_output=True, n_jobs=-1, method='sequential'):
    """Run all CONUS states in parallel.

    :param model:                       Instantiated CERF model class containing configuration options
    :type model:                        class

    :param data:                        Data from cerf.stage.Stage containing NLC and suitability arrays

    :param config_file:                 Full path with file name and extension to the input config.yml file
    :type config_file:                  str

    :param write_output:                Write output as a raster to the output directory specified in the config file
    :type write_output:                 bool

    :param n_jobs:                      The number of processors to utilize.  Default is -1 which is all but 1.
    :type n_jobs:                       int

    :param method:                      Backend parallelization method used in Joblib.  Default is `sequential` to
                                        manage overhead for local runs.  Options for advanced configurations are:
                                        `loky`, `threading`, and `multiprocessing`.
                                        See https://joblib.readthedocs.io/en/latest/parallel.html for details.
    :type method:                       str

    :return:                            A 2D arrays containing sites as the technology ID per grid cell.  All
                                        non-sited grid cells are given the value of NaN.

    """

    # start time for parallel run
    t0 = time.time()

    # run all states in parallel
    results = Parallel(n_jobs=n_jobs, backend=method)(delayed(process_state)(target_state_name=i,
                                                                             settings_dict=model.settings_dict,
                                                                             technology_dict=model.technology_dict,
                                                                             technology_order=model.technology_order,
                                                                             expansion_dict=model.expansion_dict,
                                                                             states_dict=model.states_dict,
                                                                             suitability_arr=data.suitability_arr,
                                                                             lmp_arr=data.lmp_arr,
                                                                             nov_arr=data.nov_arr,
                                                                             ic_arr=data.ic_arr,
                                                                             nlc_arr=data.nlc_arr,
                                                                             zones_arr=data.zones_arr,
                                                                             xcoords=data.xcoords,
                                                                             ycoords=data.ycoords,
                                                                             indices_2d=data.indices_2d,
                                                                             randomize=model.settings_dict.get('randomize', True),
                                                                             seed_value=model.settings_dict.get('seed_value', 0),
                                                                             verbose=model.settings_dict.get('verbose', False),
                                                                             write_output=False) for i in model.states_dict.keys())

    logging.info(f"All states processed in {round((time.time() - t0), 7)} seconds.")
    logging.info("Aggregating outputs...")

    # create a data frame to hold the outputs
    df = pd.DataFrame(util.empty_sited_dict()).astype(util.sited_dtypes())

    # add in the initialized siting data from a previous years run if so desired
    if model.initialize_site_data is not None:
        df = pd.concat([df, data.init_df])

    # combine the outputs for all states
    for i in results:

        # ensure some sites were able to be sited for the target state
        if i is not None:
            df = pd.concat([df, i.run_data.sited_df])

    if write_output:

        # write output CSV
        out_csv = os.path.join(model.settings_dict.get('output_directory'), f"cerf_sited_{model.settings_dict.get('run_year')}_conus.csv")
        df.to_csv(out_csv, index=False)

    return df


def run_parallel(config_file, write_output=True, n_jobs=-1, method='sequential', initialize_site_data=None):
    """Generate model instance for use in parallel applications.

    :param config_file:                 Full path with file name and extension to the input config.yml file
    :type config_file:                  str

    :param write_output:                Write output as a raster to the output directory specified in the config file
    :type write_output:                 bool

    :param n_jobs:                      The number of processors to utilize.  Default is -1 which is all but 1.
    :type n_jobs:                       int

    :param method:                      Backend parallelization method used in Joblib.  Default is sequential to
                                        manage overhead for local runs.  Options for advanced configurations are:
                                        loky, threading, and multiprocessing.
                                        See https://joblib.readthedocs.io/en/latest/parallel.html for details.
    :type method:                       str

    :param   initialize_site_data:      None if no initialization is required, otherwise either a CSV file or
                                        Pandas DataFrame of siting data bearing the following required fields:

                                        xcoord:  the X coordinate of the site in meters in
                                        USA_Contiguous_Albers_Equal_Area_Conic (EPSG:  102003)

                                        ycoord:  the Y coordinate of the site in meters in
                                        USA_Contiguous_Albers_Equal_Area_Conic (EPSG:  102003)

                                        retirement_year:  the year (int four digit, e.g., 2050) that the power
                                        plant is to be decommissioned

                                        buffer_in_km:  the buffer around the site to apply in kilometers

    :return:                            A 2D arrays containing sites as the technology ID per grid cell.  All
                                        non-sited grid cells are given the value of NaN.

    """

    # instantiate CERF model
    model = generate_model(config_file, initialize_site_data=initialize_site_data)

    # process supporting data
    data = model.stage()

    # process all CERF CONUS states in parallel and store the result as a 2D arrays containing sites as
    #  the technology ID per grid cell.  All non-sited grid cells are given the value of NaN.
    df = cerf_parallel(model=model,
                       data=data,
                       write_output=write_output,
                       n_jobs=n_jobs,
                       method=method)

    logging.info(f"CERF model run completed in {round(time.time() - model.start_time, 7)}")

    # clean up logger
    model.close_logger()

    return df