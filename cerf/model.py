"""
Model wrapper for CERF C++ executable.

Copyright (c) 2017, Battelle Memorial Institute

Open source under license BSD 2-Clause - see LICENSE and DISCLAIMER

@author:  Chris R. Vernon (chris.vernon@pnnl.gov)
"""

import subprocess

from config_reader import ReadConfig


class CERF:
    def __init__(self, p):
        s = ['cmd.exe /K',
             '"{}"'.format(p.exe_path),
             'siting_model 0',
             '-BUFFER {}'.format(p.buffer),
             '-YEAR {}'.format(p.yr),
             '-NORM {}'.format(p.distance_method),
             '-DIRECTION {}'.format(p.direction_method),
             '-SECONDARYGRID "{}"'.format(p.utility_zones),
             '-SUITABILITYMASK "{}"'.format(p.common_exclusion),
             '-TRANSMISSIONINPUT230 "{}"'.format(p.transmission_230kv),
             '-TRANSMISSIONINPUT345 "{}"'.format(p.transmission_345kv),
             '-TRANSMISSIONINPUT500 "{}"'.format(p.transmission_500kv),
             '-TRANSMISSIONINPUT765 "{}"'.format(p.transmission_765kv),
             '-GASINPUT16 "{}"'.format(p.gasline_16in),
             '-SHAPES "{}"'.format(p.primary_zone),
             '-OUTPUTDIRECTORY "{}"'.format(p.out_path),
             '-IOXMLDIRECTORY "{}"'.format(p.xml_path)]

        call_string = ' '.join(s)

        print('processing...')
        subprocess.call(call_string)


if __name__ == "__main__":

    ini = 'C:/Users/d3y010/Desktop/vernon/repos/github/cerf/example/config.ini'

    params = ReadConfig(ini)

    CERF(params)