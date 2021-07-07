import os

import numpy as np
import pandas as pd


class ProcessExpansion:
    """Convert expected electricity capacity plan to CERF XML format.

    :param expansion_plan_file:         Full path with file name and extension of input
                                        expansion plan file.

    :param scenario:                    Name of the target scenario.

    :param target_yr:                   Four digit year to extract.

    :param target_techs:                List of technologies to include in the expansion plan.

    :param tech_dict:                   Dictionary of {cerf_technology_name: cerf_technology_id}

    :param primary_zone_dict:           Dictionary of {cerf_state_abbreviation: cerf_state_id}

    :param expansion_plan_xml_dir:      Full path to the directory to save the
                                        expansionplan.xml file to.

    :param output_csv:                  Boolean. Choose to save a copy to of the expansion
                                        plan as a CSV file. Default is `False`.

    """

    def __init__(self, expansion_plan_file, scenario, target_yr, target_techs, tech_dict,
                 primary_zone_dict, expansion_plan_xml_dir, output_csv=False):

        self.expansion_plan_file = expansion_plan_file
        self.scenario = scenario
        self.target_yr = target_yr
        self.target_techs = target_techs
        self.tech_dict = tech_dict
        self.primary_zone_dict = primary_zone_dict
        self.output_csv = output_csv

        self.expansion_plan_xml = os.path.join(expansion_plan_xml_dir, 'expansionplan_{}.xml'.format(self.target_yr))
        self.expansion_plan_csv = os.path.join(expansion_plan_xml_dir, 'expansionplan_{}.csv'.format(self.target_yr))

    @staticmethod
    def check_idx(variable, idx, delim):
        """Split expansion variable by delimiter.  Return 'none' as string
        if the requested subcategory is not present.  Otherwise, return the
        name of the requested.

        :param variable:                The variable string to parse.

        :param idx:                     The index number to parse.

        :param delim:                   The variable string delimiter.

        :return:                        'none' if index not present, else
                                        the name.

        """
        try:
            return variable.split(delim)[idx]

        except IndexError:
            return 'none'

    @staticmethod
    def build_expansion_plan_xml_row(row):
        """Construct rows for the expansionplan.xml file.

        :param row:                     Data frame row containing input data.

        :return:                        XML formatted row.

        """

        return '  <expansion techid="{}" zoneid="{}">{}</expansion>'.format(row['techid'],
                                                                            row['zoneid'],
                                                                            int(round(row['value_mw'], 0)))

    def check_tech(self, exp_techs):
        """Make sure technologies expected by the user are in the expansion plan.
        If not, report.

        :param target_techs:            List of the target technologies desired by
                                        desired by the user.

        :param exp_techs:               List of technologies in the expansion plan.

        """
        ck = set(self.target_techs) - set(exp_techs)

        if len(ck) > 0:
            print("WARNING: The following target technologies are not in the expansion plan:  {}".format(ck))

    def process_expansion_plan(self):
        """Convert expected electricity capacity plan to CERF XML format.

        :param expansion_plan_file:         Full path with file name and extension of input
                                            expansion plan file.

        :param scenario:                    Name of the target scenario.

        :param target_yr:                   Four digit year to extract.
        """
        df = pd.read_csv(self.expansion_plan_file, usecols=['Scenario', 'Region-Origin', 'Year', 'Variable', 'Value'])

        # rename columns
        df.columns = ['scenario', 'primary_zone', 'yr', 'variable', 'value_gw']

        # convert any NA values in input to 0
        df.fillna(0, inplace=True)

        # extract target scenario and year
        df = df.loc[(df['scenario'] == self.scenario) & (df['yr'] == self.target_yr)]

        # create a catetory variable field
        df['category'] = df['variable'].apply(lambda x: self.check_idx(x, 0, '|'))

        # get only electricity capacity values
        df = df.loc[(df['category'] == 'Electricity Capacity')]

        # split out technology aggregated class (Biomass, Gas, etc.)
        df['technology'] = df['variable'].apply(lambda x: self.check_idx(x, 1, '|'))

        # exclude aggregated category that does not have specific technology breakouts
        df = df.loc[df['technology'] != 'none']

        # make sure desired techs are in the expansion plan
        self.check_tech(df['technology'].unique())

        # get target technologies and break out subtech and storage type
        df = df.loc[(df['technology'].isin(self.target_techs))]

        df['subtech'] = df['variable'].apply(lambda x: self.check_idx(x, 2, '|'))
        df['storage'] = df['variable'].apply(lambda x: self.check_idx(x, 3, '|'))

        df.drop(['variable', 'category'], axis=1, inplace=True)

        # convert GW to MW
        df['value_mw'] = df['value_gw'] * 1000
        df.drop('value_gw', axis=1, inplace=True)

        # set cerf_name default
        df['cerf_name'] = 'none'

        # coal conventional pulverized
        df['cerf_name'] = np.where((df['technology'] == 'Coal') &
                                   (df['subtech'] == 'Conv Pul') &
                                   (df['storage'].isin(('wo CCS', 'w CCS'))),
                                   'coal_conv', df['cerf_name'])

        # coal igcc without ccs
        df['cerf_name'] = np.where((df['technology'] == 'Coal') &
                                   (df['subtech'] == 'IGCC') &
                                   (df['storage'] == 'wo CCS'),
                                   'coal_igcc_wo_ccs', df['cerf_name'])
        # coal igcc with ccs
        df['cerf_name'] = np.where((df['technology'] == 'Coal') &
                                   (df['subtech'] == 'IGCC') &
                                   (df['storage'] == 'w CCS'),
                                   'coal_igcc_with_ccs', df['cerf_name'])

        # gas turbine
        df['cerf_name'] = np.where((df['technology'] == 'Gas') &
                                   (df['subtech'].isin(('CT', 'ST'))) &
                                   (df['storage'].isin(('wo CCS', 'w CCS'))),
                                   'gas_turbine', df['cerf_name'])

        # gas cc
        df['cerf_name'] = np.where((df['technology'] == 'Gas') &
                                   (df['subtech'] == 'CC') &
                                   (df['storage'].isin(('wo CCS', 'w CCS'))),
                                   'gas_cc', df['cerf_name'])

        # oil cc
        df['cerf_name'] = np.where((df['technology'] == 'Oil') &
                                   (df['subtech'] == 'CC') &
                                   (df['storage'].isin(('wo CCS', 'w CCS'))),
                                   'oil_cc', df['cerf_name'])

        # oil turbine
        df['cerf_name'] = np.where((df['technology'] == 'Oil') &
                                   (df['subtech'] == 'CT') &
                                   (df['storage'].isin(('wo CCS', 'w CCS'))),
                                   'oil_turbine', df['cerf_name'])

        # biomass conventional
        df['cerf_name'] = np.where((df['technology'] == 'Biomass') &
                                   (df['subtech'] == 'Conv') &
                                   (df['storage'].isin(('wo CCS', 'w CCS'))),
                                   'biomass', df['cerf_name'])
        # biomass igcc without ccs
        df['cerf_name'] = np.where((df['technology'] == 'Biomass') &
                                   (df['subtech'] == 'IGCC') &
                                   (df['storage'] == 'wo CCS'),
                                   'biomass_igcc_wo_ccs', df['cerf_name'])

        # biomass igcc with ccs
        df['cerf_name'] = np.where((df['technology'] == 'Biomass') &
                                   (df['subtech'] == 'IGCC') &
                                   (df['storage'] == 'w CCS'),
                                   'biomass_igcc_with_ccs', df['cerf_name'])
        # nuclear
        df['cerf_name'] = np.where((df['technology'] == 'Nuclear') &
                                   (df['subtech'].isin(('Gen II', 'Gen III'))),
                                   'nuclear', df['cerf_name'])

        # solar - all combined
        df['cerf_name'] = np.where((df['technology'] == 'Solar') &
                                   (df['subtech'].isin(('CSP', 'PV'))) &
                                   (df['storage'] != 'Dist') &
                                   (df['storage'] != 'Non Dist'),
                                   'solar_csp', df['cerf_name'])

        # wind onshore
        df['cerf_name'] = np.where((df['technology'] == 'Wind') &
                                   (df['subtech'] == 'Onshore'),
                                   'wind_onshore', df['cerf_name'])

        # drop none names
        df.drop(['technology', 'subtech', 'storage', 'yr'], axis=1, inplace=True)
        df = df.loc[df['cerf_name'] != 'none']

        # map ids to names
        df['techid'] = df['cerf_name'].map(self.tech_dict)
        df['tech_nm'] = df['cerf_name']
        df['zoneid'] = df['primary_zone'].map(self.primary_zone_dict)
        df['zone_nm'] = df['primary_zone']

        # remove non-CONUS states
        df = df[df['zoneid'].notnull()]

        # sum by cerf name
        gdf = df.groupby(['techid', 'zoneid', 'tech_nm', 'zone_nm']).sum()
        gdf.reset_index(inplace=True)

        # build expansionplan.xml
        dfx = '\n'.join(gdf.apply(self.build_expansion_plan_xml_row, axis=1))
        xml = '<expansionplan>\n{}\n</expansionplan>'.format(dfx)

        with open(self.expansion_plan_xml, 'w') as out:
            out.write(xml)

        if self.output_csv:
            gdf.to_csv(self.expansion_plan_csv, index=False)

        return gdf
