import math
from typing import Dict, Optional

import polars as pl

from ...i18n.translation import gettext as _
from ...utils.validators.common_validators import ValidationError
from ...utils.validators.tables_store_validator import (
    validate_existed_column_name,
    validate_existed_table_name,
    validate_new_column_name,
)
from ..abstract_api import AbstractApi, ApiError
from ..data.tables_store import TablesStore


class TransformColumn(AbstractApi):
    """
    テーブルの列の値を変換して新しい列を追加するためのAPIクラス

    指定されたテーブルの指定された列の値を変換し、
    指定された列の右隣に新しい列を挿入します。
    変換方法は対数変換、累乗変換、またはルート変換をサポートします。
    """

    def __init__(
        self,
        table_name: str,
        source_column_name: str,
        new_column_name: str,
        transform_method: str,
        log_base: Optional[float] = None,
        exponent: Optional[float] = None,
        root_index: Optional[float] = None,
    ):
        self.tables_store = TablesStore()
        self.table_name = table_name
        self.source_column_name = source_column_name
        self.new_column_name = new_column_name
        self.transform_method = transform_method
        self.log_base = log_base
        self.exponent = exponent
        self.root_index = root_index
        self.param_names = {
            "table_name": "tableName",
            "source_column": "sourceColumnName",
            "new_column": "newColumnName",
            "transform_method": "transformMethod",
        }

    def validate(self):
        try:
            table_name_list = self.tables_store.get_table_name_list()
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names["table_name"],
            )
            column_name_list = self.tables_store.get_column_name_list(
                self.table_name
            )
            validate_existed_column_name(
                self.source_column_name,
                column_name_list,
                self.param_names["source_column"],
            )
            validate_new_column_name(
                self.new_column_name,
                column_name_list,
                self.param_names["new_column"],
            )

            # Validate transform method
            valid_methods = ["log", "power", "root"]
            if self.transform_method not in valid_methods:
                methods_str = ", ".join(valid_methods)
                raise ValidationError(
                    _(
                        "transformMethodの'{}'は無効です。有効なメソッド: {}"
                    ).format(self.transform_method, methods_str)
                )

            # Validate log base if provided
            if self.transform_method == "log" and self.log_base is not None:
                if self.log_base <= 0 or self.log_base == 1:
                    raise ValidationError(
                        _("logBaseは1ではない正の数でなければなりません")
                    )

            # Validate exponent if provided
            if self.transform_method == "power" and self.exponent is not None:
                if not isinstance(self.exponent, (int, float)):
                    raise ValidationError(
                        _("exponentは数値でなければなりません")
                    )

            # Validate root index if provided
            if self.transform_method == "root" and self.root_index is not None:
                if not (
                    isinstance(self.root_index, (int, float))
                    or self.root_index == 0
                ):
                    raise ValidationError(
                        _("rootIndexは0以外の数値でなければなりません")
                    )

            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            # Find the insert position (right of source column)
            insert_index = df.columns.index(self.source_column_name) + 1

            # Apply transformation based on method
            if self.transform_method == "log":
                if self.log_base is None:
                    # Natural logarithm
                    transformed_series = df.select(
                        pl.col(self.source_column_name).log()
                    ).to_series()
                else:
                    # Custom base logarithm using change of base formula
                    transformed_series = df.select(
                        pl.col(self.source_column_name).log()
                        / math.log(self.log_base)
                    ).to_series()
            elif self.transform_method == "power":
                exponent = self.exponent if self.exponent is not None else 2.0
                transformed_series = df.select(
                    pl.col(self.source_column_name).pow(exponent)
                ).to_series()
            elif self.transform_method == "root":
                root_index = (
                    self.root_index if (self.root_index is not None) else 2.0
                )
                # Root transformation using power with reciprocal
                transformed_series = df.select(
                    pl.col(self.source_column_name).pow(1.0 / root_index)
                ).to_series()
            else:
                raise ValidationError(
                    f"Unsupported transform method: {self.transform_method}"
                )

            # Rename the transformed series
            transformed_series = transformed_series.alias(self.new_column_name)

            # Insert the new column
            df_with_new_col = df.insert_column(
                index=insert_index, column=transformed_series
            )

            # Update the table
            self.tables_store.update_table(self.table_name, df_with_new_col)

            # Return result
            result = {
                "tableName": self.table_name,
                "columnName": self.new_column_name,
            }
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during column transformation processing"
            )
            raise ApiError(message) from e


def transform_column(
    table_name: str,
    source_column_name: str,
    new_column_name: str,
    transform_method: str,
    log_base: Optional[float] = None,
    exponent: Optional[float] = None,
    root_index: Optional[float] = None,
) -> Dict:
    api = TransformColumn(
        table_name,
        source_column_name,
        new_column_name,
        transform_method,
        log_base,
        exponent,
        root_index,
    )
    validation_error = api.validate()
    if validation_error:
        raise ValueError(validation_error.message)
    return api.execute()
