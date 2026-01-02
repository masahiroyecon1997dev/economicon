from typing import Dict
from .django_compat import gettext as _
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_manager_validator import (
    validate_existed_table_name,
    validate_new_table_name
)
from .data.tables_manager import TablesManager
from .abstract_api import AbstractApi, ApiError


class RenameTableName(AbstractApi):
    """
    繝・・繝悶Ν蜷榊､画峩API縺ｮPython繝ｭ繧ｸ繝・け

    譌｢蟄倥・繝・・繝悶Ν縺ｮ蜷榊燕繧呈眠縺励＞蜷榊燕縺ｫ螟画峩縺励∪縺吶・    蜷後§繝・・繝悶Ν蜷阪′譌｢縺ｫ蟄伜惠縺吶ｋ蝣ｴ蜷医・繧ｨ繝ｩ繝ｼ縺ｨ縺ｪ繧翫∪縺吶・    """
    def __init__(self, old_table_name: str, new_table_name: str):
        self.tables_manager = TablesManager()
        # 螟画峩蜑阪・繝・・繝悶Ν蜷・        self.old_table_name = old_table_name
        # 螟画峩蠕後・繝・・繝悶Ν蜷・        self.new_table_name = new_table_name
        # 繝代Λ繝｡繝ｼ繧ｿ蜷阪・繝槭ャ繝斐Φ繧ｰ
        self.param_names = {
            'table_name': 'oldTableName',
            'new_table_name': 'newTableName',
        }

    def validate(self):
        # 蜈･蜉帛､縺ｮ繝舌Μ繝・・繧ｷ繝ｧ繝ｳ
        try:
            table_name_list = self.tables_manager.get_table_name_list()
            # 螟画峩蜑阪・繝・・繝悶Ν蜷阪・蟄伜惠繝√ぉ繝・け
            validate_existed_table_name(
                self.old_table_name,
                table_name_list,
                self.param_names['table_name'])
            # 螟画峩蠕後・繝・・繝悶Ν蜷阪・驥崎､・メ繧ｧ繝・け
            validate_new_table_name(
                self.new_table_name,
                table_name_list,
                self.param_names['new_table_name'])
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # 繝・・繝悶Ν蜷阪・螟画峩蜃ｦ逅・        try:
            # 螟画峩蜑阪・繝・・繝悶Ν諠・ｱ繧貞叙蠕励＠縲∝炎髯､
            renamed_table_name = self.tables_manager.rename_table(
                self.old_table_name, self.new_table_name
            )
            # 邨先棡繧定ｿ斐☆
            result = {'tableName': renamed_table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "table rename processing")
            raise ApiError(message) from e


def rename_table(old_table_name: str, new_table_name: str) -> Dict:
    api = RenameTableName(old_table_name, new_table_name)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
