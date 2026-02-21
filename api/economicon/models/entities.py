# app/schema/entities.py
from pydantic import BaseModel

from .types import DistributionConfig, NewColumnName


class SimulationColumnConfig(BaseModel):
    """
    新しい列名とその生成規則のペア。
    複数のAPI（列追加、シミュレーション設定等）で共通利用される。
    """

    column_name: NewColumnName
    distribution: DistributionConfig
