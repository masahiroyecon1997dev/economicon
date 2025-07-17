from typing import Dict
from django.utils.translation import gettext as _
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.input_validator import InputValidator
from ..utilities.validator.input_validation_config \
    import INPUT_VALIDATOR_CONFIG
from ..data.tables_manager import TablesManager
from .common_api_class import AbstractApi, ApiError


class RenameTableName(AbstractApi):
    """
    テーブル名変更APIのPythonロジック

    既存のテーブルの名前を新しい名前に変更します。
    同じテーブル名が既に存在する場合はエラーとなります。
    """
    def __init__(self, old_table_name: str, new_table_name: str):
        self.tables_manager = TablesManager()
        # 変更前のテーブル名
        self.old_table_name = old_table_name
        # 変更後のテーブル名
        self.new_table_name = new_table_name
        # パラメータ名のマッピング
        self.param_names = {
            'table_name': 'oldTableName',
            'new_table_name': 'newTableName',
        }

    def validate(self):
        # 入力値のバリデーション
        try:
            table_name_list = self.tables_manager.get_table_name_list()
            validator = InputValidator(param_names=self.param_names,
                                       **INPUT_VALIDATOR_CONFIG)
            # 変更前のテーブル名の存在チェック
            validator.validate_existed_table_name(self.old_table_name,
                                                  table_name_list)
            # 変更後のテーブル名の重複チェック
            validator.param_names['table_name'] = 'newTableName'
            validator.validate_new_table_name(self.new_table_name,
                                              table_name_list)
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # テーブル名の変更処理
        try:
            # 変更前のテーブル情報を取得し、削除
            renamed_table_name = self.tables_manager.rename_table(
                self.old_table_name, self.new_table_name
            )
            # 結果を返す
            result = {'tableName': renamed_table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "table rename processing")
            raise ApiError(message) from e


def rename_table(old_table_name: str, new_table_name: str) -> Dict:
    api = RenameTableName(old_table_name, new_table_name)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
