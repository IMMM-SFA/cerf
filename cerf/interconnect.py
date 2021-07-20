import os
import logging
import pkg_resources
import tempfile

import rasterio
import whitebox
import yaml

import numpy as np
import geopandas as gpd

from rasterio import features

from cerf.utils import suppress_callback
from cerf.package_data import cerf_crs, costs_per_kv_substation, get_state_abbrev_to_name

# instantiate whitebox toolset
wbt = whitebox.WhiteboxTools()


class Interconnection:
    """Calculate interconnection costs per grid cell in $ / yr using:

    Interconnection Cost ($ / yr) = Distance to nearest suitable transmission line (km) *
                                        Electric grid interconnection captial cost ($ / km) *
                                        Annuity factor
                                        + (if gas-fired technology) Distance to nearest suitable gas pipeline (km) *
                                        Gas interconnection captial cost ($ / km) *
                                        Annuity factor

            where, Annuity factor is (d(1 + d)**n) / ((1 + d)**n - 1)
            where, d = real annual discount rate (%), n = asset lifetime (years)


    :param technology_dict:                 Dictionary containing technology specific information from the config file
    :type technology_dict:                  dict

    :param technology_order:                Order of technologies to process
    :type technology_order:                 list

    :param substation_file:                 Full path with file name and extension to the input substations shapefile.
                                            If None, CERF will use the default data stored in the package.

    :type substation_file:                  str

    :param transmission_costs_dict:         A dictionary containing the cost of connection per km to a substation
                                            having a certain minimum voltage range.  Default is to load from the
                                            CERF data file 'costs_per_kv_substation.yml' by specifying 'None'

    :type transmission_costs_dict:          dict

    :param transmission_costs_file:         A YAML file containing the cost of connection per km to a substation
                                            having a certain minimum voltage range.  Default is to load from the
                                            CERF data file 'costs_per_kv_substation.yml' by specifying 'None'

    :type transmission_costs_file:          str

    :param pipeline_costs_dict:             A dictionary containing the cost of connection per km to a gas pipeline.
                                            Default is to load from the CERF data file 'costs_gas_pipeline.yml' by
                                            specifying 'None'

    :type pipeline_costs_dict:              dict

    :param pipeline_costs_file:             A YAML file containing the cost of connection per km to a gas pipeline.
                                            Default is to load from the CERF data file 'costs_gas_pipeline.yml' by
                                            specifying 'None'

    :type pipeline_costs_file:              str


    :param pipeline_file:                   Full path with file name and extension to the input pipelines shapefile.
                                            If None, CERF will use the default data stored in the package.

    :type pipeline_file:                    str

    :param output_rasterized_file:          Write distance raster; if True, set 'output_dir' value
    :type output_rasterized_file:           bool

    :param output_dist_file:                Write distance raster; if True, set 'output_dir' value
    :type output_dist_file:                 bool

    :param output_alloc_file:               Write allocation file; if True, set 'output_dir' value
    :type output_alloc_file:                bool

    :param output_cost_file:                Write cost file; if True, set 'output_dir' value
    :type output_cost_file:                 bool
    
    :param interconnection_cost_file:       Full path with file name and extension to a preprocessed interconnection
                                            cost NPY file that has been previously written. If None, IC will be 
                                            calculated.
    :type interconnection_cost_file:        str 

    :param output_dir:                      Full path to a directory to write outputs to if desired
    :type output_dir:                       str

    """

    def __init__(self, template_array, technology_dict, technology_order, substation_file=None,
                 transmission_costs_dict=None, transmission_costs_file=None, pipeline_costs_dict=None, 
                 pipeline_costs_file=None,pipeline_file=None, output_rasterized_file=False, output_dist_file=False, 
                 output_alloc_file=False, output_cost_file=False, interconnection_cost_file=None, output_dir=None):

        self.template_array = template_array
        self.technology_dict = technology_dict
        self.technology_order = technology_order
        self.substation_file = substation_file
        self.transmission_costs_dict = transmission_costs_dict
        self.transmission_costs_file = transmission_costs_file
        self.pipeline_costs_dict = pipeline_costs_dict
        self.pipeline_costs_file = pipeline_costs_file
        self.pipeline_file = pipeline_file
        self.output_rasterized_file = output_rasterized_file
        self.output_dist_file = output_dist_file
        self.output_alloc_file = output_alloc_file
        self.output_cost_file = output_cost_file
        self.interconnection_cost_file = interconnection_cost_file
        self.output_dir = output_dir

        # calculate electricity transmission infrastructure costs
        self.substation_costs = self.transmission_to_cost_raster(setting='substations')

        # if there are any gas technlogies present, calculate gas pipeline infrastructure costs
        self.pipeline_costs = self.transmission_to_cost_raster(setting='pipelines')

    @staticmethod
    def calc_annuity_factor(discount_rate, lifetime):
        """Calculate annuity factor."""

        fx = pow(1.0 + discount_rate, lifetime)

        return discount_rate * fx / (fx - 1.0)

    def get_pipeline_costs(self):
        """Get the costs of gas pipeline interconnection per kilometer."""

        if self.pipeline_costs_dict is not None:
            logging.info(f"Using gas pipeline costs from user defined dictionary:  {self.pipeline_costs_dict}")
            return self.pipeline_costs_dict.get('gas_pipeline_cost')

        if self.pipeline_costs_file is not None:
            f = self.pipeline_costs_file
            logging.info(f"Using gas pipeline costs from file:  {f}")

        else:
            f = pkg_resources.resource_filename('cerf', 'data/costs_gas_pipeline.yml')
            logging.info(f"Using gas pipeline costs from default file:  {f}")

        with open(f, 'r') as yml:
            yaml_dict = yaml.load(yml, Loader=yaml.FullLoader)

        return yaml_dict.get('gas_pipeline_cost')

    def process_hifld_substations(self):
        """Select substations from HIFLD data that are within the CONUS and either in service or under construction and
        having a minimum voltage rating >= 0.  A field used to rasterize ('_rval_') is also added containing the cost of
        connection in $/km for each substation.

        This data is assumed to have the following fields:  ['TYPE', 'STATE', 'STATUS'].

        :returns:                               A geodataframe containing the target substations

        """

        # load cost dictionary from package data if none passed
        if (self.transmission_costs_dict is None) and (self.transmission_costs_file is None):
            default_kv_file = pkg_resources.resource_filename('cerf', 'data/costs_per_kv_substation.yml')

            logging.info(f"Using default substations costs from file: {default_kv_file}")

            self.transmission_costs_dict = costs_per_kv_substation()

        elif self.transmission_costs_file is not None:

            logging.info(f"Using substations costs from file: {self.transmission_costs_file}")

            with open(self.transmission_costs_file, 'r') as yml:
                self.transmission_costs_dict = yaml.load(yml, Loader=yaml.FullLoader)

        if self.substation_file is None:

            sub_file = pkg_resources.resource_filename('cerf', 'data/hifld_substations_conus_albers.zip')

            logging.info(f"Using default substation file: {sub_file}")

            return gpd.read_file(sub_file)

        else:

            logging.info(f"Using substation file: {self.substation_file}")

            # get state abbreviations file from cerf package data
            states = get_state_abbrev_to_name()

            # load cerf's default coordinate reference system object
            target_crs = cerf_crs()

            # load and reproject
            gdf = gpd.read_file(self.substation_file).to_crs(target_crs)

            # keep only substations in the CONUS that are either in service or under construction
            gdf = gdf.loc[(gdf['TYPE'] == 'SUBSTATION') &
                          (gdf['STATE'].isin(states.keys())) &
                          (gdf['STATUS'].isin(('IN SERVICE', 'UNDER CONST')))].copy()

            # assign a field to rasterize by containing the cost of transmission per km
            gdf['_rval_'] = 0

            for i in self.transmission_costs_dict.keys():
                gdf['_rval_'] = np.where((gdf['MIN_VOLT'] >= self.transmission_costs_dict[i]['min_voltage']) &
                                         (gdf['MIN_VOLT'] <= self.transmission_costs_dict[i]['max_voltage']),
                                         self.transmission_costs_dict[i]['dollar_per_km'],
                                         gdf['_rval_'])

            return gdf

    def process_eia_natural_gas_pipelines(self):
        """Select natural gas pipelines from EIA data that have a status of operating and a length greater than 0.

        :returns:                               A geodataframe containing the target pipelines

        """

        if self.pipeline_file is None:

            f = pkg_resources.resource_filename('cerf', 'data/eia_natural_gas_pipelines_conus_albers.zip')

            logging.info(f"Using default gas pipeline file:  {f}")

            # read in default shapefile for pipelines
            gdf = gpd.read_file(f)

            # set field for rasterize
            gdf['_rval_'] = self.get_pipeline_costs()

            return gdf

        else:

            logging.info(f"Using gas pipeline file:  {self.pipeline_file}")

            # load cerf's default coordinate reference system object
            target_crs = cerf_crs()

            # read in data and reproject
            gdf = gpd.read_file(self.pipeline_file).to_crs(target_crs)

            # only keep features with a length > 0
            gdf = gdf.loc[gdf.geometry.length > 0].copy()

            # only keep operational pipelines
            gdf = gdf.loc[gdf['Status'] == 'Operating'].copy()

            # set field for rasterize
            gdf['_rval_'] = self.get_pipeline_costs()

            return gdf

    def transmission_to_cost_raster(self, setting):
        """Create a cost per grid cell in $/km from the input GeoDataFrame of transmission infrastructure having a cost
        designation field as '_rval_'

        :param setting:                         Either 'substations' or 'pipelines'
        :type setting:                          str

        :return:                                Array of transmission interconnection cost per grid cell

        """
        # conversion factor for meters to km
        m_to_km_factor = 0.001

        if setting == 'substations':
            gdf = self.process_hifld_substations()

        elif setting == 'pipelines':
            gdf = self.process_eia_natural_gas_pipelines()

        else:
            raise ValueError(f"Incorrect setting '{setting}' for transmission data.  Must be 'substations' or 'pipelines'")

        # get the template raster from CERF data
        template_raster = pkg_resources.resource_filename('cerf', 'data/cerf_conus_states_albers_1km.tif')

        with rasterio.open(template_raster) as src:
            # create 0 where land array
            arr = (src.read(1) * 0).astype(rasterio.float64)

            # update metadata datatype to float64
            metadata = src.meta.copy()
            metadata.update({'dtype': rasterio.float64})

            # reproject transmission data
            infrastructure_gdf = gdf.to_crs(src.crs)

            # get shapes
            shapes = ((geom, value) for geom, value in zip(infrastructure_gdf.geometry, infrastructure_gdf['_rval_']))

        with tempfile.TemporaryDirectory() as tempdir:

            # if write desired
            if any((self.output_rasterized_file, self.output_dist_file, self.output_alloc_file, self.output_cost_file)):

                if self.output_dir is None:
                    msg = "If writing rasters to file must specify 'output_dir'"
                    logging.error(msg)
                    raise NotADirectoryError(msg)

                else:
                    out_rast = os.path.join(self.output_dir, f'cerf_transmission_raster_{setting}.tif')
                    out_dist = os.path.join(self.output_dir, f'cerf_transmission_distance_{setting}.tif')
                    out_alloc = os.path.join(self.output_dir, f'cerf_transmission_allocation_{setting}.tif')
                    out_costs = os.path.join(self.output_dir, f'cerf_transmission_costs_{setting}.tif')
            else:
                out_rast = os.path.join(tempdir, f'cerf_transmission_raster_{setting}.tif')
                out_dist = os.path.join(tempdir, f'cerf_transmission_distance_{setting}.tif')
                out_alloc = os.path.join(tempdir, f'cerf_transmission_allocation_{setting}.tif')
                out_costs = os.path.join(tempdir, f'cerf_transmission_costs_{setting}.tif')

            # rasterize transmission vector data and write to memory
            with rasterio.open(out_rast, 'w', **metadata) as dataset:
                # burn features into raster
                burned = features.rasterize(shapes=shapes, fill=0, out=arr, transform=dataset.transform)

                # write the outputs to file
                dataset.write_band(1, burned)

            # calculate Euclidean distance and write raster; result just stores the return value 0
            dist_result = wbt.euclidean_distance(out_rast, out_dist, callback=suppress_callback)

            # calculate Euclidean allocation and write raster
            alloc_result = wbt.euclidean_allocation(out_rast, out_alloc, callback=suppress_callback)

            with rasterio.open(out_dist) as dist:
                dist_arr = dist.read(1)

            with rasterio.open(out_alloc) as alloc:
                alloc_arr = alloc.read(1)

            with rasterio.open(out_costs, 'w', **metadata) as out:

                # distance in km * the cost of the nearest substation; outputs $/km
                cost_arr = (dist_arr * m_to_km_factor) * alloc_arr

                out.write(cost_arr, 1)

        return cost_arr

    def generate_interconnection_costs_array(self):
        """Calculate the costs of interconnection for each technology."""
        
        # if a preprocessed file has been provided, load and return it
        if self.interconnection_cost_file is not None:

            logging.info(f"Using prebuilt interconnection costs file:  {self.interconnection_cost_file}")
            return np.load(self.interconnection_cost_file)

        # set up array to hold interconnection costs
        ic_arr = np.zeros_like(self.template_array)

        for index, i in enumerate(self.technology_order):

            # get technology specific information
            require_pipelines = self.technology_dict[i].get('require_pipelines', False)
            discount_rate = self.technology_dict[i].get('discount_rate')
            lifetime = self.technology_dict[i].get('lifetime')

            # calulate annuity factor for technology
            annuity_factor = self.calc_annuity_factor(discount_rate=discount_rate, lifetime=lifetime)

            # get transmission cost array
            substation_cost_array = self.substation_costs * annuity_factor

            if require_pipelines:

                # get pipeline cost array
                pipeline_cost_array = self.pipeline_costs * annuity_factor

                # calculate technology specific interconnection cost
                total_interconection_cost_array = substation_cost_array + pipeline_cost_array

            else:
                total_interconection_cost_array = substation_cost_array

            # calculate interconnection costs per grid cell
            ic_arr[index, :, :] = total_interconection_cost_array

        return ic_arr
