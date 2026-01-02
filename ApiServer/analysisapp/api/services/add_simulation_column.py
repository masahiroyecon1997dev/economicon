from typing import Any, Dict

import polars as pl
from .django_compat import gettext as _

from .data.tables_manager import TablesManager
from ..utils.algorithm.simulation import generate_simulation_data
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.statistics_validators import (
    validate_distribution_params, validate_distribution_type)
from ..utils.validator.tables_manager_validator import (
    validate_existed_table_name, validate_new_column_name)
from .abstract_api import AbstractApi, ApiError


class AddSimulationColumn(AbstractApi):
    """
    繝・・繝悶Ν縺ｫ繧ｷ繝溘Η繝ｬ繝ｼ繧ｷ繝ｧ繝ｳ繝・・繧ｿ縺ｮ蛻励ｒ霑ｽ蜉縺吶ｋ縺溘ａ縺ｮAPI繧ｯ繝ｩ繧ｹ

    謖・ｮ壹＆繧後◆繝・・繝悶Ν縺ｫ謖・ｮ壹＆繧後◆蛻・ｸ・↓蠕薙≧繝ｩ繝ｳ繝繝繝・・繧ｿ縺ｮ譁ｰ縺励＞蛻励ｒ霑ｽ蜉縺励∪縺吶・    蟇ｾ蠢懊☆繧句・蟶・ｼ嗽niform, exponential, normal, gamma, beta, weibull,
    lognormal, binomial, bernoulli, poisson, geometric, hypergeometric
    """

    def __init__(self, table_name: str, new_column_name: str,
                 distribution_type: str, distribution_params: Dict[str, Any]):
        self.tables_manager = TablesManager()
        self.table_name = table_name
        self.new_column_name = new_column_name
        self.distribution_type = distribution_type
        self.distribution_params = distribution_params
        self.param_names = {
            'table_name': 'tableName',
            'new_column_name': 'newColumnName',
            'distribution_type': 'distributionType',
            'distribution_params': 'distributionParams',
        }

    def validate(self):
        try:
            # 繝・・繝悶Ν蜷阪・讀懆ｨｼ
            table_name_list = self.tables_manager.get_table_name_list()
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )

            # 譁ｰ縺励＞蛻怜錐縺ｮ讀懆ｨｼ
            column_name_list = self.tables_manager.get_column_name_list(
                self.table_name
            )
            validate_new_column_name(
                self.new_column_name,
                column_name_list,
                self.param_names['new_column_name']
            )

            # 蛻・ｸ・ち繧､繝励・讀懆ｨｼ
            validate_distribution_type(
                self.distribution_type,
                self.param_names['distribution_type']
            )

            # 蛻・ｸ・ヱ繝ｩ繝｡繝ｼ繧ｿ縺ｮ讀懆ｨｼ
            validate_distribution_params(
                self.distribution_type, self.distribution_params)

            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_manager.get_table(self.table_name)
            num_rows = table_info.num_rows

            # 蛻・ｸ・↓蠕薙▲縺ｦ繝・・繧ｿ繧堤函謌・            simulation_data = generate_simulation_data(
                self.distribution_type, self.distribution_params, num_rows)

            # 譁ｰ縺励＞蛻励ｒ繝・・繧ｿ繝輔Ξ繝ｼ繝縺ｫ霑ｽ蜉
            df = table_info.table
            df_with_new_col = df.with_columns(
                pl.Series(self.new_column_name, simulation_data))

            # 繝・・繝悶Ν繧呈峩譁ｰ
            self.tables_manager.update_table(self.table_name, df_with_new_col)

            # 邨先棡繧定ｿ斐☆
            result = {
                'tableName': self.table_name,
                'columnName': self.new_column_name,
                'distributionType': self.distribution_type
            }
            return result

        except Exception as e:
            message = _("An unexpected error occurred during "
                        "adding simulation column processing")
            raise ApiError(message) from e


def add_simulation_column(table_name: str,
                          new_column_name: str,
                          distribution_type: str,
                          distribution_params: Dict[str, Any]) -> Dict:
    """繧ｷ繝溘Η繝ｬ繝ｼ繧ｷ繝ｧ繝ｳ蛻苓ｿｽ蜉縺ｮ繧ｨ繝ｳ繝医Μ繝ｼ繝昴う繝ｳ繝・""
    api = AddSimulationColumn(table_name, new_column_name,
                              distribution_type, distribution_params)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
