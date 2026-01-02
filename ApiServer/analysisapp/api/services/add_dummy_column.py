from typing import Dict

import polars as pl
from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from ..utils.validator.common_validators import (ValidationError,
                                                     validate_required)
from ..utils.validator.tables_manager_validator import (
    validate_existed_column_name, validate_existed_table_name,
    validate_new_column_name)
from .abstract_api import AbstractApi, ApiError


class AddDummyColumn(AbstractApi):
    """
    繝・・繝悶Ν縺ｮ謖・ｮ壼・縺九ｉ繝繝溘・螟画焚蛻励ｒ菴懈・縺吶ｋ縺溘ａ縺ｮAPI繧ｯ繝ｩ繧ｹ

    謖・ｮ壹＆繧後◆繝・・繝悶Ν縺ｮ謖・ｮ壹＆繧後◆蛻励・蛟､縺ｫ蝓ｺ縺･縺・※縲√ム繝溘・螟画焚蛻励ｒ菴懈・縺励∪縺吶・    謖・ｮ壹＆繧後◆蛟､縺・縺ｫ縺ｪ繧翫√◎繧御ｻ･螟悶・蛟､縺ｯ0縺ｫ縺ｪ繧翫∪縺吶・    """
    def __init__(self, table_name: str, source_column_name: str,
                 dummy_column_name: str, target_value: str):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.source_column_name = source_column_name
        self.dummy_column_name = dummy_column_name
        self.target_value = target_value
        self.param_names = {
                'table_name': 'tableName',
                'source_column_name': 'sourceColumnName',
                'dummy_column_name': 'dummyColumnName',
                'target_value': 'targetValue',
            }

    def validate(self):
        try:
            table_name_list = self.tables_manager.get_table_name_list()
            validate_existed_table_name(self.table_name,
                                        table_name_list,
                                        self.param_names['table_name'])
            column_name_list = self.tables_manager.get_column_name_list(
                self.table_name)
            validate_existed_column_name(
                self.source_column_name,
                column_name_list,
                self.param_names['source_column_name']
            )
            validate_new_column_name(self.dummy_column_name,
                                     column_name_list,
                                     self.param_names['dummy_column_name'])
            validate_required(self.target_value,
                              self.param_names['target_value'])
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_manager.get_table(self.table_name)
            df = table_info.table

            # 繝繝溘・螟画焚蛻励ｒ菴懈・・域欠螳壹＆繧後◆蛟､縺ｪ繧・縲√◎繧御ｻ･螟悶・0・・            dummy_values = (
                df[self.source_column_name] == self.target_value).cast(
                    pl.Int32)
            dummy_column = pl.Series(self.dummy_column_name, dummy_values)

            # 譁ｰ縺励＞蛻励ｒ繝・・繧ｿ繝輔Ξ繝ｼ繝縺ｫ霑ｽ蜉
            df_with_dummy = df.with_columns(dummy_column)

            # 繝・・繝悶Ν繧呈峩譁ｰ
            self.tables_manager.update_table(
                self.table_name, df_with_dummy)

            # 邨先棡繧定ｿ斐☆
            result = {'tableName': self.table_name,
                      'dummyColumnName': self.dummy_column_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "adding dummy column processing")
            raise ApiError(message) from e


def add_dummy_column(table_name: str,
                     source_column_name: str,
                     dummy_column_name: str,
                     target_value: str) -> Dict:
    api = AddDummyColumn(table_name, source_column_name,
                         dummy_column_name, target_value)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
