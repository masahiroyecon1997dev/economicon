from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.create_join_table import create_join_table
from ..services import ApiError
from ..schemas import CreateJoinTableRequest

router = APIRouter()


@router.post("/create-join-table")
async def create_join_table_endpoint(request: Request, body: CreateJoinTableRequest):
    """結合テーブルを作成するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : CreateJoinTableRequest
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
        result = create_join_table(
            join_table_name=body.joinTableName,
            left_table_name=body.leftTableName,
            right_table_name=body.rightTableName,
            left_key_column_names=body.leftKeyColumnNames,
            right_key_column_names=body.rightKeyColumnNames,
            join_type=body.joinType
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
        message = _("An unexpected error occurred during join table creation processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
