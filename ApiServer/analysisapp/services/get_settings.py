from typing import Dict

from ..i18n.translation import gettext as _

from .data.settings_manager import SettingsManager
from .abstract_api import AbstractApi, ApiError


class GetSettings(AbstractApi):
    """
    アプリケーション設定を取得するためのAPIクラス

    SettingsManagerから設定情報を取得して返します。
    """

    def __init__(self):
        self.settings_manager = SettingsManager()

    def validate(self):
        # 設定取得にはバリデーションは不要
        return None

    def execute(self):
        try:
            # SettingsManagerから設定を取得
            settings_info = self.settings_manager.get_settings()

            # 結果を返す
            return settings_info.to_dict()

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
