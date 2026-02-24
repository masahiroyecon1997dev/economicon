from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.models import DuplicateTableRequestBody
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import (
    validate_existence,
    validate_non_existence,
)


class DuplicateTable:
    """
    テーブルを複製するためのAPIクラス

    指定されたテーブルを複製して、新しい名前で追加します。
    """

    def __init__(
        self,
        body: DuplicateTableRequestBody,
        tables_store: TablesStore,
    ):
        self.tables_store = tables_store
        self.table_name = body.table_name
        self.new_table_name = body.new_table_name
        self.param_names = {
            "table_name": "tableName",
            "new_table_name": "newTableName",
        }

    def validate(self):
        table_name_list = self.tables_store.get_table_name_list()
        # ソーステーブルの存在チェック
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.param_names["table_name"],
        )
        # 新しいテーブル名の重複チェック
        validate_non_existence(
            value=self.new_table_name,
            existing_list=table_name_list,
            target=self.param_names["new_table_name"],
        )

    def execute(self):
        try:
            # ソーステーブルを取得
            source_table_info = self.tables_store.get_table(self.table_name)
            source_df = source_table_info.table

            # テーブルを複製
            duplicated_df = source_df.clone()

            # 新しい名前でテーブルを保存
            self.tables_store.store_table(self.new_table_name, duplicated_df)

            # 結果を返す
            result = {"tableName": self.new_table_name}
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "table duplication processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.TABLE_DUPLICATION_ERROR,
                message=message,
                detail=str(e),
            ) from e
