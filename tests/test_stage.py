"""Tests for staging capacity-factor raster inputs on synthetic grids."""

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from cerf.stage import Stage


GRID_SHAPE = (2, 2)
GRID_CRS = 'EPSG:5070'
GRID_TRANSFORM = from_origin(0, 2000, 1000, 1000)


def write_raster(path, values, *, crs=GRID_CRS, transform=GRID_TRANSFORM, nodata=None):
    values = np.asarray(values, dtype=np.float64)
    with rasterio.open(path, 'w', driver='GTiff', height=values.shape[0], width=values.shape[1], count=1,
                       dtype=values.dtype, crs=crs, transform=transform, nodata=nodata) as dst:
        dst.write(values, 1)


def build_stage(grid_path, capacity_factor_raster_file, shape=GRID_SHAPE):
    stage = Stage.__new__(Stage)
    stage.cerf_regionid_raster_file = str(grid_path)
    stage.lmp_arr = np.zeros((1, *shape), dtype=np.float64)
    stage.technology_order = [1]
    stage.technology_dict = {
        1: {
            'tech_name': 'test',
            'capacity_factor_fraction': 0.35,
            'capacity_factor_raster_file': capacity_factor_raster_file,
        },
    }
    return stage


def test_capacity_factor_array_uses_raster_and_marks_nodata_unsuitable(tmp_path):
    grid_path = tmp_path / 'grid.tif'
    raster_path = tmp_path / 'capacity_factor.tif'
    write_raster(grid_path, np.zeros(GRID_SHAPE))
    write_raster(raster_path, [[0.2, 0.4], [-9999, np.nan]], nodata=-9999)
    stage = build_stage(grid_path, str(raster_path))

    result = stage.build_capacity_factor_array()

    np.testing.assert_allclose(result[0], [[0.2, 0.4], [0.0, 0.0]])
    np.testing.assert_array_equal(stage.capacity_factor_unsuitable_arr[0], [[False, False], [True, True]])


def test_capacity_factor_array_uses_scalar_when_raster_is_omitted(tmp_path):
    grid_path = tmp_path / 'grid.tif'
    write_raster(grid_path, np.zeros(GRID_SHAPE))
    stage = build_stage(grid_path, None)

    result = stage.build_capacity_factor_array()

    np.testing.assert_array_equal(result[0], np.full(GRID_SHAPE, 0.35))
    assert not stage.capacity_factor_unsuitable_arr.any()


def test_capacity_factor_nodata_cells_are_unsuitable(tmp_path):
    grid_path = tmp_path / 'grid.tif'
    raster_path = tmp_path / 'capacity_factor.tif'
    suitability_path = tmp_path / 'suitability.tif'
    write_raster(grid_path, np.zeros(GRID_SHAPE))
    write_raster(raster_path, [[0.2, -9999], [0.4, 0.6]], nodata=-9999)
    write_raster(suitability_path, np.zeros(GRID_SHAPE))
    stage = build_stage(grid_path, str(raster_path))
    stage.build_capacity_factor_array()
    stage.nlc_arr = np.zeros_like(stage.lmp_arr)
    stage.technology_dict[1]['suitability_raster_file'] = str(suitability_path)
    stage.tech_name_dict = {1: 'test'}
    stage.initialize_site_data = None

    suitability = stage.build_suitability_array()

    np.testing.assert_array_equal(suitability[0], [[False, True], [False, False]])


@pytest.mark.parametrize('raster_kwargs, message', [
    ({'values': np.zeros((1, 2))}, 'shape'),
    ({'transform': from_origin(1, 2000, 1000, 1000)}, 'transform'),
    ({'crs': 'EPSG:4326'}, 'CRS'),
])
def test_capacity_factor_raster_must_align_with_region_grid(tmp_path, raster_kwargs, message):
    grid_path = tmp_path / 'grid.tif'
    raster_path = tmp_path / 'capacity_factor.tif'
    write_raster(grid_path, np.zeros(GRID_SHAPE))
    values = raster_kwargs.pop('values', np.full(GRID_SHAPE, 0.5))
    write_raster(raster_path, values, **raster_kwargs)
    stage = build_stage(grid_path, str(raster_path))

    with pytest.raises(ValueError, match=message):
        stage.build_capacity_factor_array()


@pytest.mark.parametrize('value', [-0.01, 1.01])
def test_capacity_factor_raster_rejects_values_outside_unit_interval(tmp_path, value):
    grid_path = tmp_path / 'grid.tif'
    raster_path = tmp_path / 'capacity_factor.tif'
    write_raster(grid_path, np.zeros(GRID_SHAPE))
    values = np.full(GRID_SHAPE, 0.5)
    values[0, 0] = value
    write_raster(raster_path, values)
    stage = build_stage(grid_path, str(raster_path))

    with pytest.raises(ValueError, match='between 0 and 1'):
        stage.build_capacity_factor_array()
