"""分布プレビューリクエスト・レスポンススキーマ"""

from typing import Annotated

from pydantic import Field

from economicon.schemas.common import BaseRequest, BaseResult
from economicon.schemas.types import DistributionConfig


class DistributionPreviewRequestBody(BaseRequest):
    """分布プレビューリクエスト"""

    distribution: DistributionConfig
    x_count: Annotated[
        int,
        Field(
            default=200,
            ge=50,
            le=2000,
            description="グラフ点数（連続分布）",
        ),
    ] = 200


class DistributionPreviewResult(BaseResult):
    """分布プレビューレスポンス"""

    is_discrete: bool = Field(description="離散分布のとき True")
    x: list[float] = Field(description="X 軸の値のリスト")
    y_density: list[float] = Field(
        description="PDF（連続）または PMF（離散）の値"
    )
    y_cumulative: list[float] = Field(
        description="CDF（連続）または CMF（離散）の値"
    )
