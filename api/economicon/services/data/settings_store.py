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


class SettingsStore:
    """
    アプリケーション設定を管理するシングルトンクラス

    起動時に設定ファイルを読み込み、設定がない場合はデフォルト設定で
    ファイルを作成します。スレッドセーフな実装になっています。
    """

    _instance = None
    _lock: threading.RLock = threading.RLock()

    SETTINGS_FILE_NAME = "economicon.config.yml"

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 初期化が一度だけ行われるようにする
        if not hasattr(self, "_initialized"):
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
            "os_name": os_name,
            "default_folder_path": str(Path.home()).replace(os.sep, "/"),
            "display_rows": 100,
            "app_language": "ja",
            "encoding": "utf-8",
            "path_separator": "/",
        }

    @staticmethod
    def _get_settings_file_path() -> Path:
        """
        設定ファイルのパスを取得

        Returns:
            Path: 設定ファイルのパス
        """
        os_system = platform.system()

        if os_system == "Windows":
            # WindowsではAppData/Roaming/economicon/配下に配置
            settings_dir = Path.home() / "AppData" / "Roaming" / "economicon"
        else:
            # macOS/Linuxではホームディレクトリ直下
            settings_dir = Path.home()

        # ディレクトリが存在しない場合は作成
        settings_dir.mkdir(parents=True, exist_ok=True)

        return settings_dir / SettingsStore.SETTINGS_FILE_NAME

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
                    settings_file_path, default_settings
                )

            # 設定ファイルを読み込み
            try:
                with open(settings_file_path, "r", encoding="utf-8") as f:
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
                os_name=settings.get("os_name", default_settings["os_name"]),
                default_folder_path=settings.get(
                    "default_folder_path",
                    default_settings["default_folder_path"],
                ),
                display_rows=settings.get(
                    "display_rows", default_settings["display_rows"]
                ),
                app_language=settings.get(
                    "app_language", default_settings["app_language"]
                ),
                encoding=settings.get(
                    "encoding", default_settings["encoding"]
                ),
                path_separator=settings.get(
                    "path_separator", default_settings["path_separator"]
                ),
            )

    def _create_default_settings_file(
        self, file_path: Path, settings: dict
    ) -> None:
        """
        デフォルト設定ファイルを作成

        Args:
            file_path: 設定ファイルのパス
            settings: デフォルト設定の辞書
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    settings, f, default_flow_style=False, allow_unicode=True
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
                    "Settings not initialized. Call load_settings() first."
                )
            return self._settings

    def reload_settings(self) -> None:
        """
        設定を再読み込み
        """
        self.load_settings()

    def update_settings(
        self,
        os_name: Optional[str] = None,
        default_folder_path: Optional[str] = None,
        display_rows: Optional[int] = None,
        app_language: Optional[str] = None,
        encoding: Optional[str] = None,
        path_separator: Optional[str] = None,
    ) -> None:
        """
        設定を更新する（指定された項目のみ）

        Args:
            os_name: OS名
            default_folder_path: デフォルトフォルダパス
            display_rows: 表示行数
            app_language: アプリケーション言語
            encoding: エンコーディング
            path_separator: パス区切り文字
        """
        with self._lock:
            if self._settings is None:
                raise RuntimeError(
                    "Settings not initialized. Call load_settings() first."
                )

            # 現在の設定を取得
            current_settings = self._settings

            # 指定された値で更新（Noneでない場合のみ）
            updated_os_name = (
                os_name if os_name is not None else current_settings.os_name
            )
            updated_folder_path = (
                default_folder_path
                if default_folder_path is not None
                else current_settings.default_folder_path
            )
            updated_display_rows = (
                display_rows
                if display_rows is not None
                else current_settings.display_rows
            )
            updated_app_language = (
                app_language
                if app_language is not None
                else current_settings.app_language
            )
            updated_encoding = (
                encoding if encoding is not None else current_settings.encoding
            )
            updated_path_separator = (
                path_separator
                if path_separator is not None
                else current_settings.path_separator
            )

            # 新しい設定オブジェクトを作成
            self._settings = SettingsInfo(
                os_name=updated_os_name,
                default_folder_path=updated_folder_path,
                display_rows=updated_display_rows,
                app_language=updated_app_language,
                encoding=updated_encoding,
                path_separator=updated_path_separator,
            )

    def save_settings(self) -> None:
        """
        現在の設定をファイルに保存する
        """
        with self._lock:
            if self._settings is None:
                raise RuntimeError(
                    "Settings not initialized. Call load_settings() first."
                )

            settings_file_path = self._get_settings_file_path()

            settings_dict = {
                "os_name": self._settings.os_name,
                "default_folder_path": self._settings.default_folder_path,
                "display_rows": self._settings.display_rows,
                "app_language": self._settings.app_language,
                "encoding": self._settings.encoding,
                "path_separator": self._settings.path_separator,
            }

            try:
                with open(settings_file_path, "w", encoding="utf-8") as f:
                    yaml.dump(
                        settings_dict,
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                    )
            except Exception as e:
                raise RuntimeError(f"Failed to save settings: {e}")
