from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.calculate_column import calculate_column
from ..services import ApiError
from ..schemas import StatisticsCalculateColumnRequest

router = APIRouter()


@router.post("/calculate-column")
async def calculate_column_endpoint(request: Request, body: StatisticsCalculateColumnRequest):
    """カラム計算を実行するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : StatisticsCalculateColumnRequest
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
        result = calculate_column(
            table_name=body.tableName,
            new_column_name=body.newColumnName,
            calculation_expression=body.calculationExpression
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
        message = _("An unexpected error occurred during column calculation processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
