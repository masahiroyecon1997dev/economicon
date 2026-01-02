from typing import Dict

from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_manager_validator import (
    validate_existed_table_name, validate_new_column_name)
from .abstract_api import AbstractApi, ApiError


class DuplicateTable(AbstractApi):
    """
    繝・・繝悶Ν繧定､・｣ｽ縺吶ｋ縺溘ａ縺ｮAPI繧ｯ繝ｩ繧ｹ

    謖・ｮ壹＆繧後◆繝・・繝悶Ν繧定､・｣ｽ縺励※縲∵眠縺励＞蜷榊燕縺ｧ霑ｽ蜉縺励∪縺吶・    """
    def __init__(self, source_table_name: str, new_table_name: str):
        self.tables_manager = TablesManager()
        self.source_table_name = source_table_name
        self.new_table_name = new_table_name
        self.param_names = {
                'table_name': 'tableName',
                'new_table_name': 'newTableName',
            }

    def validate(self):
        try:
            table_name_list = self.tables_manager.get_table_name_list()
            # 繧ｽ繝ｼ繧ｹ繝・・繝悶Ν縺ｮ蟄伜惠繝√ぉ繝・け
            validate_existed_table_name(
                self.source_table_name,
                table_name_list,
                self.param_names['table_name']
            )
            # 譁ｰ縺励＞繝・・繝悶Ν蜷阪・驥崎､・メ繧ｧ繝・け
            validate_new_column_name(
                self.new_table_name,
                table_name_list,
                self.param_names['new_table_name']
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            # 繧ｽ繝ｼ繧ｹ繝・・繝悶Ν繧貞叙蠕・            source_table_info = self.tables_manager.get_table(
                self.source_table_name)
            source_df = source_table_info.table

            # 繝・・繝悶Ν繧定､・｣ｽ
            duplicated_df = source_df.clone()

            # 譁ｰ縺励＞蜷榊燕縺ｧ繝・・繝悶Ν繧剃ｿ晏ｭ・            self.tables_manager.store_table(
                self.new_table_name, duplicated_df)

            # 邨先棡繧定ｿ斐☆
            result = {'tableName': self.new_table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "table duplication processing")
            raise ApiError(message) from e


def duplicate_table(source_table_name: str,
                    new_table_name: str) -> Dict:
    api = DuplicateTable(source_table_name, new_table_name)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
