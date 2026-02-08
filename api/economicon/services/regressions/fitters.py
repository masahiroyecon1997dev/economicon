"""
回帰分析のフィッター関数

各回帰モデルのフィッティングロジックを提供する純粋関数群
"""

from typing import Any

import numpy as np
import statsmodels.api as sm
from linearmodels.iv import IV2SLS
from linearmodels.panel import PanelOLS, RandomEffects
from py4etrics.tobit import Tobit
from sklearn.linear_model import Lasso, Ridge
from statsmodels.regression.linear_model import RegressionResultsWrapper

from .common import LINEARMODELS_COV_TYPE_MAP


def fit_ols(
    y_data: np.ndarray,
    x_data: np.ndarray,
    missing: str,
) -> RegressionResultsWrapper:
    """
    OLSモデルのフィッティング

    Args:
        y_data: 被説明変数のデータ
        x_data: 説明変数のデータ
        missing: 欠損値の処理方法 ('none', 'drop', 'raise')

    Returns:
        statsmodels の OLS 回帰結果
    """
    model = sm.OLS(y_data, x_data, missing=missing)
    result = model.fit()
    return result


def fit_logit(
    y_data: np.ndarray,
    x_data: np.ndarray,
    missing: str,
) -> RegressionResultsWrapper:
    """
    Logitモデルのフィッティング

    Args:
        y_data: 被説明変数のデータ
        x_data: 説明変数のデータ
        missing: 欠損値の処理方法 ('none', 'drop', 'raise')

    Returns:
        statsmodels の Logit 回帰結果
    """
    model = sm.Logit(y_data, x_data, missing=missing)
    result = model.fit()
    return result


def fit_probit(
    y_data: np.ndarray,
    x_data: np.ndarray,
    missing: str,
) -> RegressionResultsWrapper:
    """
    Probitモデルのフィッティング

    Args:
        y_data: 被説明変数のデータ
        x_data: 説明変数のデータ
        missing: 欠損値の処理方法 ('none', 'drop', 'raise')

    Returns:
        statsmodels の Probit 回帰結果
    """
    model = sm.Probit(y_data, x_data, missing=missing)
    result = model.fit()
    return result


def fit_tobit(
    df_pandas: Any,
    dependent_variable: str,
    explanatory_variables: list[str],
    has_const: bool,
    left_censoring_limit: float | None,
    right_censoring_limit: float | None,
) -> Any:
    """
    Tobitモデルのフィッティング (py4etrics を使用)

    Args:
        df_pandas: prepare_tobit_dataframe()で準備されたPandas DataFrame
        dependent_variable: 被説明変数名
        explanatory_variables: 説明変数名のリスト
        has_const: 定数項を含むかどうか
        left_censoring_limit: 左側打ち切り値
        right_censoring_limit: 右側打ち切り値

    Returns:
        py4etrics の Tobit 回帰結果
    """
    # 被説明変数と説明変数を設定
    y = df_pandas[dependent_variable].values
    X = df_pandas[explanatory_variables].values

    # 定数項を追加
    if has_const:
        X = sm.add_constant(X)

    cens = np.zeros(len(y))
    if left_censoring_limit is not None:
        # 実際に打ち切られている行を -1 にする
        cens[y <= left_censoring_limit] = -1

    if right_censoring_limit is not None:
        # 実際に打ち切られている行を 1 にする
        cens[y >= right_censoring_limit] = 1

    # Tobit モデルの作成とフィット
    model = Tobit(
        y,
        X,
        cens=cens,
        left=left_censoring_limit,
        right=right_censoring_limit,
    )  # type: ignore
    result = model.fit()

    return result


def fit_iv(
    df_pandas: Any,
    dependent_variable: str,
    explanatory_variables: list[str],
    endogenous_variables: list[str],
    instrumental_variables: list[str],
    standard_error_method: str,
) -> Any:
    """
    IVモデルのフィッティング (linearmodels を使用)

    Args:
        df_pandas: prepare_iv_dataframe()で準備されたPandas DataFrame
        dependent_variable: 被説明変数名
        explanatory_variables: 説明変数名のリスト
        endogenous_variables: 内生変数名のリスト
        instrumental_variables: 操作変数名のリスト
        standard_error_method: 標準誤差計算方法

    Returns:
        linearmodels の IV2SLS 回帰結果
    """
    # 被説明変数、外生変数、内生変数、操作変数を設定
    dependent = df_pandas[dependent_variable]
    exog = df_pandas[explanatory_variables] if explanatory_variables else None
    endog = df_pandas[endogenous_variables] if endogenous_variables else None
    instruments = df_pandas[instrumental_variables]

    # 標準誤差方法のマッピングを使用
    cov_type = LINEARMODELS_COV_TYPE_MAP.get(
        standard_error_method, "unadjusted"
    )

    # IV2SLS モデルの作成とフィット
    model = IV2SLS(dependent, exog, endog, instruments)
    result = model.fit(cov_type=cov_type)

    return result


def fit_fe(
    df_pandas: Any,
    dependent_variable: str,
    explanatory_variables: list[str],
    standard_error_method: str,
) -> Any:
    """
    固定効果モデルのフィッティング (linearmodels を使用)

    Args:
        df_pandas: prepare_panel_dataframe()で準備されたPandas DataFrame (MultiIndex設定済み)
        dependent_variable: 被説明変数名
        explanatory_variables: 説明変数名のリスト
        standard_error_method: 標準誤差計算方法

    Returns:
        linearmodels の PanelOLS 回帰結果
    """
    # 被説明変数と説明変数を設定
    y = df_pandas[dependent_variable]
    X = df_pandas[explanatory_variables]

    # 標準誤差方法のマッピングを使用
    cov_type = LINEARMODELS_COV_TYPE_MAP.get(
        standard_error_method, "clustered"
    )

    # PanelOLS モデルの作成とフィット
    model = PanelOLS(y, X, entity_effects=True)
    result = model.fit(cov_type=cov_type)

    return result


def fit_re(
    df_pandas: Any,
    dependent_variable: str,
    explanatory_variables: list[str],
    standard_error_method: str,
) -> Any:
    """
    変量効果モデルのフィッティング (linearmodels を使用)

    Args:
        df_pandas: prepare_panel_dataframe()で準備されたPandas DataFrame (MultiIndex設定済み)
        dependent_variable: 被説明変数名
        explanatory_variables: 説明変数名のリスト
        standard_error_method: 標準誤差計算方法

    Returns:
        linearmodels の RandomEffects 回帰結果
    """
    # 被説明変数と説明変数を設定
    y = df_pandas[dependent_variable]
    X = df_pandas[explanatory_variables]

    # 標準誤差方法のマッピングを使用
    cov_type = LINEARMODELS_COV_TYPE_MAP.get(
        standard_error_method, "clustered"
    )

    # RandomEffects モデルの作成とフィット
    model = RandomEffects(y, X)
    result = model.fit(cov_type=cov_type)

    return result


def fit_lasso(
    y_data: np.ndarray,
    x_data: np.ndarray,
    has_const: bool,
    alpha: float,
    missing: str,
) -> RegressionResultsWrapper:
    """
    Lassoモデルのフィッティング

    Args:
        y_data: 被説明変数のデータ
        x_data: 説明変数のデータ（定数項が含まれる可能性あり）
        has_const: 定数項を含むかどうか
        alpha: 正則化パラメータ
        missing: 欠損値の処理方法

    Returns:
        statsmodels 互換の回帰結果
    """
    # x_dataに定数項が含まれている場合は除去
    # （scikit-learnはfit_interceptで定数項を扱うため）
    x_data_sklearn = x_data
    if has_const:
        # 最初の列が定数項かチェック（全て1の列）
        if x_data.shape[1] > 0 and np.allclose(x_data[:, 0], 1.0):
            x_data_sklearn = x_data[:, 1:]  # 定数項を除去

    # scikit-learn の Lasso を使用
    lasso = Lasso(alpha=alpha, fit_intercept=has_const)
    lasso.fit(x_data_sklearn, y_data)

    # statsmodels 形式で再構築（統計量を取得するため）
    # Lassoの予測値を使ってOLSで統計量を計算
    model = sm.OLS(y_data, x_data, missing=missing)
    result = model.fit()

    # Lasso の係数で上書き
    if has_const:
        result._results.params = np.hstack(
            ([lasso.intercept_], lasso.coef_)  # type: ignore
        )
    else:
        result._results.params = lasso.coef_

    return result


def fit_ridge(
    y_data: np.ndarray,
    x_data: np.ndarray,
    has_const: bool,
    alpha: float,
    missing: str,
) -> RegressionResultsWrapper:
    """
    Ridgeモデルのフィッティング

    Args:
        y_data: 被説明変数のデータ
        x_data: 説明変数のデータ（定数項が含まれる可能性あり）
        has_const: 定数項を含むかどうか
        alpha: 正則化パラメータ
        missing: 欠損値の処理方法

    Returns:
        statsmodels 互換の回帰結果
    """
    # x_dataに定数項が含まれている場合は除去
    # （scikit-learnはfit_interceptで定数項を扱うため）
    x_data_sklearn = x_data
    if has_const:
        # 最初の列が定数項かチェック（全て1の列）
        if x_data.shape[1] > 0 and np.allclose(x_data[:, 0], 1.0):
            x_data_sklearn = x_data[:, 1:]  # 定数項を除去

    # scikit-learn の Ridge を使用
    ridge = Ridge(alpha=alpha, fit_intercept=has_const)
    ridge.fit(x_data_sklearn, y_data)

    # statsmodels 形式で再構築（統計量を取得するため）
    # Ridgeの予測値を使ってOLSで統計量を計算
    model = sm.OLS(y_data, x_data, missing=missing)
    result = model.fit()

    # Ridge の係数で上書き
    if has_const:
        result._results.params = np.hstack(
            ([ridge.intercept_], ridge.coef_)  # type: ignore
        )
    else:
        result._results.params = ridge.coef_

    return result
