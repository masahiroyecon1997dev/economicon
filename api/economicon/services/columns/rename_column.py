from ...core.enums import ErrorCode
from ...i18n.translation import gettext as _
from ...models import RenameColumnRequestBody
from ...utils import ProcessingError
from ...utils.validators import validate_existence, validate_non_existence
from ..data.tables_store import TablesStore


class RenameColumn:
    """
    列名変更APIのPythonロジック

    指定されたテーブルの指定された列名を新しい列名に変更します。
    同じ列名が既に存在する場合はエラーとなります。
    """

    def __init__(self, body: RenameColumnRequestBody):
        self.tables_store = TablesStore()
        # テーブル名
        self.table_name = body.table_name
        # 変更前の列名
        self.old_column_name = body.old_column_name
        # 変更後の列名
        self.new_column_name = body.new_column_name
        # パラメータ名のマッピング
        self.param_names = {
            "table_name": "tableName",
            "new_column_name": "newColumnName",
            "old_column_name": "oldColumnName",
        }

    def validate(self):
        table_name_list = self.tables_store.get_table_name_list()
        # 対象のテーブルが存在することを検証
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.param_names["table_name"],
        )
        column_name_list = self.tables_store.get_column_name_list(
            self.table_name
        )
        # 変更前の列名が既存の列名の中に存在することを検証
        validate_existence(
            value=self.old_column_name,
            valid_list=column_name_list,
            target=self.param_names["old_column_name"],
        )
        # 変更後の列名が既存の列名と重複しないことを検証
        validate_non_existence(
            value=self.new_column_name,
            existing_list=column_name_list,
            target=self.param_names["new_column_name"],
        )
        return None

    def execute(self):
        # 列名の変更処理
        try:
            # テーブル情報を取得
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table
            # 列名を変更
            new_df = df.rename({self.old_column_name: self.new_column_name})
            # 更新されたデータフレームを保存
            table_info.table = new_df
            renamed_table_name = self.tables_store.update_table(
                self.table_name, new_df
            )
            # 結果を返す
            result = {"tableName": renamed_table_name}
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "renaming column processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.RENAME_COLUMN_PROCESS_ERROR,
                message=message,
                detail=str(e),
            ) from e
