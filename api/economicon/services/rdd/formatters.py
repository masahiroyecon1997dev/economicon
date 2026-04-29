"""
RDD 分析結果フォーマット関数

rdrobust / rddensity の生結果から RDDResultData 形式の dict を構築する。
副作用なし・外部状態への依存なし。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RDDFormatConfig:
    """format_rdd_result() への入力パラメータ集約クラス。"""

    table_name: str
    outcome_variable: str
    running_variable: str
    cutoff: float
    kernel: str
    p: int
    vce: str
    confidence_level: float


def format_rdd_result(
    rd_stats: dict[str, Any],
    bins_data: list[dict[str, float]],
    poly_fit: dict[str, Any],
    density_test: dict[str, Any] | None,
    placebo_tests: list[dict[str, Any]],
    config: RDDFormatConfig,
) -> dict[str, Any]:
    """
    各ヘルパーの出力を RDDResultData スキーマに対応する dict に変換する。

    Eco-Note:
        estimate.coef は conventional 推定値（局所 p 次多項式の境界係数）。
        estimate.bias_corrected_coef は bias-corrected 点推定値（p+1 次補正）。
        信頼区間は robust CI（バイアス補正 + robust SE）を bias_corrected_ci_*
        として返す。フロントエンドでは robust CI を優先表示すること。

    Parameters
    ----------
    rd_stats : dict
        extract_rdrobust_results() の戻り値
    bins_data : list[dict]
        compute_bins_data() の戻り値
    poly_fit : dict
        compute_poly_fit_data() の戻り値
    density_test : dict | None
        run_density_test() の戻り値
    placebo_tests : list[dict]
        run_placebo_tests() の戻り値
    config : RDDFormatConfig
        メタ情報

    Returns
    -------
    dict
        RDDResultData スキーマに対応する camelCase dict
    """
    estimate = {
        "coef": rd_stats["conv_coef"],
        "stdErr": rd_stats["conv_se"],
        "zStat": rd_stats["conv_z"],
        "pValue": rd_stats["conv_pv"],
        "ciLower": rd_stats["conv_ci_lower"],
        "ciUpper": rd_stats["conv_ci_upper"],
        # Eco-Note: Calonico et al. (2014) 推奨の robust 推論。
        # biasCorrectedZStat / biasCorrectedPValue は
        # bias-corrected 点推定値 ÷ robust SE に基づく。
        # フロントエンドでは conventional zStat/pValue ではなく
        # こちらを優先表示すること。
        "biasCorrectedCoef": rd_stats["bc_coef"],
        "biasCorrectedZStat": rd_stats["bc_z"],
        "biasCorrectedPValue": rd_stats["bc_pv"],
        "biasCorrectedCiLower": rd_stats["bc_ci_lower"],
        "biasCorrectedCiUpper": rd_stats["bc_ci_upper"],
        "rho": rd_stats["rho"],
    }

    bandwidth = {
        "bwLeft": rd_stats["h_left"],
        "bwRight": rd_stats["h_right"],
        "bwBiasLeft": rd_stats["b_left"],
        "bwBiasRight": rd_stats["b_right"],
        "nLeft": rd_stats["n_left"],
        "nRight": rd_stats["n_right"],
        "nTotal": rd_stats["n_total"],
    }

    formatted_bins = [{"x": b["x"], "y": b["y"]} for b in bins_data]

    poly_fit_data = {
        "left": {
            "x": poly_fit["left"]["x"],
            "y": poly_fit["left"]["y"],
        },
        "right": {
            "x": poly_fit["right"]["x"],
            "y": poly_fit["right"]["y"],
        },
    }

    density_out: dict[str, Any] | None = None
    if density_test is not None:
        density_out = {
            "testStatistic": density_test["test_statistic"],
            "pValue": density_test["p_value"],
            "description": density_test["description"],
        }

    placebo_out = [
        {
            "cutoff": pt["cutoff"],
            "coef": pt["coef"],
            "stdErr": pt["std_err"],
            "pValue": pt["p_value"],
            "ciLower": pt["ci_lower"],
            "ciUpper": pt["ci_upper"],
            "isSignificant": pt["is_significant"],
        }
        for pt in placebo_tests
    ]

    return {
        "tableName": config.table_name,
        "outcomeVariable": config.outcome_variable,
        "runningVariable": config.running_variable,
        "cutoff": config.cutoff,
        "kernel": config.kernel,
        "p": config.p,
        "vce": config.vce,
        "confidenceLevel": config.confidence_level,
        "estimate": estimate,
        "bandwidth": bandwidth,
        "binsData": formatted_bins,
        "polyFitData": poly_fit_data,
        "densityTest": density_out,
        "placeboTests": placebo_out,
    }


# シリアライズ用の空デフォルト（テスト・型チェック補助）
@dataclass
class _EmptyPolyFit:
    left: dict[str, list[float]] = field(
        default_factory=lambda: {"x": [], "y": []}
    )
    right: dict[str, list[float]] = field(
        default_factory=lambda: {"x": [], "y": []}
    )
