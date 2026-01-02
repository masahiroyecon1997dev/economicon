from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.add_dummy_column import add_dummy_column
from ..services import ApiError
from ..schemas import AddDummyColumnRequest

# ルーターの作成
router = APIRouter()


@router.post("/add-dummy-column")
async def add_dummy_column_endpoint(request: Request, body: AddDummyColumnRequest):
    """ダミー変数カラムを追加するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : AddDummyColumnRequest
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
        result = add_dummy_column(
            table_name=body.tableName,
            source_column_name=body.sourceColumnName,
            dummy_column_name=body.dummyColumnName,
            target_value=body.targetValue
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
        message = _("An unexpected error occurred during adding dummy column processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
