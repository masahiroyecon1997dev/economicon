from typing import Dict

from ...i18n.translation import gettext as _

from ..data.tables_store import TablesStore
from ...utils.validators.common import ValidationError
from ...utils.validators.tables_store import (
    validate_existed_column_name,
    validate_existed_table_name,
)
from ..abstract_api import AbstractApi, ApiError


class DeleteColumn(AbstractApi):
    """
    列削除APIのPythonロジック

    指定されたテーブルから指定された列を削除します。
    削除後のテーブルは更新されたデータフレームに置き換えられます。
    """

    def __init__(self, table_name: str, column_name: str):
        self.tables_store = TablesStore()
        # テーブル名
        self.table_name = table_name
        # 削除する列名
        self.column_name = column_name
        # パラメータ名のマッピング
        self.param_names = {
            "table_name": "tableName",
            "column_names": "columnName",
        }

    def validate(self):
        # 入力値のバリデーション
        try:
            table_name_list = self.tables_store.get_table_name_list()
            # テーブル名の存在チェック
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names["table_name"],
            )
            # 列名の存在チェック
            column_names = self.tables_store.get_column_name_list(
                self.table_name
            )
            validate_existed_column_name(
                self.column_name,
                column_names,
                self.param_names["column_names"],
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # 列の削除処理
        try:
            # テーブルからデータフレームを取得
            df = self.tables_store.get_table(self.table_name).table
            # 指定された列を削除
            new_df = df.drop(self.column_name)
            # 更新されたデータフレームを保存
            updated_table_name = self.tables_store.update_table(
                self.table_name, new_df
            )
            # 結果を返す
            result = {"tableName": updated_table_name}
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "column deletion processing"
            )
            raise ApiError(message) from e
