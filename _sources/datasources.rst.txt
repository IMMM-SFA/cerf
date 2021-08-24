Package Data
============

1. ``costs_per_kv_substation.yml``
    - This is a YAML file containing the costs of connection per km to a substation having a certain minimum voltage range.  The following represents an example of how to implement this file:

    .. code-block:: yaml

        # key is the arbitrary category of each voltage range
        0:

        # the minimum voltage (MIN_VOLT) minimum
        min_voltage: -99999999999999999

        # the minimum voltage (MIN_VOLT) max limit; NOT to be confused with 'MAX_VOLT' in the data
        max_voltage: 99

        # cost per km to nearest substation meeting the voltage rating
        dollar_per_km: 678000

        1:
        min_voltage: 100
        max_voltage: 119
        dollar_per_km: 756000

        2:
        min_voltage: 120
        max_voltage: 149
        dollar_per_km: 791000

        3:
        min_voltage: 150
        max_voltage: 169
        dollar_per_km: 808000

        4:
        min_voltage: 170
        max_voltage: 299
        dollar_per_km: 863000

        5:
        min_voltage: 300
        max_voltage: 399
        dollar_per_km: 1380000

        6:
        min_voltage: 400
        max_voltage: 99999999999999999
        dollar_per_km: 1458000

2. ``substation_file``
    - Substation shapefiles can be used from any source as long as they have the following two fields:  ``min_volt`` and ``max_volt``.  These two fields represent the minimum voltage of the substation and the maxiumum voltage of the substation in kV and used to assign the substation of cost of interconnection based on what the user has specified in the ``costs_per_kv_substation.yml`` file.

3. ``costs_gas_pipeline.yml``
    - A YAML file containing the costs per km to for gas technologies to connect to a pipeline.  The folliwing represents an example of how to implement this file:

    .. code-block:: yaml

        # cost per kilometer of gas pipeline in $/km
        gas_pipeline_cost: 737000

4. ``pipeline_file``
    - Gas pipeline shapefiles can be used from any source as long as they have valid polyline geometries.





The zipped file `cerf_package_data.zip` contains the following files that support the data package for the CERF python package (see https://github.com/IMMM-SFA/cerf).  All spatial data is in the projected coordinate system described here:  https://immm-sfa.github.io/cerf/user_guide.html#preparing-suitability-rasters.

cerf_conus_boundary_albers.zip:  A shapefile containing polygons for each state in the conterminous United States (CONUS)

cerf_conus_states_albers_1km.tif:  A rasterized version of the CONUS states at a 1 km resolution

config_<year>.yml:  Sample configuration files for CERF

costs_gas_pipeline.yml:  YAML file containing gas pipeline costs

costs_per_kv_substation.yml:  YAML file containing the costs of interconnection for each substation class

eia_natural_gas_pipelines_conus_albers.zip:  A shapefile containing the natural gas pipeline polylines for the CONUS as retrieved from https://www.eia.gov/maps/layer_info-m.php per the 4/28/2020 update

hifld_substations_conus_albers.zip:  A shapefile containing HIFLD substations for the CONUS as retrieved from https://hifld-geoplatform.opendata.arcgis.com/datasets/geoplatform::electric-substations/about per the 07/08/2020 update

illustrative_lmp_8760-per-zone_dollars-per-mwh.zip:  A CSV file of fake illustrative locational marginal pricing (LMP) for 8760 hours per zone

lmp_zones_1km.img:  A raster of LMP zones per 1 km grid for the CONUS

state-abbrev_to_state-name.yml:  YAML file containing state abbreviation to state name

state-name_to_state-id.yml:  YAML file containing state name to state id

technologies.yml:  YAML file with sample technology-specific settings

suitability_<techname>.sgrd:  rasters for each technology suitability from http://doi.org/10.5334/jors.227
