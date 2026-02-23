"""統計解析関連のスキーマ定義"""

from typing import Annotated, Any

from pydantic import Field

from .common import BaseRequest, BaseResult
from .enums import (
    ConfidenceIntervalStatisticsType,
    DescriptiveStatisticType,
)
from .types import ColumnName, TableName

# ---------------------------------------------------------------------------
# リクエストボディ
# ---------------------------------------------------------------------------


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
        list[ColumnName],
        Field(
            title="Column Name List",
            description="記述統計を計算する対象カラム名のリスト。テーブル内に存在するカラム名を指定してください。複数カラムを指定することもできます。",
            min_length=1,
        ),
    ]
    statistics: Annotated[
        list[DescriptiveStatisticType],
        Field(
            title="Statistics",
            description="計算する統計量のリスト"
            "（mean: 平均、median: 中央値、mode: 最頻値、"
            "variance: 分散、std_dev: 標準偏差、"
            "range: 範囲、iqr: 四分位数範囲）",
            min_length=1,
        ),
    ]


# ---------------------------------------------------------------------------
# レスポンス（Result）
# ---------------------------------------------------------------------------


class StatisticValue(BaseResult):
    """統計量の種別と値"""

    type: str = Field(
        title="Type",
        description="統計量のタイプ（mean, median 等）",
    )
    value: Any = Field(
        title="Value",
        description="統計量の計算値",
    )


class ConfidenceIntervalBounds(BaseResult):
    """信頼区間の下限・上限"""

    lower: float = Field(
        title="Lower",
        description="信頼区間の下限値",
    )
    upper: float = Field(
        title="Upper",
        description="信頼区間の上限値",
    )


class ConfidenceIntervalResult(BaseResult):
    """信頼区間計算レスポンス"""

    table_name: str = Field(
        title="Table Name",
        description="計算対象のテーブル名",
    )
    column_name: str = Field(
        title="Column Name",
        description="計算対象のカラム名",
    )
    statistic: StatisticValue = Field(
        title="Statistic",
        description="計算した統計量のタイプと値",
    )
    confidence_interval: ConfidenceIntervalBounds = Field(
        title="Confidence Interval",
        description="信頼区間の下限値と上限値",
    )
    confidence_level: float = Field(
        title="Confidence Level",
        description="計算に使用した信頼水準",
    )


class DescriptiveStatisticsResult(BaseResult):
    """記述統計レスポンス"""

    table_name: str = Field(
        title="Table Name",
        description="計算対象のテーブル名",
    )
    statistics: Any = Field(
        title="Statistics",
        description="記述統計の計算結果。カラム名と統計量名をキーに持つ辞書型データ。",
    )
