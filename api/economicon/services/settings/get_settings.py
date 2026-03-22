from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.services.data.settings_store import SettingsStore
from economicon.utils import ProcessingError


class GetSettings:
    """
    アプリケーション設定を取得するためのAPIクラス

    SettingsStoreから設定情報を取得して返します。
    """

    def __init__(self, settings_store: SettingsStore):
        self.settings_manager = settings_store

    def validate(self):
        # 設定取得にはバリデーションは不要
        return None

    def execute(self):
        try:
            # SettingsStoreから設定を取得
            settings_info = self.settings_manager.get_settings()

            # 結果を返す
            return settings_info.to_dict()

        except Exception as e:
            message = _(
                "An unexpected error occurred "
                "during getting settings processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.GET_SETTINGS_ERROR,
                message=message,
                detail=str(e),
            ) from e
