from ..utils.validator.common_validators import (ValidationError,
                                                 validate_integer_positive,
                                                 validate_required)
from ..utils.validator.tables_store_validator import (
    validate_existed_table_name, validate_row_index)
from .abstract_api import AbstractApi, ApiError
from .data.tables_store import TablesStore
from .django_compat import gettext as _


class FetchDataToJson(AbstractApi):
    """
    テーブルのデータフレームをJSON形式で取得するAPIクラス

    指定されたテーブルの指定された開始行から指定された行数のデータをJSON形式で取得します。
    行番号は1から始まると仮定しています。
    取得行数がテーブルの行数を超える場合は、テーブルの最後まで取得します。
    """
    def __init__(self, table_name: str, start_row: int, fetch_rows: int):
        self.tables_store = TablesStore()
        self.table_name = table_name
        self.start_row = start_row
        self.fetch_rows = fetch_rows
        self.param_names = {
            'table_name': 'tableName',
            'start_row': 'startRow',
            'fetch_rows': 'fetchRows',
        }

    def validate(self):
        try:
            # 必須パラメータのチェック
            validate_required(self.table_name, self.param_names['table_name'])
            validate_required(self.start_row, self.param_names['start_row'])
            validate_required(self.fetch_rows, self.param_names['fetch_rows'])

            table_name_list = self.tables_store.get_table_name_list()
            # テーブル名の存在チェック
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )
            num_rows = self.tables_store.get_table(self.table_name).num_rows
            # 開始行番号の妥当性チェック
            validate_row_index(
                self.start_row,
                num_rows,
                self.param_names['start_row']
            )
            # 取得行数が正の整数であることをチェック
            validate_integer_positive(
                self.fetch_rows,
                self.param_names['fetch_rows']
            )

            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            # テーブルのデータを取得
            table = self.tables_store.get_table(self.table_name)
            start_row = int(self.start_row)
            fetch_rows = int(self.fetch_rows)
            total_rows = table.num_rows

            # 実際の終了行を計算（テーブルの行数を超えない範囲）
            end_row = min(start_row + fetch_rows - 1, total_rows)

            # 指定された行範囲のデータをJSON形式で取得
            data = table.table
            data_to_json = data[start_row - 1:end_row].write_json()
            result = {
                'tableName': self.table_name,
                'data': data_to_json,
                'totalRows': total_rows,
                'startRow': start_row,
                'endRow': end_row,
            }

            return result
        except Exception as e:
            message = _(f"An unexpected error during "
                        f"fetching data from table '{self.table_name}':"
                        f" {str(e)}")
            raise ApiError(message) from e


def fetch_data_to_json(table_name: str, start_row: int, fetch_rows: int):
    """
    テーブルのデータをJSON形式で取得する関数

    :param table_name: テーブル名
    :param start_row: 取得開始行（1から始まる）
    :param fetch_rows: 取得行数
    :return: JSON形式のデータとメタ情報（総行数、開始行、終了行）
    """
    api = FetchDataToJson(table_name, start_row, fetch_rows)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    return api.execute()
