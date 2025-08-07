from django.utils.translation import gettext as _
from ..data.tables_manager import TablesManager
from .common_api_class import (AbstractApi, ApiError)


class GetTableNameList(AbstractApi):
    """
    テーブル名のリストを取得するAPIクラス

    データベースに存在するすべてのテーブル名を取得します。
    """
    def __init__(self):
        self.tables_manager = TablesManager()
        self.param_names = {
            'table_name': 'tableName',
        }

    def validate(self):
        pass

    def execute(self):
        try:
            table_name_list = self.tables_manager.get_table_name_list()
            result = {
                'tableNameList': table_name_list
            }
            return result
        except Exception as e:
            message = _(f"An unexpected error during "
                        f"getting table name list: {str(e)}")
            raise ApiError(message) from e


def get_table_name_list():
    """
    テーブル名のリストを取得する関数
    :return: テーブル名のリスト
    """
    api = GetTableNameList()
    return api.execute()
