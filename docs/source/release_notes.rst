Release notes
=============

This is the list of changes to **cerf** between each release. For full details,
see the `commit logs <https://github.com/IMMM-SFA/cerf/commits>`_.

Version 2.5.0
_____________

Performance, correctness and maintainability release. Siting results for a seeded run are **identical** to 2.4.1
(verified for every change against the 2010 CONUS sample with ``benchmark/run_reference.py --compare``); the full
sample run is ~4× faster (20.4 s → ~5.2 s sequential) and stages in 4.2 GB instead of 7.4 GB. The evaluation that
drove this release is in ``docs/IMPROVEMENT_EVALUATION.md``.

Performance

- Vectorised buffer removal in the competition loop https://github.com/IMMM-SFA/cerf/pull/118
- Look-up-table zone assignment and single sort in LMP staging (18× faster) https://github.com/IMMM-SFA/cerf/pull/119
- Region raster read once; bounding boxes precomputed https://github.com/IMMM-SFA/cerf/pull/127
- ``+inf`` sentinels instead of masked arrays in the competition loop https://github.com/IMMM-SFA/cerf/pull/128
- ``uint8`` suitability, broadcast views for spatially constant costs, deferred metric lookups https://github.com/IMMM-SFA/cerf/pull/129
- Regions cropped before dispatch to process backends (``loky`` 294 s → 9 s); single output concat https://github.com/IMMM-SFA/cerf/pull/130
- Index-array buffers; bulk shapely → ``rasterize`` conversion without a temp file https://github.com/IMMM-SFA/cerf/pull/134

Bug fixes

- ``preprocess_hifld_substations`` ``isin`` signature error https://github.com/IMMM-SFA/cerf/pull/120
- ``ZeroDivisionError`` in NOV levelization when escalation equals the discount rate https://github.com/IMMM-SFA/cerf/pull/121
- Model no longer mutates the caller's configuration dictionary https://github.com/IMMM-SFA/cerf/pull/123
- ``config_dict=None`` with a file crashed; dead branch removed https://github.com/IMMM-SFA/cerf/pull/124
- Named ``cerf`` logger with idempotent handlers; root logger untouched https://github.com/IMMM-SFA/cerf/pull/125
- Interconnection distances honour the raster pixel size (``sampling=`` in the EDT) https://github.com/IMMM-SFA/cerf/pull/131
- Per-competition random state; seeded runs identical across backends (``threading`` now deterministic) https://github.com/IMMM-SFA/cerf/pull/132
- Nodata handling, coordinate arrays via rasterio transform, case-insensitive region lookup, complete ``sited_dtypes`` https://github.com/IMMM-SFA/cerf/pull/133
- ``lifetime_yrs`` / ``operational_life_yrs`` validated and documented; ``EmptyRegionResult`` instead of ``None``; suitability honours raster nodata https://github.com/IMMM-SFA/cerf/pull/135
- Robust Zenodo download with retries; data URL falls back to the newest registered version https://github.com/IMMM-SFA/cerf/pull/122 https://github.com/IMMM-SFA/cerf/pull/139

API and packaging

- Explicit ``__all__``; ``__version__`` from package metadata; ``yaml.safe_load`` https://github.com/IMMM-SFA/cerf/pull/136
- ``RegionData`` bundle and explicit ``run()`` on ``ProcessRegion`` / ``Competition`` (``auto_run=False`` to construct without running) https://github.com/IMMM-SFA/cerf/pull/137
- Dependencies dropped: ``rioxarray``, ``seaborn``, ``pyarrow``, ``rtree``, ``fiona``, ``pyproj`` (the last two remain transitive via geopandas); ``shapely>=2.0`` required https://github.com/IMMM-SFA/cerf/pull/133 https://github.com/IMMM-SFA/cerf/pull/136
- Deprecated: ``default_suitabiity_files`` (misspelling) → ``default_suitability_files``; ``Interconnection`` ``region_abbrev_to_name_file`` / ``region_name_to_id_file`` are ignored.
- **Python 3.10 or newer is now required** (3.9 reached end of life in October 2025); 3.10–3.12 tested in CI; end-to-end tests, ``ruff`` lint, coverage upload https://github.com/IMMM-SFA/cerf/pull/138 https://github.com/IMMM-SFA/cerf/pull/139
- ``MANIFEST.in`` removed (hatchling); Dockerfile builds from the checkout and pre-installs package data https://github.com/IMMM-SFA/cerf/pull/139


Version 2.4.1
_____________

- Replaced deprecated ``pkg_resources`` usage with ``importlib.resources`` and ``importlib.metadata``; cerf package data must now be installed on the filesystem https://github.com/IMMM-SFA/cerf/pull/117


Version 2.4.0
_____________

- Replaced whitebox dependency used in Euclidean distance calculations with SciPy https://github.com/IMMM-SFA/cerf/pull/107
- Limited NumPy version to less than 2 due Fiona dependency https://github.com/IMMM-SFA/cerf/pull/105
- Updated depreciated calls to xarray https://github.com/IMMM-SFA/cerf/pull/105 


Version 2.2.1
_____________

- Changed docs to thousands of km for interconnection cost variables https://github.com/IMMM-SFA/cerf/pull/92
- Reporting incorrect operation costs. There will be no effect to the siting result, but will influence operating cost reporting in the output. https://github.com/IMMM-SFA/cerf/pull/91


Version 2.1.1
_____________

- Bug fixes described in https://github.com/IMMM-SFA/cerf/pull/86


Version 2.0.9
_____________

- Update data link with new version for JOSS publication
- Release that accompanies:  https://joss.theoj.org/papers/10.21105/joss.03601


Version 2.0.8
_____________

- Preparation for JOSS publication release


Version 2.0.7
_____________

Changes made in `PR #74 <https://github.com/IMMM-SFA/cerf/pull/74>`_

- Provide option to download illustrative data to a directory of the user's choosing
- Fix bug in the units of interconnection cost


Version 2.0.6
_____________

Changes made in `PR #68 <https://github.com/IMMM-SFA/cerf/pull/68>`_

- Added release notes to documentation
- Added template for pull requests


Version 2.0.5
_____________

Changes made in `PR #65 <https://github.com/IMMM-SFA/cerf/pull/65>`_

- Remove data file that was not ignored


Version 2.0.4
_____________

Changes made in `PR #64 <https://github.com/IMMM-SFA/cerf/pull/64>`_

- Generalization of variables to non-US-specific names throught the code and documentation (e.g., change states to regions)
- Added generalization section into docs
- Add in support statement for Ubuntu 18


Version 2.0.3
_____________

Changes made in `PR #55 <https://github.com/IMMM-SFA/cerf/pull/55>`_

- Add `unit_size` to outputs
- Change package data to install data protocol from Zenodo fetch


Version 2.0.2
_____________

Changes made in `PR #49 <https://github.com/IMMM-SFA/cerf/pull/49>`_

- Add ``unit_size`` to outputs
- Change package data to install data protocol from Zenodo fetch


Version 2.0.1
_____________

Skipped release.


Version 2.0.0
_____________

- Add tests for package data, prep for JOSS paper submission


Version 2.0.0-beta.5
____________________

- Update codecov target


Version 2.0.0-beta.4
____________________

- Modify quickstarter to calculate interconnection cost rather than load it from file


Version 2.0.0-beta.3
____________________

- Updated install packages list in setup.py for pip


Version 2.0.0-beta.2
____________________

- Updated email protocol in setup.py


Version 2.0.0-beta.1
____________________

- Added download URL


Version 2.0.0-beta.0
____________________

This release represents a completely reimagined cerf hosting the following improvements and capabilities:

- Full Python implementation
- Complete rebuild of all functionality
- Quick solution competition algorithm
- No longer Windows 7 dependent; runs on all OSs
- New YAML configuration structure
- Massive performance improvements
- Modular reconstruction
- On-the-fly interconnection infrastructure building from source spatial products
- Migration to substations for interconnection
- Flexible naming conventions
- Sample and demonstration package data
- Test suite
- Full sphinx documentation served on github.io
- Locational marginal price module now calculates from 8760 hourly zonal input
- Selectable parallelization strategy for embarrassingly parallel processing of US states
- Much more!


Version 1.0.0
_____________

- Initial release
