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
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.regression.linear_model import RegressionResultsWrapper

from economicon.services.regressions.common import (
    LINEARMODELS_COV_TYPE_MAP,
    remove_const_column,
)


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


def fit_iv(  # noqa: PLR0913
    df_pandas: Any,
    dependent_variable: str,
    explanatory_variables: list[str],
    endogenous_variables: list[str],
    instrumental_variables: list[str],
    standard_error_method: str,
    has_const: bool = True,
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
        has_const: 定数項を追加するかどうか

    Returns:
        linearmodels の IV2SLS 回帰結果
    """
    # 被説明変数、外生変数、内生変数、操作変数を設定
    dependent = df_pandas[dependent_variable]
    exog_raw = (
        df_pandas[explanatory_variables] if explanatory_variables else None
    )
    if has_const and exog_raw is not None:
        exog = sm.add_constant(exog_raw)
    else:
        exog = exog_raw
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
    calculate_se: bool = False,
    bootstrap_iterations: int = 1000,
) -> tuple[RegressionResultsWrapper, np.ndarray]:
    """
    Lassoモデルのフィッティング（Pipeline使用、両係数を返す）

    make_pipelineで標準化とLassoを統合し、変数のスケールに依存しない正則化を実現。
    元のスケールの係数と標準化後の係数の両方を返すことで、
    実務的解釈（元のスケール）と変数間比較（標準化後）の両方を可能にする。

    Args:
        y_data: 被説明変数のデータ
        x_data: 説明変数のデータ（定数項が含まれる可能性あり）
        has_const: 定数項を含むかどうか
        alpha: 正則化パラメータ
        missing: 欠損値の処理方法

    Returns:
        result: statsmodels互換の回帰結果（元のスケールの係数）
        coef_scaled: 標準化後の係数（変数間の相対的重要度比較用）
    """
    # x_dataに定数項が含まれている場合は除去
    x_data_sklearn = remove_const_column(x_data, has_const)

    # Pipelineで標準化＋Lasso
    model = make_pipeline(StandardScaler(), Lasso(alpha=alpha))
    model.fit(x_data_sklearn, y_data)

    # 各ステップを取得
    scaler = model.named_steps["standardscaler"]
    lasso = model.named_steps["lasso"]

    # 標準化後の係数（変数間比較用）
    coef_scaled = lasso.coef_
    intercept_scaled = lasso.intercept_

    # 元のスケールに戻す
    coef_original = coef_scaled / scaler.scale_
    intercept_original = intercept_scaled - np.dot(coef_original, scaler.mean_)

    # statsmodels 形式で再構築（統計量を取得するため）
    model_ols = sm.OLS(y_data, x_data, missing=missing)
    result = model_ols.fit()

    # ブートストラップによる標準誤差の計算
    se = None
    if calculate_se:
        n_samples = len(y_data)
        n_params = len(coef_original) + (1 if has_const else 0)
        bootstrap_coefs = np.zeros((bootstrap_iterations, n_params))

        for i in range(bootstrap_iterations):
            indices = np.random.choice(n_samples, n_samples, replace=True)
            y_boot = y_data[indices]
            x_boot = x_data_sklearn[indices]

            boot_model = make_pipeline(StandardScaler(), Lasso(alpha=alpha))
            boot_model.fit(x_boot, y_boot)

            boot_scaler = boot_model.named_steps["standardscaler"]
            boot_lasso = boot_model.named_steps["lasso"]

            boot_coef_scaled = boot_lasso.coef_
            boot_intercept_scaled = boot_lasso.intercept_
            boot_coef_original = boot_coef_scaled / boot_scaler.scale_
            boot_intercept_original = boot_intercept_scaled - np.dot(
                boot_coef_original, boot_scaler.mean_
            )

            if has_const:
                bootstrap_coefs[i] = np.hstack(
                    ([boot_intercept_original], boot_coef_original)
                )
            else:
                bootstrap_coefs[i] = boot_coef_original

        se = np.std(bootstrap_coefs, axis=0)

    # Lasso の係数で上書き（元のスケール）
    if has_const:
        params_original = np.hstack(([intercept_original], coef_original))
    else:
        params_original = coef_original

    result._results.params = params_original
    # bse は CachedProperty のためキャッシュをクリアして normalized_cov_params で設定
    n_params = len(params_original)
    cache = getattr(result._results, "_cache", {})
    for key in ("bse", "tvalues", "pvalues"):
        cache.pop(key, None)
    if calculate_se and se is not None:
        scale = result._results.scale
        result._results.normalized_cov_params = np.diag(se**2 / scale)
    else:
        result._results.normalized_cov_params = np.full(
            (n_params, n_params), np.nan
        )

    return result, coef_scaled


def fit_ridge(
    y_data: np.ndarray,
    x_data: np.ndarray,
    has_const: bool,
    alpha: float,
    missing: str,
    calculate_se: bool = False,
    bootstrap_iterations: int = 1000,
) -> tuple[RegressionResultsWrapper, np.ndarray]:
    """
    Ridgeモデルのフィッティング（Pipeline使用、両係数を返す）

    make_pipelineで標準化とRidgeを統合し、変数のスケールに依存しない正則化を実現。
    元のスケールの係数と標準化後の係数の両方を返すことで、
    実務的解釈（元のスケール）と変数間比較（標準化後）の両方を可能にする。

    Args:
        y_data: 被説明変数のデータ
        x_data: 説明変数のデータ（定数項が含まれる可能性あり）
        has_const: 定数項を含むかどうか
        alpha: 正則化パラメータ
        missing: 欠損値の処理方法

    Returns:
        result: statsmodels互換の回帰結果（元のスケールの係数）
        coef_scaled: 標準化後の係数（変数間の相対的重要度比較用）
    """
    # x_dataに定数項が含まれている場合は除去
    x_data_sklearn = remove_const_column(x_data, has_const)

    # Pipelineで標準化＋Ridge
    model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
    model.fit(x_data_sklearn, y_data)

    # 各ステップを取得
    scaler = model.named_steps["standardscaler"]
    ridge = model.named_steps["ridge"]

    # 標準化後の係数（変数間比較用）
    coef_scaled = ridge.coef_
    intercept_scaled = ridge.intercept_

    # 元のスケールに戻す
    coef_original = coef_scaled / scaler.scale_
    intercept_original = intercept_scaled - np.dot(coef_original, scaler.mean_)

    # statsmodels 形式で再構築（統計量を取得するため）
    model_ols = sm.OLS(y_data, x_data, missing=missing)
    result = model_ols.fit()

    # ブートストラップによる標準誤差の計算
    se = None
    if calculate_se:
        n_samples = len(y_data)
        n_params = len(coef_original) + (1 if has_const else 0)
        bootstrap_coefs = np.zeros((bootstrap_iterations, n_params))

        for i in range(bootstrap_iterations):
            indices = np.random.choice(n_samples, n_samples, replace=True)
            y_boot = y_data[indices]
            x_boot = x_data_sklearn[indices]

            boot_model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
            boot_model.fit(x_boot, y_boot)

            boot_scaler = boot_model.named_steps["standardscaler"]
            boot_ridge = boot_model.named_steps["ridge"]

            boot_coef_scaled = boot_ridge.coef_
            boot_intercept_scaled = boot_ridge.intercept_
            boot_coef_original = boot_coef_scaled / boot_scaler.scale_
            boot_intercept_original = boot_intercept_scaled - np.dot(
                boot_coef_original, boot_scaler.mean_
            )

            if has_const:
                bootstrap_coefs[i] = np.hstack(
                    ([boot_intercept_original], boot_coef_original)
                )
            else:
                bootstrap_coefs[i] = boot_coef_original

        se = np.std(bootstrap_coefs, axis=0)

    # Ridge の係数で上書き（元のスケール）
    if has_const:
        params_original = np.hstack(([intercept_original], coef_original))
    else:
        params_original = coef_original

    result._results.params = params_original
    # bse は CachedProperty のためキャッシュをクリアして normalized_cov_params で設定
    n_params = len(params_original)
    cache = getattr(result._results, "_cache", {})
    for key in ("bse", "tvalues", "pvalues"):
        cache.pop(key, None)
    if calculate_se and se is not None:
        scale = result._results.scale
        result._results.normalized_cov_params = np.diag(se**2 / scale)
    else:
        result._results.normalized_cov_params = np.full(
            (n_params, n_params), np.nan
        )

    return result, coef_scaled
