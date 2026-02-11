from ...exceptions import ApiError
from ...i18n.translation import gettext as _
from ...utils.validators.common import (
    ValidationError,
)
from ...utils.validators.tables_store import (
    validate_existed_table_name,
)
from ..data.tables_store import TablesStore


class GetColumnList:
    """
    カラムの情報のリストを取得するAPIクラス

    データベースの指定されたテーブルに存在するすべてのカラム名を取得します。
    """

    def __init__(self, table_name: str, is_number_only: bool = False):
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
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            column_list = self.tables_store.get_column_info_list(
                self.table_name
            )
            if self.is_number_only:
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
