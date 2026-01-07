from typing import Dict

import polars as pl

from ..utils.validator.common_validators import (ValidationError,
                                                 validate_required)
from ..utils.validator.tables_manager_validator import (
    validate_existed_column_name, validate_existed_table_name,
    validate_new_column_name)
from .abstract_api import AbstractApi, ApiError
from .data.tables_manager import TablesManager
from .django_compat import gettext as _


class AddDummyColumn(AbstractApi):
    """
    テーブルの指定列からダミー変数列を作成するためのAPIクラス

    指定されたテーブルの指定された列の値に基づいて、ダミー変数列を作成します。
    指定された値が1になり、それ以外の値は0になります。
    """
    def __init__(self, table_name: str, source_column_name: str,
                 dummy_column_name: str, target_value: str):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.source_column_name = source_column_name
        self.dummy_column_name = dummy_column_name
        self.target_value = target_value
        self.param_names = {
                'table_name': 'tableName',
                'source_column_name': 'sourceColumnName',
                'dummy_column_name': 'dummyColumnName',
                'target_value': 'targetValue',
            }

    def validate(self):
        try:
            table_name_list = self.tables_manager.get_table_name_list()
            validate_existed_table_name(self.table_name,
                                        table_name_list,
                                        self.param_names['table_name'])
            column_name_list = self.tables_manager.get_column_name_list(
                self.table_name)
            validate_existed_column_name(
                self.source_column_name,
                column_name_list,
                self.param_names['source_column_name']
            )
            validate_new_column_name(self.dummy_column_name,
                                     column_name_list,
                                     self.param_names['dummy_column_name'])
            validate_required(self.target_value,
                              self.param_names['target_value'])
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_manager.get_table(self.table_name)
            df = table_info.table

            # ダミー変数列を作成（指定された値なら1、それ以外は0）
            dummy_values = (
                df[self.source_column_name] == self.target_value).cast(
                    pl.Int32)
            dummy_column = pl.Series(self.dummy_column_name, dummy_values)

            # 新しい列をデータフレームに追加
            df_with_dummy = df.with_columns(dummy_column)

            # テーブルを更新
            self.tables_manager.update_table(
                self.table_name, df_with_dummy)

            # 結果を返す
            result = {'tableName': self.table_name,
                      'dummyColumnName': self.dummy_column_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "adding dummy column processing")
            raise ApiError(message) from e


def add_dummy_column(table_name: str,
                     source_column_name: str,
                     dummy_column_name: str,
                     target_value: str) -> Dict:
    api = AddDummyColumn(table_name, source_column_name,
                         dummy_column_name, target_value)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
