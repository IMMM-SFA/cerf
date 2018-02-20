# cerf - The Capacity Expansion Regional Feasibility (CERF) model

## A geospatial model for assessing and analyzing future energy technology expansion feasibility

## Notice
This repository uses the Git Large File Storage (LFS) extension (see https://git-lfs.github.com/ for details).  Please run the following command before cloning if you do not already have Git LFS installed:
`git lfs install`

## Contact
For questions, technical supporting and user contribution, please contact:

Vernon, Chris R <Chris.Vernon@pnnl.gov>

## Overview
The Capacity Expansion Regional Feasibility (CERF) model is an open-source geospatial model, written in Python and C++, that is designed to determine the on-the-ground feasibility of achieving a projected energy technology expansion plan.  Integrated assessment models and grid expansion models typically do not have sufficient spatial, temporal, or process-level resolution to account for technology-specific siting considerations—for example, the value or costs of connecting a new power plant to the electric grid at a particular location or whether there is sufficient cooling water to support the installation of multiple thermal power plants in a certain region. CERF was developed to specifically examine where power plant locations can be feasibly sited when considering high spatial resolution siting constraints as well as the net locational costs (i.e., considering both net operating value and interconnection costs), at a spatial resolution of 1 km2. The outputs from CERF can provide insight into factors that influence energy system resilience under a variety of future scenarios, can be used to refine model based projections, and can also be directly useful for capacity expansion planning exercises. CERF is open-source and publicly available via GitHub.
