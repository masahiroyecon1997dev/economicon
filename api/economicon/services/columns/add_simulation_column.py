import polars as pl

from ...i18n.translation import gettext as _
from ...models import AddSimulationColumnRequestBody
from ...utils import ProcessingError, ValidationError
from ...utils.algorithms.simulation import generate_simulation_data
from ...utils.validators import validate_existence, validate_non_existence
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
        body: AddSimulationColumnRequestBody,
    ):
        self.tables_store = TablesStore()
        self.table_name = body.table_name
        self.new_column_name = body.simulation_column.column_name
        self.distribution = body.simulation_column.distribution

        self.param_names = {
            "table_name": "tableName",
            "new_column_name": "newColumnName",
            "distribution": "distribution",
        }

    def validate(self):
        try:
            table_name_list = self.tables_store.get_table_name_list()
            # 対象のテーブルが存在することを検証
            validate_existence(
                value=self.table_name,
                valid_list=table_name_list,
                target=self.param_names["table_name"],
            )

            column_name_list = self.tables_store.get_column_name_list(
                self.table_name
            )
            # 追加する列名が既存の列名と重複しないことを検証
            validate_non_existence(
                value=self.new_column_name,
                existing_list=column_name_list,
                target=self.param_names["new_column_name"],
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_store.get_table(self.table_name)
            row_count = table_info.row_count

            # 分布に従ってデータを生成
            simulation_data = generate_simulation_data(
                self.distribution, row_count
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
                "distributionType": self.distribution.type,
            }
            return result

        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "adding simulation column processing"
            )
            raise ProcessingError(
                error_code="AddSimulationColumnProcessError",
                message=message,
                detail=str(e),
            ) from e
