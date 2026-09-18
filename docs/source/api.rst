=============
API reference
=============

The public API is exposed at the top level of the ``cerf`` package. Most users only need :func:`cerf.run`,
:func:`cerf.install_package_data`, :func:`cerf.load_sample_config` and :func:`cerf.plot_siting`; the remaining
modules are documented for those who want to drive individual stages of the model or extend it.

Top-level functions
-------------------

The functions most users call directly. Everything else exported by ``cerf`` is documented under its module below.

.. autofunction:: cerf.run
   :no-index:

.. autofunction:: cerf.install_package_data
   :no-index:

.. autofunction:: cerf.load_sample_config
   :no-index:

.. autofunction:: cerf.config_file
   :no-index:

.. autofunction:: cerf.plot_siting
   :no-index:

.. autoclass:: cerf.Model
   :no-index:
   :members: stage, run_single_region


Running the model
-----------------

``cerf.process``
^^^^^^^^^^^^^^^^

Entry points that stage a configuration and site every region, optionally in parallel.

.. automodule:: cerf.process
   :members:
   :undoc-members:
   :show-inheritance:

``cerf.model``
^^^^^^^^^^^^^^

.. automodule:: cerf.model
   :members:
   :undoc-members:
   :show-inheritance:

``cerf.read_config``
^^^^^^^^^^^^^^^^^^^^

.. automodule:: cerf.read_config
   :members:
   :undoc-members:
   :show-inheritance:


Staging inputs
--------------

``cerf.stage``
^^^^^^^^^^^^^^

.. automodule:: cerf.stage
   :members:
   :undoc-members:
   :show-inheritance:

``cerf.lmp``
^^^^^^^^^^^^

.. automodule:: cerf.lmp
   :members:
   :undoc-members:
   :show-inheritance:

``cerf.nov``
^^^^^^^^^^^^

.. automodule:: cerf.nov
   :members:
   :undoc-members:
   :show-inheritance:

``cerf.interconnect``
^^^^^^^^^^^^^^^^^^^^^

.. automodule:: cerf.interconnect
   :members:
   :undoc-members:
   :show-inheritance:


Siting
------

``cerf.process_region``
^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: cerf.process_region
   :members:
   :undoc-members:
   :show-inheritance:

``cerf.compete``
^^^^^^^^^^^^^^^^

.. automodule:: cerf.compete
   :members:
   :undoc-members:
   :show-inheritance:


Outputs and utilities
---------------------

``cerf.outputs``
^^^^^^^^^^^^^^^^

.. automodule:: cerf.outputs
   :members:
   :undoc-members:
   :show-inheritance:

``cerf.utils``
^^^^^^^^^^^^^^

.. automodule:: cerf.utils
   :members:
   :undoc-members:
   :show-inheritance:

``cerf.package_data``
^^^^^^^^^^^^^^^^^^^^^

.. automodule:: cerf.package_data
   :members:
   :undoc-members:
   :show-inheritance:

``cerf.install_supplement``
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: cerf.install_supplement
   :members:
   :undoc-members:
   :show-inheritance:

``cerf.logger``
^^^^^^^^^^^^^^^

.. automodule:: cerf.logger
   :members:
   :undoc-members:
   :show-inheritance:
