from typing import Dict
from django.utils.translation import gettext as _
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.input_validator import InputValidator
from ..utilities.validator.input_validation_config \
    import INPUT_VALIDATOR_CONFIG
from ..data.tables_info import all_tables_info
from .common_api_class import AbstractApi, ApiError


class RenameTable(AbstractApi):
    """
    テーブル名変更APIのPythonロジック
    """
    def __init__(self, old_table_name: str, new_table_name: str):
        self.old_table_name = old_table_name
        self.new_table_name = new_table_name
        self.param_names = {
            'table_name': 'oldTableName',
            'new_table_name': 'newTableName',
        }

    def validate(self):
        try:
            validator = InputValidator(param_names=self.param_names,
                                       **INPUT_VALIDATOR_CONFIG)
            validator.validate_existed_table_name(self.old_table_name,
                                                  all_tables_info)
            validator.param_names['table_name'] = 'newTableName'
            validator.validate_new_table_name(self.new_table_name,
                                              all_tables_info)
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = all_tables_info.pop(self.old_table_name)
            table_info.table_name = self.new_table_name
            all_tables_info[self.new_table_name] = table_info
            result = {'tableName': self.new_table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "table rename processing")
            raise ApiError(message) from e


def rename_table(old_table_name: str, new_table_name: str) -> Dict:
    api = RenameTable(old_table_name, new_table_name)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
