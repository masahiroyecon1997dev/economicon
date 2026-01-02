import pytest
from fastapi.testclient import TestClient
from fastapi import status

from main import app
from analysisapp.api.services.data.tables_manager import TablesManager


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_manager():
    """TablesManagerのフィクスチャ"""
        # 設定マネージャーが初期化されていることを確認
        self.settings_manager = SettingsManager()
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()



def test_get_settings_success(client, tables_manager):
    # 正常系テスト: 設定情報を取得
    response = client.get(
        '/api/get-settings',
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    # 必須フィールドの存在確認
    result = response_data['result']
    assert 'osName' in result
    assert 'defaultFolderPath' in result
    assert 'displayRows' in result
    assert 'appLanguage' in result
    assert 'encoding' in result
    assert 'pathSeparator' in result
    # デフォルト値の確認
    assert result['displayRows'] == 100
    assert result['appLanguage'] == 'ja'
    assert result['encoding'] == 'utf-8'
    assert result['pathSeparator'] == '/'


def test_settings_manager_singleton(client, tables_manager):
    # シングルトンパターンのテスト
    manager1 = SettingsManager()
    manager2 = SettingsManager()
    self.assertIs(manager1, manager2)


def test_settings_info_properties(client, tables_manager):
    # 設定情報のプロパティアクセステスト
    settings_info = self.settings_manager.get_settings()
    # プロパティが正しく取得できることを確認
    self.assertIsNotNone(settings_info.os_name)
    self.assertIsNotNone(settings_info.default_folder_path)
    assert settings_info.display_rows == 100
    assert settings_info.app_language == 'ja'
    assert settings_info.encoding == 'utf-8'
    assert settings_info.path_separator == '/'


def test_settings_info_to_dict(client, tables_manager):
    # to_dict()メソッドのテスト
    settings_info = self.settings_manager.get_settings()
    settings_dict = settings_info.to_dict()
    # キャメルケースのキーが存在することを確認
    assert 'osName' in settings_dict
    assert 'defaultFolderPath' in settings_dict
    assert 'displayRows' in settings_dict
    assert 'appLanguage' in settings_dict
    assert 'encoding' in settings_dict
    assert 'pathSeparator' in settings_dict
