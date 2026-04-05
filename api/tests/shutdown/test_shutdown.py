import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.services.data.analysis_result import AnalysisResult
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.settings_store import SettingsStore
from main import app


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def settings_manager():
    """SettingsStoreのフィクスチャ"""
    store = SettingsStore()
    store.load_settings()
    return store


@pytest.fixture(autouse=True)
def clear_analysis_results():
    """各テスト前後にAnalysisResultStoreをクリアする"""
    AnalysisResultStore().clear_all()
    yield
    AnalysisResultStore().clear_all()


def test_shutdown_success(client):
    """正常系: POST /api/shutdown が 200 OK を返す"""
    response = client.post("/api/shutdown")
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    assert response_data["result"]["status"] == "ok"


def test_shutdown_clears_analysis_results(client):
    """分析結果ストアのクリア確認: shutdown 後にストアが空になる"""
    store = AnalysisResultStore()
    # ダミーの分析結果を登録
    dummy = AnalysisResult(
        name="test",
        description="test",
        table_name="test_table",
        result_data={"coef": {}},
        result_type="regression",
    )
    store.save_result(dummy)
    assert len(store.get_all_summaries()) == 1

    response = client.post("/api/shutdown")
    assert response.status_code == status.HTTP_200_OK
    assert len(store.get_all_summaries()) == 0


def test_shutdown_saves_settings(client, settings_manager, tmp_path):
    """設定保存確認: shutdown 後に設定の変更がファイルに反映される"""
    # 設定を変更（メモリのみ。save_settings は呼ばない）
    settings_manager.update_settings(language="en")
    assert settings_manager.get_settings().language == "en"

    response = client.post("/api/shutdown")
    assert response.status_code == status.HTTP_200_OK

    # 再ロードしても変更が保持されていることを確認
    settings_manager.reload_settings()
    assert settings_manager.get_settings().language == "en"

    # テスト後に元に戻す
    settings_manager.update_settings(language="ja")
    settings_manager.save_settings()


def test_shutdown_idempotent(client):
    """冪等性: 連続して2回呼んでも正常に動作する"""
    response1 = client.post("/api/shutdown")
    response2 = client.post("/api/shutdown")
    assert response1.status_code == status.HTTP_200_OK
    assert response2.status_code == status.HTTP_200_OK
    assert response1.json()["code"] == "OK"
    assert response2.json()["code"] == "OK"
