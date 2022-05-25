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


class Stage:

    # type hints
    settings_dict: dict
    lmp_zone_dict: dict
    technology_dict: dict
    technology_order: list

    def __init__(self, settings_dict, lmp_zone_dict, technology_dict, technology_order, infrastructure_dict,
                 initialize_site_data):

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

        # generate grid indices in a flat array
        self.indices_flat = np.array(np.arange(self.xcoords.flatten().shape[0]))
        self.indices_2d = self.indices_flat.reshape(self.xcoords.shape)

        # initialization data for siting
        self.init_arr, self.init_df = self.get_sited_data()

        # raster file containing the lmp zones per grid cell
        self.zones_arr = self.load_lmp_zone_raster()

        # get LMP array per tech [tech_order, x, y]
        logging.info('Processing locational marginal pricing (LMP)')
        self.lmp_arr = self.calculate_lmp()

        # get interconnection cost per tech [tech_order, x, y]
        logging.info('Calculating interconnection costs (IC)')
        self.ic_arr = self.calculate_ic()

        # get NOV array per tech [tech_order, x, y]
        logging.info('Calculating net operational cost (NOV)')
        self.generation_arr, self.operating_cost_arr, self.nov_arr = self.calculate_nov()

        # get NLC array per tech [tech_order, x, y]
        logging.info('Calculating net locational cost (NLC)')
        self.nlc_arr = self.calculate_nlc()

        # combine all suitability rasters into an array
        logging.info('Building suitability array')
        self.suitability_arr = self.build_suitability_array()

    def load_lmp_zone_raster(self):
        """Load the lmp zoness raster for the CONUS into a 2D array."""

        # raster file containing the lmp zones per grid cell
        zones_raster_file = self.lmp_zone_dict.get('lmp_zone_raster_file', None)

        # use default if none passed
        if zones_raster_file is None:
            zones_raster_file = pkg.sample_lmp_zones_raster_file()

        logging.info(f"Using 'zones_raster_file':  {zones_raster_file}")

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
        """Calculate Net Operational Value."""

        nov_arr = np.zeros_like(self.lmp_arr)
        generation_arr = np.zeros_like(self.lmp_arr)
        operating_cost_arr = np.zeros_like(self.lmp_arr)

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

            generation_tech_arr, operating_cost_tech_arr, nov_tech_arr = econ.calc_nov()

            nov_arr[index, :, :] = nov_tech_arr
            generation_arr[index, :, :] = generation_tech_arr
            operating_cost_arr[index, :, :] = operating_cost_tech_arr

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
            logging.info("Initializing previous siting data")
            init_arr, init_df = util.ingest_sited_data(run_year=self.settings_dict['run_year'],
                                                       x_array=self.xcoords,
                                                       siting_data=self.initialize_site_data)

            return init_arr, init_df

        else:
            return None, None

    def build_suitability_array(self):
        """Build suitability array for all technologies."""

        # fetch the default suitability dictionary
        default_suitability_file_dict = util.default_suitabiity_files()

        # set up holder for suitability array
        suitability_array = np.ones_like(self.nlc_arr)

        # load tech specific rasters
        for index, i in enumerate(self.technology_order):

            # path to the input raster
            tech_suitability_raster_file = self.technology_dict[i].get('suitability_raster_file', None)

            if tech_suitability_raster_file is None:
                default_raster = default_suitability_file_dict[self.tech_name_dict[i]]
                tech_suitability_raster_file = pkg.get_suitability_raster(default_raster)

            logging.info(f"Using suitability file for '{self.technology_dict[i]['tech_name']}':  {tech_suitability_raster_file}")

            # load raster to array
            with rasterio.open(tech_suitability_raster_file) as src:

                # read to 2D array
                tech_arr = src.read(1)

                if self.initialize_site_data is not None:
                    tech_arr = np.maximum(tech_arr, self.init_arr)

                # add to suitability array avoid overwriting the default dimension
                suitability_array[index, :, :] = tech_arr

        return suitability_array
