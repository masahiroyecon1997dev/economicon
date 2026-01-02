from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.create_simulation_data_table import create_simulation_data_table
from ..services import ApiError
from ..schemas import CreateSimulationDataTableRequest

router = APIRouter()


@router.post("/create-simulation-data-table")
async def create_simulation_data_table_endpoint(request: Request, body: CreateSimulationDataTableRequest):
    """シミュレーションデータテーブルを作成するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : CreateSimulationDataTableRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    try:
        # リクエスト受け取りログ
        create_log_api_request(request)

        # ビジネスロジックの実行
        result = create_simulation_data_table(
            table_name=body.tableName,
            num_rows=body.tableNumberOfRows,
            column_settings=body.columnSettings
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
        message = _("An unexpected error occurred during table creation processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
