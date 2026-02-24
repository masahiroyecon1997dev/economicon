"""操作変数法テスト"""

import pandas as pd
import statsmodels.api as sm
from fastapi import status
from linearmodels.iv import IV2SLS

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import (
    TABLE_IV,
    URL_REGRESSION,
    generate_all_data,
    iv_payload,
)

# 数値比較の許容誤差
_ABS_TOL = 1e-3


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
    resp = client.post(URL_REGRESSION, json=iv_payload())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_iv_response_structure(client, tables_store):
    """regressionOutputにIV専用キーが含まれることを確認"""
    output = _get_output(client, iv_payload())
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
    ).fit(cov_type="unadjusted")

    params = _get_output(client, iv_payload())["parameters"]
    expected_params = model_result.params  # [const, x1, x2_endog]

    for i, (exp_coef, param) in enumerate(
        zip(expected_params, params, strict=False)
    ):
        assert abs(param["coefficient"] - exp_coef) < _ABS_TOL, (
            f"IV params[{i}]: {param['coefficient']!r} != {exp_coef!r}"
        )


def test_iv_endogenous_variables_in_parameters(client, tables_store):
    """内生変数 x2_endog がパラメータに含まれることを確認"""
    params = _get_output(client, iv_payload())["parameters"]
    var_names = [p["variable"] for p in params]
    assert "x2_endog" in var_names


def test_iv_diagnostics_present(client, tables_store):
    """diagnosticsにIV検定統計量が少なくとも1つ含まれることを確認"""
    output = _get_output(client, iv_payload())
    diagnostics = output["diagnostics"]

    has_diag = any(
        key in diagnostics
        for key in ("wuHausmanTest", "sarganTest", "firstStage")
    )
    assert has_diag, "diagnostics にIV検定統計量が含まれない"


def test_iv_first_stage_for_endogenous(client, tables_store):
    """firstStageに内生変数のF統計量が含まれることを確認（存在する場合）"""
    output = _get_output(client, iv_payload())
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
    model_stats = _get_output(client, iv_payload())["modelStatistics"]
    assert isinstance(model_stats["R2"], float)


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
