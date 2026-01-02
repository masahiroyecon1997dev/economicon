from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.confidence_interval import confidence_interval
from ..services import ApiError
from ..schemas import ConfidenceIntervalRequest

router = APIRouter()


@router.post("/confidence-interval")
async def confidence_interval_endpoint(request: Request, body: ConfidenceIntervalRequest):
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
    try:
        # リクエスト受け取りログ
        create_log_api_request(request)

        # ビジネスロジックの実行
        result = confidence_interval(
            table_name=body.tableName,
            column_name=body.columnName,
            confidence_level=body.confidenceLevel,
            statistic_type=body.statisticType
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

    except KeyError as e:
        message = _("Required parameter is missing: {}").format(str(e))
        return create_error_response(
            http_status.HTTP_400_BAD_REQUEST,
            message
        )

    except Exception as e:
        message = _("An unexpected error occurred during confidence interval processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
