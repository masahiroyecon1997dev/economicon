from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.descriptive_statistics import descriptive_statistics
from ..services import ApiError
from ..schemas import DescriptiveStatisticsRequest

router = APIRouter()


@router.post("/descriptive-statistics")
async def descriptive_statistics_endpoint(request: Request, body: DescriptiveStatisticsRequest):
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
    try:
        create_log_api_request(request)

        result = descriptive_statistics(
            table_name=body.tableName,
            column_name_list=body.columnNameList,
            statistics=body.statistics
        )

        return create_success_response(
            http_status.HTTP_200_OK,
            result
        )

    except ValidationError as e:
        return create_error_response(
            http_status.HTTP_400_BAD_REQUEST,
            e.message
        )

    except ApiError as e:
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            e.message
        )

    except Exception as e:
        message = _("An unexpected error occurred during descriptive statistics processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
