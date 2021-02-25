
import logger
import numpy as np
import rasterio

from cerf.read_config import ReadConfig
from cerf.stage import Stage
from cerf.process_state import ProcessState


class Model(ReadConfig):

    def __init__(self, config_file):

        super(Model, self).__init__(config_file)

        self.technology_dict = self.config.get('technology')

        self.data = Stage(self.config, self.technology_dict, self.technology_order)

        state_arr = ProcessState(self.config, self.data, self.technology_dict, self.technology_order, target_state_id=45)








import pkg_resources

c = pkg_resources.resource_filename('cerf', 'tests/data/config.yml')
m = Model(c)


