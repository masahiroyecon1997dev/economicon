from typing import Dict
from django.utils.translation import gettext as _
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.tables_manager_validator \
    import TablesManagerValidator
from ..utilities.validator.validation_config \
    import INPUT_VALIDATOR_CONFIG
from ..data.tables_manager import TablesManager
from .common_api_class import AbstractApi, ApiError


class DeleteTable(AbstractApi):
    """
    テーブル削除APIのPythonロジック

    指定されたテーブルを完全に削除します。
    削除後、テーブルは復元できません。
    """
    def __init__(self, table_name: str):
        self.tables_manager = TablesManager()
        # 削除するテーブル名
        self.table_name = table_name
        # パラメータ名のマッピング
        self.param_names = {'table_name': 'tableName'}

    def validate(self):
        # 入力値のバリデーション
        try:
            tables_manager_validator = TablesManagerValidator(
                param_names=self.param_names,
                **INPUT_VALIDATOR_CONFIG)
            table_name_list = self.tables_manager.get_table_name_list()
            # テーブル名の存在チェック
            tables_manager_validator.validate_existed_table_name(
                self.table_name,
                table_name_list
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # テーブルの削除処理
        try:
            # テーブル情報から削除
            self.tables_manager.delete_table(self.table_name)
            # 結果を返す
            result = {'tableName': self.table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "table deletion processing")
            raise ApiError(message) from e


def delete_table(table_name: str) -> Dict:
    api = DeleteTable(table_name)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
