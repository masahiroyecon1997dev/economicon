from typing import Dict

import polars as pl
from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_manager_validator import (
    validate_existed_column_name, validate_existed_table_name,
    validate_new_column_name)
from .abstract_api import AbstractApi, ApiError


class DuplicateColumn(AbstractApi):
    """
    繝・・繝悶Ν縺ｮ譌｢蟄倥・蛻励ｒ隍・｣ｽ縺励※譁ｰ縺励＞蛻励→縺励※霑ｽ蜉縺吶ｋ縺溘ａ縺ｮAPI繧ｯ繝ｩ繧ｹ

    謖・ｮ壹＆繧後◆繝・・繝悶Ν縺ｮ謖・ｮ壹＆繧後◆蛻励ｒ隍・｣ｽ縺励∝・縺ｮ蛻励・蜿ｳ髫｣縺ｫ譁ｰ縺励＞蛻励→縺励※謖ｿ蜈･縺励∪縺吶・    譁ｰ縺励＞蛻励・蜈・・蛻励→蜷後§蛟､縺ｧ蛻晄悄蛹悶＆繧後∪縺吶・    """
    def __init__(self, table_name: str, source_column_name: str,
                 new_column_name: str):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.source_column_name = source_column_name
        self.new_column_name = new_column_name
        self.param_names = {
                'table_name': 'tableName',
                'new_column_name': 'newColumnName',
                'source_column_name': 'sourceColumnName',
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
                self.source_column_name,
                column_name_list,
                self.param_names['source_column_name']
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_manager.get_table(self.table_name)
            df = table_info.table

            # 蜈・・蛻励・繝・・繧ｿ繧貞叙蠕・            source_column_data = df[self.source_column_name].to_list()

            # 謖ｿ蜈･菴咲ｽｮ繧定ｨ育ｮ暦ｼ亥・縺ｮ蛻励・蜿ｳ髫｣・・            insert_index = df.columns.index(self.source_column_name) + 1

            # 譁ｰ縺励＞蛻励ｒ蜈・・蛻励・繝・・繧ｿ縺ｧ菴懈・縺励√ョ繝ｼ繧ｿ繝輔Ξ繝ｼ繝縺ｫ謖ｿ蜈･
            df_with_duplicated_col = df.insert_column(
                index=insert_index,
                column=pl.Series(self.new_column_name, source_column_data))

            # 繝・・繝悶Ν繧呈峩譁ｰ
            self.tables_manager.update_table(
                self.table_name, df_with_duplicated_col)

            # 邨先棡繧定ｿ斐☆
            result = {'tableName': self.table_name,
                      'columnName': self.new_column_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "duplicating column processing")
            raise ApiError(message) from e


def duplicate_column(table_name: str,
                     source_column_name: str,
                     new_column_name: str) -> Dict:

    api = DuplicateColumn(table_name, source_column_name, new_column_name)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
