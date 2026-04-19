import math

import pandas as pd
import scipy.stats as spstats

from benchmarks.helpers import f


def _round_or_none(value: float | None, digits: int) -> float | None:
    if value is None or math.isnan(value):
        return None
    return round(float(value), digits)


def _corr(a: pd.Series, b: pd.Series, method: str) -> float | None:
    valid = pd.concat([a, b], axis=1).dropna()
    if len(valid) < 2:
        return None
    x = valid.iloc[:, 0].to_numpy(dtype=float)
    y = valid.iloc[:, 1].to_numpy(dtype=float)
    if method == "pearson":
        return float(spstats.pearsonr(x, y).statistic)
    if method == "spearman":
        return float(spstats.spearmanr(x, y).statistic)
    return float(spstats.kendalltau(x, y).statistic)


def _matrix(
    df: pd.DataFrame,
    columns: list[str],
    method: str,
    decimal_places: int,
    missing_handling: str,
    lower_triangle_only: bool,
) -> dict:
    source = df[columns]
    if missing_handling == "listwise":
        source = source.dropna()

    raw_matrix: list[list[float | None]] = []
    rounded_matrix: list[list[float | None]] = []
    null_positions: list[list[int]] = []

    for row_index, row_name in enumerate(columns):
        raw_row: list[float | None] = []
        rounded_row: list[float | None] = []
        for col_index, col_name in enumerate(columns):
            if row_index == col_index:
                value = 1.0
            elif lower_triangle_only and col_index > row_index:
                value = None
            else:
                value = _corr(source[row_name], source[col_name], method)
            raw_row.append(None if value is None else f(value))
            rounded_row.append(_round_or_none(value, decimal_places))
            if rounded_row[-1] is None:
                null_positions.append([row_index, col_index])
        raw_matrix.append(raw_row)
        rounded_matrix.append(rounded_row)

    return {
        "variable_order": columns,
        "raw_matrix": raw_matrix,
        "rounded_matrix": rounded_matrix,
        "null_positions": null_positions,
        "diagonal_value": 1.0,
    }


def bench_correlation_table(
    core_df: pd.DataFrame,
    nulls_df: pd.DataFrame,
    constant_df: pd.DataFrame,
) -> dict:
    core = core_df.copy()
    nulls = nulls_df.copy()
    constant = constant_df.copy()

    cases = [
        {
            "case_id": "corr_ab_pearson_dp3",
            "table_name": "synthetic_statistics_core",
            "column_names": ["A", "B"],
            "method": "pearson",
            "missing_handling": "pairwise",
            "decimal_places": 3,
            "lower_triangle_only": False,
            "expected": _matrix(core, ["A", "B"], "pearson", 3, "pairwise", False),
        },
        {
            "case_id": "corr_ac_spearman_dp3",
            "table_name": "synthetic_statistics_core",
            "column_names": ["A", "C"],
            "method": "spearman",
            "missing_handling": "pairwise",
            "decimal_places": 3,
            "lower_triangle_only": False,
            "expected": _matrix(core, ["A", "C"], "spearman", 3, "pairwise", False),
        },
        {
            "case_id": "corr_ab_kendall_dp3",
            "table_name": "synthetic_statistics_core",
            "column_names": ["A", "B"],
            "method": "kendall",
            "missing_handling": "pairwise",
            "decimal_places": 3,
            "lower_triangle_only": False,
            "expected": _matrix(core, ["A", "B"], "kendall", 3, "pairwise", False),
        },
        {
            "case_id": "corr_ad_pearson_dp1",
            "table_name": "synthetic_statistics_core",
            "column_names": ["A", "D"],
            "method": "pearson",
            "missing_handling": "pairwise",
            "decimal_places": 1,
            "lower_triangle_only": False,
            "expected": _matrix(core, ["A", "D"], "pearson", 1, "pairwise", False),
        },
        {
            "case_id": "corr_ad_pearson_dp2",
            "table_name": "synthetic_statistics_core",
            "column_names": ["A", "D"],
            "method": "pearson",
            "missing_handling": "pairwise",
            "decimal_places": 2,
            "lower_triangle_only": False,
            "expected": _matrix(core, ["A", "D"], "pearson", 2, "pairwise", False),
        },
        {
            "case_id": "corr_ad_pearson_dp3",
            "table_name": "synthetic_statistics_core",
            "column_names": ["A", "D"],
            "method": "pearson",
            "missing_handling": "pairwise",
            "decimal_places": 3,
            "lower_triangle_only": False,
            "expected": _matrix(core, ["A", "D"], "pearson", 3, "pairwise", False),
        },
        {
            "case_id": "corr_xy_pairwise_pearson",
            "table_name": "synthetic_statistics_nulls",
            "column_names": ["X", "Y"],
            "method": "pearson",
            "missing_handling": "pairwise",
            "decimal_places": 3,
            "lower_triangle_only": False,
            "expected": _matrix(nulls, ["X", "Y"], "pearson", 3, "pairwise", False),
        },
        {
            "case_id": "corr_xy_listwise_pearson",
            "table_name": "synthetic_statistics_nulls",
            "column_names": ["X", "Y"],
            "method": "pearson",
            "missing_handling": "listwise",
            "decimal_places": 3,
            "lower_triangle_only": False,
            "expected": _matrix(nulls, ["X", "Y"], "pearson", 3, "listwise", False),
        },
        {
            "case_id": "corr_xy_listwise_spearman",
            "table_name": "synthetic_statistics_nulls",
            "column_names": ["X", "Y"],
            "method": "spearman",
            "missing_handling": "listwise",
            "decimal_places": 3,
            "lower_triangle_only": False,
            "expected": _matrix(nulls, ["X", "Y"], "spearman", 3, "listwise", False),
        },
        {
            "case_id": "corr_xy_listwise_kendall",
            "table_name": "synthetic_statistics_nulls",
            "column_names": ["X", "Y"],
            "method": "kendall",
            "missing_handling": "listwise",
            "decimal_places": 3,
            "lower_triangle_only": False,
            "expected": _matrix(nulls, ["X", "Y"], "kendall", 3, "listwise", False),
        },
        {
            "case_id": "corr_sparse_pairwise",
            "table_name": "synthetic_statistics_nulls",
            "column_names": ["P", "Q"],
            "method": "pearson",
            "missing_handling": "pairwise",
            "decimal_places": 3,
            "lower_triangle_only": False,
            "expected": _matrix(nulls, ["P", "Q"], "pearson", 3, "pairwise", False),
        },
        {
            "case_id": "corr_abcd_symmetry_dp10",
            "table_name": "synthetic_statistics_core",
            "column_names": ["A", "B", "C", "D"],
            "method": "pearson",
            "missing_handling": "pairwise",
            "decimal_places": 10,
            "lower_triangle_only": False,
            "expected": _matrix(
                core, ["A", "B", "C", "D"], "pearson", 10, "pairwise", False
            ),
        },
        {
            "case_id": "corr_abc_lower_triangle_listwise",
            "table_name": "synthetic_statistics_core",
            "column_names": ["A", "B", "C"],
            "method": "pearson",
            "missing_handling": "listwise",
            "decimal_places": 3,
            "lower_triangle_only": True,
            "expected": _matrix(core, ["A", "B", "C"], "pearson", 3, "listwise", True),
        },
        {
            "case_id": "corr_v1_v5_large_matrix",
            "table_name": "synthetic_statistics_core",
            "column_names": ["V1", "V2", "V3", "V4", "V5"],
            "method": "pearson",
            "missing_handling": "pairwise",
            "decimal_places": 3,
            "lower_triangle_only": False,
            "expected": _matrix(
                core, ["V1", "V2", "V3", "V4", "V5"], "pearson", 3, "pairwise", False
            ),
        },
        {
            "case_id": "corr_japanese_names",
            "table_name": "synthetic_statistics_core",
            "column_names": ["変数A", "変数B"],
            "method": "pearson",
            "missing_handling": "pairwise",
            "decimal_places": 3,
            "lower_triangle_only": False,
            "expected": _matrix(
                core, ["変数A", "変数B"], "pearson", 3, "pairwise", False
            ),
        },
        {
            "case_id": "corr_constant_column",
            "table_name": "synthetic_statistics_constant",
            "column_names": ["Const", "Vary"],
            "method": "pearson",
            "missing_handling": "pairwise",
            "decimal_places": 3,
            "lower_triangle_only": False,
            "expected": _matrix(
                constant, ["Const", "Vary"], "pearson", 3, "pairwise", False
            ),
        },
    ]

    return {"cases": cases}
