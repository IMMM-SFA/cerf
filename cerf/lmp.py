import numpy as np
import pandas as pd

import logging

import cerf.package_data as pkg


def generate_random_lmp_dataframe(n_zones=57, low_value=10, mid_value=300, high_value=500, n_samples=5000):
    """Generate a random dataframe of hourly 8760 LMP values per lmp zone.  Let high value LMPs only be used
    for 15 percent of the data.
    :param n_zones:                     Number of zones to process
    :param low_value:                   Desired minimum value of MWh
    :param mid_value:                   Desired mid value of MWh to split the 85-15 split to
    :param high_value:                  Desired max value of MWh
    :param n_samples:                   Number of intervals to split the min, max choices by
    :return:                            Data frame of LMPs per zone
    """

    # initialize a dictionary with the hour count for the number of hours in a year
    d = {'hour': list(range(1, 8761, 1))}

    # create an array with n_samples covering an equal space from low to mid values
    array_1 = np.linspace(low_value, mid_value, n_samples)

    # create an array with n_samples covering an equal space from mid to low values
    array_2 = np.linspace(mid_value, high_value, n_samples)

    # let only 15 percent of values come from high cost values
    threshold = 8760 - (8760 * 0.15)

    # create an LMP array for each zone
    for i in range(n_zones):

        # construct a list of random LMP values
        l = []
        for j in range(8760):

            if j < threshold:
                l.append(np.random.choice(array_1))

            else:
                l.append(np.random.choice(array_2))

        # shuffle the list
        np.random.shuffle(l)

        # assign to dict
        d[i] = l

    # convert to data frame
    return pd.DataFrame(d)


class LocationalMarginalPricing:
    """Create a 3D array of locational marginal pricing per technology by capacity factor.

    Locational Marginal Pricing (LMP) represents the cost of making and delivering electricity
    over an interconnected network of service nodes. LMPs are delivered on an hourly basis
    (8760 hours for the year) and help us to understand aspects of generation and congestion
    costs relative to the supply and demand of electricity when considering existing transmission
    infrastructure.  LMPs are a also driven by factors such as the cost of fuel which cerf also
    takes into account when calculating a power plants :ref:`Net Operating Value`.  When working
    with a scenario-driven grid operations model to evaluate the future evolution of the electricity
    system, **cerf** can ingest LMPs, return the sited generation per service area for the time
    step, and then continue this iteration through all future years to provide a harmonized view
    how the electricity system may respond to stressors in the future.

    :param lmp_zone_dict:                      A dictionary containing lmp related settings from the config file
    :type lmp_zone_dict:                       dict

    :param technology_dict:                    A dictionary containing technology related settings from the config file
    :type technology_dict:                     dict

    :param technology_order:                   A list of technologies in the order by which they should be processed
    :type lmp_zone_dict:                       list

    :param zones_arr:                          An array containing the lmp zones per grid cell
    :type lmp_zone_dict:                       dict

    """

    def __init__(self, lmp_zone_dict, technology_dict, technology_order, zones_arr):

        # dictionary containing lmp zones information
        self.lmp_zone_dict = lmp_zone_dict

        # dictionary containing technology specific information
        self.technology_dict = technology_dict

        # order of technologies to process
        self.technology_order = technology_order

        # array containing the lmp zones per grid cell
        self.zones_arr = zones_arr

    @staticmethod
    def get_cf_bin(capacity_factor_fraction):
        """Get the correct start and through index values to average over for calculating LMP."""

        if capacity_factor_fraction == 1.0:
            start_index = 0
            through_index = 8760

        elif capacity_factor_fraction >= 0.5:
            start_index = int(np.ceil(8760 * (1 - capacity_factor_fraction)))
            through_index = 8760

        elif capacity_factor_fraction == 0.0:
            msg = f"The capacity factor provided `{capacity_factor_fraction}` is outside the bounds of 0.0 through 1.0"
            raise ValueError(msg)

        else:
            start_index = 0
            through_index = int(np.ceil(8760 * capacity_factor_fraction))

        return start_index, through_index

    def get_lmp(self):
        """Create LMP array for the current technology.

        :return:                    3D numpy array of LMP where [tech_id, x, y]

        """

        # number of technologies
        n_technologies = len(self.technology_dict)

        lmp_arr = np.zeros(shape=(n_technologies, self.zones_arr.shape[0], self.zones_arr.shape[1]))

        # get the LMP file for the technology from the configuration file
        lmp_file = self.lmp_zone_dict.get('lmp_hourly_data_file', None)

        # use illustrative default if none provided
        if lmp_file is None:

            # default illustrative LMP file
            lmp_file = pkg.get_sample_lmp_file()
            logging.info(f"Using LMP from default illustrative package data:  {lmp_file}")

        else:
            logging.info(f"Using LMP file:  {lmp_file}")

        lmp_df = pd.read_csv(lmp_file)

        # drop the hour field
        lmp_df.drop('hour', axis=1, inplace=True)

        for index, i in enumerate(self.technology_order):

            # assign the correct LMP based on the capacity factor of the technology
            start_index, through_index = self.get_cf_bin(self.technology_dict[i]['capacity_factor_fraction'])

            # sort by descending lmp for each zone
            for j in lmp_df.columns:
                lmp_df[j] = lmp_df[j].sort_values(ascending=False).values

            # create a dictionary of LMP values for each power zone based on tech capacity factor
            lmp_dict = lmp_df.iloc[start_index:through_index].mean(axis=0).to_dict()
            lmp_dict = {int(k): lmp_dict[k] for k in lmp_dict.keys()}

            # add in no data
            lmp_dict[self.lmp_zone_dict['lmp_zone_raster_nodata_value']] = np.nan

            # create LMP array for the current technology
            lmp_arr[index, :, :] = np.vectorize(lmp_dict.get)(self.zones_arr)

        return lmp_arr
