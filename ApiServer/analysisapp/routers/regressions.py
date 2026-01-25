"""
統合回帰分析エンドポイント

全ての回帰分析タイプを単一のエンドポイントで処理します。
"""

from fastapi import APIRouter, Request
from fastapi import status as http_status

from ..schemas.regressions import RegressionRequest
from ..services.regression import execute_regression_analysis
from ..services.data.analysis_result import AnalysisResult
from ..services.data.analysis_result_store import AnalysisResultStore
from ..utils.validator.common_validators import ValidationError
from ..services.abstract_api import ApiError
from ..utils import (
    create_log_api_request,
    create_success_response,
    create_error_response
)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/regression")
async def unified_regression_endpoint(
    request: Request,
    body: RegressionRequest
):
    """
    統合回帰分析エンドポイント

    typeフィールドに応じて適切な分析手法を選択し、実行します。

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : AnalysisRequest
        統合回帰分析リクエスト
        - type: 分析タイプ (ols, logit, probit, tobit, fe, re, iv,
          feiv, lasso, ridge)
        - tableName: 対象テーブル名
        - dependentVariable: 被説明変数
        - explanatoryVariables: 説明変数のリスト
        - その他分析固有のパラメータ

    Returns
    -------
    JSONResponse
        分析結果またはエラーメッセージ
    """
    create_log_api_request(request)

    try:
        # 共通パラメータの準備
        params = {
            'analysis_type': body.type,
            'table_name': body.tableName,
            'dependent_variable': body.dependentVariable,
            'explanatory_variables': body.explanatoryVariables,
            'standard_error_method': body.standardErrorMethod,
            'has_const': body.hasConst,
            'missing_value_handling': body.missingValueHandling,
            'use_t_distribution': body.useTDistribution,
        }

        # パネルデータパラメータ
        if body.entityIdColumn:
            params['entity_id_column'] = body.entityIdColumn
        if body.timeColumn:
            params['time_column'] = body.timeColumn

        # 操作変数パラメータ
        if body.instrumentalVariables:
            params['instrumental_variables'] = body.instrumentalVariables
        if body.endogenousVariables:
            params['endogenous_variables'] = body.endogenousVariables

        # Tobitパラメータ
        if body.leftCensoringLimit is not None:
            params['left_censoring_limit'] = body.leftCensoringLimit
        if body.rightCensoringLimit is not None:
            params['right_censoring_limit'] = body.rightCensoringLimit

        # 正則化パラメータ
        if 'alpha' in body.hyperParameters:
            params['alpha'] = body.hyperParameters['alpha']

        # 統合サービスを呼び出し
        result = execute_regression_analysis(**params)

        # 分析結果をストアに保存
        analysis_result = AnalysisResult(
            name=body.name or f"{body.type.upper()} Analysis",
            description=body.description,
            table_name=body.tableName,
            regression_output=result
        )

        result_store = AnalysisResultStore()
        result_id = result_store.save_result(analysis_result)

        # IDのみを返却
        return create_success_response(
            http_status.HTTP_200_OK,
            {'resultId': result_id}
        )

    except ValidationError as e:
        return create_error_response(
            http_status.HTTP_400_BAD_REQUEST,
            str(e)
        )
    except ApiError as e:
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            str(e)
        )
    except NotImplementedError as e:
        return create_error_response(
            http_status.HTTP_501_NOT_IMPLEMENTED,
            str(e)
        )
    except Exception as e:
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Unexpected error: {str(e)}"
        )


@router.get("/results")
async def get_all_analysis_results(request: Request):
    """
    すべての分析結果のサマリーを取得

    Returns
    -------
    JSONResponse
        分析結果のサマリーリスト
    """
    create_log_api_request(request)

    try:
        result_store = AnalysisResultStore()
        summaries = result_store.get_all_summaries()

        return create_success_response(
            http_status.HTTP_200_OK,
            {'results': summaries}
        )

    except Exception as e:
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Unexpected error: {str(e)}"
        )


@router.get("/results/{result_id}")
async def get_analysis_result(request: Request, result_id: str):
    """
    指定されたIDの分析結果を取得

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    result_id : str
        結果のID

    Returns
    -------
    JSONResponse
        分析結果の詳細
    """
    create_log_api_request(request)

    try:
        result_store = AnalysisResultStore()
        result = result_store.get_result(result_id)

        return create_success_response(
            http_status.HTTP_200_OK,
            result.to_dict()
        )

    except KeyError as e:
        return create_error_response(
            http_status.HTTP_404_NOT_FOUND,
            str(e)
        )
    except Exception as e:
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Unexpected error: {str(e)}"
        )


@router.delete("/results/{result_id}")
async def delete_analysis_result(request: Request, result_id: str):
    """
    指定されたIDの分析結果を削除

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    result_id : str
        削除する結果のID

    Returns
    -------
    JSONResponse
        削除成功メッセージ
    """
    create_log_api_request(request)

    try:
        result_store = AnalysisResultStore()
        deleted_id = result_store.delete_result(result_id)

        return create_success_response(
            http_status.HTTP_200_OK,
            {'deletedResultId': deleted_id}
        )

    except KeyError as e:
        return create_error_response(
            http_status.HTTP_404_NOT_FOUND,
            str(e)
        )
    except Exception as e:
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Unexpected error: {str(e)}"
        )


@router.delete("/results")
async def clear_all_analysis_results(request: Request):
    """
    すべての分析結果を削除

    Returns
    -------
    JSONResponse
        削除成功メッセージ
    """
    create_log_api_request(request)

    try:
        result_store = AnalysisResultStore()
        result_store.clear_all()

        return create_success_response(
            http_status.HTTP_200_OK,
            {'message': 'All analysis results cleared'}
        )

    except Exception as e:
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Unexpected error: {str(e)}"
        )
