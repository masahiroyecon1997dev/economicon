"""
統合回帰分析エンドポイント

全ての回帰分析タイプを単一のエンドポイントで処理します。
"""

from fastapi import APIRouter, Request
from fastapi import status as http_status

from economicon.models import (
    COMMON_ERROR_RESPONSES,
    ClearAllAnalysisResultsResult,
    DeleteAnalysisResultResult,
    GetAllAnalysisResultsResult,
    GetAnalysisResultResult,
    RegressionResult,
    SuccessResponse,
)
from economicon.models.regressions import RegressionRequestBody
from economicon.services.data.dependencies import (
    AnalysisResultStoreDep,
    TablesStoreDep,
)
from economicon.services.operation import run_operation
from economicon.services.regressions.regression import Regression
from economicon.services.regressions.result import (
    ClearAllAnalysisResults,
    DeleteAnalysisResult,
    GetAllAnalysisResults,
    GetAnalysisResult,
)
from economicon.utils import (
    create_success_response,
)

router = APIRouter(
    prefix="/analysis",
    tags=["analysis"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.post("/regression", response_model=SuccessResponse[RegressionResult])
async def regression(
    request: Request,
    body: RegressionRequestBody,
    tables_store: TablesStoreDep,
    result_store: AnalysisResultStoreDep,
):
    """
    統合回帰分析エンドポイント

    typeフィールドに応じて適切な分析手法を選択し、実行します。

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : RegressionRequestBody
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
    # ビジネスロジックの実行
    api = Regression(body, tables_store, result_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.get(
    "/results", response_model=SuccessResponse[GetAllAnalysisResultsResult]
)
async def get_all_analysis_results(
    request: Request,
    result_store: AnalysisResultStoreDep,
):
    """
    すべての分析結果のサマリーを取得

    Returns
    -------
    JSONResponse
        分析結果のサマリーリスト
    """
    # ビジネスロジックの実行
    api = GetAllAnalysisResults(result_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.get(
    "/results/{result_id}",
    response_model=SuccessResponse[GetAnalysisResultResult],
)
async def get_analysis_result(
    request: Request,
    result_id: str,
    result_store: AnalysisResultStoreDep,
):
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
    # ビジネスロジックの実行
    api = GetAnalysisResult(result_id, result_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.delete(
    "/results/{result_id}",
    response_model=SuccessResponse[DeleteAnalysisResultResult],
)
async def delete_analysis_result(
    request: Request,
    result_id: str,
    result_store: AnalysisResultStoreDep,
):
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
    # ビジネスロジックの実行
    api = DeleteAnalysisResult(result_id, result_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.delete(
    "/results", response_model=SuccessResponse[ClearAllAnalysisResultsResult]
)
async def clear_all_analysis_results(
    request: Request,
    result_store: AnalysisResultStoreDep,
):
    """
    すべての分析結果を削除

    Returns
    -------
    JSONResponse
        削除成功メッセージ
    """
    # ビジネスロジックの実行
    api = ClearAllAnalysisResults(result_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )
