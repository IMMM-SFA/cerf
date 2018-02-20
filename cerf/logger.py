"""
Logger for CERF model.

Copyright (c) 2018, Battelle Memorial Institute

Open source under license BSD 2-Clause - see LICENSE and DISCLAIMER

@author:  Chris R. Vernon (chris.vernon@pnnl.gov)
"""

import datetime
import logging
import sys


loggers = {}


def make_log(out_dir):
    """
    Create a log file and console log handler.

    :param:         full path to output dir where the log file is to be saved.
    """

    global loggers

    nm = 'cerf_logger'

    if loggers.get(nm):
        return loggers.get(nm)

    else:
        log = logging.getLogger(nm)
        log.setLevel(logging.INFO)

        dt = datetime.datetime.now().strftime('%Y-%m-%d_%Hh%Mm%Ss')

        # file handler
        fh = logging.FileHandler('{}/cerf_{}.log'.format(out_dir, dt))

        # stream handler
        cns = logging.StreamHandler(sys.stdout)

        # logger string format
        fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # set format
        fh.setFormatter(fmt)
        cns.setFormatter(fmt)

        log.addHandler(fh)
        log.addHandler(cns)

        loggers.update(dict(name=log))

        return log


def kill_log(log):
    """
    Remove any existing handlers.

    :param:         log object
    """
    handlers = log.handlers[:]
    for h in handlers:
        h.close()
        log.removeHandler(h)
