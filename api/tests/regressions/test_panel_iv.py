"""Panel IV回帰テスト"""

from fastapi import status

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import URL_REGRESSION, PanelIvPayload

_N_MIN_PARAMS = 2


def _get_output(client, payload: dict) -> dict:
    """POSTして result_data を返すヘルパー"""
    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).result_data


def test_panel_iv_success(client, tables_store):
    """PanelIV が200を返し resultId を含むことを確認"""
    resp = client.post(URL_REGRESSION, json=PanelIvPayload().build())
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "resultId" in data["result"]


def test_panel_iv_response_structure(client, tables_store):
    """PanelIV の result_data に必須キーが含まれることを確認"""
    output = _get_output(client, PanelIvPayload().build())

    assert "parameters" in output
    assert "modelStatistics" in output
    assert "diagnostics" in output
    assert len(output["parameters"]) >= _N_MIN_PARAMS


def test_panel_iv_diagnostics_present(client, tables_store):
    """診断統計量が返ることを確認"""
    diagnostics = _get_output(client, PanelIvPayload().build())["diagnostics"]

    assert "fPooled" in diagnostics
    assert "firstStage" in diagnostics


def test_panel_iv_identification_error(client, tables_store):
    """操作変数数が内生変数数より少ないと 422 を返す"""
    payload = PanelIvPayload(
        endog=["x2", "z1"],
        instruments=["z2"],
    ).build()

    resp = client.post(URL_REGRESSION, json=payload)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    data = resp.json()
    assert data["message"] == (
        "Number of instrumental variables (1)"
        " must be >= endogenous variables (2)."
    )


def test_panel_iv_time_column_optional(client, tables_store):
    """timeColumn を省略しても PanelIV が動作することを確認"""
    output = _get_output(client, PanelIvPayload(time_col=None).build())
    assert output["modelStatistics"]["nObservations"] > 0


def test_panel_iv_cluster_se_success(client, tables_store):
    """entity_id で cluster 標準誤差を指定しても成功することを確認"""
    payload = PanelIvPayload().build()
    payload["standardError"] = {
        "method": "cluster",
        "groups": ["entity_id"],
    }

    output = _get_output(client, payload)
    assert len(output["parameters"]) >= _N_MIN_PARAMS
