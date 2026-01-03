from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.rename_table import rename_table
from ..services import ApiError
from ..schemas import RenameTableRequest

router = APIRouter()


@router.post("/rename-table")
async def rename_table_endpoint(request: Request, body: RenameTableRequest):
    """
    テーブル名変更エンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : RenameTableRequest
        リクエストボディ
        - oldTableName: 旧テーブル名
        - newTableName: 新テーブル名

    Returns
    -------
    JSONResponse
        処理結果
    """
    try:
        create_log_api_request(request)

        result = rename_table(
            old_table_name=body.oldTableName,
            new_table_name=body.newTableName,
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
        message = _("An unexpected error occurred during table rename processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
