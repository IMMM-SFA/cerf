"""
Reads config.ini and validates parameters.

Copyright (c) 2017, Battelle Memorial Institute

Open source under license BSD 2-Clause - see LICENSE and DISCLAIMER

@author:  Chris R. Vernon (chris.vernon@pnnl.gov)
"""

import datetime
import os
import untangle

from configobj import ConfigObj
import logger


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

    # list of acceptable distance method values [0: Chessboard; 1: Manhattan;  2: Euclidean Distance]
    DIST_VALS = [0, 1, 2]

    # list of acceptable direction method values [ 0: Left, Right, Top, Bottom (default); 1: RLBT; 2: LRBT; 3: RLTB ]
    DIR_VALS = [0, 1, 2, 3]

    def __init__(self, config_file):

        # get current time
        self.dt = datetime.datetime.now().strftime('%Y-%m-%d_%Hh%Mm%Ss')

        # check and validate ini file exists
        self.check_exist(config_file, 'file')

        # instantiate config object
        self.c = ConfigObj(config_file)

        # get params
        p = self.c['PARAMS']

        # output directory
        self.out_path = self.create_dir(p['out_path'])

        # build logger
        self.log = logger.make_log(self.out_path)

        # path to the CERF executable
        self.exe_path = self.check_exist(p['exe_path'], 'file', self.log)

        # path to the directory containing the input XML files
        self.xml_path = self.validate_xml(p['xml_path'])

        # year to run
        self.yr = self.check_year(self.check_type(p['yr'], int, self.log), self.log)

        # state zone boundary raster
        self.primary_zone = self.check_exist(p['primary_zone'], 'file', self.log)

        # utility zone boundary raster
        self.utility_zones = self.check_exist(p['utility_zones'], 'file', self.log)

        # suitability exclusion area raster common to all technologies
        self.common_exclusion = self.check_exist(p['common_exclusion'], 'file', self.log)

        # transmission lines >= 230 KV input raster
        self.transmission_230kv = self.check_exist(p['transmission_230kv'], 'file', self.log)

        # transmission lines >= 345 KV input raster
        self.transmission_345kv = self.check_exist(p['transmission_345kv'], 'file', self.log)

        # transmission lines >= 500 KV input raster
        self.transmission_500kv = self.check_exist(p['transmission_500kv'], 'file', self.log)

        # transmission lines >= 765 KV input raster
        self.transmission_765kv = self.check_exist(p['transmission_765kv'], 'file', self.log)

        # gas pipeline >= 16 inch input raster
        self.gasline_16in = self.check_exist(['gasline_16in'], 'file', self.log)

        # buffer in grid cells to place around each site
        self.buffer = self.check_type(p['buffer'], int, self.log)

        # method to calculate interconnection distance [ 2 is Euclidean Distance ]
        self.distance_method = self.check_val(self.check_type(p['distance_method'], int, self.log), ReadConfig.DIST_VALS, self.log)

        # order method used to site [ 0 = Left, Right, Top, Bottom ]
        self.direction_method = self.check_val(self.check_type(p['direction_method'], int, self.log), ReadConfig.DIR_VALS, self.log)

    @staticmethod
    def check_val(v, vals, log):
        """
        Check to see if value is in the acceptable list of values.

        :param v:           value
        :param vals:        list of acceptable values
        :param log:         log instance
        :return:            value
        """
        if v not in vals:
            msg = 'Value "{}" not in acceptable list of values {}'.format(v, vals)
            log.error(msg)
            raise RuntimeError(msg)
        else:
            return v

    @staticmethod
    def check_year(y, log):
        """
        Check to make sure year is in correct format of YYYY.

        :param y:           year value
        :param log:         log instance
        :return:            year
        """
        # get number of thousands
        ck = y / 1000

        # if less than year 1000 or greater than year 9999
        if (ck < 1) or (ck > 9):
            msg = 'Year value "{}" is not in the correct YYYY format (e.g., 2005)'.format(y)
            log.error(msg)
            raise RuntimeError(msg)
        else:
            return y

    @staticmethod
    def check_type(v, typ, log):
        """
        Check type conversion.

        :param v:           value
        :param typ:         python type
        :param log:         log instance
        :return:            value
        """
        try:
            typ(v)
            return v
        except ValueError:
            msg = 'Value "{}" not able to be converted to type "{}"'.format(v, typ)
            log.error(msg)
            raise ValueError(msg)

    @staticmethod
    def check_exist(f, kind, log=None):
        """
        Check file or directory existence.

        :param f        file or directory full path
        :param kind     either 'file' or 'dir'
        :return         either path or error
        """
        if kind == 'file' and os.path.isfile(f) is False:
            if log is not None:
                log.error("File not found:  {0}".format(f))
                log.error("Confirm path and retry.")
            raise IOError('File not found: {0}. Confirm path and retry.'.format(f))

        elif kind == 'dir' and os.path.isdir(f) is False:
            if log is not None:
                log.error("Directory not found:  {0}".format(f))
                log.error("Confirm path and retry.")
            raise IOError('Directory not found: {0}. Confirm path and retry.'.format(f))

        else:
            return f

    @staticmethod
    def create_dir(pth):
        """
        Create directory if it does not exist.

        :param pth:     full path to the directory
        :return:        full path to directory
        """
        if os.path.isdir(pth):
            return pth
        else:
            os.mkdir(pth)
            return pth

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
            msg_0 = 'The following files are missing from the input XML directory:  {}'.format(missing)
            self.log.error(msg_0)
            raise IOError(msg_0)

        # validate constants.xml
        self.eval_constants(os.path.join(path, ReadConfig.XML[0]), self.log)

        # validate technologies.xml
        techs = self.eval_techs(os.path.join(path, ReadConfig.XML[4]), self.log)

        # validate powerzones.xml
        zones = self.eval_zones(os.path.join(path, ReadConfig.XML[2]), self.log)

        # validate expansionplan.xml
        self.eval_expansion(os.path.join(path, ReadConfig.XML[1]), zones, techs, self.log)

        # validate states.xml
        self.eval_states(os.path.join(path, ReadConfig.XML[3]), self.log)

        # validate technology_suitability_paths.xml
        self.eval_tech_paths(os.path.join(path, ReadConfig.XML[5]), techs, self.log)

        return path

    @staticmethod
    def eval_constants(f, log):
        """
        Validate constants.xml input data.

        :return:
        """
        obj = untangle.parse(f)

        # look for root node
        try:
            root = obj.constants
        except AttributeError:
            msg_0 = 'Root node: <constants> is missing or misspelled in file {}. Exiting...'.format(f)
            log.error(msg_0)
            raise AttributeError(msg_0)

        # look for child
        try:
            child = root.constant
        except AttributeError:
            msg_1 = 'Child node: <constant> is missing or misspelled in file {}. Exiting...'.format(f)
            log.error(msg_1)
            raise AttributeError(msg_1)

        # check to make sure all attributes are in the file
        match = list(set([a['name'] for a in child]) - set(ReadConfig.CNST.keys()))
        if len(match) > 0:
            msg_2 = 'The following constants are missing from file {0}: {1}. Exiting...'.format(f, match)
            log.error(msg_2)
            raise KeyError(msg_2)

        # validate values
        for v in child:

            # check for valid var name
            try:
                e = ReadConfig.CNST[v['name']]
            except KeyError:
                msg_3 = 'Named constant "{0}" not expected in file {1}. Required constants are: {2}. Exiting...'.format(
                    v['name'], f, [i for i in ReadConfig.CNST.keys()])
                log.error(msg_3)
                raise KeyError(msg_3)

            # check for valid type
            try:
                xp = e[2](v.cdata)
            except ValueError:
                msg_4 = 'Incorrect type for constant "{0}" in file {1}.  Required type is {2}. Exiting...'.format(
                    v['name'], f, e[2])
                log.error(msg_4)
                raise ValueError(msg_4)

            # check lower bound
            if (e[0] is not None) and (xp < e[0]):
                msg_5 = 'Value {0} for constant "{1}" is lower than the expected bound of {2} in file {3}. Exiting...'.format(
                    xp, v['name'], e[0], f)
                log.error(msg_5)
                raise ValueError(msg_5)

            # check upper bound
            if (e[1] is not None) and (xp > e[1]):
                msg_6 = 'Value {0} for constant "{1}" is greater than the expected bound of {2} in file {3}. Exiting...'.format(
                    xp, v['name'], e[1], f)
                log.error(msg_6)
                raise ValueError(msg_6)

    @staticmethod
    def eval_techs(f, log):
        """
        Validate technologies.xml input data.

        :return:
        """
        obj = untangle.parse(f)

        # look for root node
        try:
            root = obj.technologies
        except AttributeError:
            msg_0 = 'Root node: <technologies> is missing or misspelled in file {}. Exiting...'.format(f)
            log.error(msg_0)
            raise AttributeError(msg_0)

        # look for child
        try:
            child = root.technology
        except AttributeError:
            msg_1 = 'Child node: <technology> is missing or misspelled in file {}. Exiting...'.format(f)
            log.error(msg_1)
            raise AttributeError(msg_1)

        # check each technology
        techs = []
        for idx in range(len(child)):

            for k in ReadConfig.TECH.keys():

                e = ReadConfig.TECH[k]

                # check for attribute existence
                try:
                    v = eval('child[{0}].{1}'.format(idx, k))
                except AttributeError:
                    msg_2 = 'Attribute "{0}" does not exist in the file {1}. Exiting...'.format(k, f)
                    log.error(msg_2)
                    raise AttributeError(msg_2)

                # check for valid type
                try:
                    xp = e[2](v.cdata)
                except ValueError:
                    msg_3 = 'Incorrect type for attribute "{0}" value of {1} in file {2}.  Required type is {3}. Exiting...'.format(
                        k, v.cdata, f, e[2])
                    log.error(msg_3)
                    raise ValueError(msg_3)

                # check lower bound
                if (e[0] is not None) and (xp < e[0]):
                    msg_4 = 'Value {0} for "{1}" is lower than the expected bound of {2} in file {3}. Exiting...'.format(
                        xp, v.cdata, e[0], f)
                    log.error(msg_4)
                    raise ValueError(msg_4)

                # check upper bound
                if (e[1] is not None) and (xp > e[1]):
                    msg_5 = 'Value {0} for "{1}" is greater than the expected bound of {2} in file {3}. Exiting...'.format(
                        xp, v.cdata, e[1], f)
                    log.error(msg_5)
                    raise ValueError(msg_5)

                if k == 'id':
                    techs.append(xp)

        return [str(x) for x in techs]

    @staticmethod
    def eval_zones(f, log):
        """
        Validate powerzones.xml.
        """

        obj = untangle.parse(f)

        # look for root node
        try:
            root = obj.powerzones
        except AttributeError:
            msg_0 = 'Root node: <powerzones> is missing or misspelled in file {}. Exiting...'.format(f)
            log.error(msg_0)
            raise AttributeError(msg_0)

        # look for zone child
        try:
            zones = root.zone
        except AttributeError:
            msg_1 = 'Child node: <zone> is missing or misspelled in file {}. Exiting...'.format(f)
            log.error(msg_1)
            raise AttributeError(msg_1)

        z_list = []
        for v in zones:

            vid = v['id']

            if vid is None:
                msg_2 = 'Attribute "id" missing from <zone> node in file {}. Exiting...'.format(f)
                log.error(msg_2)
                raise AttributeError(msg_2)

            try:
                zoneid = v.shapeid.cdata
            except AttributeError:
                msg_3 = 'Child node: <shapeid> missing from zone "{}" in file {}'.format(vid, f)
                log.error(msg_3)
                raise AttributeError(msg_3)

            if len(zoneid) < 1:
                msg_4 = '<shapeid> data missing for zone {} in file {}'.format(vid, f)
                log.error(msg_4)
                raise ValueError(msg_4)

            # add zone to zones list
            z_list.append(zoneid)

            try:
                nm = v.name.cdata
            except AttributeError:
                msg_5 = 'Child node: <name> missing from zone "{}" in file {}'.format(vid, f)
                log.error(msg_5)
                raise AttributeError(msg_5)

            if len(nm) < 1:
                msg_6 = '<name> data missing for zone {} in file {}'.format(vid, f)
                log.error(msg_6)
                raise ValueError(msg_6)

            try:
                lmp = v.lmp.cdata
            except AttributeError:
                msg_7 = 'Child node: <lmp> missing from zone "{}" in file {}'.format(vid, f)
                log.error(msg_7)
                raise AttributeError(msg_7)

            if len(lmp) < 1:
                msg_8 = '<lmp> data missing for zone {} in file {}'.format(vid, f)
                log.error(msg_8)
                raise ValueError(msg_8)

            try:
                float(lmp)
            except ValueError:
                msg_9 = '<lmp> data must be a float or int value for zone {} in file {}. Data "{}" cannot be converted to float'.format(
                    vid, f, lmp)
                log.error(msg_9)
                raise ValueError(msg_9)

            try:
                desc = v.description.cdata
            except AttributeError:
                msg_10 = 'Child node: <description> missing from zone "{}" in file {}'.format(vid, f)
                log.error(msg_10)
                raise AttributeError(msg_10)

            try:
                lmps = v.lmps
            except AttributeError:
                msg_11 = 'Child node: <lmps> missing from zone "{}" in file {}'.format(vid, f)
                log.error(msg_11)
                raise AttributeError(msg_11)

            try:
                cfs = lmps.cf
            except AttributeError:
                msg_12 = 'Child node <cf> missing from zone "{}" in file {}.'.format(vid, f)
                log.error(msg_12)
                raise AttributeError(msg_12)

            for item in cfs:

                cfv = item['value']

                if cfv not in ReadConfig.CF_VALS:
                    msg_13 = 'Capacity factor fraction attribute value "{}" not in acceptable values of {} for zone {} in file {}.'.format(
                        cfv, ReadConfig.CF_VALS, vid, f)
                    log.error(msg_13)
                    raise ValueError(msg_13)

                cfd = item.cdata

                try:
                    float(cfd)
                except ValueError:
                    msg_14 = 'Capactiy factor "{}" for fraction "{}" in zone {} in file {} is not able to be converted to float.'.format(
                        cfd, cfv, vid, f)
                    log.error(msg_14)
                    raise ValueError(msg_14)

        return z_list

    @staticmethod
    def eval_expansion(f, zones, techs, log):
        """
        Validate expansionplan.xml input data.
        """
        obj = untangle.parse(f)

        # look for root node
        try:
            root = obj.expansionplan
        except AttributeError:
            msg_0 = 'Root node: <expansionplan> is missing or misspelled in file {}. Exiting...'.format(f)
            log.error(msg_0)
            raise AttributeError(msg_0)

        # look for child
        try:
            child = root.expansion
        except AttributeError:
            msg_1 = 'Child node: <expansion> is missing or misspelled in file {}. Exiting...'.format(f)
            log.error(msg_1)
            raise AttributeError(msg_1)

        # validate values
        zids = []
        tids = []
        for v in child:

            zoneid = v['zoneid']
            techid = v['techid']
            exp = v.cdata

            if zoneid is None:
                msg_2 = 'Attribute "zoneid" is missing from <expansion> node in file {}'.format(f)
                log.error(msg_2)
                raise ValueError(msg_2)

            if techid is None:
                msg_3 = 'Attribute "techid" is missing from <expansion> node in file {}'.format(f)
                log.error(msg_3)
                raise ValueError(msg_3)

            if len(exp) < 1:
                msg_4 = 'Expansion value is missing for zoneid "{}", techid "{}" in file {}'.format(zoneid, techid, f)
                log.error(msg_4)
                raise ValueError(msg_4)

            zids.append(zoneid)
            tids.append(techid)

        # check to see if zones in expansion plan match those that are in the powerzones.xml file
        exp_not_zones = [str(a) for a in set(zids) - set(zones)]
        zones_not_exp = [str(b) for b in set(zones) - set(zids)]

        if (len(exp_not_zones) > 0) and (len(zones_not_exp) == 0):
            msg_5 = 'zoneid(s) {} in expansion plan file {} but not in the shapeid for powerzones.xml file.'.format(
                exp_not_zones, f)
            log.error(msg_5)
            raise RuntimeError(msg_5)

        elif (len(zones_not_exp) > 0) and (len(exp_not_zones) == 0):
            msg_6 = 'shapeid(s) {} in the powerzones.xml file but not in the zoneid in the expansion plan file {}'.format(
                zones_not_exp, f)
            log.error(msg_6)
            raise RuntimeError(msg_6)

        elif (len(zones_not_exp) > 0) and (len(exp_not_zones) > 0):
            msg_7 = 'zoneid(s) {} in the expansion plan file but not in the shapeid for the powerzones.xml file and the shapeid(s) {} in the powerzones.xml file and bot tin the zoneid in the expansion plan file {}'.format(
                exp_not_zones, zones_not_exp, f)
            log.error(msg_7)
            raise RuntimeError(msg_7)

        # check to see if techs in expansion plan match those that are in the technologies.xml file
        exp_not_techs = [str(a) for a in set(tids) - set(techs)]
        techs_not_exp = [str(b) for b in set(techs) - set(tids)]

        if (len(exp_not_techs) > 0) and (len(techs_not_exp) == 0):
            msg_8 = 'techid(s) {} in expansion plan file {} but not in the id for technologies.xml file.'.format(
                exp_not_techs, f)
            log.error(msg_8)
            raise RuntimeError(msg_8)

        elif (len(techs_not_exp) > 0) and (len(exp_not_techs) == 0):
            msg_9 = 'id(s) {} in the technologies.xml file but not in the techid in the expansion plan file {}'.format(
                techs_not_exp, f)
            log.error(msg_9)
            raise RuntimeError(msg_9)

        elif (len(techs_not_exp) > 0) and (len(exp_not_techs) > 0):
            msg_10 = 'techid(s) {} in the expansion plan file but not in the id for the technologies.xml file and the id(s) {} in the technologies.xml file and bot tin the techid in the expansion plan file {}'.format(
                exp_not_techs, techs_not_exp, f)
            log.error(msg_10)
            raise RuntimeError(msg_10)

    @staticmethod
    def eval_states(f, log):
        """
        Validate states.xml.
        """

        obj = untangle.parse(f)

        # look for root node
        try:
            root = obj.states
        except AttributeError:
            msg_0 = 'Root node: <states> is missing or misspelled in file {}. Exiting...'.format(f)
            log.error(msg_0)
            raise AttributeError(msg_0)

        # look for child
        try:
            child = root.state
        except AttributeError:
            msg_1 = 'Child node: <state> is missing or misspelled in file {}. Exiting...'.format(f)
            log.error(msg_1)
            raise AttributeError(msg_1)

        for item in child:

            sid = item['id']
            shp = item['shapeid']
            st = item.cdata

            if sid is None:
                msg_2 = 'Attribute "id" is missing from <state> node in file {}'.format(f)
                log.error(msg_2)
                raise ValueError(msg_2)

            if shp is None:
                msg_3 = 'Attribute "shapeid" is missing from <state> node in file {}'.format(f)
                log.error(msg_3)
                raise ValueError(msg_3)

            if len(st) < 1:
                msg_4 = 'State name value is missing for id "{}", shapeid "{}" in file {}'.format(sid, shp, f)
                log.error(msg_4)
                raise ValueError(msg_4)

            try:
                int(sid)
            except ValueError:
                msg_5 = 'Value "{}" for id in <state> node for shapeid "{}" in file {} should be a number greater than 0 as a string (e.g., "1")'.format(
                    sid, shp, f)
                log.error(msg_5)
                raise ValueError(msg_5)

            try:
                int(shp)
            except ValueError:
                msg_6 = 'Value "{}" for shapeid in <state> node for id "{}" in file {} should be a number greater than 0 as a string (e.g., "1")'.format(
                    shp, sid, f)
                log.error(msg_6)
                raise ValueError(msg_6)

    @staticmethod
    def eval_tech_paths(f, techs, log):
        """
        Validate technologies.xml.
        """

        obj = untangle.parse(f)

        # look for root node
        try:
            root = obj.suitabilitymasks
        except AttributeError:
            msg_0 = 'Root node: <suitabilitymasks> is missing or misspelled in file {}. Exiting...'.format(f)
            log.error(msg_0)
            raise AttributeError(msg_0)

        # look for child
        try:
            child = root.mask
        except AttributeError:
            msg_1 = 'Child node: <mask> is missing or misspelled in file {}. Exiting...'.format(f)
            log.error(msg_1)
            raise AttributeError(msg_1)

        t_list = []
        for item in child:

            tech = item['techid']
            pth = item.cdata

            if tech is None:
                msg_2 = 'Attribute "techid" is missing from <mask> node in file {}'.format(f)
                log.error(msg_2)
                raise ValueError(msg_2)

            t_list.append(tech)

            # validate path to suitability file
            ReadConfig.check_exist(pth, 'file', log)

        # check to see if techs in file are in technologies.xml
        pth_not_techs = [str(a) for a in set(t_list) - set(techs)]
        techs_not_pth = [str(b) for b in set(techs) - set(t_list)]

        if (len(pth_not_techs) > 0) and (len(techs_not_pth) == 0):
            msg_3 = 'Techid {} in {} but not in technologies.xml'.format(pth_not_techs, f)
            log.error(msg_3)
            raise RuntimeError(msg_3)

        elif (len(techs_not_pth) > 0) and (len(pth_not_techs) == 0):
            msg_4 = 'Techid {} in technologies.xml but not in {}'.format(techs_not_pth, f)
            log.error(msg_4)
            raise RuntimeError(msg_4)

        elif (len(techs_not_pth) > 0) and (len(pth_not_techs) > 0):
            msg_5 = 'Techid {0} in technologies.xml but not in {1} and techid {2} in {1} but not in technologies.xml'.format(
                techs_not_pth, f, pth_not_techs)
            log.error(msg_5)
            raise RuntimeError(msg_5)