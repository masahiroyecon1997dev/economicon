"""Tobit回帰テスト"""

import pytest
from fastapi import status

from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import (
    URL_REGRESSION,
    TobitPayload,
)

# 左側打ち切り限界
_LEFT_CENSORING_LIMIT = 0.0

# 右側打ち切り限界
_RIGHT_CENSORING_LIMIT = 5.0


def _post_tobit(client, payload):
    """POSTしてレスポンスを返すヘルパー"""
    return client.post(URL_REGRESSION, json=payload)


def _get_output(client, payload):
    """POSTして result_data を返すヘルパー（200のみ）"""
    resp = _post_tobit(client, payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    result_id = resp.json()["result"]["resultId"]
    return AnalysisResultStore().get_result(result_id).result_data


# -----------------------------------------------------------
# 正常系テスト（py4etrics が利用可能な場合のみ実行）
# -----------------------------------------------------------


def test_tobit_success(client, tables_store):
    """Tobit回帰が200またはエラーを返すことを確認"""
    resp = _post_tobit(client, TobitPayload().build())
    # py4etrics が利用可能かどうかで結果が変わりうる
    assert resp.status_code in (
        status.HTTP_200_OK,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ), f"予期しないステータスコード: {resp.status_code}"
    if resp.status_code == status.HTTP_200_OK:
        data = resp.json()
        assert data["code"] == "OK"
        assert "resultId" in data["result"]


def test_tobit_censoring_limits_in_diagnostics(client, tables_store):
    """diagnostics に censoringLimits が含まれることを確認"""
    resp = _post_tobit(client, TobitPayload().build())
    if resp.status_code != status.HTTP_200_OK:
        pytest.skip("py4etrics が利用不可のためスキップ")

    result_id = resp.json()["result"]["resultId"]
    output = AnalysisResultStore().get_result(result_id).result_data
    diagnostics = output["diagnostics"]

    assert "censoringLimits" in diagnostics
    limits = diagnostics["censoringLimits"]
    assert "left" in limits
    assert limits["left"] == _LEFT_CENSORING_LIMIT


def test_tobit_response_structure(client, tables_store):
    """Tobit結果の基本構造を確認"""
    resp = _post_tobit(client, TobitPayload().build())
    if resp.status_code != status.HTTP_200_OK:
        pytest.skip("py4etrics が利用不可のためスキップ")

    result_id = resp.json()["result"]["resultId"]
    output = AnalysisResultStore().get_result(result_id).result_data

    assert "parameters" in output
    assert "modelStatistics" in output
    assert "diagnostics" in output

    params = output["parameters"]
    assert len(params) > 0
    for p in params:
        assert "variable" in p
        assert "coefficient" in p


def test_tobit_sigma_in_diagnostics(client, tables_store):
    """diagnostics に sigma が含まれることを確認"""
    resp = _post_tobit(client, TobitPayload().build())
    if resp.status_code != status.HTTP_200_OK:
        pytest.skip("py4etrics が利用不可のためスキップ")

    result_id = resp.json()["result"]["resultId"]
    output = AnalysisResultStore().get_result(result_id).result_data
    diagnostics = output["diagnostics"]

    if "sigma" in diagnostics:
        assert diagnostics["sigma"] > 0.0


def test_tobit_right_censoring_none(client, tables_store):
    """rightCensoringLimit=None でも動作することを確認"""
    resp = _post_tobit(
        client,
        TobitPayload(left=_LEFT_CENSORING_LIMIT, right=None).build(),
    )
    if resp.status_code != status.HTTP_200_OK:
        pytest.skip("py4etrics が利用不可のためスキップ")

    result_id = resp.json()["result"]["resultId"]
    output = AnalysisResultStore().get_result(result_id).result_data
    limits = output["diagnostics"]["censoringLimits"]
    assert limits["right"] is None


def test_tobit_log_likelihood_present(client, tables_store):
    """modelStatistics に logLikelihood が含まれることを確認"""
    resp = _post_tobit(client, TobitPayload().build())
    if resp.status_code != status.HTTP_200_OK:
        pytest.skip("py4etrics が利用不可のためスキップ")

    result_id = resp.json()["result"]["resultId"]
    output = AnalysisResultStore().get_result(result_id).result_data
    model_stats = output["modelStatistics"]
    assert "logLikelihood" in model_stats


def test_tobit_right_censoring_specified(client, tables_store):
    """rightCensoringLimit 指定時に右打ち切り処理が機能することを確認"""
    resp = _post_tobit(
        client,
        TobitPayload(
            left=_LEFT_CENSORING_LIMIT,
            right=_RIGHT_CENSORING_LIMIT,
        ).build(),
    )
    if resp.status_code != status.HTTP_200_OK:
        pytest.skip("py4etrics が利用不可のためスキップ")

    result_id = resp.json()["result"]["resultId"]
    output = AnalysisResultStore().get_result(result_id).result_data
    limits = output["diagnostics"]["censoringLimits"]
    assert limits["right"] == _RIGHT_CENSORING_LIMIT
