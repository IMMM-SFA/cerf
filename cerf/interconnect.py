import gdal
import numpy as np


class Interconnection:
    """Calculate interconnection costs"""

    # value in zones raster representing no value
    NODATA_ZONE = 255

    def __init__(self, zones_raster_file, transmission_raster_file):

        zones_raster = gdal.Open(zones_raster_file)
        self.zones_array = zones_raster.GetRasterBand(1).ReadAsArray()

        # close file
        zones_raster = None

        kv_lines = gdal.Open(transmission_raster_file)
        self.transmission_array = kv_lines.GetRasterBand(1).ReadAsArray()

        # Get raster metadata
        self.dtype = kv_lines.GetRasterBand(1).DataType
        self.rows = kv_lines.RasterYSize
        self.cols = kv_lines.RasterXSize

        # close file
        kv_lines = None

    def get_bounding_box(self, target_val):
        """Get the bounding box that contains all target values in the given raster

        :param raster:             A 2d numpy array
        :param target_val:         The value to find in the array

        :return:                   Row min, max and column min and max

        """
        mask = self.zones_array == target_val
        cols = np.any(mask, axis=0)
        rows = np.any(mask, axis=1)
        cmin, cmax = np.where(cols)[0][[0, -1]]
        rmin, rmax = np.where(rows)[0][[0, -1]]

        return rmin, rmax, cmin, cmax

    def compute_distance(self, n, driver):
        """Create the proximity raster for the given power zone.

        :@param n:              The zone id
        :@param zones_raster:   A 2d numpy array indicating zone ids
        :@param kv_raster:      A 2d numpy array of zeros and ones, where ones
                                represent the target to calculate distance from
        :@param driver:         GDAL driver
        :@param dtype:          Int representing the GDAL data type of the input
                                rasters

        :return:                1D numpy array of distances per gridcell

        """
        # Do not calculate distance for the nodata zone
        if n == Interconnection.NODATA_ZONE:
            return 0

        # Get the subset of the master raster containing data for the current zone
        rmin, rmax, cmin, cmax = self.get_bounding_box(n)
        rmax += 1
        cmax += 1

        # Zero out values that are within the bounding box of the zone, but not the
        # actual zone itself
        zone_mask = self.zones_array[rmin:rmax, cmin:cmax] == n
        zone_kv_vals = self.transmission_array[rmin:rmax, cmin:cmax].copy()
        zone_kv_vals = np.logical_and(zone_kv_vals, zone_mask)

        if not np.any(zone_kv_vals):
            print("Power zone {} has no transmission infrastructure.".format(n))
            return 0

        # Create the RasterBand object that contains only values for this zone
        zone_ds = driver.Create('', int(cmax - cmin), int(rmax - rmin), 1, self.dtype)
        zone_band = zone_ds.GetRasterBand(1)
        zone_band.WriteArray(zone_kv_vals)

        # Create the RasterBand object that will have the results written to it
        dist_ds = driver.Create('', int(cmax - cmin), int(rmax - rmin), 1, self.dtype)
        dist_band = dist_ds.GetRasterBand(1)

        # gdal.ComputeProximity(zone_band, dist_band, ["MAXDIST=255", "NODATA=255"], callback = gdal.TermProgress)
        gdal.ComputeProximity(zone_band, dist_band)

        # Return just the values for the current zone
        distance_values = dist_ds.ReadAsArray()[zone_mask]

        # Close the datasets
        zone_ds = None
        dist_ds = None

        return distance_values

    def stitch_zones(self):
        """Compute distance rasters for each zone and the transmission infrastructure within them.
        Stitch the results together into one raster.

        :return:                2D distance array for each zone in the shape of the input raster

        """

        # Compute distance for each zone individually, filling in the distance raster zone by zone
        final_distances = np.zeros((self.rows, self.cols))
        driver = gdal.GetDriverByName('MEM')  # MEM means keep all in memory

        for z in np.unique(self.zones_array):
            distance_values = self.compute_distance(z, driver)
            final_distances[self.zones_array == z] = distance_values

        return final_distances

    def calculate_interconnect(self):
        """Calculate the interconnection cost associated with each the distance to transmission
        infrastructure and each technology costs."""

        # TODO
        pass