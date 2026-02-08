from typing import Dict, List

import polars as pl
from ...i18n.translation import gettext as _

from ..data.tables_store import TablesStore
from ...utils.validators.common import ValidationError
from ...utils.validators.tables_store import (
    validate_new_columns,
    validate_new_table_name,
    validate_table_num_rows,
)
from ..abstract_api import AbstractApi, ApiError


class CreateTable(AbstractApi):
    """
    テーブル作成APIのPythonロジック

    指定した名前とカラム数でテーブルを作成します。
    各カラムは空（None）の値で初期化されます。
    """

    def __init__(
        self,
        table_name: str,
        table_number_of_rows: int,
        column_names: List[str],
    ):
        self.tables_store = TablesStore()
        # テーブル名
        self.table_name = table_name
        # テーブルの行数
        self.table_number_of_rows = table_number_of_rows
        # カラム名のリスト
        self.column_names = column_names
        # パラメータ名のマッピング
        self.param_names = {
            "table_name": "tableName",
            "table_num_rows": "tableNumberOfRows",
            "column_names": "columnNames",
        }

    def validate(self):
        # 入力値のバリデーション
        try:
            table_name_list = self.tables_store.get_table_name_list()
            # テーブル名の重複チェック
            validate_new_table_name(
                self.table_name,
                table_name_list,
                self.param_names["table_name"],
            )
            # 行数の妥当性チェック
            validate_table_num_rows(
                self.table_number_of_rows, self.param_names["table_num_rows"]
            )
            # カラム名の妥当性チェック
            validate_new_columns(
                self.column_names, self.param_names["column_names"]
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # テーブルの作成処理
        try:
            # 空のデータを作成
            new_column_data_none = [None] * self.table_number_of_rows
            # 各カラムに空のデータを設定
            data = {col: new_column_data_none for col in self.column_names}
            # DataFrameを作成
            df = pl.DataFrame(data)
            # テーブル情報を保存
            created_table_name = self.tables_store.store_table(
                self.table_name, df
            )
            # 結果を返す
            result = {"tableName": created_table_name}
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during table creation processing"
            )
            raise ApiError(message) from e
