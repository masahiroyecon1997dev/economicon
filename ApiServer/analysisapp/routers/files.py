from fastapi import APIRouter, Request, status as http_status

from ..utils import create_success_response, create_log_api_request
from ..services.get_files import get_files

router = APIRouter(prefix="/file", tags=["file"])


@router.get("/list")
async def get_files_endpoint(request: Request, directoryPath: str):
    """ファイル一覧を取得するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    directoryPath : str
        ディレクトリパス

    Returns
    -------
    JSONResponse
        処理結果
    """
    create_log_api_request(request)

    result = get_files(directory_path=directoryPath)

    return create_success_response(
        http_status.HTTP_200_OK,
        result
    )
