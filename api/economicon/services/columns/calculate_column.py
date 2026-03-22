import re
from typing import ClassVar

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.models import CalculateColumnRequestBody
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.algorithms import parse_formula_to_expr
from economicon.utils.validators import (
    validate_existence,
    validate_non_existence,
    validate_numeric_types,
)


class CalculateColumn:
    """
    テーブルの列同士と数値の計算を行い、結果列を追加するためのAPIクラス

    指定されたテーブルに計算式に基づいて新しい列を追加します。
    計算式は列名を<列名>の形式で指定し、四則演算とかっこをサポートします。
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "table_name": "tableName",
        "new_column_name": "newColumnName",
        "calculation_expression": "calculationExpression",
        "column_name_in_calculation_expression": (
            "columnNameInCalculationExpression"
        ),
        "add_position_column": "addPositionColumn",
    }

    def __init__(
        self,
        body: CalculateColumnRequestBody,
        tables_store: TablesStore,
    ):
        self.tables_store = tables_store
        self.table_name = body.table_name
        self.new_column_name = body.new_column_name
        self.add_position_column = body.add_position_column
        self.calculation_expression = body.calculation_expression

    def _extract_column_names(self, expression: str) -> list[str]:
        """
        計算式から {column} 形式のカラム名を重複なく抽出する。
        """
        # { } で囲まれた中身（英数字とアンダースコア）を検索
        pattern = r"\{(\w+)\}"
        matches = re.findall(pattern, expression)

        # セット（集合）にして重複を除去して返す
        return list(set(matches))

    def validate(self):
        table_name_list = self.tables_store.get_table_name_list()
        # 対象のテーブルが存在することを検証
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.PARAM_NAMES["table_name"],
        )

        column_name_list = self.tables_store.get_column_name_list(
            self.table_name
        )
        # 追加する列名が既存の列名と重複しないことを検証
        validate_non_existence(
            value=self.new_column_name,
            existing_list=column_name_list,
            target=self.PARAM_NAMES["new_column_name"],
        )

        referenced_columns = self._extract_column_names(
            self.calculation_expression,
        )
        # 計算式に使用されている列が存在することを検証
        validate_existence(
            value=referenced_columns,
            valid_list=column_name_list,
            target=self.PARAM_NAMES["column_name_in_calculation_expression"],
        )

        # 追加位置の列名が既存の列名の中に存在することを検証
        validate_existence(
            value=self.add_position_column,
            valid_list=column_name_list,
            target=self.PARAM_NAMES["add_position_column"],
        )

        df_schema = self.tables_store.get_schema(self.table_name)
        # 計算式に使用されている列が数値型であることを検証
        validate_numeric_types(
            schema=df_schema,
            columns=referenced_columns,
            target=self.PARAM_NAMES["column_name_in_calculation_expression"],
        )

    def execute(self):
        try:
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            # Polarsの式を評価
            try:
                calc_expr = parse_formula_to_expr(self.calculation_expression)

                # 追加位置を計算（指定されたカラムの右隣）
                current_cols = df.columns
                target_idx = current_cols.index(self.add_position_column) + 1

                # 列の並び順を定義
                new_order = (
                    current_cols[:target_idx]
                    + [self.new_column_name]
                    + current_cols[target_idx:]
                )

                # 新しい列を計算して追加
                df_with_new_col = df.with_columns(
                    calc_expr.alias(self.new_column_name)
                ).select(new_order)

            except Exception as e:
                raise ProcessingError(
                    error_code=ErrorCode.CALCULATION_EXPRESSION_ERROR,
                    message=_("Invalid calculation expression: {}").format(
                        str(e)
                    ),
                    detail=str(e),
                ) from e

            # テーブルを更新
            self.tables_store.update_table(self.table_name, df_with_new_col)

            # 結果を返す
            result = {
                "tableName": self.table_name,
                "columnName": self.new_column_name,
            }
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "column calculation processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.CALCULATE_COLUMN_PROCESS_ERROR,
                message=message,
                detail=str(e),
            ) from e
