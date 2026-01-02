from typing import Dict, List

from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from ..utils.validator.common_validators import (ValidationError,
                                                     validate_boolean)
from ..utils.validator.tables_manager_validator import \
    validate_existed_table_name
from .abstract_api import AbstractApi, ApiError


class GetColumnList(AbstractApi):
    """
    繧ｫ繝ｩ繝縺ｮ諠・ｱ縺ｮ繝ｪ繧ｹ繝医ｒ蜿門ｾ励☆繧帰PI繧ｯ繝ｩ繧ｹ

    繝・・繧ｿ繝吶・繧ｹ縺ｮ謖・ｮ壹＆繧後◆繝・・繝悶Ν縺ｫ蟄伜惠縺吶ｋ縺吶∋縺ｦ縺ｮ繧ｫ繝ｩ繝蜷阪ｒ蜿門ｾ励＠縺ｾ縺吶・    """
    def __init__(self, table_name: str, is_number_only: str):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.is_number_only = is_number_only
        self.param_names = {
            'table_name': 'tableName',
            'is_number_only': 'isNumberOnly'
        }

    def validate(self):
        try:
            table_name_list = self.tables_manager.get_table_name_list()
            validate_existed_table_name(
                self.table_name, table_name_list,
                self.param_names['table_name']
            )
            validate_boolean(self.is_number_only,
                             self.param_names['is_number_only'])
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            column_list = self.tables_manager.get_column_info_list(
                self.table_name)
            if self.is_number_only.lower() == 'true':
                column_info_list = ([{'name': name, 'type': str(dtype)}
                                     for name, dtype
                                     in column_list.items()
                                     if dtype.is_numeric()])
            else:
                column_info_list = ([{'name': name, 'type': str(dtype)}
                                     for name, dtype
                                     in column_list.items()])
            result = {
                'tableName': self.table_name,
                'columnInfoList': column_info_list
            }
            return result
        except Exception as e:
            message = _("An unexpected error during "
                        "getting column info list.")
            raise ApiError(message) from e


def get_column_list(table_name: str,
                    is_number_only: str
                    ) -> Dict[str, List[Dict[str, str]]]:
    """
    謖・ｮ壹＆繧後◆繝・・繝悶Ν縺ｮ繧ｫ繝ｩ繝蜷阪・繝ｪ繧ｹ繝医ｒ蜿門ｾ励☆繧矩未謨ｰ
    :param table_name: 繝・・繝悶Ν蜷・    :return: 繧ｫ繝ｩ繝蜷阪・繝ｪ繧ｹ繝・    """
    api = GetColumnList(table_name, is_number_only)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    return api.execute()
