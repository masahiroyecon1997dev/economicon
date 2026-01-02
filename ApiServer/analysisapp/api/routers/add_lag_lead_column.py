from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.add_lag_lead_column import add_lag_lead_column
from ..services import ApiError
from ..schemas import AddLagLeadColumnRequest

# ルーターの作成
router = APIRouter()


@router.post("/add-lag-lead-column")
async def add_lag_lead_column_endpoint(request: Request, body: AddLagLeadColumnRequest):
    """ラグ・リードカラムを追加するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : AddLagLeadColumnRequest
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
        result = add_lag_lead_column(
            table_name=body.tableName,
            source_column=body.sourceColumn,
            new_column_name=body.newColumnName,
            periods=body.periods,
            group_columns=body.groupColumns
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
        message = _("An unexpected error occurred during adding lag/lead column processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
