"""統計解析関連のスキーマ定義"""

from typing import Annotated, List

from pydantic import Field

from .common import BaseRequest
from .types import ColumnName, TableName


class ConfidenceIntervalRequestBody(BaseRequest):
    """信頼区間計算リクエスト"""

    table_name: TableName
    column_name: Annotated[
        ColumnName,
        Field(
            description="対象カラム名",
        ),
    ]
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


class DescriptiveStatisticsRequestBody(BaseRequest):
    """記述統計リクエスト"""

    table_name: TableName
    column_name_list: List[
        Annotated[ColumnName, Field(description="対象カラム名のリスト")]
    ]
    statistics: List[str] = Field(
        ..., description="統計量のリスト", min_length=1
    )
