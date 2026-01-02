from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.export_csv_by_path import export_csv_by_path
from ..services import ApiError
from ..schemas import ExportCsvByPathRequest

router = APIRouter()


@router.post("/export-csv-by-path")
async def export_csv_by_path_endpoint(request: Request, body: ExportCsvByPathRequest):
    """テーブルをCSVファイルにパス指定でエクスポートするエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : ExportCsvByPathRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    try:
        create_log_api_request(request)

        result = export_csv_by_path(
            table_name=body.tableName,
            directory_path=body.directoryPath,
            file_name=body.fileName,
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
        message = _("An unexpected error occurred during CSV export processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
