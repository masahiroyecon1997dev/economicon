from fastapi import APIRouter, Request
from fastapi import status as http_status

from ..services.operation import run_operation
from ..services.settings.get_settings import GetSettings
from ..utils import create_log_api_request, create_success_response

router = APIRouter(prefix="/setting", tags=["setting"])


@router.get("/settings")
async def get_settings(request: Request):
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

    api = GetSettings()
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )
