import pkg_resources

import rasterio
import whitebox
import yaml

import numpy as np
import geopandas as gpd

from rasterio import features


def process_hifld_substations(substation_file=None):
    """Select substations from HIFLD data that are within the CONUS and either in service or under
    construction.

    This data is assumed to have the following fields:  ['TYPE', 'STATE', 'STATUS'].

    :param substation_file:                 Full path with file name and extension to the input substations file.
                                            If None, CERF will use the default data stored in the package.

    :type substation_file:                  str

    :returns:                               A geodataframe containing the target substations

    """

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




