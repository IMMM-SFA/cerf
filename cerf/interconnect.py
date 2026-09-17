import os
import logging

import geopandas as gpd
import numpy as np
import rasterio
import shapely
from rasterio import features
from scipy.ndimage import distance_transform_edt
from shapely.geometry import mapping
import yaml

import cerf.package_data as pkg
from cerf.nov import NetOperationalValue
from cerf.utils import suppress_callback

logger = logging.getLogger(__name__)


class Interconnection:
    """Calculate interconnection costs per grid cell in $ / yr using:

    Interconnection Cost ($ / yr) = Distance to nearest suitable transmission line (km) *
                                        Electric grid interconnection captial cost (thous$ / km) *
                                        Annuity factor
                                        + (if gas-fired technology) Distance to nearest suitable gas pipeline (km) *
                                        Gas interconnection captial cost (thous$ / km) *
                                        Annuity factor

            where, Annuity factor is (d(1 + d)**n) / ((1 + d)**n - 1)
            where, d = real annual discount rate (%), n = asset lifetime (years)


    :param technology_dict:                 Dictionary containing technology specific information from the config file
    :type technology_dict:                  dict

    :param technology_order:                Order of technologies to process
    :type technology_order:                 list

    :param region_raster_file:              Full path with file name and extension to the region raster file that
                                            assigns a region ID to each raster grid cell
    :type region_raster_file:               str

    :param region_abbrev_to_name_file:      Full path with file name and extension to the region abbreviation to name
                                            YAML reference file
    :type region_abbrev_to_name_file:       str

    :param region_name_to_id_file:          Full path with file name and extension to the region name to ID YAML
                                            reference file
    :type region_name_to_id_file:           str

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

    def __init__(self, template_array, technology_dict, technology_order, region_raster_file,
                 region_abbrev_to_name_file, region_name_to_id_file, substation_file=None,
                 transmission_costs_dict=None, transmission_costs_file=None, pipeline_costs_dict=None,
                 pipeline_costs_file=None, pipeline_file=None, output_rasterized_file=False, output_dist_file=False,
                 output_alloc_file=False, output_cost_file=False, interconnection_cost_file=None, output_dir=None):

        self.template_array = template_array
        self.technology_dict = technology_dict
        self.technology_order = technology_order
        self.region_raster_file = region_raster_file
        self.region_abbrev_to_name_file = region_abbrev_to_name_file
        self.region_name_to_id_file = region_name_to_id_file
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
    def calc_annuity_factor(discount_rate, lifetime_yrs):
        """Calculate annuity factor. Delegates to the shared implementation in
        :meth:`cerf.nov.NetOperationalValue.annuity_factor_from` so that interconnection and NOV
        always use identical financial factors, including the zero-discount-rate limit."""

        return NetOperationalValue.annuity_factor_from(discount_rate, lifetime_yrs)

    def get_pipeline_costs(self):
        """Get the costs of gas pipeline interconnection per kilometer."""

        if self.pipeline_costs_dict is not None:
            logger.info(f"Using gas pipeline costs from user defined dictionary:  {self.pipeline_costs_dict}")
            return self.pipeline_costs_dict.get('gas_pipeline_cost')

        if self.pipeline_costs_file is not None:
            f = self.pipeline_costs_file
            logger.info(f"Using gas pipeline costs from file:  {f}")

        else:
            f = pkg.get_costs_gas_pipeline()
            logger.info(f"Using gas pipeline costs from default file:  {f}")

        with open(f, 'r') as yml:
            yaml_dict = yaml.load(yml, Loader=yaml.FullLoader)

        return yaml_dict.get('gas_pipeline_cost')

    def process_substations(self):
        """Process input substations from shapefile."""

        # load cost dictionary from package data if none passed
        if (self.transmission_costs_dict is None) and (self.transmission_costs_file is None):
            default_kv_file = pkg.get_costs_per_kv_substation_file()

            logger.info(f"Using default substation costs from file: {default_kv_file}")

            self.transmission_costs_dict = pkg.costs_per_kv_substation()

        elif self.transmission_costs_file is not None:
            logger.info(f"Using substation costs from file: {self.transmission_costs_file}")

            with open(self.transmission_costs_file, 'r') as yml:
                self.transmission_costs_dict = yaml.load(yml, Loader=yaml.FullLoader)

        if self.substation_file is None:
            sub_file = pkg.get_substation_file()

            logger.info(f"Using default substation file: {sub_file}")

            return gpd.read_file(sub_file)

        else:

            logger.info(f"Using substation file: {self.substation_file}")

            # load file
            gdf = gpd.read_file(self.substation_file)

            # detect existing raster value binning for rasterization
            if '_rval_' in gdf.columns:

                logger.info("Using current '_rval_' field found in substation file which is used in rasterization.")
                logger.info("If '_rval_' field was included unintentionally, please remove from file and re-run.")

                return gdf

            else:

                # make all column names lower case
                gdf.columns = [i.lower() for i in gdf.columns]

                # assign a field to rasterize by containing the cost of transmission per km; raises KeyError if
                #  the required `min_volt` field is absent
                return assign_substation_costs(gdf, self.transmission_costs_dict)

    def process_pipelines(self):
        """Select natural gas pipelines data that have a length greater than 0.

        :returns:                               A geodataframe containing the target pipelines

        """

        if self.pipeline_file is None:

            f = pkg.get_default_gas_pipelines()

            logger.info(f"Using default gas pipeline file:  {f}")

            # read in default shapefile for pipelines
            gdf = gpd.read_file(f)

            # set field for rasterize
            gdf['_rval_'] = self.get_pipeline_costs()

            return gdf

        else:

            logger.info(f"Using gas pipeline file:  {self.pipeline_file}")

            # read in data and reproject
            gdf = gpd.read_file(self.pipeline_file)

            # only keep features with a length > 0
            gdf = gdf.loc[gdf.geometry.length > 0].copy()

            # set field for rasterize
            gdf['_rval_'] = self.get_pipeline_costs()

            return gdf


    @staticmethod
    def pixel_size_km(res, crs):
        """Return the ``(row, col)`` pixel size of a raster in kilometres.

        The interconnection costs are specified in thous$/km, so the Euclidean distance to the nearest
        infrastructure must be measured in kilometres regardless of the raster resolution. The raster CRS must be
        projected (as the packaged Albers rasters are); its linear unit (metre, foot, ...) is converted to
        kilometres. A geographic CRS has no meaningful per-pixel distance and is rejected.

        :param res:                             ``(x_res, y_res)`` pixel size in CRS units, as ``rasterio``'s
                                                ``dataset.res``
        :type res:                              tuple

        :param crs:                             ``rasterio.crs.CRS`` of the raster (``None`` is rejected)

        :return:                                ``(pixel_height_km, pixel_width_km)`` in array (row, col) order,
                                                suitable for ``scipy.ndimage.distance_transform_edt(sampling=...)``

        """

        if crs is None:
            raise ValueError("The region raster has no CRS; a projected CRS is required to compute interconnection "
                             "distances in kilometres.")

        if crs.is_geographic or not crs.is_projected:
            raise ValueError(f"The region raster CRS '{crs.to_string()}' is not projected. A projected CRS in linear "
                             f"units is required to compute interconnection distances in kilometres.")

        # conversion factor from the CRS linear unit to metres (1.0 for metre-based CRSs)
        _, to_metres = crs.linear_units_factor

        x_res, y_res = res

        return abs(y_res) * to_metres / 1000.0, abs(x_res) * to_metres / 1000.0

    @staticmethod
    def geometries_to_shapes(geometries, values):
        """Yield ``(GeoJSON-like dict, value)`` pairs for ``rasterio.features.rasterize``.

        ``rasterize`` accepts shapely objects directly, but then calls ``__geo_interface__`` on every feature, which
        for ~85 k features costs more than the burn itself. Points and LineStrings (the bulk of the packaged
        substation and pipeline data) are converted in bulk with shapely's vectorised coordinate extraction; any
        other geometry type falls back to ``shapely.geometry.mapping``.

        :param geometries:                      GeoPandas ``GeometryArray`` or sequence of shapely geometries
        :param values:                          Sequence of burn values, one per geometry

        """

        geometries = np.asarray(geometries, dtype=object)
        values = np.asarray(values)

        type_ids = shapely.get_type_id(geometries)
        coords, feature_index = shapely.get_coordinates(geometries, return_index=True)

        # start offset of each feature's coordinate run (features with no coordinates get an empty run)
        starts = np.searchsorted(feature_index, np.arange(len(geometries)), side='left')
        stops = np.searchsorted(feature_index, np.arange(len(geometries)), side='right')

        point_id, line_id = shapely.GeometryType.POINT, shapely.GeometryType.LINESTRING

        for i, (geom, type_id, value) in enumerate(zip(geometries, type_ids, values)):

            if geom is None or shapely.is_empty(geom):
                continue

            if type_id == point_id:
                yield {'type': 'Point', 'coordinates': coords[starts[i]].tolist()}, value

            elif type_id == line_id:
                yield {'type': 'LineString', 'coordinates': coords[starts[i]:stops[i]].tolist()}, value

            else:
                yield mapping(geom), value

    def transmission_to_cost_raster(self, setting):
        """Create a cost per grid cell in $/km from the input GeoDataFrame of transmission infrastructure having a cost
        designation field as '_rval_'.

        Distances are computed in kilometres using the raster's pixel size, so a raster at a resolution other than
        1 km produces correctly scaled costs.

        :param setting:                         Either 'substations' or 'pipelines'
        :type setting:                          str

        :return:                                Array of transmission interconnection cost per grid cell

        """
        if setting == 'substations':
            infrastructure_gdf = self.process_substations()

        elif setting == 'pipelines':
            infrastructure_gdf = self.process_pipelines()

        else:
            raise ValueError(
                f"Incorrect setting '{setting}' for transmission data.  Must be 'substations' or 'pipelines'")

        with rasterio.open(self.region_raster_file) as src:

            # pixel size in km along (row, col) so the distance transform returns km rather than pixel counts
            sampling_km = self.pixel_size_km(src.res, src.crs)

            out_shape = (src.height, src.width)
            transform = src.transform
            crs = src.crs

            # metadata for the optional float64 output rasters; the background is burned as 0, so NaN nodata only
            #  clears the inherited integer nodata (e.g. 128 from the region raster) that would be invalid for float64
            metadata = src.meta.copy()
            metadata.update({'dtype': rasterio.float64, 'nodata': np.nan})

        # reproject transmission data if necessary
        if infrastructure_gdf.crs != crs:
            infrastructure_gdf = infrastructure_gdf.to_crs(crs)

        # burn features into a zero-filled float64 raster; no temp file round trip is needed since `rasterize`
        #  returns the array
        shapes = self.geometries_to_shapes(infrastructure_gdf.geometry.values, infrastructure_gdf['_rval_'].values)
        burned = features.rasterize(shapes=shapes, fill=0, out_shape=out_shape, transform=transform,
                                    dtype=rasterio.float64)

        # calculate the Euclidean distance (km) and the indices of the nearest target (non-zero) cell
        distance_array, nearest_indices = distance_transform_edt(
            burned == 0,
            sampling=sampling_km,
            return_distances=True,
            return_indices=True
        )

        # use the nearest indices to map the value of the nearest target to each cell (allocation map)
        allocation_array = burned[nearest_indices[0], nearest_indices[1]]

        # distance in km * the cost of the nearest infrastructure feature; outputs thous$/km
        cost_arr = distance_array * allocation_array

        # write only the rasters the user asked for
        requested = {f'cerf_transmission_raster_{setting}.tif': (self.output_rasterized_file, burned),
                     f'cerf_transmission_distance_{setting}.tif': (self.output_dist_file, distance_array),
                     f'cerf_transmission_allocation_{setting}.tif': (self.output_alloc_file, allocation_array),
                     f'cerf_transmission_costs_{setting}.tif': (self.output_cost_file, cost_arr)}

        if any(flag for flag, _ in requested.values()):

            if self.output_dir is None:
                msg = "If writing rasters to file must specify 'output_dir'"
                logger.error(msg)
                raise NotADirectoryError(msg)

            for file_name, (flag, array) in requested.items():
                if flag:
                    with rasterio.open(os.path.join(self.output_dir, file_name), 'w', **metadata) as dst:
                        dst.write(array, 1)

        return cost_arr


    def generate_interconnection_costs_array(self):
        """Calculate the costs of interconnection for each technology."""

        # if a preprocessed file has been provided, load and return it
        if self.interconnection_cost_file is not None:
            logger.info(f"Using prebuilt interconnection costs file:  {self.interconnection_cost_file}")
            return np.load(self.interconnection_cost_file)

        # set up array to hold interconnection costs
        ic_arr = np.zeros_like(self.template_array)

        for index, i in enumerate(self.technology_order):

            # get technology specific information
            require_pipelines = self.technology_dict[i].get('require_pipelines', False)
            discount_rate = self.technology_dict[i].get('discount_rate')
            lifetime_yrs = self.technology_dict[i].get('lifetime_yrs')

            # calculate annuity factor for technology
            annuity_factor = self.calc_annuity_factor(discount_rate=discount_rate, lifetime_yrs=lifetime_yrs)

            # get transmission cost array and convert from thous$/km to $/km
            substation_cost_array = self.substation_costs * annuity_factor * 1000

            if require_pipelines:

                # get pipeline cost array and convert from thous$/km to $/km
                pipeline_cost_array = self.pipeline_costs * annuity_factor * 1000

                # calculate technology specific interconnection cost
                total_interconection_cost_array = substation_cost_array + pipeline_cost_array

            else:
                total_interconection_cost_array = substation_cost_array

            # calculate interconnection costs per grid cell
            ic_arr[index, :, :] = total_interconection_cost_array

        return ic_arr


def assign_substation_costs(gdf, transmission_costs_dict, voltage_field='min_volt'):
    """Assign a rasterization value field ('_rval_') to a substation GeoDataFrame containing the cost of
    interconnection in thous$/km based on the voltage class bin that each substation's minimum voltage falls in.

    :param gdf:                             Substation GeoDataFrame containing ``voltage_field``
    :type gdf:                              GeoDataFrame

    :param transmission_costs_dict:         Dictionary of {bin_id: {'min_voltage': int, 'max_voltage': int,
                                            'thous_dollar_per_km': int}, ...}
    :type transmission_costs_dict:          dict

    :param voltage_field:                   Name of the minimum voltage field. Default 'min_volt'.
    :type voltage_field:                    str

    :returns:                               The input GeoDataFrame with a populated '_rval_' field

    """

    if voltage_field not in gdf.columns:
        raise KeyError(f"Substations data must have a field named `{voltage_field}` containing the minimum voltage.")

    gdf['_rval_'] = 0

    for i in transmission_costs_dict.keys():
        gdf['_rval_'] = np.where((gdf[voltage_field] >= transmission_costs_dict[i]['min_voltage']) &
                                 (gdf[voltage_field] <= transmission_costs_dict[i]['max_voltage']),
                                 transmission_costs_dict[i]['thous_dollar_per_km'],
                                 gdf['_rval_'])

    return gdf


def preprocess_hifld_substations(substation_file, output_file=None):
    """Select substations from HIFLD data that are within the CONUS and either in service or under construction.
    A field used to rasterize ('_rval_') is also added containing the cost of connection in thous$/km for each
    substation based on its minimum voltage class.

    This data is assumed to have the following fields (case-insensitive):  ['TYPE', 'STATE', 'STATUS', 'MIN_VOLT'].
    Values in 'TYPE' and 'STATUS' are matched case-insensitively.

    :param substation_file:                 Full path with filename and extension to the input HIFLD substation
                                            shapefile
    :type substation_file:                  str

    :param output_file:                     Optional. Full path with filename and extension to the output shapefile
    :type output_file:                      str

    :returns:                               A geodataframe containing the target substations

    """

    # load the default costs per kv to connect file as a dictionary
    transmission_costs_dict = pkg.costs_per_kv_substation()

    # get region abbreviations file from cerf package data
    regions = pkg.get_region_abbrev_to_name()

    # load cerf's default coordinate reference system object
    target_crs = pkg.cerf_crs()

    # load and reproject
    gdf = gpd.read_file(substation_file).to_crs(target_crs)

    # make all column names lower case
    gdf.columns = [i.lower() for i in gdf.columns]

    # keep only substations in the CONUS that are either in service or under construction
    is_substation = gdf['type'].astype(str).str.strip().str.upper() == 'SUBSTATION'
    in_conus = gdf['state'].isin(regions.keys())
    is_active = gdf['status'].astype(str).str.strip().str.upper().isin(('IN SERVICE', 'UNDER CONST'))

    gdf = gdf.loc[is_substation & in_conus & is_active].copy()

    # assign a field to rasterize by containing the cost of transmission per km
    gdf = assign_substation_costs(gdf, transmission_costs_dict)

    if output_file is not None:
        gdf.to_file(output_file)

    return gdf


def preprocess_eia_natural_gas_pipelines(pipeline_file, output_file=None):
    """Select natural gas pipelines from EIA data that have a status of operating and a length greater than 0.

    This data is assumed to have a 'STATUS' field (case-insensitive) whose values are matched case-insensitively.

    :param pipeline_file:                   Full path with filename and extension to the input EIA pipeline
                                            shapefile
    :type pipeline_file:                    str

    :param output_file:                     Optional. Full path with filename and extension to the output shapefile
    :type output_file:                      str

    :returns:                               A geodataframe containing the target pipelines

    """

    # load cerf's default coordinate reference system object
    target_crs = pkg.cerf_crs()

    # read in data and reproject
    gdf = gpd.read_file(pipeline_file).to_crs(target_crs)

    # make all column names lower case
    gdf.columns = [i.lower() for i in gdf.columns]

    # only keep features with a length > 0
    gdf = gdf.loc[gdf.geometry.length > 0].copy()

    # only keep operational pipelines
    gdf = gdf.loc[gdf['status'].astype(str).str.strip().str.upper() == 'OPERATING'].copy()

    # use default costs file
    f = pkg.get_costs_gas_pipeline()

    with open(f, 'r') as yml:
        yaml_dict = yaml.load(yml, Loader=yaml.FullLoader)

    # set field for rasterize
    gdf['_rval_'] = yaml_dict.get('gas_pipeline_cost')

    if output_file is not None:
        gdf.to_file(output_file)

    return gdf
