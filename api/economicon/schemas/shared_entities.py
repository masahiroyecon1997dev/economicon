"""複数ドメインで共有する小さな DTO 群。"""

from economicon.schemas.common import BaseRequest
from economicon.schemas.types import (
    ColumnName,
    DistributionConfig,
    NewColumnName,
)


class SimulationColumnConfig(BaseRequest):
    """
    新しい列名とその生成規則のペア。
    複数のAPI（列追加、シミュレーション設定等）で共通利用される。
    """

    column_name: NewColumnName
    distribution: DistributionConfig


class SortInstruction(BaseRequest):
    column_name: ColumnName
    ascending: bool


__all__ = ["SimulationColumnConfig", "SortInstruction"]
