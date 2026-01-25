from typing import Dict

from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_store_validator import (
    validate_existed_column_name, validate_existed_table_name,
    validate_new_column_name)
from .abstract_api import AbstractApi, ApiError
from .data.tables_store import TablesStore
from .django_compat import gettext as _


class RenameColumn(AbstractApi):
    """
    列名変更APIのPythonロジック

    指定されたテーブルの指定された列名を新しい列名に変更します。
    同じ列名が既に存在する場合はエラーとなります。
    """
    def __init__(self, table_name: str,
                 old_column_name: str,
                 new_column_name: str):
        self.tables_store = TablesStore()
        # テーブル名
        self.table_name = table_name
        # 変更前の列名
        self.old_column_name = old_column_name
        # 変更後の列名
        self.new_column_name = new_column_name
        # パラメータ名のマッピング
        self.param_names = {
            'table_name': 'tableName',
            'new_column_name': 'newColumnName',
            'old_column_name': 'oldColumnName',
        }

    def validate(self):
        # 入力値のバリデーション
        try:
            table_name_list = self.tables_store.get_table_name_list()
            # テーブル名の存在チェック
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                table_name_param=self.param_names['table_name']
            )
            # 変更前の列名の存在チェック
            column_name_list = self.tables_store.get_column_name_list(
                self.table_name)
            validate_existed_column_name(
                self.old_column_name,
                column_name_list,
                self.param_names['old_column_name']
            )
            # 変更後の列名の重複チェック
            validate_new_column_name(
                self.new_column_name,
                column_name_list,
                self.param_names['new_column_name']
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # 列名の変更処理
        try:
            # テーブル情報を取得
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table
            # 列名を変更
            new_df = df.rename({self.old_column_name: self.new_column_name})
            # 更新されたデータフレームを保存
            table_info.table = new_df
            renamed_table_name = self.tables_store.update_table(
                self.table_name, new_df
            )
            # 結果を返す
            result = {'tableName': renamed_table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "renaming column processing")
            raise ApiError(message) from e


def rename_column(table_name: str,
                  old_column_name: str,
                  new_column_name: str) -> Dict:
    api = RenameColumn(table_name, old_column_name, new_column_name)
    validation_error = api.validate()
    if validation_error:
        raise ValueError(validation_error.message)
    return api.execute()
