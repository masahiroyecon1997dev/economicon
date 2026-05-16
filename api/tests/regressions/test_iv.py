"""操作変数法テスト"""

from pathlib import Path
from typing import cast

import pandas as pd
import polars as pl
import pytest
import statsmodels.api as sm
from fastapi import status
from linearmodels.iv import IV2SLS
from linearmodels.iv.results import IVResults

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import (
    URL_REGRESSION,
    IvPayload,
    PanelIvPayload,
    load_py_gold,
)

# 数値比較の許容誤差
_ABS_TOL = 1e-8

# 洗練データ CSV パス
_IV_CSV = (
    Path(__file__).resolve().parents[3]
    / "test"
    / "data"
    / "csv"
    / "synthetic_iv.csv"
)


def _load_iv_df() -> pd.DataFrame:
    """synthetic_iv.csv を pandas DataFrame として返す。"""
    return pl.read_csv(_IV_CSV).to_pandas()


def _get_output(client, payload):
    """POSTして result_data を返すヘルパー"""
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).result_data


# -----------------------------------------------------------
# 正常系テスト
# -----------------------------------------------------------


def test_iv_success(client, tables_store):
    """IV回帰が200を返しresultIdを含むことを確認"""
    resp = client.post(URL_REGRESSION, json=IvPayload().build())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_iv_response_structure(client, tables_store):
    """regressionOutputにIV専用キーが含まれることを確認"""
    output = _get_output(client, IvPayload().build())
    model_stats = output["modelStatistics"]

    assert "R2" in model_stats
    assert "nObservations" in model_stats

    params = output["parameters"]
    assert len(params) > 0
    for p in params:
        for key in ("variable", "coefficient", "standardError", "pValue"):
            assert key in p


def test_iv_coefficients_numerical(client, tables_store):
    """IV係数が gold JSON と一致することを確認"""
    gold = load_py_gold("iv")["estimates"]["nonrobust"]["coefficients"]

    params = _get_output(client, IvPayload().build())["parameters"]
    coef_map = {p["variable"]: p["coefficient"] for p in params}

    for var, exp_coef in gold.items():
        assert abs(coef_map[var] - exp_coef) < _ABS_TOL, (
            f"{var}: got {coef_map[var]!r}, expected {exp_coef!r}"
        )


def test_iv_endogenous_variables_in_parameters(client, tables_store):
    """内生変数 x_endog がパラメータに含まれることを確認"""
    params = _get_output(client, IvPayload().build())["parameters"]
    var_names = [p["variable"] for p in params]
    assert "x_endog" in var_names


def test_iv_diagnostics_present(client, tables_store):
    """diagnosticsにIV検定統計量が少なくとも1つ含まれることを確認"""
    output = _get_output(client, IvPayload().build())
    diagnostics = output["diagnostics"]

    has_diag = any(
        key in diagnostics
        for key in ("wuHausmanTest", "sarganTest", "firstStage")
    )
    assert has_diag, "diagnostics にIV検定統計量が含まれない"


def test_iv_first_stage_for_endogenous(client, tables_store):
    """firstStageに内生変数のF統計量が含まれることを確認（存在する場合）"""
    output = _get_output(client, IvPayload().build())
    diagnostics = output["diagnostics"]

    if "firstStage" not in diagnostics:
        return  # firstStage診断値がない場合はスキップ

    first_stage = diagnostics["firstStage"]
    if not first_stage or "x_endog" not in first_stage:
        return  # firstStageが空またはx_endogがない場合はスキップ

    fs = first_stage["x_endog"]
    assert "fStatistic" in fs
    assert fs["fStatistic"] > 0


def test_iv_r2_is_float(client, tables_store):
    """R2がfloatであることを確認"""
    model_stats = _get_output(client, IvPayload().build())["modelStatistics"]
    assert isinstance(model_stats["R2"], float)


# -----------------------------------------------------------
# 標準誤差マッピング検証テスト
# -----------------------------------------------------------


def test_iv_robust_se_matches_linearmodels(client, tables_store):
    """
    robust SE 付き IV の標準誤差が linearmodels (IV2SLS, cov_type='robust')
    の値と一致することを確認。

    旧バグ: LINEARMODELS_COV_TYPE_MAP に "robust" キーが存在しなかったため
    cov_type が 'unadjusted' にフォールバックしていた。
    このテストは旧バグ下では失敗する。
    """
    df = _load_iv_df()
    x_exog_with_const = sm.add_constant(df[["x_exog"]])
    expected = IV2SLS(
        df["y"],
        x_exog_with_const,
        df[["x_endog"]],
        df[["z1", "z2"]],
    ).fit(cov_type="robust")

    payload = IvPayload(se_method="robust").build()
    params = _get_output(client, payload)["parameters"]

    # API params (const/x_exog/x_endog) と linearmodels std_errors が
    # 同順序で一致することを位置ベースで確認
    for i, param in enumerate(params):
        api_se = param["standardError"]
        expected_se = float(expected.std_errors.iloc[i])
        assert abs(api_se - expected_se) < _ABS_TOL, (
            f"IV robust SE [{param['variable']!r}] (iloc={i}): "
            f"API={api_se!r} != linearmodels={expected_se!r}"
        )


def test_iv_robust_se_differs_from_nonrobust(client, tables_store):
    """
    robust SE が nonrobust SE と異なることを確認。

    旧バグ下では "robust" が "unadjusted" にフォールバックするため
    両者が一致してしまい、このテストは失敗する。
    """
    se_nonrobust = [
        p["standardError"]
        for p in _get_output(client, IvPayload(se_method="nonrobust").build())[
            "parameters"
        ]
    ]
    se_robust = [
        p["standardError"]
        for p in _get_output(client, IvPayload(se_method="robust").build())[
            "parameters"
        ]
    ]
    assert se_nonrobust != se_robust, (
        "IV robust SE が nonrobust SE と同一:"
        " LINEARMODELS_COV_TYPE_MAP のマッピングが"
        "正しく機能していない可能性がある"
    )


def test_iv_full_numerical_validation(client, tables_store):
    """
    IV の全統計量が linearmodels (IV2SLS, cov_type='unadjusted') と
    一致することを確認。
    シミュレーションを含まないため許容誤差内の一致が期待される。

    検証内容:
      - parameters (const/x_exog/x_endog):
          coefficient / standardError / tValue / pValue / CI
      - modelStatistics: nObservations, R2
      - diagnostics.wuHausmanTest: statistic, pValue
      - diagnostics.sarganTest: statistic, pValue
          (sargan はプロパティのため model_result.sargan で直接取得)
      - diagnostics.firstStage["x_endog"]:
          fStatistic, pValue
          (OLSResults.f_statistic を使用)
    """
    df = _load_iv_df()
    x_exog_with_const = sm.add_constant(df[["x_exog"]])
    ref = IV2SLS(
        df["y"],
        x_exog_with_const,
        df[["x_endog"]],
        df[["z1", "z2"]],
    ).fit(cov_type="unadjusted")

    output = _get_output(client, IvPayload().build())
    p_map = {p["variable"]: p for p in output["parameters"]}
    ms = output["modelStatistics"]
    diag = output["diagnostics"]
    ci = ref.conf_int()  # columns: "lower" / "upper"

    # --- parameters (const / x_exog / x_endog) ---
    for var in ["const", "x_exog", "x_endog"]:
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
    assert abs(ms["R2"] - float(ref.rsquared)) < _ABS_TOL

    # --- diagnostics.wuHausmanTest ---
    if not isinstance(ref, IVResults):
        pytest.fail(f"Expected IVResults but got {type(ref).__name__}")

    wh = ref.wu_hausman()
    wu = diag["wuHausmanTest"]
    assert abs(wu["statistic"] - float(wh.stat)) < _ABS_TOL
    assert abs(wu["pValue"] - float(wh.pval)) < _ABS_TOL

    # --- diagnostics.sarganTest ---
    # sargan はプロパティ（WaldTestStatistic）であり callable でない
    sg = diag["sarganTest"]
    assert abs(sg["statistic"] - float(ref.sargan.stat)) < _ABS_TOL
    assert abs(sg["pValue"] - float(ref.sargan.pval)) < _ABS_TOL

    # --- diagnostics.firstStage ---
    fs_api = diag["firstStage"]["x_endog"]
    fs_ref = ref.first_stage.individual["x_endog"]
    assert (
        abs(fs_api["fStatistic"] - float(fs_ref.f_statistic.stat)) < _ABS_TOL
    )
    assert abs(fs_api["pValue"] - float(fs_ref.f_statistic.pval)) < _ABS_TOL


# -----------------------------------------------------------
# Panel IV / FEIV
# -----------------------------------------------------------


def test_feiv_success(client, tables_store):
    """FEIV が 200 を返し推定結果を含むことを確認"""
    output = _get_output(client, PanelIvPayload().build())

    assert "parameters" in output
    assert "modelStatistics" in output
    assert len(output["parameters"]) > 0
    assert output["modelStatistics"]["nObservations"] > 0
