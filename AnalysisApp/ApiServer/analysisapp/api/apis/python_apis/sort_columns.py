import polars as pl
from django.utils.translation import gettext as _
from typing import Dict, List
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.validator import InputValidator
from ..utilities.validator.validation_config import (
    INPUT_VALIDATOR_CONFIG)
from ..data.tables_manager import TablesManager
from .common_api_class import (AbstractApi, ApiError)


class SortColumns(AbstractApi):
    """
    テーブルの列を指定してソートするためのAPIクラス

    指定されたテーブルを指定された列でソートします。
    複数列でのソート、昇順・降順の指定が可能です。
    """
    def __init__(self, table_name: str, sort_columns: List[Dict[str, any]]):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.sort_columns = sort_columns
        self.param_names = {
                'table_name': 'tableName',
                'column_names': 'columnName',
            }

    def validate(self):
        try:
            validator = InputValidator(param_names=self.param_names,
                                       **INPUT_VALIDATOR_CONFIG)
            table_name_list = self.tables_manager.get_table_name_list()
            validator.validate_existed_table_name(self.table_name,
                                                  table_name_list)
            
            # 各ソート列の検証
            if not self.sort_columns or len(self.sort_columns) == 0:
                raise ValidationError("sortColumns must not be empty")
            
            column_name_list = self.tables_manager.get_column_name_list(
                self.table_name)
            
            for sort_spec in self.sort_columns:
                if 'columnName' not in sort_spec:
                    raise ValidationError("columnName is required in sortColumns")
                if 'ascending' not in sort_spec:
                    raise ValidationError("ascending is required in sortColumns")
                
                column_name = sort_spec['columnName']
                ascending = sort_spec['ascending']
                
                # 列名の存在チェック
                validator.validate_existed_column_name(column_name,
                                                       column_name_list)
                # ascendingフィールドがbooleanかチェック
                if not isinstance(ascending, bool):
                    raise ValidationError("ascending must be boolean")
            
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_manager.get_table(self.table_name)
            df = table_info.table
            
            # ソート列とdescendingフラグを準備
            column_names = [spec['columnName'] for spec in self.sort_columns]
            descending_flags = [not spec['ascending'] for spec in self.sort_columns]
            
            # polarsでソート実行
            if len(column_names) == 1:
                sorted_df = df.sort(column_names[0], descending=descending_flags[0])
            else:
                sorted_df = df.sort(column_names, descending=descending_flags)
            
            # ソート結果でテーブルを更新
            self.tables_manager.update_table(self.table_name, sorted_df)
            
            # 結果を返す
            result = {'tableName': self.table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "column sorting processing")
            raise ApiError(message) from e


def sort_columns(table_name: str, sort_columns: List[Dict[str, any]]) -> Dict:
    api = SortColumns(table_name, sort_columns)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result