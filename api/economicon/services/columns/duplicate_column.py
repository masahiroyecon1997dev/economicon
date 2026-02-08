import polars as pl

from ...i18n.translation import gettext as _
from ...utils.validators.common import ValidationError
from ...utils.validators.tables_store import (
    validate_existed_column_name,
    validate_existed_table_name,
    validate_new_column_name,
)
from ..abstract_api import AbstractApi, ApiError
from ..data.tables_store import TablesStore


class DuplicateColumn(AbstractApi):
    """
    テーブルの既存の列を複製して新しい列として追加するためのAPIクラス

    指定されたテーブルの指定された列を複製し、元の列の右隣に新しい列として挿入します。
    新しい列は元の列と同じ値で初期化されます。
    """

    def __init__(
        self, table_name: str, source_column_name: str, new_column_name: str
    ):
        self.tables_store = TablesStore()
        self.table_name = table_name
        self.source_column_name = source_column_name
        self.new_column_name = new_column_name
        self.param_names = {
            "table_name": "tableName",
            "new_column_name": "newColumnName",
            "source_column_name": "sourceColumnName",
        }

    def validate(self):
        try:
            table_name_list = self.tables_store.get_table_name_list()
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names["table_name"],
            )
            column_name_list = self.tables_store.get_column_name_list(
                self.table_name
            )
            validate_new_column_name(
                self.new_column_name,
                column_name_list,
                self.param_names["new_column_name"],
            )
            validate_existed_column_name(
                self.source_column_name,
                column_name_list,
                self.param_names["source_column_name"],
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            # 元の列のデータを取得
            source_column_data = df[self.source_column_name].to_list()

            # 挿入位置を計算（元の列の右隣）
            insert_index = df.columns.index(self.source_column_name) + 1

            # 新しい列を元の列のデータで作成し、データフレームに挿入
            df_with_duplicated_col = df.insert_column(
                index=insert_index,
                column=pl.Series(self.new_column_name, source_column_data),
            )

            # テーブルを更新
            self.tables_store.update_table(
                self.table_name, df_with_duplicated_col
            )

            # 結果を返す
            result = {
                "tableName": self.table_name,
                "columnName": self.new_column_name,
            }
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "duplicating column processing"
            )
            raise ApiError(message) from e
