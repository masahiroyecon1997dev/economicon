import pytest
from fastapi import status
from fastapi.testclient import TestClient

from economicon.services.data.settings_store import SettingsStore
from main import app


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def settings_manager():
    """SettingsStoreのフィクスチャ"""
    # 設定マネージャーが初期化されていることを確認
    settings_manager = SettingsStore()
    settings_manager.load_settings()
    yield settings_manager  # noqa: PLR0913


def test_get_settings_success(client, settings_manager):
    """正常系テスト: 設定情報を取得"""
    response = client.get("/api/setting/settings")
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    # 必須フィールドの存在確認
    result = response_data["result"]
    assert "osName" in result
    assert "language" in result
    assert "lastOpenedPath" in result
    assert "theme" in result
    assert "encoding" in result
    assert "logPath" in result
    # デフォルト値の確認
    assert result["language"] == "ja"
    assert result["encoding"] == "utf-8"
    assert result["theme"] == "light"


def test_settings_manager_singleton(client, settings_manager):
    """シングルトンパターンのテスト"""
    manager1 = SettingsStore()
    manager2 = SettingsStore()
    assert manager1 is manager2


def test_settings_info_properties(client, settings_manager):
    """設定情報のプロパティアクセステスト"""
    settings_info = settings_manager.get_settings()
    # プロパティが正しく取得できることを確認
    assert settings_info.os_name is not None
    assert settings_info.language == "ja"
    assert settings_info.last_opened_path is not None
    assert settings_info.theme == "light"
    assert settings_info.encoding == "utf-8"
    assert settings_info.log_path is not None


def test_settings_info_to_dict(client, settings_manager):
    """to_dict()メソッドのテスト"""
    settings_info = settings_manager.get_settings()
    settings_dict = settings_info.to_dict()
    # キャメルケースのキーが存在することを確認
    assert "osName" in settings_dict
    assert "language" in settings_dict
    assert "lastOpenedPath" in settings_dict
    assert "theme" in settings_dict
    assert "encoding" in settings_dict
    assert "logPath" in settings_dict
