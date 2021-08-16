Contributing to **cerf**
========================

Whether you find a typo in the documentation, find a bug, or want to develop functionality that you think will make **cerf** more robust, you are welcome to contribute!


Opening issues
______________

If you find a bug or would like to contribute a new feature, please `open an issue <https://github.com/IMMM-SFA/cerf/issues>`_ and select the template that fits your need.


Contribution workflow
_____________________

The following is the recommended workflow for contributing to **cerf**:

1. `Fork the cerf repository <https://github.com/IMMM-SFA/cerf/fork>`_ and then clone it locally:

  .. code-block:: bash

    git clone https://github.com/<your-user-name>/cerf

  Cloning the repository will give you access to the test suite.  It is important to install the package in development mode before running tests.  This will give you the flexibility to make changes in the code without having to rebuild your package before running tests.  To do this run the following from your terminal in the **cerf** directory containing your ``setup.py`` script:

  .. code-block:: bash

      python setup.py develop


2. Create a branch for your changes

  .. code-block:: bash

    git checkout -b bug/some-bug

    # or

    git checkout -b feature/some-feature

3. Add your recommended changes and ensure all tests pass, then commit your changes:

    Ensure your tests pass locally before pushing to your remote branch where GitHub actions will launch CI services to build the package, run the test suite, and evaluate code coverage.  To do this, ensure that ``pytest`` has been installed then navigate to the root of your cloned directory (e.g., <my-path>/cerf) and simply execute ``pytest`` in the terminal.

  .. code-block:: bash

    git add <my-file-name>

    git commit -m '<my short message>'

  Changes to the documenation can be made in the ``cerf/docs/source`` directory containing the RST files.  To view your changes, ensure you have the development dependencies of **cerf** installed and run the following from the ``cerf/docs/source`` directory:

  .. code-block:: bash

      make html

  This will generate your new documentation in a directory named ``cerf/docs/build/html``.  You can open the ``index.html`` in your browser to view the documentation site locally.  If your changes are merged into the main branch of **cerf**, changes in your documentation will go live as well.

4. Push your changes to the remote

  .. code-block:: bash

    git push origin <my-branch-name>

5. Submit a pull request with the following information:

  - **Purpose**:  The reason for your pull request in short
  - **Summary**:  A description of the environment you are using (OS, Python version, etc.), logic, any caveats, and a summary of changes that were made.

6. If approved, your pull request will be merged into the main branch by a  **cerf** admin and a release will be conducted subsequently.  **cerf** uses `semantic naming <https://semver.org/>`_ for versioned releases.  Each release receives a DOI via a linked Zenodo service automatically.
