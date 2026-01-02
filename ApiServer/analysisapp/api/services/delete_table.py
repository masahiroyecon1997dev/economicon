from typing import Dict

from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_manager_validator import \
    validate_existed_table_name
from .abstract_api import AbstractApi, ApiError


class DeleteTable(AbstractApi):
    """
    繝・・繝悶Ν蜑企勁API縺ｮPython繝ｭ繧ｸ繝・け

    謖・ｮ壹＆繧後◆繝・・繝悶Ν繧貞ｮ悟・縺ｫ蜑企勁縺励∪縺吶・    蜑企勁蠕後√ユ繝ｼ繝悶Ν縺ｯ蠕ｩ蜈・〒縺阪∪縺帙ｓ縲・    """
    def __init__(self, table_name: str):
        self.tables_manager = TablesManager()
        # 蜑企勁縺吶ｋ繝・・繝悶Ν蜷・        self.table_name = table_name
        # 繝代Λ繝｡繝ｼ繧ｿ蜷阪・繝槭ャ繝斐Φ繧ｰ
        self.param_names = {'table_name': 'tableName'}

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
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # 繝・・繝悶Ν縺ｮ蜑企勁蜃ｦ逅・        try:
            # 繝・・繝悶Ν諠・ｱ縺九ｉ蜑企勁
            self.tables_manager.delete_table(self.table_name)
            # 邨先棡繧定ｿ斐☆
            result = {'tableName': self.table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "table deletion processing")
            raise ApiError(message) from e


def delete_table(table_name: str) -> Dict:
    api = DeleteTable(table_name)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
