from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.filter_single_condition import filter_single_condition
from ..services import ApiError
from ..schemas import FilterSingleConditionRequest

router = APIRouter()


@router.post("/filter-single-condition")
async def filter_single_condition_endpoint(request: Request, body: FilterSingleConditionRequest):
    """単一条件フィルタリングを実行するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : FilterSingleConditionRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    try:
        create_log_api_request(request)

        result = filter_single_condition(
            new_table_name=body.newTableName,
            table_name=body.tableName,
            column_name=body.columnName,
            condition=body.condition,
            is_compare_column=body.isCompareColumn,
            compare_value=body.compareValue
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
        message = _("An unexpected error occurred during filter processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
