import polars as pl
import re
from django.utils.translation import gettext as _
from typing import Dict, List
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.tables_manager_validator import (
    validate_existed_table_name,
    validate_new_column_name,
    validate_calculation_expression,
    validate_existed_numeric_columns
)
from ..data.tables_manager import TablesManager
from .common_api_class import (AbstractApi, ApiError)


class CalculateColumn(AbstractApi):
    """
    テーブルの列同士と数値の計算を行い、結果列を追加するためのAPIクラス

    指定されたテーブルに計算式に基づいて新しい列を追加します。
    計算式は列名を<列名>の形式で指定し、四則演算とかっこをサポートします。
    """
    def __init__(self, table_name: str, new_column_name: str,
                 calculation_expression: str):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.new_column_name = new_column_name
        self.calculation_expression = calculation_expression
        self.param_names = {
                'table_name': 'tableName',
                'new_column_name': 'newColumnName',
                'calculation_expression': 'calculationExpression',
                'column_name_in_calculation_expression':
                'columnName in calculationExpression'
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
            table_name_list = self.tables_manager.get_table_name_list()
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )

            # 新しい列名の検証
            column_name_list = self.tables_manager.get_column_name_list(
                self.table_name)
            validate_new_column_name(
                self.new_column_name,
                column_name_list,
                self.param_names['new_column_name']
            )

            # 計算式が空でないことを検証
            expression = self.calculation_expression.strip()
            validate_calculation_expression(
                expression,
                self.param_names['calculation_expression']
            )

            # 計算式から列名を抽出して存在チェック
            referenced_columns = self._extract_column_names(
                self.calculation_expression,

            )
            df_schema = self.tables_manager.get_column_info_list(
                self.table_name)
            validate_existed_numeric_columns(
                referenced_columns,
                column_name_list,
                df_schema,
                self.param_names['calculation_expression'],
                self.param_names['column_name_in_calculation_expression']
            )

            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_manager.get_table(self.table_name)
            df = table_info.table

            # Polarsの式を評価
            try:
                # 安全なeval環境でPolars式を評価
                safe_globals = {'pl': pl}
                polars_expr = eval(self.calculation_expression, safe_globals)

                # 新しい列を計算して追加
                df_with_new_col = df.with_columns(
                    polars_expr.alias(self.new_column_name))

            except Exception as e:
                raise ValidationError(
                    f"Invalid calculation expression: {str(e)}")

            # テーブルを更新
            self.tables_manager.update_table(self.table_name, df_with_new_col)

            # 結果を返す
            result = {'tableName': self.table_name,
                      'columnName': self.new_column_name}
            return result
        except ValidationError:
            raise
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "column calculation processing")
            raise ApiError(message) from e


def calculate_column(table_name: str,
                     new_column_name: str,
                     calculation_expression: str) -> Dict:
    api = CalculateColumn(table_name, new_column_name, calculation_expression)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
