from typing import Dict, List, Optional

import polars as pl
from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_manager_validator import (
    validate_existed_column_name, validate_existed_columns,
    validate_existed_table_name, validate_new_column_name)
from .abstract_api import AbstractApi, ApiError


class AddLagLeadColumn(AbstractApi):
    """
    繝・・繝悶Ν縺ｫ繝ｩ繧ｰ螟画焚繝ｻ繝ｪ繝ｼ繝牙､画焚蛻励ｒ霑ｽ蜉縺吶ｋ縺溘ａ縺ｮAPI繧ｯ繝ｩ繧ｹ

    謖・ｮ壹＆繧後◆繝・・繝悶Ν縺ｮ謖・ｮ壹＆繧後◆蛻励↓蟇ｾ縺励※繝ｩ繧ｰ繝ｻ繝ｪ繝ｼ繝牙､画焚繧剃ｽ懈・縺励・    譁ｰ縺励＞蛻励→縺励※霑ｽ蜉縺励∪縺吶ゅげ繝ｫ繝ｼ繝怜・縺梧欠螳壹＆繧後◆蝣ｴ蜷医・縲・    繧ｰ繝ｫ繝ｼ繝怜・縺ｧ縺ｮ繝ｩ繧ｰ繝ｻ繝ｪ繝ｼ繝牙､画焚繧剃ｽ懈・縺励∪縺吶・    """
    def __init__(self, table_name: str, source_column: str,
                 new_column_name: str, periods: int,
                 group_columns: Optional[List[str]] = None):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.source_column = source_column
        self.new_column_name = new_column_name
        self.periods = periods
        self.group_columns = group_columns or []
        self.param_names = {
                'table_name': 'tableName',
                'source_column_name': 'sourceColumn',
                'new_column_name': 'newColumnName',
                'periods': 'periods',
                'group_columns': 'groupColumns',
            }

    def validate(self):
        try:
            table_name_list = self.tables_manager.get_table_name_list()
            validate_existed_table_name(self.table_name,
                                        table_name_list,
                                        self.param_names['table_name'])
            column_name_list = self.tables_manager.get_column_name_list(
                self.table_name)
            validate_existed_column_name(self.source_column,
                                         column_name_list,
                                         self.param_names[
                                             'source_column_name'])
            validate_new_column_name(self.new_column_name,
                                     column_name_list,
                                     self.param_names['new_column_name'])

            # 繧ｰ繝ｫ繝ｼ繝怜・縺ｮ蟄伜惠遒ｺ隱・            if self.group_columns or len(self.group_columns) > 0:
                validate_existed_columns(self.group_columns,
                                         column_name_list,
                                         self.param_names['group_columns'])

            # periods縺梧紛謨ｰ縺ｧ縺ゅｋ縺薙→繧堤｢ｺ隱・            if not isinstance(self.periods, int):
                raise ValidationError(_("periods must be an integer"))

            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_manager.get_table(self.table_name)
            df = table_info.table

            # shift謫堺ｽ懊ｒ螳溯｡・            # Note: polars.shift(1) gives previous value (lag),
            # shift(-1) gives next value (lead)
            # But we want periods=-1 to mean lag, periods=1 to mean lead
            # So we need to negate the periods value
            shift_periods = -self.periods

            if self.group_columns:
                # 繧ｰ繝ｫ繝ｼ繝玲欠螳壹′縺ゅｋ蝣ｴ蜷・                df_with_lag_lead = df.with_columns(
                    pl.col(self.source_column)
                    .shift(shift_periods)
                    .over(self.group_columns)
                    .alias(self.new_column_name)
                )
            else:
                # 繧ｰ繝ｫ繝ｼ繝玲欠螳壹′縺ｪ縺・ｴ蜷・                df_with_lag_lead = df.with_columns(
                    pl.col(self.source_column)
                    .shift(shift_periods)
                    .alias(self.new_column_name)
                )

            # 譁ｰ縺励＞蛻励ｒ繝・・繧ｿ繝輔Ξ繝ｼ繝縺ｫ霑ｽ蜉
            self.tables_manager.update_table(
                self.table_name, df_with_lag_lead)

            # 邨先棡繧定ｿ斐☆
            result = {'tableName': self.table_name,
                      'columnName': self.new_column_name}
            return result
        except Exception as e:
            message = _("An unexpected error occurred during "
                        "adding lag/lead column processing")
            raise ApiError(message) from e


def add_lag_lead_column(table_name: str,
                        source_column: str,
                        new_column_name: str,
                        periods: int,
                        group_columns: Optional[List[str]] = None) -> Dict:
    api = AddLagLeadColumn(table_name, source_column, new_column_name,
                           periods, group_columns)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
