from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.import_csv_by_path import import_csv_by_path
from ..services import ApiError
from ..schemas import ImportCsvByPathRequest

router = APIRouter()


@router.post("/import-csv-by-path")
async def import_csv_by_path_endpoint(request: Request, body: ImportCsvByPathRequest):
    """パス指定でCSVファイルをインポートするエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : ImportCsvByPathRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    try:
        create_log_api_request(request)

        result = import_csv_by_path(
            file_path=body.filePath,
            table_name=body.tableName,
            separator=body.separator
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
        message = _("An unexpected error occurred during CSV import processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
