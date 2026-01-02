from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from ..utils.validator.common_validators import (ValidationError,
                                                     validate_integer_positive,
                                                     validate_required)
from ..utils.validator.tables_manager_validator import (
    validate_existed_table_name, validate_row_index)
from .abstract_api import AbstractApi, ApiError


class FetchDataToJson(AbstractApi):
    """
    繝・・繝悶Ν縺ｮ繝・・繧ｿ繝輔Ξ繝ｼ繝繧谷SON蠖｢蠑上〒蜿門ｾ励☆繧帰PI繧ｯ繝ｩ繧ｹ

    謖・ｮ壹＆繧後◆繝・・繝悶Ν縺ｮ謖・ｮ壹＆繧後◆髢句ｧ玖｡後°繧画欠螳壹＆繧後◆陦梧焚縺ｮ繝・・繧ｿ繧谷SON蠖｢蠑上〒蜿門ｾ励＠縺ｾ縺吶・    陦檎分蜿ｷ縺ｯ1縺九ｉ蟋九∪繧九→莉ｮ螳壹＠縺ｦ縺・∪縺吶・    蜿門ｾ苓｡梧焚縺後ユ繝ｼ繝悶Ν縺ｮ陦梧焚繧定ｶ・∴繧句ｴ蜷医・縲√ユ繝ｼ繝悶Ν縺ｮ譛蠕後∪縺ｧ蜿門ｾ励＠縺ｾ縺吶・    """
    def __init__(self, table_name: str, start_row: int, fetch_rows: int):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.start_row = start_row
        self.fetch_rows = fetch_rows
        self.param_names = {
            'table_name': 'tableName',
            'start_row': 'startRow',
            'fetch_rows': 'fetchRows',
        }

    def validate(self):
        try:
            # 蠢・医ヱ繝ｩ繝｡繝ｼ繧ｿ縺ｮ繝√ぉ繝・け
            validate_required(self.table_name, self.param_names['table_name'])
            validate_required(self.start_row, self.param_names['start_row'])
            validate_required(self.fetch_rows, self.param_names['fetch_rows'])

            table_name_list = self.tables_manager.get_table_name_list()
            # 繝・・繝悶Ν蜷阪・蟄伜惠繝√ぉ繝・け
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )
            num_rows = self.tables_manager.get_table(self.table_name).num_rows
            # 髢句ｧ玖｡檎分蜿ｷ縺ｮ螯･蠖捺ｧ繝√ぉ繝・け
            validate_row_index(
                self.start_row,
                num_rows,
                self.param_names['start_row']
            )
            # 蜿門ｾ苓｡梧焚縺梧ｭ｣縺ｮ謨ｴ謨ｰ縺ｧ縺ゅｋ縺薙→繧偵メ繧ｧ繝・け
            validate_integer_positive(
                self.fetch_rows,
                self.param_names['fetch_rows']
            )

            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            # 繝・・繝悶Ν縺ｮ繝・・繧ｿ繧貞叙蠕・            table = self.tables_manager.get_table(self.table_name)
            start_row = int(self.start_row)
            fetch_rows = int(self.fetch_rows)
            total_rows = table.num_rows

            # 螳滄圀縺ｮ邨ゆｺ・｡後ｒ險育ｮ暦ｼ医ユ繝ｼ繝悶Ν縺ｮ陦梧焚繧定ｶ・∴縺ｪ縺・ｯ・峇・・            end_row = min(start_row + fetch_rows - 1, total_rows)

            # 謖・ｮ壹＆繧後◆陦檎ｯ・峇縺ｮ繝・・繧ｿ繧谷SON蠖｢蠑上〒蜿門ｾ・            data = table.table
            data_to_json = data[start_row - 1:end_row].write_json()
            result = {
                'tableName': self.table_name,
                'data': data_to_json,
                'totalRows': total_rows,
                'startRow': start_row,
                'endRow': end_row,
            }

            return result
        except Exception as e:
            message = _(f"An unexpected error during "
                        f"fetching data from table '{self.table_name}':"
                        f" {str(e)}")
            raise ApiError(message) from e


def fetch_data_to_json(table_name: str, start_row: int, fetch_rows: int):
    """
    繝・・繝悶Ν縺ｮ繝・・繧ｿ繧谷SON蠖｢蠑上〒蜿門ｾ励☆繧矩未謨ｰ

    :param table_name: 繝・・繝悶Ν蜷・    :param start_row: 蜿門ｾ鈴幕蟋玖｡鯉ｼ・縺九ｉ蟋九∪繧具ｼ・    :param fetch_rows: 蜿門ｾ苓｡梧焚
    :return: JSON蠖｢蠑上・繝・・繧ｿ縺ｨ繝｡繧ｿ諠・ｱ・育ｷ剰｡梧焚縲・幕蟋玖｡後∫ｵゆｺ・｡鯉ｼ・    """
    api = FetchDataToJson(table_name, start_row, fetch_rows)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    return api.execute()
