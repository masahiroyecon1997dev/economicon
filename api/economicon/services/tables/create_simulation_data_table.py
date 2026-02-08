from typing import Any, Dict, List

import polars as pl

from ...exceptions import ApiError
from ...i18n.translation import gettext as _
from ...utils.algorithms.simulation import generate_simulation_data
from ...utils.validators.common import (
    ValidationError,
    validate_integer,
)
from ...utils.validators.statistics import (
    validate_distribution_params,
    validate_distribution_type,
)
from ...utils.validators.tables_store import (
    validate_new_column_name,
    validate_new_table_name,
)
from ..data.tables_store import TablesStore


class CreateSimulationDataTable:
    """
    シミュレーションデータテーブルを作成するためのAPIクラス

    指定されたテーブル名で新しいテーブルを作成し、指定された列設定に従って
    シミュレーションデータ列を追加します。
    各列は分布に従うランダムデータまたは固定値を持つことができます。
    """

    def __init__(
        self,
        table_name: str,
        table_number_of_rows: int,
        column_settings: List[Dict[str, Any]],
    ):
        self.tables_store = TablesStore()
        self.table_name = table_name
        self.table_number_of_rows = table_number_of_rows
        self.column_settings = column_settings
        self.param_names = {
            "table_name": "tableName",
            "table_number_of_rows": "tableNumberOfRows",
            "column_settings": "columnSettings",
        }

    def validate(self):
        try:
            # テーブル名の検証
            table_name_list = self.tables_store.get_table_name_list()
            validate_new_table_name(
                self.table_name,
                table_name_list,
                self.param_names["table_name"],
            )

            # 行数の検証
            validate_integer(
                self.table_number_of_rows,
                self.param_names["table_number_of_rows"],
            )
            if self.table_number_of_rows <= 0:
                raise ValidationError(
                    _("The number of rows must be a positive integer.")
                )

            # 列設定の検証
            if not isinstance(self.column_settings, list):
                raise ValidationError(_("Column settings must be a list."))

            if len(self.column_settings) == 0:
                raise ValidationError(
                    _("At least one column setting is required.")
                )

            # 各列設定の詳細検証
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
        self,
        column_setting: Dict[str, Any],
        existing_column_names: List[str],
        param_prefix: str,
    ):
        """個別の列設定を検証"""

        # 列名の検証
        if "columnName" not in column_setting:
            raise ValidationError(_("Column name is required."))

        column_name = column_setting["columnName"]
        validate_new_column_name(
            column_name, existing_column_names, f"{param_prefix}.columnName"
        )
        existing_column_names.append(column_name)

        # データタイプの検証
        if "dataType" not in column_setting:
            raise ValidationError(_("Data type is required."))

        data_type = column_setting["dataType"]
        if data_type not in ["distribution", "fixed"]:
            raise ValidationError(
                _("Data type must be 'distribution' or 'fixed'.")
            )

        # 分布データの場合の検証
        if data_type == "distribution":
            if "distributionType" not in column_setting:
                raise ValidationError(
                    _("Distribution type is required for distribution data.")
                )

            distribution_type = column_setting["distributionType"]
            validate_distribution_type(
                distribution_type, f"{param_prefix}.distributionType"
            )

            if "distributionParams" not in column_setting:
                raise ValidationError(
                    _(
                        "Distribution parameters are required for distribution data."
                    )
                )

            distribution_params = column_setting["distributionParams"]
            validate_distribution_params(
                distribution_type, distribution_params
            )

        # 固定値データの場合の検証
        elif data_type == "fixed":
            if "fixedValue" not in column_setting:
                raise ValidationError(
                    _("Fixed value is required for fixed data.")
                )

    def execute(self):
        try:
            # 空のテーブルを作成
            df = pl.DataFrame()

            # 各列設定に従ってデータを生成
            for column_setting in self.column_settings:
                column_name = column_setting["columnName"]
                data_type = column_setting["dataType"]
                column_data = []  # 初期化

                if data_type == "distribution":
                    # 分布に従ってデータを生成
                    distribution_type = column_setting["distributionType"]
                    distribution_params = column_setting["distributionParams"]
                    column_data = generate_simulation_data(
                        distribution_type,
                        distribution_params,
                        self.table_number_of_rows,
                    )
                elif data_type == "fixed":
                    # 固定値でデータを生成
                    fixed_value = column_setting["fixedValue"]
                    column_data = [fixed_value] * self.table_number_of_rows

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
                "An unexpected error occurred during creating simulation data table"
            )
            raise ApiError(message) from e
