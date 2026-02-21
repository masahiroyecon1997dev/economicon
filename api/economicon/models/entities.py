# app/schema/entities.py

from .common import BaseRequest
from .types import ColumnName, DistributionConfig, NewColumnName


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
