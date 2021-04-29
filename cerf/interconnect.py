

class Interconnection:
    """Calculate interconnection costs per grid cell in $ / yr using:

    Interconnection Cost ($ / yr) = Distance to nearest suitable transmission line (km) *
                                        Electric grid interconnection captial cost ($ / km) *
                                        Annuity factor
                                        + (if gas-fired technology) Distance to nearest suitable gas pipeline (km) *
                                        Gas interconnection captial cost ($ / km) *
                                        Annuity factor

            where, Annuity factor is (d(1 + d)**n) / ((1 + d)**n - 1)
            where, d = real annual discount rate (%), n = asset lifetime (years)


    """

    # dictionary of  size kV line needed to connect to power plant unit size in MW
    RANGES = {230: {'low_mw': 1, 'high_mw': 250},
              345: {'low_mw': 251, 'high_mw': 500},
              500: {'low_mw': 501, 'high_mw': 1250},
              765: {'low_mw': 1251, 'high_mw': None}}

    # dictionary of thousands $2010/km interconnection cost to power plant unit size in MW
    COST = {552: {'low_mw': 1, 'high_mw': 250},
            774: {'low_mw': 251, 'high_mw': 750},
            1104: {'low_mw': 751, 'high_mw': None}}

    # cost of gas pipeline in thousands $2010/km
    GAS_PIPE_COST = 677

    def __init__(self, raster_230kv_dist_km_file, 
                 raster_345kv_dist_km_file, 
                 raster_500kv_dist_km_file, 
                 raster_765kv_dist_km_file,
                 raster_gaspipe_dist_km_file
                 ):

        self.raster_230kv_dist_km_file = raster_230kv_dist_km_file
        self.raster_345kv_dist_km_file = raster_345kv_dist_km_file
        self.raster_500kv_dist_km_file = raster_500kv_dist_km_file
        self.raster_765kv_dist_km_file = raster_765kv_dist_km_file
        self.raster_gaspipe_dist_km_file = raster_gaspipe_dist_km_file

    def get_(self):

        pass
