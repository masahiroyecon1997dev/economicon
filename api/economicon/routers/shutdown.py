from fastapi import APIRouter, Request
from fastapi import status as http_status

from economicon.models import (
    COMMON_ERROR_RESPONSES,
    ShutdownResult,
    SuccessResponse,
)
from economicon.services.data.dependencies import (
    AnalysisResultStoreDep,
    SettingsStoreDep,
)
from economicon.services.operation import run_operation
from economicon.services.shutdown.shutdown import Shutdown
from economicon.utils import create_success_response

router = APIRouter(
    prefix="/shutdown",
    tags=["shutdown"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.post("", response_model=SuccessResponse[ShutdownResult])
async def shutdown(
    request: Request,
    analysis_result_store: AnalysisResultStoreDep,
    settings_store: SettingsStoreDep,
):
    """アプリ終了前クリーンアップエンドポイント

    フロントエンドの CloseRequested ハンドラから呼び出される。
    分析結果ファイルの削除と設定の保存を行う。

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    analysis_result_store : AnalysisResultStoreDep
        依存注入された分析結果ストア
    settings_store : SettingsStoreDep
        依存注入された設定ストア

    Returns
    -------
    JSONResponse
        処理結果
    """
    api = Shutdown(analysis_result_store, settings_store)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK, response_object=result
    )
