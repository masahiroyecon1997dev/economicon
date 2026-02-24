from fastapi import APIRouter, Request
from fastapi import status as http_status

from economicon.models import (
    GetSettingsResult,
    SuccessResponse,
)
from economicon.services.data.dependencies import SettingsStoreDep
from economicon.services.operation import run_operation
from economicon.services.settings.get_settings import GetSettings
from economicon.utils import create_success_response

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SuccessResponse[GetSettingsResult])
async def get_settings(
    request: Request,
    settings_store: SettingsStoreDep,
):
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
    # ビジネスロジックの実行
    api = GetSettings(settings_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )
