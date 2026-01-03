from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.input_cell_data import input_cell_data
from ..services import ApiError
from ..schemas import InputCellDataRequest

router = APIRouter()


@router.post("/input-cell-data")
async def input_cell_data_endpoint(request: Request, body: InputCellDataRequest):
    """
    セルデータ入力エンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : InputCellDataRequest
        リクエストボディ
        - tableName: テーブル名
        - columnName: 列名
        - rowIndex: 行インデックス
        - newValue: 新しい値

    Returns
    -------
    JSONResponse
        処理結果
    """
    try:
        create_log_api_request(request)

        result = input_cell_data(
            body.tableName,
            body.columnName,
            body.rowIndex,
            body.newValue
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
        message = _("An unexpected error occurred during input cell data processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
