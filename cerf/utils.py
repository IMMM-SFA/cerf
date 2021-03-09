
import logging

import numpy as np
import pandas as pd
import rasterio
import xarray as xr


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


def ingest_sited_data(run_year, x_array, y_array, sited_csv=None, sited_df=None):
    """Import sited data containing the locations and additional data to establish an initial suitability condition
    representing power plants and their siting buffer.

    Required fields are the following and they can appear anywhere in the CSV or data frame:

    `xcoord`:  the X coordinate of the site in meters in USA_Contiguous_Albers_Equal_Area_Conic (EPSG:  102003)
    `ycoord`:  the Y coordinate of the site in meters in USA_Contiguous_Albers_Equal_Area_Conic (EPSG:  102003)
    `retirement_year`:  the year (int four digit, e.g., 2050) that the power plant is to be decommissioned
    `buffer_in_km':  the buffer around the site to apply in kilometers

    :param run_year:                        Four-digit year of the current run (e.g., 2050)
    :type run_year:                         int

    :param x_array:                         2D array of X coordinates for the entire grid space
    :type x_array:                          ndarray

    :param y_array:                         2D array of Y coordinates for the entire grid space
    :type y_array:                          ndarray

    :param sited_csv:                       Full path with file name and extension for the input siting file
    :type sited_csv:                        str

    :param sited_df:                        Pandas DataFrame of sited data
    :type sited_df:                         DataFrame

    :return:                                2D array of 0 (suitable) and 1 (unsuitable) values where 1 are the sites
                                            and their buffers of active power plants

    """

    # if the user chooses to pass a CSV of data
    if (sited_csv is None) and (sited_df is None):
        msg = "The user must pass either a CSV file path to `sited_csv` or a Pandas DataFrame to `sited_df`"
        logging.error(msg)
        raise AssertionError()

    elif (sited_csv is not None) and (sited_df is not None):
        logging.info("Both a `sited_csv` and `sited_df` were provided.  Using `sited_df`")
        df = sited_df

    elif (sited_csv is not None) and (sited_df is None):
        df = pd.read_csv(sited_csv)

    else:
        df = sited_df

    # create a data frame using the x, y coordinate data for the entire grid space
    df_coords = pd.DataFrame({'xcoord': x_array.flatten(), 'ycoord': y_array.flatten()})

    # initialize an array to hold the 0, 1 sited and buffer data
    sited_arr = np.zeros_like(x_array).flatten()

    # only keep sites that are not retired
    df_active = df.loc[df['retirement_year'] > run_year].copy()

    # assign the index of the coordinate in 1D grid space to the sited data as a spatial reference
    l = []
    for i in df_active[['xcoord', 'ycoord']].values:
        v = df_coords.loc[(df_coords['xcoord'].round(4) == i[0]) & (df_coords['ycoord'].round(4) == i[1])]
        l.append(v.index.values[0])

    # key is the index of the full coordinate data frame to the coordinates for each site
    df_active['key'] = l

    # apply the corresponding buffer to each site and
    for ix in df_active['key'].tolist():

        # get the buffer size for the site
        site_buffer_km = df_active.loc[df_active['key'] == ix]['buffer_in_km'].values[0]

        # apply the buffer to the site and set to the entire array
        sited_arr = buffer_flat_array(ix, sited_arr, x_array.shape[0], x_array.shape[1], site_buffer_km, 1)[0]

    return sited_arr.reshape(x_array.shape)

