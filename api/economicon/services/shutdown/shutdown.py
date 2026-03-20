from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.services.data.settings_store import SettingsStore
from economicon.utils import ProcessingError
from economicon.utils.logging import logger

_TOTAL_CLEANUP_STEPS = 2


class Shutdown:
    """
    アプリ終了前クリーンアップを実行するサービスクラス

    ① 分析結果の pickle ファイルを全削除（AnalysisResultStore.clear_all）
    ② 設定をファイルに保存（SettingsStore.save_settings）

    2処理は独立して実行し、片方が失敗しても続行します。
    両方失敗した場合は ProcessingError を送出します。
    """

    def __init__(
        self,
        analysis_result_store: AnalysisResultStore,
        settings_store: SettingsStore,
    ):
        self._analysis_result_store = analysis_result_store
        self._settings_store = settings_store

    def validate(self):
        return None

    def execute(self) -> dict:
        errors: list[str] = []

        try:
            self._analysis_result_store.clear_all()
            logger.info("Shutdown: analysis result files cleared.")
        except Exception as e:
            logger.warning(f"Shutdown: clear_all failed: {e}")
            errors.append(str(e))

        try:
            self._settings_store.save_settings()
            logger.info("Shutdown: settings saved.")
        except Exception as e:
            logger.warning(f"Shutdown: save_settings failed: {e}")
            errors.append(str(e))

        if len(errors) == _TOTAL_CLEANUP_STEPS:
            # 両処理が失敗した場合のみエラーとして報告する
            message = _(
                "An unexpected error occurred during shutdown processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.SHUTDOWN_ERROR,
                message=message,
                detail="; ".join(errors),
            )

        return {"status": "ok"}
