from fastapi import APIRouter, Request
from fastapi import status as http_status

from ..models import (
    ConfidenceIntervalRequestBody,
    ConfidenceIntervalResult,
    DescriptiveStatisticsRequestBody,
    DescriptiveStatisticsResult,
    SuccessResponse,
)
from ..services.data.dependencies import TablesStoreDep
from ..services.operation import run_operation
from ..services.statistics.confidence_interval import ConfidenceInterval
from ..services.statistics.descriptive_statistics import DescriptiveStatistics
from ..utils import create_success_response

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.post(
    "/confidence-interval",
    response_model=SuccessResponse[ConfidenceIntervalResult],
)
async def confidence_interval(
    request: Request,
    body: ConfidenceIntervalRequestBody,
    tables_store: TablesStoreDep,
):
    """信頼区間計算を行うエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : ConfidenceIntervalRequestBody
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = ConfidenceInterval(body, tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post(
    "/descriptive", response_model=SuccessResponse[DescriptiveStatisticsResult]
)
async def descriptive_statistics(
    request: Request,
    body: DescriptiveStatisticsRequestBody,
    tables_store: TablesStoreDep,
):
    """記述統計を計算するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : DescriptiveStatisticsRequestBody
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # ビジネスロジックの実行
    api = DescriptiveStatistics(body, tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )
