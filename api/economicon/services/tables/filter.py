from typing import Any, ClassVar

import polars as pl

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas import FilterCondition, FilterRequestBody
from economicon.schemas.enums import LogicalOperatorType
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import (
    validate_existence,
    validate_non_existence,
)


class FilterTable:
    """
    テーブルフィルタAPIのPythonロジック

    指定されたテーブルから複数の条件（AND / OR）に合致する行のみを抽出し、
    新しいテーブルを作成します。
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "new_table_name": "newTableName",
        "table_name": "tableName",
        "column_name": "columnName",
        "compare_value": "compareValue",
    }

    def __init__(
        self,
        body: FilterRequestBody,
        tables_store: TablesStore,
    ):
        self.manager = tables_store
        self.new_table_name = body.new_table_name
        self.table_name = body.table_name
        self.logical_operator = body.logical_operator
        self.conditions = body.conditions

    def validate(self):
        table_name_list = self.manager.get_table_name_list()
        # 新しいテーブル名の重複チェック
        validate_non_existence(
            value=self.new_table_name,
            existing_list=table_name_list,
            target=self.PARAM_NAMES["new_table_name"],
        )
        # 既存テーブル名の存在チェック
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.PARAM_NAMES["table_name"],
        )
        # 各条件のカラム名チェック
        column_names = self.manager.get_column_name_list(self.table_name)
        for cond in self.conditions:
            validate_existence(
                value=cond.column_name,
                valid_list=column_names,
                target=self.PARAM_NAMES["column_name"],
            )
            # 比較値がカラムの場合の存在チェック
            if cond.is_compare_column:
                validate_existence(
                    value=cond.compare_value,
                    valid_list=column_names,
                    target=self.PARAM_NAMES["compare_value"],
                )

    def _build_expr(self, cond: FilterCondition) -> pl.Expr:
        compare: Any = (
            pl.col(cond.compare_value)
            if cond.is_compare_column
            else cond.compare_value
        )
        match cond.condition:
            case "equals":
                return pl.col(cond.column_name) == compare
            case "notEquals":
                return pl.col(cond.column_name) != compare
            case "greaterThan":
                return pl.col(cond.column_name) > compare
            case "greaterThanOrEquals":
                return pl.col(cond.column_name) >= compare
            case "lessThan":
                return pl.col(cond.column_name) < compare
            case "lessThanOrEquals":
                return pl.col(cond.column_name) <= compare
            case _:
                raise ProcessingError(
                    error_code=ErrorCode.INVALID_CONDITION_ERROR,
                    message=_("Invalid filter condition specified"),
                    detail=f"Condition: {cond.condition}",
                )

    def execute(self):
        try:
            df = self.manager.get_table(self.table_name).table

            exprs = [self._build_expr(c) for c in self.conditions]
            combined = exprs[0]
            for expr in exprs[1:]:
                if self.logical_operator == LogicalOperatorType.AND:
                    combined = combined & expr
                else:
                    combined = combined | expr

            filtered_df = df.filter(combined)
            updated_table_name = self.manager.store_table(
                self.new_table_name, filtered_df
            )
            return {"tableName": updated_table_name}
        except ProcessingError:
            raise
        except Exception as e:
            message = _(
                "An unexpected error occurred during filter processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.FILTER_TABLE_PROCESS_ERROR,
                message=message,
                detail=str(e),
            ) from e
