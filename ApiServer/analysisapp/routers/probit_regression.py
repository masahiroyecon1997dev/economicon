from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.probit_regression import probit_regression
from ..services import ApiError
from ..schemas import ProbitRegressionRequest

router = APIRouter()


@router.post("/probit-regression")
async def probit_regression_endpoint(request: Request, body: ProbitRegressionRequest):
    """
    プロビット分析を実行するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : ProbitRegressionRequest
        リクエストボディ
        - tableName: テーブル名
        - dependentVariable: 被説明変数の列名
        - explanatoryVariables: 説明変数の列名リスト

    Returns
    -------
    JSONResponse
        プロビット分析の結果
    """
    try:
        create_log_api_request(request)

        result = probit_regression(
            table_name=body.tableName,
            dependent_variable=body.dependentVariable,
            explanatory_variables=body.explanatoryVariables
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
        message = _("An unexpected error occurred during probit regression processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
