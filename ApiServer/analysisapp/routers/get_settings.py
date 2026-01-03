from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.get_settings import get_setting
from ..services import ApiError

router = APIRouter()


@router.get("/get-settings")
async def get_settings_endpoint(request: Request):
    """アプリケーション設定を取得するエンドポイント

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
        create_log_api_request(request)

        result = get_setting()

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
        message = _("An unexpected error occurred during getting settings processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
