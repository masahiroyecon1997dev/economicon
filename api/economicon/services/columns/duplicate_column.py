from typing import ClassVar

import polars as pl

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas import DuplicateColumnRequestBody
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import (
    validate_existence,
    validate_non_existence,
)


class DuplicateColumn:
    """
    テーブルの既存の列を複製して新しい列として追加するためのAPIクラス

    指定されたテーブルの指定された列を複製し、元の列の右隣に新しい列として挿入します。
    新しい列は元の列と同じ値で初期化されます。
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "table_name": "tableName",
        "new_column_name": "newColumnName",
        "source_column_name": "sourceColumnName",
        "add_position_column": "addPositionColumn",
    }

    def __init__(
        self,
        body: DuplicateColumnRequestBody,
        tables_store: TablesStore,
    ):
        self.tables_store = tables_store
        self.table_name = body.table_name
        self.source_column_name = body.source_column_name
        self.new_column_name = body.new_column_name
        self.add_position_column = body.add_position_column

    def validate(self):
        table_name_list = self.tables_store.get_table_name_list()
        # 対象のテーブルが存在することを検証
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.PARAM_NAMES["table_name"],
        )
        column_name_list = self.tables_store.get_column_name_list(
            self.table_name
        )
        # 追加する列名が既存の列名と重複しないことを検証
        validate_non_existence(
            value=self.new_column_name,
            existing_list=column_name_list,
            target=self.PARAM_NAMES["new_column_name"],
        )
        # 複製元の列名が既存の列名の中に存在することを検証
        validate_existence(
            value=self.source_column_name,
            valid_list=column_name_list,
            target=self.PARAM_NAMES["source_column_name"],
        )

        # 追加位置の列名が既存の列名の中に存在することを検証
        validate_existence(
            value=self.add_position_column,
            valid_list=column_name_list,
            target=self.PARAM_NAMES["add_position_column"],
        )

    def execute(self):
        try:
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            # 追加位置の計算（指定されたカラムの右隣）
            current_cols = df.columns
            target_idx = current_cols.index(self.add_position_column) + 1

            # 2. 列の並び順を定義
            new_order = (
                current_cols[:target_idx]
                + [self.new_column_name]
                + current_cols[target_idx:]
            )

            # 3. カラムの作成と並べ替えを一気に行う
            df_with_duplicated_col = df.with_columns(
                pl.col(self.source_column_name).alias(self.new_column_name)
            ).select(new_order)

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
                error_code=ErrorCode.DUPLICATE_COLUMN_PROCESS_ERROR,
                message=message,
                detail=str(e),
            ) from e
