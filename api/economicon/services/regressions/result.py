"""
分析結果管理サービス

AnalysisResultStoreへのアクセスをラップし、
統一されたエラーハンドリングとバリデーションを提供します。
"""

from ...core.enums import ErrorCode
from ...i18n.translation import gettext as _
from ...utils import ProcessingError, ValidationError
from ..data.analysis_result_store import AnalysisResultStore


class GetAllAnalysisResults:
    """
    すべての分析結果のサマリーを取得するサービス
    """

    def __init__(self, result_store: AnalysisResultStore):
        self.result_store = result_store
        self.param_names = {}

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
        self.param_names = {"result_id": "resultId"}

    def validate(self):
        """
        バリデーション

        結果IDが空でないことを確認
        """
        if not self.result_id or not self.result_id.strip():
            raise ValidationError(
                error_code=ErrorCode.RESULT_ID_REQUIRED,
                message=_("Result ID is required"),
            )
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
        self.param_names = {"result_id": "resultId"}

    def validate(self):
        """
        バリデーション

        結果IDが空でないことを確認
        """
        if not self.result_id or not self.result_id.strip():
            raise ValidationError(
                error_code=ErrorCode.RESULT_ID_REQUIRED,
                message=_("Result ID is required"),
            )
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


class ClearAllAnalysisResults:
    """
    すべての分析結果を削除するサービス
    """

    def __init__(self, result_store: AnalysisResultStore):
        self.result_store = result_store
        self.param_names = {}

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
            return {"message": "All analysis results cleared"}
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.CLEAR_ALL_ANALYSIS_RESULTS_ERROR,
                message=_(
                    "An unexpected error occurred during clearing "
                    "analysis results"
                ),
            ) from e
