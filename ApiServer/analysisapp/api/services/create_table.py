from typing import Dict, List

import polars as pl
from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_manager_validator import (
    validate_new_columns, validate_new_table_name, validate_table_num_rows)
from .abstract_api import AbstractApi, ApiError


class CreateTable(AbstractApi):
    """
    繝・・繝悶Ν菴懈・API縺ｮPython繝ｭ繧ｸ繝・け

    謖・ｮ壹＠縺溷錐蜑阪→繧ｫ繝ｩ繝謨ｰ縺ｧ繝・・繝悶Ν繧剃ｽ懈・縺励∪縺吶・    蜷・き繝ｩ繝縺ｯ遨ｺ・・one・峨・蛟､縺ｧ蛻晄悄蛹悶＆繧後∪縺吶・    """
    def __init__(self, table_name: str,
                 table_number_of_rows: int,
                 columnNames: List[str]):
        self.tables_manager = TablesManager()
        # 繝・・繝悶Ν蜷・        self.table_name = table_name
        # 繝・・繝悶Ν縺ｮ陦梧焚
        self.table_number_of_rows = table_number_of_rows
        # 繧ｫ繝ｩ繝蜷阪・繝ｪ繧ｹ繝・        self.columnNames = columnNames
        # 繝代Λ繝｡繝ｼ繧ｿ蜷阪・繝槭ャ繝斐Φ繧ｰ
        self.param_names = {
            'table_name': 'tableName',
            'table_num_rows': 'tableNumberOfRows',
            'column_names': 'columnNames',
        }

    def validate(self):
        # 蜈･蜉帛､縺ｮ繝舌Μ繝・・繧ｷ繝ｧ繝ｳ
        try:
            table_name_list = self.tables_manager.get_table_name_list()
            # 繝・・繝悶Ν蜷阪・驥崎､・メ繧ｧ繝・け
            validate_new_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )
            # 陦梧焚縺ｮ螯･蠖捺ｧ繝√ぉ繝・け
            validate_table_num_rows(
                self.table_number_of_rows,
                self.param_names['table_num_rows']
            )
            # 繧ｫ繝ｩ繝蜷阪・螯･蠖捺ｧ繝√ぉ繝・け
            validate_new_columns(
                self.columnNames,
                self.param_names['column_names']
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # 繝・・繝悶Ν縺ｮ菴懈・蜃ｦ逅・        try:
            # 遨ｺ縺ｮ繝・・繧ｿ繧剃ｽ懈・
            new_column_data_none = [None] * self.table_number_of_rows
            # 蜷・き繝ｩ繝縺ｫ遨ｺ縺ｮ繝・・繧ｿ繧定ｨｭ螳・            data = {col: new_column_data_none for col in self.columnNames}
            # DataFrame繧剃ｽ懈・
            df = pl.DataFrame(data)
            # 繝・・繝悶Ν諠・ｱ繧剃ｿ晏ｭ・            created_table_name = self.tables_manager.store_table(
                self.table_name, df)
            # 邨先棡繧定ｿ斐☆
            result = {'tableName': created_table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "table creation processing")
            raise ApiError(message) from e


def create_table(table_name: str, table_number_of_rows: int,
                 columnNames: List[str]) -> Dict:
    api = CreateTable(table_name, table_number_of_rows, columnNames)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
