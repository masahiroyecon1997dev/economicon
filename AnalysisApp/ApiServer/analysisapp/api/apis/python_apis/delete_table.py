from typing import Dict
from django.utils.translation import gettext as _
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.input_validator import InputValidator
from ..utilities.validator.input_validation_config \
    import INPUT_VALIDATOR_CONFIG
from ..data.tables_info import all_tables_info
from .common_api_class import AbstractApi, ApiError


class DeleteTable(AbstractApi):
    """
    テーブル削除APIのPythonロジック
    """
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.param_names = {'table_name': 'tableName'}

    def validate(self):
        try:
            validator = InputValidator(param_names=self.param_names,
                                       **INPUT_VALIDATOR_CONFIG)
            validator.validate_existed_table_name(self.table_name,
                                                  all_tables_info)
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            del all_tables_info[self.table_name]
            result = {'tableName': self.table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "table deletion processing")
            raise ApiError(message) from e


def delete_table(table_name: str) -> Dict:
    api = DeleteTable(table_name)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
