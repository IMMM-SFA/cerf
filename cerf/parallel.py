"""Parallelization module for CERF

@author Chris R. vernon
@email chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

import logging
import os
import time

from joblib import Parallel, delayed
import numpy as np

from cerf.model import Model
from cerf.process_state import process_state
import cerf.utils as util


def generate_model(config_file):
    """Generate model instance and stage data."""

    # instantiate model
    return Model(config_file)


def cerf_parallel(model, data, write_output=True, n_jobs=-1, method='sequential'):
    """Run all states in parallel"""

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
                                                                             nlc_arr=data.nlc_arr,
                                                                             randomize=model.settings_dict.get('randomize', True),
                                                                             seed_value=model.settings_dict.get('seed_value', 0),
                                                                             verbose=model.settings_dict.get('verbose', False),
                                                                             write_output=False) for i in model.states_dict.keys())

    logging.info(f"All states processed in {round((time.time() - t0), 7)} seconds.")

    # aggregate results into a single raster
    array_shape = results[0].shape
    n_techs = len(results)

    # construct a 3D array to house outputs
    result_arr_3d = np.zeros(shape=(n_techs, array_shape[0], array_shape[1]))

    # add results to 3D array
    for index in range(n_techs):
        result_arr_3d[index, :, :] = results[index]

    # create a 2D array that aggregates all individual state results; all NaN elements become 0.0
    result_arr_2d = np.nansum(result_arr_3d, axis=0)

    # replace 0 with NaN
    result_arr_2d = np.where(result_arr_2d == 0, np.nan, result_arr_2d)

    if write_output:

        # output raster file for sited power plants
        out_file = os.path.join(model.settings_dict.get('output_directory'), f"cerf_sited_{model.settings_dict.get('run_year')}_conus.tif")
        logging.info(f"Aggregated outputs for all states to raster file:  {out_file}")

        # write output using a template to prescribe the metadata
        template_raster = model.technology_dict[model.technology_order[0]]['interconnection_distance_raster_file']
        util.array_to_raster(result_arr_2d, template_raster, out_file)

    return result_arr_2d


def run_parallel(config_file):

    model = generate_model(config_file)

    data = model.stage()

    res = cerf_parallel(model, data)

    logging.info(f"CERF model run completed in {round(time.time() - model.start_time, 7)}")

    model.close_logger()

    return res


if __name__ == '__main__':

    import pkg_resources

    c = pkg_resources.resource_filename('cerf', 'tests/data/config.yml')

    opt = run_parallel(c)
