import numpy as np

from cerf.spatial_reader import raster_to_array


class Lmp:
    """Create a 3D array of locational marginal pricing per technology by capacity factor.
    LMPs are provided per capacity factor quantile as represented in the `zones_xml_file`.
    Each technologies capacity factor is matched to the corresponding LMP per utility zone
    and is thus used to create a 2D array that establishes the appropriate LMP per grid cell
    per technology.

    :param zones_raster_file:           Full path with file name and extension to the power zones raster file
                                        that delineates each utility zone per 1km grid cell

    :param zones_xml_file:              Full path with file name and extension to the power zones XML file
                                        containing the LMP values by capacity factor per utility zone

    :param technology_dict:             A dictionary containing technology specific data per technology id key
                                        as harvested from the technologies.xml file


    USAGE:

    # instantiate the LMP class
    lmp = Lmp(zones_raster_file, zones_xml_file, technology_dict)

    # create a 3D numpy array with the shape (techid, x, y) containing LMP values per 1km grid cell
    lmp_arr = lmp.get_lmp_arr()

    """
    # value in zones raster representing no value
    NODATA_ZONE = 255

    def __init__(self, zones_raster_file, zones_xml_file, technology_dict):

        # read in utility zones raster
        self.zones_arr = raster_to_array(zones_raster_file)

        # utility zone xml
        self.zones_xml = zones_xml_file

        self.tech_dict = technology_dict

    def tech_lmp(self, cf_lmp):
        """Get a dictionary of LMPs by zone and capacity factor value {zone: cf_value}"""

        d = {}
        with open(self.zones_xml) as get:

            for line in get:

                if '<shapeid>' in line:
                    zn = int(line.strip().split('<shapeid>')[1].split('<')[0])

                if '<cf value="{}">'.format(cf_lmp) in line:
                    cf_val = float(line.strip().split('<cf value="{}">'.format(cf_lmp))[1].split('<')[0])

                    d[zn] = cf_val

        # add in key for nodata
        d[Lmp.NODATA_ZONE] = np.nan

        return d

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

        return cf

    def get_lmp_arr(self):
        """Create LMP array for the current technology

        """
        lmp_arr = np.zeros(shape=(len(self.tech_dict), self.zones_arr.shape[0], self.zones_arr.shape[1]))

        for index, tech in enumerate(self.tech_dict.keys()):
            cf_lmp = self.bin_cf(self.tech_dict[tech]['capacity_factor'])

            # create a dictionary of LMP values for each power zone based on tech capacity factor
            lmp_dict = self.tech_lmp(cf_lmp)

            # create LMP array for the current technology
            lmp_arr[index] = np.vectorize(lmp_dict.get)(self.zones_arr)

        return lmp_arr
