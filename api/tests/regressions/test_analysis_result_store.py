"""
AnalysisResultStore のテスト
"""

import pytest
from fastapi import status

from economicon.services.data.analysis_result import AnalysisResult
from economicon.services.data.analysis_result_store import AnalysisResultStore
from tests.regressions.conftest import (
    URL_REGRESSION,
    URL_RESULTS,
    OlsPayload,
)

_EXPECTED_R_SQUARED = 0.95
_EXPECTED_RESULT_COUNT = 2


@pytest.fixture
def result_store():
    """テスト用のAnalysisResultStoreインスタンス"""
    store = AnalysisResultStore()
    store.clear_all()
    yield store
    store.clear_all()


@pytest.fixture
def sample_result():
    """テスト用のサンプル分析結果"""
    return AnalysisResult(
        name="Test Analysis",
        description="Test Description",
        table_name="test_table",
        result_data={"coefficients": [1.0, 2.0, 3.0], "r_squared": 0.95},
        result_type="regression",
    )


def test_save_result_returns_id(result_store, sample_result):
    """save_result が ID を返すことを確認"""
    result_id = result_store.save_result(sample_result)
    assert isinstance(result_id, str)
    assert len(result_id) > 0


def test_get_result_returns_saved_result(result_store, sample_result):
    """保存した結果を取得できることを確認"""
    result_id = result_store.save_result(sample_result)
    retrieved = result_store.get_result(result_id)

    assert retrieved.id == result_id
    assert retrieved.name == "Test Analysis"
    assert retrieved.description == "Test Description"
    assert retrieved.table_name == "test_table"
    assert retrieved.result_data["r_squared"] == _EXPECTED_R_SQUARED


def test_get_result_raises_key_error_for_nonexistent_id(result_store):
    """存在しないIDで KeyError が発生することを確認"""
    with pytest.raises(
        KeyError, match="Analysis result with ID 'nonexistent' does not exist."
    ):
        result_store.get_result("nonexistent")


def test_get_all_summaries_returns_list(result_store, sample_result):
    """get_all_summaries がサマリーリストを返すことを確認"""
    result_store.save_result(sample_result)

    sample_result2 = AnalysisResult(
        name="Test Analysis 2",
        description="Test Description 2",
        table_name="test_table_2",
        result_data={"coefficients": [4.0, 5.0]},
        result_type="regression",
    )
    result_store.save_result(sample_result2)

    summaries = result_store.get_all_summaries()

    assert len(summaries) == _EXPECTED_RESULT_COUNT
    # 基本フィールド
    assert all("id" in s for s in summaries)
    assert all("name" in s for s in summaries)
    assert all("description" in s for s in summaries)
    assert all("createdAt" in s for s in summaries)
    # 拡張フィールド
    assert all("tableName" in s for s in summaries)
    assert all("resultType" in s for s in summaries)
    assert all("resultTypeLabel" in s for s in summaries)
    assert all("modelType" in s for s in summaries)
    assert all("summaryText" in s for s in summaries)
    # 値の検証（sample_result の内容）
    first = next(s for s in summaries if s["name"] == "Test Analysis")
    assert first["tableName"] == "test_table"
    assert first["resultType"] == "regression"
    assert first["resultTypeLabel"] == "回帰分析"
    assert first["modelType"] is None
    # result_data に dependentVariable なし → description へフォールバック
    assert first["summaryText"] == "Test Description"


def test_delete_result_removes_result(result_store, sample_result):
    """delete_result が結果を削除することを確認"""
    result_id = result_store.save_result(sample_result)
    deleted_id = result_store.delete_result(result_id)

    assert deleted_id == result_id

    with pytest.raises(KeyError):
        result_store.get_result(result_id)


def test_delete_result_raises_key_error_for_nonexistent_id(result_store):
    """存在しないIDの削除で KeyError が発生することを確認"""
    with pytest.raises(
        KeyError, match="Analysis result with ID 'nonexistent' does not exist."
    ):
        result_store.delete_result("nonexistent")


def test_clear_all_removes_all_results(result_store, sample_result):
    """clear_all がすべての結果を削除することを確認"""
    result_store.save_result(sample_result)

    sample_result2 = AnalysisResult(
        name="Test Analysis 2",
        description="Test Description 2",
        table_name="test_table_2",
        result_data={"coefficients": [4.0, 5.0]},
        result_type="regression",
    )
    result_store.save_result(sample_result2)

    result = result_store.clear_all()
    assert result is True

    summaries = result_store.get_all_summaries()
    assert len(summaries) == 0


def test_singleton_pattern(result_store):
    """シングルトンパターンが正しく動作することを確認"""
    store1 = AnalysisResultStore()
    store2 = AnalysisResultStore()

    assert store1 is store2


# -----------------------------------------------------------
# API ルーターテスト (GET/DELETE 結果エンドポイント)
# -----------------------------------------------------------


def test_get_all_results_api(client, tables_store):
    """GET /results が全結果サマリーを返すことを確認"""
    # OLSの実行で結果を作成
    client.post(URL_REGRESSION, json=OlsPayload().build())

    resp = client.get(URL_RESULTS)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert "results" in data["result"]
    assert isinstance(data["result"]["results"], list)


def test_get_result_by_id_api(client, tables_store):
    """GET /results/{id} が指定結果の詳細を返すことを確認"""
    resp_reg = client.post(URL_REGRESSION, json=OlsPayload().build())
    result_id = resp_reg.json()["result"]["resultId"]

    resp = client.get(f"{URL_RESULTS}/{result_id}")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    result = data["result"]
    assert result["id"] == result_id
    assert "resultData" in result
    assert "createdAt" in result


def test_delete_result_by_id_api(client, tables_store):
    """DELETE /results/{id} が結果を削除し deletedResultId を返すことを確認"""
    resp_reg = client.post(URL_REGRESSION, json=OlsPayload().build())
    result_id = resp_reg.json()["result"]["resultId"]

    resp = client.delete(f"{URL_RESULTS}/{result_id}")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["code"] == "OK"
    assert data["result"]["deletedResultId"] == result_id

    # 削除後は取得不可になる（404 Not Found）
    resp_deleted = client.get(f"{URL_RESULTS}/{result_id}")
    assert resp_deleted.status_code == status.HTTP_404_NOT_FOUND
    body = resp_deleted.json()
    assert body.get("code") == "RESULT_NOT_FOUND"


def test_clear_all_results_api(client, tables_store):
    """DELETE /results が全結果を削除することを確認"""
    client.post(URL_REGRESSION, json=OlsPayload().build())
    client.post(URL_REGRESSION, json=OlsPayload().build())

    resp = client.delete(URL_RESULTS)
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["code"] == "OK"

    # 削除後は空になる
    resp_list = client.get(URL_RESULTS)
    assert resp_list.json()["result"]["results"] == []
