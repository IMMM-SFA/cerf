"""Shared pytest configuration for the CERF test suite.

Two custom markers are registered (see ``[tool.pytest.ini_options]`` in ``pyproject.toml``):

``package_data``
    The test reads files from the Zenodo package-data supplement (``cerf.install_package_data()``). Tests carrying
    this marker are skipped automatically when the data directory has not been populated, so the fast unit suite
    runs on a fresh checkout without a download. Force them on with ``pytest --require-package-data`` (CI does
    this so a missing download fails loudly instead of silently skipping).

``slow``
    The test takes more than roughly a second (full-CONUS interconnection, LMP). Deselect with ``-m "not slow"``.

"""

import os

import pytest

import cerf.package_data as pkg


# a file that only exists once the Zenodo supplement has been installed
_SENTINEL = 'cerf_conus_states_albers_1km.tif'


def package_data_available():
    """Return True when the CERF package-data supplement is installed."""

    return os.path.isfile(os.path.join(pkg.get_data_directory(), _SENTINEL))


def pytest_addoption(parser):
    parser.addoption('--require-package-data', action='store_true', default=False,
                     help='fail (instead of skip) tests marked `package_data` when the supplement is missing')


def pytest_collection_modifyitems(config, items):
    if package_data_available():
        return

    if config.getoption('--require-package-data'):
        marked = [item.nodeid for item in items if 'package_data' in item.keywords]
        if marked:
            raise pytest.UsageError(f"--require-package-data given but the supplement is not installed in "
                                    f"{pkg.get_data_directory()} ({len(marked)} tests need it). "
                                    f"Run `python -c 'import cerf; cerf.install_package_data()'`.")
        return

    skip = pytest.mark.skip(reason='CERF package data not installed; run cerf.install_package_data()')
    for item in items:
        if 'package_data' in item.keywords:
            item.add_marker(skip)
