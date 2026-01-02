from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.delete_column import delete_column
from ..services import ApiError
from ..schemas import DeleteColumnRequest

router = APIRouter()


@router.post("/delete-column")
async def delete_column_endpoint(request: Request, body: DeleteColumnRequest):
    """カラムを削除するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : DeleteColumnRequest
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
        result = delete_column(
            table_name=body.tableName,
            column_name=body.columnName
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
        message = _("An unexpected error occurred during column deletion processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
