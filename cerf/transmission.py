import pkg_resources
import tempfile

import rasterio
import whitebox
import yaml

import geopandas as gpd

from rasterio import features

from cerf.utils import suppress_callback


def process_hifld_substations(substation_file=None):
    """Select substations from HIFLD data that are within the CONUS and either in service or under
    construction.

    This data is assumed to have the following fields:  ['TYPE', 'STATE', 'STATUS'].

    :param substation_file:                 Full path with file name and extension to the input substations file.
                                            If None, CERF will use the default data stored in the package.

    :type substation_file:                  str

    :returns:                               A geodataframe containing the target substations

    """

    if substation_file is None:
        return gpd.read_file(pkg_resources.resource_filename('cerf', 'data/hifld_substations_conus_albers.shp'))

    else:

        # get state abbreviations file from cerf pacakge data
        states_file = pkg_resources.resource_filename('cerf', 'data/state-abbrev_to_state-name.yml')

        # get state abbreviations to search for in HIFLD data
        with open(states_file, 'r') as yml:
            states = yaml.load(yml, Loader=yaml.FullLoader)

        gdf = gpd.read_file(substation_file)

        # keep only substations in the CONUS that are either in service or under construction
        return gdf.loc[(gdf['TYPE'] == 'SUBSTATION') &
                       (gdf['STATE'].isin(states.keys())) &
                       (gdf['STATUS'].isin(('IN SERVICE', 'UNDER CONST')))].copy()


def transmission_to_distance_raster(transmission_gdf, output_raster_file):
    """Create a Euclidean distance raster from the input GeoDataFrame that has grid cells values that are the
    distance to the nearest suitable transmission infrastructure.

    Output will be a distance raster written to file in units meters.

    :param transmission_gdf:                    GeoDataFrame of transmission infrastructure to be rasterized.
    :type transmission_gdf:                     GeoDataFrame

    :param output_raster_file:                  Full path with filename and extension to write the distance
                                                raster to.
    :type output_raster_file:                   str

    """

    # instantiate whitebox toolset
    wbt = whitebox.WhiteboxTools()

    # set field to be used as raster value
    transmission_gdf['_rval_'] = 1

    # get the template raster from CERF data
    template_raster = pkg_resources.resource_filename('cerf', 'data/cerf_conus_states_albers_1km.tif')

    with tempfile.NamedTemporaryFile(suffix='.tif') as temp:

        with rasterio.open(template_raster) as src:
            # create 0 where land array
            arr = src.read(1) * 0

            metadata = src.meta.copy()

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

        # calculate Euclidean distance file and write raster; result just stores the return value 0
        result = wbt.euclidean_distance(temp.name, output_raster_file, callback=suppress_callback)

