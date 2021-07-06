[![linux](https://github.com/IMMM-SFA/cerf/actions/workflows/linux.yml/badge.svg)](https://github.com/IMMM-SFA/cerf/actions/workflows/linux.yml)
[![osx](https://github.com/IMMM-SFA/cerf/actions/workflows/osx.yml/badge.svg)](https://github.com/IMMM-SFA/cerf/actions/workflows/osx.yml)
[![windows](https://github.com/IMMM-SFA/cerf/actions/workflows/windows.yml/badge.svg)](https://github.com/IMMM-SFA/cerf/actions/workflows/windows.yml)
[![codecov](https://codecov.io/gh/IMMM-SFA/cerf/branch/version-two/graph/badge.svg?token=9jbGJv8XCJ)](https://codecov.io/gh/IMMM-SFA/cerf)
[![Documentation Status](https://readthedocs.org/projects/im3-cerf/badge/?version=latest)](https://im3-cerf.readthedocs.io/en/latest/?badge=latest)
[![DOI](https://zenodo.org/badge/115649750.svg)](https://zenodo.org/badge/latestdoi/115649750)

## cerf

### A geospatial model for assessing and analyzing future energy technology expansion feasibility

## Overview
The Capacity Expansion Regional Feasibility model (CERF) helps us evaluate the feasibility and structure of future electricity capacity expansion plans by siting power plants in areas that have been deemed the least cost option. We can use CERF to gain an understanding of topics such as: 1) whether or not future projected electricity expansion plans from models such as GCAM are possible to achieve, 2) where suitability (e.g., cooling water availability) may influence our ability to achieve certain expansions, and/or 3) how power plant infrastructure build outs and value may evolve into the future when considering locational marginal pricing from a grid operations model.

CERF currently operates at a 1 km2 resolution over the conterminous United States. Each grid cell is given an initial value of suitable (0) or unsuitable (1) based on a collection of suitability criteria gleaned from the literature. CERF's default suitability layers include both those that are common to all thermal technologies as well as technology-specific suitability criteria. Common suitability layers represent categories such as protected lands, critical habitat areas, and much more. Technology-specific suitability layers are those that satisfy requirements that may not be applicable to all technologies. An example would be minimum mean annual flow requirements for cooling water availability for individual thermal technologies.

We introduce a metric named Net Locational Cost (NLC) that is used compete power plant technologies for each grid cell based on the least expensive option. NLC is calculated by subtracting the Net Operational Value (NOV) of the proposed power plant from the cost of its interconnection to the grid to represent the potential deployment value. Both the NOV parameter which incorporates many technology-specific values such as variable operations and maintenance costs, carbon price, heat rate, etc. and the interconnection cost parameter used for both electricity transmission and gas pipelines have variables that are accessible to the user for modification per time step.

## Get Started with CERF

### Install `cerf` from GitHub

```bash
python -m pip install -e git://github.com/IMMM-SFA/cerf.git@main#egg=cerf
```

### Download and unpack the example data using the following from a Python prompt

```python
import cerf

# the directory that you want to download and extract the example data to
data_dir = "<my data download location>"

# download and unzip the package data to your local machine
cerf.get_package_data(data_dir)

```

### Setting up a `cerf` run

The `cerf` package utilizes a YAML configuration file customized by the user with project level and technology-specific settings, an electricity technology capacity expansion plan, and utility zone data for each year intended to model.  `cerf` comes equipped with prebuilt configuration files for years 2010 through 2050 to provide an illustrative example.  Each example configuration file can be viewed using the following:

```python
import cerf

sample_config = cerf.load_sample_config(yr=2010)

```

The following are the required key, values if your wish to construct your own configuration files:

#### `settings`
These are required values for project-level settings.

| Name | Description | Unit | Type |
| --- | --- | --- | --- |
| run_year | Target year to run in YYYY format | year | int |
| output_directory | Directory to write the output data to | NA | str |
| randomize | Randomize selection of a site for a technology when NLC values are equal. The first pass is always random but setting `randomize` to False and passing a seed value will ensure that runs are reproducible | NA | bool |
| seed_value | If `randomize` is False, set a seed value for reproducibility; the default is 0 | NA | int |

The following is an example implementation in the YAML configuration file:

```yaml
settings:

    run_year: 2010
    output_directory: <your output directory>
    randomize: False
    seed_value: 0
```

#### `technology`
These are technology-specific settings.

| Name | Description | Unit | Type |
| --- | --- | --- | --- |
| Integer ID given to the technology (e.g., 9)| This is an integer ID key given to the technology for reference purposes.  This ID should match the corresponding technology in the electricity technology expansion plan. | NA | int |
| tech_name | Name of the technology | NA | str |
| lifetime | Asset lifetime | number of years | int |
| capacity_factor | Defined as average annual power generated divided by the potential output if the plant operated at its rated capacity for a year | fraction | float |
| variable_cost_esc_rate | Escalation rate of variable cost | fraction | float |
| fuel_esc_rate | Escalation rate of fuel | fraction | float |
| unit_size | The size of the expected power plant | MW | float |
| variable_om | Variable operation and maintenance costs of yearly capacity use | $/MWh | float |
| heat_rate | Amount of energy used by a power plant to generate one kilowatt-hour of electricity | Btu/kWh | float |
| fuel_price | Cost of fuel per unit | ($/GJ) gets converted to ($/MBtu) in the model | float |
| carbon_capture_rate | Rate of carbon capture | fraction | float |
| fuel_co2_content | CO2 content of the fuel and the heat rate of the technology | (tons/MWh) gets converted to (tons/Btu) in the model | float |
| discount_rate | The time value of money in real terms | fraction | float |
| carbon_esc_rate | Escalation rate of carbon | fraction | float |
| carbon_tax | The fee imposed on the burning of carbon-based fuels | $/ton | float |
| buffer_in_km | Buffer around the site to apply in kilometers which becomes unsuitable for other sites after siting | number of km | int |
| require_pipelines | If the technology is gas related, pipelines will be used when calculating the interconnection cost | NA | bool |
| suitability_raster_file | Full path with file name and extension to the accompanying suitability raster file | NA | str |
| utility_zone_lmp_file | LMP CSV file containing 8760 LMP per zone where columns are each zone with a numeric zone ID header that corresponds with the zones represented in the `utility_zone_raster_file` found in the `utility_zones` section and an additional hour column named `hour` holding the hour of each record | $/MWh for the LMPs in the file | str |

The following is an example implementation in the YAML configuration file:

```yaml
technology:

    9:
        tech_name: biomass
        lifetime: 60
        capacity_factor: 0.6090000000000005
        variable_cost_esc_rate: -0.00398993418629034
        fuel_esc_rate: 0.0
        unit_size: 80
        variable_om: 11.68495803744351
        heat_rate: 15117.64999999997
        fuel_price: 0.0
        carbon_capture_rate: 0.0
        fuel_co2_content: 0.3035999999999996
        discount_rate: 0.05
        carbon_esc_rate: 0.0
        carbon_tax: 0.0
        buffer_in_km: 5
        require_pipelines: False
        suitability_raster_file: <path to file>
        utility_zone_lmp_file: <path to lmp file>
```

#### `expansion_plan`
These are the electricity technology capacity expansion plan.

| Name | Description | Unit | Type |
| --- | --- | --- | --- |
| State name (e.g., arizona)| Name key of state in all lower case with underscore separation | NA | str |
| Technology ID key matching what is in the technology section (e.g., 9) | NA | int |
| tech_name | Name of the technology matching the name in the technology section | NA | str |
| n_sites | Number of sites desired | number of sites | int |


The following is an example implementation in the YAML configuration file:

```yaml
expansion_plan:

    arizona:
        9:
            tech_name: biomass
            n_sites: 2
```

#### `utility_zones`
These are the utility zone data representing the linkage between each grid and technology and their locational marginal price (LMP).

| Name | Description | Unit | Type |
| --- | --- | --- | --- |
| utility_zone_raster_file | Full path with file name and extension to the utility zones raster file | NA | str |
| utility_zone_raster_nodata_value | No data value in the utility zone raster | NA | int; float |


The following is an example implementation in the YAML configuration file:

```yaml
utility_zones:

    utility_zone_raster_file: <path to zone raster>
    utility_zone_raster_nodata_value: 255
```

The `cerf` package comes equipped with a sample utility zones raster file and a sample hourly (8760) locational marginal price file for illustrative purposes only.

You can take a look at the utility zones raster file by running:

```python
import cerf

utility_file = cerf.sample_utility_zones_raster_file()
```

You can also view the sample hourly locational marginal price file as a Pandas DataFrame using:

```python
import cerf

df = cerf.get_sample_lmp_data()
```


### Preparing Suitability Rasters

The `cerf` package comes equipped with sample suitability data but you can build your on as well.  

You can see which suitability rasters are available in the `cerf` package by running:

```python
import cerf

cerf.list_available_suitability_files()
```

Rasters for spatial suitability at a resolution of 1km over the CONUS are required to conform to the format referenced in the following table.  Suitability rasters can be prepared using any GIS.


| Attribute | Description |
| ---| --- |
| Number of columns, Number of rows | 4693, 2999 |
| Coordinate system | PROJCS\["USA\_Contiguous\_Albers\_Equal\_Area\_Conic", GEOGCS\["GCS\_North\_American\_1983", DATUM\["North\_American\_Datum\_1983", SPHEROID\["GRS\_1980",6378137.0,298.257222101\]\], PRIMEM\["Greenwich",0.0\], UNIT\["Degree",0.0174532925199433\]\], PROJECTION\["Albers\_Conic\_Equal\_Area"\], PARAMETER\["false\_easting",0.0\], PARAMETER\["false\_northing",0.0\], PARAMETER\["longitude\_of\_center",-96.0\], PARAMETER\["standard\_parallel\_1",29.5\], PARAMETER\["standard\_parallel\_2",45.5\], PARAMETER\["latitude\_of\_center",37.5\], UNIT\["Meters",1.0\]\] |
| Origin | (-2405552.835500000044703, 1609934.799499999964610) |
| Pixel Size | (1000, -1000) |
| Upper Left | (-2405552.836, 1609934.799) |
| Lower Left | (-2405552.836, -1389065.201) |
| Upper Right | (2287447.164, 1609934.799) |
| Lower Right | (2287447.164, -1389065.201) |
| Center | (-59052.836, 110434.799) |
| Type | Byte |

## Contact
For questions please contact:

Chris Vernon:  <chris.vernon@pnnl.gov>
