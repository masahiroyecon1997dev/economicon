"""FGLS回帰テスト"""

from fastapi import status

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import URL_REGRESSION, FglsPayload

_ABS_TOL = 1e-12
_N_PARAMS_WITH_CONST = 4


def _get_output(client, payload: dict) -> dict:
    """POSTして result_data を返すヘルパー"""
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).result_data


def test_fgls_heteroskedastic_success(client, tables_store):
    """heteroskedastic FGLS が200を返すことを確認"""
    resp = client.post(
        URL_REGRESSION,
        json=FglsPayload(fgls_method="heteroskedastic").build(),
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_fgls_ar1_success(client, tables_store):
    """AR(1) FGLS が200を返すことを確認"""
    output = _get_output(client, FglsPayload(fgls_method="ar1").build())
    assert len(output["parameters"]) == _N_PARAMS_WITH_CONST


def test_fgls_response_structure(client, tables_store):
    """FGLS の result_data に必須キーが含まれることを確認"""
    output = _get_output(client, FglsPayload().build())
    assert "parameters" in output
    assert "modelStatistics" in output
    assert len(output["parameters"]) == _N_PARAMS_WITH_CONST


def test_fgls_default_matches_heteroskedastic(client, tables_store):
    """デフォルト FGLS が heteroskedastic と一致することを確認"""
    default_params = _get_output(client, FglsPayload().build())["parameters"]
    hetero_params = _get_output(
        client,
        FglsPayload(fgls_method="heteroskedastic").build(),
    )["parameters"]

    default_map = {p["variable"]: p["coefficient"] for p in default_params}
    hetero_map = {p["variable"]: p["coefficient"] for p in hetero_params}

    for var, exp_coef in hetero_map.items():
        assert abs(default_map[var] - exp_coef) < _ABS_TOL, (
            f"{var}: default={default_map[var]!r}, hetero={exp_coef!r}"
        )


def test_fgls_ar1_low_max_iter_still_returns_result(client, tables_store):
    """AR(1) で maxIter=1 でも結果が返ることを確認"""
    output = _get_output(
        client,
        FglsPayload(fgls_method="ar1", max_iter=1).build(),
    )
    assert len(output["parameters"]) == _N_PARAMS_WITH_CONST


def test_fgls_coefficient_signs(client, tables_store):
    """基本データ上で x1 は正、x2 は負の係数を返すことを確認"""
    params = _get_output(client, FglsPayload().build())["parameters"]
    coef_map = {p["variable"]: p["coefficient"] for p in params}

    assert coef_map["x1"] > 0.0
    assert coef_map["x2"] < 0.0


def test_fgls_robust_request_success(client, tables_store):
    """robust 標準誤差でも FGLS が成功することを確認"""
    output = _get_output(client, FglsPayload(se_method="robust").build())
    assert len(output["parameters"]) == _N_PARAMS_WITH_CONST
