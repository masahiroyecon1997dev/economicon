from typing import ClassVar

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas import MoveColumnRequestBody
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import validate_existence


class MoveColumn:
    """
    列移動APIのPythonロジック

    指定されたテーブル内の列を、任意の位置に移動します。
    anchorColumnName の直前、または末尾（null 指定時）に挿入します。
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "table_name": "tableName",
        "column_name": "columnName",
        "anchor_column_name": "anchorColumnName",
    }

    def __init__(
        self,
        body: MoveColumnRequestBody,
        tables_store: TablesStore,
    ) -> None:
        self.tables_store = tables_store
        self.table_name = body.table_name
        self.column_name = body.column_name
        # None のとき末尾挿入
        self.anchor_column_name = body.anchor_column_name

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
            value=self.column_name,
            valid_list=column_name_list,
            target=self.PARAM_NAMES["column_name"],
        )
        if self.anchor_column_name is not None:
            validate_existence(
                value=self.anchor_column_name,
                valid_list=column_name_list,
                target=self.PARAM_NAMES["anchor_column_name"],
            )

    def execute(self) -> dict:
        try:
            df = self.tables_store.get_table(self.table_name).table
            # 列名リストから対象列を除去し、挿入位置を決定する
            cols: list[str] = list(df.columns)
            cols.remove(self.column_name)

            if self.anchor_column_name is None:
                # anchorColumnName が null → 末尾に追加
                cols.append(self.column_name)
            else:
                # anchor 列の直前に挿入（before セマンティクス）
                anchor_idx = cols.index(self.anchor_column_name)
                cols.insert(anchor_idx, self.column_name)

            new_df = df.select(cols)
            self.tables_store.update_table(self.table_name, new_df)

            return {
                "tableName": self.table_name,
                "columnNames": cols,
            }
        except Exception as e:
            message = _(
                "An unexpected error occurred during column move processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.MOVE_COLUMN_PROCESS_ERROR,
                message=message,
                detail=str(e),
            ) from e
