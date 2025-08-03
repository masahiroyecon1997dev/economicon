from django.utils.translation import gettext as _
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.validator import InputValidator
from ..utilities.validator.validation_config import (
    INPUT_VALIDATOR_CONFIG)
from ..data.tables_manager import TablesManager
from .common_api_class import (AbstractApi, ApiError)


class FetchDataToJson(AbstractApi):
    """
    テーブルのデータフレームをJSON形式で取得するAPIクラス

    指定されたテーブルの指定された行範囲のデータをJSON形式で取得します。
    行番号は1から始まると仮定しています。
    """
    def __init__(self, table_name: str, first_row: int, last_row: int):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.first_row = first_row
        self.last_row = last_row
        self.param_names = {
            'table_name': 'tableName',
            'first_row': 'firstRow',
            'last_row': 'lastRow',
        }

    def validate(self):
        try:
            validator = InputValidator(param_names=self.param_names,
                                       **INPUT_VALIDATOR_CONFIG)
            table_name_list = self.tables_manager.get_table_name_list()
            # テーブル名の存在チェック
            validator.validate_existed_table_name(self.table_name,
                                                  table_name_list)
            num_rows = self.tables_manager.get_table(self.table_name).num_rows
            # 行番号の妥当性チェック
            validator.validate_row_index(self.first_row, num_rows, 'first_row')
            validator.validate_row_index(self.last_row, num_rows, 'last_row')

            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            # テーブルのデータを取得
            data = self.tables_manager.get_table(self.table_name).table
            first_row = int(self.first_row)
            last_row = int(self.last_row)
            # 指定された行範囲のデータをJSON形式で取得
            data_to_json = data[first_row - 1:last_row - 1].write_json()
            result = {
                'tableName': self.table_name, 'data': data_to_json
            }

            return result
        except Exception as e:
            message = _(f"An unexpected error during "
                        f"fetching data from table '{self.table_name}':"
                        f" {str(e)}")
            raise ApiError(message) from e


def fetch_data_to_json(table_name: str, first_row: int, last_row: int):
    """
    テーブルのデータをJSON形式で取得する関数

    :param table_name: テーブル名
    :param first_row: 取得開始行（1から始まる）
    :param last_row: 取得終了行（1から始まる）
    :return: JSON形式のデータ
    """
    api = FetchDataToJson(table_name, first_row, last_row)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    return api.execute()
