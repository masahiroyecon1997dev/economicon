"""分布関連エンドポイント"""

from fastapi import APIRouter, Request
from fastapi import status as http_status

from economicon.schemas import (
    COMMON_ERROR_RESPONSES,
    DistributionPreviewRequestBody,
    DistributionPreviewResult,
    SuccessResponse,
)
from economicon.services.distribution.distribution_preview import (
    DistributionPreview,
)
from economicon.services.operation import run_operation
from economicon.utils import create_success_response

router = APIRouter(
    prefix="/distribution",
    tags=["distribution"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.post(
    "/preview",
    response_model=SuccessResponse[DistributionPreviewResult],
)
async def preview_distribution(
    request: Request,
    body: DistributionPreviewRequestBody,
):
    """分布プレビュー計算エンドポイント"""
    api = DistributionPreview(body)
    result = run_operation(api)
    return create_success_response(
        status_code=http_status.HTTP_200_OK,
        response_object=result,
    )
