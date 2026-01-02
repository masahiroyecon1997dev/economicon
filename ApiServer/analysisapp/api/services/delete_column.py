from typing import Dict

from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_manager_validator import (
    validate_existed_column_name, validate_existed_table_name)
from .abstract_api import AbstractApi, ApiError


class DeleteColumn(AbstractApi):
    """
    蛻怜炎髯､API縺ｮPython繝ｭ繧ｸ繝・け

    謖・ｮ壹＆繧後◆繝・・繝悶Ν縺九ｉ謖・ｮ壹＆繧後◆蛻励ｒ蜑企勁縺励∪縺吶・    蜑企勁蠕後・繝・・繝悶Ν縺ｯ譖ｴ譁ｰ縺輔ｌ縺溘ョ繝ｼ繧ｿ繝輔Ξ繝ｼ繝縺ｫ鄂ｮ縺肴鋤縺医ｉ繧後∪縺吶・    """
    def __init__(self, table_name: str, column_name: str):
        self.tables_manager = TablesManager()
        # 繝・・繝悶Ν蜷・        self.table_name = table_name
        # 蜑企勁縺吶ｋ蛻怜錐
        self.column_name = column_name
        # 繝代Λ繝｡繝ｼ繧ｿ蜷阪・繝槭ャ繝斐Φ繧ｰ
        self.param_names = {
            'table_name': 'tableName',
            'column_names': 'columnName',
        }

    def validate(self):
        # 蜈･蜉帛､縺ｮ繝舌Μ繝・・繧ｷ繝ｧ繝ｳ
        try:
            table_name_list = self.tables_manager.get_table_name_list()
            # 繝・・繝悶Ν蜷阪・蟄伜惠繝√ぉ繝・け
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )
            # 蛻怜錐縺ｮ蟄伜惠繝√ぉ繝・け
            column_names = self.tables_manager.get_column_name_list(
                self.table_name)
            validate_existed_column_name(
                self.column_name,
                column_names,
                self.param_names['column_names']
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # 蛻励・蜑企勁蜃ｦ逅・        try:
            # 繝・・繝悶Ν縺九ｉ繝・・繧ｿ繝輔Ξ繝ｼ繝繧貞叙蠕・            df = self.tables_manager.get_table(self.table_name).table
            # 謖・ｮ壹＆繧後◆蛻励ｒ蜑企勁
            new_df = df.drop(self.column_name)
            # 譖ｴ譁ｰ縺輔ｌ縺溘ョ繝ｼ繧ｿ繝輔Ξ繝ｼ繝繧剃ｿ晏ｭ・            updated_table_name = self.tables_manager.update_table(
                self.table_name, new_df
            )
            # 邨先棡繧定ｿ斐☆
            result = {'tableName': updated_table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "column deletion processing")
            raise ApiError(message) from e


def delete_column(table_name: str, column_name: str) -> Dict:
    api = DeleteColumn(table_name, column_name)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
