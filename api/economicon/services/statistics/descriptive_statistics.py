import polars as pl

from ...i18n.translation import gettext as _
from ...models import (
    DescriptiveStatisticsRequestBody,
    DescriptiveStatisticType,
)
from ...utils import ProcessingError, ValidationError
from ...utils.validators import validate_existence
from ..data.tables_store import TablesStore


class DescriptiveStatistics:
    """
    指定されたテーブルの列の記述統計を計算するためのAPIクラス

    指定されたテーブルの指定された列に対して、要求された記述統計を計算します。
    サポートする統計: 平均、最頻値、中央値、分散、標準偏差、範囲、四分位範囲
    """

    stat_map = {
        DescriptiveStatisticType.MEAN: lambda c: pl.col(c).mean(),
        DescriptiveStatisticType.MEDIAN: lambda c: pl.col(c).median(),
        DescriptiveStatisticType.MODE: lambda c: pl.col(c).mode().first(),
        DescriptiveStatisticType.VARIANCE: lambda c: pl.col(c).var(),
        DescriptiveStatisticType.STD_DEV: lambda c: pl.col(c).std(),
        DescriptiveStatisticType.RANGE: lambda c: (
            pl.col(c).max() - pl.col(c).min()
        ),
        DescriptiveStatisticType.IQR: lambda c: (
            pl.col(c).quantile(0.75) - pl.col(c).quantile(0.25)
        ),
    }

    def __init__(
        self,
        body: DescriptiveStatisticsRequestBody,
    ):
        self.tables_store = TablesStore()
        self.table_name = body.table_name
        self.column_name_list = body.column_name_list
        self.statistics = body.statistics
        self.param_names = {
            "table_name": "tableName",
            "column_names": "columnName",
            "statistics": "statistics",
        }

    def validate(self):
        try:
            table_name_list = self.tables_store.get_table_name_list()
            validate_existence(
                value=self.table_name,
                valid_list=table_name_list,
                target=self.param_names["table_name"],
            )
            column_name_list = self.tables_store.get_column_name_list(
                self.table_name
            )
            validate_existence(
                value=self.column_name_list,
                valid_list=column_name_list,
                target=self.param_names["column_names"],
            )

            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            result = {}

            expressions = []
            for column_name in self.column_name_list:
                for stat in self.statistics:
                    if stat in self.stat_map:
                        expr = df.select(self.stat_map[stat](column_name))
                        expressions.append((stat, column_name, expr))

            # 結果を返す
            result = {
                "tableName": self.table_name,
                "statistics": df.select(expressions),
            }
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during descriptive statistics processing"
            )
            raise ProcessingError(
                error_code="DESCRIPTIVE_STATISTICS_ERROR",
                message=message,
                detail=str(e),
            ) from e
