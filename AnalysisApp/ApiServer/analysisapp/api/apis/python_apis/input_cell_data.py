import polars as pl
from typing import Dict
from django.utils.translation import gettext as _
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.input_validator import InputValidator
from ..utilities.validator.input_validation_config \
    import INPUT_VALIDATOR_CONFIG
from ..data.tables_info import all_tables_info
from .common_api_class import AbstractApi, ApiError


class InputCellData(AbstractApi):
    """
    セルデータ入力APIのPythonロジック
    """
    def __init__(self, table_name: str,
                 column_name: str,
                 row_index: int,
                 new_value):
        self.table_name = table_name
        self.column_name = column_name
        self.row_index = row_index
        self.new_value = new_value
        self.param_names = {
            'table_name': 'tableName',
            'column_names': 'columnName',
            'row_index': 'rowIndex',
        }

    def validate(self):
        try:
            validator = InputValidator(param_names=self.param_names,
                                       **INPUT_VALIDATOR_CONFIG)
            validator.validate_existed_table_name(self.table_name,
                                                  all_tables_info)
            table_info = all_tables_info[self.table_name]
            validator.validate_existed_column_name(self.column_name,
                                                   table_info)
            validator.validate_row_index(self.row_index, table_info.num_rows)
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            df = all_tables_info[self.table_name].table
            numpy_array = df.get_column(self.column_name).to_list().copy()
            numpy_array[self.row_index] = self.new_value
            modified_series = pl.Series(name=self.column_name,
                                        values=numpy_array, strict=False)
            new_df = df.with_columns(modified_series)
            all_tables_info[self.table_name].table = new_df
            result = {'tableName': self.table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "input cell data processing")
            raise ApiError(message) from e


def input_cell_data(table_name: str,
                    column_name: str,
                    row_index: int,
                    new_value) -> Dict:
    api = InputCellData(table_name, column_name, row_index, new_value)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
