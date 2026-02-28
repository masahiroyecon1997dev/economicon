from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.models import UpdateSettingsRequest
from economicon.services.data.settings_store import SettingsStore
from economicon.utils import ProcessingError


class UpdateSettings:
    """
    アプリケーション設定を更新するAPIクラス

    指定されたフィールドのみを部分更新し、設定ファイルに保存します。
    省略されたフィールドは現在の値を維持します。
    """

    def __init__(
        self,
        body: UpdateSettingsRequest,
        settings_store: SettingsStore,
    ):
        self.settings_store = settings_store
        self.language = body.language
        self.theme = body.theme
        self.encoding = body.encoding
        self.log_path = body.log_path

    def validate(self):
        # バリデーションはモデルの pattern 制約で完結しているため不要
        return None

    def execute(self):
        try:
            self.settings_store.update_settings(
                language=self.language,
                theme=self.theme,
                encoding=self.encoding,
                log_path=self.log_path,
            )
            self.settings_store.save_settings()

            # 更新後の設定全体を返す
            return self.settings_store.get_settings().to_dict()

        except Exception as e:
            message = _(
                "An unexpected error occurred "
                "during updating settings processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.UPDATE_SETTINGS_ERROR,
                message=message,
                detail=str(e),
            ) from e
