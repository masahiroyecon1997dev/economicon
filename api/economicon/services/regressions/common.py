"""
回帰分析の共通ユーティリティ

定数、マッピング、およびデータ準備の共通関数を提供します。
"""

import gc
from dataclasses import dataclass
from typing import Any

import numpy as np
import polars as pl
import statsmodels.api as sm

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.utils import ProcessingError


def handle_missing_values(df: Any, missing: str) -> Any:
    """
    欠損値を処理する共通関数

    Args:
        df: Pandas DataFrame
        missing: 欠損値処理方法 ('drop', 'raise', 'none')

    Returns:
        処理後のDataFrame

    Raises:
        ApiError: 欠損値がある場合（missing='raise'時）
                  または有効な観測値がない場合
    """
    if missing == "drop":
        df = df.dropna()
    elif missing == "raise":
        if df.isnull().any().any():
            raise ProcessingError(
                error_code=ErrorCode.MISSING_VALUES_FOUND,
                message=_("Missing values found in data"),
            )

    if len(df) == 0:
        raise ProcessingError(
            error_code=ErrorCode.NO_VALID_OBSERVATIONS,
            message=_("No valid observations after removing missing values"),
        )

    return df


def remove_const_column(x_data: np.ndarray, has_const: bool) -> np.ndarray:
    """
    scikit-learn用に定数項列を除去する共通関数

    scikit-learnはfit_interceptパラメータで定数項を扱うため、
    x_dataに定数項が含まれている場合は除去する必要がある。

    Args:
        x_data: 説明変数のデータ（定数項が含まれる可能性あり）
        has_const: 定数項を含むかどうか

    Returns:
        定数項を除去した説明変数のデータ
    """
    x_data_sklearn = x_data
    if has_const:
        # 最初の列が定数項かチェック（全て1の列）
        if x_data.shape[1] > 0 and np.allclose(x_data[:, 0], 1.0):
            x_data_sklearn = x_data[:, 1:]  # 定数項を除去
    return x_data_sklearn


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
# - robust: White型頑健標準誤差（HC0相当）
# - kernel: Newey-West型（HAC）
# - clustered: クラスター頑健標準誤差
# 注意: linearmodels は HC1/HC2/HC3 を個別にサポートしないため
#       すべて "robust" (HC0 相当) にフォールバックする。
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
    explanatory_variables: list[str],
    has_const: bool,
    missing: str,
) -> tuple[np.ndarray, np.ndarray]:
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


@dataclass
class PanelDataConfig:
    dependent_variable: str
    explanatory_variables: list[str]
    entity_id_column: str
    missing: str
    time_column: str | None = None
    """
        dependent_variable: 被説明変数名
        explanatory_variables: 説明変数名のリスト
        entity_id_column: 個体ID列名
        time_column: 時間列名
        missing: 欠損値処理方法
    """


def prepare_panel_dataframe(
    df_polars: pl.DataFrame,
    config: PanelDataConfig,
) -> Any:
    """
    パネルデータ分析用のDataFrameを準備

    Args:
        df_polars: Polars DataFrame
        config: PanelDataConfig オブジェクト

    Returns:
        MultiIndexが設定されたPandas DataFrame
    """
    # 必要な列を選択
    required_cols = (
        [config.dependent_variable]
        + config.explanatory_variables
        + [config.entity_id_column]
    )
    if config.time_column:
        required_cols.append(config.time_column)

    # Pandas DataFrameに変換（PyArrow拡張配列を使用してメモリ効率向上）
    df = df_polars.select(required_cols).to_pandas(
        use_pyarrow_extension_array=True
    )

    # Polars DataFrameを明示的に削除してメモリを解放
    del df_polars
    gc.collect()

    # 欠損値の処理
    df = handle_missing_values(df, config.missing)

    # MultiIndex の設定
    if config.time_column:
        df = df.set_index([config.entity_id_column, config.time_column])
    else:
        # 時間列がない場合は自動生成
        # 既存列との衝突を避けるためユニークな名前を使用
        temp_time_col = "__panel_time_idx__"
        while temp_time_col in df.columns:
            temp_time_col += "_"
        df[temp_time_col] = df.groupby(config.entity_id_column).cumcount()
        df = df.set_index([config.entity_id_column, temp_time_col])

    return df


@dataclass
class IvDataConfig:
    dependent_variable: str
    explanatory_variables: list[str]
    endogenous_variables: list[str]
    instrumental_variables: list[str]
    missing: str


def prepare_iv_dataframe(
    df_polars: pl.DataFrame,
    config: IvDataConfig,
) -> Any:
    """
    IV分析用のDataFrameを準備

    Args:
        df_polars: Polars DataFrame
        config: IvDataConfig オブジェクト
    Returns:
        Pandas DataFrame
    """
    # 必要な列を選択
    required_cols = (
        [config.dependent_variable]
        + config.explanatory_variables
        + config.endogenous_variables
        + config.instrumental_variables
    )

    # Pandas DataFrameに変換（PyArrow拡張配列を使用してメモリ効率向上）
    df = df_polars.select(required_cols).to_pandas(
        use_pyarrow_extension_array=True
    )

    # Polars DataFrameを明示的に削除してメモリを解放
    del df_polars
    gc.collect()

    # 欠損値の処理
    df = handle_missing_values(df, config.missing)

    return df


def prepare_tobit_dataframe(
    df_polars: pl.DataFrame,
    dependent_variable: str,
    explanatory_variables: list[str],
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
    # 注意: py4etrics.Tobit は内部で NumPy 配列を使用するため、
    #       use_pyarrow_extension_array=True を指定すると
    #       ArrowExtensionArray が渡され "unrecognized data structures"
    #       エラーが発生する。通常の to_pandas() を使用すること。
    df = df_polars.select(required_cols).to_pandas()

    # 欠損値の処理
    df = handle_missing_values(df, missing)

    return df


def extract_statsmodels_params(
    model_result: Any,
    param_names: list[str],
) -> list[dict]:
    """
    statsmodelsの回帰結果からパラメータ情報を抽出

    Args:
        model_result: statsmodels の回帰結果オブジェクト
        param_names: パラメータ名のリスト

    Returns:
        パラメータ情報の辞書リスト
    """
    params_info = []
    for i, name in enumerate(param_names):
        param_dict = {
            "variable": name,
            "coefficient": float(model_result.params[i]),
            "standardError": None
            if np.isnan(model_result.bse[i])
            else float(model_result.bse[i]),
            "pValue": None
            if np.isnan(model_result.pvalues[i])
            else float(model_result.pvalues[i]),
        }

        # t値またはz値
        if hasattr(model_result, "tvalues"):
            param_dict["tValue"] = (
                None
                if np.isnan(model_result.tvalues[i])
                else float(model_result.tvalues[i])
            )

        # 信頼区間
        if hasattr(model_result, "conf_int"):
            conf_int = model_result.conf_int()
            param_dict["confidenceIntervalLower"] = (
                None if np.isnan(conf_int[i, 0]) else float(conf_int[i, 0])
            )
            param_dict["confidenceIntervalUpper"] = (
                None if np.isnan(conf_int[i, 1]) else float(conf_int[i, 1])
            )

        params_info.append(param_dict)

    return params_info


def extract_linearmodels_params(
    model_result: Any,
    param_names: list[str],
) -> list[dict]:
    """
    linearmodelsの回帰結果からパラメータ情報を抽出

    Args:
        model_result: linearmodels の回帰結果オブジェクト
        param_names: パラメータ名のリスト

    Returns:
        パラメータ情報の辞書リスト
    """
    params_info = []
    conf_int = model_result.conf_int()
    for i, name in enumerate(param_names):
        params_info.append(
            {
                "variable": name,
                "coefficient": float(model_result.params.iloc[i]),
                "standardError": float(model_result.std_errors.iloc[i]),
                "pValue": float(model_result.pvalues.iloc[i]),
                "tValue": float(model_result.tstats.iloc[i]),
                "confidenceIntervalLower": float(conf_int.iloc[i, 0]),
                "confidenceIntervalUpper": float(conf_int.iloc[i, 1]),
            }
        )

    return params_info


def get_param_names_with_const(
    explanatory_variables: list[str], has_const: bool
) -> list[str]:
    """
    定数項を含むパラメータ名のリストを生成

    Args:
        explanatory_variables: 説明変数名のリスト
        has_const: 定数項を含むかどうか

    Returns:
        パラメータ名のリスト
    """
    return (["const"] if has_const else []) + explanatory_variables
