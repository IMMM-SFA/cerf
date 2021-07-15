
import matplotlib.pyplot as plt

from cerf.package_data import cerf_states_shapefile, cerf_boundary_shapefile
from cerf.utils import results_to_geodataframe


def plot_siting(result_df, column='tech_name', markersize=5, cmap='Paired', save_figure=False, output_file=None):
    """Plot the results of a cerf run on a map where each technology has its own color.

    :param result_df:                       Result data frame from running 'cerf.run()'
    :type result_df:                        DataFrame

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

    # result df to geodataframe
    gdf = results_to_geodataframe(result_df)

    fig, ax = plt.subplots(figsize=(20, 10))

    # read in boundary data
    states_gdf = cerf_states_shapefile()
    boundary_gdf = cerf_boundary_shapefile()

    # add background
    boundary_gdf.plot(ax=ax, color="#f3f2f2", lw=0.8)

    # add boundaries
    states_gdf.boundary.plot(ax=ax, edgecolor='gray', lw=0.2)
    boundary_gdf.boundary.plot(ax=ax, edgecolor='gray', lw=0.8)

    # add data
    gdf.plot(ax=ax, markersize=markersize, column=column, cmap=cmap, legend=True)

    ax.set_axis_off()

    if save_figure is True and output_file is None:
        raise ValueError(f"'output_file' must be set if 'save_figure' is True.")

    if save_figure:
        plt.savefig(output_file)
