import numpy as np
import rasterio


class LocationalMarginalPricing:
    """Create a 3D array of locational marginal pricing per technology by capacity factor.

    LMPs are provided per capacity factor quantile as represented in the `zones_xml_file`.
    Each technologies capacity factor is matched to the corresponding LMP per utility zone
    and is thus used to create a 2D array that establishes the appropriate LMP per grid cell
    per technology.

    :param config:                      A configuration dictionary.
    :type config:                       dict

    USAGE:

    # instantiate the LMP class and create a 3D numpy array with the shape (techid, x, y)
    #   containing LMP values per 1km grid cell
    pricing = Lmp(config)

    # access the LMP array by
    pricing.lmp_arr

    """

    # type hints
    utility_dict: dict
    technology_dict: dict
    technology_order: list

    def __init__(self, utility_dict, technology_dict, technology_order):

        # dictionary containing utility zone information
        self.utility_dict = utility_dict

        # dictionary containing technology specific information
        self.technology_dict = technology_dict

        # order of technologies to process
        self.technology_order = technology_order

        # raster file containing the utility zone per grid cell
        zones_raster_file = self.utility_dict.get('utility_zone_raster_file')

        # read in utility zones raster as a 2D numpy array
        with rasterio.open(zones_raster_file) as src:
            self.zones_arr = src.read(1)

    @staticmethod
    def bin_cf(capacity_factor):
        """Bin capacity factor for use in deriving the appropriate locational marginal price."""

        if capacity_factor >= 0.9:
            cf = 0.9

        elif (capacity_factor < 0.9) and (capacity_factor >= 0.8):
            cf = 0.8

        elif (capacity_factor < 0.8) and (capacity_factor >= 0.5):
            cf = 0.5

        elif (capacity_factor < 0.5) and (capacity_factor >= 0.3):
            cf = 0.3

        elif capacity_factor < 0.3:
            cf = 0.1

        else:
            cf = 0.0
            msg = f"The capacity factor provided `{capacity_factor}` is outside the bounds of 0.0 through 1.0"
            raise ValueError(msg)

        return cf

    def get_lmp(self):
        """Create LMP array for the current technology.

        :return:                    3D numpy array of LMP where [tech_id, x, y]

        """

        # number of technologies
        n_technologies = len(self.technology_dict)

        lmp_arr = np.zeros(shape=(n_technologies, self.zones_arr.shape[0], self.zones_arr.shape[1]))

        for index, i in enumerate(self.technology_order):

            # assign the correct LMP based on the capacity factor of the technology
            cf_lmp = self.bin_cf(self.technology_dict[i]['capacity_factor'])

            # create a dictionary of LMP values for each power zone based on tech capacity factor
            lmp_dict = {k: self.utility_dict['zone_id'][k]['lmp_by_capacity_factor'][cf_lmp] for k in self.utility_dict['zone_id'].keys()}

            # add in no data
            lmp_dict[self.utility_dict['utility_zone_raster_nodata_value']] = np.nan

            # create LMP array for the current technology
            lmp_arr[index] = np.vectorize(lmp_dict.get)(self.zones_arr)

        return lmp_arr
