import math

import polars as pl

from ...core.enums import ErrorCode
from ...i18n.translation import gettext as _
from ...models import TransformColumnRequestBody, TransformMethodType
from ...utils import ProcessingError
from ...utils.validators import validate_existence, validate_non_existence
from ..data.tables_store import TablesStore


class TransformColumn:
    """
    テーブルの列の値を変換して新しい列を追加するためのAPIクラス

    指定されたテーブルの指定された列の値を変換し、
    指定された列の右隣に新しい列を挿入します。
    変換方法は対数変換、累乗変換、またはルート変換をサポートします。
    """

    def __init__(
        self,
        body: TransformColumnRequestBody,
        tables_store: TablesStore,
    ):
        self.tables_store = tables_store
        self.table_name = body.table_name
        self.source_column_name = body.source_column_name
        self.new_column_name = body.new_column_name
        self.transform_method = body.transform_method
        self.param_names = {
            "table_name": "tableName",
            "source_column": "sourceColumnName",
            "new_column": "newColumnName",
            "transform_method": "transformMethod",
        }

    def validate(self):
        table_name_list = self.tables_store.get_table_name_list()
        # 対象のテーブルが存在することを検証
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.param_names["table_name"],
        )
        column_name_list = self.tables_store.get_column_name_list(
            self.table_name
        )
        # 変換元の列名が既存の列名の中に存在することを検証
        validate_existence(
            value=self.source_column_name,
            valid_list=column_name_list,
            target=self.param_names["source_column"],
        )
        # 変換後の列名が既存の列名と重複しないことを検証
        validate_non_existence(
            value=self.new_column_name,
            existing_list=column_name_list,
            target=self.param_names["new_column"],
        )
        return None

    def execute(self):
        try:
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            # Find the insert position (right of source column)
            insert_index = df.columns.index(self.source_column_name) + 1

            # Apply transformation based on method
            if self.transform_method.method == TransformMethodType.LOG:
                if self.transform_method.log_base is None:
                    # Natural logarithm
                    transformed_series = df.select(
                        pl.col(self.source_column_name).log()
                    ).to_series()
                else:
                    # Custom base logarithm using change of base formula
                    transformed_series = df.select(
                        pl.col(self.source_column_name).log()
                        / math.log(self.transform_method.log_base)
                    ).to_series()
            elif self.transform_method.method == TransformMethodType.POWER:
                exponent = (
                    self.transform_method.exponent
                    if self.transform_method.exponent is not None
                    else 2.0
                )
                transformed_series = df.select(
                    pl.col(self.source_column_name).pow(exponent)
                ).to_series()
            elif self.transform_method.method == TransformMethodType.ROOT:
                root_index = (
                    self.transform_method.root_index
                    if (self.transform_method.root_index is not None)
                    else 2.0
                )
                # Root transformation using power with reciprocal
                transformed_series = df.select(
                    pl.col(self.source_column_name).pow(1.0 / root_index)
                ).to_series()
            else:
                raise ProcessingError(
                    error_code=ErrorCode.TRANSFORM_METHOD_ERROR,
                    message=f"Unsupported transform method: {self.transform_method}",
                    detail=str(self.transform_method),
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
            raise ProcessingError(
                error_code=ErrorCode.TRANSFORM_COLUMN_PROCESS_ERROR,
                message=message,
                detail=str(e),
            ) from e
