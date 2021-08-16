import os
import pkg_resources

import yaml
import pandas as pd
import geopandas as gpd


def config_file(yr):
    """Return the sample configuration file for 2010.

    :param yr:                  Target four-digit year
    :type yr:                   int

    :return:                    Path to the target sample config file

    """

    return pkg_resources.resource_filename('cerf', f'data/config_{yr}.yml')


def cerf_states_shapefile():
    """Return the cerf CONUS states shapefile as a Geopandas data frame."""

    f = pkg_resources.resource_filename('cerf', 'data/cerf_conus_states_albers.zip')

    return gpd.read_file(f)


def cerf_boundary_shapefile():
    """Return the cerf CONUS boundary shapefile as a Geopandas data frame."""

    f = pkg_resources.resource_filename('cerf', 'data/cerf_conus_boundary_albers.zip')

    return gpd.read_file(f)


def cerf_crs():
    """Return a coordinate reference system (CRS) object of class 'pyproj.crs.crs.CRS'
     for USA_Contiguous_Albers_Equal_Area_Conic.

     """

    gdf = cerf_states_shapefile()

    return gdf.crs


def costs_per_kv_substation():
    """Return a dictionary of the cost of interconnection to substations of certain KV classes."""

    f = pkg_resources.resource_filename('cerf', 'data/costs_per_kv_substation.yml')

    with open(f, 'r') as yml:
        return yaml.load(yml, Loader=yaml.FullLoader)


def load_sample_config(yr):
    """Read the config YAML file for illustrative purposes.

    :param yr:                  Target configuration year in YYYY format.
    :type yr:                   int

    :return:                    dictionary for the configuration

    """

    available_years = list(range(2010, 2055, 5))

    if yr not in available_years:
        raise KeyError(f"Year '{yr}' not available as a default configuration file.  Must be in {available_years}")

    f = pkg_resources.resource_filename('cerf', f'data/config_{yr}.yml')

    with open(f, 'r') as yml:
        return yaml.load(yml, Loader=yaml.FullLoader)


def list_available_suitability_files():
    """Return a list of available suitability files."""

    root_dir = pkg_resources.resource_filename('cerf', 'data')

    return [os.path.join(root_dir, i) for i in os.listdir(root_dir) if
            (i.split('_')[0] == 'suitability') and
            (os.path.splitext(i)[-1] == '.sdat')]


def sample_lmp_zones_raster_file():
    """Return path for the sample lmp zoness raster file."""

    return pkg_resources.resource_filename('cerf', 'data/lmp_zones_1km.img')


def get_sample_lmp_data():
    """Return the sample 8760 hourly locational marginal price data as a Pandas DataFrame."""

    f = pkg_resources.resource_filename('cerf', 'data/illustrative_lmp_8760-per-zone_dollars-per-mwh.zip')

    return pd.read_csv(f)


def get_state_abbrev_to_name():
    """Return a dictionary of state abbreviation to state name."""

    # get state abbreviations file from cerf package data
    states_file = pkg_resources.resource_filename('cerf', 'data/state-abbrev_to_state-name.yml')

    # get state abbreviations to search for in HIFLD data
    with open(states_file, 'r') as yml:
        return yaml.load(yml, Loader=yaml.FullLoader)


def get_data_directory():
    """Return the directory of where the cerf package data resides."""

    return pkg_resources.resource_filename('cerf', 'data')
