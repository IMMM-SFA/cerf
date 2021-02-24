import os
import json
import time

import numpy as np
import numpy.ma as ma

import pandas as pd
import geopandas as gpd

import fiona

import rasterio
from rasterio.mask import mask


from cerf.nov import NetOperationalValue
from cerf.lmp import LocationalMarginalPricing
from cerf.utils import buffer_flat_array


def read_techs(tech_file, scenario, yr, tech_group):
    df = pd.read_csv(tech_file, usecols=['Scenario', 'Year', 'Region-Origin', 'Variable', 'Value'])

    # select the scenario
    df = df.loc[df['Scenario'] == scenario]

    # select the year
    df = df.loc[df['Year'] == yr]

    df['metric'] = df['Variable'].apply(lambda x: x.split('|')[0])
    df['tech'] = df['Variable'].apply(lambda x: '_'.join(x.split('|')[1:]).replace(' ', ''))
    df.drop(['Scenario', 'Variable'], axis=1, inplace=True)

    df['tech'] = df['tech'].map(tech_group)
    df = df.loc[df['tech'] != 'None']

    df = df.loc[~df['metric'].isin(['Full Name', 'Category', 'Variable OM (2005)'])]

    df['Value'] = df['Value'].astype(np.float)

    grp = df.groupby(['tech', 'metric', 'Year']).mean()

    grp.reset_index(inplace=True)

    grp['Value'] = np.where((grp['metric'] == 'Lifetime') & (grp['Value'].isnull()), 60, grp['Value'])

    grp['Value'].fillna(value=0, inplace=True)

    return grp






class Competition:
    """
    Technology competition algorithm for CERF.

    Grid cell level net locational cost (NLC) per technology and an
    energy technology capacity expansion plan is used to compete
    technologies against each other to see which will win the grid
    cell. The technology that wins the grid cell is then sited until
    no further winning cells exist. Once sited, the location of the
    winning technology's grid cell is no longer available for siting.
    The competition array is recalculated after all technologies have
    passed through an iteration. This process is completed until there
    are either no cells left to site in or there are no more sites left
    to site for any technology.

    :param expansion_plan:      Dictionary of {tech_id: number_of_sites, ...}

    :param nlc_mask:

    """

    def __init__(self, expansion_plan, nlc_mask, buffer_in_cells=5, verbose=False):

        self.verbose = verbose
        self.expansion_plan = expansion_plan
        self.nlc_mask = nlc_mask
        self.nlc_mask_shape = self.nlc_mask.shape

        self.buffer_in_cells = buffer_in_cells

        # number of technologies
        self.n_techs = len(expansion_plan)

        # show cheapest option, add 1 to the index to represent the technology number
        self.cheapest_arr = np.argmin(self.nlc_mask, axis=0)

        # flatten cheapest array to be able to use random
        self.cheapest_arr_1d = self.cheapest_arr.flatten()

        # prep array to hold outputs
        self.sited_arr_1d = np.zeros_like(self.cheapest_arr_1d)

        # set initial value to for available grid cells
        self.avail_grids = 1

    def compete(self):

        while self.avail_grids > 0:

            # evaluate by technology
            for tech_id in self.expansion_plan.keys():

                # get the indices of the target tech ids where the target tech is the cheapest option
                tech = np.where(self.cheapest_arr_1d == tech_id)[0]

                # if there are more power plants to site and there are grids available to site them...
                if self.avail_grids > 0 and tech.shape[0] > 0:

                    if self.verbose:
                        print('\nNumber of sites desired for tech_id {}:  {}'.format(tech_id,
                                                                                     self.expansion_plan[tech_id]))

                    # the number of sites for the target tech
                    required_sites = self.expansion_plan[tech_id]

                    # site with buffer and exclude buffered area from further siting
                    still_siting = True
                    sited_list = []
                    while still_siting:

                        # select a random index that has a winning cell for the check
                        target_ix = np.random.choice(tech)

                        # add selected index to list
                        sited_list.append(target_ix)

                        # apply buffer
                        result = buffer_flat_array(target_index=target_ix,
                                                   arr=self.cheapest_arr_1d,
                                                   nrows=self.cheapest_arr.shape[0],
                                                   ncols=self.cheapest_arr.shape[1],
                                                   ncells=self.buffer_in_cells,
                                                   set_value=0)

                        # unpack values
                        self.cheapest_arr_1d, buffer_indices_list = result

                        # update the number of sites left to site
                        required_sites -= 1

                        # remove any buffered elements as an option to site
                        tech_indices_to_delete = [np.where(tech == i)[0][0] for i in buffer_indices_list if i in tech]
                        tech = np.delete(tech, tech_indices_to_delete)

                        # exit siting for the target technology if all sites have been sited or if there are no more
                        #   winning cells
                        if required_sites == 0 or tech.shape[0] == 0:
                            still_siting = False

                    rdx = np.array(sited_list)

                    # add sited techs to output array
                    self.sited_arr_1d[rdx] = tech_id

                    # update dictionary with how many plants are left to site
                    self.expansion_plan[tech_id] = self.expansion_plan[tech_id] - rdx.shape[0]

                    if self.verbose:
                        print('\nUpdate expansion plan to represent siting requirements:')
                        print(self.expansion_plan)

                    # update original array with excluded area where siting occurred

                    # if target technology has no more sites to be sited
                    if self.expansion_plan[tech_id] == 0:

                        # make all elements for the target tech in the NLC mask unsuitable so we can progress
                        self.nlc_mask[tech_id, :, :] = np.ma.masked_array(self.nlc_mask[0, :, :],
                                                                          np.ones_like(self.nlc_mask[0, :, :]))

                    # apply the new exclusion from the current technology to all techs...
                    #   invert sited elements to have a value of 1 so they can be used as a mask
                    #   repeat the new sited array to create a mask for all techs and reshape to 2D
                    #   update all technologies with the new mask
                    self.nlc_mask[1:, :, :] = np.ma.masked_array(self.nlc_mask[1:, :, :],
                                                                 np.tile(np.where(self.cheapest_arr_1d == 0, 1, 0),
                                                                         self.nlc_mask_shape[0] - 1).reshape(
                                                                     (self.nlc_mask_shape[0] - 1,
                                                                      self.nlc_mask_shape[1],
                                                                      self.nlc_mask_shape[2])))

                    # show cheapest option, add 1 to the index to represent the technology number
                    self.cheapest_arr = np.argmin(self.nlc_mask, axis=0)

                    # flatten cheapest array to be able to use random
                    self.cheapest_arr_1d = self.cheapest_arr.flatten()

                    # check for any available grids to site in
                    self.avail_grids = np.where(self.cheapest_arr_1d > 0)[0].shape[0]

                    if self.verbose:
                        print(f'\nAvailable grid cells:  {self.avail_grids}')

        # reshape output array to 2D
        return self.sited_arr_1d.reshape(self.cheapest_arr.shape)


def workflow():

    root_dir = '/Users/d3y010/projects/cerf/data'

    spatial_data_dir = os.path.join(root_dir, 'spatial')
    xml_data_dir = os.path.join(root_dir, 'xml')

    scenario = 'GCAMUSA_Reference'

    yr = 2010

    # constants
    discount_rate = 0.05
    carbon_esc_rate = 0.0
    carbon_tax = 0

    # data paths
    zone_rast = os.path.join(root_dir, 'gis', 'rast', 'cerf_powerzones.img')
    zone_xml = os.path.join(root_dir, 'xml', 'powerzones.xml')
    dist_rast = os.path.join(root_dir, 'gis', 'rast', 'platts_substations_500kv_up_distance.img')
    common_rast = os.path.join(root_dir, 'gis', 'rast', 'suitability_common.img')
    tech_file = '/Users/d3y010/projects/cerf/runs/GCAM_CERF_reporting_2019.04.11/GCAM_CERF_tech_assumptions_Ref.csv'
    exp_file = '/Users/d3y010/projects/cerf/runs/GCAM_CERF_reporting_2019.04.11/gcam_reference/inputs/xml/expansionplan_{}.csv'.format(
        yr)
    state_raster_file = os.path.join(root_dir, 'gis', 'rast', 'promod_20121028_conus.img')
    states_file = '/Users/d3y010/projects/cerf/data/example/inputs/spatial/Promod_20121028_fips.shp'
    raster_dir = '/Users/d3y010/projects/cerf/data/example/inputs/spatial'

    # group GCAM technology into CERF technology
    tech_group = {'Biomass_Conv_wCCS': 'biomass_conv',
                  'Biomass_Conv_woCCS': 'biomass_conv',
                  'Biomass_IGCC_wCCS': 'biomass_igcc_with_ccs',
                  'Biomass_IGCC_woCCS': 'biomass_igcc_wo_ccs',
                  'Coal_ConvPul_wCCS': 'coal_conv',
                  'Coal_ConvPul_woCCS': 'coal_conv',
                  'Coal_IGCC_wCCS': 'coal_igcc_with_ccs',
                  'Coal_IGCC_woCCS': 'coal_igcc_wo_ccs',
                  'Gas_CC_wCCS': 'gas_cc',
                  'Gas_CC_woCCS': 'gas_cc',
                  'Gas_CT_woCCS': 'gas_turbine',
                  'Geothermal': 'None',
                  'Hydro': 'None',
                  'Nuclear_GenII': 'nuclear',
                  'Nuclear_GenIII': 'nuclear',
                  'Oil_CT_woCCS': 'oil_turbine',
                  'Solar_CSP': 'solar',
                  'Solar_PV_NonDist': 'solar',
                  'Wind_Onshore': 'wind'}

    # example technology info
    static = {'biomass_conv': {'unit_size': 80, 'ic': 552, 'var_cost_esc': -0.00398993418629034},
              'biomass_igcc_with_ccs': {'unit_size': 380, 'ic': 774, 'var_cost_esc': -0.00564811220001504},
              'biomass_igcc_wo_ccs': {'unit_size': 400, 'ic': 774, 'var_cost_esc': -0.00443288530388608},
              'coal_conv': {'unit_size': 600, 'ic': 774, 'var_cost_esc': -0.00398993418629034},
              'coal_igcc_with_ccs': {'unit_size': 380, 'ic': 774, 'var_cost_esc': -0.00583677050505782},
              'coal_igcc_wo_ccs': {'unit_size': 550, 'ic': 774, 'var_cost_esc': -0.00443288530388608},
              'gas_cc': {'unit_size': 400, 'ic': 774, 'var_cost_esc': -0.00458144958070683},
              'gas_turbine': {'unit_size': 400, 'ic': 774, 'var_cost_esc': -0.00398993418629034},
              'nuclear': {'unit_size': 1350, 'ic': 1104, 'var_cost_esc': -0.00104311614063357},
              'oil_turbine': {'unit_size': 400, 'ic': 774, 'var_cost_esc': -0.00398993418629034},
              'solar': {'unit_size': 80, 'ic': 552, 'var_cost_esc': -0.00249607760279447},
              'wind': {'unit_size': 251, 'ic': 774, 'var_cost_esc': -0.00249607760279447}}

    # process technologies
    tech_info = read_techs(tech_file, scenario, yr, tech_group)
    tech_list = tech_info['tech'].unique()

    # technology to tech ids
    tech_id = {'biomass_conv': '9',
               'biomass_igcc_with_ccs': '15',
               'biomass_igcc_wo_ccs': '10',
               'coal_conv': '1',
               'coal_igcc_with_ccs': '12',
               'coal_igcc_wo_ccs': '2',
               'gas_cc': '5',
               'gas_turbine': '3',
               'nuclear': '11',
               # 'oil_cc' : '8',
               'oil_turbine': '6',
               'solar': '16',
               'wind': '17'}

    # mapping to raster name
    tech_to_raster_dict = {'biomass_conv': 'suitability_biomass.sdat',
                           'biomass_igcc_with_ccs': 'suitability_biomass_igcc_ccs.sdat',
                           'biomass_igcc_wo_ccs': 'suitability_biomass_igcc.sdat',
                           'coal_conv': 'suitability_coal.sdat',
                           'coal_igcc_with_ccs': 'suitability_coal_igcc_ccs.sdat',
                           'coal_igcc_wo_ccs': 'suitability_coal_igcc.sdat',
                           'gas_cc': 'suitability_gas_cc.sdat',
                           'gas_turbine': 'suitability_gas_baseload.sdat',
                           'nuclear': 'suitability_nuclear.sdat',
                           'oil_turbine': 'suitability_oil_peak.sdat',
                           'solar': 'suitability_solar.sdat',
                           'wind': 'suitability_wind.sdat'}

    # ----------------------------------------------------------
    # process technology information
    # ----------------------------------------------------------

    tech_dict = {}

    for tech in tech_id.keys():
        # load technology specific info for the target technology
        lifetime = tech_info.loc[(tech_info['metric'] == 'Lifetime') & (tech_info['tech'] == tech)]['Value'].values[0]
        capacity_factor = \
        tech_info.loc[(tech_info['metric'] == 'Capacity Factor') & (tech_info['tech'] == tech)]['Value'].values[0]
        variable_cost_esc_rate = static[tech]['var_cost_esc']
        fuel_esc_rate = \
        tech_info.loc[(tech_info['metric'] == 'Fuel Price Escalation') & (tech_info['tech'] == tech)]['Value'].values[0]
        unit_size = static[tech]['unit_size']
        interconnection_cost_per_km = static[tech]['ic']
        variable_om = \
        tech_info.loc[(tech_info['metric'] == 'Variable OM') & (tech_info['tech'] == tech)]['Value'].values[0]
        heat_rate = tech_info.loc[(tech_info['metric'] == 'Heat Rate') & (tech_info['tech'] == tech)]['Value'].values[0]
        fuel_price = tech_info.loc[(tech_info['metric'] == 'Fuel Price') & (tech_info['tech'] == tech)]['Value'].values[0]
        carbon_capture_rate = \
        tech_info.loc[(tech_info['metric'] == 'Carbon Capture Rate') & (tech_info['tech'] == tech)]['Value'].values[0]
        fuel_co2_content = \
        tech_info.loc[(tech_info['metric'] == 'Fuel CO2 Content') & (tech_info['tech'] == tech)]['Value'].values[0]

        # load tech dict
        tech_dict[tech] = {'lifetime': lifetime,
                           'capacity_factor': capacity_factor,
                           'variable_cost_esc_rate': variable_cost_esc_rate,
                           'fuel_esc_rate': fuel_esc_rate,
                           'unit_size': unit_size,
                           'interconnection_cost_per_km': interconnection_cost_per_km,
                           'variable_om': variable_om,
                           'heat_rate': heat_rate,
                           'fuel_price': fuel_price,
                           'carbon_capture_rate': carbon_capture_rate,
                           'fuel_co2_content': fuel_co2_content}

    # ----------------------------------------------------------
    # process LMPs
    # ----------------------------------------------------------

    pricing = LocationalMarginalPricing(zone_rast, zone_xml, tech_dict)
    lmp_arx = pricing.lmp_arr
    lmp_order = pricing.tech_order

    for ix, tech in enumerate(lmp_order):

        tech_dict[tech]['lmp_arr'] = lmp_arx[ix, :, :].copy()

    # ----------------------------------------------------------
    # calculate NOV
    # ----------------------------------------------------------

    for tech in tech_id.keys():

        econ = NetOperationalValue(discount_rate=0.05,
                                   lifetime=tech_dict[tech]['lifetime'],
                                   unit_size=tech_dict[tech]['unit_size'],
                                   capacity_factor=tech_dict[tech]['capacity_factor'],
                                   variable_cost_esc_rate=tech_dict[tech]['variable_cost_esc_rate'],
                                   fuel_esc_rate=tech_dict[tech]['fuel_esc_rate'],
                                   carbon_esc_rate=0.0,
                                   variable_om=tech_dict[tech]['variable_om'],
                                   heat_rate=tech_dict[tech]['heat_rate'],
                                   fuel_price=tech_dict[tech]['fuel_price'],
                                   carbon_tax=0,
                                   carbon_capture_rate=tech_dict[tech]['carbon_capture_rate'],
                                   fuel_co2_content=tech_dict[tech]['fuel_co2_content'],
                                   lmp_arr=tech_dict[tech]['lmp_arr'],
                                   target_year=yr)

        tech_dict[tech]['nov'] = econ.nov

    # ----------------------------------------------------------
    # calculate IC costs
    # ----------------------------------------------------------

    # load substations file for 500 KV and up showing distance from every grid cell to a substation
    substation_file = os.path.join(root_dir, 'gis', 'rast', 'platts_substations_500kv_up_distance.img')

    # load to array
    with rasterio.open(substation_file) as src:
        ic_dist_km_arr = src.read(1) / 1000  # convert meters to km

    for tech in tech_id.keys():
        # calculate interconnection costs per grid cell
        tech_dict[tech]['ic'] = ic_dist_km_arr * tech_dict[tech]['interconnection_cost_per_km']

    # ----------------------------------------------------------
    # calculate NLC and apply suitability
    # ----------------------------------------------------------

    # the most negative number will be the least expensive
    for tech in tech_id.keys():
        tech_dict[tech]['nlc'] = tech_dict[tech]['ic'] - tech_dict[tech]['nov']

    # apply state nan to nlc copy
    tech_order = []
    nlc_arr = np.zeros(shape=(len(tech_id), 2999, 4693))

    for ix, tech in enumerate(tech_id.keys()):

        tech_order.append(tech)

        # add NLC per tech to 3D array
        nlc_arr[ix] = tech_dict[tech]['nlc'].copy()

    # insert zero array and mask it as index [0, :, :] so the tech_id 0 will always be min if nothing is left to site
    nlc_arr = np.insert(nlc_arr, 0, np.zeros_like(nlc_arr[0, :, :]), axis=0)
    nlc_arr = np.nan_to_num(nlc_arr, nan=np.max(nlc_arr) + 1)

    # # set up holder for suitability array
    # suitability_array = np.ones_like(nlc_arr)
    #
    # # load tech specific rasters
    # for ix, tech_name in enumerate(tech_order):
    #
    #     # path to the input raster
    #     raster_file = os.path.join(raster_dir, tech_to_raster_dict[tech_name])
    #
    #     # load raster to array
    #     with rasterio.open(raster_file) as src:
    #
    #         # store metadata specs for the first raster
    #         if ix == 0:
    #             metadata = src.meta.copy()
    #
    #         # read to 2D array
    #         tech_arr = src.read(1)
    #
    #         # add to suitability array avoid overwriting the default dimension
    #         suitability_array[ix, :, :] = tech_arr
    #
    # # load the state raster as array
    # with rasterio.open(state_raster_file) as src:
    #     int_meta = src.meta.copy()
    #     states_arr = src.read(1)

    return tech_order, raster_dir, tech_to_raster_dict, state_raster_file, nlc_arr, tech_dict


if __name__ == '__main__':

    # ----------------------------------------------------------
    # state specific
    # ----------------------------------------------------------

    state_id_list = [45, 31]

    expansion_plan = {1: 10, 2: 10, 3: 10, 4: 10, 5: 10,
                      6: 10, 7: 10, 8: 10, 9: 10, 10: 10,
                      11: 10, 12: 10}

    # prepare data
    tech_order, raster_dir, tech_to_raster_dict, state_raster_file, nlc_arr, tech_dict = workflow()

    for state_id in state_id_list:
        print(f"Processing:  {state_id}")

        # set up holder for suitability array
        suitability_array = np.ones_like(nlc_arr)

        # load tech specific rasters
        for ix, tech_name in enumerate(tech_order):

            # path to the input raster
            raster_file = os.path.join(raster_dir, tech_to_raster_dict[tech_name])

            # load raster to array
            with rasterio.open(raster_file) as src:

                # store metadata specs for the first raster
                if ix == 0:
                    metadata = src.meta.copy()

                # read to 2D array
                tech_arr = src.read(1)

                # add to suitability array avoid overwriting the default dimension
                suitability_array[ix, :, :] = tech_arr

        # load the state raster as array
        with rasterio.open(state_raster_file) as src:
            int_meta = src.meta.copy()
            states_arr = src.read(1)


        # extract Virginia and make all else unsuitable
        state_suit_mask = np.where(states_arr == state_id, 0, 1)

        # add in suitability where unsuitable is the highest value of NLC
        suitability_array_state = suitability_array.copy() + state_suit_mask

        # at this point, we have all suitable grid cells as 0 and all not as 1
        suitability_array_state = np.where(suitability_array_state == 0, 0, 1)

        # exclude all area for the default dimension
        suitability_array_state = np.insert(suitability_array_state, 0, np.ones_like(suitability_array_state[0, :, :]), axis=0)

        # apply the mask to NLC data
        nlc_mask = ma.masked_array(nlc_arr, mask=suitability_array_state)

        # exclude technologies that do not have an expansion
        #   get a list of techs that have an expansion
        local_expansion = {k: expansion_plan[k] for k in expansion_plan.keys() if expansion_plan[k] > 0}

        # get a mapping from original tech ids to local tech ids; this is so we can still use argmin
        exp_id_mapping = {k: ix+1 for ix, k in enumerate(local_expansion.keys())}
        exp_id_mapping[0] = 0

        # get a list of techs that have an expansion; ensure 0 position is kept
        exp_index_list = [0] + list(exp_id_mapping.keys())

        # create a local expansion plan reindex dictionary excluding technologies that have no expansion
        local_exp_reindex = {ix+1: local_expansion[k] for ix, k in enumerate(local_expansion.keys())}

        # extract valid techs from nlc_mask
        local_nlc_mask = nlc_mask[exp_index_list, :, :].copy()

        comp = Competition(local_exp_reindex, local_nlc_mask, verbose=False)

        t0 = time.time()

        final_array = comp.compete()

        # map back to original technology ids
        # final_array = np.vectorize(exp_id_mapping.get)(final_array)

        # create an output raster of sited techs; 0 is NaN
        final_array = np.where(final_array == 0, np.nan, final_array)

        print((time.time() - t0))

        # with rasterio.open('/Users/d3y010/Desktop/nlc/va_suit.tif', 'w', **int_meta) as dest:
        #     dest.write(suitability_array.astype(rasterio.int8), 1)
        #
        float_meta = int_meta.copy()
        float_meta.update(dtype=rasterio.float64)
        #
        # with rasterio.open('/Users/d3y010/Desktop/nlc/nlc_nuclear.tif', 'w', **float_meta) as dest:
        #     dest.write(nlc_arr[9].astype(rasterio.float64), 1)
        #
        # with rasterio.open('/Users/d3y010/Desktop/nlc/ic_nuclear.tif', 'w', **float_meta) as dest:
        #     dest.write(tech_dict['nuclear']['ic'].astype(rasterio.float64), 1)
        #
        # with rasterio.open('/Users/d3y010/Desktop/nlc/nov_nuclear.tif', 'w', **float_meta) as dest:
        #     dest.write(tech_dict['nuclear']['nov'].astype(rasterio.float64), 1)
        #
        # with rasterio.open('/Users/d3y010/Desktop/nlc/lmp_nuclear.tif', 'w', **float_meta) as dest:
        #     dest.write(tech_dict['nuclear']['lmp_arr'].astype(rasterio.float64), 1)

        with rasterio.open(f'/Users/d3y010/Desktop/nlc/va_sited_state_{state_id}.tif', 'w', **float_meta) as dest:
            dest.write(final_array.astype(rasterio.float64), 1)

