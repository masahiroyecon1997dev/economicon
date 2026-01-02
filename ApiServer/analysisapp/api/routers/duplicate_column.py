from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.duplicate_column import duplicate_column
from ..services import ApiError
from ..schemas import DataDuplicateColumnRequest

router = APIRouter()


@router.post("/duplicate-column")
async def duplicate_column_endpoint(request: Request, body: DataDuplicateColumnRequest):
    """カラムを複製するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : DataDuplicateColumnRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    try:
        create_log_api_request(request)

        result = duplicate_column(
            table_name=body.tableName,
            source_column_name=body.sourceColumnName,
            new_column_name=body.newColumnName
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
        message = _("An unexpected error occurred during duplicating column processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
