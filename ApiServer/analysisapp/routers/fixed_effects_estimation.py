from fastapi import APIRouter, Request, status as http_status

from ..i18n import _
from ..utils import create_success_response, create_error_response, create_log_api_request
from ..utils.validator import ValidationError
from ..services.fixed_effects_estimation import fixed_effects_estimation
from ..services import ApiError
from ..schemas import FixedEffectsEstimationRequest

router = APIRouter()


@router.post("/fixed-effects-estimation")
async def fixed_effects_estimation_endpoint(request: Request, body: FixedEffectsEstimationRequest):
    """固定効果推定を実行するエンドポイント

    Parameters
    ----------
    request : Request
        FastAPIのリクエストオブジェクト
    body : FixedEffectsEstimationRequest
        リクエストボディ

    Returns
    -------
    JSONResponse
        処理結果
    """
    try:
        create_log_api_request(request)

        result = fixed_effects_estimation(
            table_name=body.tableName,
            dependent_variable=body.dependentVariable,
            explanatory_variables=body.explanatoryVariables,
            entity_id_column=body.entityIdColumn,
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

    except KeyError as e:
        message = _("Required parameter is missing: {}").format(str(e))
        return create_error_response(
            http_status.HTTP_400_BAD_REQUEST,
            message
        )

    except Exception as e:
        message = _("An unexpected error occurred during fixed effects estimation processing")
        return create_error_response(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            e
        )
