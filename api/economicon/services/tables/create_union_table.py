from typing import Dict, List

import polars as pl

from ...i18n.translation import gettext as _
from ...utils.validators.common import ValidationError
from ...utils.validators.tables_store import (
    validate_existed_columns,
    validate_existed_tables,
    validate_new_table_name,
)
from ..abstract_api import AbstractApi, ApiError
from ..data.tables_store import TablesStore


class CreateUnionTable(AbstractApi):
    """
    ユニオンテーブル作成APIのPythonロジック

    複数のテーブルを指定された列でユニオン（結合）し、新しいテーブルを作成します。
    すべてのテーブルに共通する列名を指定して、それらの行を結合します。
    """

    def __init__(
        self,
        union_table_name: str,
        table_names: List[str],
        column_names: List[str],
    ):
        self.tables_store = TablesStore()
        # ユニオン後のテーブル名
        self.union_table_name = union_table_name
        # ユニオンするテーブル名リスト
        self.table_names = table_names
        # ユニオンする列名リスト
        self.column_names = column_names
        # パラメータ名のマッピング
        self.param_names = {
            "union_table_name": "unionTableName",
            "table_names": "tableNames",
            "column_names": "columnNames",
        }

    def validate(self):
        # 入力値のバリデーション
        try:
            table_name_list = self.tables_store.get_table_name_list()

            # 新しいテーブル名の重複チェック
            validate_new_table_name(
                self.union_table_name,
                table_name_list,
                self.param_names["union_table_name"],
            )

            validate_existed_tables(
                self.table_names,
                table_name_list,
                self.param_names["table_names"],
            )

            # すべてのテーブルで指定された列が存在することをチェック
            for table_name in self.table_names:
                table_column_name_list = (
                    self.tables_store.get_column_name_list(table_name)
                )
                validate_existed_columns(
                    self.column_names,
                    table_column_name_list,
                    self.param_names["column_names"],
                )

            return None
        except ValidationError as e:
            return e

    def execute(self):
        # テーブルユニオン処理
        try:
            # 各テーブルから指定された列のみを選択して
            # データフレームのリストを作成
            dataframes = []
            for table_name in self.table_names:
                df = self.tables_store.get_table(table_name).table
                # 指定された列のみを選択
                selected_df = df.select(self.column_names)
                dataframes.append(selected_df)

            # すべてのデータフレームをユニオン（縦方向に結合）
            union_df = pl.concat(dataframes, how="vertical")

            # 新しいテーブル情報を保存
            created_table_name = self.tables_store.store_table(
                self.union_table_name, union_df
            )

            # 結果を返す
            result = {"tableName": created_table_name}
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during union table creation processing"
            )
            raise ApiError(message) from e
