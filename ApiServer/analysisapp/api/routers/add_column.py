"""Add Column API - FastAPI版

Django REST FrameworkからFastAPIへの移行サンプル
"""
from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.add_column import add_column
from ..services import ApiError
from ..schemas import AddColumnRequest

# ルーターの作成
router = APIRouter()


@router.post("/add-column")
async def add_column_endpoint(request: Request, body: AddColumnRequest):
    """カラムを追加するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : AddColumnRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    try:
        # リクエスト受け取りログ
        create_log_api_request(request)

        # ビジネスロジックの実行（既存のpython_apisをそのまま使用）
        result = add_column(
            table_name=body.tableName,
            new_column_name=body.newColumnName,
            add_position_column=body.addPositionColumn
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
        message = _("An unexpected error occurred during adding column processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
