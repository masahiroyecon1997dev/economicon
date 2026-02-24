from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.models import GetColumnListRequestBody
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import validate_existence


class GetColumnList:
    """
    カラムの情報のリストを取得するAPIクラス

    データベースの指定されたテーブルに存在するすべてのカラム名を取得します。
    """

    def __init__(
        self,
        body: GetColumnListRequestBody,
        tables_store: TablesStore,
    ):
        self.tables_store = tables_store
        self.table_name = body.table_name
        self.is_number_only = body.is_number_only
        self.param_names = {
            "table_name": "tableName",
            "is_number_only": "isNumberOnly",
        }

    def validate(self):
        table_name_list = self.tables_store.get_table_name_list()
        # 対象のテーブルが存在することを検証
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.param_names["table_name"],
        )

    def execute(self):
        try:
            column_list = self.tables_store.get_schema(self.table_name)
            if self.is_number_only:
                column_info_list = [
                    {"name": name, "type": str(dtype)}
                    for name, dtype in column_list.items()
                    if dtype.is_numeric()
                ]
            else:
                column_info_list = [
                    {"name": name, "type": str(dtype)}
                    for name, dtype in column_list.items()
                ]
            result = {
                "tableName": self.table_name,
                "columnInfoList": column_info_list,
            }
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during getting column info list."
            )
            raise ProcessingError(
                error_code=ErrorCode.GET_COLUMN_LIST_PROCESS_ERROR,
                message=message,
                detail=str(e),
            ) from e
