from .django_compat import gettext as _
from typing import Dict, List
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_store_validator import (
    validate_existed_table_name,
    validate_existed_column_name
)
from ..utils.validator.common_validators import (
    validate_required_list,
    validate_item_in_dict,
    validate_list_length,
    validate_boolean
)
from .data.tables_store import TablesStore
from .abstract_api import (AbstractApi, ApiError)


class SortColumns(AbstractApi):
    """
    テーブルの列を指定してソートするためのAPIクラス

    指定されたテーブルを指定された列でソートします。
    複数列でのソート、昇順・降順の指定が可能です。
    """
    def __init__(self, table_name: str, sort_columns: List[Dict[str, str]]):
        self.tables_store = TablesStore()
        self.table_name = table_name
        self.sort_columns = sort_columns
        self.param_names = {
                'table_name': 'tableName',
                'sort_columns': 'sortColumns',
                'column_name': 'columnName',
                'ascending': 'ascending'
            }

    def validate(self):
        try:
            table_name_list = self.tables_store.get_table_name_list()
            validate_existed_table_name(self.table_name,
                                        table_name_list,
                                        self.param_names['table_name'])

            validate_required_list(self.sort_columns,
                                   self.param_names['sort_columns'])
            validate_list_length(self.sort_columns,
                                 1,
                                 self.param_names['sort_columns'],
                                 self.param_names['column_name'])
            column_name_list = self.tables_store.get_column_name_list(
                    self.table_name)
            for sort_spec in self.sort_columns:
                validate_item_in_dict(sort_spec,
                                      'columnName',
                                      self.param_names['column_name'])
                validate_item_in_dict(sort_spec,
                                      'ascending',
                                      self.param_names['ascending'])

                # 列名の存在チェック
                validate_existed_column_name(sort_spec['columnName'],
                                             column_name_list,
                                             self.param_names['column_name'])
                # ascendingフィールドがbooleanかチェック
                validate_boolean(sort_spec['ascending'],
                                 self.param_names['ascending'])
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            # ソート列とdescendingフラグを準備
            column_names = [spec['columnName'] for spec in self.sort_columns]
            descending_flags = [(not spec['ascending'] == 'true')
                                for spec in self.sort_columns]

            # polarsでソート実行
            if len(column_names) == 1:
                sorted_df = df.sort(column_names[0],
                                    descending=descending_flags[0])
            else:
                sorted_df = df.sort(column_names, descending=descending_flags)

            # ソート結果でテーブルを更新
            self.tables_store.update_table(self.table_name, sorted_df)

            # 結果を返す
            result = {'tableName': self.table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "column sorting processing")
            raise ApiError(message) from e


def sort_columns(table_name: str, sort_columns: List[Dict[str, str]]) -> Dict:
    api = SortColumns(table_name, sort_columns)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
