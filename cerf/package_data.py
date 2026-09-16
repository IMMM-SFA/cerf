import os
from importlib.resources import files

import yaml
import pandas as pd
import geopandas as gpd


def _package_resource_path(*parts):
    """Return a package resource path as a string.

    cerf requires its package data to live on the filesystem: the default data
    files are downloaded into the package ``data`` directory by
    ``cerf.install_package_data()`` and are consumed by ``rasterio``,
    ``geopandas``, ``open``, and ``os.listdir`` which all need real paths.
    Installs that expose the package through a non-filesystem loader (e.g., a
    zipped archive) are therefore not supported and raise an explicit error
    rather than returning an unusable path string.

    :param parts:               Path components relative to the ``cerf`` package root

    :return:                    Absolute filesystem path to the resource as a string

    """

    resource = files('cerf')
    for part in parts:
        resource = resource.joinpath(part)

    if not isinstance(resource, os.PathLike):
        raise RuntimeError(
            "cerf package data must be installed on the filesystem; "
            f"resource '{'/'.join(parts)}' resolved to a non-filesystem location ({resource!r}). "
            "Install cerf as a regular (non-zipped) package."
        )

    return os.fspath(resource)


def _data_file(filename):
    """Return a path to a file in the package data directory."""

    return _package_resource_path('data', str(filename))


def config_file(yr):
    """Return the sample configuration file for 2010.

    :param yr:                  Target four-digit year
    :type yr:                   int

    :return:                    Path to the target sample config file

    """

    return _data_file(f'config_{yr}.yml')


def cerf_regions_raster():
    """Return the cerf regions raster file."""

    return _data_file('cerf_conus_states_albers_1km.tif')


def cerf_regions_shapefile():
    """Return the cerf regions shapefile as a Geopandas data frame.  Used in output plot."""

    f = _data_file('cerf_conus_states_albers.zip')

    return gpd.read_file(f)


def cerf_boundary_shapefile():
    """Return the cerf boundary shapefile as a Geopandas data frame.  Used in output plot."""

    f = _data_file('cerf_conus_boundary_albers.zip')

    return gpd.read_file(f)


def cerf_crs():
    """Return a coordinate reference system (CRS) object of class 'pyproj.crs.crs.CRS'
     for USA_Contiguous_Albers_Equal_Area_Conic.

    """

    gdf = cerf_regions_shapefile()

    return gdf.crs


def get_default_gas_pipelines():
    """Return the full path with file name and extension to the default gas pipeline shapefile"""

    return _data_file('eia_natural_gas_pipelines_conus_albers.zip')


def get_costs_per_kv_substation_file():
    """Return the full path with file name and extension to the default costs per km of each kv substation file."""

    return _data_file('costs_per_kv_substation.yml')


def get_costs_gas_pipeline():
    """Return the full path with file name and extension to the default costs per km to gas connect to pipelines."""

    return _data_file('costs_gas_pipeline.yml')


def costs_per_kv_substation():
    """Return a dictionary of the cost of interconnection to substations of certain KV classes."""

    f = get_costs_per_kv_substation_file()

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

    f = _data_file(f'config_{yr}.yml')

    with open(f, 'r') as yml:
        return yaml.load(yml, Loader=yaml.FullLoader)


def list_available_suitability_files():
    """Return a list of available suitability files."""

    root_dir = get_data_directory()

    return [os.path.join(root_dir, i) for i in os.listdir(root_dir) if
            (i.split('_')[0] == 'suitability') and
            (os.path.splitext(i)[-1] == '.sdat')]


def sample_lmp_zones_raster_file():
    """Return path for the sample lmp zoness raster file."""

    return _data_file('lmp_zones_1km.img')


def get_sample_lmp_file():
    """Return the sample 8760 hourly locational marginal price sample file."""

    return _data_file('illustrative_lmp_8760-per-zone_dollars-per-mwh.zip')


def get_sample_lmp_data():
    """Return the sample 8760 hourly locational marginal price data as a Pandas DataFrame."""

    f = get_sample_lmp_file()

    return pd.read_csv(f)


def get_suitability_raster(default_raster):
    """Return the default suitability raster file associated with the technology being processed."""

    return _data_file(default_raster)


def get_region_abbrev_to_name_file():
    """Return the file path for region abbreviation to region name."""

    # get region abbreviations file from cerf package data
    return _data_file('region-abbrev_to_region-name.yml')


def get_region_abbrev_to_name():
    """Return a dictionary of region abbreviation to region name."""

    # get region abbreviations file from cerf package data
    regions_file = get_region_abbrev_to_name_file()

    # get region abbreviations to search for in HIFLD data
    with open(regions_file, 'r') as yml:
        return yaml.load(yml, Loader=yaml.FullLoader)


def get_region_name_to_id():
    """Return the region name to ID file path."""

    return _data_file('region-name_to_region-id.yml')


def get_data_directory():
    """Return the directory of where the cerf package data resides."""

    return _package_resource_path('data')


def get_substation_file():
    """Return the default substation file for the CONUS."""

    return _data_file('hifld_substations_conus_albers.zip')
