from typing import Any, Dict

import polars as pl

from ...i18n.translation import gettext as _
from ...utils.algorithms.simulation import generate_simulation_data
from ...utils.validators.common import ValidationError
from ...utils.validators.statistics import (
    validate_distribution_params,
    validate_distribution_type,
)
from ...utils.validators.tables_store import (
    validate_existed_table_name,
    validate_new_column_name,
)
from ..abstract_api import AbstractApi, ApiError
from ..data.tables_store import TablesStore


class AddSimulationColumn(AbstractApi):
    """
    テーブルにシミュレーションデータの列を追加するためのAPIクラス

    指定されたテーブルに指定された分布に従うランダムデータの新しい列を追加します。
    対応する分布：uniform, exponential, normal, gamma, beta, weibull,
    lognormal, binomial, bernoulli, poisson, geometric, hypergeometric
    """

    def __init__(
        self,
        table_name: str,
        new_column_name: str,
        distribution_type: str,
        distribution_params: Dict[str, Any],
    ):
        self.tables_store = TablesStore()
        self.table_name = table_name
        self.new_column_name = new_column_name
        self.distribution_type = distribution_type
        self.distribution_params = distribution_params
        self.param_names = {
            "table_name": "tableName",
            "new_column_name": "newColumnName",
            "distribution_type": "distributionType",
            "distribution_params": "distributionParams",
        }

    def validate(self):
        try:
            # テーブル名の検証
            table_name_list = self.tables_store.get_table_name_list()
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names["table_name"],
            )

            # 新しい列名の検証
            column_name_list = self.tables_store.get_column_name_list(
                self.table_name
            )
            validate_new_column_name(
                self.new_column_name,
                column_name_list,
                self.param_names["new_column_name"],
            )

            # 分布タイプの検証
            validate_distribution_type(
                self.distribution_type, self.param_names["distribution_type"]
            )

            # 分布パラメータの検証
            validate_distribution_params(
                self.distribution_type, self.distribution_params
            )

            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_store.get_table(self.table_name)
            num_rows = table_info.num_rows

            # 分布に従ってデータを生成
            simulation_data = generate_simulation_data(
                self.distribution_type, self.distribution_params, num_rows
            )

            # 新しい列をデータフレームに追加
            df = table_info.table
            df_with_new_col = df.with_columns(
                pl.Series(self.new_column_name, simulation_data)
            )

            # テーブルを更新
            self.tables_store.update_table(self.table_name, df_with_new_col)

            # 結果を返す
            result = {
                "tableName": self.table_name,
                "columnName": self.new_column_name,
                "distributionType": self.distribution_type,
            }
            return result

        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "adding simulation column processing"
            )
            raise ApiError(message) from e


def add_simulation_column(
    table_name: str,
    new_column_name: str,
    distribution_type: str,
    distribution_params: Dict[str, Any],
) -> Dict:
    """
    テーブルにシミュレーション列を追加するためのAPI関数
    """
    api = AddSimulationColumn(
        table_name, new_column_name, distribution_type, distribution_params
    )
    validation_error = api.validate()
    if validation_error:
        raise ValueError(validation_error.message)
    return api.execute()
