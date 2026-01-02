from typing import Any, Dict, List

import polars as pl
from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from ..utils.algorithm.simulation import generate_simulation_data
from ..utils.validator.common_validators import (ValidationError,
                                                     validate_integer)
from ..utils.validator.statistics_validators import (
    validate_distribution_params, validate_distribution_type)
from ..utils.validator.tables_manager_validator import (
    validate_new_column_name, validate_new_table_name)
from .abstract_api import AbstractApi, ApiError


class CreateSimulationDataTable(AbstractApi):
    """
    繧ｷ繝溘Η繝ｬ繝ｼ繧ｷ繝ｧ繝ｳ繝・・繧ｿ繝・・繝悶Ν繧剃ｽ懈・縺吶ｋ縺溘ａ縺ｮAPI繧ｯ繝ｩ繧ｹ

    謖・ｮ壹＆繧後◆繝・・繝悶Ν蜷阪〒譁ｰ縺励＞繝・・繝悶Ν繧剃ｽ懈・縺励∵欠螳壹＆繧後◆蛻苓ｨｭ螳壹↓蠕薙▲縺ｦ
    繧ｷ繝溘Η繝ｬ繝ｼ繧ｷ繝ｧ繝ｳ繝・・繧ｿ蛻励ｒ霑ｽ蜉縺励∪縺吶・    蜷・・縺ｯ蛻・ｸ・↓蠕薙≧繝ｩ繝ｳ繝繝繝・・繧ｿ縺ｾ縺溘・蝗ｺ螳壼､繧呈戟縺､縺薙→縺後〒縺阪∪縺吶・    """

    def __init__(self, table_name: str, table_number_of_rows: int,
                 column_settings: List[Dict[str, Any]]):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.table_number_of_rows = table_number_of_rows
        self.column_settings = column_settings
        self.param_names = {
            'table_name': 'tableName',
            'table_number_of_rows': 'tableNumberOfRows',
            'column_settings': 'columnSettings',
        }

    def validate(self):
        try:
            # 繝・・繝悶Ν蜷阪・讀懆ｨｼ
            table_name_list = self.tables_manager.get_table_name_list()
            validate_new_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )

            # 陦梧焚縺ｮ讀懆ｨｼ
            validate_integer(self.table_number_of_rows,
                             self.param_names['table_number_of_rows'])
            if self.table_number_of_rows <= 0:
                raise ValidationError(
                    _("The number of rows must be a positive integer.")
                )

            # 蛻苓ｨｭ螳壹・讀懆ｨｼ
            if not isinstance(self.column_settings, list):
                raise ValidationError(
                    _("Column settings must be a list.")
                )

            if len(self.column_settings) == 0:
                raise ValidationError(
                    _("At least one column setting is required.")
                )

            # 蜷・・險ｭ螳壹・隧ｳ邏ｰ讀懆ｨｼ
            column_names = []
            for i, column_setting in enumerate(self.column_settings):
                param_prefix = f"{self.param_names['column_settings']}[{i}]"
                self._validate_column_setting(
                    column_setting, column_names, param_prefix
                )

            return None
        except ValidationError as e:
            return e

    def _validate_column_setting(
            self, column_setting: Dict[str, Any],
            existing_column_names: List[str], param_prefix: str
    ):
        """蛟句挨縺ｮ蛻苓ｨｭ螳壹ｒ讀懆ｨｼ"""

        # 蛻怜錐縺ｮ讀懆ｨｼ
        if 'columnName' not in column_setting:
            raise ValidationError(
                _("Column name is required.")
            )

        column_name = column_setting['columnName']
        validate_new_column_name(
            column_name,
            existing_column_names,
            f"{param_prefix}.columnName"
        )
        existing_column_names.append(column_name)

        # 繝・・繧ｿ繧ｿ繧､繝励・讀懆ｨｼ
        if 'dataType' not in column_setting:
            raise ValidationError(
                _("Data type is required.")
            )

        data_type = column_setting['dataType']
        if data_type not in ['distribution', 'fixed']:
            raise ValidationError(
                _("Data type must be 'distribution' or 'fixed'.")
            )

        # 蛻・ｸ・ョ繝ｼ繧ｿ縺ｮ蝣ｴ蜷医・讀懆ｨｼ
        if data_type == 'distribution':
            if 'distributionType' not in column_setting:
                raise ValidationError(
                    _("Distribution type is required for distribution data.")
                )

            distribution_type = column_setting['distributionType']
            validate_distribution_type(
                distribution_type,
                f"{param_prefix}.distributionType"
            )

            if 'distributionParams' not in column_setting:
                raise ValidationError(
                    _("Distribution parameters are required for "
                      "distribution data.")
                )

            distribution_params = column_setting['distributionParams']
            validate_distribution_params(
                distribution_type, distribution_params
            )

        # 蝗ｺ螳壼､繝・・繧ｿ縺ｮ蝣ｴ蜷医・讀懆ｨｼ
        elif data_type == 'fixed':
            if 'fixedValue' not in column_setting:
                raise ValidationError(
                    _("Fixed value is required for fixed data.")
                )

    def execute(self):
        try:
            # 遨ｺ縺ｮ繝・・繝悶Ν繧剃ｽ懈・
            df = pl.DataFrame()

            # 蜷・・險ｭ螳壹↓蠕薙▲縺ｦ繝・・繧ｿ繧堤函謌・            for column_setting in self.column_settings:
                column_name = column_setting['columnName']
                data_type = column_setting['dataType']
                column_data = []  # 蛻晄悄蛹・
                if data_type == 'distribution':
                    # 蛻・ｸ・↓蠕薙▲縺ｦ繝・・繧ｿ繧堤函謌・                    distribution_type = column_setting['distributionType']
                    distribution_params = column_setting['distributionParams']
                    column_data = generate_simulation_data(
                        distribution_type,
                        distribution_params,
                        self.table_number_of_rows
                    )
                elif data_type == 'fixed':
                    # 蝗ｺ螳壼､縺ｧ繝・・繧ｿ繧堤函謌・                    fixed_value = column_setting['fixedValue']
                    column_data = [fixed_value] * self.table_number_of_rows

                # 蛻励ｒ繝・・繧ｿ繝輔Ξ繝ｼ繝縺ｫ霑ｽ蜉
                if df.is_empty():
                    df = pl.DataFrame({column_name: column_data})
                else:
                    df = df.with_columns(pl.Series(column_name, column_data))

            # 繝・・繝悶Ν繧堤匳骭ｲ
            self.tables_manager.store_table(self.table_name, df)

            # 邨先棡繧定ｿ斐☆
            result = {
                'tableName': self.table_name
            }
            return result

        except Exception as e:
            message = _("An unexpected error occurred during "
                        "creating simulation data table")
            raise ApiError(message) from e


def create_simulation_data_table(
        table_name: str,
        num_rows: int,
        column_settings: List[Dict[str, Any]]
) -> Dict:
    """繧ｷ繝溘Η繝ｬ繝ｼ繧ｷ繝ｧ繝ｳ繝・・繧ｿ繝・・繝悶Ν菴懈・縺ｮ繧ｨ繝ｳ繝医Μ繝ｼ繝昴う繝ｳ繝・""
    api = CreateSimulationDataTable(table_name, num_rows, column_settings)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
