from typing import Dict

import polars as pl
from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_manager_validator import (
    validate_compare_value, validate_existed_column_name,
    validate_existed_table_name, validate_filter_condition,
    validate_is_compare_column, validate_new_table_name)
from .abstract_api import AbstractApi, ApiError


class FilterSingleCondition(AbstractApi):
    """
    蜊倅ｸ譚｡莉ｶ繝輔ぅ繝ｫ繧ｿ繝ｪ繝ｳ繧ｰAPI縺ｮPython繝ｭ繧ｸ繝・け

    謖・ｮ壹＆繧後◆繝・・繝悶Ν縺九ｉ謖・ｮ壹＆繧後◆譚｡莉ｶ縺ｫ蜷郁・縺吶ｋ陦後・縺ｿ繧呈歓蜃ｺ縺励・    譁ｰ縺励＞繝・・繝悶Ν繧剃ｽ懈・縺励∪縺吶・    """
    def __init__(self, new_table_name: str, table_name: str,
                 column_name: str, condition: str,
                 is_compare_column: str, compare_value: str):
        self.manager = TablesManager()
        # 譁ｰ縺励＞繝・・繝悶Ν蜷・        self.new_table_name = new_table_name
        # 繝輔ぅ繝ｫ繧ｿ繝ｪ繝ｳ繧ｰ蟇ｾ雎｡縺ｮ繝・・繝悶Ν蜷・        self.table_name = table_name
        # 繝輔ぅ繝ｫ繧ｿ繝ｪ繝ｳ繧ｰ蟇ｾ雎｡縺ｮ繧ｫ繝ｩ繝蜷・        self.column_name = column_name
        # 繝輔ぅ繝ｫ繧ｿ繝ｪ繝ｳ繧ｰ譚｡莉ｶ
        self.condition = condition
        # 豈碑ｼ・､縺後き繝ｩ繝縺九←縺・°
        self.is_compare_column = is_compare_column
        # 豈碑ｼ・､
        self.compare_value = compare_value
        # 繝代Λ繝｡繝ｼ繧ｿ蜷阪・繝槭ャ繝斐Φ繧ｰ
        self.param_names = {
            'new_table_name': 'newTableName',
            'table_name': 'tableName',
            'column_names': 'columnName',
            'condition': 'condition',
            'is_compare_column': 'isCompareColumn',
            'compare_value': 'compareValue',
        }

    def validate(self):
        # 蜈･蜉帛､縺ｮ繝舌Μ繝・・繧ｷ繝ｧ繝ｳ
        try:
            table_name_list = self.manager.get_table_name_list()
            # 譁ｰ縺励＞繝・・繝悶Ν蜷阪・驥崎､・メ繧ｧ繝・け
            validate_new_table_name(
                self.new_table_name,
                table_name_list,
                self.param_names['new_table_name']
            )
            # 譌｢蟄倥ユ繝ｼ繝悶Ν蜷阪・蟄伜惠繝√ぉ繝・け
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )
            # 繧ｫ繝ｩ繝蜷阪・蟄伜惠繝√ぉ繝・け
            column_names = self.manager.get_column_name_list(self.table_name)
            validate_existed_column_name(
                self.column_name,
                column_names,
                self.param_names['column_names']
            )
            # 繝輔ぅ繝ｫ繧ｿ繝ｪ繝ｳ繧ｰ譚｡莉ｶ縺ｮ螯･蠖捺ｧ繝√ぉ繝・け
            validate_filter_condition(
                self.condition,
                self.param_names['condition']
            )
            # 豈碑ｼ・､繧ｿ繧､繝励・螯･蠖捺ｧ繝√ぉ繝・け
            validate_is_compare_column(
                self.is_compare_column,
                self.param_names['is_compare_column']
            )
            # 豈碑ｼ・､縺ｮ螯･蠖捺ｧ繝√ぉ繝・け
            validate_compare_value(
                self.compare_value,
                self.param_names['compare_value']
            )
            # 豈碑ｼ・､縺後き繝ｩ繝縺ｮ蝣ｴ蜷医・蟄伜惠繝√ぉ繝・け
            if self.is_compare_column == 'true':
                validate_existed_column_name(
                    self.compare_value,
                    column_names,
                    self.param_names['compare_value']
                )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # 繝輔ぅ繝ｫ繧ｿ繝ｪ繝ｳ繧ｰ蜃ｦ逅・        try:
            # 蟇ｾ雎｡繝・・繝悶Ν縺ｮ繝・・繧ｿ繝輔Ξ繝ｼ繝繧貞叙蠕・            df = self.manager.get_table(self.table_name).table

            # 譚｡莉ｶ縺ｫ蠢懊§縺ｦ繝輔ぅ繝ｫ繧ｿ繝ｪ繝ｳ繧ｰ蜃ｦ逅・ｒ螳溯｡・            match self.condition:
                case 'equals':
                    # 遲我ｾ｡譚｡莉ｶ
                    filtered_df = df.filter(
                        pl.col(self.column_name) == (
                            pl.col(self.compare_value)
                            if self.is_compare_column == 'true'
                            else self.compare_value
                        )
                    )
                case 'notEquals':
                    # 髱樒ｭ我ｾ｡譚｡莉ｶ
                    filtered_df = df.filter(
                        pl.col(self.column_name) != (
                            pl.col(self.compare_value)
                            if self.is_compare_column == 'true'
                            else self.compare_value
                        )
                    )
                case 'greaterThan':
                    # 繧医ｊ螟ｧ縺阪＞譚｡莉ｶ
                    filtered_df = df.filter(
                        pl.col(self.column_name) > (
                            pl.col(self.compare_value)
                            if self.is_compare_column == 'true'
                            else self.compare_value
                        )
                    )
                case 'greaterThanOrEquals':
                    # 莉･荳頑擅莉ｶ
                    filtered_df = df.filter(
                        pl.col(self.column_name) >= (
                            pl.col(self.compare_value)
                            if self.is_compare_column == 'true'
                            else self.compare_value
                        )
                    )
                case 'lessThan':
                    # 繧医ｊ蟆上＆縺・擅莉ｶ
                    filtered_df = df.filter(
                        pl.col(self.column_name) < (
                            pl.col(self.compare_value)
                            if self.is_compare_column == 'true'
                            else self.compare_value
                        )
                    )
                case 'lessThanOrEquals':
                    # 莉･荳区擅莉ｶ
                    filtered_df = df.filter(
                        pl.col(self.column_name) <= (
                            pl.col(self.compare_value)
                            if self.is_compare_column == 'true'
                            else self.compare_value
                        )
                    )
                case _:
                    raise ValidationError(_('Invalid condition specified'))

            # 繝・・繝悶Ν諠・ｱ繧呈峩譁ｰ
            updated_table_name = self.manager.store_table(
                self.new_table_name, filtered_df
            )
            # 邨先棡繧定ｿ斐☆
            result = {'tableName': updated_table_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "filter processing")
            raise ApiError(message) from e


def filter_single_condition(
    new_table_name: str, table_name: str, column_name: str,
    condition: str, is_compare_column: str, compare_value: str
) -> Dict:
    api = FilterSingleCondition(
        new_table_name, table_name, column_name, condition,
        is_compare_column, compare_value
    )
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
