from ...i18n.translation import gettext as _
from ...utils import ProcessingError
from ..data.tables_store import TablesStore


class ClearTables:
    """
    全てのテーブル情報をクリアするためのAPIクラス

    TablesStoreに保存されている全てのテーブルを削除します。
    """

    def __init__(self):
        self.tables_store = TablesStore()
        self.param_names = {}

    def validate(self):
        # パラメータなしのため、バリデーションは不要
        return None

    def execute(self):
        try:
            self.tables_store.clear_tables()
            # 結果を返す（空の辞書）
            result = {}
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred "
                "during clearing tables processing"
            )
            raise ProcessingError(
                error_code="ClearTablesError", message=message, detail=str(e)
            )
