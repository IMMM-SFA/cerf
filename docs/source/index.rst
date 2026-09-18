:hide-toc:

.. meta::
   :description: Explore cerf, the open-source geospatial Python model for evaluating electricity capacity expansion feasibility and least-cost power plant siting.

====
cerf
====

.. container:: cerf-hero

   .. container:: cerf-hero-copy

      .. rst-class:: cerf-eyebrow

         GEOSPATIAL CAPACITY EXPANSION MODELING

      .. rst-class:: cerf-hero-title

         Spatially aware energy expansion.

      .. rst-class:: lead

         **Capacity Expansion Regional Feasibility (CERF) model.** An open-source geospatial Python package for evaluating and
         analyzing the feasibility of future electricity technology capacity expansion plans by siting power plants where
         they are the least-cost option.

      .. container:: cerf-actions

         .. button-ref:: getting_started
            :ref-type: doc
            :color: primary
            :class: cerf-button-primary

            Get started →

         .. button-ref:: quickstart
            :ref-type: doc
            :color: secondary
            :outline:

            Run the quickstart

   .. container:: cerf-hero-art

      .. image:: _static/siting-landscape.svg
         :alt: Conceptual layers of land suitability and local costs, connected to individual power plant sites.
         :width: 640
         :height: 480

      .. rst-class:: cerf-art-caption

         Regional plans. Local possibilities.

.. container:: cerf-install-strip

   .. container:: cerf-install-label

      .. rst-class:: cerf-eyebrow

         START EXPLORING

      Install. Configure. Site.

   .. code-block:: bash

      pip install cerf

.. container:: hero-meta

   **Version** |release| · `Source <https://github.com/IMMM-SFA/cerf>`_ ·
   `Issues and ideas <https://github.com/IMMM-SFA/cerf/issues>`_ ·
   `JOSS paper <https://doi.org/10.21105/joss.03601>`_

Explore the documentation
-------------------------

From your first model run to the details behind every siting decision.

.. grid:: 1 2 2 2
   :gutter: 3
   :class-container: index-cards

   .. grid-item-card:: Getting started
      :link: getting_started
      :link-type: doc
      :class-card: index-card

      What **cerf** does, how to install it and its package data, and which Python and dependency versions are
      supported.

      +++
      Set up your environment →

   .. grid-item-card:: Quickstart
      :link: quickstart
      :link-type: doc
      :class-card: index-card

      Site a full CONUS expansion plan in a few lines, chain runs across years with retirement, run regions in
      parallel, and plot the result.

      +++
      Run your first model →

   .. grid-item-card:: User guide
      :link: user_guide
      :link-type: doc
      :class-card: index-card

      Configuration file reference, input data requirements, the NOV / interconnection / NLC equations, the
      competition algorithm and every output column.

      +++
      Understand the model →

   .. grid-item-card:: API reference
      :link: api
      :link-type: doc
      :class-card: index-card

      Every public function and class - ``run``, ``Model``, ``Stage``, ``ProcessRegion``, ``Competition``,
      ``Interconnection`` and more.

      +++
      Explore the Python API →

From expansion plans to places
------------------------------

**cerf** was created to evaluate the on-the-ground siting feasibility of an electricity system expansion plan by:

.. rst-class:: cerf-principles

1. Translating a capacity expansion plan into individually sited renewable and non-renewable power plants across a
   region.
2. Emulating regional practices that address local congestion and interconnection costs as well as the social, land,
   and policy-based constraints faced by developers.
3. Providing a flexible and computationally efficient tool to understand the relative importance of different factors
   affecting the feasibility of siting new infrastructure, such as energy justice, land suitability, water
   availability, and emissions.

How it works
------------

.. grid:: 1 1 3 3
   :gutter: 3
   :class-container: cerf-workflow

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

.. container:: cerf-metric

   .. rst-class:: cerf-eyebrow

      THE SITING DECISION

   The metric that drives siting is **Net Locational Cost (NLC)**: the annualised cost of interconnecting a plant to the
   electricity transmission network (and to a gas pipeline for gas technologies) minus its **Net Operational Value
   (NOV)** - the value of the electricity it generates at the local locational marginal price less its operating costs.
   Every input to both terms is configurable per technology and per time step; see
   :doc:`user_guide` for the equations.

.. container:: cerf-community

   .. rst-class:: cerf-eyebrow

      OPEN SCIENCE, SHARED PROGRESS

   Built for research. Better together.

   Explore the :doc:`publications`, learn :doc:`how to cite cerf <how_to_cite>`, or help shape what comes next by
   :doc:`contributing <contributing>`.

.. toctree::
   :caption: Documentation
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
