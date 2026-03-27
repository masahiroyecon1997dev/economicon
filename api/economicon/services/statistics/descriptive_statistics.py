from typing import ClassVar

import polars as pl

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas import (
    DescriptiveStatisticsRequestBody,
    DescriptiveStatisticType,
)
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import validate_existence


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

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "table_name": "tableName",
        "column_names": "columnName",
        "statistics": "statistics",
    }

    def __init__(
        self,
        body: DescriptiveStatisticsRequestBody,
        tables_store: TablesStore,
    ):
        self.tables_store = tables_store
        self.table_name = body.table_name
        self.column_name_list = body.column_name_list
        self.statistics = body.statistics

    def validate(self):
        table_name_list = self.tables_store.get_table_name_list()
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.PARAM_NAMES["table_name"],
        )
        column_name_list = self.tables_store.get_column_name_list(
            self.table_name
        )
        validate_existence(
            value=self.column_name_list,
            valid_list=column_name_list,
            target=self.PARAM_NAMES["column_names"],
        )

    def execute(self):
        try:
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            stats_result = {}
            for column_name in self.column_name_list:
                col_stats = {}
                for stat in self.statistics:
                    if stat not in self.stat_map:
                        col_stats[stat.value] = None
                        continue
                    try:
                        expr = self.stat_map[stat](column_name)
                        val = df.select(expr).to_series(0)[0]
                        col_stats[stat.value] = val
                    except Exception:
                        col_stats[stat.value] = None
                stats_result[column_name] = col_stats

            return {
                "tableName": self.table_name,
                "statistics": stats_result,
            }
        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "descriptive statistics processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.DESCRIPTIVE_STATISTICS_ERROR,
                message=message,
                detail=str(e),
            ) from e
