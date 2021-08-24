import geopandas as gpd
import matplotlib.pyplot as plt

from cerf.package_data import cerf_regions_shapefile, cerf_boundary_shapefile
from cerf.utils import results_to_geodataframe


def plot_siting(result_df, boundary_shp=None, regions_shp=None, column='tech_name', markersize=5, cmap='Paired',
                save_figure=False, output_file=None):
    """Plot the results of a cerf run on a map where each technology has its own color.

    :param result_df:                       Result data frame from running 'cerf.run()'
    :type result_df:                        DataFrame

    :param boundary_shp:                    Full path to a boundary shapefile with file name and extension.  If no file
                                            provided, the default boundary for the CONUS will be used.
    :type boundary_shp:                     str

    :param regions_shp:                     Full path to a regions shapefile with file name and extension.  If no file
                                            provided, the default regions for the CONUS will be used.
    :type regions_shp:                      str

    :param column:                          Column to plot
    :type column:                           str

    :param markersize:                      Size of power plant marker
    :type markersize:                       int

    :param cmap:                            Custom matplotlib colormap object or name

    :param save_figure:                     If True, figure is saved to file and 'output_file' must be set
    :type save_figure:                      bool

    :param output_file:                     If 'save_figure' is True, specify full path with file name and extension
                                            for the file to be saved to

    """

    fig, ax = plt.subplots(figsize=(20, 10))

    # read in boundary data
    if boundary_shp is None:
        boundary_gdf = cerf_boundary_shapefile()
    else:
        boundary_gdf = gpd.read_file(boundary_shp)

    if regions_shp is None:
        regions_gdf = cerf_regions_shapefile()
    else:
        regions_gdf = gpd.read_file(regions_shp)

    # result df to geodataframe
    gdf = results_to_geodataframe(result_df, regions_gdf.crs)

    # add background
    boundary_gdf.plot(ax=ax, color="#f3f2f2", lw=0.8)

    # add boundaries
    regions_gdf.boundary.plot(ax=ax, edgecolor='gray', lw=0.2)
    boundary_gdf.boundary.plot(ax=ax, edgecolor='gray', lw=0.8)

    # add data
    gdf.plot(ax=ax, markersize=markersize, column=column, cmap=cmap, legend=True)

    ax.set_axis_off()

    if save_figure is True and output_file is None:
        raise ValueError(f"'output_file' must be set if 'save_figure' is True.")

    if save_figure:
        plt.savefig(output_file)
