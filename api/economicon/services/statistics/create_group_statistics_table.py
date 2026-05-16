"""GroupBy 統計テーブル作成サービス"""

from collections.abc import Callable
from typing import ClassVar

import polars as pl

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas import (
    CreateGroupStatisticsTableRequestBody,
    DescriptiveStatisticType,
)
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.exceptions import ValidationError
from economicon.utils.validators import (
    validate_existence,
    validate_no_overlap,
    validate_non_existence,
)

# GroupBy agg 内で直接使える統計量 (IQR・RANGE は一時列が必要なため除外)
_PLAIN_STAT_MAP: dict[DescriptiveStatisticType, Callable[[str], pl.Expr]] = {
    DescriptiveStatisticType.MEAN: lambda c: pl.col(c).mean(),
    DescriptiveStatisticType.MEDIAN: lambda c: pl.col(c).median(),
    DescriptiveStatisticType.MODE: lambda c: pl.col(c).mode().first(),
    DescriptiveStatisticType.VARIANCE: lambda c: pl.col(c).var(),
    DescriptiveStatisticType.STD_DEV: lambda c: pl.col(c).std(),
    DescriptiveStatisticType.COUNT: lambda c: pl.col(c).count(),
    DescriptiveStatisticType.NULL_COUNT: lambda c: pl.col(c).null_count(),
    DescriptiveStatisticType.NULL_RATIO: (
        lambda c: pl.col(c).is_null().mean()
    ),
    DescriptiveStatisticType.POPULATION_VARIANCE: (
        lambda c: pl.col(c).var(ddof=0)
    ),
    DescriptiveStatisticType.MIN: lambda c: pl.col(c).min(),
    DescriptiveStatisticType.MAX: lambda c: pl.col(c).max(),
    DescriptiveStatisticType.SKEWNESS: (lambda c: pl.col(c).skew(bias=True)),
    DescriptiveStatisticType.KURTOSIS: (
        lambda c: pl.col(c).kurtosis(fisher=True, bias=True)
    ),
}


class CreateGroupStatisticsTable:
    """GroupBy 後に記述統計を計算し新テーブルとして保存するサービス。

    結果テーブルの列名は ``{stat_column}__{stat_type}`` 形式。
    例: income__mean, income__std_dev

    IQR および RANGE は Polars の group_by().agg() 内で算術演算が
    制約される場合に備え、一時列経由で後処理として計算する。
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "table_name": "tableName",
        "group_by_columns": "groupByColumns",
        "stat_columns": "statColumns",
        "new_table_name": "newTableName",
    }

    def __init__(
        self,
        body: CreateGroupStatisticsTableRequestBody,
        tables_store: TablesStore,
    ) -> None:
        self.tables_store = tables_store
        self.table_name = body.table_name
        self.group_by_columns = body.group_by_columns
        self.stat_columns = body.stat_columns
        self.statistics = body.statistics
        self.new_table_name = body.new_table_name

    def validate(self) -> None:
        table_name_list = self.tables_store.get_table_name_list()

        # 元テーブルの存在チェック
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.PARAM_NAMES["table_name"],
        )
        # 新テーブル名の重複なしチェック
        validate_non_existence(
            value=self.new_table_name,
            existing_list=table_name_list,
            target=self.PARAM_NAMES["new_table_name"],
        )
        column_name_list = self.tables_store.get_column_name_list(
            self.table_name
        )
        # groupByColumns の存在チェック
        validate_existence(
            value=self.group_by_columns,
            valid_list=column_name_list,
            target=self.PARAM_NAMES["group_by_columns"],
        )
        # statColumns の存在チェック
        validate_existence(
            value=self.stat_columns,
            valid_list=column_name_list,
            target=self.PARAM_NAMES["stat_columns"],
        )
        # groupByColumns と statColumns の重複チェック
        validate_no_overlap(
            values=self.stat_columns,
            reserved=set(self.group_by_columns),
            target=self.PARAM_NAMES["stat_columns"],
            reserved_target=self.PARAM_NAMES["group_by_columns"],
        )
        # groupByColumns の型チェック（浮動小数点は不可）
        schema = self.tables_store.get_schema(self.table_name)
        float_cols = [
            col for col in self.group_by_columns if schema[col].is_float()
        ]
        if float_cols:
            raise ValidationError(
                error_code=ErrorCode.INVALID_DTYPE,
                message=_(
                    "The following columns cannot be used as group keys"
                    " because they are floating-point type: {}"
                ).format(", ".join(float_cols)),
                target=self.PARAM_NAMES["group_by_columns"],
            )

    def _build_agg_exprs(self) -> list[pl.Expr]:
        """統計量ごとの agg 式リストを構築する。

        IQR・RANGE は group_by().agg() 内での算術演算を避けるため
        一時列（``__q75__``, ``__q25__``, ``__rmax__``, ``__rmin__``）
        として追加し、後処理で差分を計算する。
        """
        exprs: list[pl.Expr] = []
        for col in self.stat_columns:
            for stat in self.statistics:
                if stat == DescriptiveStatisticType.IQR:
                    exprs.append(
                        pl.col(col).quantile(0.75).alias(f"__q75__{col}")
                    )
                    exprs.append(
                        pl.col(col).quantile(0.25).alias(f"__q25__{col}")
                    )
                elif stat == DescriptiveStatisticType.RANGE:
                    exprs.append(pl.col(col).max().alias(f"__rmax__{col}"))
                    exprs.append(pl.col(col).min().alias(f"__rmin__{col}"))
                elif stat in _PLAIN_STAT_MAP:
                    exprs.append(
                        _PLAIN_STAT_MAP[stat](col).alias(
                            f"{col}__{stat.value}"
                        )
                    )
        return exprs

    def _post_process(self, df: pl.DataFrame) -> pl.DataFrame:
        """IQR・RANGE の一時列を差分計算して最終列名に変換する。"""
        need_iqr = DescriptiveStatisticType.IQR in self.statistics
        need_range = DescriptiveStatisticType.RANGE in self.statistics
        for col in self.stat_columns:
            if need_iqr:
                df = df.with_columns(
                    (pl.col(f"__q75__{col}") - pl.col(f"__q25__{col}")).alias(
                        f"{col}__{DescriptiveStatisticType.IQR.value}"
                    )
                ).drop([f"__q75__{col}", f"__q25__{col}"])
            if need_range:
                df = df.with_columns(
                    (
                        pl.col(f"__rmax__{col}") - pl.col(f"__rmin__{col}")
                    ).alias(f"{col}__{DescriptiveStatisticType.RANGE.value}")
                ).drop([f"__rmax__{col}", f"__rmin__{col}"])
        return df

    def execute(self) -> dict[str, str]:
        try:
            df = self.tables_store.get_table(self.table_name).table

            result = df.group_by(
                self.group_by_columns, maintain_order=True
            ).agg(self._build_agg_exprs())
            result = self._post_process(result)

            # 列順序を [groupByColumns, stat_columns × statistics] に整理
            ordered_stat_cols = [
                f"{col}__{stat.value}"
                for col in self.stat_columns
                for stat in self.statistics
            ]
            result = result.select(
                list(self.group_by_columns) + ordered_stat_cols
            )

            self.tables_store.store_table(self.new_table_name, result)
            return {"tableName": self.new_table_name}

        except ValidationError, ProcessingError:
            raise
        except Exception as e:
            message = _(
                "An unexpected error occurred during"
                " group statistics table creation processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.CREATE_TABLE_ERROR,
                message=message,
                detail=str(e),
            ) from e
