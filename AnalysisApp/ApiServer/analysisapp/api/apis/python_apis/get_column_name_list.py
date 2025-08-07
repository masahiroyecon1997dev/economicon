from django.utils.translation import gettext as _
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.validator import InputValidator
from ..utilities.validator.validation_config import (
    INPUT_VALIDATOR_CONFIG)
from ..data.tables_manager import TablesManager
from .common_api_class import (AbstractApi, ApiError)


class GetColumnNameList(AbstractApi):
    """
    カラム名のリストを取得するAPIクラス

    データベースの指定されたテーブルに存在するすべてのカラム名を取得します。
    """
    def __init__(self, table_name: str):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.param_names = {
            'table_name': 'tableName',
        }

    def validate(self):
        try:
            validator = InputValidator(param_names=self.param_names,
                                       **INPUT_VALIDATOR_CONFIG)
            table_name_list = self.tables_manager.get_table_name_list()
            validator.validate_existed_table_name(
                self.table_name, table_name_list)
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            column_name_list = self.tables_manager.get_column_name_list(
                self.table_name)
            result = {
                'tableName': self.table_name,
                'columnNameList': column_name_list
            }
            return result
        except Exception as e:
            message = _(f"An unexpected error during "
                        f"getting column name list: {str(e)}")
            raise ApiError(message) from e


def get_column_name_list(table_name: str):
    """
    指定されたテーブルのカラム名のリストを取得する関数
    :param table_name: テーブル名
    :return: カラム名のリスト
    """
    api = GetColumnNameList(table_name)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    return api.execute()
