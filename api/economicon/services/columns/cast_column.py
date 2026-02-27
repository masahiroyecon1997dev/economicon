from typing import ClassVar, Literal

import polars as pl

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.models import CastColumnRequestBody
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError, ValidationError
from economicon.utils.validators import (
    validate_existence,
    validate_non_existence,
)

# Polars型マッピング（date/datetime は str メソッドで別途処理）
_SCALAR_TYPE_MAP: dict[
    Literal["float", "int", "str", "bool"], pl.PolarsDataType
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

        # --- 型変換の適用 ---
        if self.target_type in _SCALAR_TYPE_MAP:
            # strict=True の場合、Polarsが変換失敗時に例外を送出する。
            # その例外を捕捉して ValidationError (HTTP 400) に変換する。
            if self.strict:
                try:
                    expr = expr.cast(
                        _SCALAR_TYPE_MAP[self.target_type], strict=True
                    )
                    # Polars はlazyなので即時評価して例外を確認する
                    df.select(expr)
                except Exception as e:
                    message = _(
                        "Type conversion failed: column '{}' cannot be "
                        "cast to '{}'"
                    ).format(self.source_column_name, self.target_type)
                    raise ValidationError(
                        error_code=ErrorCode.CAST_COLUMN_TYPE_ERROR,
                        message=message,
                        target=self.PARAM_NAMES["source_column_name"],
                    ) from e
            else:
                # strict=False: 変換失敗値を null に置き換える
                expr = expr.cast(
                    _SCALAR_TYPE_MAP[self.target_type], strict=False
                )

        elif self.target_type == "date":
            if self.strict:
                try:
                    df.select(
                        pl.col(self.source_column_name).str.to_date(
                            format=self.datetime_format, strict=True
                        )
                    )
                except Exception as e:
                    message = _(
                        "Type conversion failed: column '{}' cannot be "
                        "cast to '{}'"
                    ).format(self.source_column_name, self.target_type)
                    raise ValidationError(
                        error_code=ErrorCode.CAST_COLUMN_TYPE_ERROR,
                        message=message,
                        target=self.PARAM_NAMES["source_column_name"],
                    ) from e
            expr = expr.str.to_date(
                format=self.datetime_format, strict=self.strict
            )

        elif self.target_type == "datetime":
            if self.strict:
                try:
                    df.select(
                        pl.col(self.source_column_name).str.to_datetime(
                            format=self.datetime_format, strict=True
                        )
                    )
                except Exception as e:
                    message = _(
                        "Type conversion failed: column '{}' cannot be "
                        "cast to '{}'"
                    ).format(self.source_column_name, self.target_type)
                    raise ValidationError(
                        error_code=ErrorCode.CAST_COLUMN_TYPE_ERROR,
                        message=message,
                        target=self.PARAM_NAMES["source_column_name"],
                    ) from e
            expr = expr.str.to_datetime(
                format=self.datetime_format, strict=self.strict
            )

        else:
            # Literal 型制約により通常ここには到達しない
            raise ProcessingError(
                error_code=ErrorCode.CAST_COLUMN_PROCESS_ERROR,
                message=_("Unsupported target type: {}").format(
                    self.target_type
                ),
                detail=str(self.target_type),
            )

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
