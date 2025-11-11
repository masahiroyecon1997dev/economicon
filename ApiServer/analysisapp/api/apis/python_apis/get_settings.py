import os
import platform
from pathlib import Path
from typing import Dict

import yaml
from django.utils.translation import gettext as _

from .common_api_class import AbstractApi, ApiError


class GetSettings(AbstractApi):
    """
    アプリケーション設定を取得するためのAPIクラス

    ホームディレクトリから設定ファイルを読み込み、設定情報を返します。
    設定ファイルが存在しない場合はデフォルト設定を返します。
    """

    os_system = platform.system()
    os_name = "Windows"

    if os_system == "Windows":
        os_name = "Windows"
    elif os_system == "Darwin" or os_system == "MacOs":
        os_name = "macOS"
    elif os_system == "Linux":
        os_name = "Linux"
    else:
        print(f"その他のOSです: {os_system}")

    # デフォルト設定値
    DEFAULT_SETTINGS = {
        'os_name': os_name,
        'default_folder_path': str(Path.home()).replace(os.sep, '/'),
        'display_rows': 100,
        'app_language': 'ja',
        'encoding': 'utf-8',
        'path_separator': '/'
    }

    SETTINGS_FILE_NAME = 'analysis_app_settings.yml'

    def __init__(self):
        self.settings_file_path = Path.home() / self.SETTINGS_FILE_NAME

    def validate(self):
        # 設定取得にはバリデーションは不要
        return None

    def execute(self):
        try:
            # 設定ファイルの存在チェック
            if self.settings_file_path.exists():
                # 設定ファイルが存在する場合は読み込み
                with open(self.settings_file_path, 'r', encoding='utf-8') as f:
                    user_settings = yaml.safe_load(f)

                # デフォルト設定とマージ（ユーザー設定を優先）
                settings = self.DEFAULT_SETTINGS.copy()
                settings.update(user_settings)
            else:
                # 設定ファイルが存在しない場合はデフォルト設定を使用
                settings = self.DEFAULT_SETTINGS.copy()

            # 結果を返す
            result = {
                'osName': settings.get('os_name'),
                'defaultFolderPath': settings.get('default_folder_path'),
                'displayRows': settings.get('display_rows'),
                'appLanguage': settings.get('app_language'),
                'encoding': settings.get('encoding'),
                'pathSeparator': settings.get('path_separator')
            }
            return result

        except yaml.YAMLError:
            # YAMLの解析エラーの場合はデフォルト設定を返す
            result = {
                'osName':
                    self.DEFAULT_SETTINGS['os_name'],
                'defaultFolderPath':
                    self.DEFAULT_SETTINGS['default_folder_path'],
                'displayRows':
                    self.DEFAULT_SETTINGS['display_rows'],
                'appLanguage':
                    self.DEFAULT_SETTINGS['app_language'],
                'encoding':
                    self.DEFAULT_SETTINGS['encoding'],
                'pathSeparator':
                    self.DEFAULT_SETTINGS['path_separator']
            }
            return result

        except Exception as e:
            message = _("An unexpected error occurred "
                        "during getting settings processing")
            raise ApiError(message) from e


def get_setting() -> Dict:
    """
    アプリケーション設定を取得する関数

    Returns:
        Dict: 設定情報を含む辞書
            - osName: クライアントOSの名前
            - defaultFolderPath: ファイル読み込みをするフォルダパスの初期値
            - displayRows: テーブルに表示する行数
            - appLanguage: アプリケーションの表示言語
            - encoding: ファイル読み込み時のデフォルトエンコーディング
            - pathSeparator: パス区切り文字
    """
    api = GetSettings()
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    return api.execute()
