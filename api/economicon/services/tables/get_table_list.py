from ...core.enums import ErrorCode
from ...i18n.translation import gettext as _
from ...utils import ProcessingError
from ..data.tables_store import TablesStore


class GetTableList:
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
            message = _(
                "An unexpected error occurred during getting table name list."
            )
            raise ProcessingError(
                error_code=ErrorCode.GET_TABLE_LIST_ERROR,
                message=message,
                detail=str(e),
            ) from e
