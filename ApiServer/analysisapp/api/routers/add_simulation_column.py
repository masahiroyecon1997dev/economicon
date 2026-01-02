from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.add_simulation_column import add_simulation_column
from ..services import ApiError
from ..schemas import AddSimulationColumnRequest

# ルーターの作成
router = APIRouter()


@router.post("/add-simulation-column")
async def add_simulation_column_endpoint(request: Request, body: AddSimulationColumnRequest):
    """シミュレーションカラムを追加するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : AddSimulationColumnRequest
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
        result = add_simulation_column(
            table_name=body.tableName,
            new_column_name=body.newColumnName,
            distribution_type=body.distributionType,
            distribution_params=body.distributionParams
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

    except KeyError as e:
        message = _("Missing required parameter: {key}").format(key=str(e))
        return create_error_response(
            http_status.HTTP_400_BAD_REQUEST,
            message
        )

    except Exception as e:
        message = _("An unexpected error occurred during adding simulation column processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
