from typing import ClassVar

import polars as pl

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.models import InputCellDataRequestBody
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import (
    validate_existence,
    validate_row_count_limit,
)


class InputCellData:
    """
    セルデータ入力APIのPythonロジック

    指定されたテーブルの指定されたセルに新しい値を入力します。
    既存の値は上書きされます。
    行番号は1から始まると仮定しています。
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "table_name": "tableName",
        "column_names": "columnName",
        "row_index": "rowIndex",
    }

    def __init__(
        self,
        body: InputCellDataRequestBody,
        tables_store: TablesStore,
    ):
        self.tables_store = tables_store
        # テーブル名
        self.table_name = body.table_name
        # カラム名
        self.column_name = body.column_name
        # 行インデックス
        self.row_index = body.row_index
        # 新しい値
        self.new_value = body.new_value

    def validate(self):
        table_name_list = self.tables_store.get_table_name_list()
        # テーブル名の存在チェック
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.PARAM_NAMES["table_name"],
        )
        column_name_list = self.tables_store.get_column_name_list(
            self.table_name
        )
        # カラム名の存在チェック
        validate_existence(
            value=self.column_name,
            valid_list=column_name_list,
            target=self.PARAM_NAMES["column_names"],
        )
        row_count = self.tables_store.get_table_row_count(self.table_name) - 1
        # 行インデックスの妥当性チェック
        validate_row_count_limit(
            current_row_count=row_count,
            requested_count=self.row_index,
            target=self.PARAM_NAMES["row_index"],
        )

    def execute(self):
        # セルデータの入力処理
        try:
            # 対象テーブルのデータフレームを取得
            df = self.tables_store.get_table(self.table_name).table
            # 指定列のデータを取得してコピー
            numpy_array = df.get_column(self.column_name).to_list().copy()
            # 指定行のデータを新しい値に更新
            numpy_array[self.row_index] = self.new_value
            # 更新されたデータでSeriesを作成
            modified_series = pl.Series(
                name=self.column_name, values=numpy_array, strict=False
            )
            # データフレームを更新
            new_df = df.with_columns(modified_series)
            # 更新されたデータフレームを保存
            updated_table_name = self.tables_store.update_table(
                self.table_name, new_df
            )
            # 結果を返す
            result = {"tableName": updated_table_name}
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "input cell data processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.INPUT_CELL_DATA_PROCESS_ERROR,
                message=message,
                detail=str(e),
            ) from e
