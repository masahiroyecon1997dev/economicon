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
            "general": {
                "language": "ja",
                "last_opened_path": str(Path.home()).replace(os.sep, "/"),
                "theme": "light",
            },
            "data": {
                "encoding": "utf-8",
            },
            "log": {
                "path": "./logs/app.log",
            },
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
                    for section in ("general", "data", "log"):
                        if section in user_settings and isinstance(
                            user_settings[section], dict
                        ):
                            settings[section] = {
                                **settings.get(section, {}),
                                **user_settings[section],
                            }

            except yaml.YAMLError:
                # YAML解析エラーの場合はデフォルト設定を使用
                settings = default_settings

            general = settings.get("general", {})
            data_cfg = settings.get("data", {})
            log_cfg = settings.get("log", {})
            defaults_general = default_settings["general"]
            defaults_data = default_settings["data"]
            defaults_log = default_settings["log"]

            # SettingsInfoオブジェクトを作成
            self._settings = SettingsInfo(
                os_name=settings.get("os_name", default_settings["os_name"]),
                language=general.get("language", defaults_general["language"]),
                last_opened_path=general.get(
                    "last_opened_path", defaults_general["last_opened_path"]
                ),
                theme=general.get("theme", defaults_general["theme"]),
                encoding=data_cfg.get("encoding", defaults_data["encoding"]),
                log_path=log_cfg.get("path", defaults_log["path"]),
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
        language: Optional[str] = None,
        last_opened_path: Optional[str] = None,
        theme: Optional[str] = None,
        encoding: Optional[str] = None,
        log_path: Optional[str] = None,
    ) -> None:
        """
        設定を更新する（指定された項目のみ）

        Args:
            os_name: OS名
            language: アプリケーション言語
            last_opened_path: 最後に開いたフォルダパス
            theme: テーマ
            encoding: エンコーディング
            log_path: ログファイルパス
        """
        with self._lock:
            if self._settings is None:
                raise RuntimeError(
                    "Settings not initialized. Call load_settings() first."
                )

            current = self._settings
            self._settings = SettingsInfo(
                os_name=os_name if os_name is not None else current.os_name,
                language=language
                if language is not None
                else current.language,
                last_opened_path=(
                    last_opened_path
                    if last_opened_path is not None
                    else current.last_opened_path
                ),
                theme=theme if theme is not None else current.theme,
                encoding=encoding
                if encoding is not None
                else current.encoding,
                log_path=log_path
                if log_path is not None
                else current.log_path,
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
                "general": {
                    "language": self._settings.language,
                    "last_opened_path": self._settings.last_opened_path,
                    "theme": self._settings.theme,
                },
                "data": {
                    "encoding": self._settings.encoding,
                },
                "log": {
                    "path": self._settings.log_path,
                },
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
