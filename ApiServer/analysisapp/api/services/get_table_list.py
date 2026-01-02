from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from .abstract_api import AbstractApi, ApiError


class GetTableList(AbstractApi):
    """
    繝・・繝悶Ν蜷阪・繝ｪ繧ｹ繝医ｒ蜿門ｾ励☆繧帰PI繧ｯ繝ｩ繧ｹ

    繝・・繧ｿ繝吶・繧ｹ縺ｫ蟄伜惠縺吶ｋ縺吶∋縺ｦ縺ｮ繝・・繝悶Ν蜷阪ｒ蜿門ｾ励＠縺ｾ縺吶・    """
    def __init__(
        self,
    ):
        self.tables_manager = TablesManager()

    def validate(
        self,
    ) -> None:
        # 繝代Λ繝｡繝ｼ繧ｿ縺御ｸ崎ｦ√↑縺溘ａ縲∽ｽ輔ｂ讀懆ｨｼ縺励↑縺・        return None

    def execute(
        self,
    ):
        try:
            table_name_list = self.tables_manager.get_table_name_list()
            result = {
                'tableNameList': table_name_list
            }
            return result
        except Exception as e:
            message = _("An unexpected error during getting table name list.")
            raise ApiError(message) from e


def get_table_list(
) -> dict:
    api = GetTableList()
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    return api.execute()
