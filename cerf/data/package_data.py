import pickle
import pkg_resources


def config_file(yr):
    """Return the sample configuration file for 2010.

    :param yr:                  Target four-digit year
    :type yr:                   int

    :return:                    Path to the target sample config file

    """

    return pkg_resources.resource_filename('cerf', f'tests/data/config_{yr}.yml')


def cerf_crs():
    """Return the CRS object of type 'rasterio.crs.CRS' for USA_Contiguous_Albers_Equal_Area_Conic."""

    f = pkg_resources.resource_filename('cerf', 'data/crs_usa_contiguous_albers_equal_area_conic.p')

    return pickle.load(open(f, 'rb'))
