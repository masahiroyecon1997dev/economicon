import re
from typing import List

import polars as pl

from ...i18n.translation import gettext as _
from ...models import CalculateColumnRequestBody
from ...utils import ProcessingError, ValidationError
from ...utils.validators import (
    validate_existence,
    validate_non_existence,
    validate_numeric_types,
)
from ..data.tables_store import TablesStore


class CalculateColumn:
    """
    テーブルの列同士と数値の計算を行い、結果列を追加するためのAPIクラス

    指定されたテーブルに計算式に基づいて新しい列を追加します。
    計算式は列名を<列名>の形式で指定し、四則演算とかっこをサポートします。
    """

    def __init__(self, body: CalculateColumnRequestBody):
        self.tables_store = TablesStore()
        self.table_name = body.table_name
        self.new_column_name = body.new_column_name
        self.calculation_expression = body.calculation_expression
        self.param_names = {
            "table_name": "tableName",
            "new_column_name": "newColumnName",
            "calculation_expression": "calculationExpression",
            "column_name_in_calculation_expression": "columnNameInCalculationExpression",
        }

    def _extract_column_names(self, expression: str) -> List[str]:
        """
        計算式から列名を抽出する
        """
        # pl.col("列名")のパターンで列名を抽出
        pattern = r'pl\.col\("([^"]+)"\)'
        column_names = re.findall(pattern, expression)
        return list(set(column_names))  # 重複を除去

    def validate(self):
        try:
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
            # 追加する列名が既存の列名と重複しないことを検証
            validate_non_existence(
                value=self.new_column_name,
                existing_list=column_name_list,
                target=self.param_names["new_column_name"],
            )

            referenced_columns = self._extract_column_names(
                self.calculation_expression,
            )
            # 計算式に使用されている列が存在することを検証
            validate_existence(
                value=referenced_columns,
                valid_list=column_name_list,
                target=self.param_names[
                    "column_name_in_calculation_expression"
                ],
            )
            df_schema = self.tables_store.get_column_info_list(self.table_name)
            # 計算式に使用されている列が数値型であることを検証
            validate_numeric_types(
                schema=df_schema,
                columns=referenced_columns,
                target=self.param_names[
                    "column_name_in_calculation_expression"
                ],
            )

            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            # Polarsの式を評価
            try:
                # 安全なeval環境でPolars式を評価
                safe_globals = {"pl": pl}
                polars_expr = eval(self.calculation_expression, safe_globals)

                # 新しい列を計算して追加
                df_with_new_col = df.with_columns(
                    polars_expr.alias(self.new_column_name)
                )

            except Exception as e:
                raise ProcessingError(
                    error_code="CalculationExpressionError",
                    message=_("Invalid calculation expression: {}").format(
                        str(e)
                    ),
                    detail=str(e),
                )

            # テーブルを更新
            self.tables_store.update_table(self.table_name, df_with_new_col)

            # 結果を返す
            result = {
                "tableName": self.table_name,
                "columnName": self.new_column_name,
            }
            return result
        except ValidationError:
            raise
        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "column calculation processing"
            )
            raise ProcessingError(
                error_code="CalculateColumnProcessError",
                message=message,
                detail=str(e),
            )
