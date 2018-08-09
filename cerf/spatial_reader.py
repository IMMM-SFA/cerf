import gdal
import numpy as np
import os


def raster_to_array(f):
    """
    Import a single band raster to a NumPy array.

    :param f:           Full path to raster file with filename and extension

    :return:            NumPy Array
    """
    r = gdal.Open(f)
    return r.GetRasterBand(1).ReadAsArray()


def sum_rasters(in_dir, fprefix, fext):
    """
    Sum the values of matching rasters within an input directory.

    :param in_dir:      File path of directory containing rasters
    :param fprefix:     String uniquely identifying the rasters within in_dir
                        to sum
    :param fext:        Raster file extension

    :return:            NumPy Array
    """
    raster_sum = None

    for f in os.listdir(in_dir):
        if fprefix not in f or f.split('.')[-1] != fext:
            continue

        source = gdal.Open(in_dir + f)
        raster = source.GetRasterBand(1).ReadAsArray()

        if raster_sum is None:
            raster_sum = raster
        else:
            raster_sum += raster

        # close file connection
        source = None

    return raster_sum