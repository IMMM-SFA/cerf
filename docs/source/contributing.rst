========================
Contributing to **cerf**
========================

Whether you find a typo in the documentation, find a bug, or want to develop functionality that you think will make
**cerf** more robust, you are welcome to contribute!


Opening issues
--------------

If you find a bug or would like to contribute a new feature, please `open an issue
<https://github.com/IMMM-SFA/cerf/issues>`_ and select the template that fits your need. For substantial changes it is
worth discussing the approach in an issue before writing code.


Contribution workflow
---------------------

The following is the recommended workflow for contributing to **cerf**:

1. `Fork the cerf repository <https://github.com/IMMM-SFA/cerf/fork>`_ and then clone it locally:

   .. code-block:: bash

      git clone https://github.com/<your-user-name>/cerf
      cd cerf

   Install the package in editable (development) mode with the test extras. This gives you the flexibility to make
   changes in the code without having to rebuild the package before running tests:

   .. code-block:: bash

      pip install -e ".[test]"

   The fast unit suite runs without the package data; install the data if you want to run the end-to-end tests too:

   .. code-block:: bash

      python -c "import cerf; cerf.install_package_data()"

2. Create a branch for your changes:

   .. code-block:: bash

      git checkout -b bug/some-bug

      # or

      git checkout -b feature/some-feature

3. Add your changes and ensure all tests pass, then commit:

   .. code-block:: bash

      # lint (configuration in pyproject.toml)
      ruff check cerf tests benchmark

      # fast unit suite; skips tests that need the package data
      pytest -m "not package_data"

      # full suite including end-to-end runs on the sample data
      pytest --require-package-data

   Any change that touches the siting path must leave the seeded reference run unchanged:

   .. code-block:: bash

      python benchmark/run_reference.py --compare

   This runs the 2010 sample for all regions with a fixed seed and compares every sited plant against
   ``benchmark/reference/cerf_sited_2010_conus_seed0.csv``. If your change intentionally alters results, say so in
   the pull request and regenerate the reference in a separate commit with ``--write``.

   .. code-block:: bash

      git add <my-file-name>
      git commit -m '<my short message>'

   Changes to the documentation can be made in the ``docs/source`` directory containing the RST files. To view your
   changes, install the documentation dependencies and build the site:

   .. code-block:: bash

      pip install -e ".[docs]"
      cd docs
      make html

   This generates the documentation in ``docs/build/html``; open ``index.html`` in your browser to view it locally.
   When your changes are merged into the main branch of **cerf**, the documentation is rebuilt and published to GitHub
   Pages automatically.

4. Push your changes to the remote:

   .. code-block:: bash

      git push origin <my-branch-name>

5. Submit a pull request following the repository template:

   - **Purpose**: the reason for your pull request in short
   - **Summary**: a description of the environment you are using (OS, Python version, etc.), logic, any caveats, and
     a summary of changes that were made
   - **Validation**: how you tested the change (test suite, regression check, timings if performance-related)

   Continuous integration will lint the code, run the unit suite on a fresh checkout, and run the full suite plus the
   regression check on every supported Python version.

6. If approved, your pull request will be merged into the main branch by a **cerf** admin and a release will be
   conducted subsequently. **cerf** uses `semantic versioning <https://semver.org/>`_ for releases. Each release
   receives a DOI via a linked Zenodo service automatically.


Coding conventions
------------------

- Line length 120; ``ruff`` (rules E, F, W) must pass.
- Public functions and classes carry docstrings in the existing ``:param:`` / ``:type:`` / ``:return:`` style.
- Prefer NumPy vectorisation over Python loops in anything on the per-region path; the competition loop runs for every
  sited plant.
- New behaviour comes with a unit test; anything that needs the package data is marked ``@pytest.mark.package_data``
  (and ``@pytest.mark.slow`` if it takes more than about a second).
