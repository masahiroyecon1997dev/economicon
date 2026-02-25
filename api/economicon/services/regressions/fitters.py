"""
回帰分析のフィッター関数

各回帰モデルのフィッティングロジックを提供する純粋関数群
"""

from dataclasses import dataclass
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


@dataclass
class TobitInput:
    df_pandas: Any
    dependent_variable: str
    explanatory_variables: list[str]
    has_const: bool
    left_censoring_limit: float | None
    right_censoring_limit: float | None


def fit_tobit(data_input: TobitInput) -> Any:
    """
    Tobitモデルのフィッティング (py4etrics を使用)

    Args:
        data_input: TobitInputデータクラス

    Returns:
        py4etrics の Tobit 回帰結果
    """
    # 被説明変数と説明変数を設定
    y = data_input.df_pandas[data_input.dependent_variable].values
    depns = data_input.df_pandas[data_input.explanatory_variables].values

    # 定数項を追加
    if data_input.has_const:
        depns = sm.add_constant(depns)

    cens = np.zeros(len(y))
    if data_input.left_censoring_limit is not None:
        # 実際に打ち切られている行を -1 にする
        cens[y <= data_input.left_censoring_limit] = -1

    if data_input.right_censoring_limit is not None:
        # 実際に打ち切られている行を 1 にする
        cens[y >= data_input.right_censoring_limit] = 1

    # Tobit モデルの作成とフィット
    model = Tobit(
        y,
        depns,
        cens=cens,
        left=data_input.left_censoring_limit,
        right=data_input.right_censoring_limit,
    )  # type: ignore
    result = model.fit()

    return result


def fit_tobit_null(data_input: TobitInput) -> Any:
    """
    LR検定用の帰無モデル（定数項のみ）をフィット

    完全モデルと同じ打ち切り設定を使用する。

    Args:
        data_input: TobitInput データクラス（被説明変数と打ち切り設定を使用）

    Returns:
        py4etrics の Tobit 回帰結果（定数項のみ）
    """
    y = data_input.df_pandas[data_input.dependent_variable].values
    x_null = np.ones((len(y), 1))  # 定数項のみ

    cens = np.zeros(len(y))
    if data_input.left_censoring_limit is not None:
        cens[y <= data_input.left_censoring_limit] = -1
    if data_input.right_censoring_limit is not None:
        cens[y >= data_input.right_censoring_limit] = 1

    model = Tobit(
        y,
        x_null,
        cens=cens,
        left=data_input.left_censoring_limit,
        right=data_input.right_censoring_limit,
    )  # type: ignore
    return model.fit(disp=False)


@dataclass
class IVInput:
    df_pandas: Any
    dependent_variable: str
    explanatory_variables: list[str]
    endogenous_variables: list[str]
    instrumental_variables: list[str]
    standard_error_method: str
    has_const: bool = True


def fit_iv(data_input: IVInput) -> Any:
    """
    IVモデルのフィッティング (linearmodels を使用)

    Args:
        data_input: IVInputデータクラス

    Returns:
        linearmodels の IV2SLS 回帰結果
    """
    # 被説明変数、外生変数、内生変数、操作変数を設定
    dependent = data_input.df_pandas[data_input.dependent_variable]
    exog_raw = (
        data_input.df_pandas[data_input.explanatory_variables]
        if data_input.explanatory_variables
        else None
    )
    if data_input.has_const and exog_raw is not None:
        exog = sm.add_constant(exog_raw)
    else:
        exog = exog_raw
    endog = (
        data_input.df_pandas[data_input.endogenous_variables]
        if data_input.endogenous_variables
        else None
    )
    instruments = data_input.df_pandas[data_input.instrumental_variables]

    # 標準誤差方法のマッピングを使用
    cov_type = LINEARMODELS_COV_TYPE_MAP.get(
        data_input.standard_error_method, "unadjusted"
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
        df_pandas: prepare_panel_dataframe()で準備されたPandas DataFrame
            (MultiIndex設定済み)
        dependent_variable: 被説明変数名
        explanatory_variables: 説明変数名のリスト
        standard_error_method: 標準誤差計算方法

    Returns:
        linearmodels の PanelOLS 回帰結果
    """
    # 被説明変数と説明変数を設定
    y = df_pandas[dependent_variable]
    depns = df_pandas[explanatory_variables]

    # 標準誤差方法のマッピングを使用
    # 未知のキーは unadjusted にフォールバック
    cov_type = LINEARMODELS_COV_TYPE_MAP.get(
        standard_error_method, "unadjusted"
    )

    # PanelOLS モデルの作成とフィット
    model = PanelOLS(y, depns, entity_effects=True)
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
        df_pandas: prepare_panel_dataframe()で準備されたPandas DataFrame
            (MultiIndex設定済み)
        dependent_variable: 被説明変数名
        explanatory_variables: 説明変数名のリスト
        standard_error_method: 標準誤差計算方法

    Returns:
        linearmodels の RandomEffects 回帰結果
    """
    # 被説明変数と説明変数を設定
    y = df_pandas[dependent_variable]
    depns = df_pandas[explanatory_variables]

    # 標準誤差方法のマッピングを使用
    # 未知のキーは unadjusted にフォールバック
    cov_type = LINEARMODELS_COV_TYPE_MAP.get(
        standard_error_method, "unadjusted"
    )

    # RandomEffects モデルの作成とフィット
    model = RandomEffects(y, depns)
    result = model.fit(cov_type=cov_type)

    return result


@dataclass
class RegularizedRegressionInput:
    y_data: np.ndarray
    x_data: np.ndarray
    has_const: bool
    alpha: float
    missing: str
    calculate_se: bool = False
    bootstrap_iterations: int = 1000


@dataclass
class RegularizedResult:
    """
    正則化回帰（Lasso/Ridge）の結果を保持するデータクラス

    - bootstrap_ci_lower / bootstrap_ci_upper:
        calculate_se=True 時のパーセンタイル法 95% CI
        (params_original と同順 — 定数項を含む)
    - bootstrap_se: Ridge のみ。ブートストラップ標準偏差
    - selection_rate: Lasso のみ。変数が非ゼロとなった
        ブートストラップの割合。定数項ご除く n_features 次元
    """

    params_original: np.ndarray  # 元スケールの係数（定数項を含む）
    coef_scaled: np.ndarray  # 標準化後の係数（定数項なし）
    r2: float  # 訓練データ R²
    n_obs: int  # 観測数
    has_const: bool  # 定数項フラグ
    bootstrap_ci_lower: np.ndarray | None = None
    bootstrap_ci_upper: np.ndarray | None = None
    bootstrap_se: np.ndarray | None = None  # Ridge 用
    selection_rate: np.ndarray | None = None  # Lasso 用


def fit_lasso(
    data_input: RegularizedRegressionInput,
) -> RegularizedResult:
    """
    Lasso モデルのフィッティング

    - R²: 訓練データでの model.score()
    - calculate_se=True 時はブートストラップを実行し、
      パーセンタイル法 95% CI と選択率（Selection Rate）を返す。
      SE は Lasso の点質量問題（Knight & Fu, 2000）により None。
    - t 値・ p 値は理論的根拠なしのため常に None。

    Args:
        data_input: RegularizedRegressionInput データクラス

    Returns:
        RegularizedResult
    """
    x_data_sklearn = remove_const_column(
        data_input.x_data, data_input.has_const
    )

    model = make_pipeline(StandardScaler(), Lasso(alpha=data_input.alpha))
    model.fit(x_data_sklearn, data_input.y_data)
    r2 = float(model.score(x_data_sklearn, data_input.y_data))

    scaler = model.named_steps["standardscaler"]
    lasso = model.named_steps["lasso"]

    coef_scaled = lasso.coef_
    intercept_scaled = lasso.intercept_
    coef_original = coef_scaled / scaler.scale_
    intercept_original = intercept_scaled - np.dot(coef_original, scaler.mean_)

    if data_input.has_const:
        params_original = np.hstack(([intercept_original], coef_original))
    else:
        params_original = coef_original

    bootstrap_ci_lower: np.ndarray | None = None
    bootstrap_ci_upper: np.ndarray | None = None
    selection_rate: np.ndarray | None = None

    if data_input.calculate_se:
        n_samples = len(data_input.y_data)
        n_params = len(params_original)
        bootstrap_coefs = np.zeros((data_input.bootstrap_iterations, n_params))

        for i in range(data_input.bootstrap_iterations):
            idx = np.random.choice(n_samples, n_samples, replace=True)
            y_boot = data_input.y_data[idx]
            x_boot = x_data_sklearn[idx]

            boot_model = make_pipeline(
                StandardScaler(), Lasso(alpha=data_input.alpha)
            )
            boot_model.fit(x_boot, y_boot)

            boot_sc = boot_model.named_steps["standardscaler"]
            boot_las = boot_model.named_steps["lasso"]
            boot_coef_sc = boot_las.coef_
            boot_int_sc = boot_las.intercept_
            boot_coef = boot_coef_sc / boot_sc.scale_
            boot_int = boot_int_sc - np.dot(boot_coef, boot_sc.mean_)

            if data_input.has_const:
                bootstrap_coefs[i] = np.hstack(([boot_int], boot_coef))
            else:
                bootstrap_coefs[i] = boot_coef

        _ci_alpha = 0.05
        bootstrap_ci_lower = np.percentile(
            bootstrap_coefs, _ci_alpha / 2 * 100, axis=0
        )
        bootstrap_ci_upper = np.percentile(
            bootstrap_coefs, (1 - _ci_alpha / 2) * 100, axis=0
        )
        # 選択率: 係数が非ゼロになったブートストラップの割合
        # 定数項は除外し n_features 次元で返す
        coef_cols = (
            bootstrap_coefs[:, 1:] if data_input.has_const else bootstrap_coefs
        )
        selection_rate = np.mean(coef_cols != 0, axis=0)

    return RegularizedResult(
        params_original=params_original,
        coef_scaled=coef_scaled,
        r2=r2,
        n_obs=len(data_input.y_data),
        has_const=data_input.has_const,
        bootstrap_ci_lower=bootstrap_ci_lower,
        bootstrap_ci_upper=bootstrap_ci_upper,
        selection_rate=selection_rate,
    )


def fit_ridge(
    data_input: RegularizedRegressionInput,
) -> RegularizedResult:
    """
    Ridge モデルのフィッティング

    - R²: 訓練データでの model.score()
    - calculate_se=True 時はブートストラップを実行し、
      様本分布の標準偏差（bootstrap_se）と
      パーセンタイル法 95% CI を返す。
    - t 値・ p 値は理論的根拠なしのため常に None。

    Args:
        data_input: RegularizedRegressionInput データクラス

    Returns:
        RegularizedResult
    """
    x_data_sklearn = remove_const_column(
        data_input.x_data, data_input.has_const
    )

    model = make_pipeline(StandardScaler(), Ridge(alpha=data_input.alpha))
    model.fit(x_data_sklearn, data_input.y_data)
    r2 = float(model.score(x_data_sklearn, data_input.y_data))

    scaler = model.named_steps["standardscaler"]
    ridge = model.named_steps["ridge"]

    coef_scaled = ridge.coef_
    intercept_scaled = ridge.intercept_
    coef_original = coef_scaled / scaler.scale_
    intercept_original = intercept_scaled - np.dot(coef_original, scaler.mean_)

    if data_input.has_const:
        params_original = np.hstack(([intercept_original], coef_original))
    else:
        params_original = coef_original

    bootstrap_ci_lower: np.ndarray | None = None
    bootstrap_ci_upper: np.ndarray | None = None
    bootstrap_se: np.ndarray | None = None

    if data_input.calculate_se:
        n_samples = len(data_input.y_data)
        n_params = len(params_original)
        bootstrap_coefs = np.zeros((data_input.bootstrap_iterations, n_params))

        for i in range(data_input.bootstrap_iterations):
            idx = np.random.choice(n_samples, n_samples, replace=True)
            y_boot = data_input.y_data[idx]
            x_boot = x_data_sklearn[idx]

            boot_model = make_pipeline(
                StandardScaler(), Ridge(alpha=data_input.alpha)
            )
            boot_model.fit(x_boot, y_boot)

            boot_sc = boot_model.named_steps["standardscaler"]
            boot_rid = boot_model.named_steps["ridge"]
            boot_coef_sc = boot_rid.coef_
            boot_int_sc = boot_rid.intercept_
            boot_coef = boot_coef_sc / boot_sc.scale_
            boot_int = boot_int_sc - np.dot(boot_coef, boot_sc.mean_)

            if data_input.has_const:
                bootstrap_coefs[i] = np.hstack(([boot_int], boot_coef))
            else:
                bootstrap_coefs[i] = boot_coef

        bootstrap_se = np.std(bootstrap_coefs, axis=0)
        _ci_alpha = 0.05
        bootstrap_ci_lower = np.percentile(
            bootstrap_coefs, _ci_alpha / 2 * 100, axis=0
        )
        bootstrap_ci_upper = np.percentile(
            bootstrap_coefs, (1 - _ci_alpha / 2) * 100, axis=0
        )

    return RegularizedResult(
        params_original=params_original,
        coef_scaled=coef_scaled,
        r2=r2,
        n_obs=len(data_input.y_data),
        has_const=data_input.has_const,
        bootstrap_ci_lower=bootstrap_ci_lower,
        bootstrap_ci_upper=bootstrap_ci_upper,
        bootstrap_se=bootstrap_se,
    )
