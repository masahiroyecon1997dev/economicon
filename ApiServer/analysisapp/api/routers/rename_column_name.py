from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.rename_column import rename_column
from ..services import ApiError
from ..schemas import RenameColumnRequest

router = APIRouter()


@router.post("/rename-column-name")
async def rename_column_name_endpoint(request: Request, body: RenameColumnRequest):
    """
    列名変更エンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : RenameColumnNameRequest
        リクエストボディ
        - tableName: テーブル名
        - oldColumnName: 旧列名
        - newColumnName: 新列名

    Returns
    -------
    JSONResponse
        処理結果
    """
    try:
        create_log_api_request(request)

        result = rename_column(
            body.tableName,
            body.oldColumnName,
            body.newColumnName
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
        message = _("An unexpected error occurred during renaming column processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
