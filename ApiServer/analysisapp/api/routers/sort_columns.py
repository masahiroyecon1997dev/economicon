from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.sort_columns import sort_columns
from ..services import ApiError
from ..schemas import OperationsSortColumnsRequest

router = APIRouter()


@router.post("/sort-columns")
async def sort_columns_endpoint(request: Request, body: OperationsSortColumnsRequest):
    """
    列のソート処理エンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : OperationsSortColumnsRequest
        リクエストボディ
        - tableName: テーブル名
        - sortColumns: ソート列情報

    Returns
    -------
    JSONResponse
        処理結果
    """
    try:
        create_log_api_request(request)

        result = sort_columns(
            table_name=body.tableName,
            sort_columns=body.sortColumns
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
        message = _("An unexpected error occurred during column sorting processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
