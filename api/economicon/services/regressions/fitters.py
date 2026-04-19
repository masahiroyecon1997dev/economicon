"""
回帰分析のフィッター関数

各回帰モデルのフィッティングロジックを提供する純粋関数群
"""

from __future__ import annotations

# NOTE（起動速度最適化）: statsmodels / linearmodels / py4etrics / pandas
# は重量ライブラリのためモジュールレベルの import を排除した。
# 各フィッター関数の先頭で遅延ロード（関数スコープ import）する。
# Python は sys.modules でモジュールをキャッシュするため、
# 2回目以降の呼び出しコストは無視できる。
# Ruff PLC0415 (import-not-at-top-level) は意図的に抑制している。
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from economicon.services.regressions.common import (
    LINEARMODELS_COV_TYPE_MAP,
    remove_const_column,
)

if TYPE_CHECKING:
    # 型チェック時のみ import: 実行時は各関数内の遅延ロードで代替する
    from statsmodels.regression.linear_model import RegressionResultsWrapper


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
    import statsmodels.api as sm  # noqa: PLC0415

    model = sm.OLS(y_data, x_data, missing=missing)
    result = model.fit()
    return result


def fit_logit(
    y_data: np.ndarray,
    x_data: np.ndarray,
    missing: str,
    cov_type: str = "nonrobust",
    cov_kwds: dict | None = None,
) -> RegressionResultsWrapper:
    """
    Logitモデルのフィッティング

    Args:
        y_data: 被説明変数のデータ
        x_data: 説明変数のデータ
        missing: 欠損値の処理方法 ('none', 'drop', 'raise')
        cov_type: 標準誤差の種別。statsmodels の fit() に直接渡す。
        cov_kwds: cov_type 固有の追加引数辞書（groups, maxlags 等）。

    Returns:
        statsmodels の Logit 回帰結果
    """
    import statsmodels.api as sm  # noqa: PLC0415

    model = sm.Logit(y_data, x_data, missing=missing)
    result = model.fit(cov_type=cov_type, cov_kwds=cov_kwds or {}, disp=False)
    return result


def fit_probit(
    y_data: np.ndarray,
    x_data: np.ndarray,
    missing: str,
    cov_type: str = "nonrobust",
    cov_kwds: dict | None = None,
) -> RegressionResultsWrapper:
    """
    Probitモデルのフィッティング

    Args:
        y_data: 被説明変数のデータ
        x_data: 説明変数のデータ
        missing: 欠損値の処理方法 ('none', 'drop', 'raise')
        cov_type: 標準誤差の種別。statsmodels の fit() に直接渡す。
        cov_kwds: cov_type 固有の追加引数辞書（groups, maxlags 等）。

    Returns:
        statsmodels の Probit 回帰結果
    """
    import statsmodels.api as sm  # noqa: PLC0415

    model = sm.Probit(y_data, x_data, missing=missing)
    result = model.fit(cov_type=cov_type, cov_kwds=cov_kwds or {}, disp=False)
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
    import statsmodels.api as sm  # noqa: PLC0415
    from py4etrics.tobit import Tobit  # noqa: PLC0415

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
    from py4etrics.tobit import Tobit  # noqa: PLC0415

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
    iv_method: str = "2sls"
    gmm_weight_matrix: str = "robust"


def fit_iv(data_input: IVInput) -> Any:
    """
    IVモデルのフィッティング (linearmodels を使用)

    Args:
        data_input: IVInputデータクラス

    Returns:
        linearmodels の IV2SLS 回帰結果
    """
    import pandas as pd  # noqa: PLC0415
    import statsmodels.api as sm  # noqa: PLC0415
    from linearmodels.iv import IV2SLS, IVGMM  # noqa: PLC0415

    # 被説明変数、外生変数、内生変数、操作変数を設定
    dependent = data_input.df_pandas[data_input.dependent_variable]
    exog_raw = (
        data_input.df_pandas[data_input.explanatory_variables]
        if data_input.explanatory_variables
        else None
    )
    # Warning#4: has_const=True かつ exog_raw=None
    # (外生変数なし) の場合も定数項を追加する
    if data_input.has_const:
        if exog_raw is not None:
            exog = sm.add_constant(exog_raw)
        else:
            # 外生変数なし + 定数項のみの設計行列
            exog = pd.DataFrame(
                {"const": np.ones(len(data_input.df_pandas))},
                index=data_input.df_pandas.index,
            )
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

    # IV 推定モデルの作成とフィット
    if data_input.iv_method == "gmm":
        # IVGMM: 重み行列タイプはコンストラクタ引数で指定する
        # 過導識別・異分散の場合 (over-identified + heteroskedastic) に有効
        model: IV2SLS | IVGMM = IVGMM(
            dependent,
            exog,
            endog,
            instruments,
            weight_type=data_input.gmm_weight_matrix,
        )
    else:
        # デフォルト: IV2SLS
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
    from linearmodels.panel import PanelOLS  # noqa: PLC0415

    # 被説明変数と説明変数を設定
    y = df_pandas[dependent_variable]
    depns = df_pandas[explanatory_variables]

    # 標準誤差方法のマッピングを使用
    # 未知のキーは unadjusted にフォールバック
    cov_type = LINEARMODELS_COV_TYPE_MAP.get(
        standard_error_method, "unadjusted"
    )

    # PanelOLS モデルの作成とフィット
    # Warning#7: FE (内部推定) では個体効果が切片を吸収するため
    # has_const は意図的に無視。
    # time_demeaning 後に定数項が必要な場合のみ追加すること。
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
    from linearmodels.panel import RandomEffects  # noqa: PLC0415

    # 被説明変数と説明変数を設定
    y = df_pandas[dependent_variable]
    depns = df_pandas[explanatory_variables]

    # 標準誤差方法のマッピングを使用
    # 未知のキーは unadjusted にフォールバック
    cov_type = LINEARMODELS_COV_TYPE_MAP.get(
        standard_error_method, "unadjusted"
    )

    # RandomEffects モデルの作成とフィット
    # Warning#7: RE (ブレイス/GLS 変換) では
    # linearmodels 内部で has_const を考慮済み。
    # (切片項は within + between の合成として内部に追加される)
    model = RandomEffects(y, depns)
    result = model.fit(cov_type=cov_type)

    return result


@dataclass
class PanelIVInput:
    """固定効果IV推定の入力データクラス。"""

    df_pandas: Any
    dependent_variable: str
    explanatory_variables: list[str]
    endogenous_variables: list[str]
    instrumental_variables: list[str]
    entity_id_column: str
    standard_error_method: str


def fit_panel_iv(data_input: PanelIVInput) -> Any:
    """固定効果IV (FE-2SLS) モデルのフィッティング。

    Eco-Note: FWL定理により、entity effectsを absorb した AbsorbingLS は
    Within変換後の2SLS推定と等価。
    AbsorbingLS(absorb=Categorical列) がダミー吸収を内部で行う。
    has_const は個体固定効果が切片を吸収するため不要。

    Args:
        data_input: PanelIVInput データクラス (MultiIndex 設定済み DataFrame)

    Returns:
        linearmodels AbsorbingLS 推定結果
    """
    import pandas as pd  # noqa: PLC0415
    from linearmodels.iv.absorbing import AbsorbingLS  # noqa: PLC0415

    cov_type = LINEARMODELS_COV_TYPE_MAP.get(
        data_input.standard_error_method, "unadjusted"
    )

    # MultiIndex から entity_id を absorb 用 Categorical 列として取り出す
    # Eco-Note: AbsorbingLS は Categorical dtype の列を entity dummies として
    # 吸収するため、pd.Categorical に変換する必要がある。
    entity_idx = data_input.df_pandas.index.get_level_values(
        data_input.entity_id_column
    )
    absorb_df = pd.DataFrame(
        {
            data_input.entity_id_column: pd.Categorical(entity_idx),
        },
        index=data_input.df_pandas.index,
    )

    y = data_input.df_pandas[data_input.dependent_variable]
    exog = (
        data_input.df_pandas[data_input.explanatory_variables]
        if data_input.explanatory_variables
        else None
    )
    endog = (
        data_input.df_pandas[data_input.endogenous_variables]
        if data_input.endogenous_variables
        else None
    )
    instruments = data_input.df_pandas[data_input.instrumental_variables]

    model = AbsorbingLS(
        y,
        exog,
        endog=endog,
        instruments=instruments,
        absorb=absorb_df,
    )
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
    # Eco-Note C: 在様固定。None 指定時は推定のたびに結果が変わる
    random_state: int | None = None
    max_iter: int = 1000
    # Eco-Note D: alpha の規約。glmnet (R) または sklearn のどちらに準拠するか
    # デフォルトは glmnet（計量経済学標準）。
    alpha_convention: Literal["glmnet", "sklearn"] = "glmnet"


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
    - pipeline: sklearn Pipeline（StandardScaler + Lasso/Ridge）
        診断列追加時に predict() 再実行用
    - x_data: 推定時の説明変数（定数項除去済み）
    - y_data: 推定時の被説明変数（残差計算用）
    """

    params_original: np.ndarray  # 元スケールの係数（定数項を含む）
    coef_scaled: np.ndarray  # 標準化後の係数（定数項なし）
    r2: float  # 訓練データ R²
    n_obs: int  # 観測数
    has_const: bool  # 定数項フラグ
    fittedvalues: np.ndarray  # 予測値（診断列追加時に使用）
    x_data: np.ndarray  # 説明変数（定数項除去済み・ブートストラップ用）
    y_data: np.ndarray  # 推定時の被説明変数（残差計算用）
    converged: bool = True  # 収束フラグ（警告表示に使用）
    bootstrap_ci_lower: np.ndarray | None = None
    bootstrap_ci_upper: np.ndarray | None = None
    bootstrap_se: np.ndarray | None = None  # Ridge 用
    selection_rate: np.ndarray | None = None  # Lasso 用


def _build_alpha_arr(
    alpha_sm: float,
    has_const: bool,
    n_features: int,
) -> np.ndarray:
    """
    statsmodels fit_regularized 用の alpha 配列を構築する。

    定数項（切片）は正則化の対象外とする（glmnet / sklearn 準拠）。
    has_const=True の場合、先頭要素を 0.0 にする。

    Args:
        alpha_sm: statsmodels 規約に変換済みの alpha 値
        has_const: 定数項フラグ
        n_features: 説明変数数（定数項を除く）

    Returns:
        shape (n_features,) or (n_features+1,) の alpha 配列
    """
    if has_const:
        return np.array([0.0] + [alpha_sm] * n_features, dtype=np.float64)
    return np.full(n_features, alpha_sm, dtype=np.float64)


def _to_statsmodels_alpha(
    alpha_user: float,
    convention: str,
    n_samples: int,
    l1_wt: float,
) -> float:
    """
    パブリック API の alpha を statsmodels 座標降下法規約に変換する。

    statsmodels elastic_net 目的関数（OLS）:
        1/(2n)||y-Xβ||² + α·[L1_wt·||β||₁ + (1-L1_wt)/2·||β||²]

    glmnet (R) 規約:
        Lasso: 1/(2n)||y-Xβ||² + λ||β||₁  → α_sm = λ  (直接一致)
        Ridge: 1/(2n)||y-Xβ||² + λ||β||²  → α_sm = λ  (直接一致)

    sklearn 規約:
        Lasso: 1/(2n)||y-Xβ||² + α||β||₁ → α_sm = α (同一式)
        Ridge: ||y-Xβ||² + α||β||²        → α_sm = α/n

    Args:
        alpha_user: API から受け取った alpha 値
        convention: "glmnet" または "sklearn"
        n_samples: サンプルサイズ（Ridge sklearn 変換に使用）
        l1_wt: 0.0 = Ridge, 1.0 = Lasso

    Returns:
        statsmodels に渡す alpha 値
    """
    is_lasso = l1_wt >= 1.0
    if convention == "sklearn":
        if is_lasso:
            return float(alpha_user)  # sklearn Lasso = statsmodels Lasso
        else:
            return float(alpha_user) / n_samples  # sklearn Ridge → statsmodels
    elif is_lasso:  # glmnet (default)
        return float(alpha_user)  # glmnet λ = statsmodels α (直接一致)
    else:
        return float(alpha_user)  # glmnet λ = statsmodels α (直接一致)


def _standardize(
    x_no_const: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    説明変数を標準化する（ddof=0、sklearn StandardScaler 相当）。

    ゼロ分散の列はスケールを 1.0 として除算エラーを回避する。

    Returns:
        (x_scaled, x_mean, x_scale)
    """
    x_mean = x_no_const.mean(axis=0)
    x_scale = x_no_const.std(axis=0, ddof=0)
    x_scale = np.where(x_scale == 0.0, 1.0, x_scale)
    return (x_no_const - x_mean) / x_scale, x_mean, x_scale


def _backscale_params(
    coef_scaled: np.ndarray,
    intercept_scaled: float,
    x_mean: np.ndarray,
    x_scale: np.ndarray,
    has_const: bool,
) -> np.ndarray:
    """
    標準化スペースの係数を元スケールに逆変換して params_original を返す。

    変換式:
        β_orig = β_scaled / σ
        β₀_orig = β₀_scaled - β_orig · μ
    """
    coef_original = coef_scaled / x_scale
    intercept_original = intercept_scaled - np.dot(coef_original, x_mean)
    if has_const:
        return np.hstack(([intercept_original], coef_original))
    return coef_original


def fit_lasso(  # noqa: PLR0915
    data_input: RegularizedRegressionInput,
) -> RegularizedResult:
    """
    Lasso モデルのフィッティング（statsmodels 座標降下法 elastic_net 使用）

    Eco-Note D: alpha 変換規約
        glmnet λ（デフォルト）→ statsmodels α = λ（直接一致）
        sklearn  α            → statsmodels α = α（同一式）

    - R²: 手動計算 (1 - SS_res / SS_tot)
    - calculate_se=True 時はブートストラップを実行し、
      パーセンタイル法 95% CI と選択率（Selection Rate）を返す。
      SE は Lasso の点質量問題（Knight & Fu, 2000）により None。
    - t 値・ p 値は理論的根拠なしのため常に None。
    - 収束失敗時は converged=False として警告を後段に伝達する。

    Args:
        data_input: RegularizedRegressionInput データクラス

    Returns:
        RegularizedResult
    """
    import statsmodels.api as sm  # noqa: PLC0415

    x_no_const = remove_const_column(data_input.x_data, data_input.has_const)
    n_samples, n_features = x_no_const.shape

    x_scaled, x_mean, x_scale = _standardize(x_no_const)

    x_sm = (
        sm.add_constant(x_scaled, has_constant="add")
        if data_input.has_const
        else x_scaled
    )

    alpha_sm = _to_statsmodels_alpha(
        data_input.alpha,
        data_input.alpha_convention,
        n_samples,
        l1_wt=1.0,
    )
    alpha_arr = _build_alpha_arr(alpha_sm, data_input.has_const, n_features)

    sm_model = sm.OLS(data_input.y_data, x_sm, missing=data_input.missing)
    result = sm_model.fit_regularized(
        method="elastic_net",
        alpha=alpha_arr,  # type: ignore[arg-type]
        L1_wt=1.0,
        maxiter=data_input.max_iter,
    )
    converged = bool(getattr(result, "converged", True))

    params_sm = np.asarray(result.params, dtype=np.float64)
    if data_input.has_const:
        intercept_scaled = float(params_sm[0])
        coef_scaled = params_sm[1:]
    else:
        intercept_scaled = 0.0
        coef_scaled = params_sm

    params_original = _backscale_params(
        coef_scaled, intercept_scaled, x_mean, x_scale, data_input.has_const
    )

    fittedvalues = x_sm @ params_sm
    ss_res = float(np.sum((data_input.y_data - fittedvalues) ** 2))
    ss_tot = float(np.sum((data_input.y_data - data_input.y_data.mean()) ** 2))
    r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    bootstrap_ci_lower: np.ndarray | None = None
    bootstrap_ci_upper: np.ndarray | None = None
    selection_rate: np.ndarray | None = None

    if data_input.calculate_se:
        n_params = len(params_original)
        bootstrap_coefs = np.zeros((data_input.bootstrap_iterations, n_params))
        # Eco-Note C: Generator ベースの RNG で在様性を確保
        rng = np.random.default_rng(data_input.random_state)

        for i in range(data_input.bootstrap_iterations):
            idx = rng.choice(n_samples, n_samples, replace=True)
            y_boot = data_input.y_data[idx]
            x_boot_no_const = x_no_const[idx]

            x_boot_sc, boot_mean, boot_scale = _standardize(x_boot_no_const)
            x_boot_sm = (
                sm.add_constant(x_boot_sc, has_constant="add")
                if data_input.has_const
                else x_boot_sc
            )
            boot_alpha_arr = _build_alpha_arr(
                alpha_sm, data_input.has_const, n_features
            )
            boot_result = sm.OLS(y_boot, x_boot_sm).fit_regularized(
                method="elastic_net",
                alpha=boot_alpha_arr,  # type: ignore[arg-type]
                L1_wt=1.0,
                maxiter=data_input.max_iter,
            )
            boot_params_sm = np.asarray(boot_result.params, dtype=np.float64)
            if data_input.has_const:
                boot_int_sc = float(boot_params_sm[0])
                boot_coef_sc = boot_params_sm[1:]
            else:
                boot_int_sc = 0.0
                boot_coef_sc = boot_params_sm
            bootstrap_coefs[i] = _backscale_params(
                boot_coef_sc,
                boot_int_sc,
                boot_mean,
                boot_scale,
                data_input.has_const,
            )

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
        n_obs=n_samples,
        has_const=data_input.has_const,
        fittedvalues=fittedvalues,
        x_data=x_no_const,
        y_data=data_input.y_data,
        converged=converged,
        bootstrap_ci_lower=bootstrap_ci_lower,
        bootstrap_ci_upper=bootstrap_ci_upper,
        selection_rate=selection_rate,
    )


def fit_ridge(  # noqa: PLR0915
    data_input: RegularizedRegressionInput,
) -> RegularizedResult:
    """
    Ridge モデルのフィッティング（statsmodels 座標降下法 elastic_net 使用）

    Eco-Note D: alpha 変換規約
        glmnet λ（デフォルト）→ statsmodels α = λ（直接一致）
        sklearn  α            → statsmodels α = α / n

    - R²: 手動計算 (1 - SS_res / SS_tot)
    - calculate_se=True 時はブートストラップを実行し、
      様本分布の標準偏差（bootstrap_se）と
      パーセンタイル法 95% CI を返す。
    - t 値・ p 値は理論的根拠なしのため常に None。
    - 収束失敗時は converged=False として警告を後段に伝達する。

    Args:
        data_input: RegularizedRegressionInput データクラス

    Returns:
        RegularizedResult
    """
    import statsmodels.api as sm  # noqa: PLC0415

    x_no_const = remove_const_column(data_input.x_data, data_input.has_const)
    n_samples, n_features = x_no_const.shape

    x_scaled, x_mean, x_scale = _standardize(x_no_const)

    x_sm = (
        sm.add_constant(x_scaled, has_constant="add")
        if data_input.has_const
        else x_scaled
    )

    alpha_sm = _to_statsmodels_alpha(
        data_input.alpha,
        data_input.alpha_convention,
        n_samples,
        l1_wt=0.0,
    )
    alpha_arr = _build_alpha_arr(alpha_sm, data_input.has_const, n_features)

    sm_model = sm.OLS(data_input.y_data, x_sm, missing=data_input.missing)
    result = sm_model.fit_regularized(
        method="elastic_net",
        alpha=alpha_arr,  # type: ignore[arg-type]
        L1_wt=0.0,
        maxiter=data_input.max_iter,
    )
    converged = bool(getattr(result, "converged", True))

    params_sm = np.asarray(result.params, dtype=np.float64)
    if data_input.has_const:
        intercept_scaled = float(params_sm[0])
        coef_scaled = params_sm[1:]
    else:
        intercept_scaled = 0.0
        coef_scaled = params_sm

    params_original = _backscale_params(
        coef_scaled, intercept_scaled, x_mean, x_scale, data_input.has_const
    )

    fittedvalues = x_sm @ params_sm
    ss_res = float(np.sum((data_input.y_data - fittedvalues) ** 2))
    ss_tot = float(np.sum((data_input.y_data - data_input.y_data.mean()) ** 2))
    r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    bootstrap_ci_lower: np.ndarray | None = None
    bootstrap_ci_upper: np.ndarray | None = None
    bootstrap_se: np.ndarray | None = None

    if data_input.calculate_se:
        n_params = len(params_original)
        bootstrap_coefs = np.zeros((data_input.bootstrap_iterations, n_params))
        # Eco-Note C: Generator ベースの RNG で在様性を確保
        rng = np.random.default_rng(data_input.random_state)

        for i in range(data_input.bootstrap_iterations):
            idx = rng.choice(n_samples, n_samples, replace=True)
            y_boot = data_input.y_data[idx]
            x_boot_no_const = x_no_const[idx]

            x_boot_sc, boot_mean, boot_scale = _standardize(x_boot_no_const)
            x_boot_sm = (
                sm.add_constant(x_boot_sc, has_constant="add")
                if data_input.has_const
                else x_boot_sc
            )
            boot_alpha_arr = _build_alpha_arr(
                alpha_sm, data_input.has_const, n_features
            )
            boot_result = sm.OLS(y_boot, x_boot_sm).fit_regularized(
                method="elastic_net",
                alpha=boot_alpha_arr,  # type: ignore[arg-type]
                L1_wt=0.0,
                maxiter=data_input.max_iter,
            )
            boot_params_sm = np.asarray(boot_result.params, dtype=np.float64)
            if data_input.has_const:
                boot_int_sc = float(boot_params_sm[0])
                boot_coef_sc = boot_params_sm[1:]
            else:
                boot_int_sc = 0.0
                boot_coef_sc = boot_params_sm
            bootstrap_coefs[i] = _backscale_params(
                boot_coef_sc,
                boot_int_sc,
                boot_mean,
                boot_scale,
                data_input.has_const,
            )

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
        n_obs=n_samples,
        has_const=data_input.has_const,
        fittedvalues=fittedvalues,
        x_data=x_no_const,
        y_data=data_input.y_data,
        converged=converged,
        bootstrap_ci_lower=bootstrap_ci_lower,
        bootstrap_ci_upper=bootstrap_ci_upper,
        bootstrap_se=bootstrap_se,
    )


def fit_wls(
    y_data: np.ndarray,
    x_data: np.ndarray,
    weights: np.ndarray,
    missing: str,
) -> RegressionResultsWrapper:
    """WLS モデルのフィッティング。

    Eco-Note: weights は 1/σ²_i に対応する正の重みベクトル。
    statsmodels WLS(y, X, weights=w) は
        min Σ w_i (y_i - x_i β)²
    を最小化する。w_i = 1/σ²_i とすることで GLS の特殊ケースとして
    不均一分散を効率的に処理する。

    Args:
        y_data: 被説明変数
        x_data: 説明変数（定数項含む）
        weights: 観測値ごとの重み (1/σ²_i)。全値 > 0 が必要。
        missing: 欠損値処理方法 ('none', 'drop', 'raise')

    Returns:
        statsmodels の WLS 回帰結果
    """
    import statsmodels.api as sm  # noqa: PLC0415

    model = sm.WLS(
        y_data,
        x_data,
        weights=weights,  # type: ignore[arg-type]
        missing=missing,
    )
    return model.fit()


def fit_gls(
    y_data: np.ndarray,
    x_data: np.ndarray,
    sigma: np.ndarray,
) -> RegressionResultsWrapper:
    """GLS モデルのフィッティング（既知の分散共分散行列を使用）。

    Eco-Note: sigma は n×n の正定値分散共分散行列 Σ。
    statsmodels GLS(y, X, sigma=Σ) は Aitken の一般化最小二乗法
        β̂_GLS = (X'Σ⁻¹X)⁻¹ X'Σ⁻¹y
    を計算する。Σ が正定値でない場合、LinAlgError が発生する。

    欠損値処理は呼び出し元で "error" 固定として行うため、
    missing 引数は不要（サンプル数と sigma の次元を一致させるため）。

    Args:
        y_data: 被説明変数 (n,)
        x_data: 説明変数 (n, k)（定数項含む）
        sigma: 分散共分散行列 (n, n)

    Returns:
        statsmodels の GLS 回帰結果
    """
    import statsmodels.api as sm  # noqa: PLC0415

    model = sm.GLS(y_data, x_data, sigma=sigma)
    return model.fit()


def fit_fgls_heteroskedastic(
    y_data: np.ndarray,
    x_data: np.ndarray,
    missing: str,
) -> RegressionResultsWrapper:
    """1ステップ FGLS（不均一分散対応）のフィッティング。

    Eco-Note: OLS 残差 ê_i から分散を推定し WLS を適用する。
        Step 1: OLS 推定 → ê = y - Xβ̂_OLS
        Step 2: σ̂²_i = ê²_i（ゼロ除算防止のため ε = 1e-8 でクリップ）
        Step 3: WLS(weights = 1/σ̂²_i) で再推定
    この手法は不均一分散の構造が未知の場合の FGLS 近似として広く使われる。

    Args:
        y_data: 被説明変数
        x_data: 説明変数（定数項含む）
        missing: 欠損値処理方法

    Returns:
        statsmodels の WLS 回帰結果（FGLS 第2ステップ）
    """
    import statsmodels.api as sm  # noqa: PLC0415

    # Step 1: OLS で残差を取得
    ols_result = sm.OLS(y_data, x_data, missing=missing).fit()
    residuals = np.asarray(ols_result.resid, dtype=np.float64)

    # Step 2: σ̂²_i = ê²_i（数値安定性のため最小値でクリップ）
    sigma2_hat = np.clip(residuals**2, a_min=1e-8, a_max=None)
    weights = 1.0 / sigma2_hat

    # Step 3: WLS 再推定
    model = sm.WLS(
        y_data,
        x_data,
        weights=weights,  # type: ignore[arg-type]
        missing=missing,
    )
    return model.fit()


def fit_fgls_ar1(
    y_data: np.ndarray,
    x_data: np.ndarray,
    max_iter: int,
    missing: str,
) -> RegressionResultsWrapper:
    """AR(1) 誤差構造を仮定した FGLS（GLSAR）のフィッティング。

    Eco-Note: statsmodels GLSAR は AR(p) 誤差の GLS を反復推定する。
        Step 1: OLS → 残差から ρ を推定
        Step 2: Prais-Winsten 変換で GLS
        → max_iter 回まで収束判定を繰り返す。
    系列相関が疑われる時系列データに有効。

    Args:
        y_data: 被説明変数
        x_data: 説明変数（定数項含む）
        max_iter: 収束判定の最大イテレーション数
        missing: 欠損値処理方法

    Returns:
        statsmodels の GLSAR 回帰結果
    """
    import statsmodels.api as sm  # noqa: PLC0415

    model = sm.GLSAR(y_data, x_data, rho=1, missing=missing)
    return model.iterative_fit(maxiter=max_iter)
