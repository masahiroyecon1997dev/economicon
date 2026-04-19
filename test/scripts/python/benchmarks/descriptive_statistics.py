from typing import cast

import pandas as pd
import polars as pl

from benchmarks.helpers import f


def _column_stats(df: pl.DataFrame, column: str, statistics: list[str]) -> dict:
    series = df[column]
    result: dict[str, object] = {}

    if "mean" in statistics:
        result["mean"] = None if not series.dtype.is_numeric() else f(series.mean())
    if "median" in statistics:
        result["median"] = None if not series.dtype.is_numeric() else f(series.median())
    if "mode" in statistics:
        mode_df = df.select(pl.col(column).mode()).drop_nulls()
        values = mode_df[column].to_list() if column in mode_df.columns else []
        result["mode"] = values
    if "variance" in statistics:
        result["variance"] = (
            None if not series.dtype.is_numeric() else f(series.var(ddof=1))
        )
    if "std_dev" in statistics:
        result["std_dev"] = (
            None if not series.dtype.is_numeric() else f(series.std(ddof=1))
        )
    if "range" in statistics:
        result["range"] = (
            None
            if not series.dtype.is_numeric()
            else f(cast(float, series.max()) - cast(float, series.min()))
        )
    if "iqr" in statistics:
        result["iqr"] = (
            None
            if not series.dtype.is_numeric()
            else f(
                cast(float, series.quantile(0.75)) - cast(float, series.quantile(0.25))
            )
        )
    if "count" in statistics:
        result["count"] = int(series.len() - series.null_count())
    if "null_count" in statistics:
        result["null_count"] = int(series.null_count())
    if "null_ratio" in statistics:
        result["null_ratio"] = f(series.null_count() / series.len())
    if "population_variance" in statistics:
        result["population_variance"] = (
            None if not series.dtype.is_numeric() else f(series.var(ddof=0))
        )

    return result


def bench_descriptive_statistics(
    core_df: pd.DataFrame,
    nulls_df: pd.DataFrame,
) -> dict:
    core = pl.from_pandas(core_df)
    nulls = pl.from_pandas(nulls_df)

    cases = [
        {
            "case_id": "ds_A_basic",
            "table_name": "synthetic_statistics_core",
            "column_names": ["A"],
            "requested_statistics": ["mean", "median", "variance", "std_dev"],
            "expected": {
                "statistics": {
                    "A": _column_stats(
                        core, "A", ["mean", "median", "variance", "std_dev"]
                    )
                }
            },
        },
        {
            "case_id": "ds_A_range_iqr",
            "table_name": "synthetic_statistics_core",
            "column_names": ["A"],
            "requested_statistics": ["range", "iqr"],
            "expected": {
                "statistics": {"A": _column_stats(core, "A", ["range", "iqr"])}
            },
        },
        {
            "case_id": "ds_A_variance_vs_population",
            "table_name": "synthetic_statistics_core",
            "column_names": ["A"],
            "requested_statistics": ["variance", "population_variance"],
            "expected": {
                "statistics": {
                    "A": _column_stats(core, "A", ["variance", "population_variance"])
                }
            },
        },
        {
            "case_id": "ds_A_counts",
            "table_name": "synthetic_statistics_core",
            "column_names": ["A"],
            "requested_statistics": ["count", "null_count", "null_ratio"],
            "expected": {
                "statistics": {
                    "A": _column_stats(core, "A", ["count", "null_count", "null_ratio"])
                }
            },
        },
        {
            "case_id": "ds_X_null_counts",
            "table_name": "synthetic_statistics_nulls",
            "column_names": ["X"],
            "requested_statistics": ["count", "null_count", "null_ratio"],
            "expected": {
                "statistics": {
                    "X": _column_stats(
                        nulls, "X", ["count", "null_count", "null_ratio"]
                    )
                }
            },
        },
        {
            "case_id": "ds_AB_mean_std",
            "table_name": "synthetic_statistics_core",
            "column_names": ["A", "B"],
            "requested_statistics": ["mean", "std_dev"],
            "expected": {
                "statistics": {
                    "A": _column_stats(core, "A", ["mean", "std_dev"]),
                    "B": _column_stats(core, "B", ["mean", "std_dev"]),
                }
            },
        },
        {
            "case_id": "ds_name_mode",
            "table_name": "synthetic_statistics_core",
            "column_names": ["name"],
            "requested_statistics": ["mode"],
            "expected": {"statistics": {"name": _column_stats(core, "name", ["mode"])}},
        },
        {
            "case_id": "ds_name_numeric_none",
            "table_name": "synthetic_statistics_core",
            "column_names": ["name"],
            "requested_statistics": ["mean", "variance"],
            "expected": {
                "statistics": {
                    "name": _column_stats(core, "name", ["mean", "variance"])
                }
            },
        },
    ]

    return {"cases": cases}
