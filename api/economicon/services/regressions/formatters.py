"""
回帰分析結果フォーマット関数

各モデルの regression_output dict を構築する純粋関数群。
副作用なし・外部状態への依存なし。
"""

import logging
from typing import Any

import numpy as np
from scipy import stats as spstats

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas.standard_error_settings import (
    ClusteredStandardError,
)
from economicon.services.regressions.common import (
    extract_linearmodels_params,
    extract_statsmodels_params,
)
from economicon.services.regressions.fitters import RegularizedResult
from economicon.utils import ProcessingError

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 共通ヘルパー
# ---------------------------------------------------------------------------


def build_groups_arrays(
    df: Any,
    y_data: np.ndarray,
    x_data: np.ndarray,
    standard_error: Any,
) -> dict[str, np.ndarray] | None:
    """ClusteredStandardError 用の欠損除去済みグループ配列辞書を構築する。

    ClusteredStandardError 以外の場合は None を返す。
    """
    if not isinstance(standard_error, ClusteredStandardError):
        return None
    x_nan = (
        np.isnan(x_data).any(axis=1) if x_data.ndim > 1 else np.isnan(x_data)
    )
    valid_mask = ~(np.isnan(y_data) | x_nan)
    return {
        col: df[col].to_numpy()[valid_mask] for col in standard_error.groups
    }


# ---------------------------------------------------------------------------
# OLS / Logit / Probit 共通フォーマット
# ---------------------------------------------------------------------------


def format_statsmodels_result(
    model_result: Any,
    table_name: str,
    dependent_variable: str,
    explanatory_variables: list[str],
    has_const: bool,
) -> dict:
    """OLS / Logit / Probit の statsmodels 結果を dict に変換する。"""
    summary_text = model_result.summary().as_text()

    param_names = (["const"] if has_const else []) + explanatory_variables
    params_info = extract_statsmodels_params(model_result, param_names)

    model_stats: dict[str, Any] = {"nObservations": int(model_result.nobs)}
    if hasattr(model_result, "rsquared"):
        model_stats["R2"] = float(model_result.rsquared)
    if hasattr(model_result, "rsquared_adj"):
        model_stats["adjustedR2"] = float(model_result.rsquared_adj)
    if hasattr(model_result, "fvalue"):
        model_stats["fValue"] = float(model_result.fvalue)
    if hasattr(model_result, "f_pvalue"):
        model_stats["fProbability"] = float(model_result.f_pvalue)
    if hasattr(model_result, "aic"):
        model_stats["AIC"] = float(model_result.aic)
    if hasattr(model_result, "bic"):
        model_stats["BIC"] = float(model_result.bic)
    if hasattr(model_result, "llf"):
        model_stats["logLikelihood"] = float(model_result.llf)
    if hasattr(model_result, "prsquared"):
        model_stats["pseudoRSquared"] = float(model_result.prsquared)

    return {
        "tableName": table_name,
        "dependentVariable": dependent_variable,
        "explanatoryVariables": explanatory_variables,
        "regressionResult": summary_text,
        "parameters": params_info,
        "modelStatistics": model_stats,
    }


def compute_ame(
    model_result: Any,
    has_const: bool,
    explanatory_variables: list[str],
) -> list[dict[str, Any]]:
    """平均限界効果 (AME) を計算する。

    at='overall' でデータ全体の平均を使用する。
    定数項は結果から除外する（解釈不能なため）。
    """
    try:
        margeff = model_result.get_margeff(at="overall")
        param_names = (["const"] if has_const else []) + explanatory_variables
        ci = margeff.conf_int()
        result_list: list[dict[str, Any]] = []
        # Critical#1: margeff の下標は定数項を含まないため
        # param_names とは別に ame_idx で管理する。
        ame_idx = 0
        for name in param_names:
            if name == "const":
                continue
            result_list.append(
                {
                    "variable": name,
                    "marginalEffect": float(margeff.margeff[ame_idx]),
                    "standardError": float(margeff.margeff_se[ame_idx]),
                    "tValue": float(margeff.tvalues[ame_idx]),
                    "pValue": float(margeff.pvalues[ame_idx]),
                    "confidenceIntervalLower": float(ci[ame_idx, 0]),
                    "confidenceIntervalUpper": float(ci[ame_idx, 1]),
                }
            )
            ame_idx += 1
        return result_list
    except Exception as e:
        raise ProcessingError(
            error_code=ErrorCode.REGRESSION_PROCESS_ERROR,
            message=_("Failed to compute average marginal effects"),
        ) from e


# ---------------------------------------------------------------------------
# Tobit
# ---------------------------------------------------------------------------


def format_tobit_result(
    model_result: Any,
    table_name: str,
    dependent_variable: str,
    explanatory_variables: list[str],
    has_const: bool,
    left_censoring_limit: float | None,
    right_censoring_limit: float | None,
    lr_test_result: dict[str, Any] | None = None,
) -> dict:
    """Tobit モデルの結果を dict に変換する。"""
    summary_text = str(model_result.summary())

    param_names = (["const"] if has_const else []) + explanatory_variables
    params_info = extract_statsmodels_params(model_result, param_names)

    model_stats: dict[str, Any] = {
        "nObservations": int(model_result.nobs),
        "logLikelihood": float(model_result.llf),
    }
    if hasattr(model_result, "aic"):
        model_stats["AIC"] = float(model_result.aic)
    if hasattr(model_result, "bic"):
        model_stats["BIC"] = float(model_result.bic)

    diagnostics: dict[str, Any] = {
        "censoringLimits": {
            "left": left_censoring_limit,
            "right": right_censoring_limit,
        }
    }

    if hasattr(model_result, "scale"):
        diagnostics["sigma"] = float(model_result.scale)
        diagnostics["sigmaDescription"] = "Standard error of the error term"

    try:
        n_params = len(model_result.params)
        start_idx = 1 if has_const else 0
        n_slopes = n_params - start_idx
        if n_slopes > 0:
            r_matrix = np.eye(n_params)[start_idx:]
            wald = model_result.wald_test(r_matrix, scalar=True)
            diagnostics["waldTest"] = {
                "statistic": float(wald.statistic),
                "pValue": float(wald.pvalue),
                "df": n_slopes,
                "description": (
                    "Wald test for joint significance of slope parameters"
                ),
            }
    except Exception:
        pass

    if lr_test_result is not None:
        diagnostics["lrTest"] = lr_test_result

    return {
        "tableName": table_name,
        "dependentVariable": dependent_variable,
        "explanatoryVariables": explanatory_variables,
        "regressionResult": summary_text,
        "parameters": params_info,
        "modelStatistics": model_stats,
        "diagnostics": diagnostics,
    }


def build_tobit_lr_test(
    model_result: Any,
    null_result: Any,
    n_slopes: int,
) -> dict[str, Any]:
    """Tobit LR 検定結果 dict を構築する。"""
    lr_stat = 2.0 * (float(model_result.llf) - float(null_result.llf))
    lr_pvalue = float(spstats.chi2.sf(lr_stat, df=n_slopes))
    return {
        "statistic": lr_stat,
        "pValue": lr_pvalue,
        "df": n_slopes,
        "description": "Likelihood ratio test vs. constant-only Tobit",
    }


# ---------------------------------------------------------------------------
# IV
# ---------------------------------------------------------------------------


def format_iv_result(
    model_result: Any,
    table_name: str,
    dependent_variable: str,
    explanatory_variables: list[str],
    endogenous_variables: list[str],
    instrumental_variables: list[str],
    has_const: bool,
) -> dict:
    """IV (linearmodels) の結果を dict に変換する。"""
    summary_text = str(model_result.summary)

    all_vars = (
        (["const"] if has_const else [])
        + explanatory_variables
        + endogenous_variables
    )
    params_info = extract_linearmodels_params(model_result, all_vars)

    model_stats: dict[str, Any] = {
        "nObservations": int(model_result.nobs),
        "R2": float(model_result.rsquared),
    }

    diagnostics: dict[str, Any] = {}

    if hasattr(model_result, "wu_hausman"):
        try:
            wu_test = model_result.wu_hausman()
            diagnostics["wuHausmanTest"] = {
                "statistic": float(wu_test.stat),
                "pValue": float(wu_test.pval),
                "description": "Test for endogeneity",
            }
        except Exception:
            pass

    if hasattr(model_result, "sargan"):
        try:
            sargan = model_result.sargan
            diagnostics["sarganTest"] = {
                "statistic": float(sargan.stat),
                "pValue": float(sargan.pval),
                "description": "Test for overidentifying restrictions",
            }
        except Exception:
            pass

    if hasattr(model_result, "first_stage"):
        try:
            first_stage = model_result.first_stage
            diagnostics["firstStage"] = {}
            for endog_var in endogenous_variables:
                if endog_var in first_stage.individual:
                    fs_result = first_stage.individual[endog_var]
                    diagnostics["firstStage"][endog_var] = {
                        "fStatistic": float(fs_result.f_statistic.stat),
                        "pValue": float(fs_result.f_statistic.pval),
                        "description": (
                            "First-stage F-test for weak instruments"
                        ),
                    }
        except Exception:
            pass

    return {
        "tableName": table_name,
        "dependentVariable": dependent_variable,
        "explanatoryVariables": explanatory_variables,
        "endogenousVariables": endogenous_variables,
        "instrumentalVariables": instrumental_variables,
        "regressionResult": summary_text,
        "parameters": params_info,
        "modelStatistics": model_stats,
        "diagnostics": diagnostics,
    }


# ---------------------------------------------------------------------------
# Fixed Effects
# ---------------------------------------------------------------------------


def format_fe_result(
    model_result: Any,
    table_name: str,
    dependent_variable: str,
    explanatory_variables: list[str],
    entity_id_column: str,
) -> dict:
    """固定効果モデル (linearmodels) の結果を dict に変換する。"""
    summary_text = str(model_result.summary)

    params_info = extract_linearmodels_params(
        model_result, explanatory_variables
    )

    model_stats: dict[str, Any] = {
        "nObservations": int(model_result.nobs),
        "nEntities": int(model_result.entity_info["total"]),
        "R2Within": float(model_result.rsquared),
        "R2Between": float(model_result.rsquared_between),
        "R2Overall": float(model_result.rsquared_overall),
        "fValue": float(model_result.f_statistic.stat),
        "fProbability": float(model_result.f_statistic.pval),
    }

    diagnostics: dict[str, Any] = {}
    if hasattr(model_result, "f_pooled"):
        diagnostics["fPooled"] = {
            "statistic": float(model_result.f_pooled.stat),
            "pValue": float(model_result.f_pooled.pval),
            "description": "Test for entity effects",
        }

    return {
        "tableName": table_name,
        "dependentVariable": dependent_variable,
        "explanatoryVariables": explanatory_variables,
        "entityIdColumn": entity_id_column,
        "estimationMethod": "Fixed Effects (Within)",
        "regressionResult": summary_text,
        "parameters": params_info,
        "modelStatistics": model_stats,
        "diagnostics": diagnostics,
    }


# ---------------------------------------------------------------------------
# Random Effects
# ---------------------------------------------------------------------------


def format_re_result(
    model_result: Any,
    table_name: str,
    dependent_variable: str,
    explanatory_variables: list[str],
    entity_id_column: str,
) -> dict:
    """変量効果モデル (linearmodels) の結果を dict に変換する。

    実装差異:
        分散成分の推定量は linearmodels の独自アルゴリズムを使用するため、
        R の plm (Swamy-Arora 推定量) と比較した場合に
        最大約 7% の差異が生じる。
        これはバグではなく分散成分推定量の定義の違いによるもの。
    """  # noqa: RUF002
    summary_text = str(model_result.summary)

    params_info = extract_linearmodels_params(
        model_result, explanatory_variables
    )

    model_stats: dict[str, Any] = {
        "nObservations": int(model_result.nobs),
        "R2Within": float(model_result.rsquared),
        "R2Between": float(model_result.rsquared_between),
        "R2Overall": float(model_result.rsquared_overall),
    }

    diagnostics: dict[str, Any] = {}
    if hasattr(model_result, "theta"):
        theta_value = model_result.theta
        if hasattr(theta_value, "mean"):
            if hasattr(theta_value, "values"):
                diagnostics["theta"] = float(theta_value.values.mean())
            else:
                diagnostics["theta"] = float(theta_value.mean())
        else:
            diagnostics["theta"] = float(theta_value)
        diagnostics["thetaDescription"] = (
            "Weight of random effects transformation (0=pooled, 1=within)"
        )

    return {
        "tableName": table_name,
        "dependentVariable": dependent_variable,
        "explanatoryVariables": explanatory_variables,
        "entityIdColumn": entity_id_column,
        "estimationMethod": "Random Effects (GLS)",
        "regressionResult": summary_text,
        "parameters": params_info,
        "modelStatistics": model_stats,
        "diagnostics": diagnostics,
    }


# ---------------------------------------------------------------------------
# Panel IV (FE-2SLS / AbsorbingLS)
# ---------------------------------------------------------------------------

# Eco-Note: Staiger & Stock (1997) が提唱する弱操作変数の経験則閾値
_WEAK_IV_F_THRESHOLD: float = 10.0


def _compute_r2_between_overall(
    model_result: Any,
    y: Any,
) -> tuple[float | None, float | None]:
    """R²Between と R²Overall を残差から手動計算する。

    Eco-Note: AbsorbingLS は rsquared_between / rsquared_overall を
    持たないため FWL定理後の残差から算出する。
        R²_overall = 1 - Σe²_it / Σ(y_it - ȳ)²
        R²_between = 1 - Σē²_i  / Σ(ȳ_i  - ȳ)²
    """
    try:
        resids = np.asarray(model_result.resids, dtype=np.float64)
        y_vals = np.asarray(y, dtype=np.float64)
        y_mean = float(np.mean(y_vals))

        ss_tot_overall = float(np.sum((y_vals - y_mean) ** 2))
        ss_res_overall = float(np.sum(resids**2))
        r2_overall: float | None = (
            1.0 - ss_res_overall / ss_tot_overall
            if ss_tot_overall > 0
            else None
        )

        # Between: 個体平均で集計（MultiIndex の level-0 を使用）
        import pandas as pd  # noqa: PLC0415

        idx = y.index.get_level_values(0)
        e_series = pd.Series(resids, index=y.index)
        y_series = pd.Series(y_vals, index=y.index)
        e_bar = e_series.groupby(idx).mean()
        y_bar = y_series.groupby(idx).mean()
        y_bar_mean = float(y_bar.mean())
        ss_res_between = float((e_bar**2).sum())
        ss_tot_between = float(((y_bar - y_bar_mean) ** 2).sum())
        r2_between: float | None = (
            1.0 - ss_res_between / ss_tot_between
            if ss_tot_between > 0
            else None
        )

        return r2_between, r2_overall
    except Exception:
        return None, None


def _build_panel_iv_wu_hausman(
    model_result: Any,
) -> dict[str, Any] | None:
    """Wu-Hausman 内生性検定結果を構築する (H₀: 変数は外生)。"""
    if not hasattr(model_result, "wu_hausman"):
        return None
    try:
        wu = model_result.wu_hausman()
        return {
            "statistic": float(wu.stat),
            "pValue": float(wu.pval),
            "description": "Wu-Hausman test for endogeneity",
        }
    except Exception:
        return None


def _build_panel_iv_sargan(
    model_result: Any,
    n_iv: int,
    n_endog: int,
) -> dict[str, Any] | None:
    """Sargan/Hansen J 検定結果を構築する (過剰識別時のみ)。"""
    if n_iv <= n_endog or not hasattr(model_result, "sargan"):
        return None
    try:
        sargan = model_result.sargan
        return {
            "statistic": float(sargan.stat),
            "pValue": float(sargan.pval),
            "df": n_iv - n_endog,
            "description": (
                "Sargan/Hansen J test for overidentifying restrictions"
            ),
        }
    except Exception:
        return None


def _build_panel_iv_first_stage(
    model_result: Any,
    endogenous_variables: list[str],
    warnings: list[str],
) -> dict[str, Any] | None:
    """First-stage F 統計量を構築し、弱操作変数の警告を warnings に追記。"""
    if not hasattr(model_result, "first_stage"):
        return None
    try:
        first_stage = model_result.first_stage
        fs_dict: dict[str, Any] = {}
        for endog_var in endogenous_variables:
            if endog_var not in first_stage.individual:
                continue
            fs = first_stage.individual[endog_var]
            f_stat = float(fs.f_statistic.stat)
            fs_dict[endog_var] = {
                "fStatistic": f_stat,
                "pValue": float(fs.f_statistic.pval),
                "description": (
                    "First-stage F-test for weak instruments"
                    " (rule of thumb: F > 10)"
                ),
            }
            if f_stat < _WEAK_IV_F_THRESHOLD:
                warnings.append(
                    f"Weak instrument warning: first-stage F"
                    f" for '{endog_var}' = {f_stat:.2f} (< 10)"
                )
        return fs_dict
    except Exception:
        return None


def format_panel_iv_result(
    model_result: Any,
    y: Any,
    table_name: str,
    dependent_variable: str,
    explanatory_variables: list[str],
    endogenous_variables: list[str],
    instrumental_variables: list[str],
    entity_id_column: str,
) -> dict:
    """固定効果IV (AbsorbingLS) の結果を dict に変換する。

    統計量:
        R2Within  : AbsorbingLS の rsquared (absorb後の説明力)
        R2Between : 残差の個体平均から手動計算
        R2Overall : 残差全体から手動計算
        nEntities : MultiIndex level-0 の unique 数
        fPooled   : AbsorbingLS は非対応のため None
        wuHausmanTest / sarganTest / firstStage: IV検定統計量
    """
    summary_text = str(model_result.summary)
    all_vars = explanatory_variables + endogenous_variables
    params_info = extract_linearmodels_params(model_result, all_vars)

    n_entities = int(y.index.get_level_values(0).nunique())
    r2_between, r2_overall = _compute_r2_between_overall(model_result, y)

    model_stats: dict[str, Any] = {
        "nObservations": int(model_result.nobs),
        "nEntities": n_entities,
        "R2Within": float(model_result.rsquared),
    }
    if r2_between is not None:
        model_stats["R2Between"] = r2_between
    if r2_overall is not None:
        model_stats["R2Overall"] = r2_overall

    diagnostics: dict[str, Any] = {
        # Eco-Note: f_pooled は AbsorbingLS に実装されていないため省略
        # (PanelOLS.f_pooled は Within vs Pooled-OLS の F 検定だが、
        #  AbsorbingLS はその統計量を提供しない)
        "fPooled": None,
    }

    wu = _build_panel_iv_wu_hausman(model_result)
    if wu is not None:
        diagnostics["wuHausmanTest"] = wu

    sargan = _build_panel_iv_sargan(
        model_result,
        len(instrumental_variables),
        len(endogenous_variables),
    )
    if sargan is not None:
        diagnostics["sarganTest"] = sargan

    warnings: list[str] = []
    fs = _build_panel_iv_first_stage(
        model_result, endogenous_variables, warnings
    )
    if fs is not None:
        diagnostics["firstStage"] = fs

    return {
        "tableName": table_name,
        "dependentVariable": dependent_variable,
        "explanatoryVariables": explanatory_variables,
        "endogenousVariables": endogenous_variables,
        "instrumentalVariables": instrumental_variables,
        "entityIdColumn": entity_id_column,
        "estimationMethod": "Fixed Effects IV (FE-2SLS)",
        "regressionResult": summary_text,
        "parameters": params_info,
        "modelStatistics": model_stats,
        "diagnostics": diagnostics,
        **({"warnings": warnings} if warnings else {}),
    }


# ---------------------------------------------------------------------------
# Lasso / Ridge (正則化回帰)
# ---------------------------------------------------------------------------


def format_regularized_result(
    reg_result: RegularizedResult,
    table_name: str,
    dependent_variable: str,
    explanatory_variables: list[str],
) -> dict:
    """Lasso / Ridge の結果を dict に変換する。

    - t 値・p 値は理論的根拠なしのため常に None。
    - Ridge: ブートストラップ SE + 95% パーセンタイル CI。
    - Lasso: selectionRate + CI、SE は None（点質量問題）。
    - converged=False 時は warnings に収束失敗メッセージを追加。
    """
    param_names = (
        ["const"] if reg_result.has_const else []
    ) + explanatory_variables

    params_info: list[dict[str, Any]] = []
    for i, name in enumerate(param_names):
        is_const = name == "const"
        var_idx = (i - 1) if reg_result.has_const else i

        param_dict: dict[str, Any] = {
            "variable": name,
            "coefficient": float(reg_result.params_original[i]),
            "coefficientScaled": (
                None if is_const else float(reg_result.coef_scaled[var_idx])
            ),
            "standardError": (
                None
                if (reg_result.bootstrap_se is None or is_const)
                else float(reg_result.bootstrap_se[i])
            ),
            "tValue": None,
            "pValue": None,
            "confidenceIntervalLower": (
                None
                if reg_result.bootstrap_ci_lower is None
                else float(reg_result.bootstrap_ci_lower[i])
            ),
            "confidenceIntervalUpper": (
                None
                if reg_result.bootstrap_ci_upper is None
                else float(reg_result.bootstrap_ci_upper[i])
            ),
        }

        if reg_result.selection_rate is not None and not is_const:
            param_dict["selectionRate"] = float(
                reg_result.selection_rate[var_idx]
            )

        params_info.append(param_dict)

    model_stats: dict[str, Any] = {
        "nObservations": reg_result.n_obs,
        "R2": reg_result.r2,
        "adjustedR2": None,
        "fValue": None,
        "fProbability": None,
    }

    warnings_list: list[str] = []
    if not reg_result.converged:
        warnings_list.append(
            _(
                "収束しませんでした。計算結果は参考値です。"
                "正則化パラメータ alpha を調整するか、"
                "反復回数（maxIter）を増やしてください。"
            )
        )

    return {
        "tableName": table_name,
        "dependentVariable": dependent_variable,
        "explanatoryVariables": explanatory_variables,
        "regressionResult": None,
        "parameters": params_info,
        "modelStatistics": model_stats,
        "warnings": warnings_list,
    }
