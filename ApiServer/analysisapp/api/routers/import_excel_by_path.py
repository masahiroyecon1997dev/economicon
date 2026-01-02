from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.import_excel_by_path import import_excel_by_path
from ..services import ApiError
from ..schemas import ImportExcelByPathRequest

router = APIRouter()


@router.post("/import-excel-by-path")
async def import_excel_by_path_endpoint(request: Request, body: ImportExcelByPathRequest):
    """
    EXCELファイルをパス指定でインポートしてテーブルを作成する

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : ImportExcelByPathRequest
        リクエストボディ
        - filePath: EXCELファイルのパス
        - tableName: 作成するテーブル名
        - sheetName: シート名（オプション）

    Returns
    -------
    JSONResponse
        処理結果
    """
    try:
        create_log_api_request(request)

        result = import_excel_by_path(
            file_path=body.filePath,
            table_name=body.tableName,
            sheet_name=body.sheetName
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
        message = _("An unexpected error occurred during EXCEL import processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
