import polars as pl

from ...core.enums import ErrorCode
from ...i18n.translation import gettext as _
from ...models import AddSimulationColumnRequestBody
from ...utils import ProcessingError
from ...utils.algorithms import generate_simulation_data
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
        tables_store: TablesStore,
    ):
        self.tables_store = tables_store
        self.table_name = body.table_name
        self.new_column_name = body.simulation_column.column_name
        self.add_position_column = body.add_position_column
        self.distribution = body.simulation_column.distribution

        self.param_names = {
            "table_name": "tableName",
            "new_column_name": "newColumnName",
            "add_position_column": "addPositionColumn",
            "distribution": "distribution",
        }

    def validate(self):
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

        # 追加位置の列名が既存の列名の中に存在することを検証
        validate_existence(
            value=self.add_position_column,
            valid_list=column_name_list,
            target=self.param_names["add_position_column"],
        )
        return None

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

            # 追加位置の計算（指定されたカラムの右隣）
            current_cols = df.columns
            target_idx = current_cols.index(self.add_position_column) + 1

            # 列の並び順を定義
            new_order = (
                current_cols[:target_idx]
                + [self.new_column_name]
                + current_cols[target_idx:]
            )

            df_with_new_col = df.with_columns(
                pl.lit(simulation_data).alias(self.new_column_name)
            ).select(new_order)

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
                error_code=ErrorCode.ADD_SIMULATION_COLUMN_PROCESS_ERROR,
                message=message,
                detail=str(e),
            ) from e
