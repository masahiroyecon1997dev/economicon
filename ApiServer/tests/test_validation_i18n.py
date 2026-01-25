"""
Pydantic バリデーションエラー多言語化のテスト
"""

import pytest
from analysisapp.services.data.settings_manager import SettingsManager
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
        app_language='ja',
        encoding=settings.encoding,
        path_separator=settings.path_separator
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
        app_language='ja',
        encoding=settings.encoding,
        path_separator=settings.path_separator
    )
    settings_manager.save_settings()

    # 必須フィールドが欠けているリクエスト
    payload = {
        "type": "ols",
        # tableName が欠けている
        "dependentVariable": "y",
        "explanatoryVariables": ["x1", "x2"]
    }

    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert 'detail' in response_data

    # エラーメッセージが日本語であることを確認
    errors = response_data['detail']
    assert len(errors) > 0

    # 必須フィールドエラーを探す
    field_required_error = None
    for error in errors:
        if 'tableName' in str(error.get('loc', [])):
            field_required_error = error
            break

    assert field_required_error is not None
    # 日本語メッセージが含まれていることを確認
    assert '必須' in field_required_error['msg']


def test_validation_error_missing_field_en(client, settings_manager):
    """必須フィールド欠落エラーが英語で返されることを確認"""
    # 英語設定
    settings = settings_manager.get_settings()
    settings_manager.update_settings(
        os_name=settings.os_name,
        default_folder_path=settings.default_folder_path,
        display_rows=settings.display_rows,
        app_language='en',
        encoding=settings.encoding,
        path_separator=settings.path_separator
    )
    settings_manager.save_settings()

    # 必須フィールドが欠けているリクエスト
    payload = {
        "type": "ols",
        # tableName が欠けている
        "dependentVariable": "y",
        "explanatoryVariables": ["x1", "x2"]
    }

    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert 'detail' in response_data

    # エラーメッセージが英語であることを確認
    errors = response_data['detail']
    assert len(errors) > 0

    # 必須フィールドエラーを探す
    field_required_error = None
    for error in errors:
        if 'tableName' in str(error.get('loc', [])):
            field_required_error = error
            break

    assert field_required_error is not None
    # 英語メッセージが含まれていることを確認
    assert 'required' in field_required_error['msg'].lower()


def test_validation_error_invalid_type_ja(client, settings_manager):
    """型エラーが日本語で返されることを確認"""
    # 日本語設定
    settings = settings_manager.get_settings()
    settings_manager.update_settings(
        os_name=settings.os_name,
        default_folder_path=settings.default_folder_path,
        display_rows=settings.display_rows,
        app_language='ja',
        encoding=settings.encoding,
        path_separator=settings.path_separator
    )
    settings_manager.save_settings()

    # 型が間違っているリクエスト
    payload = {
        "type": "ols",
        "tableName": "test_table",
        "dependentVariable": "y",
        "explanatoryVariables": "x1"  # リストであるべきが文字列
    }

    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert 'detail' in response_data

    # エラーメッセージに日本語が含まれていることを確認
    errors = response_data['detail']
    assert len(errors) > 0

    # 型エラーを探す
    type_error = None
    for error in errors:
        if 'explanatoryVariables' in str(error.get('loc', [])):
            type_error = error
            break

    assert type_error is not None
    # 日本語メッセージであることを確認（リストまたはリスト型が含まれる）
    assert 'リスト' in type_error['msg']


def test_validation_error_invalid_enum_ja(client, settings_manager):
    """列挙型エラーが日本語で返されることを確認"""
    # 日本語設定
    settings = settings_manager.get_settings()
    settings_manager.update_settings(
        os_name=settings.os_name,
        default_folder_path=settings.default_folder_path,
        display_rows=settings.display_rows,
        app_language='ja',
        encoding=settings.encoding,
        path_separator=settings.path_separator
    )
    settings_manager.save_settings()

    # 無効な列挙値
    payload = {
        "type": "invalid_type",  # 無効な分析タイプ
        "tableName": "test_table",
        "dependentVariable": "y",
        "explanatoryVariables": ["x1", "x2"]
    }

    response = client.post('/api/analysis/regression', json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert 'detail' in response_data

    # エラーメッセージが返されることを確認
    errors = response_data['detail']
    assert len(errors) > 0
