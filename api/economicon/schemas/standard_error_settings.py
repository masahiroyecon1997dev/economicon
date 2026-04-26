"""標準誤差設定関連のスキーマ定義。"""

from typing import Annotated, Literal

from pydantic import Field

from economicon.schemas.common import BaseRequest
from economicon.schemas.enums import StandardErrorMethodType
from economicon.schemas.types import ColumnName


class NonRobustStandardError(BaseRequest):
    method: Literal[StandardErrorMethodType.NONROBUST] = (
        StandardErrorMethodType.NONROBUST
    )


class RobustStandardError(BaseRequest):
    method: Literal[StandardErrorMethodType.ROBUST] = (
        StandardErrorMethodType.ROBUST
    )
    hc_type: Literal["HC0", "HC1", "HC2", "HC3"] = Field(default="HC1")


class ClusteredStandardError(BaseRequest):
    method: Literal[StandardErrorMethodType.CLUSTER] = (
        StandardErrorMethodType.CLUSTER
    )
    groups: list[ColumnName] = Field(description="クラスターを構成する列名")
    use_correction: bool = Field(
        default=True, description="小標本補正を行うか"
    )


class HacStandardError(BaseRequest):
    method: Literal[StandardErrorMethodType.HAC] = StandardErrorMethodType.HAC
    maxlags: int = Field(..., ge=0, description="考慮する最大ラグ数")
    kernel: str = Field(default="bartlett", description="カーネルの種類")
    use_correction: bool = Field(
        default=True, description="小標本補正を行うか"
    )


type StandardErrorSettings = Annotated[
    NonRobustStandardError
    | RobustStandardError
    | ClusteredStandardError
    | HacStandardError,
    Field(discriminator="method"),
]


__all__ = [
    "NonRobustStandardError",
    "RobustStandardError",
    "ClusteredStandardError",
    "HacStandardError",
    "StandardErrorSettings",
]
