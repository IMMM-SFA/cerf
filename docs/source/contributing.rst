Contributing to **cerf**
========================

Whether you find a typo in the documentation, find a bug, or want to develop functionality that you think will make **cerf** more robust, you are welcome to contribute!


Opening issues
______________

If you find a bug or would like to contribute a new feature, please `open an issue <https://github.com/IMMM-SFA/cerf/issues>`_.


Contribution workflow
_____________________

The following is the recommended workflow for contributing to **cerf**:

1. `Fork the cerf repository <https://github.com/IMMM-SFA/cerf/fork>`_ and then clone it locally:

  .. code-block:: bash

    git clone https://github.com/<your-user-name>/cerf


2. Create a branch for your changes

  .. code-block:: bash

    git checkout -b bug/some-bug

    # or

    git checkout -b feature/some-feature

3. Add your recommended changes and ensure all tests pass, then commit your changes:

    Ensure your tests pass locally before pushing to your remote branch where CI will trigger tests.  To do this, ensure that `pytest` has been installed then navigate to the root of your cloned directory (e.g., <my-path>/cerf) and simply execute `pytest`in the terminal.

  .. code-block:: bash

    git add <my-file-name>

    git commit -m '<my short message>'

4. Push your changes to the remote

  .. code-block:: bash

    git push origin <my-branch-name>

5. Submit a pull request with the following information:

  - **Purpose**:  The reason for your pull request in short
  - **Summary**:  A description of the environment you are using (OS, Python version, etc.), logic, any caveats, and a summary of changes that were made.
