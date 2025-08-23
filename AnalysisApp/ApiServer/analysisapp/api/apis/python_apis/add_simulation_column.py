import polars as pl
import numpy as np
from django.utils.translation import gettext as _
from typing import Dict, Any
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.tables_manager_validator import (
    validate_existed_table_name,
    validate_new_column_name,
    validate_distribution_type,
    validate_distribution_params
)
from ..data.tables_manager import TablesManager
from .common_api_class import (AbstractApi, ApiError)


class AddSimulationColumn(AbstractApi):
    """
    テーブルにシミュレーションデータの列を追加するためのAPIクラス

    指定されたテーブルに指定された分布に従うランダムデータの新しい列を追加します。
    対応する分布：uniform, exponential, normal, gamma, beta, weibull,
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
            # テーブル名の検証
            table_name_list = self.tables_manager.get_table_name_list()
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names['table_name']
            )

            # 新しい列名の検証
            column_name_list = self.tables_manager.get_column_name_list(
                self.table_name
            )
            validate_new_column_name(
                self.new_column_name,
                column_name_list,
                self.param_names['new_column_name']
            )

            # 分布タイプの検証
            validate_distribution_type(
                self.distribution_type,
                self.param_names['distribution_type']
            )

            # 分布パラメータの検証
            validate_distribution_params(
                self.distribution_type, self.distribution_params)

            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_manager.get_table(self.table_name)
            num_rows = table_info.num_rows

            # 分布に従ってデータを生成
            simulation_data = self._generate_simulation_data(num_rows)

            # 新しい列をデータフレームに追加
            df = table_info.table
            df_with_new_col = df.with_columns(
                pl.Series(self.new_column_name, simulation_data))

            # テーブルを更新
            self.tables_manager.update_table(self.table_name, df_with_new_col)

            # 結果を返す
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

    def _generate_simulation_data(self, num_rows: int):
        """指定された分布に従ってシミュレーションデータを生成"""
        dist_type = self.distribution_type
        params = self.distribution_params

        # NumPyのランダムジェネレータを使用
        rng = np.random.default_rng()

        if dist_type == 'uniform':
            return rng.uniform(params['low'], params['high'], num_rows)

        elif dist_type == 'exponential':
            return rng.exponential(params['scale'], num_rows)

        elif dist_type == 'normal':
            return rng.normal(params['loc'], params['scale'], num_rows)

        elif dist_type == 'gamma':
            return rng.gamma(params['shape'], params['scale'], num_rows)

        elif dist_type == 'beta':
            return rng.beta(params['a'], params['b'], num_rows)

        elif dist_type == 'weibull':
            return rng.weibull(params['a'], num_rows)

        elif dist_type == 'lognormal':
            return rng.lognormal(params['mean'], params['sigma'], num_rows)

        elif dist_type == 'binomial':
            return rng.binomial(params['n'], params['p'], num_rows)

        elif dist_type == 'bernoulli':
            return rng.binomial(1, params['p'], num_rows)

        elif dist_type == 'poisson':
            return rng.poisson(params['lam'], num_rows)

        elif dist_type == 'geometric':
            return rng.geometric(params['p'], num_rows)

        elif dist_type == 'hypergeometric':
            return rng.hypergeometric(params['K'], params['N'] - params['K'],
                                      params['n'], num_rows)

        else:
            raise ValueError(f"Unsupported distribution type: {dist_type}")


def add_simulation_column(table_name: str,
                          new_column_name: str,
                          distribution_type: str,
                          distribution_params: Dict[str, Any]) -> Dict:
    """シミュレーション列追加のエントリーポイント"""
    api = AddSimulationColumn(table_name, new_column_name,
                              distribution_type, distribution_params)
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
