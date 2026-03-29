from typing import ClassVar, Literal

import polars as pl

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas import CastColumnRequestBody
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError, ValidationError
from economicon.utils.validators import (
    validate_existence,
    validate_non_existence,
)

# polars.type_aliases は Polars 1.0 で非推奨のため独自に定義
type PolarsDataType = pl.DataType | type[pl.DataType]

# Polars型マッピング（date/datetime は str メソッドで別途処理）
_SCALAR_TYPE_MAP: dict[
    Literal["float", "int", "str", "bool"], PolarsDataType
] = {
    "float": pl.Float64,
    "int": pl.Int64,
    "str": pl.Utf8,
    "bool": pl.Boolean,
}


class CastColumn:
    """
    テーブルの列を指定したデータ型に変換し、新しい列として追加するAPIクラス

    変換前に文字列クリーンアップ（空白・カンマ削除）を任意で適用します。
    strict=True の場合、変換失敗時に 400 エラーを返します。
    strict=False の場合、変換失敗値を null に置き換えて処理を続行します。
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "table_name": "tableName",
        "source_column_name": "sourceColumnName",
        "new_column_name": "newColumnName",
        "add_position_column": "addPositionColumn",
    }

    def __init__(
        self,
        body: CastColumnRequestBody,
        tables_store: TablesStore,
    ):
        self.tables_store = tables_store
        self.table_name = body.table_name
        self.source_column_name = body.source_column_name
        self.target_type = body.target_type
        self.new_column_name = body.new_column_name
        self.add_position_column = body.add_position_column
        self.cleanup_whitespace = body.cleanup_whitespace
        self.remove_commas = body.remove_commas
        self.datetime_format = body.datetime_format
        self.strict = body.strict

    def validate(self):
        table_name_list = self.tables_store.get_table_name_list()
        # 対象テーブルの存在確認
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.PARAM_NAMES["table_name"],
        )
        column_name_list = self.tables_store.get_column_name_list(
            self.table_name
        )
        # 変換元列の存在確認
        validate_existence(
            value=self.source_column_name,
            valid_list=column_name_list,
            target=self.PARAM_NAMES["source_column_name"],
        )
        # 挿入位置列の存在確認
        validate_existence(
            value=self.add_position_column,
            valid_list=column_name_list,
            target=self.PARAM_NAMES["add_position_column"],
        )
        # 新しい列名が既存列と重複しないことを確認
        validate_non_existence(
            value=self.new_column_name,
            existing_list=column_name_list,
            target=self.PARAM_NAMES["new_column_name"],
        )

    def _cast_error(self) -> ValidationError:
        """型変換失敗時の ValidationError を生成する"""
        message = _(
            "Type conversion failed: column '{}' cannot be cast to '{}'"
        ).format(self.source_column_name, self.target_type)
        return ValidationError(
            error_code=ErrorCode.CAST_COLUMN_TYPE_ERROR,
            message=message,
            target=self.PARAM_NAMES["source_column_name"],
        )

    def _build_scalar_expr(
        self,
        df: pl.DataFrame,
        expr: pl.Expr,
        dtype: PolarsDataType,
    ) -> pl.Expr:
        """スカラー型変換エクスプレッションを構築する"""
        if self.strict:
            try:
                df.select(expr.cast(dtype, strict=True))
            except Exception as e:
                raise self._cast_error() from e
        return expr.cast(dtype, strict=self.strict)

    def _build_temporal_expr(
        self,
        df: pl.DataFrame,
        expr: pl.Expr,
        kind: Literal["date", "datetime"],
    ) -> pl.Expr:
        """日付/日時型変換エクスプレッションを構築する"""
        if kind == "date":
            cast_expr = expr.str.to_date(
                format=self.datetime_format, strict=self.strict
            )
        else:
            cast_expr = expr.str.to_datetime(
                format=self.datetime_format, strict=self.strict
            )
        # strict=True の場合は前処理済み expr で即時評価して例外を確認する
        if self.strict:
            try:
                df.select(cast_expr)
            except Exception as e:
                raise self._cast_error() from e
        return cast_expr

    def _build_expr(self, df: pl.DataFrame, expr: pl.Expr) -> pl.Expr:
        """型変換エクスプレッションを構築する"""
        if self.target_type in _SCALAR_TYPE_MAP:
            return self._build_scalar_expr(
                df, expr, _SCALAR_TYPE_MAP[self.target_type]
            )
        if self.target_type == "date":
            return self._build_temporal_expr(df, expr, "date")
        if self.target_type == "datetime":
            return self._build_temporal_expr(df, expr, "datetime")
        # Literal 型制約により通常ここには到達しない
        raise ProcessingError(
            error_code=ErrorCode.CAST_COLUMN_PROCESS_ERROR,
            message=_("Unsupported target type: {}").format(self.target_type),
            detail=str(self.target_type),
        )

    def execute(self):
        table_info = self.tables_store.get_table(self.table_name)
        df = table_info.table

        # --- 前処理エクスプレッションの構築 ---
        expr: pl.Expr = pl.col(self.source_column_name)

        # 文字列型の列のみクリーニングを適用
        if df.schema[self.source_column_name] == pl.Utf8:
            if self.cleanup_whitespace:
                expr = expr.str.strip_chars()
            if self.remove_commas:
                expr = expr.str.replace_all(",", "")

        expr = self._build_expr(df, expr)

        # --- 新列の追加と挿入位置の調整 ---
        try:
            df = df.with_columns(expr.alias(self.new_column_name))

            # add_position_column の右隣に新列を再配置する
            cols: list[str] = df.columns
            new_col_idx = cols.index(self.new_column_name)
            cols.pop(new_col_idx)
            insert_idx = cols.index(self.add_position_column) + 1
            cols.insert(insert_idx, self.new_column_name)
            df = df.select(cols)

            self.tables_store.update_table(self.table_name, df)
        except Exception as e:
            message = _(
                "An unexpected error occurred during column cast processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.CAST_COLUMN_PROCESS_ERROR,
                message=message,
                detail=str(e),
            ) from e

        return {
            "tableName": self.table_name,
            "columnName": self.new_column_name,
        }
