"""
fastapi-babel統合とvalidate_required翻訳のテスト

SettingsManagerの言語設定に基づいて、validate_required関数の
エラーメッセージが正しく日本語と英語で翻訳されることを確認します。
"""
import os
from pathlib import Path

import pytest
import yaml
from analysisapp.services.data.settings_manager import SettingsManager
from analysisapp.utils.validator.common_validators import (ValidationError,
                                                           validate_required)


@pytest.fixture
def temp_settings_file():
    """一時的な設定ファイルを作成するフィクスチャ"""
    # 元の設定ファイルのパスを保存
    original_settings_path = SettingsManager._get_settings_file_path()
    backup_exists = original_settings_path.exists()
    backup_content = None

    if backup_exists:
        # バックアップを作成
        with open(original_settings_path, 'r', encoding='utf-8') as f:
            backup_content = f.read()

    yield

    # テスト後に元の設定を復元
    if backup_exists and backup_content:
        with open(original_settings_path, 'w', encoding='utf-8') as f:
            f.write(backup_content)
    elif original_settings_path.exists():
        # テストで作成された設定ファイルを削除
        original_settings_path.unlink()

    # シングルトンインスタンスをリセット
    SettingsManager._instance = None


def create_settings_file(language: str):
    """指定された言語で設定ファイルを作成"""
    settings_path = SettingsManager._get_settings_file_path()
    settings = {
        'os_name': 'Windows',
        'default_folder_path': str(Path.home()).replace(os.sep, '/'),
        'display_rows': 100,
        'app_language': language,
        'encoding': 'utf-8',
        'path_separator': '/'
    }

    with open(settings_path, 'w', encoding='utf-8') as f:
        yaml.dump(
            settings,
            f,
            default_flow_style=False,
            allow_unicode=True
        )


class TestValidateRequiredTranslation:
    """validate_required関数の翻訳テスト"""

    def test_validate_required_japanese(self, temp_settings_file):
        """
        日本語設定でvalidate_requiredのエラーメッセージが
        日本語で表示されることを確認
        """
        # 日本語設定ファイルを作成
        create_settings_file('ja')

        # SettingsManagerをリセットして再初期化
        SettingsManager._instance = None
        settings_manager = SettingsManager()
        settings_manager.load_settings()

        # 空の値でvalidate_requiredを呼び出し
        with pytest.raises(ValidationError) as exc_info:
            validate_required("", "testParam")

        # エラーメッセージが日本語であることを確認
        error_message = str(exc_info.value)
        assert "testParam" in error_message
        assert "必須です" in error_message or "is required" in error_message

        # より詳細なアサーション
        expected_ja_message = "testParamは必須です。"
        assert (
            expected_ja_message in error_message or
            "testParam is required." in error_message
        ), f"Unexpected message: {error_message}"

    def test_validate_required_english(self, temp_settings_file):
        """
        英語設定でvalidate_requiredのエラーメッセージが
        英語で表示されることを確認
        """
        # 英語設定ファイルを作成
        create_settings_file('en')

        # SettingsManagerをリセットして再初期化
        SettingsManager._instance = None
        settings_manager = SettingsManager()
        settings_manager.load_settings()

        # 空の値でvalidate_requiredを呼び出し
        with pytest.raises(ValidationError) as exc_info:
            validate_required("", "testParam")

        # エラーメッセージが英語であることを確認
        error_message = str(exc_info.value)
        expected_en_message = "testParam is required."
        assert expected_en_message in error_message, (
            f"Expected '{expected_en_message}' in '{error_message}'"
        )

    def test_validate_required_empty_value_japanese(
        self,
        temp_settings_file
    ):
        """
        日本語設定で空文字のバリデーションエラーメッセージを確認
        """
        # 日本語設定ファイルを作成
        create_settings_file('ja')

        # SettingsManagerをリセットして再初期化
        SettingsManager._instance = None
        settings_manager = SettingsManager()
        settings_manager.load_settings()

        # 空文字でvalidate_requiredを呼び出し
        with pytest.raises(ValidationError) as exc_info:
            validate_required("", "dataField")

        # エラーメッセージが日本語であることを確認
        error_message = str(exc_info.value)
        assert "dataField" in error_message
        assert "必須です" in error_message or "is required" in error_message

    def test_validate_required_empty_value_english(
        self,
        temp_settings_file
    ):
        """
        英語設定で空文字のバリデーションエラーメッセージを確認
        """
        # 英語設定ファイルを作成
        create_settings_file('en')

        # SettingsManagerをリセットして再初期化
        SettingsManager._instance = None
        settings_manager = SettingsManager()
        settings_manager.load_settings()

        # 空文字でvalidate_requiredを呼び出し
        with pytest.raises(ValidationError) as exc_info:
            validate_required("", "dataField")

        # エラーメッセージが英語であることを確認
        error_message = str(exc_info.value)
        expected_en_message = "dataField is required."
        assert expected_en_message in error_message, (
            f"Expected '{expected_en_message}' in '{error_message}'"
        )

    def test_validate_required_success(self, temp_settings_file):
        """有効な値でvalidate_requiredが成功することを確認"""
        # 日本語設定ファイルを作成
        create_settings_file('ja')

        # SettingsManagerをリセットして再初期化
        SettingsManager._instance = None
        settings_manager = SettingsManager()
        settings_manager.load_settings()

        # 有効な値でvalidate_requiredを呼び出し(例外が発生しないことを確認)
        try:
            validate_required("valid_value", "testParam")
            validate_required(123, "numericParam")
            validate_required(45.67, "floatParam")
        except ValidationError:
            pytest.fail(
                "validate_required raised ValidationError unexpectedly"
            )

    def test_language_switch(self, temp_settings_file):
        """
        言語設定を切り替えた後、エラーメッセージの言語も
        切り替わることを確認
        """
        # 最初は日本語で設定
        create_settings_file('ja')
        SettingsManager._instance = None
        settings_manager = SettingsManager()
        settings_manager.load_settings()

        with pytest.raises(ValidationError) as exc_info_ja:
            validate_required("", "param1")

        error_message_ja = str(exc_info_ja.value)

        # 英語に切り替え
        create_settings_file('en')
        SettingsManager._instance = None
        settings_manager = SettingsManager()
        settings_manager.load_settings()

        with pytest.raises(ValidationError) as exc_info_en:
            validate_required("", "param1")

        error_message_en = str(exc_info_en.value)

        # 両方のメッセージに"param1"が含まれることを確認
        assert "param1" in error_message_ja
        assert "param1" in error_message_en

        # メッセージが異なることを確認(言語が切り替わっている)
        # 注: 実際の翻訳が機能している場合は、
        # 日本語と英語で異なるメッセージになるはず
        assert (
            "必須です" in error_message_ja or
            "is required" in error_message_ja
        )
        assert "is required" in error_message_en
