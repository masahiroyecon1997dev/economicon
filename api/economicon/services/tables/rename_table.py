from typing import ClassVar

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.models import RenameTableRequestBody
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import (
    validate_existence,
    validate_non_existence,
)


class RenameTable:
    """
    テーブル名変更APIのPythonロジック

    既存のテーブルの名前を新しい名前に変更します。
    同じテーブル名が既に存在する場合はエラーとなります。
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "table_name": "oldTableName",
        "new_table_name": "newTableName",
    }

    def __init__(
        self,
        body: RenameTableRequestBody,
        tables_store: TablesStore,
    ):
        self.tables_store = tables_store
        # 変更前のテーブル名
        self.old_table_name = body.old_table_name
        # 変更後のテーブル名
        self.new_table_name = body.new_table_name

    def validate(self):
        table_name_list = self.tables_store.get_table_name_list()
        # 変更前のテーブル名の存在チェック
        validate_existence(
            value=self.old_table_name,
            valid_list=table_name_list,
            target=self.PARAM_NAMES["table_name"],
        )
        # 変更後のテーブル名の重複チェック
        validate_non_existence(
            value=self.new_table_name,
            existing_list=table_name_list,
            target=self.PARAM_NAMES["new_table_name"],
        )

    def execute(self):
        # テーブル名の変更処理
        try:
            # 変更前のテーブル情報を取得し、削除
            renamed_table_name = self.tables_store.rename_table(
                self.old_table_name, self.new_table_name
            )
            # 結果を返す
            result = {"tableName": renamed_table_name}
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during table rename processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.TABLE_RENAME_ERROR,
                message=message,
                detail=str(e),
            ) from e
