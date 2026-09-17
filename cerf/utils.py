import os
import logging
import tempfile

import numpy as np
import pandas as pd
import rasterio
import geopandas as gpd
from scipy.ndimage import find_objects
from shapely.geometry import Point

logger = logging.getLogger(__name__)


def region_bounding_boxes(regions_arr):
    """Compute the grid-space bounding box of every region ID present in a 2D region raster array.

    The bounds follow Python slice conventions so that ``arr[ymin:ymax, xmin:xmax]`` is the smallest window
    containing every cell of the region, matching the values previously derived per region with ``np.where``.

    :param regions_arr:                     2D array of integer region IDs
    :type regions_arr:                      ndarray

    :return:                                Dictionary of ``{region_id: (ymin, ymax, xmin, xmax)}`` for every region
                                            ID that occurs in the array (a nodata/background ID is included if present)

    """

    regions_arr = np.asarray(regions_arr)

    if regions_arr.ndim != 2:
        raise ValueError(f"`regions_arr` must be 2D; got shape {regions_arr.shape}")

    if not np.issubdtype(regions_arr.dtype, np.integer):
        raise TypeError(f"`regions_arr` must have an integer dtype; got {regions_arr.dtype}")

    # find_objects treats 0 as background and needs labels >= 1 and small; remap the (arbitrary, possibly
    #  negative or nodata) IDs to 1..n first
    ids, labels = np.unique(regions_arr, return_inverse=True)
    labels = labels.reshape(regions_arr.shape).astype(np.int32) + 1

    slices = find_objects(labels)

    return {int(region_id): (sl[0].start, sl[0].stop, sl[1].start, sl[1].stop)
            for region_id, sl in zip(ids, slices) if sl is not None}


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
            'operational_life_yrs': [],
            'variable_om_usd_per_mwh': [],
            'variable_om_esc_rate_fraction': [],
            'carbon_tax_usd_per_ton': [],
            'carbon_tax_esc_rate_fraction': []}


def sited_dtypes():
    """Return the data type of every column produced by `empty_sited_dict()`.

    Keeping this complete ensures an empty initial frame, per-region results, and a CSV round trip through
    `ingest_sited_data` all carry identical dtypes rather than whatever pandas infers per column.

    """

    return {'region_name': str,
            'tech_id': np.int64,
            'tech_name': str,
            'unit_size_mw': np.float64,
            'xcoord': np.float64,
            'ycoord': np.float64,
            'index': np.int64,
            'buffer_in_km': np.int64,
            'sited_year': np.int64,
            'retirement_year': np.int64,
            'lmp_zone': np.int64,
            'locational_marginal_price_usd_per_mwh': np.float64,
            'generation_mwh_per_year': np.float64,
            'operating_cost_usd_per_year': np.float64,
            'net_operational_value_usd_per_year': np.float64,
            'interconnection_cost_usd_per_year': np.float64,
            'net_locational_cost_usd_per_year': np.float64,
            'capacity_factor_fraction': np.float64,
            'carbon_capture_rate_fraction': np.float64,
            'fuel_co2_content_tons_per_btu': np.float64,
            'fuel_price_usd_per_mmbtu': np.float64,
            'fuel_price_esc_rate_fraction': np.float64,
            'heat_rate_btu_per_kWh': np.float64,
            'lifetime_yrs': np.int64,
            'operational_life_yrs': np.int64,
            'variable_om_usd_per_mwh': np.float64,
            'variable_om_esc_rate_fraction': np.float64,
            'carbon_tax_usd_per_ton': np.float64,
            'carbon_tax_esc_rate_fraction': np.float64}


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


def buffer_window(target_index, nrows, ncols, ncells):
    """Return the ``(row_slice, col_slice)`` of the square window of ``ncells`` cells around a flat grid index,
    clipped to the grid.

    :param target_index:                Flat (row-major) index of the target cell
    :type target_index:                 int

    :param nrows:                       The number of rows in the parent 2D array
    :type nrows:                        int

    :param ncols:                       The number of columns in the parent 2D array
    :type ncols:                        int

    :param ncells:                      The number of cells for the buffer extending as a radius
    :type ncells:                       int

    :return:                            ``(slice(r0, r1), slice(c0, c1))`` usable directly on the 2D array

    """

    ngrids = nrows * ncols
    target_index = int(target_index)

    if not 0 <= target_index < ngrids:
        raise IndexError(f"Index: '{target_index}' is not in the range of the grid space from 0 to {ngrids - 1}.")

    ncells = int(ncells)
    row, col = divmod(target_index, ncols)

    return (slice(max(row - ncells, 0), min(row + ncells + 1, nrows)),
            slice(max(col - ncells, 0), min(col + ncells + 1, ncols)))


def buffer_flat_indices(target_index, nrows, ncols, ncells):
    """Return the sorted flat indices of the square window of ``ncells`` cells around a flat grid index, clipped to
    the grid, as an integer NumPy array.

    Parameters are as for `buffer_window`.

    """

    rows, cols = buffer_window(target_index, nrows, ncols, ncells)

    return (np.arange(rows.start, rows.stop, dtype=np.intp)[:, None] * ncols
            + np.arange(cols.start, cols.stop, dtype=np.intp)).ravel()


def buffer_flat_array(target_index, arr, nrows, ncols, ncells, set_value):
    """Assign a value to the neighboring elements of a 1D array as if they
    were in 2D space. The number of neighbors are based on the `ncells` argument
    which is used to define the window around the target cell to be altered as
    if they were in 2D space.

    :param target_index:                Index of the target element in the 1D array
    :type target_index:                 int

    :param arr:                         A 1D array that has been flattened from a corresponding 2D array; modified
                                        in place
    :type arr:                          ndarray

    :param nrows:                       The number of rows in the parent 2D array
    :type nrows:                        int

    :param ncols:                       The number of columns in the parent 2D array
    :type ncols:                        int

    :param ncells:                      The number of cells for the buffer extending as a radius
    :type ncells:                       int

    :param set_value:                   The value to set for the selected buffer
    :type set_value:                    int; float

    :return:                            [0] Modified 1D array (the same object as ``arr``)
                                        [1] Sorted integer array of buffered flat indices

    """

    buffer_indices = buffer_flat_indices(target_index, nrows, ncols, ncells)

    arr[buffer_indices] = set_value

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
    """Use the template raster to create two 2D arrays containing the X and Y cell-centre coordinates of every grid
    cell, computed from the raster's affine transform.

    :param template_raster:                 Full path with file name and extension to the input raster.
    :type template_raster:                  str

    :return:                                [0] 2D array of X coordinates
                                            [1] 2D array of Y coordinates

    """

    with rasterio.open(template_raster) as src:
        transform = src.transform
        height, width = src.height, src.width

    if transform.b != 0 or transform.d != 0:
        raise ValueError(f"Rotated or sheared rasters are not supported: {template_raster}")

    # cell centres: origin + (index + 0.5) * pixel size along each axis
    xs = transform.c + (np.arange(width) + 0.5) * transform.a
    ys = transform.f + (np.arange(height) + 0.5) * transform.e

    return np.meshgrid(xs, ys)


def ingest_sited_data(run_year,
                      x_array,
                      siting_data,
                      template_raster_file: str):
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

    :param siting_data:                     Full path with file name and extension for the input siting file or a
                                            Pandas DataFrame
    :type siting_data:                      str, DataFrame

    :param template_raster_file:            Full path with file name and extension to the input template raster file
                                            containing a grid index value per grid cell.
    :type template_raster_file:             str

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
        logger.error(msg)
        raise TypeError()

    # only keep sites that are not retired
    df_active = df.loc[df['retirement_year'] > run_year].copy()

    # initialize an array to hold the 0, 1 sited and buffer data
    sited_arr = np.zeros_like(x_array).flatten()

    # generate the corresponding grid index for the input coordinate pairs
    with rasterio.open(template_raster_file) as src:
        metadata = src.meta.copy()

        # get array
        arr = src.read(1)
        n_cells = arr.shape[0] * arr.shape[1]
        max_allowable_cells = np.iinfo(rasterio.uint32).max

        if n_cells > max_allowable_cells:
            raise ValueError(f"Too many grid cells in array for a uint32 format.  Max allowable: {max_allowable_cells}")

        # create continuous index values from flat array and then reshape back to 2D
        flat_arr = np.array(range(arr.shape[0] * arr.shape[1]))
        index_arr = flat_arr.reshape((arr.shape[0], arr.shape[1])).astype(np.uint32)

        # update data type
        metadata.update(dtype=np.uint32)

    with tempfile.TemporaryDirectory() as tempdir:

        # construct temporary raster file name
        out_temp_rast = os.path.join(tempdir, "cerf_temp_raster.tif")

        # write array as spatial in a temp file
        with rasterio.open(out_temp_rast, "w", **metadata) as dest:
            dest.write(index_arr, 1)

        # read temp file to use for grid search
        with rasterio.open(out_temp_rast) as idx:
            index_generator = idx.sample(df_active[["xcoord", "ycoord"]].values)
            located_index_list = [i[0] for i in index_generator]

    # give the input data frame the new index from the coordinate lookup
    df_active["index"] = located_index_list

    for ix in df_active['index'].tolist():

        # get the buffer size for the site
        site_buffer_km = df_active.loc[df_active['index'] == ix]['buffer_in_km'].values[0]

        # apply the buffer to the site and set to the entire array
        sited_arr = buffer_flat_array(ix, sited_arr, x_array.shape[0], x_array.shape[1], site_buffer_km, 1)[0]

    return sited_arr.reshape(x_array.shape).astype(np.int8), df_active
