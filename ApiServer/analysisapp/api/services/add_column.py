from typing import Dict

import polars as pl
from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_manager_validator import (
    validate_existed_column_name, validate_existed_table_name,
    validate_new_column_name)
from .abstract_api import AbstractApi, ApiError


class AddColumn(AbstractApi):
    """
    繝・・繝悶Ν縺ｫ譁ｰ縺励＞蛻励ｒ霑ｽ蜉縺吶ｋ縺溘ａ縺ｮAPI繧ｯ繝ｩ繧ｹ

    謖・ｮ壹＆繧後◆繝・・繝悶Ν縺ｮ謖・ｮ壹＆繧後◆菴咲ｽｮ縺ｫ譁ｰ縺励＞蛻励ｒ謖ｿ蜈･縺励∪縺吶・    譁ｰ縺励＞蛻励・遨ｺ・・one・峨・蛟､縺ｧ蛻晄悄蛹悶＆繧後∪縺吶・    """
    def __init__(
        self,
        table_name: str,
        new_column_name: str,
        add_position_column: str
    ):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.new_column_name = new_column_name
        self.add_position_column = add_position_column
        self.param_names = {
            'table_name': 'tableName',
            'new_column_name': 'newColumnName',
            'add_position_column': 'addPositionColumn',
        }

    def validate(self):
        try:
            table_name_list = self.tables_manager.get_table_name_list()
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )
            column_name_list = self.tables_manager.get_column_name_list(
                self.table_name)
            validate_new_column_name(
                self.new_column_name,
                column_name_list,
                self.param_names['new_column_name']
            )
            validate_existed_column_name(
                self.add_position_column,
                column_name_list,
                self.param_names['add_position_column']
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_manager.get_table(self.table_name)
            num_rows = table_info.num_rows
            new_column_data_none = [None] * num_rows
            df = table_info.table
            insert_index = df.columns.index(self.add_position_column) + 1
            df_with_new_col = df.insert_column(
                index=insert_index,
                column=pl.Series(self.new_column_name, new_column_data_none)
            )
            # 譁ｰ縺励＞蛻励ｒ繝・・繧ｿ繝輔Ξ繝ｼ繝縺ｫ霑ｽ蜉
            self.tables_manager.update_table(self.table_name, df_with_new_col)
            # 邨先棡繧定ｿ斐☆
            result = {
                'tableName': self.table_name,
                'columnName': self.new_column_name
            }
            return result
        except Exception as e:
            message = _("An unexpected error occurred "
                        "during adding column processing")
            raise ApiError(message) from e


def add_column(
    table_name: str,
    new_column_name: str,
    add_position_column: str
) -> Dict:
    api = AddColumn(table_name, new_column_name, add_position_column)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    return api.execute()
