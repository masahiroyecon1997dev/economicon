from typing import ClassVar

import polars as pl

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.models import CreateSimulationDataTableRequestBody
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.algorithms import generate_simulation_data
from economicon.utils.validators import validate_non_existence


class CreateSimulationDataTable:
    """
    シミュレーションデータテーブルを作成するためのAPIクラス

    指定されたテーブル名で新しいテーブルを作成し、指定された列設定に従って
    シミュレーションデータ列を追加します。
    各列は分布に従うランダムデータまたは固定値を持つことができます。
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "table_name": "tableName",
        "row_count": "rowCount",
        "simulation_columns": "simulationColumns",
    }

    def __init__(
        self,
        body: CreateSimulationDataTableRequestBody,
        tables_store: TablesStore,
    ):
        self.tables_store = tables_store
        self.table_name = body.table_name
        self.row_count = body.row_count
        self.simulation_columns = body.simulation_columns

    def validate(self):
        # テーブル名の検証
        table_name_list = self.tables_store.get_table_name_list()
        validate_non_existence(
            value=self.table_name,
            existing_list=table_name_list,
            target=self.PARAM_NAMES["table_name"],
        )

    def execute(self):
        try:
            # 空のテーブルを作成
            df = pl.DataFrame()

            # 各列設定に従ってデータを生成
            for column in self.simulation_columns:
                column_name = column.column_name

                column_data = generate_simulation_data(
                    column.distribution,
                    self.row_count,
                )
                # 列をデータフレームに追加
                if df.is_empty():
                    df = pl.DataFrame({column_name: column_data})
                else:
                    df = df.with_columns(pl.Series(column_name, column_data))

            # テーブルを登録
            self.tables_store.store_table(self.table_name, df)

            # 結果を返す
            result = {"tableName": self.table_name}
            return result

        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "creating simulation data table"
            )
            raise ProcessingError(
                error_code=ErrorCode.CREATE_SIMULATION_DATA_TABLE_ERROR,
                message=message,
                detail=str(e),
            ) from e
