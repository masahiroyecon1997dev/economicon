from typing import ClassVar

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.models import DeleteTableRequestBody
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import validate_existence


class DeleteTable:
    """
    テーブル削除APIのPythonロジック

    指定されたテーブルを完全に削除します。
    削除後、テーブルは復元できません。
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "table_name": "tableName",
    }

    def __init__(
        self,
        body: DeleteTableRequestBody,
        tables_store: TablesStore,
    ):
        self.tables_store = tables_store
        # 削除するテーブル名
        self.table_name = body.table_name

    def validate(self):
        table_name_list = self.tables_store.get_table_name_list()
        # テーブル名の存在チェック
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.PARAM_NAMES["table_name"],
        )

    def execute(self):
        # テーブルの削除処理
        try:
            # テーブル情報から削除
            self.tables_store.delete_table(self.table_name)
            # 結果を返す
            result = {"tableName": self.table_name}
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during table deletion processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.TABLE_DELETION_ERROR,
                message=message,
                detail=str(e),
            ) from e
