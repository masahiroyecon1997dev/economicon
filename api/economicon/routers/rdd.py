"""
回帰不連続デザイン（RDD）分析エンドポイント

NOTE: rdrobust / rddensity は GPL ライセンスのため削除済み。
      エンドポイントは現在 501 Not Implemented を返す。
"""

from fastapi import APIRouter

from economicon.schemas import (
    COMMON_ERROR_RESPONSES,
    SuccessResponse,
)
from economicon.schemas.rdd import RDDRequestBody, RDDResult

router = APIRouter(
    prefix="/analysis",
    tags=["analysis"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.post("/rdd", response_model=SuccessResponse[RDDResult])
async def rdd_analysis(
    body: RDDRequestBody,
):
    """
    回帰不連続デザイン（RDD）分析エンドポイント

    NOTE: rdrobust / rddensity は GPL ライセンスのため削除済み。
    現在は 501 Not Implemented を返す。
    """
    raise NotImplementedError()
