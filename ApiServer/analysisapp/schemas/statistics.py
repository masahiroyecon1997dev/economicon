"""統計解析関連のスキーマ定義"""
from typing import List

from pydantic import BaseModel, Field


class ConfidenceIntervalRequest(BaseModel):
    """信頼区間計算リクエスト"""
    tableName: str = Field(..., description="テーブル名")
    columnName: str = Field(..., description="対象カラム名")
    confidenceLevel: float = Field(..., description="信頼水準 (例: 0.95)")
    statisticType: str = Field(
        ...,
        description="統計量のタイプ (mean, median, etc.)"
    )


class DescriptiveStatisticsRequest(BaseModel):
    """記述統計リクエスト"""
    tableName: str = Field(..., description="テーブル名")
    columnNameList: List[str] = Field(..., description="対象カラム名のリスト")
    statistics: List[str] = Field(..., description="統計量のリスト")
