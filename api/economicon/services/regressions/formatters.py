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
from economicon.schemas.entities import ClusteredStandardError
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
