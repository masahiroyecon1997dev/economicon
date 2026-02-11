"""
Pydantic バリデーションエラー多言語化のテスト
"""

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
    manager = SettingsManager()
    manager.load_settings()
    # デフォルトで日本語に設定
    settings = manager.get_settings()
    manager.update_settings(
        os_name=settings.os_name,
        default_folder_path=settings.default_folder_path,
        display_rows=settings.display_rows,
        app_language="ja",
        encoding=settings.encoding,
        path_separator=settings.path_separator,
    )
    manager.save_settings()
    yield manager


def test_validation_error_missing_field_ja(client, settings_manager):
    """必須フィールド欠落エラーが日本語で返されることを確認"""
    # 日本語設定
    settings = settings_manager.get_settings()
    settings_manager.update_settings(
        os_name=settings.os_name,
        default_folder_path=settings.default_folder_path,
        display_rows=settings.display_rows,
        app_language="ja",
        encoding=settings.encoding,
        path_separator=settings.path_separator,
    )
    settings_manager.save_settings()

    # 必須フィールドが欠けているリクエスト
    payload = {
        "type": "ols",
        # tableName が欠けている
        "dependentVariable": "y",
        "explanatoryVariables": ["x1", "x2"],
    }

    response = client.post("/api/analysis/regression", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert "code" in response_data
    assert response_data["code"] == "NG"
    assert "message" in response_data

    # エラーメッセージが文字列であることを確認
    message = response_data["message"]
    assert isinstance(message, str)
    assert len(message) > 0

    # 日本語メッセージが含まれていることを確認
    # "tableName は必須です" のようなメッセージを期待
    assert "tableName" in message and "必須" in message, (
        f"Expected Japanese error message, got: {message}"
    )


def test_validation_error_missing_field_en(client, settings_manager):
    """必須フィールド欠落エラーが英語で返されることを確認"""
    # 英語設定
    settings = settings_manager.get_settings()
    settings_manager.update_settings(
        os_name=settings.os_name,
        default_folder_path=settings.default_folder_path,
        display_rows=settings.display_rows,
        app_language="en",
        encoding=settings.encoding,
        path_separator=settings.path_separator,
    )
    settings_manager.save_settings()

    # 必須フィールドが欠けているリクエスト
    payload = {
        "type": "ols",
        # tableName が欠けている
        "dependentVariable": "y",
        "explanatoryVariables": ["x1", "x2"],
    }

    response = client.post("/api/analysis/regression", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    response_data = response.json()
    assert "code" in response_data
    assert response_data["code"] == "NG"
    assert "message" in response_data

    # エラーメッセージが文字列であることを確認
    message = response_data["message"]
    assert isinstance(message, str)
    assert len(message) > 0

    # 英語メッセージが含まれていることを確認
    # "tableName is required" のようなメッセージを期待
    assert "tableName" in message and "required" in message, (
        f"Expected English error message, got: {message}"
    )


def test_validation_error_invalid_type_ja(client, settings_manager):
    """型エラーが日本語で返されることを確認"""
    # 日本語設定
    settings = settings_manager.get_settings()
    settings_manager.update_settings(
        os_name=settings.os_name,
        default_folder_path=settings.default_folder_path,
        display_rows=settings.display_rows,
        app_language="ja",
        encoding=settings.encoding,
        path_separator=settings.path_separator,
    )
    settings_manager.save_settings()

    # 型が間違っているリクエスト
    payload = {
        "type": "ols",
        "tableName": "test_table",
        "dependentVariable": "y",
        "explanatoryVariables": "x1",  # リストであるべきが文字列
    }

    response = client.post("/api/analysis/regression", json=payload)
    response_data = response.json()

    assert "code" in response_data
    assert response_data["code"] == "NG"
    assert "message" in response_data

    # エラーメッセージが文字列であることを確認
    message = response_data["message"]
    assert isinstance(message, str)
    assert len(message) > 0

    # 日本語メッセージが含まれていることを確認
    # "explanatoryVariables はリストである必要があります" のようなメッセージを期待
    assert "explanatoryVariables" in message and "リスト" in message, (
        f"Expected Japanese type error message, got: {message}"
    )


def test_validation_error_invalid_enum_ja(client, settings_manager):
    """列挙型エラーが日本語で返されることを確認"""
    # 日本語設定
    settings = settings_manager.get_settings()
    settings_manager.update_settings(
        os_name=settings.os_name,
        default_folder_path=settings.default_folder_path,
        display_rows=settings.display_rows,
        app_language="ja",
        encoding=settings.encoding,
        path_separator=settings.path_separator,
    )
    settings_manager.save_settings()

    # 無効な列挙値
    payload = {
        "type": "invalid_type",  # 無効な分析タイプ
        "tableName": "test_table",
        "dependentVariable": "y",
        "explanatoryVariables": ["x1", "x2"],
    }

    response = client.post("/api/analysis/regression", json=payload)
    response_data = response.json()
    assert "code" in response_data
    assert response_data["code"] == "NG"
    assert "message" in response_data

    # エラーメッセージが文字列であることを確認
    message = response_data["message"]
    assert isinstance(message, str)
    assert len(message) > 0

    # 日本語でエラーメッセージが返されることを確認
    # "type は次のいずれかである必要があります" のようなメッセージを期待
    assert "type" in message, (
        f"Expected error message about 'type', got: {message}"
    )
