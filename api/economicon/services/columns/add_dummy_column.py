import polars as pl

from ...i18n.translation import gettext as _
from ...models import AddDummyColumnRequestBody
from ...utils import ProcessingError, ValidationError
from ...utils.validators import validate_existence, validate_non_existence
from ..data.tables_store import TablesStore


class AddDummyColumn:
    """
    テーブルの指定列からダミー変数列を作成するためのAPIクラス

    指定されたテーブルの指定された列の値に基づいて、ダミー変数列を作成します。
    指定された値が1になり、それ以外の値は0になります。
    """

    def __init__(
        self,
        body: AddDummyColumnRequestBody,
    ):
        self.tables_store = TablesStore()
        self.table_name = body.table_name
        self.source_column_name = body.source_column_name
        self.dummy_column_name = body.dummy_column_name
        self.target_value = body.target_value
        self.param_names = {
            "table_name": "tableName",
            "source_column_name": "sourceColumnName",
            "dummy_column_name": "dummyColumnName",
            "target_value": "targetValue",
        }

    def validate(self):
        try:
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
            # 対象の列が存在することを検証
            validate_existence(
                value=self.source_column_name,
                valid_list=column_name_list,
                target=self.param_names["source_column_name"],
            )
            # ダミー列名が既存の列名と重複しないことを検証
            validate_non_existence(
                value=self.dummy_column_name,
                existing_list=column_name_list,
                target=self.param_names["dummy_column_name"],
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            # ダミー変数列を作成（指定された値なら1、それ以外は0）
            dummy_values = (
                df[self.source_column_name] == self.target_value
            ).cast(pl.Int32)
            dummy_column = pl.Series(self.dummy_column_name, dummy_values)

            # 新しい列をデータフレームに追加
            df_with_dummy = df.with_columns(dummy_column)

            # テーブルを更新
            self.tables_store.update_table(self.table_name, df_with_dummy)

            # 結果を返す
            result = {
                "tableName": self.table_name,
                "dummyColumnName": self.dummy_column_name,
            }
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "adding dummy column processing"
            )
            raise ProcessingError(
                error_code="AddDummyColumnProcessError",
                message=message,
                detail=str(e),
            )
