from fastapi import APIRouter, Request
from fastapi import status as http_status

from economicon.models import (
    COMMON_ERROR_RESPONSES,
    ConfidenceIntervalRequestBody,
    ConfidenceIntervalResult,
    CreateCorrelationTableRequestBody,
    CreateCorrelationTableResult,
    DescriptiveStatisticsRequestBody,
    DescriptiveStatisticsResult,
    StatisticalTestRequestBody,
    StatisticalTestResult,
    SuccessResponse,
)
from economicon.services.data.dependencies import TablesStoreDep
from economicon.services.operation import run_operation
from economicon.services.statistics.confidence_interval import (
    ConfidenceInterval,
)
from economicon.services.statistics.create_correlation_table import (
    CreateCorrelationTable,
)
from economicon.services.statistics.descriptive_statistics import (
    DescriptiveStatistics,
)
from economicon.services.statistics.statistical_test import (
    StatisticalTest,
)
from economicon.utils import create_success_response

router = APIRouter(
    prefix="/statistics",
    tags=["statistics"],
    responses=COMMON_ERROR_RESPONSES,
)


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


@router.post(
    "/create-correlation-table",
    response_model=SuccessResponse[CreateCorrelationTableResult],
)
async def create_correlation_table(
    request: Request,
    body: CreateCorrelationTableRequestBody,
    tables_store: TablesStoreDep,
):
    """相関係数テーブル作成を行うエンドポイント

    指定されたテーブルの各列間の相関係数行列を計算し、
    新しいテーブルとして保存します。

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : CreateCorrelationTableRequestBody
        リクエストボディ
    tables_store : TablesStoreDep
        テーブルストア依存性

    Returns
    -------
    JSONResponse
        処理結果（新規作成されたテーブル名）
    """
    # ビジネスロジックの実行
    api = CreateCorrelationTable(body, tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )


@router.post(
    "/test",
    response_model=SuccessResponse[StatisticalTestResult],
)
async def statistical_test(
    request: Request,
    body: StatisticalTestRequestBody,
    tables_store: TablesStoreDep,
):
    """統計的検定を実行するエンドポイント

    t 検定・z 検定・F 検定（分散比検定 / ANOVA）を実行し、
    検定統計量・p 値・自由度・信頼区間・効果量を返します。

    Parameters
    ----------
    request : Request
        FastAPI のリクエストオブジェクト
    body : StatisticalTestRequestBody
        リクエストボディ
    tables_store : TablesStoreDep
        テーブルストア依存性

    Returns
    -------
    JSONResponse
        処理結果
    """
    api = StatisticalTest(body, tables_store)
    result = run_operation(api)

    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )
