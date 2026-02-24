from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.models import FetchDataToJsonRequestBody
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import (
    validate_existence,
    validate_row_count_limit,
)


class FetchDataToJson:
    """
    テーブルのデータフレームをJSON形式で取得するAPIクラス

    指定されたテーブルの指定された開始行から指定された行数のデータをJSON形式で取得します。
    行番号は1から始まると仮定しています。
    取得行数がテーブルの行数を超える場合は、テーブルの最後まで取得します。
    """

    def __init__(
        self,
        body: FetchDataToJsonRequestBody,
        tables_store: TablesStore,
    ):
        self.tables_store = tables_store
        self.table_name = body.table_name
        self.start_row = body.start_row
        self.fetch_rows = body.fetch_rows
        self.param_names = {
            "table_name": "tableName",
            "start_row": "startRow",
            "fetch_rows": "fetchRows",
        }

    def validate(self):
        table_name_list = self.tables_store.get_table_name_list()
        # テーブル名の存在チェック
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.param_names["table_name"],
        )
        row_count = self.tables_store.get_table(self.table_name).row_count - 1
        # 開始行番号の妥当性チェック
        validate_row_count_limit(
            current_row_count=row_count,
            requested_count=self.start_row,
            target=self.param_names["start_row"],
        )

    def execute(self):
        try:
            # テーブルのデータを取得
            table = self.tables_store.get_table(self.table_name)
            start_row = int(self.start_row)
            fetch_rows = int(self.fetch_rows)
            total_rows = table.row_count

            end_row = min(start_row + fetch_rows, total_rows)

            # 指定された行範囲のデータをJSON形式で取得
            data = table.table
            data_to_json = data.slice(start_row, fetch_rows).write_json()
            result = {
                "tableName": self.table_name,
                "data": data_to_json,
                "totalRows": total_rows,
                "startRow": start_row,
                "endRow": end_row,
            }

            return result
        except Exception as e:
            message = _(
                f"An unexpected error during "
                f"fetching data from table '{self.table_name}':"
                f" {str(e)}"
            )
            raise ProcessingError(
                error_code=ErrorCode.FETCH_DATA_TO_JSON_ERROR,
                message=message,
                detail=str(e),
            ) from e
