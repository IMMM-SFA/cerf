:html_theme.sidebar_secondary.remove:

====
cerf
====

.. rst-class:: lead

   **Capacity Expansion Regional Feasibility model.** An open-source geospatial Python package for evaluating and
   analyzing the feasibility of future electricity technology capacity expansion plans by siting power plants where
   they are the least-cost option.

.. container:: hero-meta

   **Version** |release| · `Source <https://github.com/IMMM-SFA/cerf>`_ ·
   `Issues and ideas <https://github.com/IMMM-SFA/cerf/issues>`_ ·
   `JOSS paper <https://doi.org/10.21105/joss.03601>`_

.. code-block:: bash

   pip install cerf

**cerf** was created to evaluate the on-the-ground siting feasibility of an electricity system expansion plan by:

1. Translating a capacity expansion plan into individually sited renewable and non-renewable power plants across a
   region.
2. Emulating regional practices that address local congestion and interconnection costs as well as the social, land,
   and policy-based constraints faced by developers.
3. Providing a flexible and computationally efficient tool to understand the relative importance of different factors
   affecting the feasibility of siting new infrastructure, such as energy justice, land suitability, water
   availability, and emissions.

.. grid:: 1 2 2 2
   :gutter: 3
   :class-container: index-cards

   .. grid-item-card:: Getting started
      :link: getting_started
      :link-type: doc
      :class-card: index-card

      What **cerf** does, how to install it and its package data, and which Python and dependency versions are
      supported.

   .. grid-item-card:: Quickstart
      :link: quickstart
      :link-type: doc
      :class-card: index-card

      Site a full CONUS expansion plan in a few lines, chain runs across years with retirement, run regions in
      parallel, and plot the result.

   .. grid-item-card:: User guide
      :link: user_guide
      :link-type: doc
      :class-card: index-card

      Configuration file reference, input data requirements, the NOV / interconnection / NLC equations, the
      competition algorithm and every output column.

   .. grid-item-card:: API reference
      :link: api
      :link-type: doc
      :class-card: index-card

      Every public function and class - ``run``, ``Model``, ``Stage``, ``ProcessRegion``, ``Competition``,
      ``Interconnection`` and more.

How it works
------------

.. grid:: 1 3 3 3
   :gutter: 3

   .. grid-item-card:: 1. Stage
      :class-card: step-card

      Build per-technology grids of locational marginal price, interconnection cost, generation, operating cost and
      Net Operational Value, and combine the technology suitability rasters.

   .. grid-item-card:: 2. Compete
      :class-card: step-card

      Region by region, technologies compete for each cell on Net Locational Cost; the winner is sited, its buffer is
      excluded, and the loop repeats until the expansion plan is met or no land remains.

   .. grid-item-card:: 3. Aggregate
      :class-card: step-card

      Return one row per sited plant with coordinates, costs, LMP zone and retirement year - ready to feed the next
      year's run or your own analysis.

The metric that drives siting is **Net Locational Cost (NLC)**: the annualised cost of interconnecting a plant to the
electricity transmission network (and to a gas pipeline for gas technologies) minus its **Net Operational Value
(NOV)** - the value of the electricity it generates at the local locational marginal price less its operating costs.
Every input to both terms is configurable per technology and per time step; see
:doc:`user_guide` for the equations.

.. toctree::
   :maxdepth: 2
   :hidden:

   getting_started
   quickstart
   user_guide
   api

.. toctree::
   :caption: Project
   :maxdepth: 1
   :hidden:

   contributing
   release_notes
   publications
   how_to_cite
   authors
   license
   footer
