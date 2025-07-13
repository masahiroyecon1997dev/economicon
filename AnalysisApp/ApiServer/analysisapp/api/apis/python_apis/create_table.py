import polars as pl
from django.utils.translation import gettext as _
from typing import Dict, List
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.input_validator import InputValidator
from ..utilities.validator.input_validation_config \
    import INPUT_VALIDATOR_CONFIG
from ..data.tables_info import TableInfo, all_tables_info
from .common_api_class import AbstractApi, ApiError


class CreateTable(AbstractApi):
    """
    テーブル作成APIのPythonロジック
    """
    def __init__(self, table_name: str,
                 table_number_of_rows: int,
                 columnNames: List[str]):
        self.table_name = table_name
        self.table_number_of_rows = table_number_of_rows
        self.columnNames = columnNames
        self.param_names = {
            'table_name': 'tableName',
            'table_num_rows': 'tableNumberOfRows',
            'column_names': 'columnNames',
        }

    def validate(self):
        try:
            validator = InputValidator(param_names=self.param_names,
                                       **INPUT_VALIDATOR_CONFIG)
            validator.validate_new_table_name(self.table_name, all_tables_info)
            validator.validate_table_num_rows(self.table_number_of_rows)
            validator.validate_new_columns(self.columnNames)
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            new_column_data_none = [None] * self.table_number_of_rows
            data = {col: new_column_data_none for col in self.columnNames}
            df = pl.DataFrame(data)
            table_info = TableInfo(table_name=self.table_name, table=df)
            all_tables_info[self.table_name] = table_info
            result = {'tableName': self.table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "table creation processing")
            raise ApiError(message) from e


def create_table(table_name: str, table_number_of_rows: int,
                 columnNames: List[str]) -> Dict:
    api = CreateTable(table_name, table_number_of_rows, columnNames)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
