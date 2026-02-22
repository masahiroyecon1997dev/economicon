"""統計解析関連のスキーマ定義"""

from typing import Annotated, List

from pydantic import Field

from .common import BaseRequest
from .enums import (
    ConfidenceIntervalStatisticsType,
    DescriptiveStatisticType,
)
from .types import ColumnName, TableName


class ConfidenceIntervalRequestBody(BaseRequest):
    """信頼区間計算リクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            title="Table Name",
            description="信頼区間を計算する対象テーブル名。ワークスペース内に存在するテーブル名を指定してください。",
        ),
    ]
    column_name: Annotated[
        ColumnName,
        Field(
            title="Column Name",
            description="信頼区間を計算する対象カラム名。テーブル内に存在するカラム名を指定してください。",
        ),
    ]
    confidence_level: Annotated[
        float,
        Field(
            title="Confidence Level",
            description="信頼水準（例: 0.95 = 95%信頼区間）",
            gt=0.0,
            lt=1.0,
        ),
    ]
    statistic_type: Annotated[
        ConfidenceIntervalStatisticsType,
        Field(
            title="Statistic Type",
            description="信頼区間を計算する統計量のタイプ。"
            "（mean: 平均、median: 中央値、proportion: 割合、"
            "variance: 分散、standard_deviation: 標準偏差）",
        ),
    ]


class DescriptiveStatisticsRequestBody(BaseRequest):
    """記述統計リクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            title="Table Name",
            description="記述統計を計算する対象テーブル名。ワークスペース内に存在するテーブル名を指定してください。",
        ),
    ]
    column_name_list: Annotated[
        List[ColumnName],
        Field(
            title="Column Name List",
            description="記述統計を計算する対象カラム名のリスト。テーブル内に存在するカラム名を指定してください。複数カラムを指定することもできます。",
            min_length=1,
        ),
    ]
    statistics: Annotated[
        List[DescriptiveStatisticType],
        Field(
            title="Statistics",
            description="計算する統計量のリスト"
            "（mean: 平均、median: 中央値、mode: 最頻値、"
            "variance: 分散、std_dev: 標準偏差、range: 範囲、iqr: 四分位数範囲）",
            min_length=1,
        ),
    ]
