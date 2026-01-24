import polars as pl
from typing import Dict
from .django_compat import gettext as _
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_store_validator import (
    validate_existed_table_name,
    validate_existed_column_name,
    validate_row_index
)
from .data.tables_store import TablesStore
from .abstract_api import AbstractApi, ApiError


class InputCellData(AbstractApi):
    """
    セルデータ入力APIのPythonロジック

    指定されたテーブルの指定されたセルに新しい値を入力します。
    既存の値は上書きされます。
    行番号は1から始まると仮定しています。
    """
    def __init__(self, table_name: str,
                 column_name: str,
                 row_index: int,
                 new_value):
        self.tables_store = TablesStore()
        # テーブル名
        self.table_name = table_name
        # カラム名
        self.column_name = column_name
        # 行インデックス
        self.row_index = row_index
        # 新しい値
        self.new_value = new_value
        # パラメータ名のマッピング
        self.param_names = {
            'table_name': 'tableName',
            'column_names': 'columnName',
            'row_index': 'rowIndex',
        }

    def validate(self):
        # 入力値のバリデーション
        try:
            table_name_list = self.tables_store.get_table_name_list()
            # テーブル名の存在チェック
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )
            column_name_list = \
                self.tables_store.get_column_name_list(self.table_name)
            # カラム名の存在チェック
            validate_existed_column_name(
                self.column_name,
                column_name_list,
                self.param_names['column_names']
            )
            num_rows = self.tables_store.get_table(self.table_name).num_rows
            # 行インデックスの妥当性チェック
            validate_row_index(
                self.row_index,
                num_rows,
                self.param_names['row_index']
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # セルデータの入力処理
        try:
            # 対象テーブルのデータフレームを取得
            df = self.tables_store.get_table(self.table_name).table
            # 指定列のデータを取得してコピー
            numpy_array = df.get_column(self.column_name).to_list().copy()
            # 指定行のデータを新しい値に更新
            numpy_array[self.row_index - 1] = self.new_value
            # 更新されたデータでSeriesを作成
            modified_series = pl.Series(name=self.column_name,
                                        values=numpy_array, strict=False)
            # データフレームを更新
            new_df = df.with_columns(modified_series)
            # 更新されたデータフレームを保存
            updated_table_name = \
                self.tables_store.update_table(self.table_name, new_df)
            # 結果を返す
            result = {'tableName': updated_table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "input cell data processing")
            raise ApiError(message) from e


def input_cell_data(table_name: str,
                    column_name: str,
                    row_index: int,
                    new_value) -> Dict:
    api = InputCellData(table_name, column_name, row_index, new_value)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
