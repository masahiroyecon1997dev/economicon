import re
from typing import List

import polars as pl

from ...exceptions import ApiError
from ...i18n.translation import gettext as _
from ...models import CalculateColumnRequestBody
from ...utils.validators.common import ValidationError
from ...utils.validators.tables_store import (
    validate_existed_numeric_columns,
    validate_existed_table_name,
    validate_new_column_name,
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
            "column_name_in_calculation_expression": "columnName in calculationExpression",
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
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names["table_name"],
            )

            # 新しい列名の検証
            column_name_list = self.tables_store.get_column_name_list(
                self.table_name
            )
            validate_new_column_name(
                self.new_column_name,
                column_name_list,
                self.param_names["new_column_name"],
            )

            # 計算式から列名を抽出して存在チェック
            referenced_columns = self._extract_column_names(
                self.calculation_expression,
            )
            df_schema = self.tables_store.get_column_info_list(self.table_name)
            validate_existed_numeric_columns(
                referenced_columns,
                column_name_list,
                df_schema,
                self.param_names["calculation_expression"],
                self.param_names["column_name_in_calculation_expression"],
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
                raise ValidationError(
                    "CalculationExpressionError",
                    _("Invalid calculation expression: {}").format(str(e)),
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
            raise ApiError(message) from e
