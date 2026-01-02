from .django_compat import gettext as _
from typing import Dict, List
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_manager_validator import (
    validate_existed_table_name,
    validate_existed_column_name
)
from ..utils.validator.common_validators import (
    validate_required_list,
    validate_item_in_dict,
    validate_list_length,
    validate_boolean
)
from .data.tables_manager import TablesManager
from .abstract_api import (AbstractApi, ApiError)


class SortColumns(AbstractApi):
    """
    繝・・繝悶Ν縺ｮ蛻励ｒ謖・ｮ壹＠縺ｦ繧ｽ繝ｼ繝医☆繧九◆繧√・API繧ｯ繝ｩ繧ｹ

    謖・ｮ壹＆繧後◆繝・・繝悶Ν繧呈欠螳壹＆繧後◆蛻励〒繧ｽ繝ｼ繝医＠縺ｾ縺吶・    隍・焚蛻励〒縺ｮ繧ｽ繝ｼ繝医∵・鬆・・髯埼・・謖・ｮ壹′蜿ｯ閭ｽ縺ｧ縺吶・    """
    def __init__(self, table_name: str, sort_columns: List[Dict[str, str]]):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.sort_columns = sort_columns
        self.param_names = {
                'table_name': 'tableName',
                'sort_columns': 'sortColumns',
                'column_name': 'columnName',
                'ascending': 'ascending'
            }

    def validate(self):
        try:
            table_name_list = self.tables_manager.get_table_name_list()
            validate_existed_table_name(self.table_name,
                                        table_name_list,
                                        self.param_names['table_name'])

            validate_required_list(self.sort_columns,
                                   self.param_names['sort_columns'])
            validate_list_length(self.sort_columns,
                                 1,
                                 self.param_names['sort_columns'],
                                 self.param_names['column_name'])
            column_name_list = self.tables_manager.get_column_name_list(
                    self.table_name)
            for sort_spec in self.sort_columns:
                validate_item_in_dict(sort_spec,
                                      'columnName',
                                      self.param_names['column_name'])
                validate_item_in_dict(sort_spec,
                                      'ascending',
                                      self.param_names['ascending'])

                # 蛻怜錐縺ｮ蟄伜惠繝√ぉ繝・け
                validate_existed_column_name(sort_spec['columnName'],
                                             column_name_list,
                                             self.param_names['column_name'])
                # ascending繝輔ぅ繝ｼ繝ｫ繝峨′boolean縺九メ繧ｧ繝・け
                validate_boolean(sort_spec['ascending'],
                                 self.param_names['ascending'])
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_manager.get_table(self.table_name)
            df = table_info.table

            # 繧ｽ繝ｼ繝亥・縺ｨdescending繝輔Λ繧ｰ繧呈ｺ門ｙ
            column_names = [spec['columnName'] for spec in self.sort_columns]
            descending_flags = [(not spec['ascending'] == 'true')
                                for spec in self.sort_columns]

            # polars縺ｧ繧ｽ繝ｼ繝亥ｮ溯｡・            if len(column_names) == 1:
                sorted_df = df.sort(column_names[0],
                                    descending=descending_flags[0])
            else:
                sorted_df = df.sort(column_names, descending=descending_flags)

            # 繧ｽ繝ｼ繝育ｵ先棡縺ｧ繝・・繝悶Ν繧呈峩譁ｰ
            self.tables_manager.update_table(self.table_name, sorted_df)

            # 邨先棡繧定ｿ斐☆
            result = {'tableName': self.table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "column sorting processing")
            raise ApiError(message) from e


def sort_columns(table_name: str, sort_columns: List[Dict[str, str]]) -> Dict:
    api = SortColumns(table_name, sort_columns)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
