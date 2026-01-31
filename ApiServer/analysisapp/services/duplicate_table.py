from typing import Dict

from ..i18n.translation import gettext as _

from .data.tables_store import TablesStore
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_store_validator import (
    validate_existed_table_name, validate_new_table_name)
from .abstract_api import AbstractApi, ApiError


class DuplicateTable(AbstractApi):
    """
    テーブルを複製するためのAPIクラス

    指定されたテーブルを複製して、新しい名前で追加します。
    """
    def __init__(self, table_name: str, new_table_name: str):
        self.tables_store = TablesStore()
        self.table_name = table_name
        self.new_table_name = new_table_name
        self.param_names = {
                'table_name': 'tableName',
                'new_table_name': 'newTableName',
            }

    def validate(self):
        try:
            table_name_list = self.tables_store.get_table_name_list()
            # ソーステーブルの存在チェック
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )
            # 新しいテーブル名の重複チェック
            validate_new_table_name(
                self.new_table_name,
                table_name_list,
                self.param_names['new_table_name']
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            # ソーステーブルを取得
            source_table_info = self.tables_store.get_table(
                self.table_name)
            source_df = source_table_info.table

            # テーブルを複製
            duplicated_df = source_df.clone()

            # 新しい名前でテーブルを保存
            self.tables_store.store_table(
                self.new_table_name, duplicated_df)

            # 結果を返す
            result = {'tableName': self.new_table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "table duplication processing")
            raise ApiError(message) from e


def duplicate_table(table_name: str,
                    new_table_name: str) -> Dict:
    api = DuplicateTable(table_name, new_table_name)
    validation_error = api.validate()
    if validation_error:
        raise ValueError(validation_error.message)
    result = api.execute()
    return result
