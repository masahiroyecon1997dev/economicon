from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..services.clear_tables import clear_tables
from ..services import ApiError

router = APIRouter()


@router.delete("/clear-tables")
async def clear_tables_endpoint(request: Request):
    """全テーブルをクリアするエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト

    Returns
    -------
    JSONResponse
        処理結果
    """
    try:
        # リクエスト受け取りログ
        create_log_api_request(request)

        # ビジネスロジックの実行
        result = clear_tables()

        return create_success_response(
            http_status.HTTP_200_OK,
            result
        )

    except ApiError as e:
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            e.message
        )

    except Exception as e:
        message = _("An unexpected error occurred during clearing tables processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
