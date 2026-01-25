from typing import Dict

import polars as pl
from pydantic import validate_call
from .django_compat import gettext as _

from .data.tables_store import TablesStore
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_store_validator import (
    validate_existed_column_name, validate_existed_table_name,
    validate_new_column_name)
from .abstract_api import AbstractApi, ApiError


class AddColumn(AbstractApi):
    """
    テーブルに新しい列を追加するためのAPIクラス

    指定されたテーブルの指定された位置に新しい列を挿入します。
    新しい列は空（None）の値で初期化されます。
    """
    def __init__(
        self,
        table_name: str,
        new_column_name: str,
        add_position_column: str
    ):
        self.tables_store = TablesStore()
        self.table_name = table_name
        self.new_column_name = new_column_name
        self.add_position_column = add_position_column
        self.param_names = {
            'table_name': 'tableName',
            'new_column_name': 'newColumnName',
            'add_position_column': 'addPositionColumn',
        }

    def validate(self):
        try:
            table_name_list = self.tables_store.get_table_name_list()
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )
            column_name_list = self.tables_store.get_column_name_list(
                self.table_name)
            validate_new_column_name(
                self.new_column_name,
                column_name_list,
                self.param_names['new_column_name']
            )
            validate_existed_column_name(
                self.add_position_column,
                column_name_list,
                self.param_names['add_position_column']
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_store.get_table(self.table_name)
            num_rows = table_info.num_rows
            new_column_data_none = [None] * num_rows
            df = table_info.table
            insert_index = df.columns.index(self.add_position_column) + 1
            df_with_new_col = df.insert_column(
                index=insert_index,
                column=pl.Series(self.new_column_name, new_column_data_none)
            )
            # 新しい列をデータフレームに追加
            self.tables_store.update_table(self.table_name, df_with_new_col)
            # 結果を返す
            result = {
                'tableName': self.table_name,
                'columnName': self.new_column_name
            }
            return result
        except Exception as e:
            message = _("An unexpected error occurred "
                        "during adding column processing")
            raise ApiError(message) from e

@validate_call
def add_column(
    table_name: str,
    new_column_name: str,
    add_position_column: str
) -> Dict:
    api = AddColumn(table_name, new_column_name, add_position_column)
    validation_error = api.validate()
    if validation_error:
        raise ValueError(validation_error.message)
    return api.execute()
