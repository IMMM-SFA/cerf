import os
import pickle
import pkg_resources

import yaml


def config_file(yr):
    """Return the sample configuration file for 2010.

    :param yr:                  Target four-digit year
    :type yr:                   int

    :return:                    Path to the target sample config file

    """

    return pkg_resources.resource_filename('cerf', f'data/config_{yr}.yml')


def cerf_crs():
    """Return the CRS object of type 'rasterio.crs.CRS' for USA_Contiguous_Albers_Equal_Area_Conic."""

    f = pkg_resources.resource_filename('cerf', 'data/crs_usa_contiguous_albers_equal_area_conic.p')

    return pickle.load(open(f, 'rb'))


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
