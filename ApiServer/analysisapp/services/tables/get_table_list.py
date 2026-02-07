from ...i18n.translation import gettext as _

from ..data.tables_store import TablesStore
from ..abstract_api import AbstractApi, ApiError


class GetTableList(AbstractApi):
    """
    テーブル名のリストを取得するAPIクラス

    データベースに存在するすべてのテーブル名を取得します。
    """

    def __init__(
        self,
    ):
        self.tables_store = TablesStore()

    def validate(
        self,
    ) -> None:
        # パラメータが不要なため、何も検証しない
        return None

    def execute(
        self,
    ):
        try:
            table_name_list = self.tables_store.get_table_name_list()
            result = {"tableNameList": table_name_list}
            return result
        except Exception as e:
            message = _("An unexpected error during getting table name list.")
            raise ApiError(message) from e


def get_table_list() -> dict:
    api = GetTableList()
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    return api.execute()
