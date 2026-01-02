from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.export_excel_by_path import export_excel_by_path
from ..services import ApiError
from ..schemas import ExportExcelByPathRequest

router = APIRouter()


@router.post("/export-excel-by-path")
async def export_excel_by_path_endpoint(request: Request, body: ExportExcelByPathRequest):
    """テーブルをExcelファイルにパス指定でエクスポートするエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : ExportExcelByPathRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    try:
        create_log_api_request(request)

        result = export_excel_by_path(
            table_name=body.tableName,
            directory_path=body.directoryPath,
            file_name=body.fileName
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
        message = _("An unexpected error occurred during EXCEL export processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
