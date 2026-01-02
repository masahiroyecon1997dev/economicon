import polars as pl
from typing import Dict
from .django_compat import gettext as _
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_manager_validator import (
    validate_existed_table_name,
    validate_existed_column_name,
    validate_row_index
)
from .data.tables_manager import TablesManager
from .abstract_api import AbstractApi, ApiError


class InputCellData(AbstractApi):
    """
    繧ｻ繝ｫ繝・・繧ｿ蜈･蜉妁PI縺ｮPython繝ｭ繧ｸ繝・け

    謖・ｮ壹＆繧後◆繝・・繝悶Ν縺ｮ謖・ｮ壹＆繧後◆繧ｻ繝ｫ縺ｫ譁ｰ縺励＞蛟､繧貞・蜉帙＠縺ｾ縺吶・    譌｢蟄倥・蛟､縺ｯ荳頑嶌縺阪＆繧後∪縺吶・    陦檎分蜿ｷ縺ｯ1縺九ｉ蟋九∪繧九→莉ｮ螳壹＠縺ｦ縺・∪縺吶・    """
    def __init__(self, table_name: str,
                 column_name: str,
                 row_index: int,
                 new_value):
        self.tables_manager = TablesManager()
        # 繝・・繝悶Ν蜷・        self.table_name = table_name
        # 繧ｫ繝ｩ繝蜷・        self.column_name = column_name
        # 陦後う繝ｳ繝・ャ繧ｯ繧ｹ
        self.row_index = row_index
        # 譁ｰ縺励＞蛟､
        self.new_value = new_value
        # 繝代Λ繝｡繝ｼ繧ｿ蜷阪・繝槭ャ繝斐Φ繧ｰ
        self.param_names = {
            'table_name': 'tableName',
            'column_names': 'columnName',
            'row_index': 'rowIndex',
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
            column_name_list = \
                self.tables_manager.get_column_name_list(self.table_name)
            # 繧ｫ繝ｩ繝蜷阪・蟄伜惠繝√ぉ繝・け
            validate_existed_column_name(
                self.column_name,
                column_name_list,
                self.param_names['column_names']
            )
            num_rows = self.tables_manager.get_table(self.table_name).num_rows
            # 陦後う繝ｳ繝・ャ繧ｯ繧ｹ縺ｮ螯･蠖捺ｧ繝√ぉ繝・け
            validate_row_index(
                self.row_index,
                num_rows,
                self.param_names['row_index']
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # 繧ｻ繝ｫ繝・・繧ｿ縺ｮ蜈･蜉帛・逅・        try:
            # 蟇ｾ雎｡繝・・繝悶Ν縺ｮ繝・・繧ｿ繝輔Ξ繝ｼ繝繧貞叙蠕・            df = self.tables_manager.get_table(self.table_name).table
            # 謖・ｮ壼・縺ｮ繝・・繧ｿ繧貞叙蠕励＠縺ｦ繧ｳ繝斐・
            numpy_array = df.get_column(self.column_name).to_list().copy()
            # 謖・ｮ夊｡後・繝・・繧ｿ繧呈眠縺励＞蛟､縺ｫ譖ｴ譁ｰ
            numpy_array[self.row_index - 1] = self.new_value
            # 譖ｴ譁ｰ縺輔ｌ縺溘ョ繝ｼ繧ｿ縺ｧSeries繧剃ｽ懈・
            modified_series = pl.Series(name=self.column_name,
                                        values=numpy_array, strict=False)
            # 繝・・繧ｿ繝輔Ξ繝ｼ繝繧呈峩譁ｰ
            new_df = df.with_columns(modified_series)
            # 譖ｴ譁ｰ縺輔ｌ縺溘ョ繝ｼ繧ｿ繝輔Ξ繝ｼ繝繧剃ｿ晏ｭ・            updated_table_name = \
                self.tables_manager.update_table(self.table_name, new_df)
            # 邨先棡繧定ｿ斐☆
            result = {'tableName': updated_table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "input cell data processing")
            raise ApiError(message) from e


def input_cell_data(table_name: str,
                    column_name: str,
                    row_index: int,
                    new_value) -> Dict:
    api = InputCellData(table_name, column_name, row_index, new_value)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
