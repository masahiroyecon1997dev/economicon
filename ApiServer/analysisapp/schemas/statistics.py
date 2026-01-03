"""統計解析関連のスキーマ定義"""
from pydantic import BaseModel, Field
from .common import TableRequest
from typing import List


class ConfidenceIntervalRequest(TableRequest):
    """信頼区間計算リクエスト"""
    columnName: str = Field(..., description="対象カラム名")
    confidenceLevel: float = Field(..., description="信頼水準 (例: 0.95)")
    statisticType: str = Field(..., description="統計量のタイプ (mean, median, etc.)")


class DescriptiveStatisticsRequest(TableRequest):
    """記述統計リクエスト"""
    columnNameList: List[str] = Field(..., description="対象カラム名のリスト")
    statistics: List[str] = Field(..., description="統計量のリスト")
