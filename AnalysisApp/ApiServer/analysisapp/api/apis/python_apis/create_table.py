import polars as pl
from django.utils.translation import gettext as _
from typing import Dict, List
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.validator import InputValidator
from ..utilities.validator.validation_config \
    import INPUT_VALIDATOR_CONFIG
from ..data.tables_manager import TablesManager
from .common_api_class import AbstractApi, ApiError


class CreateTable(AbstractApi):
    """
    テーブル作成APIのPythonロジック

    指定した名前とカラム数でテーブルを作成します。
    各カラムは空（None）の値で初期化されます。
    """
    def __init__(self, table_name: str,
                 table_number_of_rows: int,
                 columnNames: List[str]):
        self.tables_manager = TablesManager()
        # テーブル名
        self.table_name = table_name
        # テーブルの行数
        self.table_number_of_rows = table_number_of_rows
        # カラム名のリスト
        self.columnNames = columnNames
        # パラメータ名のマッピング
        self.param_names = {
            'table_name': 'tableName',
            'table_num_rows': 'tableNumberOfRows',
            'column_names': 'columnNames',
        }

    def validate(self):
        # 入力値のバリデーション
        try:
            validator = InputValidator(param_names=self.param_names,
                                       **INPUT_VALIDATOR_CONFIG)
            table_name_list = self.tables_manager.get_table_name_list()
            # テーブル名の重複チェック
            validator.validate_new_table_name(self.table_name, table_name_list)
            # 行数の妥当性チェック
            validator.validate_table_num_rows(self.table_number_of_rows)
            # カラム名の妥当性チェック
            validator.validate_new_columns(self.columnNames)
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # テーブルの作成処理
        try:
            # 空のデータを作成
            new_column_data_none = [None] * self.table_number_of_rows
            # 各カラムに空のデータを設定
            data = {col: new_column_data_none for col in self.columnNames}
            # DataFrameを作成
            df = pl.DataFrame(data)
            # テーブル情報を保存
            created_table_name = self.tables_manager.store_table(
                self.table_name, df)
            # 結果を返す
            result = {'tableName': created_table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "table creation processing")
            raise ApiError(message) from e


def create_table(table_name: str, table_number_of_rows: int,
                 columnNames: List[str]) -> Dict:
    api = CreateTable(table_name, table_number_of_rows, columnNames)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
