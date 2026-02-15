import polars as pl

from ...exceptions import ApiError
from ...i18n.translation import gettext as _
from ...models.common import DistributionParams
from ...utils.algorithms.simulation import generate_simulation_data
from ...utils.validators.common import ValidationError
from ...utils.validators.statistics import validate_distribution_params
from ...utils.validators.tables_store import (
    validate_existed_table_name,
    validate_new_column_name,
)
from ..data.tables_store import TablesStore


class AddSimulationColumn:
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
        distribution: DistributionParams,
    ):
        self.tables_store = TablesStore()
        self.table_name = table_name
        self.new_column_name = new_column_name

        # Pydanticモデルをdictに変換
        dist_dict = distribution.model_dump()

        # typeフィールドから分布名を取得
        self.distribution_type = dist_dict["type"]
        # type以外のフィールドをパラメータとして抽出
        self.distribution_params = {
            k: v for k, v in dist_dict.items() if k != "type"
        }

        self.param_names = {
            "table_name": "tableName",
            "new_column_name": "newColumnName",
            "distribution": "distribution",
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
