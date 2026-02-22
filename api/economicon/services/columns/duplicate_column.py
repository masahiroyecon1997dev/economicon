import polars as pl

from ...i18n.translation import gettext as _
from ...models import DuplicateColumnRequestBody
from ...utils import ProcessingError
from ...utils.validators import validate_existence, validate_non_existence
from ..data.tables_store import TablesStore


class DuplicateColumn:
    """
    テーブルの既存の列を複製して新しい列として追加するためのAPIクラス

    指定されたテーブルの指定された列を複製し、元の列の右隣に新しい列として挿入します。
    新しい列は元の列と同じ値で初期化されます。
    """

    def __init__(self, body: DuplicateColumnRequestBody):
        self.tables_store = TablesStore()
        self.table_name = body.table_name
        self.source_column_name = body.source_column_name
        self.new_column_name = body.new_column_name
        self.param_names = {
            "table_name": "tableName",
            "new_column_name": "newColumnName",
            "source_column_name": "sourceColumnName",
        }

    def validate(self):
        table_name_list = self.tables_store.get_table_name_list()
        # 対象のテーブルが存在することを検証
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.param_names["table_name"],
        )
        column_name_list = self.tables_store.get_column_name_list(
            self.table_name
        )
        # 追加する列名が既存の列名と重複しないことを検証
        validate_non_existence(
            value=self.new_column_name,
            existing_list=column_name_list,
            target=self.param_names["new_column_name"],
        )
        # 複製元の列名が既存の列名の中に存在することを検証
        validate_existence(
            value=self.source_column_name,
            valid_list=column_name_list,
            target=self.param_names["source_column_name"],
        )
        return None

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
            raise ProcessingError(
                error_code="DuplicateColumnProcessError",
                message=message,
                detail=str(e),
            ) from e
