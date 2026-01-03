from fastapi import APIRouter, Request, UploadFile, File, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.import_tsv_by_file import import_tsv_by_file
from ..services import ApiError

router = APIRouter()


@router.post("/import-tsv-by-file")
async def import_tsv_by_file_endpoint(request: Request, file: UploadFile = File(...)):
    """
    アップロードされたTSVファイルをインポートしてテーブルを作成する

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    file : UploadFile
        アップロードされたTSVファイル

    Returns
    -------
    JSONResponse
        処理結果
    """
    try:
        create_log_api_request(request)

        result = import_tsv_by_file(
            file_data=file.file,
            file_name=file.filename
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
        message = _("An unexpected error occurred during TSV import processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
