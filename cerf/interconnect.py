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
from cerf.package_data import cerf_crs, costs_per_kv_substation


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

    :param costs_to_connect_dict:           A dictionary containing the cost of connection per km to a substation
                                            having a certain minimum voltage range.  Default is to load from the
                                            CERF data file 'costs_per_kv_substation.yml' by specifying 'None'

    :type costs_to_connect_dict:            dict

    :param costs_to_connect_file:           A YAML file containing the cost of connection per km to a substation
                                            having a certain minimum voltage range.  Default is to load from the
                                            CERF data file 'costs_per_kv_substation.yml' by specifying 'None'

    :type costs_to_connect_file:            str

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

    :param transmission_gdf:                GeoDataFrame of transmission infrastructure to be rasterized. If None
                                            the 'process_hifld_substations' method will generate the data either based
                                            off of the 'substation_file' or using the default CERF data.
    :type transmission_gdf:                 GeoDataFrame

    :param output_dir:                      Full path to a directory to write outputs to if desired
    :type output_dir:                       str

    """

    # cost of gas pipeline in $2015/km
    GAS_PIPE_COST = 737000

    def __init__(self, template_array, technology_dict, technology_order, substation_file=None,
                 costs_to_connect_dict=None, costs_to_connect_file=None, pipeline_file=None,
                 output_rasterized_file=False, output_dist_file=False, output_alloc_file=False, output_cost_file=False,
                 transmission_gdf=None, output_dir=None):

        self.template_array = template_array
        self.technology_dict = technology_dict
        self.technology_order = technology_order
        self.substation_file = substation_file
        self.costs_to_connect_dict = costs_to_connect_dict
        self.costs_to_connect_file = costs_to_connect_file
        self.pipeline_file = pipeline_file
        self.output_rasterized_file = output_rasterized_file
        self.output_dist_file = output_dist_file
        self.output_alloc_file = output_alloc_file
        self.output_cost_file = output_cost_file
        self.transmission_gdf = transmission_gdf
        self.output_dir = output_dir

    @staticmethod
    def calc_annuity_factor(discount_rate, lifetime):
        """Calculate annuity factor."""

        fx = pow(1.0 + discount_rate, lifetime)

        return discount_rate * fx / (fx - 1.0)

    def process_hifld_substations(self):
        """Select substations from HIFLD data that are within the CONUS and either in service or under construction and
        having a minimum voltage rating >= 0.  A field used to rasterize ('_rval_') is also added containing the cost of
        connection in $/km for each substation.

        This data is assumed to have the following fields:  ['TYPE', 'STATE', 'STATUS'].

        :returns:                               A geodataframe containing the target substations

        """

        # load cost dictionary from package data if none passed
        if (self.costs_to_connect_dict is None) and (self.costs_to_connect_file is None):
            self.costs_to_connect_dict = costs_per_kv_substation()

        elif self.costs_to_connect_file is not None:
            with open(self.costs_to_connect_file, 'r') as yml:
                self.costs_to_connect_dict = yaml.load(yml, Loader=yaml.FullLoader)

        if self.substation_file is None:
            return gpd.read_file(pkg_resources.resource_filename('cerf', 'data/hifld_substations_conus_albers.zip'))

        else:

            # get state abbreviations file from cerf package data
            states_file = pkg_resources.resource_filename('cerf', 'data/state-abbrev_to_state-name.yml')

            # get state abbreviations to search for in HIFLD data
            with open(states_file, 'r') as yml:
                states = yaml.load(yml, Loader=yaml.FullLoader)

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

            for i in self.costs_to_connect_dict.keys():
                gdf['_rval_'] = np.where((gdf['MIN_VOLT'] >= self.costs_to_connect_dict[i]['min_voltage']) &
                                         (gdf['MIN_VOLT'] <= self.costs_to_connect_dict[i]['max_voltage']),
                                         self.costs_to_connect_dict[i]['dollar_per_km'],
                                         gdf['_rval_'])

            return gdf

    def process_eia_natural_gas_pipelines(self):
        """Select natural gas pipelines from EIA data that have a status of operating and a length greater than 0.

        :returns:                               A geodataframe containing the target pipelines

        """

        if self.pipeline_file is None:
            return gpd.read_file(
                pkg_resources.resource_filename('cerf', 'data/eia_natural_gas_pipelines_conus_albers.zip'))

        else:

            # load cerf's default coordinate reference system object
            target_crs = cerf_crs()

            # read in data and reproject
            gdf = gpd.read_file(self.pipeline_file).to_crs(target_crs)

            # only keep features with a length > 0
            gdf = gdf.loc[gdf.geometry.length > 0].copy()

            # only keep operational pipelines
            gdf = gdf.loc[gdf['Status'] == 'Operating'].copy()

            # set field for rasterize
            gdf['_rval_'] = self.GAS_PIPE_COST

            return gdf

    def transmission_to_cost_raster(self, setting):
        """Create a cost per grid cell in $/km from the input GeoDataFrame of transmission infrastructure having a cost
        designation field as '_rval_'

        :param setting:                         Either 'substations' or 'pipelines'

        :return:                                Array of transmission interconnection cost per grid cell

        """
        # conversion factor for meters to km
        m_to_km_factor = 0.001

        if self.transmission_gdf is None:

            if setting == 'substations':
                self.transmission_gdf = self.process_hifld_substations()

            elif setting == 'pipelines':
                self.transmission_gdf = self.process_eia_natural_gas_pipelines()

            else:
                raise KeyError(f"'setting' value '{setting}' not supported. Choose either 'substations' or 'pipelines'")

        # instantiate whitebox toolset
        wbt = whitebox.WhiteboxTools()

        # get the template raster from CERF data
        template_raster = pkg_resources.resource_filename('cerf', 'data/cerf_conus_states_albers_1km.tif')

        with rasterio.open(template_raster) as src:
            # create 0 where land array
            arr = (src.read(1) * 0).astype(rasterio.float64)

            # update metadata datatype to float64
            metadata = src.meta.copy()
            metadata.update({'dtype': rasterio.float64})

            # reproject transmission data
            gdf = self.transmission_gdf.to_crs(src.crs)

            # get shapes
            shapes = ((geom, value) for geom, value in zip(gdf.geometry, gdf['_rval_']))

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
            substation_cost_array = self.transmission_to_cost_raster(setting='substations') * annuity_factor

            if require_pipelines:

                # get pipeline cost array
                pipeline_cost_array = self.transmission_to_cost_raster(setting='pipelines') * annuity_factor

                # calculate technology specific interconnection cost
                total_interconection_cost_array = substation_cost_array + pipeline_cost_array

            else:
                total_interconection_cost_array = substation_cost_array

            # calculate interconnection costs per grid cell
            ic_arr[index, :, :] = total_interconection_cost_array

        return ic_arr
