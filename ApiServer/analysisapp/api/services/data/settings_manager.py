"""
アプリケーション設定を管理するシングルトンマネージャー
"""
import os
import platform
import threading
from pathlib import Path
from typing import Optional

import yaml

from .settings_info import SettingsInfo


class SettingsManager:
    """
    アプリケーション設定を管理するシングルトンクラス

    起動時に設定ファイルを読み込み、設定がない場合はデフォルト設定で
    ファイルを作成します。スレッドセーフな実装になっています。
    """

    _instance = None
    _lock: threading.RLock = threading.RLock()

    SETTINGS_FILE_NAME = 'analysis_app_settings.yml'

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 初期化が一度だけ行われるようにする
        if not hasattr(self, '_initialized'):
            self._settings: Optional[SettingsInfo] = None
            self._lock = threading.RLock()
            self._initialized = True

    @staticmethod
    def _get_default_settings() -> dict:
        """
        デフォルト設定を取得

        Returns:
            dict: デフォルト設定の辞書
        """
        os_system = platform.system()
        os_name = "Windows"

        if os_system == "Windows":
            os_name = "Windows"
        elif os_system == "Darwin" or os_system == "MacOs":
            os_name = "macOS"
        elif os_system == "Linux":
            os_name = "Linux"

        return {
            'os_name': os_name,
            'default_folder_path': str(Path.home()).replace(os.sep, '/'),
            'display_rows': 100,
            'app_language': 'ja',
            'encoding': 'utf-8',
            'path_separator': '/'
        }

    @staticmethod
    def _get_settings_file_path() -> Path:
        """
        設定ファイルのパスを取得

        Returns:
            Path: 設定ファイルのパス
        """
        return Path.home() / SettingsManager.SETTINGS_FILE_NAME

    def load_settings(self) -> None:
        """
        設定ファイルを読み込む

        設定ファイルが存在しない場合は、デフォルト設定でファイルを作成します。
        """
        with self._lock:
            settings_file_path = self._get_settings_file_path()
            default_settings = self._get_default_settings()

            # 設定ファイルが存在しない場合は作成
            if not settings_file_path.exists():
                self._create_default_settings_file(
                    settings_file_path,
                    default_settings
                )

            # 設定ファイルを読み込み
            try:
                with open(settings_file_path, 'r', encoding='utf-8') as f:
                    user_settings = yaml.safe_load(f)

                # デフォルト設定とマージ（ユーザー設定を優先）
                settings = default_settings.copy()
                if user_settings:
                    settings.update(user_settings)

            except yaml.YAMLError:
                # YAML解析エラーの場合はデフォルト設定を使用
                settings = default_settings

            # SettingsInfoオブジェクトを作成
            self._settings = SettingsInfo(
                os_name=settings.get(
                    'os_name',
                    default_settings['os_name']
                ),
                default_folder_path=settings.get(
                    'default_folder_path',
                    default_settings['default_folder_path']
                ),
                display_rows=settings.get(
                    'display_rows',
                    default_settings['display_rows']
                ),
                app_language=settings.get(
                    'app_language',
                    default_settings['app_language']
                ),
                encoding=settings.get(
                    'encoding',
                    default_settings['encoding']
                ),
                path_separator=settings.get(
                    'path_separator',
                    default_settings['path_separator']
                )
            )

    def _create_default_settings_file(
        self,
        file_path: Path,
        settings: dict
    ) -> None:
        """
        デフォルト設定ファイルを作成

        Args:
            file_path: 設定ファイルのパス
            settings: デフォルト設定の辞書
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(
                    settings,
                    f,
                    default_flow_style=False,
                    allow_unicode=True
                )
        except Exception as e:
            print(f"Failed to create default settings file: {e}")

    def get_settings(self) -> SettingsInfo:
        """
        設定情報を取得

        Returns:
            SettingsInfo: 設定情報オブジェクト

        Raises:
            RuntimeError: 設定が初期化されていない場合
        """
        with self._lock:
            if self._settings is None:
                raise RuntimeError(
                    "Settings not initialized. "
                    "Call load_settings() first."
                )
            return self._settings

    def reload_settings(self) -> None:
        """
        設定を再読み込み
        """
        self.load_settings()
