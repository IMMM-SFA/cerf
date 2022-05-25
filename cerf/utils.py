
import logging

import numpy as np
import pandas as pd
import rasterio
import xarray as xr
import geopandas as gpd
from shapely.geometry import Point


def results_to_geodataframe(result_df, target_crs):
    """Convert the results from 'cerf.run()' to a GeoDataFrame.

    :param result_df:                       Result data frame from running 'cerf.run()'
    :type result_df:                        DataFrame

    :param target_crs:                      Coordinate reference system to assign the output.

    :return:                                GeoPandas GeoDataFrame of results

    """

    # create geometry column from coordinate fields
    geometry = [Point(xy) for xy in zip(result_df['xcoord'], result_df['ycoord'])]

    return gpd.GeoDataFrame(result_df, crs=target_crs, geometry=geometry)


def kilometers_to_miles(input_km_value):
    """Convert kilometers to miles.

    :param input_km_value:          Kilometer value to convert to miles
    :type input_km_value:           float, int

    :return:                        Miles

    """

    return input_km_value * 0.621371


def suppress_callback(value):
    """Do not log callback output for whitebox functions.

    :param value:                   Value of callback

    """

    pass


def empty_sited_dict():
    """Initialize a sited dictionary."""

    return {'region_name': [],
            'tech_id': [],
            'tech_name': [],
            'unit_size_mw': [],
            'xcoord': [],
            'ycoord': [],
            'index': [],
            'buffer_in_km': [],
            'sited_year': [],
            'retirement_year': [],
            'lmp_zone': [],
            'locational_marginal_price_usd_per_mwh': [],
            'generation_mwh_per_year': [],
            'operating_cost_usd_per_year': [],
            'net_operational_value_usd_per_year': [],
            'interconnection_cost_usd_per_year': [],
            'net_locational_cost_usd_per_year': [],
            'capacity_factor_fraction': [],
            'carbon_capture_rate_fraction': [],
            'fuel_co2_content_tons_per_btu': [],
            'fuel_price_usd_per_mmbtu': [],
            'fuel_price_esc_rate_fraction': [],
            'heat_rate_btu_per_kWh': [],
            'lifetime_yrs': [],
            'variable_om_usd_per_mwh': [],
            'variable_om_esc_rate_fraction': [],
            'carbon_tax_usd_per_ton': [],
            'carbon_tax_esc_rate_fraction': []}


def sited_dtypes():
    """Return data type dictionary for the sited data frame."""

    return {'region_name': str,
            'tech_id': np.int64,
            'tech_name': str,
            'unit_size_mw': np.float64,
            'xcoord': np.float64,
            'ycoord': np.float64,
            'lmp_zone': np.int64,
            'locational_marginal_price_usd_per_mwh': np.float64,
            'net_operational_value_usd_per_year': np.float64,
            'interconnection_cost_usd_per_year': np.float64,
            'net_locational_cost_usd_per_year': np.float64,
            'index': np.int64,
            'retirement_year': np.int64,
            'sited_year': np.int64,
            'buffer_in_km': np.int64}


def default_suitabiity_files():
    """Return a dictionary of default suitability file names."""

    return {'biomass_conv_wo_ccs': 'suitability_biomass.sdat',
            'biomass_conv_w_ccs': 'suitability_biomass.sdat',
            'biomass_igcc_wo_ccs': 'suitability_biomass_igcc.sdat',
            'biomass_igcc_w_ccs': 'suitability_biomass_igcc_ccs.sdat',
            'coal_conv_pul_wo_ccs': 'suitability_coal.sdat',
            'coal_conv_pul_w_ccs': 'suitability_coal.sdat',
            'coal_igcc_wo_ccs': 'suitability_coal_igcc.sdat',
            'coal_igcc_w_ccs': 'suitability_coal_igcc_ccs.sdat',
            'gas_cc_wo_ccs': 'suitability_gas_cc.sdat',
            'gas_cc_w_ccs': 'suitability_gas_cc_ccs.sdat',
            'gas_ct_wo_ccs': 'suitability_gas_cc.sdat',
            'geothermal': None,
            'hydro': None,
            'nuclear_gen_ii': 'suitability_nuclear.sdat',
            'nuclear_gen_iii': 'suitability_nuclear.sdat',
            'oil_ct_wo_ccs': 'suitability_oil_baseload.sdat',
            'solar_csp': 'suitability_solar.sdat',
            'solar_pv_non_dist': 'suitability_solar.sdat',
            'wind_onshore': 'suitability_wind.sdat'}


def buffer_flat_array(target_index, arr, nrows, ncols, ncells, set_value):
    """Assign a value to the neighboring elements of a 1D array as if they
    were in 2D space. The number of neighbors are based on the `ncells` argument
    which is used to define the window around the target cell to be altered as
    if they were in 2D space.

    :param target_index:                Index of the target element in the 1D array
    :type target_index:                 int

    :param arr:                         A 1D array that has been flattened from a corresponding 2D array
    :type arr:                          ndarray

    :param nrows:                       The number of rows in the parent 2D array
    :type nrows:                        int

    :param ncols:                       The number of columns in the parent 2D array
    :type ncols:                        int

    :param ncells:                      The number of cells for the buffer extending as a radius
    :type ncells:                       int

    :param set_value:                   The value to set for the selected buffer
    :type set_value:                    int; float

    :return:                            [0] Modified 1D array
                                        [1] list of buffered indices

    """
    # list to hold buffer indices for the target grid cell
    buffer_indices = []

    # calculate the number of elements in the 2D grid space
    ngrids = nrows * ncols

    # ensure that the target index is in the grid space
    if 0 <= target_index < ngrids:

        # target cell index bounds for the row
        min_idx = target_index - ncells
        max_idx = target_index + ncells + 1

        # create target row limits
        end_row_idx = target_index + ncols - np.mod(target_index, ncols) - 1
        start_row_idx = end_row_idx - (ncols - 1)

        # do not let the index bleed past the row
        if max_idx > end_row_idx:
            max_idx = end_row_idx + 1

        # do not let the index go negative
        if min_idx < start_row_idx:
            min_idx = start_row_idx

        # initialize above
        min_above = min_idx - ncols
        max_above = max_idx - ncols

        # initialize below
        min_below = min_idx + ncols
        max_below = max_idx + ncols

        # target row assignment
        arr[min_idx: max_idx] = set_value

        # add indices to buffer list
        buffer_indices.extend(list(range(min_idx, max_idx)))

        for _ in range(ncells):

            # above
            if min_above >= 0 and max_above >= 0 and start_row_idx < ngrids:
                arr[min_above: max_above] = set_value

                # add indices to buffer list
                buffer_indices.extend(list(range(min_above, max_above)))

            # advance above to the next row
            min_above -= ncols
            max_above -= ncols

            # below
            if min_below <= ngrids and max_below <= ngrids:
                arr[min_below: max_below] = set_value

                # add indices to buffer list
                buffer_indices.extend(list(range(min_below, max_below)))

            # advance below to the next row
            min_below += ncols
            max_below += ncols

    else:
        raise IndexError(f"Index: '{target_index}' is not in the range of the grid space from 0 to {ngrids - 1}.")

    return arr, buffer_indices


def array_to_raster(arr, template_raster_file, output_raster_file):
    """Write a raster file from a 2D array."""

    with rasterio.open(template_raster_file) as src:

        metadata = src.meta.copy()

        # update metadata
        metadata.update(dtype=np.float64,
                        nodata=np.nan)

        with rasterio.open(output_raster_file, 'w', **metadata) as dest:
            dest.write(arr, 1)


def raster_to_coord_arrays(template_raster):
    """Use the template raster to create two 2D arrays containing the X and Y coordinates of every grid cell.

    :param template_raster:                 Full path with file name and extension to the input raster.
    :type template_raster:                  str

    :return:                                [0] 2D array of X coordinates
                                            [1] 2D array of Y coordinates

    """

    # Read the data
    da = xr.open_rasterio(template_raster)

    # Compute the lon/lat coordinates with rasterio.warp.transform
    x, y = np.meshgrid(da['x'], da['y'])

    return x, y


def ingest_sited_data(run_year, x_array, siting_data):
    """Import sited data containing the locations and additional data to establish an initial suitability condition
    representing power plants and their siting buffer.

    Required fields are the following and they can appear anywhere in the CSV or data frame:

    xcoord:  the X coordinate of the site in meters in USA_Contiguous_Albers_Equal_Area_Conic (EPSG:  102003)
    ycoord:  the Y coordinate of the site in meters in USA_Contiguous_Albers_Equal_Area_Conic (EPSG:  102003)
    retirement_year:  the year (int four digit, e.g., 2050) that the power plant is to be decommissioned
    buffer_in_km:  the buffer around the site to apply in kilometers

    :param run_year:                        Four-digit year of the current run (e.g., 2050)
    :type run_year:                         int

    :param x_array:                         2D array of X coordinates for the entire grid space
    :type x_array:                          ndarray

    :param y_array:                         2D array of Y coordinates for the entire grid space
    :type y_array:                          ndarray

    :param siting_data:                     Full path with file name and extension for the input siting file or a
                                            Pandas DataFrame
    :type siting_data:                      str, DataFrame

    :return:                                [0] 2D array of 0 (suitable) and 1 (unsuitable) values where 1 are the sites
                                            and their buffers of active power plants

                                            [1] Pandas DataFrame of active sites (not retired)

    """

    # assign input data to a data frame
    if isinstance(siting_data, pd.DataFrame):
        df = siting_data
    elif isinstance(siting_data, str):
        df = pd.read_csv(siting_data, dtype=sited_dtypes())
    else:
        msg = "The user must pass either a CSV file path to 'sited_csv' or a Pandas DataFrame to 'sited_df'"
        logging.error(msg)
        raise TypeError()

    # only keep sites that are not retired
    df_active = df.loc[df['retirement_year'] > run_year].copy()

    # initialize an array to hold the 0, 1 sited and buffer data
    sited_arr = np.zeros_like(x_array).flatten()

    for ix in df_active['index'].tolist():

        # get the buffer size for the site
        site_buffer_km = df_active.loc[df_active['index'] == ix]['buffer_in_km'].values[0]

        # apply the buffer to the site and set to the entire array
        sited_arr = buffer_flat_array(ix, sited_arr, x_array.shape[0], x_array.shape[1], site_buffer_km, 1)[0]

    return sited_arr.reshape(x_array.shape).astype(np.int8), df_active
