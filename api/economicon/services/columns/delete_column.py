from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.models import DeleteColumnRequestBody
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import validate_existence


class DeleteColumn:
    """
    列削除APIのPythonロジック

    指定されたテーブルから指定された列を削除します。
    削除後のテーブルは更新されたデータフレームに置き換えられます。
    """

    def __init__(
        self,
        body: DeleteColumnRequestBody,
        tables_store: TablesStore,
    ):
        self.tables_store = tables_store
        # テーブル名
        self.table_name = body.table_name
        # 削除する列名
        self.column_name = body.column_name
        # パラメータ名のマッピング
        self.param_names = {
            "table_name": "tableName",
            "column_names": "columnName",
        }

    def validate(self):
        table_name_list = self.tables_store.get_table_name_list()
        # 対象のテーブルが存在することを検証
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.param_names["table_name"],
        )

        column_names = self.tables_store.get_column_name_list(self.table_name)
        # 対象の列が存在することを検証
        validate_existence(
            value=self.column_name,
            valid_list=column_names,
            target=self.param_names["column_names"],
        )

    def execute(self):
        # 列の削除処理
        try:
            # テーブルからデータフレームを取得
            df = self.tables_store.get_table(self.table_name).table
            # 指定された列を削除
            new_df = df.drop(self.column_name)
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
                "column deletion processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.DELETE_COLUMN_PROCESS_ERROR,
                message=message,
                detail=str(e),
            ) from e
