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


def test_update_metadata_updates_summary_and_detail(
    result_store, sample_result
):
    """update_metadata が名前・説明・要約上書きを更新することを確認"""
    result_id = result_store.save_result(sample_result)

    updated = result_store.update_metadata(
        result_id,
        name="Updated Analysis",
        description="Updated Description",
        summary_text_override="Manual Summary",
    )

    assert updated.id == result_id
    assert updated.name == "Updated Analysis"
    assert updated.description == "Updated Description"
    assert updated.to_summary_dict()["summaryText"] == "Manual Summary"


def test_update_metadata_with_none_summary_override_restores_generated_summary(
    result_store,
):
    """summary_text_override を None にすると自動生成へ戻ることを確認"""
    sample = AnalysisResult(
        name="Generated Summary Test",
        description="Fallback Description",
        table_name="test_table",
        result_type="regression",
        model_type="ols",
        result_data={
            "dependentVariable": "y",
            "explanatoryVariables": ["x1"],
        },
    )
    result_id = result_store.save_result(sample)
    generated_summary = result_store.get_result(result_id).to_summary_dict()[
        "summaryText"
    ]

    result_store.update_metadata(
        result_id,
        summary_text_override="Manual Summary",
    )
    restored = result_store.update_metadata(
        result_id,
        summary_text_override=None,
    )

    assert restored.to_summary_dict()["summaryText"] == generated_summary


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


def test_patch_result_by_id_api_updates_metadata_and_syncs_summary(
    client, tables_store
):
    """PATCH /results/{id} がメタデータを更新し一覧と詳細を同期する"""
    resp_reg = client.post(URL_REGRESSION, json=OlsPayload().build())
    result_id = resp_reg.json()["result"]["resultId"]

    resp_before = client.get(URL_RESULTS)
    summaries_before = resp_before.json()["result"]["results"]
    summary_before = next(s for s in summaries_before if s["id"] == result_id)

    patch_resp = client.patch(
        f"{URL_RESULTS}/{result_id}",
        json={
            "name": "Updated OLS",
            "description": "Updated Description",
            "summaryTextOverride": "Manual Summary",
        },
    )

    assert patch_resp.status_code == status.HTTP_200_OK
    patch_data = patch_resp.json()
    assert patch_data["code"] == "OK"
    assert patch_data["result"]["updatedSummary"]["name"] == "Updated OLS"
    assert (
        patch_data["result"]["updatedSummary"]["description"]
        == "Updated Description"
    )
    assert (
        patch_data["result"]["updatedSummary"]["summaryText"]
        == "Manual Summary"
    )
    assert patch_data["result"]["updatedDetail"]["id"] == result_id
    assert patch_data["result"]["updatedDetail"]["name"] == "Updated OLS"

    resp_after = client.get(URL_RESULTS)
    summaries_after = resp_after.json()["result"]["results"]
    summary_after = next(s for s in summaries_after if s["id"] == result_id)
    assert summary_after["name"] == "Updated OLS"
    assert summary_after["description"] == "Updated Description"
    assert summary_after["summaryText"] == "Manual Summary"

    detail_resp = client.get(f"{URL_RESULTS}/{result_id}")
    detail_data = detail_resp.json()["result"]
    assert detail_data["name"] == "Updated OLS"
    assert detail_data["description"] == "Updated Description"

    reset_resp = client.patch(
        f"{URL_RESULTS}/{result_id}",
        json={"summaryTextOverride": None},
    )
    assert reset_resp.status_code == status.HTTP_200_OK
    reset_data = reset_resp.json()
    assert (
        reset_data["result"]["updatedSummary"]["summaryText"]
        == summary_before["summaryText"]
    )


def test_patch_result_by_id_api_returns_invalid_input_for_empty_body(
    client, tables_store
):
    """PATCH /results/{id} に更新項目なしなら 400 を返す"""
    resp_reg = client.post(URL_REGRESSION, json=OlsPayload().build())
    result_id = resp_reg.json()["result"]["resultId"]

    resp = client.patch(f"{URL_RESULTS}/{result_id}", json={})

    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    data = resp.json()
    assert data["code"] == "INVALID_INPUT"
    assert data["message"] == "At least one field must be provided"


def test_patch_result_by_id_api_returns_invalid_input_for_blank_name(
    client, tables_store
):
    """PATCH /results/{id} に空白 name を送ると 422 を返す"""
    resp_reg = client.post(URL_REGRESSION, json=OlsPayload().build())
    result_id = resp_reg.json()["result"]["resultId"]

    resp = client.patch(
        f"{URL_RESULTS}/{result_id}",
        json={"name": "   "},
    )

    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = resp.json()
    assert data["code"] == "VALIDATION_ERROR"
    assert data["message"] == "Name must not be blank"


# -----------------------------------------------------------
# 存在しない ID へのアクセス (404 Not Found)
# -----------------------------------------------------------

_NONEXISTENT_ID = "00000000-0000-0000-0000-000000000000"


def test_get_result_by_nonexistent_id_returns_404(client, tables_store):
    """GET /results/{id} で存在しない ID は 404 RESULT_NOT_FOUND を返す"""
    resp = client.get(f"{URL_RESULTS}/{_NONEXISTENT_ID}")

    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json()["code"] == "RESULT_NOT_FOUND"


def test_delete_result_by_nonexistent_id_returns_404(client, tables_store):
    """DELETE /results/{id} で存在しない ID は 404 RESULT_NOT_FOUND を返す"""
    resp = client.delete(f"{URL_RESULTS}/{_NONEXISTENT_ID}")

    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json()["code"] == "RESULT_NOT_FOUND"


def test_patch_result_by_nonexistent_id_returns_404(client, tables_store):
    """PATCH /results/{id} で存在しない ID は 404 RESULT_NOT_FOUND を返す"""
    resp = client.patch(
        f"{URL_RESULTS}/{_NONEXISTENT_ID}",
        json={"name": "Updated Name"},
    )

    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json()["code"] == "RESULT_NOT_FOUND"


# -----------------------------------------------------------
# フィールド長バリデーション (422 Unprocessable Entity)
# -----------------------------------------------------------


def test_patch_result_api_returns_422_for_name_too_long(client, tables_store):
    """PATCH /results/{id} の name が 101 文字超なら 422 を返す"""
    resp_reg = client.post(URL_REGRESSION, json=OlsPayload().build())
    result_id = resp_reg.json()["result"]["resultId"]

    resp = client.patch(
        f"{URL_RESULTS}/{result_id}",
        json={"name": "a" * 101},
    )

    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert resp.json()["code"] == "VALIDATION_ERROR"


def test_patch_result_api_returns_422_for_description_too_long(
    client, tables_store
):
    """PATCH /results/{id} の description が 1001 文字超なら 422 を返す"""
    resp_reg = client.post(URL_REGRESSION, json=OlsPayload().build())
    result_id = resp_reg.json()["result"]["resultId"]

    resp = client.patch(
        f"{URL_RESULTS}/{result_id}",
        json={"description": "a" * 1001},
    )

    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert resp.json()["code"] == "VALIDATION_ERROR"


def test_patch_result_api_returns_422_for_summary_text_override_too_long(
    client, tables_store
):
    """PATCH /results/{id} の summaryTextOverride が 201 文字超なら 422"""
    resp_reg = client.post(URL_REGRESSION, json=OlsPayload().build())
    result_id = resp_reg.json()["result"]["resultId"]

    resp = client.patch(
        f"{URL_RESULTS}/{result_id}",
        json={"summaryTextOverride": "a" * 201},
    )

    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert resp.json()["code"] == "VALIDATION_ERROR"
