from typing import Dict, List

from ...utils.validators.common_validators import (
    ValidationError,
    validate_boolean,
)
from ...utils.validators.tables_store_validator import (
    validate_existed_table_name,
)
from ..abstract_api import AbstractApi, ApiError
from ..data.tables_store import TablesStore
from ...i18n.translation import gettext as _


class GetColumnList(AbstractApi):
    """
    カラムの情報のリストを取得するAPIクラス

    データベースの指定されたテーブルに存在するすべてのカラム名を取得します。
    """

    def __init__(self, table_name: str, is_number_only: str):
        self.tables_store = TablesStore()
        self.table_name = table_name
        self.is_number_only = is_number_only
        self.param_names = {
            "table_name": "tableName",
            "is_number_only": "isNumberOnly",
        }

    def validate(self):
        try:
            table_name_list = self.tables_store.get_table_name_list()
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names["table_name"],
            )
            validate_boolean(
                self.is_number_only, self.param_names["is_number_only"]
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            column_list = self.tables_store.get_column_info_list(
                self.table_name
            )
            if self.is_number_only.lower() == "true":
                column_info_list = [
                    {"name": name, "type": str(dtype)}
                    for name, dtype in column_list.items()
                    if dtype.is_numeric()
                ]
            else:
                column_info_list = [
                    {"name": name, "type": str(dtype)}
                    for name, dtype in column_list.items()
                ]
            result = {
                "tableName": self.table_name,
                "columnInfoList": column_info_list,
            }
            return result
        except Exception as e:
            message = _("An unexpected error during getting column info list.")
            raise ApiError(message) from e


def get_column_list(
    table_name: str, is_number_only: str
) -> Dict[str, List[Dict[str, str]]]:
    """
    指定されたテーブルのカラム名のリストを取得する関数
    :param table_name: テーブル名
    :return: カラム名のリスト
    """
    api = GetColumnList(table_name, is_number_only)
    validation_error = api.validate()
    if validation_error:
        raise ValueError(validation_error.message)
    return api.execute()
