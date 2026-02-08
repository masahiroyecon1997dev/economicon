"""
回帰分析の共通ユーティリティ

定数、マッピング、およびデータ準備の共通関数を提供します。
"""

import gc
from typing import Any, List, Tuple

import numpy as np
import polars as pl
import statsmodels.api as sm

from ...exceptions import ApiError
from ...i18n.translation import gettext as _

# 欠損値処理方法のマッピング
MISSING_HANDLING_MAP = {
    "ignore": "none",
    "remove": "drop",
    "error": "raise",
}

# 標準誤差タイプのマッピング（statsmodels用）
# - nonrobust: 通常の標準誤差（調整なし）
# - HC0-3: White (1980) の不均一分散頑健標準誤差
#   * HC0: 基本形
#   * HC1: 小標本補正
#   * HC2: てこ比補正
#   * HC3: ジャックナイフ型補正
# - HAC: Newey-West (1987) の不均一分散・自己相関頑健標準誤差
# - clustered: クラスター頑健標準誤差（群内相関に対応）
STATSMODELS_COV_TYPE_MAP = {
    "nonrobust": None,  # 調整なし（元の結果をそのまま使用）
    "hc0": "HC0",
    "hc1": "HC1",
    "hc2": "HC2",
    "hc3": "HC3",
    "hac": "HAC",
    "clustered": "cluster",
}

# 標準誤差タイプのマッピング（linearmodels用）
# パネルデータ分析（FE/RE）やIV分析で使用
# - unadjusted: 通常の標準誤差
# - robust: White型頑健標準誤差
# - kernel: Newey-West型（HAC）
# - clustered: クラスター頑健標準誤差
LINEARMODELS_COV_TYPE_MAP = {
    "nonrobust": "unadjusted",
    "hc0": "robust",
    "hc1": "robust",
    "hc2": "robust",
    "hc3": "robust",
    "hac": "kernel",
    "clustered": "clustered",
}


def prepare_basic_data(
    df: pl.DataFrame,
    dependent_variable: str,
    explanatory_variables: List[str],
    has_const: bool,
    missing: str,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    基本的な回帰分析用のデータを準備

    Args:
        df: Polars DataFrame
        dependent_variable: 被説明変数名
        explanatory_variables: 説明変数名のリスト
        has_const: 定数項を含むかどうか
        missing: 欠損値処理方法

    Returns:
        (y_data, x_data): 準備されたnumpy配列のタプル
    """
    y_data = df[dependent_variable].to_numpy()
    x_data = df[explanatory_variables].to_numpy()

    if has_const:
        # has_constant='skip'で既存の定数列をチェック（通常は存在しないはず）
        x_data = sm.add_constant(x_data, has_constant="skip")

    return y_data, x_data


def prepare_panel_dataframe(
    df_polars: pl.DataFrame,
    dependent_variable: str,
    explanatory_variables: List[str],
    entity_id_column: str,
    time_column: str,
    missing: str,
) -> Any:
    """
    パネルデータ分析用のDataFrameを準備

    Args:
        df_polars: Polars DataFrame
        dependent_variable: 被説明変数名
        explanatory_variables: 説明変数名のリスト
        entity_id_column: 個体ID列名
        time_column: 時間列名
        missing: 欠損値処理方法

    Returns:
        MultiIndexが設定されたPandas DataFrame
    """
    # 必要な列を選択
    required_cols = (
        [dependent_variable] + explanatory_variables + [entity_id_column]
    )
    if time_column:
        required_cols.append(time_column)

    # Pandas DataFrameに変換（PyArrow拡張配列を使用してメモリ効率向上）
    df = df_polars.select(required_cols).to_pandas(
        use_pyarrow_extension_array=True
    )

    # Polars DataFrameを明示的に削除してメモリを解放
    del df_polars
    gc.collect()

    # 欠損値の処理
    if missing == "drop":
        df = df.dropna()
    elif missing == "raise":
        if df.isnull().any().any():
            raise ApiError(_("Missing values found in data"))

    if len(df) == 0:
        raise ApiError(
            _("No valid observations after removing missing values")
        )

    # MultiIndex の設定
    if time_column:
        df = df.set_index([entity_id_column, time_column])
    else:
        # 時間列がない場合は自動生成
        # 既存列との衝突を避けるためユニークな名前を使用
        temp_time_col = "__panel_time_idx__"
        while temp_time_col in df.columns:
            temp_time_col += "_"
        df[temp_time_col] = df.groupby(entity_id_column).cumcount()
        df = df.set_index([entity_id_column, temp_time_col])

    return df


def prepare_iv_dataframe(
    df_polars: pl.DataFrame,
    dependent_variable: str,
    explanatory_variables: List[str],
    endogenous_variables: List[str],
    instrumental_variables: List[str],
    missing: str,
) -> Any:
    """
    IV分析用のDataFrameを準備

    Args:
        df_polars: Polars DataFrame
        dependent_variable: 被説明変数名
        explanatory_variables: 説明変数名のリスト
        endogenous_variables: 内生変数名のリスト
        instrumental_variables: 操作変数名のリスト
        missing: 欠損値処理方法

    Returns:
        Pandas DataFrame
    """
    # 必要な列を選択
    required_cols = (
        [dependent_variable]
        + explanatory_variables
        + endogenous_variables
        + instrumental_variables
    )

    # Pandas DataFrameに変換（PyArrow拡張配列を使用してメモリ効率向上）
    df = df_polars.select(required_cols).to_pandas(
        use_pyarrow_extension_array=True
    )

    # Polars DataFrameを明示的に削除してメモリを解放
    del df_polars
    gc.collect()

    # 欠損値の処理
    if missing == "drop":
        df = df.dropna()
    elif missing == "raise":
        if df.isnull().any().any():
            raise ApiError(_("Missing values found in data"))

    if len(df) == 0:
        raise ApiError(
            _("No valid observations after removing missing values")
        )

    return df


def prepare_tobit_dataframe(
    df_polars: pl.DataFrame,
    dependent_variable: str,
    explanatory_variables: List[str],
    missing: str,
) -> Any:
    """
    Tobit分析用のDataFrameを準備

    Args:
        df_polars: Polars DataFrame
        dependent_variable: 被説明変数名
        explanatory_variables: 説明変数名のリスト
        missing: 欠損値処理方法

    Returns:
        Pandas DataFrame
    """
    # 必要な列を選択
    required_cols = [dependent_variable] + explanatory_variables

    # Pandas DataFrameに変換
    df = df_polars.select(required_cols).to_pandas()

    # 欠損値の処理
    if missing == "drop":
        df = df.dropna()
    elif missing == "raise":
        if df.isnull().any().any():
            raise ApiError(_("Missing values found in data"))

    if len(df) == 0:
        raise ApiError(
            _("No valid observations after removing missing values")
        )

    return df


def get_param_names_with_const(
    explanatory_variables: List[str], has_const: bool
) -> List[str]:
    """
    定数項を含むパラメータ名のリストを生成

    Args:
        explanatory_variables: 説明変数名のリスト
        has_const: 定数項を含むかどうか

    Returns:
        パラメータ名のリスト
    """
    return (["const"] if has_const else []) + explanatory_variables
