"""変量効果回帰テスト"""

from pathlib import Path
from typing import cast

import pandas as pd
import polars as pl
from fastapi import status
from linearmodels.panel import RandomEffects

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import (
    URL_REGRESSION,
    RePayload,
    load_py_gold,
)

# 数値比較の許容誤差
_ABS_TOL = 1e-8
# gold JSON は linearmodels の版差を考慮して少し広め
_GOLD_ABS_TOL = 1e-3

# nObservations 定数（10 エンティティ × 10 期間 = 100）
_N_OBS = 100

# 洗練データ CSV パス
_PANEL_CSV = (
    Path(__file__).resolve().parents[3]
    / "test"
    / "data"
    / "csv"
    / "synthetic_panel.csv"
)


def _load_panel_df() -> pd.DataFrame:
    """synthetic_panel.csv を pandas MultiIndex DataFrame として返す。"""
    return (
        pl.read_csv(_PANEL_CSV).to_pandas().set_index(["entity_id", "time_id"])
    )


def _get_output(client, payload):
    """POSTして regressionOutput を返すヘルパー"""
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).result_data


# -----------------------------------------------------------
# 正常系テスト
# -----------------------------------------------------------


def test_re_success(client, tables_store):
    """変量効果モデルが200を返しresultIdを含むことを確認"""
    resp = client.post(URL_REGRESSION, json=RePayload().build())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_re_response_structure(client, tables_store):
    """regressionOutputに変量効果専用キーが含まれることを確認"""
    output = _get_output(client, RePayload().build())
    model_stats = output["modelStatistics"]

    for key in ("R2Within", "R2Between", "R2Overall"):
        assert key in model_stats, (
            f"キー {key!r} が modelStatistics に存在しない"
        )

    params = output["parameters"]
    assert len(params) > 0
    for p in params:
        for key in ("variable", "coefficient", "standardError", "pValue"):
            assert key in p


def test_re_coefficients_numerical(client, tables_store):
    """RE係数が gold JSON と一致することを確認"""
    gold_all = load_py_gold("re")["estimates"]["nonrobust"]["coefficients"]
    gold = {k: v for k, v in gold_all.items() if k != "const"}

    params = _get_output(client, RePayload().build())["parameters"]
    coef_map = {p["variable"]: p["coefficient"] for p in params}

    for var, exp_coef in gold.items():
        assert abs(coef_map[var] - exp_coef) < _GOLD_ABS_TOL, (
            f"{var}: got {coef_map[var]!r}, expected {exp_coef!r}"
        )


def test_re_theta_range(client, tables_store):
    """diagnostics の theta が 0 以上 1 以下であることを確認"""
    output = _get_output(client, RePayload().build())
    diagnostics = output["diagnostics"]

    if "theta" in diagnostics:
        theta = diagnostics["theta"]
        assert 0.0 <= theta <= 1.0, f"theta={theta!r} が範囲外"


def test_re_r2_values_are_float(client, tables_store):
    """R2Within・R2Between・R2Overallが数値であることを確認"""
    model_stats = _get_output(client, RePayload().build())["modelStatistics"]
    for key in ("R2Within", "R2Between", "R2Overall"):
        assert isinstance(model_stats[key], float), f"{key!r} がfloatでない"


def test_re_n_observations(client, tables_store):
    """nObservationsがPanelDataの行数と一致することを確認"""
    model_stats = _get_output(client, RePayload().build())["modelStatistics"]
    assert model_stats["nObservations"] == _N_OBS


def test_re_coefficient_sign_x1_positive(client, tables_store):
    """x1の係数が正（設計値 1.5）であることを確認"""
    params = _get_output(client, RePayload().build())["parameters"]
    coef_map = {p["variable"]: p["coefficient"] for p in params}
    assert coef_map["x1"] > 0.0


def test_re_coefficient_sign_x2_negative(client, tables_store):
    """x2の係数が負（設計値 -0.8）であることを確認"""
    params = _get_output(client, RePayload().build())["parameters"]
    coef_map = {p["variable"]: p["coefficient"] for p in params}
    assert coef_map["x2"] < 0.0


# -----------------------------------------------------------
# 標準誤差マッピング検証テスト
# -----------------------------------------------------------


def test_re_robust_se_matches_linearmodels(client, tables_store):
    """
    robust SE 付き RE の標準誤差が
    linearmodels (RandomEffects, cov_type='robust')
    の値と一致することを確認。

    旧バグ: LINEARMODELS_COV_TYPE_MAP に "robust" キーが存在しなかったため
    cov_type が 'unadjusted' にフォールバックしていた。
    このテストは旧バグ下では失敗する。
    """
    df = _load_panel_df()
    expected = RandomEffects(df["y"], df[["x1", "x2"]]).fit(cov_type="robust")

    payload = {
        "tableName": "PanelData",
        "dependentVariable": "y",
        "explanatoryVariables": ["x1", "x2"],
        "analysis": {"method": "re", "entityIdColumn": "entity_id"},
        "standardError": {"method": "robust"},
    }
    params = _get_output(client, payload)["parameters"]
    se_map = {p["variable"]: p["standardError"] for p in params}

    # RandomEffects は定数項を吸収するため params = ['x1', 'x2'] のみ
    for var in ["x1", "x2"]:
        expected_se = float(expected.std_errors[var])
        assert abs(se_map[var] - expected_se) < _ABS_TOL, (
            f"RE robust SE [{var}]: API={se_map[var]!r} "
            f"!= linearmodels={expected_se!r}"
        )


def test_re_robust_se_differs_from_nonrobust(client, tables_store):
    """
    robust SE が nonrobust SE と異なることを確認。

    旧バグ下では "robust" が "unadjusted" にフォールバックするため
    両者が一致してしまい、このテストは失敗する。
    """
    se_nonrobust = [
        p["standardError"]
        for p in _get_output(client, RePayload(se_method="nonrobust").build())[
            "parameters"
        ]
    ]
    payload_robust = {
        "tableName": "PanelData",
        "dependentVariable": "y",
        "explanatoryVariables": ["x1", "x2"],
        "analysis": {"method": "re", "entityIdColumn": "entity_id"},
        "standardError": {"method": "robust"},
    }
    se_robust = [
        p["standardError"]
        for p in _get_output(client, payload_robust)["parameters"]
    ]
    assert se_nonrobust != se_robust, (
        "RE robust SE が nonrobust SE と同一:"
        " LINEARMODELS_COV_TYPE_MAP のマッピングが"
        "正しく機能していない可能性がある"
    )


def test_re_full_numerical_validation(client, tables_store):
    """
    RE の全統計量が linearmodels (RandomEffects, cov_type='unadjusted') と
    一致することを確認。
    シミュレーションを含まないため許容誤差内の一致が期待される。

    検証内容:
      - parameters: coefficient / standardError / tValue / pValue / CI
      - modelStatistics: nObservations, R2Within/Between/Overall
      - diagnostics.theta: 変量効果の重み（全エンティティ平均）
    """
    df = _load_panel_df()
    # fit_re は exog に const を追加しないため params = ['x1', 'x2']
    ref = RandomEffects(df["y"], df[["x1", "x2"]]).fit(cov_type="unadjusted")

    output = _get_output(client, RePayload().build())
    p_map = {p["variable"]: p for p in output["parameters"]}
    ms = output["modelStatistics"]
    diag = output["diagnostics"]
    ci = ref.conf_int()  # columns: "lower" / "upper"

    # --- parameters ---
    for var in ["x1", "x2"]:
        p = p_map[var]
        ci_lower = float(cast(float, ci.loc[var, "lower"]))
        ci_upper = float(cast(float, ci.loc[var, "upper"]))
        assert abs(p["coefficient"] - float(ref.params[var])) < _ABS_TOL
        assert abs(p["standardError"] - float(ref.std_errors[var])) < _ABS_TOL
        assert abs(p["tValue"] - float(ref.tstats[var])) < _ABS_TOL
        assert abs(p["pValue"] - float(ref.pvalues[var])) < _ABS_TOL
        assert abs(p["confidenceIntervalLower"] - ci_lower) < _ABS_TOL
        assert abs(p["confidenceIntervalUpper"] - ci_upper) < _ABS_TOL

    # --- modelStatistics ---
    assert ms["nObservations"] == int(ref.nobs)
    assert abs(ms["R2Within"] - float(ref.rsquared)) < _ABS_TOL
    assert abs(ms["R2Between"] - float(ref.rsquared_between)) < _ABS_TOL
    assert abs(ms["R2Overall"] - float(ref.rsquared_overall)) < _ABS_TOL

    # --- diagnostics.theta ---
    if "theta" in diag:
        expected_theta = float(ref.theta.values.mean())
        assert abs(diag["theta"] - expected_theta) < _ABS_TOL
