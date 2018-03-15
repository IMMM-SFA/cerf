"""
Model wrapper for CERF C++ executable.

Copyright (c) 2018, Battelle Memorial Institute

Open source under license BSD 2-Clause - see LICENSE and DISCLAIMER

@author:  Chris R. Vernon (chris.vernon@pnnl.gov)

SAGA-CERF C++ core module developed by Nino Zuljevic (nino.zuljevic@pnnl.gov)
"""

import os
import subprocess
import shlex
import logger

from config_reader import ReadConfig


class Cerf:

    # a list of the first five characters for relevant strings to log
    CAPTURE = ['libr', 'modu', 'auth', 'set ', 'save',
               'buff', '4-di', 'suit', 'seco', 'shap', 'outp',
               'inpu', 'type', 'dire', 'disc', 'carb', 'tx_l', 'inte', 'file',
               'cell', 'expa', 'curr']

    def __init__(self, ini):

        self.p = ReadConfig(ini)
        self.cwd = os.path.dirname(self.p.exe_path)
        self.log = self.p.log

        # build arguments for SAGA module
        s = ['{}'.format(self.p.exe_path),
             'siting_model 0',
             '-BUFFER {}'.format(self.p.buffer),
             '-YEAR {}'.format(self.p.yr),
             '-NORM {}'.format(self.p.distance_method),
             '-DIRECTION {}'.format(self.p.direction_method),
             '-SECONDARYGRID "{}"'.format(self.p.utility_zones),
             '-SUITABILITYMASK "{}"'.format(self.p.common_exclusion),
             '-TRANSMISSIONINPUT230 "{}"'.format(self.p.transmission_230kv),
             '-TRANSMISSIONINPUT345 "{}"'.format(self.p.transmission_345kv),
             '-TRANSMISSIONINPUT500 "{}"'.format(self.p.transmission_500kv),
             '-TRANSMISSIONINPUT765 "{}"'.format(self.p.transmission_765kv),
             '-GASINPUT16 "{}"'.format(self.p.gasline_16in),
             '-SHAPES "{}"'.format(self.p.primary_zone),
             '-OUTPUTDIRECTORY "{}"'.format(self.p.out_path),
             '-IOXMLDIRECTORY "{}"'.format(self.p.xml_path)]

        # join arguments by space
        self.command = ' '.join(s)

    def run_saga(self):
        """
        Run subprocess call to the C++ SAGA custom executable from the executables
        root directory. Log the output as it becomes available instead of
        waiting until completion.
        """
        # start process
        process = subprocess.Popen(shlex.split(self.command), stdout=subprocess.PIPE, cwd=self.cwd)

        x = 0
        while True and x < 10:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                x += 1
                break
            if output:
                out_string = output.strip()

                # only log relevant info
                if (len(out_string) > 0) and (out_string[:4].lower() in Cerf.CAPTURE):
                    self.log.info(out_string)

        rc = process.poll()
        return rc
        
    def execute(self):
        """
        Run CERF based on config file params.
        """
        self.log.info('Start siting model...')
        
        # run command as subprocess
        self.run_saga()

        self.log.info('Siting model completed.')

        # remove any handlers that may exist
        logger.kill_log(self.log)