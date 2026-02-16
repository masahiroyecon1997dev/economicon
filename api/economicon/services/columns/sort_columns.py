from ...i18n.translation import gettext as _
from ...models import SortColumnsRequestBody
from ...utils import ProcessingError, ValidationError
from ...utils.validators import validate_existence
from ..data.tables_store import TablesStore


class SortColumns:
    """
    テーブルの列を指定してソートするためのAPIクラス

    指定されたテーブルを指定された列でソートします。
    複数列でのソート、昇順・降順の指定が可能です。
    """

    def __init__(self, body: SortColumnsRequestBody):
        self.tables_store = TablesStore()
        self.table_name = body.table_name
        self.sort_columns = body.sort_columns
        self.param_names = {
            "table_name": "tableName",
            "sort_columns": "sortColumns",
            "column_name": "columnName",
            "ascending": "ascending",
        }

    def validate(self):
        try:
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
            for sort_spec in self.sort_columns:
                # ソート指定された列が既存の列名の中に存在することを検証
                validate_existence(
                    value=sort_spec.column_name,
                    valid_list=column_name_list,
                    target=self.param_names["column_name"],
                )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            # ソート列とdescendingフラグを準備
            column_names = [spec.column_name for spec in self.sort_columns]
            descending_flags = [
                (not spec.ascending) for spec in self.sort_columns
            ]

            # polarsでソート実行
            if len(column_names) == 1:
                sorted_df = df.sort(
                    column_names[0], descending=descending_flags[0]
                )
            else:
                sorted_df = df.sort(column_names, descending=descending_flags)

            # ソート結果でテーブルを更新
            self.tables_store.update_table(self.table_name, sorted_df)

            # 結果を返す
            result = {"tableName": self.table_name}
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during column sorting processing"
            )
            raise ProcessingError(
                error_code="SortColumnsProcessError",
                message=message,
                detail=str(e),
            )
