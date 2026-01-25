from fastapi import APIRouter, Request
from fastapi import status as http_status

from ..schemas import ConfidenceIntervalRequest, DescriptiveStatisticsRequest
from ..services.confidence_interval import confidence_interval
from ..services.descriptive_statistics import descriptive_statistics
from ..utils import create_log_api_request, create_success_response

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.post("/confidence-interval")
async def confidence_interval_endpoint(request: Request,
                                       body: ConfidenceIntervalRequest):
    """信頼区間計算を行うエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : ConfidenceIntervalRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    # リクエスト受け取りログ
    create_log_api_request(request)

    # ビジネスロジックの実行
    result = confidence_interval(**body.model_dump())

    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )


@router.post("/descriptive")
async def descriptive_statistics_endpoint(request: Request,
                                          body: DescriptiveStatisticsRequest):
    """記述統計を計算するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : DescriptiveStatisticsRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    create_log_api_request(request)

    result = descriptive_statistics(**body.model_dump())

    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )
