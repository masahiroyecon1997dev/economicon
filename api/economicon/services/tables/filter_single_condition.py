import polars as pl

from ...i18n.translation import gettext as _
from ...models import FilterSingleConditionRequestBody
from ...utils import ProcessingError, ValidationError
from ...utils.validators import (
    validate_existence,
    validate_non_existence,
)
from ..data.tables_store import TablesStore


class FilterSingleCondition:
    """
    単一条件フィルタリングAPIのPythonロジック

    指定されたテーブルから指定された条件に合致する行のみを抽出し、
    新しいテーブルを作成します。
    """

    def __init__(
        self,
        body: FilterSingleConditionRequestBody,
    ):
        self.manager = TablesStore()
        # 新しいテーブル名
        self.new_table_name = body.new_table_name
        # フィルタリング対象のテーブル名
        self.table_name = body.table_name
        # フィルタリング対象のカラム名
        self.column_name = body.column_name
        # フィルタリング条件
        self.condition = body.condition
        # 比較値がカラムかどうか
        self.is_compare_column = body.is_compare_column
        # 比較値
        self.compare_value = body.compare_value
        # パラメータ名のマッピング
        self.param_names = {
            "new_table_name": "newTableName",
            "table_name": "tableName",
            "column_names": "columnName",
            "condition": "condition",
            "is_compare_column": "isCompareColumn",
            "compare_value": "compareValue",
        }

    def validate(self):
        # 入力値のバリデーション
        try:
            table_name_list = self.manager.get_table_name_list()
            # 新しいテーブル名の重複チェック
            validate_non_existence(
                value=self.new_table_name,
                existing_list=table_name_list,
                target=self.param_names["new_table_name"],
            )
            # 既存テーブル名の存在チェック
            validate_existence(
                value=self.table_name,
                valid_list=table_name_list,
                target=self.param_names["table_name"],
            )
            # カラム名の存在チェック
            column_names = self.manager.get_column_name_list(self.table_name)
            validate_existence(
                value=self.column_name,
                valid_list=column_names,
                target=self.param_names["column_names"],
            )
            # 比較値がカラムの場合の存在チェック
            if self.is_compare_column == "true":
                validate_existence(
                    value=self.compare_value,
                    valid_list=column_names,
                    target=self.param_names["compare_value"],
                )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # フィルタリング処理
        try:
            # 対象テーブルのデータフレームを取得
            df = self.manager.get_table(self.table_name).table

            # 条件に応じてフィルタリング処理を実行
            match self.condition:
                case "equals":
                    # 等価条件
                    filtered_df = df.filter(
                        pl.col(self.column_name)
                        == (
                            pl.col(self.compare_value)
                            if self.is_compare_column == "true"
                            else self.compare_value
                        )
                    )
                case "notEquals":
                    # 非等価条件
                    filtered_df = df.filter(
                        pl.col(self.column_name)
                        != (
                            pl.col(self.compare_value)
                            if self.is_compare_column == "true"
                            else self.compare_value
                        )
                    )
                case "greaterThan":
                    # より大きい条件
                    filtered_df = df.filter(
                        pl.col(self.column_name)
                        > (
                            pl.col(self.compare_value)
                            if self.is_compare_column == "true"
                            else self.compare_value
                        )
                    )
                case "greaterThanOrEquals":
                    # 以上条件
                    filtered_df = df.filter(
                        pl.col(self.column_name)
                        >= (
                            pl.col(self.compare_value)
                            if self.is_compare_column == "true"
                            else self.compare_value
                        )
                    )
                case "lessThan":
                    # より小さい条件
                    filtered_df = df.filter(
                        pl.col(self.column_name)
                        < (
                            pl.col(self.compare_value)
                            if self.is_compare_column == "true"
                            else self.compare_value
                        )
                    )
                case "lessThanOrEquals":
                    # 以下条件
                    filtered_df = df.filter(
                        pl.col(self.column_name)
                        <= (
                            pl.col(self.compare_value)
                            if self.is_compare_column == "true"
                            else self.compare_value
                        )
                    )
                case _:
                    raise ProcessingError(
                        error_code="InvalidConditionError",
                        message=_("Invalid filter condition specified"),
                        detail=f"Condition: {self.condition}",
                    )

            # テーブル情報を更新
            updated_table_name = self.manager.store_table(
                self.new_table_name, filtered_df
            )
            # 結果を返す
            result = {"tableName": updated_table_name}
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during filter processing"
            )
            raise ProcessingError(
                error_code="FilterSingleConditionProcessError",
                message=message,
                detail=str(e),
            ) from e
