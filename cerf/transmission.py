import pkg_resources
import tempfile

import rasterio
import whitebox
import yaml

import numpy as np
import geopandas as gpd

from rasterio import features

from cerf.utils import suppress_callback
from cerf.data.package_data import cerf_crs, costs_per_kv_substation


def process_eia_natural_gas_pipelines(pipeline_file=None):
    """Select natural gas pipelines from EIA data that have a status of operating and a length greater than 0.

    :param pipeline_file:                   Full path with file name and extension to the input pipelines shapefile.
                                            If None, CERF will use the default data stored in the package.

    :type pipeline_file:                    str

    :returns:                               A geodataframe containing the target pipelines

    """

    if pipeline_file is None:
        return gpd.read_file(pkg_resources.resource_filename('cerf', 'data/eia_natural_gas_pipelines_conus_albers.zip'))

    else:

        # load cerf's default coordinate reference system object
        target_crs = cerf_crs()

        # read in data and reproject
        gdf = gpd.read_file(pipeline_file).to_crs(target_crs)

        # only keep features with a length > 0
        gdf = gdf.loc[gdf.geometry.length > 0].copy()

        # only keep operational pipelines
        return gdf.loc[gdf['Status'] == 'Operating'].copy()


def process_hifld_substations(substation_file=None, costs_to_connect_dict=None):
    """Select substations from HIFLD data that are within the CONUS and either in service or under construction and
    having a minimum voltage rating >= 0.  A field used to rasterize ('_rval_') is also added containing the cost of
    connection in $/km for each substation.

    This data is assumed to have the following fields:  ['TYPE', 'STATE', 'STATUS'].

    :param substation_file:                 Full path with file name and extension to the input substations shapefile.
                                            If None, CERF will use the default data stored in the package.

    :type substation_file:                  str

    :param costs_to_connect_dict:           A dictionary containing the cost of connection per km to a substation
                                            having a certain minimum voltage range.  Default is to load from the
                                            CERF data file 'costs_per_kv_substation.yml' by specifying 'None'
    :type costs_to_connect_dict:            dict

    :returns:                               A geodataframe containing the target substations

    """

    # load cost dictionary from package data if none passed
    if costs_to_connect_dict is None:
        costs_to_connect_dict = costs_per_kv_substation()

    if substation_file is None:
        return gpd.read_file(pkg_resources.resource_filename('cerf', 'data/hifld_substations_conus_albers.zip'))

    else:

        # get state abbreviations file from cerf pacakge data
        states_file = pkg_resources.resource_filename('cerf', 'data/state-abbrev_to_state-name.yml')

        # get state abbreviations to search for in HIFLD data
        with open(states_file, 'r') as yml:
            states = yaml.load(yml, Loader=yaml.FullLoader)

        # load cerf's default coordinate reference system object
        target_crs = cerf_crs()

        # load and reproject
        gdf = gpd.read_file(substation_file).to_crs(target_crs)

        # keep only substations in the CONUS that are either in service or under construction
        gdf = gdf.loc[(gdf['TYPE'] == 'SUBSTATION') &
                      (gdf['STATE'].isin(states.keys())) &
                      (gdf['STATUS'].isin(('IN SERVICE', 'UNDER CONST'))) &
                      (gdf['MIN_VOLT'] >= 0)].copy()

        # assign a field to rasterize by containing the cost of transmission per km
        gdf['_rval_'] = 0

        for i in costs_to_connect_dict.keys():

            gdf['_rval_'] = np.where((gdf['MIN_VOLT'] >= costs_to_connect_dict[i]['min_voltage']) &
                                     (gdf['MIN_VOLT'] <= costs_to_connect_dict[i]['max_voltage']),
                                     costs_to_connect_dict[i]['dollar_per_km'],
                                     gdf['_rval_'])

        return gdf


def transmission_to_cost_raster(transmission_gdf, output_dist_file, output_alloc_file, output_cost_file):
    """Create a cost per grid cell in $/km from the input GeoDataFrame of transmission infrastructure having a cost
    designation field as '_rval_'.

    :param transmission_gdf:                    GeoDataFrame of transmission infrastructure to be rasterized
    :type transmission_gdf:                     GeoDataFrame

    :param output_dist_file:                    Full path with filename and extension to write the distance raster to
    :type output_dist_file:                     str

    :param output_alloc_file:                   Full path with filename and extension to write the allocation raster to
    :type output_alloc_file:                    str

    :param output_cost_file:                    Full path with filename and extension to write the allocation raster to
    :type output_cost_file:                     str

    :return:                                    Array of transmission interconnection cost per grid cell

    """
    # conversion factor for meters to km
    m_to_km_factor = 0.001

    # instantiate whitebox toolset
    wbt = whitebox.WhiteboxTools()

    # get the template raster from CERF data
    template_raster = pkg_resources.resource_filename('cerf', 'data/cerf_conus_states_albers_1km.tif')

    with tempfile.NamedTemporaryFile(suffix='.tif') as temp:

        with rasterio.open(template_raster) as src:
            # create 0 where land array
            arr = (src.read(1) * 0).astype(rasterio.float64)

            # update metadata datatype to float64
            metadata = src.meta.copy()
            metadata.update({'dtype': rasterio.float64})

            # reproject transmission data
            gdf = transmission_gdf.to_crs(src.crs)

            # get shapes
            shapes = ((geom, value) for geom, value in zip(gdf.geometry, gdf['_rval_']))

        # rasterize transmission vector data and write to memory
        with rasterio.open(temp.name, 'w', **metadata) as dataset:
            # burn features into raster
            burned = features.rasterize(shapes=shapes, fill=0, out=arr, transform=dataset.transform)

            # write the outputs to file
            dataset.write_band(1, burned)

        # calculate Euclidean distance and write raster; result just stores the return value 0
        dist_result = wbt.euclidean_distance(temp.name, output_dist_file, callback=suppress_callback)

        # calculate Euclidean allocation and write raster
        alloc_result = wbt.euclidean_allocation(temp.name, output_alloc_file, callback=suppress_callback)

        with rasterio.open(output_dist_file) as dist:
            dist_arr = dist.read(1)

        with rasterio.open(output_alloc_file) as alloc:
            alloc_arr = alloc.read(1)

        with rasterio.open(output_cost_file, 'w', **metadata) as out:

            # distance in km * the cost of the nearest substation; outputs $2015/km
            cost_arr = (dist_arr * m_to_km_factor) * alloc_arr

            out.write(cost_arr, 1)

    return cost_arr
