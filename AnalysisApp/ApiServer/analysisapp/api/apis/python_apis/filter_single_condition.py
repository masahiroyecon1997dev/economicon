import polars as pl
from typing import Dict
from django.utils.translation import gettext as _
from ..data.tables_manager import TablesManager
from ..utilities.validator.validator import Validator
from ..utilities.validator.validation_config import (
    INPUT_VALIDATOR_CONFIG)
from ..utilities.validator.common_validators import ValidationError
from .common_api_class import (AbstractApi, ApiError)


class FilterSingleCondition(AbstractApi):
    """
    単一条件フィルタリングAPIのPythonロジック

    指定されたテーブルから指定された条件に合致する行のみを抽出し、
    新しいテーブルを作成します。
    """
    def __init__(self, new_table_name: str, table_name: str,
                 column_name: str, condition: str,
                 is_compare_column: str, compare_value: str):
        self.manager = TablesManager()
        # 新しいテーブル名
        self.new_table_name = new_table_name
        # フィルタリング対象のテーブル名
        self.table_name = table_name
        # フィルタリング対象のカラム名
        self.column_name = column_name
        # フィルタリング条件
        self.condition = condition
        # 比較値がカラムかどうか
        self.is_compare_column = is_compare_column
        # 比較値
        self.compare_value = compare_value
        # パラメータ名のマッピング
        self.param_names = {
            'new_table_name': 'newTableName',
            'table_name': 'tableName',
            'column_names': 'columnName',
            'condition': 'condition',
            'is_compare_column': 'isCompareColumn',
            'compare_value': 'compareValue',
        }

    def validate(self):
        # 入力値のバリデーション
        try:
            validator = Validator(param_names=self.param_names,
                                  **INPUT_VALIDATOR_CONFIG)
            table_name_list = self.manager.get_table_name_list()
            # 新しいテーブル名の重複チェック
            validator.validate_new_table_name(self.new_table_name,
                                              table_name_list)
            # 既存テーブル名の存在チェック
            validator.validate_existed_table_name(self.table_name,
                                                  table_name_list)
            # カラム名の存在チェック
            column_names = self.manager.get_column_name_list(self.table_name)
            validator.validate_existed_column_name(self.column_name,
                                                   column_names)
            # フィルタリング条件の妥当性チェック
            validator.validate_filter_condition(self.condition)
            # 比較値タイプの妥当性チェック
            validator.validate_is_compare_column(self.is_compare_column)
            # 比較値の妥当性チェック
            validator.validate_compare_value(self.compare_value)
            # 比較値がカラムの場合の存在チェック
            if self.is_compare_column == 'true':
                validator.validate_existed_column_name(self.compare_value,
                                                       column_names)
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
                case 'equals':
                    # 等価条件
                    filtered_df = df.filter(
                        pl.col(self.column_name) == (
                            pl.col(self.compare_value)
                            if self.is_compare_column == 'true'
                            else self.compare_value
                        )
                    )
                case 'notEquals':
                    # 非等価条件
                    filtered_df = df.filter(
                        pl.col(self.column_name) != (
                            pl.col(self.compare_value)
                            if self.is_compare_column == 'true'
                            else self.compare_value
                        )
                    )
                case 'greaterThan':
                    # より大きい条件
                    filtered_df = df.filter(
                        pl.col(self.column_name) > (
                            pl.col(self.compare_value)
                            if self.is_compare_column == 'true'
                            else self.compare_value
                        )
                    )
                case 'greaterThanOrEquals':
                    # 以上条件
                    filtered_df = df.filter(
                        pl.col(self.column_name) >= (
                            pl.col(self.compare_value)
                            if self.is_compare_column == 'true'
                            else self.compare_value
                        )
                    )
                case 'lessThan':
                    # より小さい条件
                    filtered_df = df.filter(
                        pl.col(self.column_name) < (
                            pl.col(self.compare_value)
                            if self.is_compare_column == 'true'
                            else self.compare_value
                        )
                    )
                case 'lessThanOrEquals':
                    # 以下条件
                    filtered_df = df.filter(
                        pl.col(self.column_name) <= (
                            pl.col(self.compare_value)
                            if self.is_compare_column == 'true'
                            else self.compare_value
                        )
                    )
                case _:
                    raise ValidationError(_('Invalid condition specified'))

            # テーブル情報を更新
            updated_table_name = self.manager.store_table(
                self.new_table_name, filtered_df
            )
            # 結果を返す
            result = {'tableName': updated_table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "filter processing")
            raise ApiError(message) from e


def filter_single_condition(
    new_table_name: str, table_name: str, column_name: str,
    condition: str, is_compare_column: str, compare_value: str
) -> Dict:
    api = FilterSingleCondition(
        new_table_name, table_name, column_name, condition,
        is_compare_column, compare_value
    )
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
