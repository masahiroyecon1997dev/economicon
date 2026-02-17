from ...i18n.translation import gettext as _
from ...models import RenameTableRequestBody
from ...utils import ProcessingError, ValidationError
from ...utils.validators import validate_existence, validate_non_existence
from ..data.tables_store import TablesStore


class RenameTable:
    """
    テーブル名変更APIのPythonロジック

    既存のテーブルの名前を新しい名前に変更します。
    同じテーブル名が既に存在する場合はエラーとなります。
    """

    def __init__(self, body: RenameTableRequestBody):
        self.tables_store = TablesStore()
        # 変更前のテーブル名
        self.old_table_name = body.old_table_name
        # 変更後のテーブル名
        self.new_table_name = body.new_table_name
        # パラメータ名のマッピング
        self.param_names = {
            "table_name": "oldTableName",
            "new_table_name": "newTableName",
        }

    def validate(self):
        try:
            table_name_list = self.tables_store.get_table_name_list()
            # 変更前のテーブル名の存在チェック
            validate_existence(
                value=self.old_table_name,
                valid_list=table_name_list,
                target=self.param_names["table_name"],
            )
            # 変更後のテーブル名の重複チェック
            validate_non_existence(
                value=self.new_table_name,
                existing_list=table_name_list,
                target=self.param_names["new_table_name"],
            )
            return None
        except ValidationError as e:
            return e

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
                error_code="TableRenameError",
                message=message,
                detail=str(e),
            ) from e
