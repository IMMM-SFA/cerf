===============
User guide
===============

Setting up a **cerf** run
-------------------------

The following with indroduce you to the input data required by **cerf** and how to set up a configuration file to run **cerf**.

Configration file setup
~~~~~~~~~~~~~~~~~~~~~~~

The **cerf** package utilizes a YAML configuration file customized by the user with project level and technology-specific settings, an electricity technology capacity expansion plan, and utility zone data for each year intended to model. **cerf** comes equipped with prebuilt configuration files for years 2010 through 2050 to provide an illustrative example. Each example configuration file can be viewed using the following:

.. code-block:: python

  import cerf

  sample_config = cerf.load_sample_config(yr=2010)

The following are the required key, values if your wish to construct your own configuration files:

``settings``
^^^^^^^^^^^^

These are required values for project-level settings.

.. table::

    +--------------------+-------------------------------------------------------+-------+-------+
    | Name               | Description                                           | Unit  | Type  |
    +====================+=======================================================+=======+=======+
    | run_year           | Target year to run in YYYY format                     | year  | int   |
    +--------------------+-------------------------------------------------------+-------+-------+
    | output_directory   | Directory to write the output data to                 | NA    | str   |
    +--------------------+-------------------------------------------------------+-------+-------+
    | randomize          | | Randomize selection of a site for a technology when | NA    | str   |
    |                    | | NLC values are equal. The first pass is always      |       |       |
    |                    | | random but setting `randomize` to False and passing |       |       |
    |                    | | a seed value will ensure that runs are reproducible |       |       |
    +--------------------+-------------------------------------------------------+-------+-------+
    | seed_value         | | If ``randomize`` is False; set a seed value for     | NA    | int   |
    |                    | | reproducibility; the default is 0                   |       |       |
    +--------------------+-------------------------------------------------------+-------+-------+



The following is an example implementation in the YAML configuration file:

.. code-block:: yaml

  settings:

      run_year: 2010
      output_directory: <your output directory>
      randomize: False
      seed_value: 0


``technology``
^^^^^^^^^^^^^^

These are technology-specific settings.

.. table::

    +-------------------------+---------------------------------------------+----------+----------+
    | Name                    | Description                                 | Unit     | Type     |
    +=========================+=============================================+==========+==========+
    | <tech id number>        | | This is an integer ID key given to the    | NA       | int      |
    |                         | | technology for reference purposes.  This  |          |          |
    |                         | | ID should match the corresponding         |          |          |
    |                         | | technology in the electricity technology  |          |          |
    |                         | | expansion plan.                           |          |          |
    +-------------------------+---------------------------------------------+----------+----------+
    | tech_name               | Name of the technology                      | NA       | str      |
    +-------------------------+---------------------------------------------+----------+----------+
    | lifetime                | Asset lifetime                              | n_years  | int      |
    +-------------------------+---------------------------------------------+----------+----------+
    | capacity_factor         | | Defined as average annual power generated | fraction | float    |
    |                         | | divided by the potential output if the    |          |          |
    |                         | | plant operated at its rated capacity for a|          |          |
    |                         | | year                                      |          |          |
    +-------------------------+---------------------------------------------+----------+----------+
    | variable_cost_esc_rate  | Escalation rate of variable cost            | fraction | float    |
    +-------------------------+---------------------------------------------+----------+----------+
    | fuel_esc_rate           | Escalation rate of fuel                     | fraction | float    |
    +-------------------------+---------------------------------------------+----------+----------+
    | unit_size               | The size of the expected power plant        | MW       | float    |
    +-------------------------+---------------------------------------------+----------+----------+
    | variable_om             | | Variable operation and maintenance costs  | $/MWh    | float    |
    |                         | | of yearly capacity use                    |          |          |
    +-------------------------+---------------------------------------------+----------+----------+
    | heat_rate               | | Amount of energy used by a power plant to | Btu/kWh  | float    |
    |                         | | generate one kilowatt-hour of electricity |          |          |
    +-------------------------+---------------------------------------------+----------+----------+
    | fuel_price              | Cost of fuel per unit                       | $/GJ     | float    |
    +-------------------------+---------------------------------------------+----------+----------+
    | carbon_capture_rate     | Rate of carbon capture                      | fraction | float    |
    +-------------------------+---------------------------------------------+----------+----------+
    | fuel_co2_content        | | CO2 content of the fuel and the heat rate | tons/MWh | float    |
    |                         | | of the technology                         |          |          |
    +-------------------------+---------------------------------------------+----------+----------+
    | discount_rate           | The time value of money in real terms       | fraction | float    |
    +-------------------------+---------------------------------------------+----------+----------+
    | carbon_esc_rate         | Escalation rate of carbon                   | fraction | float    |
    +-------------------------+---------------------------------------------+----------+----------+
    | carbon_tax              | | The fee imposed on the burning of         | $/ton    | float    |
    |                         | | carbon-based fuels                        |          |          |
    +-------------------------+---------------------------------------------+----------+----------+
    | buffer_in_km            | | Buffer around the site to apply in        | n_km     | int      |
    |                         | | kilometers which becomes unsuitable for   |          |          |
    |                         | | other sites after siting                  |          |          |
    +-------------------------+---------------------------------------------+----------+----------+
    | require_pipelines       | | If the technology is gas related pipelines| NA       | bool     |
    |                         | | will be used when calculating the         |          |          |
    |                         | | interconnection cost                      |          |          |
    +-------------------------+---------------------------------------------+----------+----------+
    | suitability_raster_file | | Full path with file name and extension to | NA       | str      |
    |                         | | the accompanying suitability raster file  |          |          |
    +-------------------------+---------------------------------------------+----------+----------+
    | utility_zone_lmp_file   | | LMP CSV file containing 8760 LMP per zone | $/MWh    | str      |
    |                         | | where columns are each zone with a numeric|          |          |
    |                         | | zone ID header that corresponds with the  |          |          |
    |                         | | zones represented in the                  |          |          |
    |                         | | ``utility_zone_raster_file`` found in the |          |          |
    |                         | | ``utility_zones`` section and an          |          |          |
    |                         | | additional hour column named ``hour``     |          |          |
    |                         | | holding the hour of each record           |          |          |
    +-------------------------+---------------------------------------------+----------+----------+

The following is an example implementation in the YAML configuration file:

.. code-block:: yaml

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


``expansion_plan``
^^^^^^^^^^^^^^^^^^

These are technology-specific settings.

.. table::

    +-------------------------+---------------------------------------------+----------+----------+
    | Name                    | Description                                 | Unit     | Type     |
    +=========================+=============================================+==========+==========+
    | <state name>            | | Name key of state in all lower case with  | NA       | str      |
    |                         | | underscore separation                     |          |          |
    +-------------------------+---------------------------------------------+----------+----------+
    | <tech id key>           | | Technology ID key matching what is in the | NA       | int      |
    |                         | | technology section (e.g. 9)               |          |          |
    +-------------------------+---------------------------------------------+----------+----------+
    | tech_name               | | Name of the technology matching the name  | NA       | str      |
    |                         | | in the technology section                 |          |          |
    +-------------------------+---------------------------------------------+----------+----------+
    | n_sites                 | Number of sites desired                     | n_sites  | int      |
    +-------------------------+---------------------------------------------+----------+----------+

The following is an example implementation in the YAML configuration file:

.. code-block:: yaml

    expansion_plan:

        arizona:
            9:
                tech_name: biomass
                n_sites: 2


``utility_zones``
^^^^^^^^^^^^^^^^^^

These are the utility zone data representing the linkage between each grid and technology and their locational marginal price (LMP).

.. table::

    +----------------------------------+---------------------------------------------+----------+----------+
    | Name                             | Description                                 | Unit     | Type     |
    +==================================+=============================================+==========+==========+
    | utility_zone_raster_file         | | Full path with file name and extension to | NA       | str      |
    |                                  | | the utility zones raster file             |          |          |
    +----------------------------------+---------------------------------------------+----------+----------+
    | utility_zone_raster_nodata_value | No data value in the utility zone raster    | NA       | float    |
    +----------------------------------+---------------------------------------------+----------+----------+

The following is an example implementation in the YAML configuration file:

.. code-block:: yaml

    utility_zones:

        utility_zone_raster_file: <path to zone raster>
        utility_zone_raster_nodata_value: 255


The `cerf` package comes equipped with a sample utility zones raster file and a sample hourly (8760) locational marginal price file for illustrative purposes only.

You can take a look at the utility zones raster file by running:

.. code-block:: python

    import cerf

    utility_file = cerf.sample_utility_zones_raster_file()


You can also view the sample hourly locational marginal price file as a Pandas DataFrame using:

.. code-block:: python

    import cerf

    df = cerf.get_sample_lmp_data()


``infrastructure``
^^^^^^^^^^^^^^^^^^

These are the electricity transmission and gas pipeline infrastructure data.

.. table::

    +-------------------------+---------------------------------------------+----------+----------+
    | Name                    | Description                                 | Unit     | Type     |
    +=========================+=============================================+==========+==========+
    | substation_file         | | Full path with file name and extension to | NA       | str      |
    |                         | | he input substations shapefile. If None   |          |          |
    |                         | | `cerf` will use the default data stored in|          |          |
    |                         | | the package.                              |          |          |
    +-------------------------+---------------------------------------------+----------+----------+
    | costs_to_connect_file   | | A YAML file containing the cost of        | NA       | dict     |
    |                         | | connection per km to a substation having a|          |          |
    |                         | | certain minimum voltage range.  Default is|          |          |
    |                         | | to load from the CERF data file           |          |          |
    |                         | | 'costs_per_kv_substation.yml' by          |          |          |
    |                         | | specifying 'None'                         |          |          |
    +-------------------------+---------------------------------------------+----------+----------+
    | pipeline_file           | | Full path with file name and extension to | NA       | str      |
    |                         | | he input pipelines shapefile. If None     |          |          |
    |                         | | CERF will use the default data stored in  |          |          |
    |                         | | the package.                              |          |          |
    +-------------------------+---------------------------------------------+----------+----------+
    | output_rasterized_file  | Write distance raster                       | NA       | bool     |
    +-------------------------+---------------------------------------------+----------+----------+
    | output_dist_file        | Write distance raster                       | NA       | bool     |
    +-------------------------+---------------------------------------------+----------+----------+
    | output_alloc_file       | Write allocation file                       | NA       | bool     |
    +-------------------------+---------------------------------------------+----------+----------+
    | output_cost_file        | Write cost file                             | NA       | bool     |
    +-------------------------+---------------------------------------------+----------+----------+

The following is an example implementation in the YAML configuration file:

.. code-block:: yaml

    infrastructure:

        substation_file: <path to substation shapefile>
        costs_to_connect_file: <path to the yaml file>
        pipeline_file: <path to the pipeline file>
        output_rasterized_file: False
        output_dist_file: False
        output_alloc_file: False
        output_cost_file: False


You can view the built-in costs per kV to connect to a substation using:

.. code-block:: python

    import cerf

    costs_dict = cerf.costs_per_kv_substation()


Preparing suitability rasters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **cerf** package comes equipped with sample suitability data but you can build your on as well.

You can see which suitability rasters are available in the `cerf` package by running:

.. code-block:: python

    import cerf

    cerf.list_available_suitability_files()


Rasters for spatial suitability at a resolution of 1km over the CONUS are required to conform to the format referenced in the following table.  Suitability rasters can be prepared using any GIS.

.. table::

    +----------------------+-------------------------------------------------------------+
    | Attribute            | Description                                                 |
    +======================+=============================================================+
    | | Number of columns  | 4693, 2999                                                  |
    | | Number of rows     |                                                             |
    +----------------------+-------------------------------------------------------------+
    | Coordinate system    | | PROJCS\["USA\_Contiguous\_Albers\_Equal\_Area\_Conic",    |
    |                      | | GEOGCS\["GCS\_North\_American\_1983",                     |
    |                      | | DATUM\["North\_American\_Datum\_1983",                    |
    |                      | | SPHEROID\["GRS\_1980",6378137.0,298.257222101\]\],        |
    |                      | | PRIMEM\["Greenwich",0.0\],                                |
    |                      | | UNIT\["Degree",0.0174532925199433\]\],                    |
    |                      | | PROJECTION\["Albers\_Conic\_Equal\_Area"\],               |
    |                      | | PARAMETER\["false\_easting",0.0\],                        |
    |                      | | PARAMETER\["false\_northing",0.0\],                       |
    |                      | | PARAMETER\["longitude\_of\_center",-96.0\],               |
    |                      | | PARAMETER\["standard\_parallel\_1",29.5\],                |
    |                      | | PARAMETER\["standard\_parallel\_2",45.5\],                |
    |                      | | PARAMETER\["latitude\_of\_center",37.5\],                 |
    |                      | | UNIT\["Meters",1.0\]\]                                    |
    +----------------------+-------------------------------------------------------------+
    | Origin               | (-2405552.835500000044703, 1609934.799499999964610)         |
    +----------------------+-------------------------------------------------------------+
    | Pixel Size           | (1000, -1000)                                               |
    +----------------------+-------------------------------------------------------------+
    | Upper Left           | (-2405552.836, 1609934.799)                                 |
    +----------------------+-------------------------------------------------------------+
    | Lower Left           | (-2405552.836, -1389065.201)                                |
    +----------------------+-------------------------------------------------------------+
    | Upper Right          | (2287447.164, 1609934.799)                                  |
    +----------------------+-------------------------------------------------------------+
    | Lower Right          | (2287447.164, -1389065.201)                                 |
    +----------------------+-------------------------------------------------------------+
    | Center               | (-59052.836, 110434.799)                                    |
    +----------------------+-------------------------------------------------------------+
    | Type                 | Byte                                                        |
    +----------------------+-------------------------------------------------------------+


Locational Marginal Price (LMP)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

description here.  link in NOV below needs to be updated.


Tutorials
---------

Jupyter Notebooks

**cerf** quickstarter
~~~~~~~~~~~~~~~~~~~~~

The following is a link to a Jupyter Notebook to run **cerf** without having to install any software:  `cerf quickstarter <https://github.com/IMMM-SFA/cerf>`_


Fundamental equations and concepts
----------------------------------

The following are the building blocks of how **cerf** sites power plants.


Net Operating Value
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Net Operating Value is the difference between the locational marginal value of the energy generated by a technology and its operating costs.  The locational marginal value is a function of the plant’s capacity factor, the average locational marginal price (LMP) for that capacity factor in the zone that encompasses the grid cell, and the plant’s generation.  The average LMP for each zone/capacity factor is calculated from a grid operation model output as the average of the hours corresponding to that capacity factor (e.g., for a 10% capacity factor, the LMP is calculated based on the top 10% of LMP values).  The operating costs are determined by the plant’s generation, heat rate, fuel cost, variable O&M, carbon tax, and carbon emissions--if there is a carbon tax in the expansion plan scenario being processed.

Net operating value (NOV)
^^^^^^^^^^^^^^^^^^^^^^^^^

.. math::

    NOV = G(LMP - OC)

where, *NOV* is Net Operating Value in $/yr; *G* is electricity generation in MWh/yr; *LMP* is locational marginal price in $/MWh; *OC* are operating costs in $/MWh.

Generation (G)
^^^^^^^^^^^^^^

.. math::

    G = U * CF * HPY

where, *U* is the unit size of a power plant in MW; *CF* is the capacity factor of the power plant; *HPY* is the number of hours in a year.  Both unit size and capacity factor are input variables to **cerf**.

Levelization factor (LF\ :subscript:`i`\)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. math::

    k_i = \frac{1 + l_i}{1 + d}

.. math::

    LF_i = k_i(1-k_i^n) * \frac{AF}{1-k_i}

where, *l*\ :subscript:`fuel` \ is an escalation rate as a fraction; *d* is the real annual discount rate as a fraction; *n* is the asset lifetime in years; and *AF* is the annuity factor.  All escalation rates are input variables to **cerf**.

Annuity factor (AF)
^^^^^^^^^^^^^^^^^^^

.. math::

    AF = \frac{d(1 + d)^n}{(1 + d)^n - 1}

where, *d* is the real annual discount rate as a fraction and *n* is the asset lifetime in years.


Locational marginal price (LMP)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. math::

    LMP_{lev} = LMP * LF_{fuel}

where, *LMP* is the locational marginal price (*LMP*) in $/MWh and *LF*\ :subscript:`fuel` \ is the levelization factor of fuel.  *LMP* is also an input to **cerf** and is described in full `here <www.google.com>`_.

Operating cost (OC)
^^^^^^^^^^^^^^^^^^^

.. math::

    OC = \bigg(HR * \bigg(\frac{FP}{1000}\bigg) * LF_{fuel}\bigg) + \bigg(VOM * LF_{vom}\bigg) + \bigg(\bigg(\frac{CT * CO2 * HR * LF_{carbon}}{1000000}\bigg) * \bigg(1 - CCR\bigg)\bigg)

where, *HR* is heat rate in Btu/kWh; *FP* is fuel price which **cerf** takes in as $/GJ but it gets converted to $/MBtu in the model; *VOM* is the variable operation and maintenance costs of yearly capacity use in $/MWh; *LF*\ :subscript:`vom` \ is the levelization factor of variable O&M; *CT* is the carbon tax in $/ton; *CO2* is the CO2 content of the fuel taken as an input in units tons/MWh but gets converted to tons/Btu in the model; *LF*\ :subscript:`carbon` \ is the levelization factor for carbon as a fraction; and *CCR* is the carbon capture rate as a fraction.  All variables are inputs to the **cerf** model.


Interconnection Cost
~~~~~~~~~~~~~~~~~~~~

Interconnection cost is the sum of the transmission interconnection cost and the gas pipeline interconnection cost (if a gas-fired technology is being evaluated) at each grid cell.  **cerf** calculates the distances to the nearest substation with the minimum required voltage rating and to the nearest gas pipeline with the minimum required diameter for each suitable grid cell.  It then applies distance- and voltage-based capital costs to estimate the total cost for the new plant to connect to the grid.  This is calculated as:

.. math::

    IC = (D_{elec} * C_{elec} * AF) + (D_{gas} * C_{gas} * AF)

where, *IC* is Interconnection Cost in $/yr; *D*\ :subscript:`elec` is the distance to the nearest suitable electricity transmission infrastructure (e.g., substation) in kilometers; *C*\ :subscript:`elec` is the electric grid interconnection captial cost in $/km; *D*\ :subscript:`gas` is the distance to the nearest suitable gas pipeline in kilometers; *C*\ :subscript:`gas` is the gas interconnection captial cost in $/km and *AF* is the annuity factor.

The annuity factor (*AF*) is calculated as:

.. math::

    AF = \frac{d(1 + d)^n}{(1 + d)^n - 1}

where, *d* is the real annual discount rate as a fraction and *n* is the asset lifetime in years.



Net Locational Cost
~~~~~~~~~~~~~~~~~~~~

Net Locational Cost (*NLC*) is used to compete power plant technologies per grid cell based on the least expensive option to site.  *NLC* is calculated by subtracting the Net Operating Value (NOV) of the proposed power plant from the cost of its interconnection (IC) to the grid to represent the potential deployment value.  Both the NOV parameter which incorporates many technology-specific values such as variable operations and maintenance costs, carbon price, heat rate, etc. and the interconnection cost parameter used for both electricity transmission and gas pipelines have variables that are accessible to the user for modification per time step.

*NLC* is calculated as:

.. math::

    NLC = IC - NOV

where, *NLC* is in $/yr; *IC* is interconnection cost in $/yr; and *NOV* is in $/yr.


Competetion algorithm
~~~~~~~~~~~~~~~~~~~~~

asdf
