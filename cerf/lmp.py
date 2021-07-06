import numpy as np
import pandas as pd


class LocationalMarginalPricing:
    """Create a 3D array of locational marginal pricing per technology by capacity factor.

    LMPs ($/MWh) are provided per capacity factor quantile as represented in the `zones_xml_file`.
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

    def __init__(self, utility_dict, technology_dict, technology_order, zones_arr, utility_zone_lmp_csv):

        # dictionary containing utility zone information
        self.utility_dict = utility_dict

        # dictionary containing technology specific information
        self.technology_dict = technology_dict

        # order of technologies to process
        self.technology_order = technology_order

        # array containing the utility zone per grid cell
        self.zones_arr = zones_arr

        # data frame containing the 8760 LMPs per zone
        self.utility_zone_lmp_df = pd.read_csv(utility_zone_lmp_csv)

        # drop hours column
        self.utility_zone_lmp_df.drop(column='hours', inplace=True)

    @staticmethod
    def get_cf_bin(capacity_factor):
        """Get the correct start and through index values to average over for calculating LMP."""

        if capacity_factor == 1.0:
            start_index = 0
            through_index = 8760

        elif capacity_factor >= 0.5:
            start_index = int(np.ceil(8760 * (1 - capacity_factor)))
            through_index = 8760

        elif capacity_factor == 0.0:
            msg = f"The capacity factor provided `{capacity_factor}` is outside the bounds of 0.0 through 1.0"
            raise ValueError(msg)

        else:
            start_index = 0
            through_index = int(np.ceil(8760 * capacity_factor))

        return start_index, through_index

    def get_lmp(self):
        """Create LMP array for the current technology.

        :return:                    3D numpy array of LMP where [tech_id, x, y]

        """

        # number of technologies
        n_technologies = len(self.technology_dict)

        lmp_arr = np.zeros(shape=(n_technologies, self.zones_arr.shape[0], self.zones_arr.shape[1]))

        for index, i in enumerate(self.technology_order):

            # assign the correct LMP based on the capacity factor of the technology
            start_index, through_index = self.get_cf_bin(self.technology_dict[i]['capacity_factor'])

            # make a copy of the data frame
            df_sorted = self.utility_zone_lmp_df.copy()

            # sort by descending lmp for each zone
            for i in self.utility_zone_lmp_df.columns:
                df_sorted[i] = self.utility_zone_lmp_df[i].sort_values(ascending=False).values

            # create a dictionary of LMP values for each power zone based on tech capacity factor
            lmp_dict = df_sorted.iloc[start_index:through_index].mean(axis=0).to_dict()
            lmp_dict = {int(k): lmp_dict[k] for k in lmp_dict.keys()}

            # add in no data
            lmp_dict[self.utility_dict['utility_zone_raster_nodata_value']] = np.nan

            # create LMP array for the current technology
            lmp_arr[index] = np.vectorize(lmp_dict.get)(self.zones_arr)

        return lmp_arr
