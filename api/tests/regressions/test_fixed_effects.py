"""固定効果回帰テスト"""

from pathlib import Path
from typing import cast

import pandas as pd
import polars as pl
from fastapi import status
from linearmodels.panel import PanelOLS

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import (
    URL_REGRESSION,
    FePayload,
    load_py_gold,
)

# 数値比較の許容誤差
_ABS_TOL = 1e-8

# パラメータ数定数（FEは定数項を吸収するためconst含まず）
_N_PARAMS_FE = 2

# エンティティ数定数
_N_ENTITIES = 10

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
    """POSTして result_data を返すヘルパー"""
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).result_data


# -----------------------------------------------------------
# 正常系テスト
# -----------------------------------------------------------


def test_fe_success(client, tables_store):
    """固定効果モデルが200を返しresultIdを含むことを確認"""
    resp = client.post(URL_REGRESSION, json=FePayload().build())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_fe_response_structure(client, tables_store):
    """regressionOutputに固定効果専用キーが含まれることを確認"""
    output = _get_output(client, FePayload().build())
    model_stats = output["modelStatistics"]

    for key in (
        "R2Within",
        "R2Between",
        "R2Overall",
        "nEntities",
        "fValue",
        "fProbability",
    ):
        assert key in model_stats, (
            f"キー {key!r} が modelStatistics に存在しない"
        )

    params = output["parameters"]
    assert len(params) == _N_PARAMS_FE  # x1, x2（FEは定数項なし）
    for p in params:
        for key in ("variable", "coefficient", "standardError", "pValue"):
            assert key in p


def test_fe_coefficients_numerical(client, tables_store):
    """FE係数が gold JSON と一致することを確認"""
    gold = load_py_gold("fe")["estimates"]["nonrobust"]["coefficients"]

    params = _get_output(client, FePayload().build())["parameters"]
    coef_map = {p["variable"]: p["coefficient"] for p in params}

    for var, exp_coef in gold.items():
        assert abs(coef_map[var] - exp_coef) < _ABS_TOL, (
            f"{var}: got {coef_map[var]!r}, expected {exp_coef!r}"
        )


def test_fe_n_entities(client, tables_store):
    """nEntitiesがデータのエンティティ数と一致することを確認"""
    # PanelDataは10エンティティ
    model_stats = _get_output(client, FePayload().build())["modelStatistics"]
    assert model_stats["nEntities"] == _N_ENTITIES


def test_fe_r2_within_range(client, tables_store):
    """R2Within・R2Between・R2Overallが0以上1以下であることを確認"""
    model_stats = _get_output(client, FePayload().build())["modelStatistics"]
    for key in ("R2Within", "R2Between", "R2Overall"):
        val = model_stats[key]
        # R2はマイナスになりうる（プーリングOLSを基準にした場合）
        assert isinstance(val, float), f"{key!r} がfloatでない"


def test_fe_diagnostics_f_pooled(client, tables_store):
    """diagnostics に fPooled が含まれることを確認"""
    output = _get_output(client, FePayload().build())
    diagnostics = output["diagnostics"]
    assert "fPooled" in diagnostics
    fp = diagnostics["fPooled"]
    assert "statistic" in fp
    assert "pValue" in fp


def test_fe_clustered_se(client, tables_store):
    """クラスタロバスト標準誤差付きFEが成功することを確認"""
    payload = FePayload(se_method="cluster").build()
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["code"] == "OK"


def test_fe_coefficient_sign_x1_positive(client, tables_store):
    """x1の係数が正（設計値 1.5）であることを確認"""
    params = _get_output(client, FePayload().build())["parameters"]
    coef_map = {p["variable"]: p["coefficient"] for p in params}
    assert coef_map["x1"] > 0.0


def test_fe_coefficient_sign_x2_negative(client, tables_store):
    """x2の係数が負（設計値 -0.8）であることを確認"""
    params = _get_output(client, FePayload().build())["parameters"]
    coef_map = {p["variable"]: p["coefficient"] for p in params}
    assert coef_map["x2"] < 0.0


# -----------------------------------------------------------
# 標準誤差マッピング検証テスト
# LINEARMODELS_COV_TYPE_MAP のキーが正しく linearmodels に渡されることを確認
# -----------------------------------------------------------


def test_fe_robust_se_matches_linearmodels(client, tables_store):
    """
    robust SE 付き FE の標準誤差が linearmodels (PanelOLS, cov_type='robust')
    の値と一致することを確認。

    旧バグ: LINEARMODELS_COV_TYPE_MAP に "robust" キーが存在しなかったため
    cov_type が 'unadjusted' にフォールバックしていた。
    このテストは旧バグ下では失敗する。
    """
    df = _load_panel_df()
    expected = PanelOLS(df["y"], df[["x1", "x2"]], entity_effects=True).fit(
        cov_type="robust"
    )

    payload = FePayload(se_method="robust").build()
    params = _get_output(client, payload)["parameters"]
    se_map = {p["variable"]: p["standardError"] for p in params}

    for i, var in enumerate(["x1", "x2"]):
        expected_se = float(expected.std_errors.iloc[i])
        assert abs(se_map[var] - expected_se) < _ABS_TOL, (
            f"FE robust SE [{var}]: API={se_map[var]!r} "
            f"!= linearmodels={expected_se!r}"
        )


def test_fe_robust_se_differs_from_nonrobust(client, tables_store):
    """
    robust SE が nonrobust SE と異なることを確認。

    旧バグ下では "robust" が "unadjusted" にフォールバックするため
    両者が一致してしまい、このテストは失敗する。
    """
    se_nonrobust = [
        p["standardError"]
        for p in _get_output(client, FePayload(se_method="nonrobust").build())[
            "parameters"
        ]
    ]
    se_robust = [
        p["standardError"]
        for p in _get_output(client, FePayload(se_method="robust").build())[
            "parameters"
        ]
    ]
    assert se_nonrobust != se_robust, (
        "robust SE が nonrobust SE と同一:"
        " LINEARMODELS_COV_TYPE_MAP のマッピングが"
        "正しく機能していない可能性がある"
    )


def test_fe_cluster_se_matches_linearmodels(client, tables_store):
    """
    cluster SE 付き FE の標準誤差が linearmodels
    (PanelOLS, cov_type='clustered') の値と一致することを確認。

    旧バグ: LINEARMODELS_COV_TYPE_MAP に "cluster" キーが存在しなかったため
    cov_type が 'unadjusted' にフォールバックしていた。
    このテストは旧バグ下では失敗する。
    """
    df = _load_panel_df()
    # PanelOLS + cov_type='clustered': entity でクラスタリング（デフォルト）
    expected = PanelOLS(df["y"], df[["x1", "x2"]], entity_effects=True).fit(
        cov_type="clustered"
    )

    payload = FePayload(se_method="cluster").build()
    params = _get_output(client, payload)["parameters"]
    se_map = {p["variable"]: p["standardError"] for p in params}

    for i, var in enumerate(["x1", "x2"]):
        expected_se = float(expected.std_errors.iloc[i])
        assert abs(se_map[var] - expected_se) < _ABS_TOL, (
            f"FE cluster SE [{var}]: API={se_map[var]!r} "
            f"!= linearmodels={expected_se!r}"
        )


def test_fe_full_numerical_validation(client, tables_store):
    """
    FE の全統計量が linearmodels (PanelOLS, cov_type='unadjusted') と
    一致することを確認。
    シミュレーションを含まないため許容誤差内の一致が期待される。

    検証内容:
      - parameters: coefficient / standardError / tValue / pValue / CI
      - modelStatistics: nObservations, nEntities,
                         R2Within/Between/Overall, fValue, fProbability
      - diagnostics.fPooled: statistic, pValue
    """
    df = _load_panel_df()
    ref = PanelOLS(df["y"], df[["x1", "x2"]], entity_effects=True).fit(
        cov_type="unadjusted"
    )

    output = _get_output(client, FePayload().build())
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
    assert ms["nEntities"] == int(ref.entity_info["total"])
    assert abs(ms["R2Within"] - float(ref.rsquared)) < _ABS_TOL
    assert abs(ms["R2Between"] - float(ref.rsquared_between)) < _ABS_TOL
    assert abs(ms["R2Overall"] - float(ref.rsquared_overall)) < _ABS_TOL
    assert abs(ms["fValue"] - float(ref.f_statistic.stat)) < _ABS_TOL
    assert abs(ms["fProbability"] - float(ref.f_statistic.pval)) < _ABS_TOL

    # --- diagnostics.fPooled ---
    fp = diag["fPooled"]
    assert abs(fp["statistic"] - float(ref.f_pooled.stat)) < _ABS_TOL
    assert abs(fp["pValue"] - float(ref.f_pooled.pval)) < _ABS_TOL
