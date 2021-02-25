import os
import json
import pkg_resources

import rasterio
import numpy as np
import pandas as pd


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


class Model:

    def __init__(self, **kwargs):

        self.start_year = kwargs.get('start_year', 2010)
        self.end_year = kwargs.get('end_year', 2010)
        self.timestep = kwargs.get('timestep', 5)

        self.utility_zone_raster_file = kwargs.get('utility_zone_raster_file', None)


if __name__ == '__main__':

    # utility zones raster file
    utility_zone_raster_file = '/Users/d3y010/projects/cerf/data/gis/rast/cerf_powerzones.img'

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
    exp_file = '/Users/d3y010/projects/cerf/runs/GCAM_CERF_reporting_2019.04.11/gcam_reference/inputs/xml/expansionplan_{}.csv'.format(yr)
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
    tech_id = {'biomass_conv' : '9',
                'biomass_igcc_with_ccs' : '15',
                'biomass_igcc_wo_ccs' : '10',
                'coal_conv' : '1',
                'coal_igcc_with_ccs' : '12',
                'coal_igcc_wo_ccs' : '2',
                'gas_cc' : '5',
                'gas_turbine' : '3',
                'nuclear' : '11',
                #'oil_cc' : '8',
                'oil_turbine' : '6',
                'solar' : '16',
                'wind' : '17'}

    # mapping to raster name
    tech_to_raster_dict = {'biomass_conv' : 'suitability_biomass.sdat',
                'biomass_igcc_with_ccs' : 'suitability_biomass_igcc_ccs.sdat',
                'biomass_igcc_wo_ccs' : 'suitability_biomass_igcc.sdat',
                'coal_conv' : 'suitability_coal.sdat',
                'coal_igcc_with_ccs' : 'suitability_coal_igcc_ccs.sdat',
                'coal_igcc_wo_ccs' : 'suitability_coal_igcc.sdat',
                'gas_cc' : 'suitability_gas_cc.sdat',
                'gas_turbine' : 'suitability_gas_baseload.sdat',
                'nuclear' : 'suitability_nuclear.sdat',
                'oil_turbine' : 'suitability_oil_peak.sdat',
                'solar' : 'suitability_solar.sdat',
                'wind' : 'suitability_wind.sdat'}

    # ----------------------------------------------------------
    # process technology information
    # ----------------------------------------------------------

    tech_dict = {}

    for tech in tech_id.keys():

        # load technology specific info for the target technology
        lifetime = tech_info.loc[(tech_info['metric'] == 'Lifetime') & (tech_info['tech'] == tech)]['Value'].values[0]
        capacity_factor = tech_info.loc[(tech_info['metric'] == 'Capacity Factor') & (tech_info['tech'] == tech)]['Value'].values[0]
        variable_cost_esc_rate = static[tech]['var_cost_esc']
        fuel_esc_rate = tech_info.loc[(tech_info['metric'] == 'Fuel Price Escalation') & (tech_info['tech'] == tech)]['Value'].values[0]
        unit_size = static[tech]['unit_size']
        interconnection_cost_per_km = static[tech]['ic']
        variable_om = tech_info.loc[(tech_info['metric'] == 'Variable OM') & (tech_info['tech'] == tech)]['Value'].values[0]
        heat_rate = tech_info.loc[(tech_info['metric'] == 'Heat Rate') & (tech_info['tech'] == tech)]['Value'].values[0]
        fuel_price = tech_info.loc[(tech_info['metric'] == 'Fuel Price') & (tech_info['tech'] == tech)]['Value'].values[0]
        carbon_capture_rate = tech_info.loc[(tech_info['metric'] == 'Carbon Capture Rate') & (tech_info['tech'] == tech)]['Value'].values[0]
        fuel_co2_content = tech_info.loc[(tech_info['metric'] == 'Fuel CO2 Content') & (tech_info['tech'] == tech)]['Value'].values[0]

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