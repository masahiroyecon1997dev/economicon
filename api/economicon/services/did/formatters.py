"""
DID 分析結果フォーマット関数

linearmodels PanelOLS の結果を DIDResultData 形式の dict に変換する。
副作用なし・外部状態への依存なし。
"""

from dataclasses import dataclass
from typing import Any

from economicon.services.did.fitters import _ES_PREFIX_LEN


@dataclass
class DIDFormatConfig:
    """format_did_result() への入力パラメータ集約クラス。"""

    table_name: str
    dependent_variable: str
    treatment_column: str
    post_column: str
    time_column: str
    entity_id_column: str
    explanatory_variables: list[str]
    confidence_level: float
    include_event_study: bool
    base_period: int
    interact_col: str | None
    es_cols: list[str]
    pre_trend_test: dict | None


def format_did_result(
    model_result: Any,
    df_pandas: Any,
    config: DIDFormatConfig,
) -> dict:
    """
    linearmodels PanelOLS 結果を DIDResultData 形式の dict に変換する。

    Eco-Note:
        rsquared は within R² (個体・時点効果除去後の説明力)。
        OLS の R² とは異なり、固定効果で説明される分散を除いた
        測度であるため一般に低くなる傾向がある。
        adjustedR2 も同値として報告する（linearmodels には
        TWFE 用の自由度調整 R² が存在しないため）。

    Args:
        model_result: linearmodels の PanelOLS 結果オブジェクト
        df_pandas: MultiIndex(entity, time) 付き Pandas DataFrame
        config: フォーマット設定

    Returns:
        DIDResultData スキーマに対応する dict
    """
    conf_int = model_result.conf_int(level=config.confidence_level)
    param_index: dict[str, int] = {
        n: i for i, n in enumerate(model_result.params.index)
    }

    def _param(col: str) -> dict:
        """指定列のパラメータ情報を抽出する。"""
        i = param_index[col]
        return {
            "coefficient": float(model_result.params.iloc[i]),
            "standardError": float(model_result.std_errors.iloc[i]),
            "tValue": float(model_result.tstats.iloc[i]),
            "pValue": float(model_result.pvalues.iloc[i]),
            "ciLower": float(conf_int.iloc[i, 0]),
            "ciUpper": float(conf_int.iloc[i, 1]),
        }

    # --- DID 推定量（ATT）---
    # 基本 DID: 交差項係数が ATT の一致推定量
    # Event Study: 集計 ATT は定義されないため NaN placeholder
    if config.interact_col is not None:
        did_estimate = {
            **_param(config.interact_col),
            "description": (
                "ATT: Average Treatment Effect on the Treated (TWFE)"
            ),
        }
    else:
        nan = float("nan")
        did_estimate = {
            "coefficient": nan,
            "standardError": nan,
            "tValue": nan,
            "pValue": nan,
            "ciLower": nan,
            "ciUpper": nan,
            "description": (
                "Event Study model: see eventStudy"
                " for period-specific estimates."
            ),
        }

    # --- 共変量係数（交差項以外）---
    parameters = [
        {"name": col, **_param(col)}
        for col in config.explanatory_variables
        if col in param_index
    ]

    # --- モデル統計量 ---
    # entity_id は MultiIndex の level 0
    entity_treatment = (
        df_pandas[config.treatment_column].groupby(level=0).first()
    )
    n_treated = int((entity_treatment == 1).sum())
    n_control = int((entity_treatment == 0).sum())
    n_periods = df_pandas.index.get_level_values(1).nunique()

    model_statistics = {
        "nObservations": int(model_result.nobs),
        "nTreated": n_treated,
        "nControl": n_control,
        "nPeriods": n_periods,
        "r2": float(model_result.rsquared),
        "adjustedR2": float(model_result.rsquared),
        "fValue": float(model_result.f_statistic.stat),
        "fProbability": float(model_result.f_statistic.pval),
    }

    # --- Event Study 係数リスト ---
    event_study: list[dict] | None = None
    if config.include_event_study:
        entries: list[dict] = []
        # base_period: 係数=0（正規化・基準期）
        entries.append(
            {
                "period": config.base_period,
                "coefficient": 0.0,
                "standardError": 0.0,
                "tValue": 0.0,
                "pValue": 1.0,
                "ciLower": 0.0,
                "ciUpper": 0.0,
            }
        )
        for col in config.es_cols:
            period = int(col[_ES_PREFIX_LEN:])
            entries.append({"period": period, **_param(col)})
        entries.sort(key=lambda e: e["period"])
        event_study = entries

    return {
        "tableName": config.table_name,
        "dependentVariable": config.dependent_variable,
        "treatmentColumn": config.treatment_column,
        "postColumn": config.post_column,
        "timeColumn": config.time_column,
        "entityIdColumn": config.entity_id_column,
        "confidenceLevel": config.confidence_level,
        "didEstimate": did_estimate,
        "parameters": parameters,
        "modelStatistics": model_statistics,
        "diagnostics": {"preTrendTest": config.pre_trend_test},
        "eventStudy": event_study,
    }
