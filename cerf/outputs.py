"""
Generate figures based on user desires.

Copyright (c) 2018, Battelle Memorial Institute

Open source under license BSD 2-Clause - see LICENSE and DISCLAIMER

@author:  Chris R. Vernon (chris.vernon@pnnl.gov)
"""

import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import pylab

from config_reader import ReadConfig


class ValidationException(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

class Outputs:
    """
    Process and create outputs for the CERF model.
    """
    
    def __init__(self, ini, cerf_output=None):
        
        cfg = ReadConfig(ini)
        
        if cerf_output is None:
            self.sited_xml = os.path.join(cfg.out_path, 'plantsites_{}.xml'.format(cfg.yr))
        else:
            self.sited_xml = cerf_output
            
        self.states_xml = os.path.join(cfg.xml_path, 'states.xml')
        self.tech_xml = os.path.join(cfg.xml_path, 'technologies.xml')
        self.exp_xml = os.path.join(cfg.xml_path, 'expansionplan.xml')
        self.out_dir = cfg.out_path
                
        # read in states.xml as dict
        self.sdct = self.read_states()
        
        # read in technologies.xml and get unit size per tech
        self.udct, self.tdct = self.get_tech_info()
        
        # get expansion data as dict and a sum per state and tech dict
        self.d_exp, self.df_plan = self.get_expansion()  
        
        # build plantsited data frame
        self.df_site = self.read_plantsites()

    def read_plantsites(self):
        """
        Mine information from the plantsites.xml file.
        """
        d = {'x': [], 'y': [], 'nlc': [], 'techid': [], 'zoneid': [], 'nov': [], 'ic': [], 'capacity': []}
        with open(self.sited_xml) as get:
            get.next()
            for row in get:
                r = row.strip()
                try:
                    d['x'].append(float(r.split('xworld="')[1].split('"')[0]))
                    d['y'].append(float(r.split('yworld="')[1].split('"')[0]))
                    d['nlc'].append(float(r.split('net_location_cost="')[1].split('"')[0]))
                    d['techid'].append(int(r.split('techid="')[1].split('"')[0]))
                    d['zoneid'].append(int(r.split('zoneid="')[1].split('"')[0]))
                    d['nov'].append(float(r.split('net_operational_value="')[1].split('"')[0]))
                    d['ic'].append(float(r.split('interconnection_cost="')[1].split('"')[0]))
                    d['capacity'].append(int(r.split('capacity_sited="')[1].split('"')[0]))
                except IndexError:
                    pass
        
        df = pd.DataFrame(d)
        
        # add state and technology readable names
        df['state'] = df['zoneid'].map(self.sdct)
        df['technology'] = df['techid'].map(self.tdct)
    
        return df
    
    def read_states(self):
        """
        Get the shapeid and name of each state in the input XML file.
        """
        d = {}
        with open(self.states_xml) as get:
            for row in get:
                i = row.strip()
                if 'shapeid' in i:
                    try:
                        sid = int(i.split('shapeid="')[1].split('"')[0])
                        snm = i.split('>')[1].split('<')[0]
                        d[sid] = snm
                    except IndexError:
                        pass
        return d 

    def get_expansion(self):
        """
        Get expansion.xml file as dict and data frame
        """
        d = {}
        dx = {'techid': [], 'zoneid': [], 'capacity': []}
        with open(self.exp_xml) as get:
            for row in get:
                i = row.strip()
                if 'techid' in i:
                    try:
                        t = int(i.split('techid="')[1].split('"')[0])
                        z = int(i.split('zoneid="')[1].split('"')[0])
                        v = int(i.split('>')[1].split('<')[0])
                        dx['techid'].append(t)
                        dx['zoneid'].append(z)
                        dx['capacity'].append(v)
                        d['{}_{}'.format(t, z)] = v
                    except IndexError:
                        pass
                    
        df = pd.DataFrame(dx)
        df['Siting'] = 'planned'
        df['pkey'] = df['zoneid'].astype(str) + '_' + df['techid'].astype(str)
        df['unit_size'] = df['techid'].map(self.udct)
        df['num_sites'] = (df['capacity'] / df['unit_size']).round(0).astype(int)
        
        return d, df
        
    def get_tech_info(self):
        """
        Get unit_size from the technology.xml file.
        """
        unit_d = {}
        tech_d = {}
        with open(self.tech_xml) as get:
            for row in get:
                i = row.strip()
                if '<id>' in i:
                    try:
                        sid = int(i.split('<id>')[1].split('</id>')[0])
                    except IndexError:
                        pass
                if '<unit_size>' in i:
                    try:
                        us = int(i.split('<unit_size>')[1].split('</unit_size>')[0])
                        unit_d[sid] = us
                    except IndexError:
                        pass
                if '<full_name>' in i:
                    try:
                        nm = i.split('<full_name>')[1].split('</full_name>')[0]
                        tech_d[sid] = nm
                    except IndexError:
                        pass
    
        return unit_d, tech_d 

    def stack_frames(self):
        """
        Stack planned and sited capacity data frames. Creates field for the 
        number of plants sited per state and technology.
        """
        obs = self.sited_by_capacity()
        cdf = pd.concat([self.df_plan, obs])
        cdf['state'] = cdf['zoneid'].map(self.sdct)
        cdf['technology'] = cdf['techid'].map(self.tdct)
        cdf['unit_size'] = cdf['techid'].map(self.udct)
        cdf['num_sites'] = (cdf['capacity'] / cdf['unit_size']).round(0)
        
        return cdf
        
    def sited_by_capacity(self):
        """
        Create a data frame that sums sited capacity by zoneid and techid.
        """
        obs = self.df_site.groupby(['zoneid', 'techid'])['capacity', 'ic'].sum()
        obs.reset_index(inplace=True)
        obs.drop('ic', axis=1, inplace=True)
        obs['Siting'] = 'sited'
        obs['pkey'] = obs['zoneid'].astype(str) + '_' + obs['techid'].astype(str)
        obs['unit_size'] = obs['techid'].map(self.udct)
        obs['num_sites'] = (obs['capacity'] / obs['unit_size']).round(0).astype(int)       

        return obs
        
    def set_outfile(self, out_file, basenm=None):
        """
        Check and return out_file name.
        """
        if out_file is None:
            out = os.path.join(self.out_dir, basenm)
        else:
            save_dir = os.path.dirname(out_file)
            if os.path.isdir(save_dir):
                out = out_file
            else:
                raise IOError('File "{}" is not a valid directory.'.format(save_dir))
        
        return out  

    def export_planned_vs_sited(self, out_file=None):
        """
        Shows the number of sites that were planned but not sited and vice versa.
        Outputs as a CSV file.
        
        :@param out_file:       Full path with extension to save output file; if
                                None (Default) file will be saved to output dir
                                from run.
        :@returns:              Data frame
        """
        obs = self.sited_by_capacity()
        mdf = pd.merge(self.df_plan, obs, how='left', on='pkey')
        mdf.fillna(0, inplace=True)
        mdf['not_sited'] = mdf['num_sites_x'] - mdf['num_sites_y']
        # eliminate all sited and overflow cases
        mdf = mdf.loc[(mdf['not_sited'] != 0) & (mdf['num_sites_x'] != 0)]
        mdf.drop(['capacity_x', 'capacity_y', 'techid_y', 'zoneid_y', 'Siting_x', 
                  'unit_size_x', 'Siting_y', 'unit_size_y', 'pkey' ], axis=1, inplace=True)
                  
        mdf.columns = ['techid', 'zoneid', 'planned', 'sited', 'not_sited']
        mdf['state'] = mdf['zoneid'].map(self.sdct)
        mdf['technology'] = mdf['techid'].map(self.tdct)
        
        out = self.set_outfile(out_file, 'planned_versus_sited.csv')
        
        mdf.to_csv(out, index=False)
        
        return mdf

    def heatmap(self, metric='ic', annot=False, figsize=(10,20), dpi=150, out_file=None):
        """
        Create a heatmap figure showing all states and technologies
        relative to one another for a target metric.
        
        :@param metric:         Either 'ic', 'nlc', or 'nov' for interconnection
                                cost, net locational cost, or net operating value, 
                                respectively
        :@param annot:          Boolean to annotate the cells value onto the
                                figure; default False
        :@param figsize:        Tuple to define the size of the figure (x, y)
        :@param dpi:            Dots per inch of output figure; default 150
        :@param out_file:       Full path with extension to save output file; if
                                None (Default) file will be saved to output dir
                                from run.
        """        
        if metric.lower() == 'ic':
            v = 'Interconnection cost'
            units = '($/yr)'
        elif metric.lower() == 'nlc':
            v = 'Net locational cost'
            units = '($/yr)'
        elif metric.lower() == 'nov':
            v = 'Net operating value'
            units = '($/yr)'
        else:
            raise ValidationException('Metric entered "{}" not "ic", "nlc", or "nov"'.format(metric))
        
        # prep data
        adf = self.df_site[['state', 'technology', 'nlc', 'ic', 'nov']].groupby(['state','technology']).sum()
        adf.reset_index(inplace=True)
        heat = adf.pivot('state', 'technology', metric)
        
        # set up plot
        sns.set(style="darkgrid", color_codes=True, font_scale=2)
        plt.subplots(figsize=figsize)
        ax = sns.heatmap(heat, annot=annot, cbar_kws={'label': '{} {}'.format(v, units)})
        fig = ax.get_figure()
        ax.set_title('{} per tech per state'.format(v, units), fontweight='bold')
        ax.set_xlabel("Technology") 
        ax.set_ylabel("State") 
        ttl = ax.title
        ttl.set_position([.5, 1.05])
        plt.tight_layout()
        
        out = self.set_outfile(out_file, 'heatmap_allstates_alltechs.jpg')
        
        fig.savefig(out, dpi=dpi)
        
    def plot_planned_vs_sited(self, state_name, metric='num_sites', figsize=(8,7), dpi=150, out_file=None) : 
        """
        Plot either planned versus sited number of sites or capacity per
        technology for a state.
        
        :@param state_name:         Full state name as it appears in the states.xml file
        :@param metric:             Either plot by the number of sites "num_sites" (Defualt)
                                    or by capacity "capacity"
        :@param figsize:            (x, y) size of the figure to save
        :@param dpi:                Dots per inch for the output figure
        :@param out_file:           Full path with extension to save output file; if
                                    None (Default) file will be saved to output dir
                                    from run.
        """
        if metric == 'capacity':
            v = 'Capacity (MW)'
        elif metric == 'num_sites':
            v = 'Number of Sites'
        else:
            raise ValidationException('Metric entered "{}" not "capacity" or "num_sites".'.format(metric))
            
        cdf = self.stack_frames()
        cdf = cdf.loc[cdf['state'] == state_name]
        
        if cdf.shape[0] == 0:
            raise KeyError('State name "{}" not found.'.format(state_name))
        
        # set up plot
        sns.set(style="darkgrid", color_codes=True, font_scale=2)
        plt.subplots(figsize=figsize)
        ax = sns.barplot(x="technology", y=metric, hue="Siting", data=cdf)
        fig = ax.get_figure()
        ax.set_title('Planned vs sited by tech for {}'.format(state_name), fontweight='bold')
        ax.set(ylabel=v, xlabel='Technology')
        # add thousands separator
        ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
        for item in ax.get_xticklabels():
            item.set_rotation(90)
        ttl = ax.title
        ttl.set_position([.5, 1.05])
        pylab.legend(loc=10, bbox_to_anchor=(1.2, .9))
        
        out = self.set_outfile(out_file, 'planned_vs_sited_{}.jpg'.format(state_name.lower()))
        fig.savefig(out, dpi=dpi, bbox_inches='tight')
        
    def eval_metric_per_tech(self, state_name, metric='ic', figsize=(8,7), dpi=150, out_file=None):
        """
        Plot the interconnection cost of each site per technology for a state.
		
		:@param state_name:         Full state name as it appears in the states.xml file
        :@param metric:             Either 'ic', 'nlc', or 'nov' for interconnection
									cost, net locational cost, or net operating value, 
									respectively
        :@param figsize:            (x, y) size of the figure to save
        :@param dpi:                Dots per inch for the output figure
        :@param out_file:           Full path with extension to save output file; if
                                    None (Default) file will be saved to output dir
                                    from run.
        """
        if metric == 'ic':
            v = 'Interconnection cost'
            units = '($/yr)'
        elif metric == 'nlc':
            v = 'Net locational cost'
            units = '($/yr)'
        elif metric == 'nov':
            v = 'Net operating value'
            units = '($/yr)'        
        else:
            raise ValidationException('Metric entered "{}" not "ic", "nlc", or "nov"'.format(metric))
            
        df = self.df_site.loc[self.df_site['state'] == state_name]        

        if df.shape[0] == 0:
            raise KeyError('State name "{}" not found.'.format(state_name))

        # set up plot
        sns.set(style="darkgrid", color_codes=True, font_scale=2)
        plt.subplots(figsize=figsize)
        ax = sns.stripplot(x="technology", y=metric, data=df.loc[df['state'] == state_name], jitter=True, size=8)
        fig = ax.get_figure()
        ax.set_title('{} per tech per site for {}'.format(v, state_name), fontweight='bold')
        ax.set(ylabel='{} {}'.format(v, units), xlabel='Technology')
        # add thousands separator
        ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
        
        for item in ax.get_xticklabels():
            item.set_rotation(90) 
        ttl = ax.title
        ttl.set_position([.5, 1.10]) 
        
        out = self.set_outfile(out_file, '{}_per_tech_{}.jpg'.format(metric, state_name.lower()))
        fig.savefig(out, dpi=dpi, bbox_inches='tight')
        