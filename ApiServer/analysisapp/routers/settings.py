from fastapi import APIRouter, Request, status as http_status

from ..utils import create_success_response, create_log_api_request
from ..services.get_settings import get_setting

router = APIRouter(prefix="/setting", tags=["setting"])


@router.get("/get")
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
    create_log_api_request(request)

    result = get_setting()

    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )
