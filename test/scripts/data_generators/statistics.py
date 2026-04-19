import numpy as np
import pandas as pd

from data_generators.helpers import N_STAT_CI, N_STAT_TEST, N_STAT_TEST_SMALL


# statistics 系テストで再利用しやすいように、厳密値が読み取りやすい小規模列をまとめる。
def generate_statistics_core_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "A": [1.0, 2.0, 3.0, 4.0, 5.0],
            "B": [10.0, 20.0, 30.0, 40.0, 50.0],
            "C": [5.234, 8.321, 2.976, 4.567, 9.629],
            "D": [2.0, 3.0, 5.0, 4.0, 5.0],
            "name": ["Alice", "Bob", "Charlie", "Alice", "Bob"],
            "category": ["A", "B", "A", "A", "C"],
            "変数A": [1.0, 2.0, 3.0, 4.0, 5.0],
            "変数B": [2.0, 4.0, 6.0, 8.0, 10.0],
            "V1": [1.0, 2.0, 3.0, 4.0, 5.0],
            "V2": [2.0, 4.0, 6.0, 8.0, 10.0],
            "V3": [5.0, 4.0, 3.0, 2.0, 1.0],
            "V4": [2.0, 3.0, 5.0, 4.0, 5.0],
            "V5": [1.0, 3.0, 2.0, 5.0, 4.0],
        }
    )


def generate_statistics_nulls_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "X": [1.0, np.nan, 3.0, 4.0, 5.0],
            "Y": [2.0, 4.0, np.nan, 8.0, 10.0],
            "P": [1.0, np.nan, np.nan, np.nan, np.nan],
            "Q": [np.nan, 2.0, 3.0, 4.0, np.nan],
        }
    )


def generate_statistics_constant_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Const": [3.0, 3.0, 3.0, 3.0, 3.0],
            "Vary": [1.0, 2.0, 3.0, 4.0, 5.0],
        }
    )


# 現行 statistics テストの乱数列と整合しやすいように RandomState(42) 互換で作る。
def generate_statistics_ci_data(seed: int = 42) -> pd.DataFrame:
    rng = np.random.RandomState(seed)
    normal_data = rng.normal(50.0, 10.0, N_STAT_CI)
    binary_data = rng.binomial(1, 0.3, N_STAT_CI).astype(float)

    return pd.DataFrame(
        {
            "id": np.arange(N_STAT_CI, dtype=float),
            "normal_col": normal_data,
            "binary_col": binary_data,
        }
    )


def generate_statistics_ci_invalid_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "numeric_col": [1.0, 2.0, 3.0, 4.0],
            "text_col": ["a", "b", "c", "d"],
            "empty_col": [np.nan, np.nan, np.nan, np.nan],
        }
    )


# t/z/F/ANOVA で使う群データを long format で保持し、将来 fixture 側で tableName ごとに分割しやすくする。
def generate_statistics_test_groups_data(seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    groups = {
        "StatTestTableA": rng.normal(50.0, 10.0, N_STAT_TEST),
        "StatTestTableB": rng.normal(55.0, 10.0, N_STAT_TEST),
        "StatTestTableC": rng.normal(60.0, 10.0, N_STAT_TEST),
        "StatTestTableSmall": rng.normal(50.0, 10.0, N_STAT_TEST_SMALL),
    }

    records: list[dict[str, float | str]] = []
    for table_name, values in groups.items():
        for row_id, value in enumerate(values):
            records.append(
                {
                    "table_name": table_name,
                    "row_id": float(row_id),
                    "value": float(value),
                }
            )

    return pd.DataFrame(records)
