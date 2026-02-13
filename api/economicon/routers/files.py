from fastapi import APIRouter, Request
from fastapi import status as http_status

from ..models import GetFilesRequest
from ..services.files.get_files import get_files
from ..utils import create_log_api_request, create_success_response

router = APIRouter(prefix="/file", tags=["file"])


@router.post("/get-list")
async def get_files(request: Request, body: GetFilesRequest):
    """ファイル一覧を取得するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : GetFilesRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    create_log_api_request(request)

    result = get_files(**body.model_dump())

    return create_success_response(http_status.HTTP_200_OK, result)
