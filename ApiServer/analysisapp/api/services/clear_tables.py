from typing import Dict

from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from .abstract_api import AbstractApi, ApiError


class ClearTables(AbstractApi):
    """
    蜈ｨ縺ｦ縺ｮ繝・・繝悶Ν諠・ｱ繧偵け繝ｪ繧｢縺吶ｋ縺溘ａ縺ｮAPI繧ｯ繝ｩ繧ｹ

    TablesManager縺ｫ菫晏ｭ倥＆繧後※縺・ｋ蜈ｨ縺ｦ縺ｮ繝・・繝悶Ν繧貞炎髯､縺励∪縺吶・    """
    def __init__(self):
        self.tables_manager = TablesManager()
        self.param_names = {}

    def validate(self):
        # 繝代Λ繝｡繝ｼ繧ｿ縺ｪ縺励・縺溘ａ縲√ヰ繝ｪ繝・・繧ｷ繝ｧ繝ｳ縺ｯ荳崎ｦ・        return None

    def execute(self):
        try:
            self.tables_manager.clear_tables()
            # 邨先棡繧定ｿ斐☆・育ｩｺ縺ｮ霎樊嶌・・            result = {}
            return result
        except Exception as e:
            message = _("An unexpected error occurred "
                        "during clearing tables processing")
            raise ApiError(message) from e


def clear_tables() -> Dict:
    api = ClearTables()
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    return api.execute()
