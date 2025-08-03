import polars as pl
from django.utils.translation import gettext as _
from typing import Dict
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.validator import InputValidator
from ..utilities.validator.validation_config import (
    INPUT_VALIDATOR_CONFIG)
from ..data.tables_manager import TablesManager
from .common_api_class import (AbstractApi, ApiError)


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
                'column_names': 'sourceColumnName',
                'new_column_name': 'dummyColumnName',
                'target_value': 'targetValue',
            }

    def validate(self):
        try:
            validator = InputValidator(param_names=self.param_names,
                                       **INPUT_VALIDATOR_CONFIG)
            table_name_list = self.tables_manager.get_table_name_list()
            validator.validate_existed_table_name(self.table_name,
                                                  table_name_list)
            column_name_list = self.tables_manager.get_column_name_list(
                self.table_name)
            validator.validate_existed_column_name(self.source_column_name,
                                                   column_name_list)
            validator.validate_new_column_name(self.dummy_column_name,
                                               column_name_list)
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_manager.get_table(self.table_name)
            df = table_info.table
            
            # ダミー変数列を作成（指定された値なら1、それ以外は0）
            dummy_values = (df[self.source_column_name] == self.target_value).cast(pl.Int32)
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