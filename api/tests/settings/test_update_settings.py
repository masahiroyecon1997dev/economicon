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
    store = SettingsStore()
    store.load_settings()
    return store


def test_update_settings_language(client, settings_manager):
    """正常系: language を 'en' に更新できる"""
    response = client.put("/api/settings", json={"language": "en"})
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert "en" == response_data["result"]["language"]
    # 設定ストアにも反映されていること
    assert "en" == settings_manager.get_settings().language
    # 他のフィールドは変わっていないこと
    assert "light" == response_data["result"]["theme"]

    # テスト後に元に戻す
    settings_manager.update_settings(language="ja")
    settings_manager.save_settings()


def test_update_settings_theme(client, settings_manager):
    """正常系: theme を 'dark' に更新できる"""
    response = client.put("/api/settings", json={"theme": "dark"})
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert "dark" == response_data["result"]["theme"]
    assert "dark" == settings_manager.get_settings().theme

    # テスト後に元に戻す
    settings_manager.update_settings(theme="light")
    settings_manager.save_settings()


def test_update_settings_encoding(client, settings_manager):
    """正常系: encoding を 'shift_jis' に更新できる"""
    response = client.put("/api/settings", json={"encoding": "shift_jis"})
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert "shift_jis" == response_data["result"]["encoding"]
    assert "shift_jis" == settings_manager.get_settings().encoding

    # テスト後に元に戻す
    settings_manager.update_settings(encoding="utf-8")
    settings_manager.save_settings()


def test_update_settings_multiple_fields(client, settings_manager):
    """正常系: 複数フィールドを同時に更新できる"""
    response = client.put(
        "/api/settings", json={"language": "en", "theme": "dark"}
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    assert "en" == response_data["result"]["language"]
    assert "dark" == response_data["result"]["theme"]

    # テスト後に元に戻す
    settings_manager.update_settings(language="ja", theme="light")
    settings_manager.save_settings()


def test_update_settings_empty_body(client, settings_manager):
    """正常系: 空ボディでリクエストしても現在の設定が返る"""
    before = settings_manager.get_settings()
    response = client.put("/api/settings", json={})
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "OK" == response_data["code"]
    # 何も変わっていないこと
    assert before.language == response_data["result"]["language"]
    assert before.theme == response_data["result"]["theme"]
    assert before.encoding == response_data["result"]["encoding"]


def test_update_settings_response_has_all_fields(client, settings_manager):
    """正常系: レスポンスに全フィールドが含まれる"""
    response = client.put("/api/settings", json={"language": "ja"})
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    result = response_data["result"]
    assert "language" in result
    assert "lastOpenedPath" in result
    assert "theme" in result
    assert "encoding" in result
    assert "logPath" in result


def test_update_settings_invalid_language(client, settings_manager):
    """異常系: 不正な language 値（pattern 制約）は 422 を返す"""
    response = client.put("/api/settings", json={"language": "fr"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_update_settings_invalid_theme(client, settings_manager):
    """異常系: 不正な theme 値（pattern 制約）は 422 を返す"""
    response = client.put("/api/settings", json={"theme": "blue"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
