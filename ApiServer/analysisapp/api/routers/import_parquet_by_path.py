from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.import_parquet_by_path import import_parquet_by_path
from ..services import ApiError
from ..schemas import ImportParquetByPathRequest

router = APIRouter()


@router.post("/import-parquet-by-path")
async def import_parquet_by_path_endpoint(request: Request, body: ImportParquetByPathRequest):
    """
    PARQUETファイルをパス指定でインポートしてテーブルを作成する

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : ImportParquetByPathRequest
        リクエストボディ
        - filePath: PARQUETファイルのパス
        - tableName: 作成するテーブル名

    Returns
    -------
    JSONResponse
        処理結果
    """
    try:
        create_log_api_request(request)

        result = import_parquet_by_path(
            file_path=body.filePath,
            table_name=body.tableName
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
        message = _("An unexpected error occurred during PARQUET import processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
