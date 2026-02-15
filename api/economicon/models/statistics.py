"""統計解析関連のスキーマ定義"""

from typing import List

from pydantic import BaseModel, ConfigDict, Field


class ConfidenceIntervalRequestBody(BaseModel):
    """信頼区間計算リクエスト"""

    table_name: str = Field(
        ...,
        alias="tableName",
        description="テーブル名",
        min_length=1,
        max_length=255,
    )
    column_name: str = Field(
        ...,
        alias="columnName",
        description="対象カラム名",
        min_length=1,
        max_length=255,
    )
    confidence_level: float = Field(
        ...,
        alias="confidenceLevel",
        description="信頼水準 (例: 0.95)",
        gt=0.0,
        lt=1.0,
    )
    statistic_type: str = Field(
        ...,
        alias="statisticType",
        description="統計量のタイプ (mean, median, etc.)",
        min_length=1,
        max_length=50,
    )

    model_config = ConfigDict(populate_by_name=True)


class DescriptiveStatisticsRequestBody(BaseModel):
    """記述統計リクエスト"""

    table_name: str = Field(
        ...,
        alias="tableName",
        description="テーブル名",
        min_length=1,
        max_length=255,
    )
    column_name_list: List[str] = Field(
        ...,
        alias="columnNameList",
        description="対象カラム名のリスト",
        min_length=1,
    )
    statistics: List[str] = Field(
        ..., description="統計量のリスト", min_length=1
    )

    model_config = ConfigDict(populate_by_name=True)
