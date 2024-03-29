===============
User guide
===============

Generalization
--------------

Though **cerf** is demonstrated for the conterminous United States (CONUS), the package could easily be used in research ranging from regional to global analysis.

**cerf** requires the following inputs to be able to operate:

- A shapefile of substations as points.  The substation file must contain a field defining the minimum voltage per substation named "min_volt".
- A shapefile of gas pipelines as polylines if siting gas technologies.
- A raster containing region IDs.  Each grid cell has the value of its parent region.  Currently, this is demonstrated using US states, though this could be generalized to any region/country/locale identifier matching what the electricity expansion plan provides.
- A raster containing locational marginal pricing (LMP) zone IDs.  Each grid cell has the ID of its LMP zones.  These zones are representative of the nodal structure of the underlying model or software that produces the LMPs.  Production cost models to generate this value are not US-specific and this could be generated from any number of open-source and/or commercial products.
- A file of LMPs per zone (corresponding to the aforementioned raster) for each 8760 hour.  Again, the source model or dataset that these are generated from does not have to be US-specific.
- An electricity capacity expansion plan and its accompanying technology-specific information (e.g., variable O&M, fuel price, etc.).  For the CONUS, we use the 50 US-state version of GCAM.  However, GCAM is a global model and can produce this data for each of its regions.
- Both the `region-abbrev_to_region-name.yml` and the `region-name_to_region-id.yml` files can be replaced with regional information.
- Other variable information which is able to be modified per run, are the assumed interconnection costs per km to a substation KV class and the cost per km to connect to a gas pipeline if applicable.
- Lastly, are the suitability rasters which can be composed of any number of locally-relevant exclusion criteria (e.g., protected area, critical habitat, etc.) per technology being sited in the expansion plan.

Let us know if you are using **cerf** in your research in our `discussion thread <https://github.com/IMMM-SFA/cerf/discussions/61>`_!


Setting up a **cerf** run
-------------------------

The following with indroduce you to the input data required by **cerf** and how to set up a configuration file to run **cerf**.

Configuration file setup
~~~~~~~~~~~~~~~~~~~~~~~~

The **cerf** package utilizes a YAML configuration file customized by the user with project level and technology-specific settings, an electricity technology capacity expansion plan, and LMP zone data for each year intended to model. **cerf** comes equipped with prebuilt configuration files for years 2010 through 2050 to provide an illustrative example. Each example configuration file can be viewed using the following:

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

    +---------------------------------+---------------------------------------------+----------+----------+
    | Name                            | Description                                 | Unit     | Type     |
    +=================================+=============================================+==========+==========+
    | <tech id number>                | | This is an integer ID key given to the    | NA       | int      |
    |                                 | | technology for reference purposes.  This  |          |          |
    |                                 | | ID should match the corresponding         |          |          |
    |                                 | | technology in the electricity technology  |          |          |
    |                                 | | expansion plan.                           |          |          |
    +---------------------------------+---------------------------------------------+----------+----------+
    | tech_name                       | Name of the technology                      | NA       | str      |
    +---------------------------------+---------------------------------------------+----------+----------+
    | lifetime_yrs                    | | Asset lifetime used in calculating        | n_years  | int      |
    |                                 | | annuity factor                            |          |          |
    +---------------------------------+---------------------------------------------+----------+----------+
    | operational_life_yrs            | | A separate parameter to allow for early   | n_years  | int      |
    |                                 | | retirement of power plants (i.e., not     |          |          |
    |                                 | | operating to their full expected life) and|          |          |
    |                                 | | is set as the number of years after       |          |          |
    |                                 | | siting that the plant gets retired.       |          |          |
    +---------------------------------+---------------------------------------------+----------+----------+
    | capacity_factor_fraction        | | Defined as average annual power generated | fraction | float    |
    |                                 | | divided by the potential output if the    |          |          |
    |                                 | | plant operated at its rated capacity for a|          |          |
    |                                 | | year                                      |          |          |
    +---------------------------------+---------------------------------------------+----------+----------+
    | variable_om_esc_rate_fraction   | Escalation rate of variable cost            | fraction | float    |
    +---------------------------------+---------------------------------------------+----------+----------+
    | fuel_price_esc_rate_fraction    | Escalation rate of fuel                     | fraction | float    |
    +---------------------------------+---------------------------------------------+----------+----------+
    | unit_size_mw                    | The size of the expected power plant        | MW       | float    |
    +---------------------------------+---------------------------------------------+----------+----------+
    | variable_om_usd_per_mwh         | | Variable operation and maintenance costs  | $/MWh    | float    |
    |                                 | | of yearly capacity use                    |          |          |
    +---------------------------------+---------------------------------------------+----------+----------+
    | heat_rate_btu_per_kWh           | | Amount of energy used by a power plant to | Btu/kWh  | float    |
    |                                 | | generate one kilowatt-hour of electricity |          |          |
    +---------------------------------+---------------------------------------------+----------+----------+
    | fuel_price_usd_per_mmbtu        | Cost of fuel per unit                       | $/MMbtu  | float    |
    +---------------------------------+---------------------------------------------+----------+----------+
    | carbon_capture_rate_fraction    | Rate of carbon capture                      | fraction | float    |
    +---------------------------------+---------------------------------------------+----------+----------+
    | fuel_co2_content_tons_per_btu   | | CO2 content of the fuel and the heat rate | tons/Btu | float    |
    |                                 | | of the technology                         |          |          |
    +---------------------------------+---------------------------------------------+----------+----------+
    | discount_rate                   | The time value of money in real terms       | fraction | float    |
    +---------------------------------+---------------------------------------------+----------+----------+
    | carbon_tax_esc_rate_fraction    | Escalation rate of carbon                   | fraction | float    |
    +---------------------------------+---------------------------------------------+----------+----------+
    | carbon_tax_usd_per_ton          | | The fee imposed on the burning of         | $/ton    | float    |
    |                                 | | carbon-based fuels                        |          |          |
    +---------------------------------+---------------------------------------------+----------+----------+
    | buffer_in_km                    | | Buffer around the site to apply in        | n_km     | int      |
    |                                 | | kilometers which becomes unsuitable for   |          |          |
    |                                 | | other sites after siting                  |          |          |
    +---------------------------------+---------------------------------------------+----------+----------+
    | require_pipelines               | | If the technology is gas related pipelines| NA       | bool     |
    |                                 | | will be used when calculating the         |          |          |
    |                                 | | interconnection cost                      |          |          |
    +---------------------------------+---------------------------------------------+----------+----------+
    | suitability_raster_file         | | Full path with file name and extension to | NA       | str      |
    |                                 | | the accompanying suitability raster file  |          |          |
    +---------------------------------+---------------------------------------------+----------+----------+


The following is an example implementation in the YAML configuration file:

.. code-block:: yaml

    technology:

        9:
            tech_name: biomass
            lifetime_yrs: 60
            operational_life_yrs: 60
            capacity_factor_fraction: 0.6090000000000005
            variable_om_esc_rate_fraction: -0.00398993418629034
            fuel_price_esc_rate_fraction: 0.0
            unit_size_mw: 80
            variable_om: 11.68495803744351
            heat_rate_btu_per_kWh: 15117.64999999997
            fuel_price_usd_per_mmbtu: 0.0
            carbon_capture_rate_fraction: 0.0
            fuel_co2_content_tons_per_btu: 0.3035999999999996
            discount_rate: 0.05
            carbon_tax_esc_rate_fraction: 0.0
            carbon_tax_usd_per_ton: 0.0
            buffer_in_km: 5
            require_pipelines: False
            suitability_raster_file: <path to file>


``expansion_plan``
^^^^^^^^^^^^^^^^^^

These are technology-specific settings.

.. table::

    +-------------------------+-----------------------------------------------+----------+----------+
    | Name                    | Description                                   | Unit     | Type     |
    +=========================+===============================================+==========+==========+
    | <region name>           | | Name key of region in all lower case with   | NA       | str      |
    |                         | | underscore separation                       |          |          |
    +-------------------------+-----------------------------------------------+----------+----------+
    | <tech id key>           | | Technology ID key matching what is in the   | NA       | int      |
    |                         | | technology section (e.g. 9)                 |          |          |
    +-------------------------+-----------------------------------------------+----------+----------+
    | tech_name               | | Name of the technology matching the name    | NA       | str      |
    |                         | | in the technology section                   |          |          |
    +-------------------------+-----------------------------------------------+----------+----------+
    | n_sites                 | Number of sites desired                       | n_sites  | int      |
    +-------------------------+-----------------------------------------------+----------+----------+

The following is an example implementation in the YAML configuration file:

.. code-block:: yaml

    expansion_plan:

        arizona:
            9:
                tech_name: biomass
                n_sites: 2


``lmp_zones``
^^^^^^^^^^^^^

These are the lmp zones data representing the linkage between each grid and technology and their locational marginal price (LMP).

.. table::

    +----------------------------------+---------------------------------------------+----------+----------+
    | Name                             | Description                                 | Unit     | Type     |
    +==================================+=============================================+==========+==========+
    | lmp_zone_raster_file             | | Full path with file name and extension to | NA       | str      |
    |                                  | | the lmp zoness raster file                |          |          |
    +----------------------------------+---------------------------------------------+----------+----------+
    | lmp_zone_raster_nodata_value     | No data value in the lmp zones raster       | NA       | float    |
    +----------------------------------+---------------------------------------------+----------+----------+
    | lmp_hourly_data_file             | | LMP CSV file containing 8760 LMP per zone | $/MWh    | str      |
    |                                  | | where columns are each zone with a numeric|          |          |
    |                                  | | zone ID header that corresponds with the  |          |          |
    |                                  | | zones represented in the                  |          |          |
    |                                  | | ``lmp_zone_raster_file`` found in the     |          |          |
    |                                  | | ``lmp_zones`` section and an              |          |          |
    |                                  | | additional hour column named ``hour``     |          |          |
    |                                  | | holding the hour of each record           |          |          |
    +----------------------------------+---------------------------------------------+----------+----------+

The following is an example implementation in the YAML configuration file:

.. code-block:: yaml

    lmp_zones:

        lmp_zone_raster_file: <path to zone raster>
        lmp_zone_raster_nodata_value: 255
        lmp_hourly_data_file: <path to data file>


The `cerf` package comes equipped with a sample lmp zoness raster file and a sample hourly (8760) locational marginal price file for illustrative purposes only.

You can take a look at the lmp zoness raster file by running:

.. code-block:: python

    import cerf

    lmp_zone_file = cerf.sample_lmp_zones_raster_file()


You can also view the sample hourly locational marginal price file as a Pandas DataFrame using:

.. code-block:: python

    import cerf

    df = cerf.get_sample_lmp_data()


``infrastructure``
^^^^^^^^^^^^^^^^^^

These are the electricity transmission and gas pipeline infrastructure data.

.. table::

    +----------------------------+---------------------------------------------+----------+----------+
    | Name                       | Description                                 | Unit     | Type     |
    +============================+=============================================+==========+==========+
    | substation_file            | | Full path with file name and extension to | NA       | str      |
    |                            | | he input substations shapefile. If        |          |          |
    |                            | | ``null`` **cerf** will use the default    |          |          |
    |                            | | data stored in the package.               |          |          |
    +----------------------------+---------------------------------------------+----------+----------+
    | pipeline_file              | | Full path with file name and extension to | NA       | str      |
    |                            | | he input pipelines shapefile. If ``null`` |          |          |
    |                            | | CERF will use the default data stored in  |          |          |
    |                            | | the package.                              |          |          |
    +----------------------------+---------------------------------------------+----------+----------+
    | transmission_costs_file    | | A YAML file containing the costs of       | NA       | str      |
    |                            | | connection per km to a substation having  |          |          |
    |                            | | a certain minimum voltage range. Default  |          |          |
    |                            | | is to load from the defualt               |          |          |
    |                            | | 'costs_per_kv_substation.yml' file        |          |          |
    |                            | | by specifying ``null``                    |          |          |
    +----------------------------+---------------------------------------------+----------+----------+
    | pipeline_costs_file        | | A YAML file containing the costs of       | NA       | str      |
    |                            | | connection per km to a gas pipeline.      |          |          |
    |                            | | Default is to load from the default       |          |          |
    |                            | | 'costs_gas_pipeline.yml' file             |          |          |
    |                            | | by specifying ``null``                    |          |          |
    +----------------------------+---------------------------------------------+----------+----------+
    | output_rasterized_file     | Write distance raster                       | NA       | bool     |
    +----------------------------+---------------------------------------------+----------+----------+
    | output_dist_file           | Write distance raster                       | NA       | bool     |
    +----------------------------+---------------------------------------------+----------+----------+
    | output_alloc_file          | Write allocation file                       | NA       | bool     |
    +----------------------------+---------------------------------------------+----------+----------+
    | output_cost_file           | Write cost file                             | NA       | bool     |
    +----------------------------+---------------------------------------------+----------+----------+
    | output_dir                 | If writing files, specify an out directory  | NA       | bool     |
    +----------------------------+---------------------------------------------+----------+----------+
    | interconnection_cost_file  | | Full path with the file name and extension| NA       | str      |
    |                            | | to a preprocessed interconnection cost    |          |          |
    |                            | | NPY file that has been previously written.|          |          |
    |                            | | If ``null``, interconnection costs will be|          |          |
    |                            | | calculated.                               |          |          |
    +----------------------------+---------------------------------------------+----------+----------+


The following is an example implementation in the YAML configuration file:

.. code-block:: yaml

    infrastructure:

        substation_file: <path to substation shapefile>
        transmission_costs_file: <path to the yaml file>
        pipeline_file: <path to the pipeline file>
        output_rasterized_file: false
        output_dist_file: false
        output_alloc_file: false
        output_cost_file: false


You can view the built-in costs per kV to connect to a substation using:

.. code-block:: python

    import cerf

    costs_dict = cerf.costs_per_kv_substation()


Preparing suitability rasters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **cerf** package comes equipped with sample suitability data but you can build your on as well.

You can see which suitability rasters are available in the `cerf` package by running the following after installing the package data:

.. code-block:: python

    import cerf

    cerf.list_available_suitability_files()


The sample rasters for spatial suitability at a resolution of 1km over the CONUS use the following format.  Suitability rasters can be prepared using any GIS.

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


Locational Marginal Price
~~~~~~~~~~~~~~~~~~~~~~~~~

Locational Marginal Pricing (LMP) represents the cost of making and delivering electricity over an interconnected network of service nodes. LMPs are delivered on an hourly basis (8760 hours for the year) and help us to understand aspects of generation and congestion costs relative to the supply and demand of electricity when considering existing transmission infrastructure.  LMPs are a also driven by factors such as the cost of fuel which **cerf** also takes into account when calculating a power plants :ref:`Net Operating Value`.  When working with a scenario-driven grid operations model to evaluate the future evolution of the electricity system, **cerf** can ingest LMPs, return the sited generation per service area for the time step, and then continue this iteration through all future years to provide a harmonized view how the electricity system may respond to stressors in the future.

**cerf** was designed to ingest a single CSV file of LMPs per service area for each of the 8760 hours in a year where LMPs are in units $/MWh.  Mean LMPs representing annual trends are then calculated over the time period corresponding to each technology's capacity factor using the following logic:

.. code:: sh

  FOR each service area AND technology

    SORT LMP 8760 values descending and rank 1..8760 where 1 is the largest LMP value;

    IF the capacity factor is == 1.0:
      MEAN of all values;

    ELSE IF the capacity factor is >= 0.5:
      MEAN of values starting in the rank position
      CEILING(8760 * (1 - capacity factor)) through 8760;

    ELSE IF the 0.0 < capacity factor < 0.5:
      MEAN of values starting in the rank position 1 through
      CEILING(8760 * (1 - capacity factor));

    ELSE:
      FAIL;

.. note::

  **cerf** comes with an LMP dataset for illustrative purposes only which can be accessed using the ``get_sample_lmp_file()`` function.  The service areas in this file correspond with the sample lmp zoness raster file in the **cerf** package which defines the service area ID for each grid cell in the CONUS.  This raster file can also be accessed using ``sample_lmp_zones_raster_file()`` function.


Tutorials
---------

**cerf** quickstarter
~~~~~~~~~~~~~~~~~~~~~

.. include:: quickstarter.rst


Running the quickstarter locally
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can download the **cerf** quickstarter Jupyter notebook here: `cerf quickstarter <https://github.com/IMMM-SFA/cerf/blob/main/notebooks/quickstarter.ipynb>`_

This will allow you to run the tutorial interactively on your local computer.  Installation instructions for installing Jupyter software can be found `here <https://jupyter.org/install>`_.

Once you have Jupyter up-and-running, make sure you install **cerf** and its package data by running:

.. code-block:: bash

  python3 -m pip install cerf

  python3 -c 'import cerf; cerf.install_package_data()'

where, ``python3`` would be the instance of Python that you installed Jupyter on.  Now you are ready to explore **cerf**!


Fundamental equations and concepts
----------------------------------

The following are the building blocks of how **cerf** sites power plants.


Net Operating Value
~~~~~~~~~~~~~~~~~~~

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

where, *LMP* is the locational marginal price (*LMP*) in $/MWh and *LF*\ :subscript:`fuel` \ is the levelization factor of fuel.  *LMP* is also an input to **cerf** and is described in full in the :ref:`Locational Marginal Price` section.

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

where, *IC* is Interconnection Cost in $/yr; *D*\ :subscript:`elec` is the distance to the nearest suitable electricity transmission infrastructure (e.g., substation) in kilometers; *C*\ :subscript:`elec` is the electric grid interconnection captial cost in thous$/km; *D*\ :subscript:`gas` is the distance to the nearest suitable gas pipeline in kilometers; *C*\ :subscript:`gas` is the gas interconnection capital cost in thous$/km and *AF* is the annuity factor.

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


Competition algorithm
~~~~~~~~~~~~~~~~~~~~~

Technology competition algorithm for CERF.

Grid cell level net locational cost (NLC) per technology and an electricity technology capacity expansion plan are used to compete technologies against each other to see which will win the grid cell. The technology that wins the grid cell is then sited until no further winning cells exist. Once sited, the location of the winning technology’s grid cell, along with its buffer, are no longer available for siting. The competition array is recalculated after all technologies have passed through an iteration. This process is repeated until there are either no cells left to site or there are no more power plants left to satisfy the expansion plan for any technology. For technologies that have the same NLC value in multiple grid cells that win the competition, random selection is available by default. If the user wishes to have the outcomes be repeatable, the randomizer can be set to False and a random seed set.


Key outputs
-----------

The following are the outputs and their descriptions from the Pandas DataFrame that is generated when calling ``run()`` to site power plant for all regions in the CONUS for all technologies:

.. list-table::
    :header-rows: 1

    * - Name
      - Description
      - Units
    * - region_name
      - Name of region
      - NA
    * - tech_id
      - Technology ID
      - NA
    * - tech_name
      - Technology name
      - NA
    * - unit_size_mw
      - Power plant unit size
      - MW
    * - xcoord
      - X coordinate in the default `CRS <https://spatialreference.org/ref/esri/usa-contiguous-albers-equal-area-conic/>`_
      - meters
    * - ycoord
      - Y coordinate in the default `CRS <https://spatialreference.org/ref/esri/usa-contiguous-albers-equal-area-conic/>`_
      - meters
    * - index
      - Index position in the flattend 2D array
      - NA
    * - buffer_in_km
      - Exclusion buffer around site
      - km
    * - sited_year
      - Year of siting
      - year
    * - retirement_year
      - Year of retirement
      - year
    * - lmp_zone
      - LMP zone ID
      - NA
    * - locational_marginal_price_usd_per_mwh
      - See :ref:`Locational marginal price (LMP)`
      - $/MWh
    * - generation_mwh_per_year
      - See :ref:`Generation (G)`
      - MWh/yr
    * - operating_cost_usd_per_year
      - See :ref:`Operating cost (OC)`
      - $/yr
    * - net_operational_value
      - See :ref:`Net Operating Value`
      - $/yr
    * - interconnection_cost
      - See :ref:`Interconnection Cost`
      - $/yr
    * - net_locational_cost
      - See :ref:`Net Locational Cost`
      - $/yr
    * - capacity_factor_fraction
      - Capacity factor
      - fraction
    * - carbon_capture_rate_fraction
      - Carbon capture rate
      - fraction
    * - fuel_co2_content_tons_per_btu
      - Fuel CO2 content
      - tons/Btu
    * - fuel_price_usd_per_mmbtu
      - Fuel price
      - $/MMBtu
    * - fuel_price_esc_rate_fraction
      - Fuel price escalation rate
      - fraction
    * - heat_rate_btu_per_kWh
      - Heat rate
      - Btu/kWh
    * - lifetime_yrs
      - Technology lifetime for annuity
      - years
    * - operational_life_yrs
      - Operational lifetime for retirement
      - years
    * - variable_om_usd_per_mwh
      - Variable operation and maintenance costs of yearly capacity use
      - $/mWh
    * - variable_om_esc_rate_fraction
      - Variable operation and maintenance costs escalation rate
      - fraction
    * - carbon_tax_usd_per_ton
      - Carbon tax
      - $/ton
    * - carbon_tax_esc_rate_fraction
      - Carbon tax escalation rate
      - fraction
