[![build](https://github.com/IMMM-SFA/cerf/actions/workflows/build.yml/badge.svg)](https://github.com/IMMM-SFA/cerf/actions/workflows/build.yml)
[![DOI](https://zenodo.org/badge/115649750.svg)](https://zenodo.org/badge/latestdoi/115649750)
[![status](https://joss.theoj.org/papers/28fee3407bbbef020fb4bb19bd451407/status.svg)](https://joss.theoj.org/papers/28fee3407bbbef020fb4bb19bd451407)

## cerf

#### `cerf` is an open-source geospatial Python package for evaluating and analyzing future electricity technology capacity expansion feasibility.

### Purpose
`cerf` was created to:

  - Evaluate the feasibility of a future scenario-driven electricity technology capacity expansion plan as generated by a parent model,

  - Site power plants in the least cost configuration when considering regional economics an on-the-ground barriers to siting,

  - Assist planners and modelers of alternate future realizations of the electricity system to gain an understanding of how siting costs and service area congestion may respond under certain stressors.


### Install `cerf`

**NOTE**:  `cerf` is not officially supported for Ubuntu 18 users due to a system dependency (`GLIBC_2.29`) required by the `whitebox` package which `cerf` uses to conduct spatial analysis. Ubuntu 18 natively includes `GLIBC_2.27`.  It may be possible for Ubuntu 18 users to upgrade to `GLIBC_2.29` but this should be done with careful consideration.  Instead, we officially support `cerf` use for Ubuntu users for versions 20.04.2 LTS and greater.

```bash
pip install cerf
```

### Check out a quickstart tutorial to run `cerf`

Run `cerf` using the quicktart tutorial: [`cerf` Quickstarter](https://immm-sfa.github.io/cerf/user_guide.html#cerf-quickstarter)

### Getting started

New to `cerf`?  Get familiar with what `cerf` is all about in our [Getting Started](https://immm-sfa.github.io/cerf/getting_started.html) docs!

### User guide

Our user guide provides in-depth information on the key concepts of `cerf` with useful background information and explanation.  See our [User Guide](https://immm-sfa.github.io/cerf/user_guide.html)

### Contributing to `cerf`

Whether you find a typo in the documentation, find a bug, or want to develop functionality that you think will make `cerf` more robust, you are welcome to contribute! See our [Contribution Guidelines](https://immm-sfa.github.io/cerf/contributing.html)

### API reference
The reference guide contains a detailed description of the `cerf` API.  The reference describes how the methods work and which parameters can be used.  It assumes that you have an understanding of the key concepts.  See [API Reference](https://immm-sfa.github.io/cerf/cerf.html)
