from typing import Dict
from django.utils.translation import gettext as _
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.input_validator import InputValidator
from ..utilities.validator.input_validation_config \
    import INPUT_VALIDATOR_CONFIG
from ..data.tables_manager import TablesManager
from .common_api_class import AbstractApi, ApiError


class DeleteColumn(AbstractApi):
    """
    列削除APIのPythonロジック

    指定されたテーブルから指定された列を削除します。
    削除後のテーブルは更新されたデータフレームに置き換えられます。
    """
    def __init__(self, table_name: str, column_name: str):
        self.tables_manager = TablesManager()
        # テーブル名
        self.table_name = table_name
        # 削除する列名
        self.column_name = column_name
        # パラメータ名のマッピング
        self.param_names = {
            'table_name': 'tableName',
            'column_names': 'columnName',
        }

    def validate(self):
        # 入力値のバリデーション
        try:
            table_name_list = self.tables_manager.get_table_name_list()
            validator = InputValidator(param_names=self.param_names,
                                       **INPUT_VALIDATOR_CONFIG)
            # テーブル名の存在チェック
            validator.validate_existed_table_name(self.table_name,
                                                  table_name_list)
            # 列名の存在チェック
            column_names = self.tables_manager.get_column_names(
                self.table_name)
            validator.validate_existed_column_name(self.column_name,
                                                   column_names)
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # 列の削除処理
        try:
            # テーブルからデータフレームを取得
            df = self.tables_manager.get_table(self.table_name).table
            # 指定された列を削除
            new_df = df.drop(self.column_name)
            # 更新されたデータフレームを保存
            updated_table_name = self.tables_manager.update_table(
                self.table_name, new_df
            )
            # 結果を返す
            result = {'tableName': updated_table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "column deletion processing")
            raise ApiError(message) from e


def delete_column(table_name: str, column_name: str) -> Dict:
    api = DeleteColumn(table_name, column_name)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
