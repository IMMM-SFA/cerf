[![build](https://github.com/IMMM-SFA/cerf/actions/workflows/build.yml/badge.svg)](https://github.com/IMMM-SFA/cerf/actions/workflows/build.yml)
[![codecov](https://codecov.io/gh/IMMM-SFA/cerf/branch/version-two/graph/badge.svg?token=9jbGJv8XCJ)](https://codecov.io/gh/IMMM-SFA/cerf)
[![Documentation Status](https://readthedocs.org/projects/im3-cerf/badge/?version=latest)](https://im3-cerf.readthedocs.io/en/latest/?badge=latest)
[![DOI](https://zenodo.org/badge/115649750.svg)](https://zenodo.org/badge/latestdoi/115649750)

## cerf

### An open-source geospatial Python package for assessing and analyzing future electricity technology capacity expansion feasibility

## Overview
The Capacity Expansion Regional Feasibility model (CERF) helps us evaluate the feasibility and structure of future electricity capacity expansion plans by siting power plants in areas that have been deemed the least cost option. We can use CERF to gain an understanding of topics such as: 1) whether or not future projected electricity expansion plans from models such as GCAM are possible to achieve, 2) where suitability (e.g., cooling water availability) may influence our ability to achieve certain expansions, and/or 3) how power plant infrastructure build outs and value may evolve into the future when considering locational marginal pricing from a grid operations model.

CERF currently operates at a 1 km<sup>2</sup> resolution over the conterminous United States. Each grid cell is given an initial value of suitable (0) or unsuitable (1) based on a collection of suitability criteria gleaned from the literature. CERF's default suitability layers include both those that are common to all thermal technologies as well as technology-specific suitability criteria. Common suitability layers represent categories such as protected lands, critical habitat areas, and much more. Technology-specific suitability layers are those that satisfy requirements that may not be applicable to all technologies. An example would be minimum mean annual flow requirements for cooling water availability for individual thermal technologies.

We introduce a metric named Net Locational Cost (NLC) that is used compete power plant technologies for each grid cell based on the least expensive option. NLC is calculated by subtracting the Net Operational Value (NOV) of the proposed power plant from the cost of its interconnection to the grid to represent the potential deployment value. Both the NOV parameter which incorporates many technology-specific values such as variable operations and maintenance costs, carbon price, heat rate, etc. and the interconnection cost parameter used for both electricity transmission and gas pipelines have variables that are accessible to the user for modification per time step.

## Get Started with CERF

### Install `cerf`

```bash
pip install cerf
```

### Check out a quickstart tutorial to run `cerf`

Link to docs

### Check out the docs to learn how to setup a custom `cerf` run

Read the docs here.
