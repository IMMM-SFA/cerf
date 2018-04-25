# cerf

## A geospatial model for assessing and analyzing future energy technology expansion feasibility

## Notice
This repository uses the Git Large File Storage (LFS) extension (see https://git-lfs.github.com/ for details).  Please run the following command before cloning if you do not already have Git LFS installed:
`git lfs install`.  Windows users have had better luck cloning LFS enabled repositories using the following command `git lfs clone https://github.com/IMMM-SFA/cerf.git`

## Contact
For questions please contact:

Chris Vernon:  <chris.vernon@pnnl.gov>

## Overview
The Capacity Expansion Regional Feasibility (CERF) model is an open-source geospatial model, written in Python and C++, that is designed to determine the on-the-ground feasibility of achieving a projected energy technology expansion plan.  Integrated assessment models and grid expansion models typically do not have sufficient spatial, temporal, or process-level resolution to account for technology-specific siting considerations—for example, the value or costs of connecting a new power plant to the electric grid at a particular location or whether there is sufficient cooling water to support the installation of thermal power plants in a certain region. CERF was developed to specifically examine where power plant locations can be feasibly sited when considering high spatial resolution siting suitability data as well as the net locational costs (i.e., considering both net operating value and interconnection costs), at a spatial resolution of 1 km2. The outputs from CERF can provide insight into factors that influence energy system resilience under a variety of future scenarios, can be used to refine model based projections, and can also be directly useful for capacity expansion planning exercises. CERF is open-source and publicly available via GitHub.


## CERF Setup

The following describes the requirements and format of each input:

***Constants***

This file contains constant assumptions that are applied in CERF. The
file name should be constants.xml. **Table 5** describes the required
parameters for the constants.xml file.

Table 5: Parameters and descriptions for CERF’s constants.xml input
file.

| Name                       | Description                                                           |
|----------------------------|-----------------------------------------------------------------------|
| discount\_rate             | Float from 0.0 to 1.0. The time value of money in real terms.         |
| carbon\_tax                | Float. The fee imposed on the burning of carbon-based fuels in $/ton. |
| carbon\_tax\_escalation    | The annual escalation rate for carbon tax. From 0.0 to 1.0.           |
| tx\_lifetime               | Integer in years of the expected technology plant lifetime.           |
| interconnection\_cost\_gas | Float for the capital cost of gas interconnection in 2005 in $K/km    |

***Expansion Plan***

This file contains the expansion plan expected capacity for each
technology per state. **Table 6** describes the required parameters for
the expansionplan.xml file.

Table 6: Parameters and descriptions for CERF’s expansionplan.xml input
file.

| Name          | Description                                                            |
|---------------|------------------------------------------------------------------------|
| Zoneid        | Corresponding state id as referenced in the states.xml file            |
| Techid        | Corresponding technology id as referenced in the technologies.xml file |
| &lt;value&gt; | The expected capacity in MW.                                           |

***Utility Zone Data***

This file contains specifics related to each utility zone. **Table 7**
describes the required parameters for the powerzones.xml file.

Table 7: Parameters and descriptions for CERF’s powerzones.xml input
file.

| Name                   | Description                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| zone                   | Integer ID of the utility zone                                              |
| shapeid                | Integer ID of the spatial reference referred to in states.xml               |
| name                   | The abbreviated name of the power zone as a string.                         |
| lmp                    | Float of the annualized locational marginal price for the target zone $/MWh |
| description            | String description of the utility zone                                      |
| &lt;lmps&gt;&lt;cf&gt; | Float capacity factor for each LMP percentile.                              |

***States***

This file contains information for the states referenced in the
expansion plan. **Table 8** describes the required parameters for the
states.xml file.

Table 8: Parameters and descriptions for CERF’s states.xml input file.

| Name          | Description                                              |
|---------------|----------------------------------------------------------|
| Id            | Unique Integer ID of the state                           |
| Shapeid       | Unique integer ID of the feature in the input shapefile. |
| &lt;value&gt; | String name of the state                                 |

***Technologies***

This file contains information for each technology. This information is
usually derived from the technology assumptions utilized in the IAM
providing the technology expansion plans. **Table 9** describes the
required parameters for the technologies.xml file.

Table 9: Parameters and descriptions for CERF’s technologies.xml input
file.

| Name                             | Description                                                                                                                                               |
|----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| Id                               | Unique integer ID for each technology                                                                                                                     |
| unit\_size                       | Integer value for power plant unit size in MW                                                                                                             |
| capacity\_factor                 | Float value from 0.0 to 1.0 for the average annual power generated divided by the potential output if the plant operated at its rated capacity for a year |
| variable\_om                     | Float value representing the variable operation and maintenance costs of yearly capacity use in $/MWh                                                     |
| variable\_cost\_escalation\_rate | Float from -1.0 to 1.0 for the escalation rate of variable costs                                                                                          |
| heat\_rate                       | Float for the amount of energy used by a power plant to generate one kilowatt-hour of electricity in Btu/kWh                                              |
| fuel\_price                      | Float for cost of fuel per unit in ($/MBtu)(10<sup>6</sup> Btu/MBtu)(10<sup>3</sup> kWh/MWh)                                                              |
| fuel\_price\_escalation          | Float from -1.0 to 1.0 for fuel price escalation                                                                                                          |
| fuel\_co2\_content               | Float for CO<sub>2</sub> content of the fuel and the heat rate of the technology in Tons/MWh                                                              |
| interconnection\_cost\_per\_km   | Float for the capital cost of interconnection in 2005 $K/km                                                                                               |
| full\_name                       | Full technology name                                                                                                                                      |
| lifetime                         | Integer for asset life time in years                                                                                                                      |
| category                         | Type of fuel (e.g., gas, coal, etc.)                                                                                                                      |
| fuel\_index                      | String reference for fuel index type                                                                                                                      |
| variable\_om\_2005               | Float value for variable operation and maintenance costs of 2005 capacity use in $/MWh                                                                    |
| siting\_buffer                   | Buffer to place around a plant once sited                                                                                                                 |
| carbon\_capture\_rate            | Float for the rate from 0 to 1 of carbon capture |


***Suitability data***

This file contains the full path reference to each technologies
suitability raster. **Table 10** describes the required parameters for
the technology\_suitabilitymask\_paths.xml file.

Table 10: Parameters and descriptions for CERF’s
technology\_suitabilitymask\_paths.xml input file.

| Name          | Description                                                           |
|---------------|-----------------------------------------------------------------------|
| techid        | Integer ID of the corresponding technology                            |
| &lt;value&gt; | Full path with file name and extension to the input SAGA grid raster. |

***Configuration file***

This file is the main configuration used to run CERF. **Table 11**
describes the required parameters for the configuration file.

Table 11: Parameters and descriptions for CERF’s configuration file.

| Name                | Description                                                                                                                                                |
|---------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| exe\_path           | Full path with file name and extension of saga\_cerf.exe                                                                                                   |
| xml\_path           | Full path to the directory containing the input XML files                                                                                                  |
| out\_path           | Full path to the directory where the output files will be written                                                                                          |
| yr                  | Integer target four digit year (e.g. 2005)                                                                                                                 |
| primary\_zone       | Full path with file name and extension to the input states raster                                                                                          |
| utility\_zones      | Full path with file name and extension to the input utility zones                                                                                          |
| common\_exclusion   | Full path with file name and extension to the input suitability raster common to all technologies                                                          |
| transmission\_230kv | Full path with file name and extension to the input raster for transmission lines &gt;= 230 Kv                                                             |
| transmission\_345kv | Full path with file name and extension to the input raster for transmission lines &gt;= 345 Kv                                                             |
| transmission\_500kv | Full path with file name and extension to the input raster for transmission lines &gt;= 500 Kv                                                             |
| gasline\_16in       | Full path with file name and extension to the input raster for gas pipelines that are &gt;= 16 inches                                                      |
| buffer              | Integer buffer in grid cells to place around each site                                                                                                     |
| distance\_method    | Integer from 0 to 2 to select type of distance method used when calculating interconnection costs \[0: Chessboard, 1: Manhattan, 2: Euclidean distance\]   |
| direction\_method   | Integer from 0 to 3 to select the directional pattern used when siting a technology in a region \[0: left, right, top, bottom; 1: RLBT; 2: LRBT; 3: RLTB\] |

***Preparing Suitability Rasters***

Rasters for spatial suitability are required to conform to the format
referenced in **Table 12**. Suitability rasters can be prepared using
any GIS.

**Table 12**. Requirements for spatial suitability rasters.

| Attribute                         | Description                                            |
|-----------------------------------|--------------------------------------------------------|
| Number of columns, Number of rows | 4693, 2999                                             |
| Coordinate system                 | PROJCS\["USA\_Contiguous\_Albers\_Equal\_Area\_Conic", GEOGCS\["GCS\_North\_American\_1983", DATUM\["North\_American\_Datum\_1983", SPHEROID\["GRS\_1980",6378137.0,298.257222101\]\], PRIMEM\["Greenwich",0.0\], UNIT\["Degree",0.0174532925199433\]\], PROJECTION\["Albers\_Conic\_Equal\_Area"\], PARAMETER\["false\_easting",0.0\], PARAMETER\["false\_northing",0.0\], PARAMETER\["longitude\_of\_center",-96.0\], PARAMETER\["standard\_parallel\_1",29.5\], PARAMETER\["standard\_parallel\_2",45.5\], PARAMETER\["latitude\_of\_center",37.5\], UNIT\["Meters",1.0\]\]                                  |
| Origin                            | (-2405552.835500000044703, 1609934.799499999964610)    |
| Pixel Size                        | (1000, -1000)                                          |
| Upper Left                        | (-2405552.836, 1609934.799)                             |
| Lower Left                        | (-2405552.836, -1389065.201)                           |
| Upper Right                       | (2287447.164, 1609934.799)                             |
| Lower Right                       | (2287447.164, -1389065.201)                            |
| Center                            | (-59052.836, 110434.799)                               |
| Type                              | Byte                                                   |
