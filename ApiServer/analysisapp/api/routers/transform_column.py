from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.transform_column import transform_column
from ..services import ApiError
from ..schemas import OperationsTransformColumnRequest

router = APIRouter()


@router.post("/transform-column")
async def transform_column_endpoint(request: Request, body: OperationsTransformColumnRequest):
    """
    列の変換処理エンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : OperationsTransformColumnRequest
        リクエストボディ
        - tableName: テーブル名
        - sourceColumnName: 変換元の列名
        - newColumnName: 新しい列名
        - transformMethod: 変換メソッド
        - logBase: 対数の底（オプション）
        - exponent: 指数（オプション）
        - rootIndex: 累乗根の次数（オプション）

    Returns
    -------
    JSONResponse
        処理結果
    """
    try:
        create_log_api_request(request)

        result = transform_column(
            table_name=body.tableName,
            source_column_name=body.sourceColumnName,
            new_column_name=body.newColumnName,
            transform_method=body.transformMethod,
            log_base=body.logBase,
            exponent=body.exponent,
            root_index=body.rootIndex
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
        message = _("An unexpected error occurred during column transformation processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
