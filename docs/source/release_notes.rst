Release notes
=============

This is the list of changes to **cerf** between each release. For full details,
see the `commit logs <https://github.com/IMMM-SFA/cerf/commits>`_.

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
