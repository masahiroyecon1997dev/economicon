"""
分析結果管理サービス

AnalysisResultStoreへのアクセスをラップし、
統一されたエラーハンドリングとバリデーションを提供します。
"""
from typing import Dict

from ...utils.validator.common_validators import ValidationError
from ..abstract_api import AbstractApi, ApiError
from ..data.analysis_result_store import AnalysisResultStore
from ..django_compat import gettext as _


class GetAllAnalysisResults(AbstractApi):
    """
    すべての分析結果のサマリーを取得するサービス
    """

    def __init__(self):
        self.result_store = AnalysisResultStore()
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
            return {'results': summaries}
        except Exception as e:
            raise ApiError(
                _("An unexpected error occurred during getting "
                  "analysis results")
            ) from e


class GetAnalysisResult(AbstractApi):
    """
    特定の分析結果を取得するサービス
    """

    def __init__(self, result_id: str):
        self.result_store = AnalysisResultStore()
        self.result_id = result_id
        self.param_names = {
            'result_id': 'resultId'
        }

    def validate(self):
        """
        バリデーション

        結果IDが空でないことを確認
        """
        if not self.result_id or not self.result_id.strip():
            raise ValidationError(
                _("Result ID is required")
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
            raise ApiError(
                _("An unexpected error occurred during getting "
                  "analysis result")
            ) from e


class DeleteAnalysisResult(AbstractApi):
    """
    特定の分析結果を削除するサービス
    """

    def __init__(self, result_id: str):
        self.result_store = AnalysisResultStore()
        self.result_id = result_id
        self.param_names = {
            'result_id': 'resultId'
        }

    def validate(self):
        """
        バリデーション

        結果IDが空でないことを確認
        """
        if not self.result_id or not self.result_id.strip():
            raise ValidationError(
                _("Result ID is required")
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
            return {'deletedResultId': deleted_id}
        except KeyError:
            raise
        except Exception as e:
            raise ApiError(
                _("An unexpected error occurred during deleting "
                  "analysis result")
            ) from e


class ClearAllAnalysisResults(AbstractApi):
    """
    すべての分析結果を削除するサービス
    """

    def __init__(self):
        self.result_store = AnalysisResultStore()
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
            return {'message': 'All analysis results cleared'}
        except Exception as e:
            raise ApiError(
                _("An unexpected error occurred during clearing "
                  "analysis results")
            ) from e


def get_all_analysis_results() -> Dict:
    api = GetAllAnalysisResults()
    validation_error = api.validate()
    if validation_error:
        raise ValueError(validation_error.message)
    return api.execute()


def get_analysis_result(result_id: str) -> Dict:
    api = GetAnalysisResult(result_id)
    validation_error = api.validate()
    if validation_error:
        raise ValueError(validation_error.message)
    return api.execute()


def delete_analysis_result(result_id: str) -> Dict:
    api = DeleteAnalysisResult(result_id)
    validation_error = api.validate()
    if validation_error:
        raise ValueError(validation_error.message)
    return api.execute()


def clear_all_analysis_results() -> Dict:
    api = ClearAllAnalysisResults()
    validation_error = api.validate()
    if validation_error:
        raise ValueError(validation_error.message)
    return api.execute()
