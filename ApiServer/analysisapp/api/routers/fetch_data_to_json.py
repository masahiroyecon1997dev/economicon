from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.fetch_data_to_json import fetch_data_to_json
from ..services import ApiError

router = APIRouter()


@router.get("/fetch-data-to-json")
async def fetch_data_to_json_endpoint(request: Request, tableName: str, startRow: int, fetchRows: int):
    """データをJSON形式で取得するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    tableName : str
        テーブル名
    startRow : int
        開始行番号
    fetchRows : int
        取得行数

    Returns
    -------
    JSONResponse
        処理結果
    """
    try:
        create_log_api_request(request)

        result = fetch_data_to_json(
            table_name=tableName,
            start_row=startRow,
            fetch_rows=fetchRows
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
        message = _("An unexpected error occurred during fetching data processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
