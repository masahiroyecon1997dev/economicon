"""
分析結果管理サービス

AnalysisResultStoreへのアクセスをラップし、
統一されたエラーハンドリングとバリデーションを提供します。
"""

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas.result_management import UpdateAnalysisResultRequest
from economicon.services.data.analysis_result_store import AnalysisResultStore
from economicon.utils import ProcessingError, ValidationError


class GetAllAnalysisResults:
    """
    すべての分析結果のサマリーを取得するサービス
    """

    def __init__(self, result_store: AnalysisResultStore):
        self.result_store = result_store

    def validate(self):
        """バリデーション（特になし）"""
        return None

    def execute(self):
        """
        すべての分析結果のサマリーを取得

        Returns
        -------
        dict
            分析結果のサマリーリスト
        """
        try:
            summaries = self.result_store.get_all_summaries()
            return {"results": summaries}
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.GET_ALL_RESULTS_ERROR,
                message=_(
                    "An unexpected error occurred during getting "
                    "analysis results"
                ),
            ) from e


class GetAnalysisResult:
    """
    特定の分析結果を取得するサービス
    """

    def __init__(self, result_id: str, result_store: AnalysisResultStore):
        self.result_store = result_store
        self.result_id = result_id

    def validate(self):
        """バリデーション（特になし）"""
        return None

    def execute(self):
        """
        指定されたIDの分析結果を取得

        Returns
        -------
        dict
            分析結果の詳細

        Raises
        ------
        KeyError
            結果が見つからない場合
        ApiError
            その他のエラーが発生した場合
        """
        try:
            result = self.result_store.get_result(self.result_id)
            return result.to_dict()
        except KeyError:
            raise
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.GET_ANALYSIS_RESULT_ERROR,
                message=_(
                    "An unexpected error occurred during getting "
                    "analysis result"
                ),
            ) from e


class DeleteAnalysisResult:
    """
    特定の分析結果を削除するサービス
    """

    def __init__(self, result_id: str, result_store: AnalysisResultStore):
        self.result_store = result_store
        self.result_id = result_id

    def validate(self):
        """バリデーション（特になし）"""
        return None

    def execute(self):
        """
        指定されたIDの分析結果を削除

        Returns
        -------
        dict
            削除された結果のID

        Raises
        ------
        KeyError
            結果が見つからない場合
        ApiError
            その他のエラーが発生した場合
        """
        try:
            deleted_id = self.result_store.delete_result(self.result_id)
            return {"deletedResultId": deleted_id}
        except KeyError:
            raise
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.DELETE_ANALYSIS_RESULT_ERROR,
                message=_(
                    "An unexpected error occurred during deleting "
                    "analysis result"
                ),
            ) from e


class UpdateAnalysisResult:
    """特定の分析結果メタデータを更新するサービス"""

    def __init__(
        self,
        result_id: str,
        request: UpdateAnalysisResultRequest,
        result_store: AnalysisResultStore,
    ):
        self.result_store = result_store
        self.result_id = result_id
        self.request = request

    def validate(self):
        if not self.request.model_fields_set:
            raise ValidationError(
                error_code=ErrorCode.INVALID_INPUT,
                message=_("At least one field must be provided"),
            )

    def execute(self):
        try:
            name = None
            description = None
            summary_text_override: str | None | object = object()

            if "name" in self.request.model_fields_set:
                name = self.request.name.strip() if self.request.name else None

            if "description" in self.request.model_fields_set:
                description = (self.request.description or "").strip()

            if "summary_text_override" in self.request.model_fields_set:
                raw_summary = self.request.summary_text_override
                summary_text_override = (
                    raw_summary.strip()
                    if raw_summary and raw_summary.strip()
                    else None
                )

            updated = self.result_store.update_metadata(
                self.result_id,
                name=name,
                description=description,
                summary_text_override=summary_text_override,
            )
            return {
                "updatedSummary": updated.to_summary_dict(),
                "updatedDetail": updated.to_dict(),
            }
        except KeyError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.UPDATE_ANALYSIS_RESULT_ERROR,
                message=_(
                    "An unexpected error occurred during updating "
                    "analysis result"
                ),
            ) from e


class ClearAllAnalysisResults:
    """
    すべての分析結果を削除するサービス
    """

    def __init__(self, result_store: AnalysisResultStore):
        self.result_store = result_store

    def validate(self):
        """バリデーション（特になし）"""
        return None

    def execute(self):
        """
        すべての分析結果を削除

        Returns
        -------
        dict
            削除成功メッセージ
        """
        try:
            self.result_store.clear_all()
            return {"message": _("All analysis results cleared")}
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.CLEAR_ALL_ANALYSIS_RESULTS_ERROR,
                message=_(
                    "An unexpected error occurred during clearing "
                    "analysis results"
                ),
            ) from e
