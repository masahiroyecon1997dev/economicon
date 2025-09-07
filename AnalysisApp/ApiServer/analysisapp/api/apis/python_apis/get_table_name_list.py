from django.utils.translation import gettext as _
from ..data.tables_manager import TablesManager
from .common_api_class import AbstractApi, ApiError


class GetTableNameList(AbstractApi):
    """
    テーブル名のリストを取得するAPIクラス

    データベースに存在するすべてのテーブル名を取得します。
    """
    def __init__(
        self,
    ):
        self.tables_manager = TablesManager()

    def validate(
        self,
    ) -> None:
        # パラメータが不要なため、何も検証しない
        return None

    def execute(
        self,
    ):
        try:
            table_name_list = self.tables_manager.get_table_name_list()
            result = {
                'tableNameList': table_name_list
            }
            return result
        except Exception as e:
            message = _("An unexpected error during getting table name list.")
            raise ApiError(message) from e


def get_table_name_list(
) -> dict:
    api = GetTableNameList()
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    return api.execute()
