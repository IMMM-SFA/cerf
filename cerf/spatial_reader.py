import gdal
import os


def raster_to_array(f):
    """Import a single band raster to a NumPy array.

    :param f:           Full path to raster file with filename and extension

    :return:            NumPy Array

    """
    r = gdal.Open(f)
    return r.GetRasterBand(1).ReadAsArray()


def sum_rasters(in_dir, fprefix, fext):
    """Sum the values of matching rasters within an input directory.

    :param in_dir:      File path of directory containing rasters
    :param fprefix:     String uniquely identifying the rasters within in_dir
                        to sum
    :param fext:        Raster file extension with leading dot

    :return:            NumPy 2D Array

    """
    raster_sum = None

    for f in os.listdir(in_dir):

        # get file prefix
        len_prefix = len(fprefix)
        file_prefix = f[0:len_prefix]

        file_ext = os.path.splitext(f)[-1]

        # get raster matching prefix and file extension
        if (fprefix == file_prefix) and (fext == file_ext):

            file_path = os.path.join(in_dir, f)

            source = gdal.Open(file_path)
            raster = source.GetRasterBand(1).ReadAsArray()

            if raster_sum is None:
                raster_sum = raster

            else:
                try:
                    raster_sum += raster

                except TypeError:
                    print("CORRUPT FILE:  {}".format(file_path))
                    raise

            # close file connection
            source = None

        else:
            continue

    return raster_sum
