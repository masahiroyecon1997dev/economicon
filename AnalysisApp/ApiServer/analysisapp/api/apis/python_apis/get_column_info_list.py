from typing import Dict, List
from django.utils.translation import gettext as _
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.validator import Validator
from ..utilities.validator.validation_config import (
    INPUT_VALIDATOR_CONFIG)
from ..utilities.validator.common_validators import validate_boolean
from ..data.tables_manager import TablesManager
from .common_api_class import (AbstractApi, ApiError)


class GetColumnInfoList(AbstractApi):
    """
    カラムの情報のリストを取得するAPIクラス

    データベースの指定されたテーブルに存在するすべてのカラム名を取得します。
    """
    def __init__(self, table_name: str, is_number_only: str):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.is_number_only = is_number_only
        self.param_names = {
            'table_name': 'tableName',
            'is_number_only': 'isNumberOnly'
        }

    def validate(self):
        try:
            validator = Validator(param_names=self.param_names,
                                  **INPUT_VALIDATOR_CONFIG)
            table_name_list = self.tables_manager.get_table_name_list()
            validator.validate_existed_table_name(
                self.table_name, table_name_list)
            validate_boolean(self.is_number_only,
                             self.param_names['is_number_only'])
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            column_list = self.tables_manager.get_column_info_list(
                self.table_name)
            if self.is_number_only.lower() == 'true':
                column_info_list = ([{'name': name, 'type': dtype}
                                     for name, dtype
                                     in column_list.items()
                                     if dtype.is_numeric()])
            else:
                column_info_list = ([{'name': name, 'type': dtype}
                                     for name, dtype
                                     in column_list.items()])
            result = {
                'tableName': self.table_name,
                'columnInfoList': column_info_list
            }
            return result
        except Exception as e:
            message = _(f"An unexpected error during "
                        f"getting column info list: {str(e)}")
            raise ApiError(message) from e


def get_column_info_list(table_name: str,
                         is_number_only: str
                         ) -> Dict[str, List[Dict[str, str]]]:
    """
    指定されたテーブルのカラム名のリストを取得する関数
    :param table_name: テーブル名
    :return: カラム名のリスト
    """
    api = GetColumnInfoList(table_name, is_number_only)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    return api.execute()
