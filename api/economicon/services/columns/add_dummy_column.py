from typing import ClassVar

import polars as pl

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.models import AddDummyColumnRequestBody
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import (
    validate_existence,
    validate_non_existence,
)


class AddDummyColumn:
    """
    テーブルの指定列からダミー変数列を作成するためのAPIクラス

    指定されたテーブルの指定された列の値に基づいて、ダミー変数列を作成します。
    指定された値が1になり、それ以外の値は0になります。
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "table_name": "tableName",
        "source_column_name": "sourceColumnName",
        "dummy_column_name": "dummyColumnName",
        "add_position_column": "addPositionColumn",
        "target_value": "targetValue",
    }

    def __init__(
        self,
        body: AddDummyColumnRequestBody,
        tables_store: TablesStore,
    ):
        self.tables_store = tables_store
        self.table_name = body.table_name
        self.source_column_name = body.source_column_name
        self.dummy_column_name = body.dummy_column_name
        self.add_position_column = body.add_position_column
        self.target_value = body.target_value

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
        # 対象の列が存在することを検証
        validate_existence(
            value=self.source_column_name,
            valid_list=column_name_list,
            target=self.PARAM_NAMES["source_column_name"],
        )
        # ダミー列名が既存の列名と重複しないことを検証
        validate_non_existence(
            value=self.dummy_column_name,
            existing_list=column_name_list,
            target=self.PARAM_NAMES["dummy_column_name"],
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

            # ダミー変数列を作成（指定された値なら1、それ以外は0）
            dummy_values = (
                df[self.source_column_name] == self.target_value
            ).cast(pl.Int32)

            # 追加位置を計算（指定されたカラムの右隣）
            current_cols = df.columns
            target_idx = current_cols.index(self.add_position_column) + 1

            # 列の並び順を定義
            new_order = (
                current_cols[:target_idx]
                + [self.dummy_column_name]
                + current_cols[target_idx:]
            )

            # 新しい列をデータフレームに追加
            df_with_dummy = df.with_columns(
                dummy_values.alias(self.dummy_column_name)
            ).select(new_order)

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
                error_code=ErrorCode.ADD_DUMMY_COLUMN_PROCESS_ERROR,
                message=message,
                detail=str(e),
            ) from e
