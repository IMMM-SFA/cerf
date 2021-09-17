Getting started
===============

About
-----

The Capacity Expansion Regional Feasibility model (**cerf**) helps us evaluate the feasibility and structure of future electricity capacity expansion plans by siting power plants in areas that have been deemed the least cost option. We can use **cerf** to gain an understanding of topics such as: 1) whether or not future projected electricity expansion plans from models such as GCAM are possible to achieve, 2) where and which on-the-ground barriers to siting (e.g., protected areas, cooling water availability) may influence our ability to achieve certain expansions, and 3) how power plant infrastructure build outs and value may evolve into the future when considering locational marginal pricing (LMP) based on the supply and demand of electricity from a grid operations model.

Each grid cell in **cerf** is given an initial value of suitable (0) or unsuitable (1) based on a collection of suitability criteria gleaned from the literature. **cerf**'s default suitability layers include both those that are common to all thermal technologies as well as technology-specific suitability criteria. Common suitability layers represent categories such as protected lands, critical habitat areas, and much more. Technology-specific suitability layers are those that satisfy requirements that may not be applicable to all technologies. An example would be minimum mean annual flow requirements for cooling water availability for individual thermal technologies.

Though **cerf** provides sample data to run the conterminous United States (CONUS), it could be extended to function for any country or set of regions that had the following prerequisite data sources:  a spatial representation of substations or electricity transmission infrastructure, a spatial representation of gas pipeline infrastructure if applicable, any regionally applicable spatial data to construct suitability rasters from, access to hourly zonal LMP, and access to technology-specific information and each technologies accompanying electricity capacity expansion plan per region.  The Global Change Analysis Model (`GCAM <https://github.com/JGCRI/gcam-core>`_) is used to build our expansion plans and establish our technology-specific requirements through the end of the century. We derive our LMP from a grid operations model that also is harmonized with GCAM to provide consistent projections of energy system evolution.  See more about how to generalize **cerf** for your research `here <user_guide.rst#generalization>`_.

We introduce a metric named Net Locational Cost (NLC) that is used compete power plant technologies for each grid cell based on the least cost option to site. NLC is calculated by subtracting the Net Operating Value (NOV) of a proposed power plant from the cost of its interconnection to the grid to represent the potential deployment value. Both the NOV parameter which incorporates many technology-specific values such as variable operations and maintenance costs, carbon price, heat rate, etc. and the interconnection cost parameter used for both electricity transmission and gas pipelines are configurable per time step.  All equations used in **cerf** are described in detail in the `documentation <user_guide.rst#fundamental-equations-and-concepts>`_.


Python version support
----------------------

Officially Python 3.7, 3.8, and 3.9


Installation
------------

.. note::

  **cerf** is not officially supported for Ubuntu 18 users due to a system dependency (``GLIBC_2.29``) required by the ``whitebox`` package which **cerf** uses to conduct spatial analysis. Ubuntu 18 natively includes ``GLIBC_2.27``.  It may be possible for Ubuntu 18 users to upgrade to ``GLIBC_2.29`` but this should be done with careful consideration.  Instead, we officially support **cerf** use for Ubuntu users for versions 20.04.2 LTS and greater.

**cerf** can be installed via pip by running the following from a terminal window::

    pip install cerf

Conda/Miniconda users can utilize the ``environment.yml`` stored in the root of this repository by executing the following from a terminal window::

    conda env create --file environment.yml

It may be favorable to the user to create a virtual environment for the **cerf** package to minimize package version conflicts.  See `creating virtual environments <https://docs.python.org/3/library/venv.html>`_ to learn how these function and can be setup.

Installing package data
-----------------------

**cerf** requires package data to be installed from Zenodo to keep the package lightweight.  After **cerf** has been installed, run the following from a Python prompt:

**NOTE**:  The package data will require approximately 195 MB of storage.

.. code-block:: python

    import cerf

    cerf.install_package_data()

This will automatically download and install the package data necessary to run the examples in accordance with the version of **cerf** you are running.  You can pass an alternative directory to install the data into (default is to install it in the package data directory) using ``data_dir``.  When doing so, you must modify the configuration file to point to your custom paths. 


Dependencies
------------

=============   ================
Dependency      Minimum Version
=============   ================
numpy           1.19.4
pandas          1.1.4
rasterio        1.2.3
xarray          0.16.1
PyYAML          5.4.1
requests        2.25.1
joblib          1.0.1
matplotlib      3.3.3
seaborn         0.11.1
whitebox        1.5.1
fiona           1.8.19
pyproj          3.0.1
rtree           0.9.7
shapely         1.7.1
geopandas       0.9.0
=============   ================


Optional dependencies
---------------------

==================    ================
Dependency            Minimum Version
==================    ================
build                 0.5.1
nbsphinx              0.8.6
setuptools            57.0.0
sphinx                4.0.2
sphinx-panels         0.6.0
sphinx-rtd-theme      0.5.2
twine                 3.4.1
pytest                6.2.4
pytest-cov            2.12.1
==================    ================
