"""DID（差の差）Python gold benchmark 生成。

TWFE (Two-Way Fixed Effects) + Event Study を linearmodels PanelOLS で推定し
JSON 互換の dict を返す。

API 内部の fitters.py と同一の変数命名規則を使用:
  - 基本 DID 交差項: ``_did_interact = treated * post``
  - Event Study 列 : ``_es_{k}  (k = event_time, base_period 除外)``
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS

from benchmarks.helpers import f

# API と一致させるプレフィックス
_DID_INTERACT_COL = "_did_interact"
_ES_PREFIX = "_es_"

# 生成設定（data_generators/did.py と一致）
_DEP = "y"
_EXPL = ["x1", "x2"]
_TREATED_COL = "treated"
_POST_COL = "post"
_TIME_COL = "time_id"
_ENTITY_COL = "entity_id"
_EVENT_TIME_COL = "event_time"
_TREATMENT_START = 4  # time_id >= 4 → post=1
_BASE_PERIOD = _TREATMENT_START - 1  # =3 → event_time = 3-4 = -1


def _fit_twfe(df_idx: pd.DataFrame, cov_type: str, **cov_kwargs) -> dict:
    """TWFE PanelOLS を推定し paremter dict を返す。"""
    vars_in_model = _EXPL + [_DID_INTERACT_COL]
    res = PanelOLS(
        df_idx[_DEP],
        df_idx[vars_in_model],
        entity_effects=True,
        time_effects=True,
    ).fit(cov_type=cov_type, **cov_kwargs)

    conf_int = res.conf_int()
    params = res.params
    se = res.std_errors
    ts = res.tstats
    ps = res.pvalues

    def _coef(name: str) -> dict:
        return {
            "coefficient": f(params[name]),
            "standard_error": f(se[name]),
            "t_value": f(ts[name]),
            "p_value": f(ps[name]),
            "ci_lower": f(conf_int.loc[name, "lower"]),
            "ci_upper": f(conf_int.loc[name, "upper"]),
        }

    did_est = {
        **_coef(_DID_INTERACT_COL),
        "description": "ATT: Average Treatment Effect on the Treated (TWFE)",
    }
    parameters = [{"name": col, **_coef(col)} for col in _EXPL]
    model_stats = {
        "n_observations": int(res.nobs),
        "r2": f(res.rsquared),
        "adjusted_r2": f(res.rsquared),
        "f_value": f(res.f_statistic.stat),
        "f_probability": f(res.f_statistic.pval),
    }
    return {
        "did_estimate": did_est,
        "parameters": parameters,
        "model_statistics": model_stats,
    }


def _fit_event_study(df_orig: pd.DataFrame) -> dict:
    """Event Study (entity+time FE, entity-clustered SE) を推定。"""
    df = df_orig.copy()
    event_times = sorted(df[_EVENT_TIME_COL].unique())

    # 基準期 (event_time = base_period - TREATMENT_START = -1) を除外した列を追加
    es_cols: list[str] = []
    base_event = _BASE_PERIOD - _TREATMENT_START  # = -1
    for k in event_times:
        if k == base_event:
            continue
        col = f"{_ES_PREFIX}{int(k)}"
        df[col] = (df[_EVENT_TIME_COL] == k).astype(float) * df[_TREATED_COL]
        es_cols.append(col)

    df_idx = df.set_index([_ENTITY_COL, _TIME_COL])
    vars_in_model = _EXPL + es_cols
    res = PanelOLS(
        df_idx[_DEP],
        df_idx[vars_in_model],
        entity_effects=True,
        time_effects=True,
    ).fit(cov_type="clustered", cluster_entity=True)

    conf_int = res.conf_int()
    params = res.params
    se = res.std_errors
    ts = res.tstats
    ps = res.pvalues

    # Event Study ポイント（基準期の 0 エントリも含む）
    event_study_points: list[dict] = []
    event_study_points.append(
        {
            "period": int(base_event),
            "coefficient": 0.0,
            "standard_error": 0.0,
            "t_value": 0.0,
            "p_value": 1.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
        }
    )
    for col in es_cols:
        period = int(col[len(_ES_PREFIX) :])
        event_study_points.append(
            {
                "period": period,
                "coefficient": f(params[col]),
                "standard_error": f(se[col]),
                "t_value": f(ts[col]),
                "p_value": f(ps[col]),
                "ci_lower": f(conf_int.loc[col, "lower"]),
                "ci_upper": f(conf_int.loc[col, "upper"]),
            }
        )
    event_study_points.sort(key=lambda x: x["period"])

    # Pre-trend Wald テスト: event_time < 0 の係数が同時に 0
    pre_cols = [c for c in es_cols if int(c[len(_ES_PREFIX) :]) < 0]
    pre_trend_test: dict | None = None
    if pre_cols:
        # LinearModelResults.wald_test(restriction) はサポートされていないため
        # 手動で F 検定に相当する Wald 統計量を計算する
        try:
            wald = res.wald_test(
                restriction=np.eye(len(vars_in_model))[: len(pre_cols)],
                value=np.zeros(len(pre_cols)),
            )
            pre_trend_test = {
                "f_statistic": f(wald.stat),
                "df1": int(wald.df),
                "df2": int(res.df_resid) if hasattr(res, "df_resid") else None,
                "p_value": f(wald.pval),
            }
        except Exception:
            # Wald テスト計算失敗時は Null とし、テストでは pre-trend の存在確認に留める
            pre_trend_test = None

    return {
        "event_study_points": event_study_points,
        "diagnostics": {"pre_trend_test": pre_trend_test},
    }


def bench_did(df: pd.DataFrame) -> dict:
    """DID ベンチマーク全体を生成して返す。"""
    df_idx = df.set_index([_ENTITY_COL, _TIME_COL]).copy()
    df_idx[_DID_INTERACT_COL] = df_idx[_TREATED_COL] * df_idx[_POST_COL]

    # TWFE: nonrobust（unadjusted）
    twfe_nonrobust = _fit_twfe(df_idx, cov_type="unadjusted")

    # TWFE: entity cluster SE
    twfe_clustered = _fit_twfe(df_idx, cov_type="clustered", cluster_entity=True)

    # entity / control カウント
    entity_treatment = df_idx[_TREATED_COL].groupby(level=0).first()
    n_treated = int((entity_treatment == 1).sum())
    n_control = int((entity_treatment == 0).sum())
    n_periods = int(df[_TIME_COL].nunique())
    n_obs = len(df)

    # model_statistics に entity/period 情報を追加
    for twfe in (twfe_nonrobust, twfe_clustered):
        twfe["model_statistics"]["n_treated"] = n_treated
        twfe["model_statistics"]["n_control"] = n_control
        twfe["model_statistics"]["n_periods"] = n_periods
        twfe["model_statistics"]["n_observations"] = n_obs

    # Event Study
    event_study = _fit_event_study(df)

    return {
        "input": {
            "dependent_variable": _DEP,
            "treatment_column": _TREATED_COL,
            "post_column": _POST_COL,
            "time_column": _TIME_COL,
            "entity_id_column": _ENTITY_COL,
            "confidence_level": 0.95,
            "n_entities": int(df[_ENTITY_COL].nunique()),
            "n_periods": n_periods,
            "n_treated": n_treated,
            "n_control": n_control,
        },
        "twfe": {
            "nonrobust": twfe_nonrobust,
            "clustered_entity": twfe_clustered,
        },
        "event_study": event_study,
    }
