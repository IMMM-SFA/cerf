"""
Reads config.ini and validates parameters.

Copyright (c) 2017, Battelle Memorial Institute

Open source under license BSD 2-Clause - see LICENSE and DISCLAIMER

@author:  Chris R. Vernon (chris.vernon@pnnl.gov)
"""

import datetime
import logging
import os
import sys
import untangle

from configobj import ConfigObj


class ReadConfig:
    # required XML files
    XML = ['constants.xml', 'expansionplan.xml', 'powerzones.xml', 'states.xml', 'technologies.xml',
           'technology_suitabilitymask_paths.xml']

    # required constants with [ lower bounds, upper bounds, type ] None if not applicable
    CNST = {'discount_rate': [0.0, 1.0, float],
            'carbon_tax': [0.0, 1.0, float],
            'carbon_tax_escalation': [0.0, 1.0, float],
            'tx_lifetime': [0, None, int],
            'interconnection_cost_gas': [0, None, float]}

    # required nodes, bounds, and types for technologies.xml [ lower bounds, upper bounds, type ]
    TECH = {'id': [0, None, int],
            'unit_size': [0, None, int],
            'capacity_factor': [0.0, 1.0, float],
            'variable_om': [0.0, None, float],
            'variable_cost_escalation_rate': [None, None, float],
            'heat_rate': [0.0, None, float],
            'fuel_price': [0.0, None, float],
            'fuel_price_escalation': [None, None, float],
            'fuel_co2_content': [0, None, float],
            'interconnection_cost_per_km': [0, None, int],
            'full_name': [None, None, unicode],
            'lifetime': [0, None, int],
            'category': [None, None, unicode],
            'fuel_index': [None, None, unicode],
            'fixed_om_2005': [0.0, None, float],
            'variable_om_2005': [None, None, float],
            'minimum_capacity': [0, None, int],
            'maintenance_requirement': [0, None, int],
            'forced_outage_rate': [0, None, float],
            'forced_outage_duration': [0, None, int],
            'efficiency_2005': [0.0, None, float],
            'siting_buffer': [0, None, int],
            'carbon_capture_rate': [0.0, None, float]}

    # acceptable values for the capacity factor fractions in the powerzones.xml file
    CF_VALS = ('0.9', '0.8', '0.5', '0.3', '0.1')

    def __init__(self, config_file):

        self.log = self.console_logger()

        # get current time
        self.dt = datetime.datetime.now().strftime('%Y-%m-%d_%Hh%Mm%Ss')

        # check and validate ini file exists
        self.check_exist(config_file, 'file', self.log)

        # instantiate config object
        self.c = ConfigObj(config_file)

        # get params
        p = self.c['PARAMS']

        # path to the CERF executable
        self.exe_path = self.check_exist(p['exe_path'], 'file', self.log)

        # path to the directory containing the input XML files
        self.xml_path = self.validate_xml(p['xml_path'])

        # output directory
        self.out_path = p['out_path']

        # year to run
        self.yr = int(p['yr'])

        # state zone boundary raster
        self.primary_zone = p['primary_zone']

        # utility zone boundary raster
        self.utility_zones = p['utility_zones']

        # suitability exclusion area raster common to all technologies
        self.common_exclusion = p['common_exclusion']

        # transmission lines >= 230 KV input raster
        self.transmission_230kv = p['transmission_230kv']

        # transmission lines >= 345 KV input raster
        self.transmission_345kv = p['transmission_345kv']

        # transmission lines >= 500 KV input raster
        self.transmission_500kv = p['transmission_500kv']

        # transmission lines >= 765 KV input raster
        self.transmission_765kv = p['transmission_765kv']

        # gas pipeline >= 16 inch input raster
        self.gasline_16in = p['gasline_16in']

        # buffer in grid cells to place around each site
        self.buffer = int(p['buffer'])

        # method to calculate interconnection distance [ 2 is Euclidean Distance ]
        self.distance_method = int(p['distance_method'])

        # order method used to site [ 0 = Left, Right, Top, Bottom ]
        self.direction_method = int(p['direction_method'])

    @staticmethod
    def check_exist(f, kind, log):
        """
        Check file or directory existence.

        :param f        file or directory full path
        :param kind     either 'file' or 'dir'
        :return         either path or error
        """
        if kind == 'file' and os.path.isfile(f) is False:
            log.error("File not found:  {0}".format(f))
            log.error("Confirm path and retry.")
            raise IOError('File not found: {0}. Confirm path and retry.'.format(f))

        elif kind == 'dir' and os.path.isdir(f) is False:
            log.error("Directory not found:  {0}".format(f))
            log.error("Confirm path and retry.")
            raise IOError('Directory not found: {0}. Confirm path and retry.'.format(f))

        else:
            return f

    def console_logger(self):
        """
        Instantiate console logger to log any errors in config.ini file that the user
        must repair before model initialization.

        :return:  logger object
        """
        # set up logger
        log = logging.getLogger('cerf_initialization_logger')
        log.setLevel(logging.INFO)

        # set up console handler
        fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        cns = logging.StreamHandler(sys.stdout)
        cns.setLevel(logging.INFO)
        cns.setFormatter(fmt)
        log.addHandler(cns)

        return log

    def validate_xml(self, path):
        """
        Ensure that all XML inputs are present and their format and values are within the
        expected bounds.

        :return:
        """
        # check to see if inputs dir exists
        self.check_exist(path, 'dir', self.log)

        # get a list of all files in dir
        files = os.listdir(path)

        # see if the expected files are in the dir
        missing = list(set(ReadConfig.XML) - set(files))

        if len(missing) > 0:
            raise IOError('The following files are missing from the input XML directory:  {}'.format(missing))

        # validate constants.xml
        self.eval_constants(os.path.join(path, ReadConfig.XML[0]))

        # validate technologies.xml
        self.eval_techs(os.path.join(path, ReadConfig.XML[4]))

        # validate powerzones.xml
        self.eval_zones(os.path.join(path, ReadConfig.XML[2]))

        # validate expansionplan.xml
        self.eval_expansion(os.path.join(path, ReadConfig.XML[1]))

    @staticmethod
    def eval_constants(f):
        """
        Validate constants.xml input data.

        :return:
        """
        obj = untangle.parse(f)

        # look for root node
        try:
            root = obj.constants
        except AttributeError:
            raise AttributeError('Root node: <constants> is missing or misspelled in file {}. Exiting...'.format(f))

        # look for child
        try:
            child = root.constant
        except AttributeError:
            raise AttributeError('Child node: <constant> is missing or misspelled in file {}. Exiting...'.format(f))

        # check to make sure all attributes are in the file
        match = list(set([a['name'] for a in child]) - set(ReadConfig.CNST.keys()))
        if len(match) > 0:
            raise KeyError('The following constants are missing from file {0}: {1}. Exiting...'.format(f, match))

        # validate values
        for v in child:

            # check for valid var name
            try:
                e = ReadConfig.CNST[v['name']]
            except KeyError:
                raise KeyError(
                    'Named constant "{0}" not expected in file {1}. Required constants are: {2}. Exiting...'.format(
                        v['name'], f, [i for i in ReadConfig.CNST.keys()]))

            # check for valid type
            try:
                xp = e[2](v.cdata)
            except ValueError:
                raise ValueError(
                    'Incorrect type for constant "{0}" in file {1}.  Required type is {2}. Exiting...'.format(v['name'],
                                                                                                              f, e[2]))

            # check lower bound
            if (e[0] is not None) and (xp < e[0]):
                raise ValueError(
                    'Value {0} for constant "{1}" is lower than the expected bound of {2} in file {3}. Exiting...'.format(
                        xp, v['name'], e[0], f))

            # check upper bound
            if (e[1] is not None) and (xp > e[1]):
                raise ValueError(
                    'Value {0} for constant "{1}" is greater than the expected bound of {2} in file {3}. Exiting...'.format(
                        xp, v['name'], e[1], f))

        return f

    @staticmethod
    def eval_techs(f):
        """
        Validate technologies.xml input data.

        :return:
        """
        obj = untangle.parse(f)

        # look for root node
        try:
            root = obj.technologies
        except AttributeError:
            raise AttributeError('Root node: <technologies> is missing or misspelled in file {}. Exiting...'.format(f))

        # look for child
        try:
            child = root.technology
        except AttributeError:
            raise AttributeError('Child node: <technology> is missing or misspelled in file {}. Exiting...'.format(f))

        # check each technology
        for idx in range(len(child)):

            for k in ReadConfig.TECH.keys():

                e = ReadConfig.TECH[k]

                # check for attribute existence
                try:
                    v = eval('child[{0}].{1}'.format(idx, k))
                except AttributeError:
                    raise AttributeError('Attribute "{0}" does not exist in the file {1}. Exiting...'.format(k, f))

                # check for valid type
                try:
                    xp = e[2](v.cdata)
                except ValueError:
                    raise ValueError(
                        'Incorrect type for attribute "{0}" value of {1} in file {2}.  Required type is {3}. Exiting...'.format(
                            k, v.cdata, f, e[2]))

                # check lower bound
                if (e[0] is not None) and (xp < e[0]):
                    raise ValueError(
                        'Value {0} for "{1}" is lower than the expected bound of {2} in file {3}. Exiting...'.format(
                            xp, v.cdata, e[0], f))

                # check upper bound
                if (e[1] is not None) and (xp > e[1]):
                    raise ValueError(
                        'Value {0} for "{1}" is greater than the expected bound of {2} in file {3}. Exiting...'.format(
                            xp, v.cdata, e[1], f))

        return f

    @staticmethod
    def eval_zones(f):

        obj = untangle.parse(f)

        # look for root node
        try:
            root = obj.powerzones
        except AttributeError:
            raise AttributeError('Root node: <powerzones> is missing or misspelled in file {}. Exiting...'.format(f))

        # look for zone child
        try:
            zones = root.zone
        except AttributeError:
            raise AttributeError('Child node: <zone> is missing or misspelled in file {}. Exiting...'.format(f))

        for v in zones:

            vid = v['id']

            if vid is None:
                raise AttributeError('Attribute "id" missing from <zone> node in file {}. Exiting...'.format(f))

            try:
                zoneid = v.shapeid.cdata
            except AttributeError:
                raise AttributeError('Child node: <shapeid> missing from zone "{}" in file {}'.format(vid, f))

            if len(zoneid) < 1:
                raise ValueError('<shapeid> data missing for zone {} in file {}'.format(vid, f))

            try:
                nm = v.name.cdata
            except AttributeError:
                raise AttributeError('Child node: <name> missing from zone "{}" in file {}'.format(vid, f))

            if len(nm) < 1:
                raise ValueError('<name> data missing for zone {} in file {}'.format(vid, f))

            try:
                lmp = v.lmp.cdata
            except AttributeError:
                raise AttributeError('Child node: <lmp> missing from zone "{}" in file {}'.format(vid, f))

            if len(lmp) < 1:
                raise ValueError('<lmp> data missing for zone {} in file {}'.format(vid, f))

            try:
                float(lmp)
            except ValueError:
                raise ValueError(
                    '<lmp> data must be a float or int value for zone {} in file {}. Data "{}" cannot be converted to float'.format(
                        vid, f, lmp))

            try:
                desc = v.description.cdata
            except AttributeError:
                raise AttributeError('Child node: <description> missing from zone "{}" in file {}'.format(vid, f))

            try:
                lmps = v.lmps
            except AttributeError:
                raise AttributeError('Child node: <lmps> missing from zone "{}" in file {}'.format(vid, f))

            try:
                cfs = lmps.cf
            except AttributeError:
                raise AttributeError('Child node <cf> missing from zone "{}" in file {}.'.format(vid, f))

            for item in cfs:

                cfv = item['value']

                if cfv not in ReadConfig.CF_VALS:
                    raise ValueError(
                        'Capacity factor fraction attribute value "{}" not in acceptable values of {} for zone {} in file {}.'.format(
                            cfv, ReadConfig.CF_VALS, vid, f))

                cfd = item.cdata

                try:
                    float(cfd)
                except ValueError:
                    raise ValueError(
                        'Capactiy factor "{}" for fraction "{}" in zone {} in file {} is not able to be converted to float.'.format(
                            cfd, cfv, vid, f))

        return f

    @staticmethod
    def eval_expansion(f):
        """
        TODO: Validate expansionplan.xml input data.

        :return:
        """
        obj = untangle.parse(f)

        # look for root node
        try:
            root = obj.expansionplan
        except AttributeError:
            raise AttributeError('Root node: <expansionplan> is missing or misspelled in file {}. Exiting...'.format(f))

        # look for child
        try:
            child = root.expansion
        except AttributeError:
            raise AttributeError('Child node: <expansion> is missing or misspelled in file {}. Exiting...'.format(f))

        # validate values
        for v in child:
            zoneid = v['zoneid']
            techid = v['techid']
            exp = v.cdata

            break

            # TODO: check to make sure all zones/techs in the expansion plan are in the technology.xml and the powerzones.mxl

        return f

    @staticmethod
    def eval_states(f):

        pass

    @staticmethod
    def eval_rasters(f):

        pass


if __name__ == "__main__":
    ini = '/Users/ladmin/repos/github/cerf/config.ini'

    c = ReadConfig(ini)