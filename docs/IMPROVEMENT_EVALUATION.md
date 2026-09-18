# CERF Package Evaluation: Recommended Improvements

**Package:** `cerf` v2.4.1 (commit `8fbe0db`)
**Evaluated:** 2026-09-16
**Environment:** Python 3.11.7, numpy 2.1.1, pandas 2.2.2, rasterio 1.3.11, geopandas 1.0.1
**Target release:** 2.5.0 (branch `release/2.5.0`)

---

## 0. Progress Tracker

Work is landing on `release/2.5.0` via one PR per item. Every PR must pass the unit suite and the seeded end-to-end regression check (`python benchmark/run_reference.py --compare`), which compares all sited plants for the 2010 CONUS sample (49 regions, `seed_value=0`, sequential backend) against the reference generated on the unmodified code at `4821f51`. PRs that intentionally change results must say so and regenerate the reference in a separate commit.

**Workflow:** `git checkout release/2.5.0 && git pull` → `git checkout -b feature/<name>` → implement → `pytest` + `run_reference.py --compare` → push → PR into `release/2.5.0`.

| Item | Description | Branch / PR | Status | Result vs. reference | Timing impact |
|------|-------------|-------------|--------|----------------------|---------------|
| — | Evaluation document | `release/2.5.0` `af98651` | ✅ Done | n/a | n/a |
| — | Seeded reference run + baseline CSV (`benchmark/`) | `release/2.5.0` `4821f51` | ✅ Done | baseline: 1838 sites | staging 8.45 s · competition 11.93 s · total 20.37 s |
| 4.1 | Vectorise buffer removal in `Competition.compete()` | [#118](https://github.com/IMMM-SFA/cerf/pull/118) `6013ff0` | ✅ Merged | identical | competition **11.93 → 5.77 s (−52%)**; total 20.37 → 13.82 s |
| 4.2 + 4.3 | LUT zone lookup + single sort in `get_lmp()` | [#119](https://github.com/IMMM-SFA/cerf/pull/119) `01d0545` | ✅ Merged | identical (LMP array bitwise equal) | `get_lmp` **4.71 → 0.26 s (18×)**; staging 8.05 → 3.34 s; total 13.82 → 8.65 s |
| 3.1 | `isin` signature bug in `preprocess_hifld_substations()` | [#120](https://github.com/IMMM-SFA/cerf/pull/120) `03fef02` | ✅ Merged | identical (not on run path) | n/a; +5 tests |
| 3.2 | NOV `ZeroDivisionError` when esc == discount | [#121](https://github.com/IMMM-SFA/cerf/pull/121) `f16fb73` | ✅ Merged | identical | n/a; +6 tests |
| 7.3 (part) | Robust Zenodo download (retries, ZIP magic check, clear errors) + cached package data in CI | [#122](https://github.com/IMMM-SFA/cerf/pull/122) `a2f9b66` | ✅ Merged | identical (not on run path) | CI: data download skipped on cache hit; +13 tests |
| 3.3 | Model mutates caller's config dict | [#123](https://github.com/IMMM-SFA/cerf/pull/123) `d4b59fc` | ✅ Merged | identical | none (8.60–8.71 s); +3 tests |
| 3.4 + 3.5 | Dead `expansion_dict[tech_id] == 0` branch; `config_dict=None` crash / mutable default | [#124](https://github.com/IMMM-SFA/cerf/pull/124) `9b67175` | ✅ Merged | identical | none (8.59 s); +3 tests |
| 3.6 / 3.7 | Named `cerf` logger; idempotent handlers; root logger untouched; working optional log file | [#125](https://github.com/IMMM-SFA/cerf/pull/125) `a986694` | ✅ Merged | identical | none; +8 tests |
| 7.3 (part) | CI package-data cache keyed on data URL only; 8 download attempts | [#126](https://github.com/IMMM-SFA/cerf/pull/126) `3771712` | ✅ Merged | n/a (workflow only) | cold-cache downloads only on data-version change |
| 4.4 | Read region raster once / precompute bounding boxes | [#127](https://github.com/IMMM-SFA/cerf/pull/127) `bc95610` | ✅ Merged | identical | competition **5.40 → 3.65 s (−32%)**; total 8.59 → 6.9 s; Rhode Island 50 → 3 ms |
| 4.6 | Replace masked arrays in competition loop with `+inf` sentinels; buffer exclusion touches only changed cells | [#128](https://github.com/IMMM-SFA/cerf/pull/128) `c8eb8ea` | ✅ Merged | identical | competition **3.65 → 3.21 s (−12%)**; total 6.93 → 6.8 s; +3 tests |
| 4.5 | `uint8` suitability; scalar (broadcast-view) generation / operating cost; boolean region suitability; deferred metric lookups via 2D views | [#129](https://github.com/IMMM-SFA/cerf/pull/129) `fd2c27f` | ✅ Merged | identical | staged memory **7.4 → 4.2 GB**; competition **3.21 → 2.18 s (−32%)**; total 6.80 → 5.53 s; +4 tests (first `ProcessRegion` tests). `float32` costs deferred (would change `$/yr` outputs) |
| 4.9 + 4.10 | Crop regions before dispatch to process backends (`crop_to_region`, `region_tasks`); single `pd.concat` (`aggregate_results`) | [#130](https://github.com/IMMM-SFA/cerf/pull/130) `7578f2c` | ✅ Merged | identical (sequential and `loky`) | `loky, n_jobs=4`: **294 s → 9.2 s**; per-task payload ~4 GB → ≤ 481 MB; +3 tests |
| 5.1 | LMP CF-bin discontinuity (decision required) | — | ⏸ Deferred by maintainer | will change results | — |
| 5.2 | Pixel-size-aware interconnection distance (`Interconnection.pixel_size_km`, `sampling=` in EDT) | [#131](https://github.com/IMMM-SFA/cerf/pull/131) `7c33993` | ✅ Merged | identical (1 km pixels) | none; +6 tests |
| 5.3 | Per-competition `RandomState` (legacy-stream compatible) instead of global seed; seedable `generate_random_lmp_dataframe` | [#132](https://github.com/IMMM-SFA/cerf/pull/132) `b09603e` | ✅ Merged | identical; `threading` backend now also identical (was nondeterministic) | `threading, n_jobs=4`: full CONUS competition **1.0 s**; +3 tests |
| 3.8–3.11 | `np.nan` nodata / redundant `astype` removed; `raster_to_coord_arrays` via rasterio transform (**`rioxarray` dependency dropped**); case-insensitive `get_region_id` with informative `KeyError`; `sited_dtypes()` covers all 29 columns | [#133](https://github.com/IMMM-SFA/cerf/pull/133) `76cc346` | ✅ Merged | identical | none; +3 tests; one fewer dependency |
| 4.7 + 4.8 | `buffer_window` / `buffer_flat_indices` index arrays (exact bounds); bulk shapely → GeoJSON conversion for `rasterize`; no temp-file round trip, outputs written only on request | [#134](https://github.com/IMMM-SFA/cerf/pull/134) `5d5b9ac` | ✅ Merged | identical | IC step **2.71 → 2.16 s**; total 5.5 → 5.2 s; +3 tests |
| 5.4 + 5.5 + 5.6 | Lifetime fields documented/validated (`validate_technology_parameters`); `EmptyRegionResult` instead of `None`; suitability honours raster `nodata`, shape check, non-0/1 warning | [#135](https://github.com/IMMM-SFA/cerf/pull/135) `c148e04` | ✅ Merged | identical | none; +3 tests |
| 6.3–6.8 | Explicit `__all__` / no star imports; `__version__` from package metadata; unused deps (`seaborn`, `pyarrow`, `rtree`, `fiona`, `pyproj`) removed, `environment.yml` synced; dead code removed; `yaml.safe_load`; `__init__` annotations; `sited_record()` | [#136](https://github.com/IMMM-SFA/cerf/pull/136) `6070061` | ✅ Merged | identical | none; +5 tests; pyflakes clean |
| 6.1 + 6.2 | `RegionData` dataclass (`from_stage` / `crop`) replaces 21-argument plumbing in `ProcessRegion`, `process_region`, `region_tasks`, `Model.run_single_region`; `auto_run=False` + idempotent `run()` on `ProcessRegion` and `Competition` (kwargs still accepted) | [#137](https://github.com/IMMM-SFA/cerf/pull/137) `0fbaa19` | ✅ Merged | identical (sequential and `loky`) | none; +2 tests |
| 7.x | Tests: remove placeholder test, float comparisons, golden data, slow/integration markers; CI matrix, pinned actions, coverage, lint | — | 🟡 In progress | — | — |
| 8.x | Docs and packaging | — | ⬜ Not started | — | — |

Cumulative full-run timing (2010 CONUS sample, sequential, single process):

| After | Staging | Competition | Total | vs. baseline |
|-------|---------|-------------|-------|--------------|
| baseline `4821f51` | 8.45 s | 11.93 s | 20.37 s | — |
| #118 (4.1) | 8.05 s | 5.77 s | 13.82 s | −32% |
| #119 (4.2 + 4.3) | 3.34 s | 5.31 s | 8.65 s | −58% |
| #120–#126 (bug fixes, logger, CI) | 3.20 s | 5.40 s | 8.59 s | −58% |
| #127 (4.4) | 3.28 s | 3.65 s | 6.93 s | −66% |
| #128 (4.6) | 3.30 s | 3.21 s | 6.80 s | −67% |
| #129 (4.5) | 3.30 s | 2.18 s | 5.53 s | −73% |
| #130 (4.9 + 4.10) | 3.22 s | 2.24 s | 5.47 s | −73% (sequential unchanged; `loky` now usable) |
| #131–#133 (5.2, 5.3, 3.8–3.11) | 3.29 s | 2.22 s | 5.51 s | −73% (no perf change; `threading` deterministic at ~1.0 s) |
| #134 (4.7 + 4.8) | 3.10 s | 2.08 s | 5.18 s | −75% |

---

## 1. Summary

CERF is functionally sound: all 9 tests pass and the full 2010 sample configuration (9 technologies, 49 regions, 1,843 sites on a 2999 × 4693 grid) runs end to end. However, profiling and code review surfaced a small number of confirmed bugs, several significant compute hot spots, and structural issues that make the package harder to maintain and to run at scale.

The highest-value items, in priority order:

| # | Area | Item | Impact |
|---|------|------|--------|
| 1 | Performance | Replace per-site Python list comprehension in `Competition.compete()` | ~80% of region compute time |
| 2 | Performance | Replace `np.vectorize(dict.get)` in `LocationalMarginalPricing.get_lmp()` | ~55% of staging time |
| 3 | Bug | `Series.isin()` called with wrong signature in `preprocess_hifld_substations()` | Function always raises `TypeError` |
| 4 | Bug | `ZeroDivisionError` in NOV levelization factors when escalation rate equals discount rate | Crash on valid input |
| 5 | Bug | Model mutates the user's config dict / expansion plan in place | Silent wrong results on re-run |
| 6 | Bug | Dead `if self.expansion_dict[tech_id] == 0` branch in `compete()` | Never executes |
| 7 | Memory | 7.4 GB of `float64` staged arrays, all copied to every worker | Blocks realistic parallelism |
| 8 | Correctness | LMP capacity-factor bin has a discontinuity at CF = 0.5 | Questionable pricing for mid-CF techs |

Each item below includes the location, evidence, and a recommended fix. Sections are grouped by category; a suggested implementation order is at the end.

---

## 2. Measured Baseline

Profiles were collected using `cProfile` on the shipped 2010 sample configuration.

### 2.1 Staging (`Model.stage()` → `Stage.__init__`) – 8.5 s total

| Component | Time | Share | Dominant call |
|-----------|------|-------|---------------|
| `calculate_lmp` | 4.84 s | 57% | `np.vectorize(lmp_dict.get)` × 9 techs |
| `calculate_ic` | 2.80 s | 33% | `features.rasterize` + `distance_transform_edt` × 2, plus ~1.7 s in `np.asanyarray` on shapely geometries |
| `build_suitability_array` | 0.48 s | 6% | raster reads + `float64` writes |
| `calculate_nov` | 0.24 s | 3% | `zeros_like` on 1 GB arrays |

### 2.2 Per-region competition (`process_region`)

| Region | Sites | Time | Top hotspot |
|--------|-------|------|-------------|
| Texas | 266 | 3.08 s | `compete.py:255` list comprehension: **2.45 s (80%)** |
| Rhode Island | 5 | 0.05 s | `extract_region_suitability` (re-reads region raster from disk) |

### 2.3 Memory

All staged arrays are `float64`, shape `(9, 2999, 4693)`:

- `nlc_arr`, `suitability_arr`, `lmp_arr`, `ic_arr`, `nov_arr`, `generation_arr`, `operating_cost_arr`: **~1.01 GB each**
- Total held by `Stage`: **~7.4 GB**
- Every one of these is passed as an argument to `process_region` for every region, so with `loky`/`multiprocessing` backends each worker receives a pickled copy.

---

## 3. Confirmed Bugs

### 3.1 `preprocess_hifld_substations()` always raises `TypeError` — ✅ DONE in #120

> **Resolved.** Case-insensitive `type`/`status` filters; voltage binning extracted to `assign_substation_costs()` and shared with `Interconnection.process_substations()`. New `tests/test_interconnect_preprocess.py`.

**Location:** [`cerf/interconnect.py:435`](../cerf/interconnect.py:435)

```python
gdf = gdf.loc[(gdf['type'].isin('SUBSTATION', 'substation')) & ...
```

`Series.isin()` takes a single iterable. Passing two positional strings raises
`TypeError: Series.isin() takes 2 positional arguments but 3 were given` (verified). The function is public (`from .interconnect import *`) and cannot succeed in its current form.

**Fix:** `gdf['type'].isin(('SUBSTATION', 'substation'))`, or better, normalize case once (`gdf['type'].str.upper() == 'SUBSTATION'`) as is done for `status`.

**Also:** there is no test covering this function.

### 3.2 `ZeroDivisionError` in NOV levelization factors — ✅ DONE in #121

**Location:** [`cerf/nov.py:166-182`](../cerf/nov.py:166)

```python
k = (1.0 + self.variable_cost_esc) / (1.0 + self.discount_rate)
return k * (1.0 - pow(k, self.lifetime_yrs)) * self.annuity_factor / (1.0 - k)
```

When any escalation rate equals the discount rate, `k == 1.0` and `1.0 - k == 0.0` → `ZeroDivisionError` (verified with `esc = discount = 0.05`). Mathematically the limit as k→1 of the levelization factor is `lifetime_yrs * annuity_factor`. Zero escalation with a zero discount rate hits the same path; additionally `calc_annuity_factor` divides by `fx - 1.0`, which is zero when `discount_rate == 0`.

**Fix:** Add a guard for `abs(1.0 - k) < eps` returning `lifetime_yrs * annuity_factor`; handle `discount_rate == 0` in the annuity factor (limit is `1 / lifetime_yrs`). The three `calc_levelization_factor_*` methods are copy-paste identical apart from the rate; collapse into one `_levelization_factor(esc_rate)` helper.

### 3.3 Model mutates the caller's configuration dictionary — ✅ DONE in #123

**Location:** [`cerf/read_config.py:43-62`](../cerf/read_config.py:43), [`cerf/compete.py:252`](../cerf/compete.py:252)

`ReadConfig` stores references (not copies) to the sub-dicts of `config_dict`, and `Competition.compete()` decrements `expansion_dict[tech_id]['n_sites']` in place. Verified: after `Model(config_dict=cfg).run_single_region('rhode_island')`, `cfg['expansion_plan']['rhode_island'][9]['n_sites']` went from `4` to `0` in the **user's own dictionary**.

Consequences:
- Calling `run()` twice with the same `config_dict` silently sites zero plants the second time.
- `Model.expansion_dict` is corrupted after `run_single_region`, so calling it for a second region on the same model yields wrong results.
- In `cerf_parallel` with the `sequential`/`threading` backends, all regions share the same dict; correctness currently depends on each region's sub-dict being distinct (it is, per region), but the shared `technology_dict` and `settings_dict` are one accidental `.update()` away from cross-contamination.

**Fix:** `copy.deepcopy` the config in `ReadConfig.__init__`, and have `Competition` track remaining sites in a local dict rather than mutating `expansion_dict`.

### 3.4 Dead code in `Competition.compete()` — ✅ DONE in #124

**Location:** [`cerf/compete.py:275`](../cerf/compete.py:275)

```python
if self.expansion_dict[tech_id] == 0:
```

`expansion_dict[tech_id]` is a dict (`{'tech_name': ..., 'n_sites': ...}`), never `0`. This branch never executes. The intended check (`['n_sites'] == 0`) already appears correctly at line 294, so this block should simply be removed. Note also the body would assign a masked copy of `nlc_mask[0]` (the sentinel layer) into the tech layer rather than masking the tech layer itself – a second latent bug hidden behind the first.

### 3.5 `ReadConfig` crashes when `config_dict=None` is passed with a file — ✅ DONE in #124

**Location:** [`cerf/read_config.py:26-44`](../cerf/read_config.py:26)

The signature advertises `config_dict` as optional, but passing `config_dict=None` alongside `config_file` raises `AttributeError: 'NoneType' object has no attribute 'get'` at `config_dict.get('settings', {})`. The mutable default `config_dict={}` is also a classic Python pitfall (shared across calls).

**Fix:** default to `None`, then `config_dict = config_dict or {}` at the top.

### 3.6 Logging handlers accumulate — ✅ DONE in #125

**Location:** [`cerf/model.py:53`](../cerf/model.py:53), [`cerf/logger.py:46`](../cerf/logger.py:46)

Each `Model()` instantiation calls `console_handler()`, which adds a new `StreamHandler` to the **root** logger and sets the root level to `DEBUG`. Handlers are only removed by `close_logger()`, which is called from `run_single_region` but not from `stage()` or when the model is used directly. Verified: two extra `Model()` instances → 2 root handlers → duplicated log lines. Setting the root logger to `DEBUG` also floods output from every third-party library (rasterio, fiona, matplotlib) in notebook sessions.

**Fix:** Use a named logger (`logging.getLogger('cerf')`), do not touch the root level, check for existing handlers before adding, and prefer a context manager or explicit `close()` for teardown.

### 3.7 Broken / dead code in `Logger` — ✅ DONE in #125

**Location:** [`cerf/logger.py:36-70`](../cerf/logger.py:36)

`initialize_logger()` calls `self.console_handler()` with no `log_level` argument (required) and references `self.write_logfile` / `self.logfile`, which are never defined anywhere. `file_handler()` is also never called. Either implement file logging properly or delete these methods.

### 3.8 `metadata.update({"nodata": -np.nan})` — ✅ DONE in #133

**Location:** [`cerf/interconnect.py:319`](../cerf/interconnect.py:319)

`-np.nan` is just `nan`; harmless but misleading. More importantly the rasters are written with dtype `float64` even for the rasterized `_rval_` cost layer and the allocation layer, and `distance_array` is written as `float64` after being computed as `float64` already – the `.astype` calls are no-ops.

### 3.9 `raster_to_coord_arrays` leaks a file handle — ✅ DONE in #133

> **Resolved.** Coordinates are computed from the rasterio affine transform inside a `with` block (bitwise identical to the `rioxarray` result on the packaged raster). `rioxarray` removed from `pyproject.toml`.

**Location:** [`cerf/utils.py:256`](../cerf/utils.py:256)

`rioxarray.open_rasterio(template_raster)` is never closed. Should use a `with` block or `.close()`. This is also the only use of `rioxarray` in the package; the same coordinates can be computed from `rasterio` transform + `np.meshgrid` in a few lines, allowing the dependency (and its `xarray` transitive dependency) to be dropped.

### 3.10 `get_region_id` inconsistent lookup — ✅ DONE in #133

**Location:** [`cerf/process_region.py:136-137`](../cerf/process_region.py:136)

```python
if self.target_region_name in self.regions_dict:
    return self.regions_dict.get(self.target_region_name.lower())
```

Membership is tested on the raw name but the lookup uses `.lower()`. A mixed-case name that happens to be in the dict fails the lookup and returns `None`; a lower-case-only dict rejects mixed-case at the membership test. Pick one (normalize on input) and raise a `KeyError` with the message rather than logging and raising an empty `KeyError()`.

### 3.11 `sited_dtypes()` is incomplete vs. `empty_sited_dict()` — ✅ DONE in #133

**Location:** [`cerf/utils.py:88-105`](../cerf/utils.py:88)

`empty_sited_dict()` has 29 keys; `sited_dtypes()` covers 15. Columns like `generation_mwh_per_year`, `operating_cost_usd_per_year`, `capacity_factor_fraction`, `lifetime_yrs`, etc. get whatever dtype pandas infers, so an empty initial frame concatenated with real data can yield `object` columns. `ingest_sited_data` passes `dtype=sited_dtypes()` to `read_csv`, so a CSV produced by a previous run round-trips with inconsistent dtypes for the uncovered columns.

---

## 4. Performance Improvements

### 4.1 `Competition.compete()` buffer-removal list comprehension (critical) — ✅ DONE in #118

**Location:** [`cerf/compete.py:255-256`](../cerf/compete.py:255)

> **Resolved.** Implemented as `tech = tech[~np.isin(tech, buffer_indices_list)]`. Seeded reference output identical (1838/1838 sites). Competition phase 11.93 s → 5.77 s.

```python
tech_indices_to_delete = [np.where(tech == i)[0][0] for i in buffer_indices_list if i in tech]
tech = np.delete(tech, tech_indices_to_delete)
```

This is O(B × T) per sited plant where B = number of buffer cells (121 for a 5 km buffer) and T = number of candidate cells for the technology (can be hundreds of thousands in a large state). `i in tech` performs a full linear scan of a NumPy array from Python, then `np.where` scans it again. Measured at **2.45 s of 3.08 s for Texas (80%)**.

**Fix (drop-in, vectorised):**

```python
tech = tech[~np.isin(tech, buffer_indices_list, assume_unique=True)]
```

or, since `cheapest_arr_1d` has already been zeroed for the buffer, simply:

```python
tech = tech[self.cheapest_arr_1d[tech] == tech_index]
```

Expected: region compute drops by roughly an order of magnitude for large states.

### 4.2 `np.vectorize(dict.get)` for LMP zone lookup (critical for staging) — ✅ DONE in #119

> **Resolved.** Implemented as `LocationalMarginalPricing.zone_lookup()`, a dense integer lookup table offset by `zones.min()`. Full-CONUS LMP array bitwise identical to the previous implementation; `get_lmp` 4.71 s → 0.26 s.

**Location:** [`cerf/lmp.py:166`](../cerf/lmp.py:166)

`np.vectorize` is a Python-level loop over all 14 M cells, repeated for each of 9 technologies: **4.6 s of 8.5 s staging (55%)**. Replace with an integer lookup table:

```python
lut = np.full(int(zones_arr.max()) + 1, np.nan)
lut[list(lmp_dict.keys())] = list(lmp_dict.values())
lmp_arr[index] = lut[zones_arr]
```

This is a single fancy-index operation (~50 ms). The `nodata` value (255) is handled by leaving that slot as `nan`.

### 4.3 Redundant per-technology sorting in `get_lmp` — ✅ DONE in #119 (bundled with 4.2)

**Location:** [`cerf/lmp.py:154-156`](../cerf/lmp.py:154)

Inside the technology loop, every zone column is re-sorted descending on each iteration. The sort is idempotent, so it only needs to happen once before the loop. Additionally, the column-by-column assignment loop can be replaced by `np.sort(lmp_df.values, axis=0)[::-1]` on the underlying array.

### 4.4 Region raster re-read from disk per region — ✅ DONE in #127

**Location:** [`cerf/process_region.py:150-153`](../cerf/process_region.py:150)

`extract_region_suitability` opens and reads the full 14 M-cell region raster for every region (49 times). For small states this is the dominant cost (Rhode Island: 30 ms of 50 ms). The array should be read once in `Stage` and passed in, exactly like `zones_arr`. Even better, precompute the bounding box (`ymin, ymax, xmin, xmax`) per region ID once via `scipy.ndimage.find_objects` and pass a small dict.

### 4.5 Excessive `float64` and full-grid copies — ✅ DONE in #129 (except `float32` costs)

> **Resolved.** Suitability is `uint8`; generation and operating cost are per-technology scalars exposed as read-only broadcast views; `ProcessRegion` builds a boolean unsuitable stack and passes 2D metric *views* to `Competition`, which reads them only at sited cells (`metric_at`). Staged memory 7.4 GB → 4.2 GB, seeded reference identical. Converting `lmp`/`ic`/`nov`/`nlc` to `float32` was measured (~6e-8 relative error) and deferred because it would change the reported `$/yr` columns.

**Location:** [`cerf/stage.py`](../cerf/stage.py), [`cerf/process_region.py`](../cerf/process_region.py)

- `suitability_arr` is a 0/1 mask stored as `float64` (1 GB); should be `bool` or `uint8` (127 MB).
- `lmp_arr`, `ic_arr`, `nov_arr`, `generation_arr`, `operating_cost_arr` could be `float32` with no meaningful loss for $/yr magnitudes (halves 5 GB → 2.5 GB). `generation_arr` is a per-technology scalar broadcast to the full grid – it does not need to be an array at all.
- `extract_region_metrics` flattens 5 full technology stacks for the bounding box, then `Competition` receives them as dicts of flat arrays. Only the values at the finally-sited indices are ever read (see `sited_dict[...].append(self.lmp_flat_dict[tech_id][target_ix])`). These lookups could be deferred to the end and done once against the 3D arrays with the winning `(tech, row, col)` indices, eliminating five 3D slices + flattens per region.

### 4.6 Masked arrays in the competition loop — ✅ DONE in #128

> **Resolved.** `Competition` now works on a plain contiguous `float64` stack where unsuitable cells are `+inf` (`ProcessRegion.mask_nlc` builds it directly; masked-array input is still accepted and converted). Buffer exclusion is `nlc_2d[1:, flat_indices] = inf` on only the affected cells, batched per technology, followed by a single `argmin` refresh (`exclude_technology` / `exclude_cells` / `update_cheapest`). Seeded reference identical.

**Location:** [`cerf/compete.py`](../cerf/compete.py)

`np.ma.masked_array` operations (`argmin`, `__getitem__`, `filled`) are considerably slower than plain NumPy and account for the next tier of profile time after 4.1. The whole loop can be expressed with a plain `float` array where unsuitable cells are `+inf`, replacing:

- `np.ma.masked_array(nlc_mask[1:], np.tile(...).reshape(...))` (line 285) — builds a `(n_tech, rows, cols)` mask via `tile`+`reshape` every iteration. With `inf` semantics this becomes `nlc[1:, buffer_rows, buffer_cols] = np.inf` touching only buffer cells.
- `np.argmin(self.nlc_mask, axis=0)` — full-grid recompute each time a technology finishes its batch; with the inf-array approach only the changed cells need recomputing, or the argmin can be maintained incrementally.

### 4.7 `buffer_flat_array` returns Python lists — ✅ DONE in #134

> **Resolved.** `utils.buffer_window()` / `utils.buffer_flat_indices()` compute the clipped neighbourhood with `divmod` + clipping and return slices / a sorted `intp` array; `Competition` uses them directly. `buffer_flat_array` delegates and now returns the array. Bounds are exact.

**Location:** [`cerf/utils.py:132-226`](../cerf/utils.py:132)

Builds `buffer_indices` via repeated `list.extend(range(...))` and is called once per site. Returning a NumPy index array (or a `(row_slice, col_slice)` tuple against the 2D view) would remove the list allocations and pair naturally with 4.1 / 4.6. The function also has an off-by-one in its bounds check (`min_below <= ngrids` should be `< ngrids`; harmless today because slicing past the end is silently truncated, but incorrect as written).

### 4.8 Interconnection: shapely → `rasterize` overhead — ✅ DONE in #134

> **Resolved.** `Interconnection.geometries_to_shapes()` converts Points / LineStrings in bulk via shapely 2 `get_coordinates`; `transmission_to_cost_raster()` rasterizes to an array and writes only the requested outputs (no `tempfile`). IC step 2.71 s → 2.16 s; the remainder is the EDT kernel.

**Location:** [`cerf/interconnect.py:295`](../cerf/interconnect.py:295)

~1.7 s of the 2.7 s IC step is `np.asanyarray` + `__geo_interface__` on 84 k shapely geometries. Passing `infrastructure_gdf.geometry.values` (a GeometryArray) or pre-converting with `shapely.to_geojson`/`__geo_interface__` in bulk avoids the per-feature Python attribute traversal. Also, all four intermediate rasters are written to disk (temp dir) even when no outputs are requested; `rasterize` already returns the array, so the temp-file round trip is unnecessary unless the user asked for the files.

### 4.9 Parallel backend and data transfer — ✅ DONE in #130

> **Resolved.** `process_region.crop_to_region()` slices every staged array to the region's bounding box in the parent (contiguous copies; broadcast-view metrics collapsed to a per-technology vector) and `process.region_tasks()` uses it for `loky`/`multiprocessing`, while in-process backends still share the full arrays by reference. `loky, n_jobs=4` full CONUS run 294 s → 9.2 s with results identical to the seeded reference. Note: `threading` results differ from the reference before and after because of the shared global RNG (→ 5.3).

**Location:** [`cerf/process.py:85-105`](../cerf/process.py:85)

With `method='loky'` or `'multiprocessing'`, joblib pickles all ~7.4 GB of arrays **per task** (49 tasks). This makes the non-sequential backends effectively unusable on typical hardware, which is presumably why `sequential` is the default. Options:

- Use `joblib.Parallel(..., mmap_mode='r')` with arrays dumped once to disk via `joblib.dump`, or explicitly `np.save` + `np.load(mmap_mode='r')`.
- Pre-crop each region's bounding box in the parent process and send only the cropped stack (Texas is ~1/8 of the grid; Rhode Island is <0.1%).
- Combined with 4.5, the payload shrinks by an order of magnitude.

### 4.10 Output aggregation with repeated `pd.concat` — ✅ DONE in #130

> **Resolved.** `process.aggregate_results()` collects the frames and concatenates once with `ignore_index=True`.

**Location:** [`cerf/process.py:118-122`](../cerf/process.py:118)

`df = pd.concat([df, i.run_data.sited_df])` in a loop is quadratic; collect frames into a list and `concat` once. Minor at 49 regions, but trivial to fix.

---

## 5. Correctness and Modelling Concerns

### 5.1 LMP capacity-factor binning discontinuity

**Location:** [`cerf/lmp.py:98-117`](../cerf/lmp.py:98)

Verified behaviour (LMPs sorted descending):

| CF | Hours averaged |
|----|----------------|
| 0.49 | indices 0–4293 (the **top** 49% priciest hours) |
| 0.50 | indices 4380–8760 (the **bottom** 50% cheapest hours) |
| 0.90 | indices 876–8760 (bottom 90%) |

A technology at CF = 0.49 is priced on the most expensive hours; at CF = 0.50 on the cheapest. This is a hard discontinuity and the two branches embody opposite assumptions (peaking vs. baseload dispatch). If this is intentional it needs documentation and a test; if not, one consistent convention should be chosen (e.g., a plant with CF *c* is dispatched during the top *c* fraction of price hours).

### 5.2 Interconnection distance units — ✅ DONE in #131

> **Resolved.** `Interconnection.pixel_size_km(res, crs)` derives the `(row, col)` pixel size in km (converting the CRS linear unit; geographic / missing CRS rejected) and is passed as `sampling=` to `distance_transform_edt`. Bitwise identical on the packaged 1 km rasters.

**Location:** [`cerf/interconnect.py:353`](../cerf/interconnect.py:353)

`distance_transform_edt` returns distance in **pixels** and the result is multiplied directly by `thous$/km`. This is only correct because the shipped raster is exactly 1 km × 1 km (verified: `res = (1000.0, 1000.0)`). A user providing a different-resolution `region_raster_file` gets silently wrong costs. Pass `sampling=src.res` (in km) to `distance_transform_edt`, or multiply by pixel size.

### 5.3 `randomize`/`seed_value` semantics — ✅ DONE in #132

> **Resolved.** Each `Competition` owns `self.rng = np.random.RandomState(None if randomize else seed_value)` and draws tie-breaks from it. `RandomState` reproduces the legacy global stream exactly, so the seeded reference is unchanged, while results are now independent of backend / thread scheduling / region order. `generate_random_lmp_dataframe` gained a `seed` parameter with a local generator.

**Location:** [`cerf/compete.py:114-115`](../cerf/compete.py:114)

`np.random.seed(seed_value)` sets the **global** NumPy RNG state, which affects any other code in the process and is reset per region in a way that depends on execution order. Use a local `np.random.default_rng(seed)` instance; for parallel runs derive per-region seeds (e.g., `seed + region_id`) so results are reproducible regardless of backend or scheduling.

### 5.4 Retirement year uses `operational_life_yrs` but IC/NOV use `lifetime_yrs` — ✅ DONE in #135

> **Resolved.** `ReadConfig.validate_technology_parameters()` documents the semantics (economic vs. physical life), requires a positive `lifetime_yrs`, defaults `operational_life_yrs` to it, and rejects non-positive values.

**Location:** [`cerf/compete.py:186`](../cerf/compete.py:186), [`cerf/nov.py`](../cerf/nov.py), [`cerf/interconnect.py:376`](../cerf/interconnect.py:376)

Two lifetime fields exist and are used in different places. The sample configs appear to set them equal, but the semantics should be documented (economic vs. physical life) and validated on read.

### 5.5 `n_sites <= 0` check silently returns `None` — ✅ DONE in #135

> **Resolved.** `process_region()` returns an `EmptyRegionResult` with the same attribute surface as a `ProcessRegion` result and an empty, correctly typed `sited_df`.

**Location:** [`cerf/process_region.py:350-355`](../cerf/process_region.py:350)

Regions with zero planned sites return `None`, which the aggregator handles, but `run_single_region` returns `None` to the user with only a log warning. Prefer returning an empty result object so downstream code (`process.run_data.sited_df`) doesn't need `None` checks.

### 5.6 Suitability rasters combined with `np.maximum` assumes 0/1 encoding — ✅ DONE in #135

> **Resolved.** `Stage.unsuitable_from_raster()` honours the declared nodata explicitly (incl. nodata 0 and NaN); `build_suitability_array()` checks the grid shape and warns on values other than 0 / 1 / nodata.

**Location:** [`cerf/stage.py:240`](../cerf/stage.py:240)

`np.maximum(tech_arr, self.init_arr)` and the later `np.where(suitability == 0, 0, 1)` mean any non-zero value (including a nodata value such as 255 or -9999) is treated as "unsuitable". A negative nodata value would survive `np.maximum` and be treated as unsuitable – probably correct by accident, but the raster's declared `nodata` should be honoured explicitly.

---

## 6. Code Quality and Maintainability

### 6.1 `ProcessRegion` and `Competition` do all work in `__init__` — ✅ DONE in #137

Both classes run the full algorithm during construction, making them impossible to instantiate for inspection or unit-test partially. Split construction from `run()`.

> **Resolved.** Both classes take `auto_run=True` (default preserves the old behaviour). With `auto_run=False` the object is fully constructed (region slicing, masks, indices) without competing; `run()` executes once and returns `self`, and repeated calls are no-ops.

### 6.2 Argument explosion — ✅ DONE in #137

`process_region()` takes 21 positional/keyword arguments, mirrored in `ProcessRegion.__init__`, `Model.run_single_region`, and `cerf_parallel`. Passing the `Stage` object (or a small dataclass of arrays) would remove ~60 lines of duplicated plumbing and make it impossible to mis-order arguments.

> **Resolved.** `RegionData` (dataclass) bundles the 13 staged arrays; `RegionData.from_stage(stage)` builds it, `.crop(region_id)` replaces the loose `crop_to_region` call in `region_tasks`. `ProcessRegion` / `process_region` take `data=` and expose read-only properties for each array; the legacy per-array keyword arguments are still accepted (and unknown ones raise `TypeError`).

### 6.3 `Competition` sited-record construction — ✅ DONE in #136

Lines 206–234 append 29 fields one at a time per site. A single `dict` per site appended to a list, then `pd.DataFrame(records)`, is shorter, faster, and guarantees column alignment with `empty_sited_dict()`.

### 6.4 `from .module import *` in `__init__.py` — ✅ DONE in #136

**Location:** [`cerf/__init__.py`](../cerf/__init__.py:1)

Star imports without `__all__` export every helper (`os`, `np`, `logging`, private-ish functions) into the top-level namespace and make the public API unclear. Define `__all__` in each module or import names explicitly. Also `__version__` is duplicated between `__init__.py` and `pyproject.toml`; use `importlib.metadata.version('cerf')` or hatch's dynamic version.

### 6.5 Dependency hygiene — ✅ DONE in #133 (`rioxarray`) and #136 (remaining unused deps)

**Location:** [`pyproject.toml:22-39`](../pyproject.toml:22)

- `seaborn`, `pyarrow`, `rtree`, `fiona`, `pyproj` are declared but never imported anywhere in `cerf/`. (`fiona`/`pyproj` are transitive via geopandas; `pyarrow>=17` is a heavy install for zero use.)
- `rioxarray` is used once and can be replaced (see 3.9).
- `requests` is only needed for `install_package_data`; could be an optional extra.
- Dropping these would cut install size substantially and remove several version-conflict surfaces.

### 6.6 Unused imports and helpers — ✅ DONE in #136 (`generate_random_lmp_dataframe` vectorised in #132)

- `cerf/process_region.py:18` imports `cerf.package_data as pkg` – unused.
- `cerf/interconnect.py:13` imports `suppress_callback` – unused (`suppress_callback` itself is a leftover from a removed whitebox dependency).
- `cerf/interconnect.py`: `region_abbrev_to_name_file`, `region_name_to_id_file` are stored but never used.
- `cerf/read_config.py:198-201`: `infrastructure_files` is built, then immediately rebuilt identically at line 220.
- `cerf/utils.py:108` `default_suitabiity_files` is misspelled (suitabiity) and is part of the public surface via star import.
- `cerf/utils.py:322`: `n_cells > max_allowable_cells` check compares a cell count to `uint32` max but `index_arr` is only used locally.
- `cerf/lmp.py:9` `generate_random_lmp_dataframe`: pure-Python loop over 8760 × 57 samples; `np.random.choice(array, size=8760)` does it in one call.

### 6.7 YAML loading — ✅ DONE in #136

`yaml.load(..., Loader=yaml.FullLoader)` is used in six places. `yaml.safe_load` is the recommended API and is sufficient for these plain configuration files.

### 6.8 Type hints and docstrings — ✅ DONE in #130 / #135 / #136

Class-level "type hints" (e.g., `settings_dict: dict` at class scope in `Stage`, `NetOperationalValue`) are annotations on class attributes, not constructor parameters, and don't help IDEs or type checkers. Move them to `__init__` signatures. Several docstrings are stale (e.g., `process_region` documents a `data` parameter that doesn't exist and a 2D-array return that is actually a `ProcessRegion` object; `cerf_parallel` documents a `config_file` parameter it doesn't accept).

---

## 7. Testing and CI

### 7.1 Coverage gaps

Tests exist for `compete`, `interconnect`, `lmp`, `nov`, `read_config`, `utils.buffer_flat_array`. There is **no** test for:

- `process_region` / `ProcessRegion`
- `process.run` / `cerf_parallel` end-to-end (any backend)
- `Stage` (including `initialize_site_data` path and `ingest_sited_data`)
- `preprocess_hifld_substations` / `preprocess_eia_natural_gas_pipelines` (3.1 would have been caught)
- `outputs.plot_siting`
- `Model.run_single_region`
- NOV edge cases (zero discount, esc == discount → 3.2)
- LMP bin boundaries (→ 5.1)

`tests/test_spatial_reader.py` is a placeholder (`assertEqual(2, 2)`) referencing a module that no longer exists and should be removed. `tests/_test_package_data.py` is disabled by its underscore prefix.

### 7.2 Test fragility

- `test_compete.COMP_SITED_DICT` hard-codes a full 29-key dictionary; any column addition breaks it. Compare the resulting DataFrame against a small golden CSV instead.
- `test_nov` uses `assertEqual` on floating-point values (`0.05282818452724236`); use `assertAlmostEqual`/`np.testing.assert_allclose`.
- `test_interconnect`/`test_lmp` require the ~1 GB Zenodo package data and take ~10 s; they should be marked (e.g., `@pytest.mark.slow`/`integration`) so a fast unit suite can run without downloads.

### 7.3 CI configuration

**Location:** [`.github/workflows/build.yml`](../.github/workflows/build.yml)

- Tests only Python 3.9 on Ubuntu, though `pyproject.toml` claims 3.9–3.11 and the package is being developed on 3.11 / numpy 2.x. Add a matrix (3.9, 3.10, 3.11, 3.12) and ideally macOS.
- `actions/checkout@v1` and `actions/setup-python@master` are outdated / unpinned; use `@v4`/`@v5`.
- Downloads the full Zenodo dataset on every push; cache it (`actions/cache` keyed on data version).
- Coverage report is generated but never uploaded/enforced.
- No linting (ruff/flake8) or formatting checks — many of the items in §6.6 would be flagged automatically.

---

## 8. Documentation and Packaging

- `install_supplement.DATA_VERSION_URLS` must be manually extended on every release; a version-range or "latest" fallback (with a warning) would prevent `KeyError` on new patch versions.
- `Dockerfile` and `environment.yml` were not evaluated in depth but should pin against the same dependency set as `pyproject.toml` (they currently can drift).
- `MANIFEST.in` is irrelevant under hatchling and can be removed.
- The `README`/docs describe `n_jobs=-1` as "all but 1" processor; in joblib `-1` means **all** processors (`-2` is all but one).

---

## 9. Suggested Implementation Order

1. **Quick, safe, high-value fixes (one PR):**
   - 4.1 vectorise buffer removal in `compete()`
   - 4.2 + 4.3 LUT lookup and single sort in `get_lmp()`
   - 3.1 `isin` fix
   - 3.4 remove dead branch
   - 3.5 `config_dict=None` handling
   - 4.10 single `concat`
   - Add regression tests for each.

2. **Correctness fixes requiring small design decisions:**
   - 3.2 NOV limit handling (+ helper consolidation)
   - 3.3 deep-copy config / stop mutating expansion plan
   - 3.6 / 3.7 logger cleanup
   - 5.2 pixel-size-aware distance
   - 5.3 local RNG

3. **Memory and parallelism:**
   - 4.5 dtypes (`bool` suitability, `float32` costs, scalar generation)
   - 4.4 read region raster once / precompute bounding boxes
   - 4.9 crop-before-dispatch or memmap for parallel backends
   - 6.2 pass a data object instead of 21 arguments

4. **Algorithmic refactor of `Competition`:**
   - 4.6 replace masked arrays with `inf`-sentinel arrays and incremental updates
   - 4.7 return index arrays from `buffer_flat_array`
   - 6.1 / 6.3 split construction from execution; build records as dicts

5. **Housekeeping:**
   - 5.1 decide and document LMP CF convention
   - 6.4–6.8 imports, dependencies, `safe_load`, docstrings
   - 7.x tests, CI matrix, caching, linting

Items in step 1 alone should reduce a full sequential CONUS run from roughly (8.5 s staging + Σ regions) to a small fraction of that, with no behavioural change to the siting results (the vectorised buffer removal is exactly equivalent to the current list comprehension).
