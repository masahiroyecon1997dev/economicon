from ...i18n.translation import gettext as _
from ...utils import ProcessingError
from ..data.settings_manager import SettingsManager


class GetSettings:
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
            message = _(
                "An unexpected error occurred "
                "during getting settings processing"
            )
            raise ProcessingError(
                error_code="GET_SETTINGS_ERROR", message=message, detail=str(e)
            ) from e
