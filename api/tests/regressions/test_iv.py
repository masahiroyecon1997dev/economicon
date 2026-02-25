"""操作変数法テスト"""

import pandas as pd
import statsmodels.api as sm
from fastapi import status
from linearmodels.iv import IV2SLS

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import (
    TABLE_IV,
    URL_REGRESSION,
    IvPayload,
    generate_all_data,
)

# 数値比較の許容誤差
_ABS_TOL = 1e-12


def _get_output(client, payload):
    """POSTして regressionOutput を返すヘルパー"""
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).regression_output


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
    """IV係数がlinearmodels (IV2SLS) と一致することを確認"""
    _, _, iv = generate_all_data()
    x1_iv, x2_endog, z1, z2, y_iv = iv

    df = pd.DataFrame(
        {
            "y": y_iv,
            "x1": x1_iv,
            "x2_endog": x2_endog,
            "z1": z1,
            "z2": z2,
        }
    )

    # IV2SLS: dependent=y, exog=[const, x1], endog=[x2_endog], instr=[z1, z2]
    x_exog = sm.add_constant(df[["x1"]])
    model_result = IV2SLS(
        df["y"],
        x_exog,
        df[["x2_endog"]],
        df[["z1", "z2"]],
    ).fit(cov_type="unadjusted")  # nonrobust → unadjusted

    params = _get_output(client, IvPayload().build())["parameters"]
    expected_params = model_result.params  # [const, x1, x2_endog]

    for i, (exp_coef, param) in enumerate(
        zip(expected_params, params, strict=False)
    ):
        assert abs(param["coefficient"] - exp_coef) < _ABS_TOL, (
            f"IV params[{i}]: {param['coefficient']!r} != {exp_coef!r}"
        )


def test_iv_endogenous_variables_in_parameters(client, tables_store):
    """内生変数 x2_endog がパラメータに含まれることを確認"""
    params = _get_output(client, IvPayload().build())["parameters"]
    var_names = [p["variable"] for p in params]
    assert "x2_endog" in var_names


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
    if not first_stage or "x2_endog" not in first_stage:
        return  # firstStageが空またはx2_endogがない場合はスキップ

    fs = first_stage["x2_endog"]
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

    注意: _iv_format_result は param_names に const を含めないため、
    API が返す SE[0], SE[1] は linearmodels の std_errors.iloc[0], iloc[1]
    (iloc順: const, x1) に対応する。名前ではなく位置ベースで比較する。

    旧バグ: LINEARMODELS_COV_TYPE_MAP に "robust" キーが存在しなかったため
    cov_type が 'unadjusted' にフォールバックしていた。
    このテストは旧バグ下では失敗する。
    """
    _, _, iv = generate_all_data()
    x1_iv, x2_endog, z1, z2, y_iv = iv

    df = pd.DataFrame(
        {
            "y": y_iv,
            "x1": x1_iv,
            "x2_endog": x2_endog,
            "z1": z1,
            "z2": z2,
        }
    )
    x_exog = sm.add_constant(df[["x1"]])
    expected = IV2SLS(
        df["y"],
        x_exog,
        df[["x2_endog"]],
        df[["z1", "z2"]],
    ).fit(cov_type="robust")

    payload = IvPayload(se_method="robust").build()
    params = _get_output(client, payload)["parameters"]

    # API params (len=2) は linearmodels std_errors (len=3, const 含む) の
    # iloc[0], iloc[1] に対応
    # （_iv_format_result の param_names が const を省く挙動）
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
      - parameters (const/x1/x2_endog):
          coefficient / standardError / tValue / pValue / CI
      - modelStatistics: nObservations, R2
      - diagnostics.wuHausmanTest: statistic, pValue
      - diagnostics.sarganTest: statistic, pValue
          (sargan はプロパティのため model_result.sargan で直接取得)
      - diagnostics.firstStage["x2_endog"]:
          fStatistic, pValue
          (OLSResults.f_statistic を使用)
    """
    _, _, iv = generate_all_data()
    x1_iv, x2_endog, z1, z2, y_iv = iv

    df = pd.DataFrame(
        {
            "y": y_iv,
            "x1": x1_iv,
            "x2_endog": x2_endog,
            "z1": z1,
            "z2": z2,
        }
    )
    x_exog = sm.add_constant(df[["x1"]])
    ref = IV2SLS(
        df["y"],
        x_exog,
        df[["x2_endog"]],
        df[["z1", "z2"]],
    ).fit(cov_type="unadjusted")

    output = _get_output(client, IvPayload().build())
    p_map = {p["variable"]: p for p in output["parameters"]}
    ms = output["modelStatistics"]
    diag = output["diagnostics"]
    ci = ref.conf_int()  # columns: "lower" / "upper"

    # --- parameters (const / x1 / x2_endog) ---
    for var in ["const", "x1", "x2_endog"]:
        p = p_map[var]
        ci_lower = float(ci.loc[var, "lower"])
        ci_upper = float(ci.loc[var, "upper"])
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
    fs_api = diag["firstStage"]["x2_endog"]
    fs_ref = ref.first_stage.individual["x2_endog"]
    assert (
        abs(fs_api["fStatistic"] - float(fs_ref.f_statistic.stat)) < _ABS_TOL
    )
    assert abs(fs_api["pValue"] - float(fs_ref.f_statistic.pval)) < _ABS_TOL


# -----------------------------------------------------------
# FEIVは未実装
# -----------------------------------------------------------


def test_feiv_not_implemented(client, tables_store):
    """FEIVが 500 (REGRESSION_PROCESS_ERROR) を返すことを確認"""
    payload = {
        "tableName": TABLE_IV,
        "dependentVariable": "y",
        "explanatoryVariables": ["x1"],
        "analysis": {
            "method": "feiv",
            "entity_id_column": "x1",
            "endogenous_variables": ["x2_endog"],
            "instrumental_variables": ["z1", "z2"],
        },
        "standardError": {"method": "nonrobust"},
    }
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = resp.json()
    assert "FEIV" in data["message"] or "not" in data["message"].lower()
