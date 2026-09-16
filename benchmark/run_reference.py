"""Reproducible CERF reference run for regression checking.

Runs the packaged 2010 sample configuration for all CONUS regions with a fixed
seed and the sequential joblib backend, so the siting outcome is deterministic.

Usage
-----
Create (or overwrite) the reference output on a known-good commit:

    python benchmark/run_reference.py --write

Compare the current code against the stored reference:

    python benchmark/run_reference.py --compare

Both modes report wall-clock timing for staging and the region competition so
performance changes can be tracked alongside correctness.

"""

import argparse
import os
import sys
import time

import numpy as np
import pandas as pd

import cerf
from cerf.process import cerf_parallel


HERE = os.path.dirname(os.path.abspath(__file__))
REFERENCE_DIR = os.path.join(HERE, "reference")
REFERENCE_FILE = os.path.join(REFERENCE_DIR, "cerf_sited_2010_conus_seed0.csv")

RUN_YEAR = 2010
SEED_VALUE = 0

# columns that uniquely identify a sited plant; used to order rows before comparison
SORT_KEYS = ["region_name", "tech_id", "index"]


def build_config():
    """Load the packaged sample config and force deterministic settings."""

    cfg = cerf.load_sample_config(RUN_YEAR)
    cfg["settings"]["output_directory"] = None
    cfg["settings"]["randomize"] = False
    cfg["settings"]["seed_value"] = SEED_VALUE
    cfg["settings"]["verbose"] = False

    return cfg


def run_reference(log_level="info"):
    """Run CERF for all regions deterministically.

    :return:    (DataFrame of sited plants, staging seconds, competition seconds)

    """

    model = cerf.Model(config_dict=build_config(), log_level=log_level)

    t0 = time.perf_counter()
    data = model.stage()
    t_stage = time.perf_counter() - t0

    t0 = time.perf_counter()
    df = cerf_parallel(model=model, data=data, write_output=False, n_jobs=1, method="sequential")
    t_compete = time.perf_counter() - t0

    model.close_logger()

    return df, t_stage, t_compete


def normalize(df):
    """Order rows and columns deterministically so comparisons are independent of region processing order."""

    df = df.sort_values(SORT_KEYS).reset_index(drop=True)

    return df[sorted(df.columns)]


def compare(df, reference_file=REFERENCE_FILE):
    """Compare a result frame against the stored reference. Raises AssertionError on mismatch."""

    ref = pd.read_csv(reference_file)

    result = normalize(df)
    ref = normalize(ref)

    # dtype alignment: CSV round trip may widen ints or change string dtype representation
    for col in result.columns:
        if col in ref.columns:
            try:
                ref[col] = ref[col].astype(result[col].dtype)
            except (TypeError, ValueError):
                pass

    if list(result.columns) != list(ref.columns):
        raise AssertionError(
            f"Column mismatch.\n  result: {list(result.columns)}\n  reference: {list(ref.columns)}"
        )

    if len(result) != len(ref):
        raise AssertionError(f"Row count mismatch: result={len(result)} reference={len(ref)}")

    # exact match for integer / string columns, tight float tolerance for float columns
    float_cols = [c for c in result.columns if np.issubdtype(result[c].dtype, np.floating)]
    other_cols = [c for c in result.columns if c not in float_cols]

    pd.testing.assert_frame_equal(result[other_cols], ref[other_cols], check_exact=True)
    pd.testing.assert_frame_equal(result[float_cols], ref[float_cols], check_exact=False, rtol=1e-12, atol=0)


def summarize(df):
    """Print a compact per-technology summary."""

    print(f"\nTotal sites: {len(df)}")
    print(df.groupby("tech_name")["tech_id"].count().rename("n_sites").to_string())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="run and write the reference CSV")
    mode.add_argument("--compare", action="store_true", help="run and compare against the reference CSV")
    parser.add_argument("--reference", default=REFERENCE_FILE, help="path to the reference CSV")
    parser.add_argument("--log-level", default="info", choices=["info", "debug"])
    args = parser.parse_args(argv)

    df, t_stage, t_compete = run_reference(log_level=args.log_level)

    print(f"\nStaging:      {t_stage:8.2f} s")
    print(f"Competition:  {t_compete:8.2f} s")
    print(f"Total:        {t_stage + t_compete:8.2f} s")
    summarize(df)

    if args.write:
        os.makedirs(os.path.dirname(args.reference), exist_ok=True)
        normalize(df).to_csv(args.reference, index=False)
        print(f"\nReference written:  {args.reference}")
        return 0

    try:
        compare(df, args.reference)
    except AssertionError as e:
        print(f"\nREGRESSION: results differ from reference {args.reference}\n{e}")
        return 1

    print(f"\nOK: results match reference {args.reference}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
