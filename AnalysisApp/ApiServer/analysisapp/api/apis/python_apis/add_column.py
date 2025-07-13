import polars as pl
from django.utils.translation import gettext as _
from typing import Dict
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.input_validator import InputValidator
from ..utilities.validator.input_validation_config import (
    INPUT_VALIDATOR_CONFIG)
from ..data.tables_info import all_tables_info
from .common_api_class import (AbstractApi, ApiError)


class AddColumn(AbstractApi):
    """
    """
    def __init__(self, table_name: str, new_column_name: str,
                 add_position_column: str):
        self.table_name = table_name
        self.new_column_name = new_column_name
        self.add_position_column = add_position_column
        self.param_names = {
                'table_name': 'tableName',
                'new_column_name': 'newColumnName',
                'column_names': 'addPositionColumn',
            }

    def validate(self):
        try:
            validator = InputValidator(param_names=self.param_names,
                                       **INPUT_VALIDATOR_CONFIG)
            validator.validate_existed_table_name(self.table_name,
                                                  all_tables_info)
            table_info = all_tables_info[self.table_name]
            validator.validate_new_column_name(self.new_column_name,
                                               table_info.table.columns)
            validator.validate_existed_column_name(self.add_position_column,
                                                   table_info)
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            df = all_tables_info[self.table_name].table
            num_rows = all_tables_info[self.table_name].num_rows
            new_column_data_none = [None] * num_rows
            insert_index = df.columns.index(self.add_position_column) + 1
            df_with_new_col = df.insert_column(
                index=insert_index,
                column=pl.Series(self.new_column_name, new_column_data_none))
            # 新しい列をデータフレームに追加
            all_tables_info[self.table_name].table = df_with_new_col
            result = {'tableName': self.table_name,
                      'columnName': self.new_column_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "adding column processing")
            raise ApiError(message) from e


def add_column(table_name: str,
               new_column_name: str,
               add_position_column: str) -> Dict:
    api = AddColumn(table_name, new_column_name, add_position_column)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
