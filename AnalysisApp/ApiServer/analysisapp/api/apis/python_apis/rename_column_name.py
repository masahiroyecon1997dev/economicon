from typing import Dict
from django.utils.translation import gettext as _
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.input_validator import InputValidator
from ..utilities.validator.input_validation_config \
    import INPUT_VALIDATOR_CONFIG
from ..data.tables_info import all_tables_info
from .common_api_class import AbstractApi, ApiError


class RenameColumnName(AbstractApi):
    """
    列名変更APIのPythonロジック
    """
    def __init__(self, table_name: str,
                 old_column_name: str,
                 new_column_name: str):
        self.table_name = table_name
        self.old_column_name = old_column_name
        self.new_column_name = new_column_name
        self.param_names = {
            'table_name': 'tableName',
            'new_column_name': 'newColumnName',
            'column_names': 'oldColumnName',
        }

    def validate(self):
        try:
            validator = InputValidator(param_names=self.param_names,
                                       **INPUT_VALIDATOR_CONFIG)
            validator.validate_existed_table_name(self.table_name,
                                                  all_tables_info)
            table_info = all_tables_info[self.table_name]
            validator.validate_existed_column_name(self.old_column_name,
                                                   table_info)
            validator.validate_new_column_name(self.new_column_name,
                                               table_info.table.columns)
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = all_tables_info[self.table_name]
            df = table_info.table
            new_df = df.rename({self.old_column_name: self.new_column_name})
            table_info.table = new_df
            all_tables_info[self.table_name] = table_info
            result = {'tableName': self.table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "renaming column processing")
            raise ApiError(message) from e


def rename_column_name(table_name: str,
                       old_column_name: str,
                       new_column_name: str) -> Dict:
    api = RenameColumnName(table_name, old_column_name, new_column_name)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
