"""
分析結果管理エンドポイント

結果の取得・削除・出力など、分析結果に対する操作を提供します。
回帰分析・検定・因果推論など、あらゆる分析の結果を統一して管理します。
"""

from fastapi import APIRouter, Request
from fastapi import status as http_status

from economicon.schemas import (
    COMMON_ERROR_RESPONSES,
    SuccessResponse,
)
from economicon.schemas.results import (
    ClearAllAnalysisResultsResult,
    DeleteAnalysisResultResult,
    GetAllAnalysisResultsResult,
    GetAnalysisResultResult,
    OutputResultRequest,
    OutputResultResult,
)
from economicon.services.data.dependencies import AnalysisResultStoreDep
from economicon.services.operation import run_operation
from economicon.services.results.output_result import OutputResult
from economicon.services.results.result import (
    ClearAllAnalysisResults,
    DeleteAnalysisResult,
    GetAllAnalysisResults,
    GetAnalysisResult,
)
from economicon.utils import create_success_response

router = APIRouter(
    prefix="/analysis",
    tags=["analysis"],
    responses=COMMON_ERROR_RESPONSES,
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
    api = ClearAllAnalysisResults(result_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post(
    "/results/output",
    response_model=SuccessResponse[OutputResultResult],
)
async def output_result(
    request: Request,
    body: OutputResultRequest,
    result_store: AnalysisResultStoreDep,
):
    """
    推定結果をテキスト / Markdown / LaTeX 形式で整形出力する

    指定した分析結果 ID のリストから係数表などを生成します。
    複数 ID を指定するとモデル比較表を生成します。

    Parameters
    ----------
    request : Request
        FastAPI のリクエストオブジェクト
    body : OutputResultRequest
        - resultIds: 出力する分析結果 ID のリスト（1件以上）
        - format: 出力形式（text / markdown / latex）
        - statInParentheses: 括弧内統計量（se / t / p / none）
        - significanceStars: 有意性記号の設定（省略時はデフォルト）
        - variableLabels: 変数名の表示ラベル辞書
        - constAtBottom: 定数項を最下部に表示するか

    Returns
    -------
    JSONResponse
        整形済み出力テキストを含む成功レスポンス
    """
    api = OutputResult(body, result_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )
