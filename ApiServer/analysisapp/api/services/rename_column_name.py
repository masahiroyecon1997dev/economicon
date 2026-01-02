from typing import Dict
from .django_compat import gettext as _
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_manager_validator import (
    validate_existed_table_name,
    validate_new_column_name,
    validate_existed_column_name
)
from .data.tables_manager import TablesManager
from .abstract_api import AbstractApi, ApiError


class RenameColumnName(AbstractApi):
    """
    蛻怜錐螟画峩API縺ｮPython繝ｭ繧ｸ繝・け

    謖・ｮ壹＆繧後◆繝・・繝悶Ν縺ｮ謖・ｮ壹＆繧後◆蛻怜錐繧呈眠縺励＞蛻怜錐縺ｫ螟画峩縺励∪縺吶・    蜷後§蛻怜錐縺梧里縺ｫ蟄伜惠縺吶ｋ蝣ｴ蜷医・繧ｨ繝ｩ繝ｼ縺ｨ縺ｪ繧翫∪縺吶・    """
    def __init__(self, table_name: str,
                 old_column_name: str,
                 new_column_name: str):
        self.tables_manager = TablesManager()
        # 繝・・繝悶Ν蜷・        self.table_name = table_name
        # 螟画峩蜑阪・蛻怜錐
        self.old_column_name = old_column_name
        # 螟画峩蠕後・蛻怜錐
        self.new_column_name = new_column_name
        # 繝代Λ繝｡繝ｼ繧ｿ蜷阪・繝槭ャ繝斐Φ繧ｰ
        self.param_names = {
            'table_name': 'tableName',
            'new_column_name': 'newColumnName',
            'old_column_name': 'oldColumnName',
        }

    def validate(self):
        # 蜈･蜉帛､縺ｮ繝舌Μ繝・・繧ｷ繝ｧ繝ｳ
        try:
            table_name_list = self.tables_manager.get_table_name_list()
            # 繝・・繝悶Ν蜷阪・蟄伜惠繝√ぉ繝・け
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                table_name_param=self.param_names['table_name']
            )
            # 螟画峩蜑阪・蛻怜錐縺ｮ蟄伜惠繝√ぉ繝・け
            column_name_list = self.tables_manager.get_column_name_list(
                self.table_name)
            validate_existed_column_name(
                self.old_column_name,
                column_name_list,
                self.param_names['old_column_name']
            )
            # 螟画峩蠕後・蛻怜錐縺ｮ驥崎､・メ繧ｧ繝・け
            validate_new_column_name(
                self.new_column_name,
                column_name_list,
                self.param_names['new_column_name']
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # 蛻怜錐縺ｮ螟画峩蜃ｦ逅・        try:
            # 繝・・繝悶Ν諠・ｱ繧貞叙蠕・            table_info = self.tables_manager.get_table(self.table_name)
            df = table_info.table
            # 蛻怜錐繧貞､画峩
            new_df = df.rename({self.old_column_name: self.new_column_name})
            # 譖ｴ譁ｰ縺輔ｌ縺溘ョ繝ｼ繧ｿ繝輔Ξ繝ｼ繝繧剃ｿ晏ｭ・            table_info.table = new_df
            renamed_table_name = self.tables_manager.update_table(
                self.table_name, new_df
            )
            # 邨先棡繧定ｿ斐☆
            result = {'tableName': renamed_table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "renaming column processing")
            raise ApiError(message) from e


def rename_column_name(table_name: str,
                       old_column_name: str,
                       new_column_name: str) -> Dict:
    api = RenameColumnName(table_name, old_column_name, new_column_name)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
