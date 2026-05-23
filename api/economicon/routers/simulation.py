"""シミュレーションエンドポイント"""

from fastapi import APIRouter, Request
from fastapi import status as http_status

from economicon.schemas import COMMON_ERROR_RESPONSES, SuccessResponse
from economicon.schemas.simulation import (
    AsymptoticNormalityRequestBody,
    AsymptoticNormalityResult,
    ConfidenceIntervalSimRequestBody,
    ConfidenceIntervalSimResult,
    ConsistencyRequestBody,
    ConsistencyResult,
    UnbiasednessRequestBody,
    UnbiasednessResult,
)
from economicon.services.operation import run_operation
from economicon.services.simulation.asymptotic_normality import (
    AsymptoticNormality,
)
from economicon.services.simulation.confidence_interval_sim import (
    ConfidenceIntervalSim,
)
from economicon.services.simulation.consistency import Consistency
from economicon.services.simulation.unbiasedness import Unbiasedness
from economicon.utils import create_success_response

router = APIRouter(
    prefix="/simulation",
    tags=["simulation"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.post(
    "/confidence-interval",
    response_model=SuccessResponse[ConfidenceIntervalSimResult],
)
async def confidence_interval_sim(
    request: Request,
    body: ConfidenceIntervalSimRequestBody,
):
    """信頼区間シミュレーション

    M 回サンプリングを行い、各試行の信頼区間と
    真の値との包含関係を返す。
    """
    api = ConfidenceIntervalSim(body)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK,
        response_object=result,
    )


@router.post(
    "/asymptotic-normality",
    response_model=SuccessResponse[AsymptoticNormalityResult],
)
async def asymptotic_normality(
    request: Request,
    body: AsymptoticNormalityRequestBody,
):
    """漸近正規性シミュレーション

    同一パラメータで num_simulations 回 OLS を行い、
    β̂ の標本分布と漸近分布の理論値を返す。
    """
    api = AsymptoticNormality(body)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK,
        response_object=result,
    )


@router.post(
    "/consistency",
    response_model=SuccessResponse[ConsistencyResult],
)
async def consistency(
    request: Request,
    body: ConsistencyRequestBody,
):
    """一致性シミュレーション

    n=2 から n_max まで逐次 OLS を行い、
    サンプルサイズ増加に伴う β̂ の収束軌跡を返す。
    """
    api = Consistency(body)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK,
        response_object=result,
    )


@router.post(
    "/unbiasedness",
    response_model=SuccessResponse[UnbiasednessResult],
)
async def unbiasedness(
    request: Request,
    body: UnbiasednessRequestBody,
):
    """不偏性シミュレーション

    同一母集団から num_trials 回独立にサンプリングして
    OLS を行い、β̂ の標本分布を返す。
    """
    api = Unbiasedness(body)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK,
        response_object=result,
    )
