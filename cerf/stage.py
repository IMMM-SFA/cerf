"""Stage data for CERF run.

@author Chris R. vernon
@email chris.vernon@pnnl.gov

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

import logging

import numpy as np
import rasterio

import cerf.utils as util
import cerf.package_data as pkg
from cerf.lmp import LocationalMarginalPricing
from cerf.nov import NetOperationalValue
from cerf.interconnect import Interconnection

logger = logging.getLogger(__name__)


class Stage:
    """Stage all spatial inputs (LMP, interconnection, NOV, NLC, suitability) for a CERF run.

    :param settings_dict:               Project level settings from `cerf.read_config.ReadConfig`
    :type settings_dict:                dict

    :param lmp_zone_dict:               LMP zone settings from `cerf.read_config.ReadConfig`
    :type lmp_zone_dict:                dict

    :param technology_dict:             Technology parameters keyed by technology ID
    :type technology_dict:              dict

    :param technology_order:            Technology IDs in the order used to index the 3D arrays
    :type technology_order:             list

    :param infrastructure_dict:         Infrastructure (substation / pipeline) settings
    :type infrastructure_dict:          dict

    :param initialize_site_data:        ``None``, or a CSV path / DataFrame of previously sited plants
    :type initialize_site_data:         str, pandas.DataFrame, None

    """

    def __init__(self,
                 settings_dict: dict,
                 lmp_zone_dict: dict,
                 technology_dict: dict,
                 technology_order: list,
                 infrastructure_dict: dict,
                 initialize_site_data=None):

        # dictionary containing project level settings
        self.settings_dict = settings_dict

        # dictionary containing lmp zones information
        self.lmp_zone_dict = lmp_zone_dict

        # dictionary containing technology specific information
        self.technology_dict = technology_dict

        # order of technologies to process
        self.technology_order = technology_order

        # infrastructure dictionary
        self.infrastructure_dict = infrastructure_dict

        # initialize model with existing site data
        self.initialize_site_data = initialize_site_data

        # tech_id to tech_name dictionary
        self.tech_name_dict = ({k: self.technology_dict[k].get('tech_name') for k in self.technology_dict.keys()})

        # load coordinate data
        self.cerf_regionid_raster_file = self.settings_dict.get('region_raster_file')
        self.xcoords, self.ycoords = util.raster_to_coord_arrays(self.cerf_regionid_raster_file)

        # region ID per grid cell, read once here and shared with every region instead of re-reading the raster
        #  per region; plus each region's bounding box in grid space
        self.regions_arr = self.load_regions_raster()
        self.region_bounds = util.region_bounding_boxes(self.regions_arr)

        # generate grid indices in a flat array
        self.indices_flat = np.array(np.arange(self.xcoords.flatten().shape[0]))
        self.indices_2d = self.indices_flat.reshape(self.xcoords.shape)

        # initialization data for siting
        self.init_arr, self.init_df = self.get_sited_data()

        # raster file containing the lmp zones per grid cell
        self.zones_arr = self.load_lmp_zone_raster()

        # get LMP array per tech [tech_order, x, y]
        logger.info('Processing locational marginal pricing (LMP)')
        self.lmp_arr = self.calculate_lmp()

        # get interconnection cost per tech [tech_order, x, y]
        logger.info('Calculating interconnection costs (IC)')
        self.ic_arr = self.calculate_ic()

        # get NOV array per tech [tech_order, x, y]
        logger.info('Calculating net operational cost (NOV)')
        self.generation_arr, self.operating_cost_arr, self.nov_arr = self.calculate_nov()

        # get NLC array per tech [tech_order, x, y]
        logger.info('Calculating net locational cost (NLC)')
        self.nlc_arr = self.calculate_nlc()

        # combine all suitability rasters into an array
        logger.info('Building suitability array')
        self.suitability_arr = self.build_suitability_array()

    def load_regions_raster(self):
        """Load the region ID raster for the CONUS into a 2D array."""

        with rasterio.open(self.cerf_regionid_raster_file) as src:
            return src.read(1)

    def load_lmp_zone_raster(self):
        """Load the lmp zoness raster for the CONUS into a 2D array."""

        # raster file containing the lmp zones per grid cell
        zones_raster_file = self.lmp_zone_dict.get('lmp_zone_raster_file', None)

        # use default if none passed
        if zones_raster_file is None:
            zones_raster_file = pkg.sample_lmp_zones_raster_file()

        logger.info(f"Using 'zones_raster_file':  {zones_raster_file}")

        # read in lmp zoness raster as a 2D numpy array
        with rasterio.open(zones_raster_file) as src:
            return src.read(1)

    def calculate_lmp(self):
        """Calculate Locational Marginal Pricing."""

        # create technology specific locational marginal price based on capacity factor
        pricing = LocationalMarginalPricing(self.lmp_zone_dict,
                                            self.technology_dict,
                                            self.technology_order,
                                            self.zones_arr)
        lmp_arr = pricing.get_lmp()

        # get lmp array per tech [tech_order, x, y]
        return lmp_arr

    def calculate_ic(self):
        """Calculate interconnection costs."""

        # unpack configuration and assign defaults
        substation_file = self.infrastructure_dict.get('substation_file', None)
        transmission_costs_file = self.infrastructure_dict.get('transmission_costs_file', None)
        pipeline_costs_file = self.infrastructure_dict.get('pipeline_costs_file', None)
        pipeline_file = self.infrastructure_dict.get('pipeline_file', None)
        output_rasterized_file = self.infrastructure_dict.get('output_rasterized_file', False)
        output_alloc_file = self.infrastructure_dict.get('output_alloc_file', False)
        output_cost_file = self.infrastructure_dict.get('output_cost_file', False)
        output_dist_file = self.infrastructure_dict.get('output_dist_file', False)
        interconnection_cost_file = self.infrastructure_dict.get('interconnection_cost_file', None)

        # instantiate class
        ic = Interconnection(template_array=self.lmp_arr,
                             technology_dict=self.technology_dict,
                             technology_order=self.technology_order,
                             region_raster_file=self.settings_dict.get('region_raster_file'),
                             region_abbrev_to_name_file=self.settings_dict.get('region_abbrev_to_name_file'),
                             region_name_to_id_file=self.settings_dict.get('region_name_to_id_file'),
                             substation_file=substation_file,
                             transmission_costs_file=transmission_costs_file,
                             pipeline_costs_file=pipeline_costs_file,
                             pipeline_file=pipeline_file,
                             output_rasterized_file=output_rasterized_file,
                             output_dist_file=output_dist_file,
                             output_alloc_file=output_alloc_file,
                             output_cost_file=output_cost_file,
                             interconnection_cost_file=interconnection_cost_file,
                             output_dir=self.settings_dict.get('output_directory', None))

        ic_arr = ic.generate_interconnection_costs_array()

        return ic_arr

    def calculate_nov(self):
        """Calculate Net Operational Value.

        Generation and operating cost do not vary spatially; they are per-technology scalars. They are returned as
        read-only broadcast views with the same ``[tech_order, x, y]`` shape as ``nov_arr`` so callers can index them
        like any other staged array without holding two extra full-grid copies in memory.

        """

        nov_arr = np.zeros_like(self.lmp_arr)
        generation_per_tech = np.zeros(len(self.technology_order), dtype=np.float64)
        operating_cost_per_tech = np.zeros(len(self.technology_order), dtype=np.float64)

        for index, i in enumerate(self.technology_order):
            econ = NetOperationalValue(discount_rate=self.technology_dict[i]['discount_rate'],
                                       lifetime_yrs=self.technology_dict[i]['lifetime_yrs'],
                                       unit_size_mw=self.technology_dict[i]['unit_size_mw'],
                                       capacity_factor_fraction=self.technology_dict[i]['capacity_factor_fraction'],
                                       variable_om_esc_rate_fraction=self.technology_dict[i]['variable_om_esc_rate_fraction'],
                                       fuel_price_esc_rate_fraction=self.technology_dict[i]['fuel_price_esc_rate_fraction'],
                                       carbon_tax_esc_rate_fraction=self.technology_dict[i]['carbon_tax_esc_rate_fraction'],
                                       variable_om_usd_per_mwh=self.technology_dict[i]['variable_om_usd_per_mwh'],
                                       heat_rate_btu_per_kWh=self.technology_dict[i]['heat_rate_btu_per_kWh'],
                                       fuel_price_usd_per_mmbtu=self.technology_dict[i]['fuel_price_usd_per_mmbtu'],
                                       carbon_tax_usd_per_ton=self.technology_dict[i]['carbon_tax_usd_per_ton'],
                                       carbon_capture_rate_fraction=self.technology_dict[i]['carbon_capture_rate_fraction'],
                                       fuel_co2_content_tons_per_btu=self.technology_dict[i]['fuel_co2_content_tons_per_btu'],
                                       lmp_arr=self.lmp_arr[index, :, :],
                                       target_year=self.settings_dict.get('run_year'))

            generation_tech, operating_cost_tech, nov_tech_arr = econ.calc_nov()

            nov_arr[index, :, :] = nov_tech_arr
            generation_per_tech[index] = generation_tech
            operating_cost_per_tech[index] = operating_cost_tech

        generation_arr = np.broadcast_to(generation_per_tech[:, None, None], self.lmp_arr.shape)
        operating_cost_arr = np.broadcast_to(operating_cost_per_tech[:, None, None], self.lmp_arr.shape)

        return generation_arr, operating_cost_arr, nov_arr

    def calculate_nlc(self):
        """Calculate Net Locational Costs."""

        # the most negative number will be the least expensive
        return self.ic_arr - self.nov_arr

    def get_sited_data(self):
        """If initial condition data is provided generate an array to use unsuitable where sites and their buffers
        exists.  Also return a data frame of active sites (not reaching retirement age) to include in the current years
        output.

        """

        # if initial condition data is provided, apply to all technologies
        if self.initialize_site_data is not None:

            # load siting data into a 2D array for the full grid space
            logger.info("Initializing previous siting data")
            init_arr, init_df = util.ingest_sited_data(run_year=self.settings_dict['run_year'],
                                                       x_array=self.xcoords,
                                                       siting_data=self.initialize_site_data,
                                                       template_raster_file=self.settings_dict.get('region_raster_file'))
            return init_arr, init_df

        else:
            return None, None

    @staticmethod
    def unsuitable_from_raster(arr, nodata=None):
        """Convert a suitability raster band to a boolean *unsuitable* mask.

        The suitability convention is ``0`` = suitable and ``1`` = unsuitable. Any cell holding the raster's declared
        ``nodata`` value is treated as unsuitable explicitly, so a raster whose nodata happens to be ``0`` cannot
        make missing data look suitable. Any other non-zero value is also unsuitable (logged, since it indicates a
        raster that is not 0/1 encoded).

        :param arr:                             2D raster band
        :param nodata:                          Declared nodata value of the band, or ``None``

        :return:                                Boolean array, ``True`` where the cell is unsuitable

        """

        unsuitable = arr != 0

        if nodata is not None and not (isinstance(nodata, float) and np.isnan(nodata)):
            unsuitable |= arr == nodata

        elif nodata is not None:
            unsuitable |= np.isnan(arr)

        return unsuitable

    def build_suitability_array(self):
        """Build suitability array for all technologies.

        Cells are unsuitable (``1``) where the technology raster is non-zero **or** equals its declared nodata value,
        and, when initial siting data is provided, where an existing plant or its buffer occupies the cell.

        """

        # fetch the default suitability dictionary
        default_suitability_file_dict = util.default_suitability_files()

        # set up holder for suitability array; 0 = suitable, non-zero = unsuitable, so a byte per cell is sufficient
        suitability_array = np.ones(self.nlc_arr.shape, dtype=np.uint8)

        # load tech specific rasters
        for index, i in enumerate(self.technology_order):

            # path to the input raster
            tech_suitability_raster_file = self.technology_dict[i].get('suitability_raster_file', None)

            if tech_suitability_raster_file is None:
                default_raster = default_suitability_file_dict[self.tech_name_dict[i]]
                tech_suitability_raster_file = pkg.get_suitability_raster(default_raster)

            logger.info(f"Using suitability file for '{self.technology_dict[i]['tech_name']}':  "
                        f"{tech_suitability_raster_file}")

            # load raster to array
            with rasterio.open(tech_suitability_raster_file) as src:

                if (src.height, src.width) != suitability_array.shape[1:]:
                    raise ValueError(f"Suitability raster {tech_suitability_raster_file} has shape "
                                     f"{(src.height, src.width)} but the region raster grid is "
                                     f"{suitability_array.shape[1:]}.")

                tech_arr = src.read(1)
                nodata = src.nodata

            unsuitable = self.unsuitable_from_raster(tech_arr, nodata)

            # values other than 0 / 1 / nodata indicate a raster that is not encoded as expected; they are treated
            #  as unsuitable but flagged so the user can check the input
            other = unsuitable & (tech_arr != 1)
            if nodata is not None:
                other &= tech_arr != nodata
            if other.any():
                logger.warning(f"Suitability raster {tech_suitability_raster_file} contains "
                               f"{int(other.sum())} cells with values other than 0, 1 or nodata ({nodata}); "
                               f"they are treated as unsuitable.")

            # existing plants and their buffers from previous siting data are unsuitable for every technology
            if self.initialize_site_data is not None:
                unsuitable |= self.init_arr != 0

            suitability_array[index, :, :] = unsuitable

        return suitability_array
