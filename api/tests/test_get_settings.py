import pytest
from economicon.services.data.settings_manager import SettingsManager
from fastapi import status
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def settings_manager():
    """SettingsManagerのフィクスチャ"""
    # 設定マネージャーが初期化されていることを確認
    settings_manager = SettingsManager()
    settings_manager.load_settings()
    yield settings_manager


def test_get_settings_success(client, settings_manager):
    """正常系テスト: 設定情報を取得"""
    response = client.get("/api/setting/get-settings")
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data["code"] == "OK"
    # 必須フィールドの存在確認
    result = response_data["result"]
    assert "osName" in result
    assert "defaultFolderPath" in result
    assert "displayRows" in result
    assert "appLanguage" in result
    assert "encoding" in result
    assert "pathSeparator" in result
    # デフォルト値の確認
    assert result["displayRows"] == 100
    assert result["appLanguage"] == "ja"
    assert result["encoding"] == "utf-8"
    assert result["pathSeparator"] == "/"


def test_settings_manager_singleton(client, settings_manager):
    """シングルトンパターンのテスト"""
    manager1 = SettingsManager()
    manager2 = SettingsManager()
    assert manager1 is manager2


def test_settings_info_properties(client, settings_manager):
    """設定情報のプロパティアクセステスト"""
    settings_info = settings_manager.get_settings()
    # プロパティが正しく取得できることを確認
    assert settings_info.os_name is not None
    assert settings_info.default_folder_path is not None
    assert settings_info.display_rows == 100
    assert settings_info.app_language == "ja"
    assert settings_info.encoding == "utf-8"
    assert settings_info.path_separator == "/"


def test_settings_info_to_dict(client, settings_manager):
    """to_dict()メソッドのテスト"""
    settings_info = settings_manager.get_settings()
    settings_dict = settings_info.to_dict()
    # キャメルケースのキーが存在することを確認
    assert "osName" in settings_dict
    assert "defaultFolderPath" in settings_dict
    assert "displayRows" in settings_dict
    assert "appLanguage" in settings_dict
    assert "encoding" in settings_dict
    assert "pathSeparator" in settings_dict
