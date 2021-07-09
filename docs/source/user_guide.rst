===============
User guide
===============



Setting up a **cerf** run
-------------------------

The **cerf** package utilizes a YAML configuration file customized by the user with project level and technology-specific settings, an electricity technology capacity expansion plan, and utility zone data for each year intended to model. **cerf** comes equipped with prebuilt configuration files for years 2010 through 2050 to provide an illustrative example. Each example configuration file can be viewed using the following:

.. code-block:: python

  import cerf

  sample_config = cerf.load_sample_config(yr=2010)

The following are the required key, values if your wish to construct your own configuration files:

``settings``
^^^^^^^^^^^^

These are required values for project-level settings.

.. table::

    +-------------------+-----------------------------------+------+------+
    | Name              | Description                       | Unit | Type |
    +===================+===================================+======+======+
    | run_year          | Target year to run in YYYY format | year | int  |
    +-------------------+-----------------------------------+------+------+
    | randomize         | | Randomize selection of a site   | NA   | str  |
    |                   |   for a technology  when NLC      |      |      |
    |                   | | values are equal. The first     |      |      |
    |                   |   pass is for a technology for    |      |      |
    |                   | | a technology                    |      |      |
    +-------------------+-----------------------------------+------+------+
    | seed_value        | | If `randomize` is False, set a  | NA   | bool |
    |                   |   seed value for reproducibility; |      |      |
    |                   | | the default is 0                |      |      |
    +-------------------+-----------------------------------+------+------+

.. list-table::
  :header-rows: 1

  * - Name
    - Description
    - Unit
    - Type
  * - run_year
    - Target year to run in YYYY format
    - year
    - int
  * - output_directory
    - Directory to write the output data to
    - NA
    - str
  * - randomize
    - Randomize selection of a site for a technology
      when NLC values are equal. The first pass is always
      random but setting `randomize` to False and passing
      a seed value will ensure that runs are reproducible
    - NA
    - bool
  * - seed_value
    - If `randomize` is False, set a seed value for reproducibility; the default is 0
    - NA
    - int

The following is an example implementation in the YAML configuration file:

.. code-block:: yaml

  settings:

      run_year: 2010
      output_directory: <your output directory>
      randomize: False
      seed_value: 0
