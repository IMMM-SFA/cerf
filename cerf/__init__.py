"""CERF: Capacity Expansion Regional Feasibility model.

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files

"""

from importlib.metadata import PackageNotFoundError, version

from .install_supplement import install_package_data
from .interconnect import (
    Interconnection,
    assign_substation_costs,
    preprocess_eia_natural_gas_pipelines,
    preprocess_hifld_substations,
)
from .lmp import LocationalMarginalPricing, generate_random_lmp_dataframe
from .model import Model
from .outputs import plot_siting
from .package_data import (
    cerf_boundary_shapefile,
    cerf_crs,
    cerf_regions_raster,
    cerf_regions_shapefile,
    config_file,
    costs_per_kv_substation,
    get_costs_gas_pipeline,
    get_costs_per_kv_substation_file,
    get_data_directory,
    get_default_gas_pipelines,
    get_region_abbrev_to_name,
    get_region_abbrev_to_name_file,
    get_region_name_to_id,
    get_sample_lmp_data,
    get_sample_lmp_file,
    get_substation_file,
    get_suitability_raster,
    list_available_suitability_files,
    load_sample_config,
    sample_lmp_zones_raster_file,
)
from .process import cerf_parallel, generate_model, run
from .process_region import EmptyRegionResult, ProcessRegion, RegionData, process_region
from .utils import (
    array_to_raster,
    buffer_flat_array,
    buffer_flat_indices,
    buffer_window,
    default_suitability_files,
    default_suitabiity_files,
    empty_sited_dict,
    ingest_sited_data,
    kilometers_to_miles,
    raster_to_coord_arrays,
    region_bounding_boxes,
    results_to_geodataframe,
    sited_dtypes,
)

try:
    # single source of truth: the version declared in pyproject.toml of the installed distribution
    __version__ = version("cerf")
except PackageNotFoundError:  # pragma: no cover - running from a source tree that has not been installed
    __version__ = "0.0.0+unknown"

__all__ = [
    "__version__",
    # model entry points
    "Model",
    "run",
    "generate_model",
    "cerf_parallel",
    "process_region",
    "ProcessRegion",
    "RegionData",
    "EmptyRegionResult",
    # components
    "Interconnection",
    "LocationalMarginalPricing",
    "assign_substation_costs",
    "preprocess_hifld_substations",
    "preprocess_eia_natural_gas_pipelines",
    "generate_random_lmp_dataframe",
    "plot_siting",
    # package data
    "install_package_data",
    "config_file",
    "load_sample_config",
    "cerf_regions_raster",
    "cerf_regions_shapefile",
    "cerf_boundary_shapefile",
    "cerf_crs",
    "get_default_gas_pipelines",
    "get_costs_per_kv_substation_file",
    "get_costs_gas_pipeline",
    "costs_per_kv_substation",
    "list_available_suitability_files",
    "sample_lmp_zones_raster_file",
    "get_sample_lmp_file",
    "get_sample_lmp_data",
    "get_suitability_raster",
    "get_region_abbrev_to_name_file",
    "get_region_abbrev_to_name",
    "get_region_name_to_id",
    "get_data_directory",
    "get_substation_file",
    # utilities
    "results_to_geodataframe",
    "kilometers_to_miles",
    "empty_sited_dict",
    "sited_dtypes",
    "default_suitability_files",
    "default_suitabiity_files",
    "buffer_window",
    "buffer_flat_indices",
    "buffer_flat_array",
    "array_to_raster",
    "raster_to_coord_arrays",
    "ingest_sited_data",
    "region_bounding_boxes",
]
