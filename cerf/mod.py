
import logger

import cerf.utils as util


from cerf.read_config import ReadConfig
from cerf.stage import Stage
from cerf.process_state import ProcessState


class Model(ReadConfig):

    def __init__(self, config_file):

        super(Model, self).__init__(config_file)

        self.technology_dict = self.config.get('technology')

        print('staging')
        self.data = Stage(self.config, self.technology_dict, self.technology_order)

        print('processing state')
        self.sited_arr = ProcessState(self.config, self.data, self.technology_dict, self.technology_order, target_state_id=45)

        out_raster = '/Users/d3y010/Desktop/nlc/out_2010_va.tif'
        util.array_to_raster(self.sited_arr, self.config['settings']['states_raster_file'], out_raster)






import pkg_resources

c = pkg_resources.resource_filename('cerf', 'tests/data/config.yml')
m = Model(c)


