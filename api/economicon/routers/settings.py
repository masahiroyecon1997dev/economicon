from fastapi import APIRouter, Request
from fastapi import status as http_status

from economicon.schemas import (
    COMMON_ERROR_RESPONSES,
    GetSettingsResult,
    SuccessResponse,
    UpdateSettingsRequest,
    UpdateSettingsResult,
)
from economicon.services.data.dependencies import SettingsStoreDep
from economicon.services.operation import run_operation
from economicon.services.settings.get_settings import GetSettings
from economicon.services.settings.update_settings import UpdateSettings
from economicon.utils import create_success_response

router = APIRouter(
    prefix="/settings",
    tags=["settings"],
    responses=COMMON_ERROR_RESPONSES,
)


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


@router.put("", response_model=SuccessResponse[UpdateSettingsResult])
async def update_settings(
    request: Request,
    body: UpdateSettingsRequest,
    settings_store: SettingsStoreDep,
):
    """アプリケーション設定を更新するエンドポイント

    指定されたフィールドのみを部分更新します。省略したフィールドは
    現在の値を維持します。更新後の設定全体をレスポンスとして返します。

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : UpdateSettingsRequest
        更新するフィールドを含むリクエストボディ（すべて省略可能）
    settings_store : SettingsStoreDep
        依存注入された設定ストア

    Returns
    -------
    JSONResponse
        更新後の設定情報
    """
    api = UpdateSettings(body, settings_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )
