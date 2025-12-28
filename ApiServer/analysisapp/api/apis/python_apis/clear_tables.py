from typing import Dict

from django.utils.translation import gettext as _

from ..data.tables_manager import TablesManager
from .abstract_api import AbstractApi, ApiError


class ClearTables(AbstractApi):
    """
    全てのテーブル情報をクリアするためのAPIクラス

    TablesManagerに保存されている全てのテーブルを削除します。
    """
    def __init__(self):
        self.tables_manager = TablesManager()
        self.param_names = {}

    def validate(self):
        # パラメータなしのため、バリデーションは不要
        return None

    def execute(self):
        try:
            self.tables_manager.clear_tables()
            # 結果を返す（空の辞書）
            result = {}
            return result
        except Exception as e:
            message = _("An unexpected error occurred "
                        "during clearing tables processing")
            raise ApiError(message) from e


def clear_tables() -> Dict:
    api = ClearTables()
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    return api.execute()
