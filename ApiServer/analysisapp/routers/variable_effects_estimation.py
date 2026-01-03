from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.variable_effects_estimation import variable_effects_estimation
from ..services import ApiError
from ..schemas import VariableEffectsEstimationRequest

router = APIRouter()


@router.post("/variable-effects-estimation")
async def variable_effects_estimation_endpoint(request: Request, body: VariableEffectsEstimationRequest):
    """
    変量効果推定分析を実行するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : VariableEffectsEstimationRequest
        リクエストボディ
        - tableName: テーブル名
        - dependentVariable: 被説明変数の列名
        - explanatoryVariables: 説明変数の列名リスト
        - standardErrorMethod: 標準誤差の計算方法（オプション、デフォルト: "nonrobust"）
        - useTDistribution: t分布を使用するか（オプション、デフォルト: true）

    Returns
    -------
    JSONResponse
        変量効果推定分析の結果
    """
    try:
        create_log_api_request(request)

        result = variable_effects_estimation(
            table_name=body.tableName,
            dependent_variable=body.dependentVariable,
            explanatory_variables=body.explanatoryVariables,
            standard_error_method=body.standardErrorMethod,
            use_t_distribution=body.useTDistribution
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
        message = _("An unexpected error occurred during variable effects estimation processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
