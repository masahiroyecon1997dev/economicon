from typing import Dict

from ...i18n.translation import gettext as _

from ..data.tables_store import TablesStore
from ...utils.validator.common_validators import ValidationError
from ...utils.validator.tables_store_validator import (
    validate_existed_table_name,
)
from ..abstract_api import AbstractApi, ApiError


class DeleteTable(AbstractApi):
    """
    テーブル削除APIのPythonロジック

    指定されたテーブルを完全に削除します。
    削除後、テーブルは復元できません。
    """

    def __init__(self, table_name: str):
        self.tables_store = TablesStore()
        # 削除するテーブル名
        self.table_name = table_name
        # パラメータ名のマッピング
        self.param_names = {"table_name": "tableName"}

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
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # テーブルの削除処理
        try:
            # テーブル情報から削除
            self.tables_store.delete_table(self.table_name)
            # 結果を返す
            result = {"tableName": self.table_name}
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during table deletion processing"
            )
            raise ApiError(message) from e


def delete_table(table_name: str) -> Dict:
    api = DeleteTable(table_name)
    validation_error = api.validate()
    if validation_error:
        raise ValueError(validation_error.message)
    result = api.execute()
    return result
