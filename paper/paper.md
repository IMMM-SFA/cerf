---
title: 'cerf: A Python package to evaluate the feasibility and costs of power plant siting for alternate futures'
tags:
  - Python
  - power plant siting
  - electricity capacity expansion
authors:
  - name: Chris R. Vernon
    orcid: 0000-0002-3406-6214
    affiliation: 1
  - name: Jennie S. Rice
    orcid: 0000-0002-7833-9456
    affiliation: 1
  - name: Nino Zuljevic
    orcid: 0000-0002-3175-9277
    affiliation: 1
  - name: Kendall Mongird
    orcid: 0000-0003-2807-7088
    affiliation: 1
  - name: Kristian Nelson
    orcid: 0000-0002-6745-167X
    affiliation: 1
  - name: Gokul Iyer
    orcid: 0000-0002-3565-7526
    affiliation: 2
  - name: Nathalie Voisin
    orcid: 0000-0002-6848-449X
    affiliation: 1
  - name: Matthew Binsted
    orcid: 0000-0002-5177-7253
    affiliation: 2
affiliations:
 - name: Pacific Northwest National Laboratory, Richland, WA., USA
   index: 1
 - name: Joint Global Change Research Institute, PNNL, College Park, MD., USA
   index: 2
date: 21 July 2021
bibliography: paper.bib
---

# Summary
Long-term planning for the electric grid, also referred to as resource adequacy planning, informs decisions about investments in infrastructure associated with policy goals with the ultimate objective to maintain or enhance resilience to potential future vulnerabilities under various natural and human stressors [@alova2020global; @craig2018review; @sridharan2019resilience; @JAYADEV2020114267, @khan2021impacts].  Most capacity expansion planning studies are performed at a regional scale, with the last process of actually siting the needed power plants to the care of industry. The cost of siting is a major driver in the cost-benefit analysis led by the industry to decide on final investment.  Future power plant siting costs will depend on a number of factors including the characteristics of the electricity capacity expansion and electricity demand (e.g., fuel mix of future electric power capacity, and the magnitude and geographic distribution of electricity demand growth) as well as the geographic location of power plants [@eia2021lcoe]. Electricity technology capacity expansion plans modeled to represent alternate future conditions meeting a set of scenario assumptions are traditionally compared against historical trends which may not be consistent with current and future conditions [@iyer2015diffusion; @van2015comparing; @wilson2013future].

We present the `cerf` Python package (a.k.a., the Capacity Expansion Regional Feasibility model) which helps evaluate the feasibility of future, scenario-driven electricity capacity expansion plans by siting power plants in areas that have been deemed the least cost option while considering dynamic future conditions [Figure 1].  We can use `cerf` to gain insight to research topics such as:  1) which future projected electricity expansion plans from models such as GCAM-USA [@wise2019representing] are possible to achieve, 2) where and which on-the-ground barriers to siting (e.g., protected areas, cooling water availability) may influence our ability to achieve certain expansion scenarios, and 3) evaluate pathways of sited electricity infrastructure build-outs under evolving locational marginal pricing (LMP) based on the supply and demand of electricity from a grid operations model.

![Illustrative power plant siting for an electricity capacity expansion plan for year 2030.](figure_1.png)

# Statement of Need
Existing tools for identifying criteria for power plants and suitable energy corridors such as the Energy Zones Mapping Tool (EZMT, https://ezmt.anl.gov/) provide a valuable resource assessment for the United States but do not address the influence of regional economics on siting and allow for scenario-driven, forward projections. To the best of our knowledge, `cerf` is the only forward looking power plant siting open-source software that incorporates scenario-driven electricity expansion plans for renewable and non-renewable technology portfolios, zonal LMP from grid operations models, an extensive suite of technology-specific suitability spatial data, and the inclusion of an economic algorithm to site power plants by least cost at a resolution of one square kilometer over the conterminous United States.

`cerf` was originally published in @vernon2018cerf but was constrained in its ability to be utilized and extended due to a set of dependencies in the core module which bound it to a single version of an operating system which is now depreciated. The version of `cerf` described in this publication represents a complete rebirth of the fundamental methodology that was key to the original purpose of `cerf`.  This package now replaces the original design of wrapping a call to execute a pre-compiled C++ module with a Python-only approach that does not have operating system specific requirements. Major advancements were made to the performance of the software to enable `cerf` to be used in, and facilitate, large scenario exploration and uncertainty quantification experiments.  This effort has elucidated the internal decision-making structure of `cerf` and allows users to control key parameters that influence those decisions.  

# Design and Functionality
We utilize a metric named Net Locational Cost (NLC) that is used compete power plant technologies for each grid cell based on the least cost option to site. NLC is calculated by subtracting the Net Operating Value (NOV) of a proposed power plant from the cost of its interconnection to the grid to represent the potential deployment value. Both the NOV parameter which incorporates many technology-specific values such as variable operations and maintenance costs, carbon price, heat rate, etc. and the interconnection cost parameter used for both electricity transmission and gas pipelines are configurable per time step.  All equations used in `cerf` are described in detail in the [documentation](https://immm-sfa.github.io/cerf/user_guide.html#fundamental-equations-and-concepts).

Only grid cells that meet technology-specific, on-the-ground criteria for siting are considered in the competition. `cerf` comes equipped with pre-built suitability rasters for a suite of technologies that account for barriers to siting such as protected areas, densely populated areas, cooling water availability meeting minimum mean annual flow requirements, and much more.  The processing resolution of `cerf` is determined by the suitability data that is utilized leaving flexibility for local analysis.  For example, custom suitability rasters can be created by the user to represent local barriers to siting that may not be generally captured at a regional scale.  

`cerf` is configured using a YAML file describing the input settings for the target model year (see [configuration documentation](https://immm-sfa.github.io/cerf/user_guide.html#configration-file-setup)).  Once the configuration file has been created, the `run()` function is used to launch a process for each year that calculates the per grid cell and technology:  annualized LMP using an 8760 hourly projection for each LMP zone, interconnection cost, NOV, and NLC for grid cells meeting the prescribed suitability criteria.  The desired technologies within each region are then competed to determine the least cost placement of each power plant for an electricity technology capacity expansion plan.  When a grid cell has been chosen for a power plant, the focal cell and a number neighboring cells as defined in the configuration are no longer available for siting.  The competition then resumes until all power plants have been sited or until there is no longer suitable land available.  

A Pandas DataFrame [@mckinney-proc-scipy-2010] containing all siting information is returned as an output from the `run()` function.  The outputs provided by the model are described in the [key outputs documentation](https://immm-sfa.github.io/cerf/user_guide.html#key-outputs).  These outputs can be directly used to initialize siting for a subsequent year using the `initialize_site_data` argument available in the `run()` function.  In this way, we are able to manage the retirement and inheritance of power plants as the model progresses through future years.  It is important when using this feature to ensure that the expansion plan only accounts for new capacity for technology vintage to avoid siting capacity that may already exist in a previous time step.

# Acknowledgements
This research was supported by the U.S. Department of Energy, Office of Science, as part of research in MultiSector Dynamics, Earth and Environmental System Modeling Program.

# References
