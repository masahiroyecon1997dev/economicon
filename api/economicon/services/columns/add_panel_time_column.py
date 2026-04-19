from typing import ClassVar

import polars as pl

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas import AddPanelTimeColumnRequestBody
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import (
    validate_existence,
    validate_non_existence,
)


class AddPanelTimeColumn:
    """
    個体IDでグループ化して時間変数を追加するAPIクラス。

    各グループ（個体）の行順に start_value から step 刻みの
    整数列を生成する。パネルデータの年次・期次変数作成に使用。

    実装: pl.int_range(pl.len()).over(id_column) * step + start_value
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "table_name": "tableName",
        "id_column": "idColumn",
        "new_column_name": "newColumnName",
        "add_position_column": "addPositionColumn",
    }

    def __init__(
        self,
        body: AddPanelTimeColumnRequestBody,
        tables_store: TablesStore,
    ):
        self.tables_store = tables_store
        self.table_name = body.table_name
        self.id_column = body.id_column
        self.new_column_name = body.new_column_name
        self.add_position_column = body.add_position_column
        self.start_value = body.start_value
        self.step = body.step

    def validate(self) -> None:
        table_name_list = self.tables_store.get_table_name_list()
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.PARAM_NAMES["table_name"],
        )

        column_name_list = self.tables_store.get_column_name_list(
            self.table_name
        )
        validate_existence(
            value=self.id_column,
            valid_list=column_name_list,
            target=self.PARAM_NAMES["id_column"],
        )
        validate_non_existence(
            value=self.new_column_name,
            existing_list=column_name_list,
            target=self.PARAM_NAMES["new_column_name"],
        )
        validate_existence(
            value=self.add_position_column,
            valid_list=column_name_list,
            target=self.PARAM_NAMES["add_position_column"],
        )

    def execute(self) -> dict[str, str]:
        try:
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            # グループ内行番号 (0-indexed) * step + start_value
            time_col = (
                pl.int_range(pl.len()).over(self.id_column) * self.step
                + self.start_value
            ).alias(self.new_column_name)

            df = df.with_columns(time_col)

            # 列順の整理（add_position_column の右隣に挿入）
            current_cols = [c for c in df.columns if c != self.new_column_name]
            target_idx = current_cols.index(self.add_position_column) + 1
            new_order = (
                current_cols[:target_idx]
                + [self.new_column_name]
                + current_cols[target_idx:]
            )
            df = df.select(new_order)

            self.tables_store.update_table(self.table_name, df)

            return {
                "tableName": self.table_name,
                "columnName": self.new_column_name,
            }

        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "adding panel time column processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.ADD_PANEL_TIME_COLUMN_PROCESS_ERROR,
                message=message,
                detail=str(e),
            ) from e
