from collections.abc import Sequence
from typing import ClassVar

import numpy as np
import polars as pl

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas import CreateSimulationDataTableRequestBody
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
        self.random_seed = body.random_seed

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

            # シード指定時は列ごとに独立した再現性を確保
            # SeedSequence.spawn() で列数分の独立ストリームを生成する
            if self.random_seed is not None:
                ss = np.random.SeedSequence(self.random_seed)
                child_seeds: Sequence[np.random.SeedSequence | None] = (
                    ss.spawn(len(self.simulation_columns))
                )
            else:
                child_seeds = [None] * len(self.simulation_columns)

            # 各列設定に従ってデータを生成
            for column, col_seed in zip(
                self.simulation_columns, child_seeds, strict=True
            ):
                column_name = column.column_name

                column_data = generate_simulation_data(
                    column.distribution,
                    self.row_count,
                    seed=col_seed,
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
