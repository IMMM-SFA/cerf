"""
Model wrapper for CERF C++ executable.

Copyright (c) 2017, Battelle Memorial Institute

Open source under license BSD 2-Clause - see LICENSE and DISCLAIMER

@author:  Chris R. Vernon (chris.vernon@pnnl.gov)
"""

import subprocess

class CERF:

    def __init__(self, p):

        call = ['cmd.exe',
                p.exe_path,
                'siting_model',
                0,
                p.buffer,
                1,
                p.utility_zones,
                p.common_exclusion,
                p.transmission_230kv,
                p.transmission_345kv,
                p.transmission_500kv,
                p.transmission_765kv,
                p.gasline_16in,
                '-WINDCAPINPUT "//olympus/projects/iresm/a_cms/prima/RCP8.5/cerf/actual_inputs/erdasimg_windenergy/platts_ewits_2005_potential_onshore_wind_sites_gwh_conus.img"'
                p.primary_zones,
                p.out_path,
                p.xml_path,
                p.distance_method,
                p.direction_method,
                ]

        subprocess.call(['cmd.exe', p.exe_path, p.buffer, p.yr, p.utility_zones, p.])