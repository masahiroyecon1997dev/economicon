from typing import Dict, List, Optional

import polars as pl
from ...i18n.translation import gettext as _

from ..data.tables_store import TablesStore
from ...utils.validators.common_validators import ValidationError
from ...utils.validators.tables_store_validator import (
    validate_existed_column_name,
    validate_existed_columns,
    validate_existed_table_name,
    validate_new_column_name,
)
from ..abstract_api import AbstractApi, ApiError


class AddLagLeadColumn(AbstractApi):
    """
    テーブルにラグ変数・リード変数列を追加するためのAPIクラス

    指定されたテーブルの指定された列に対してラグ・リード変数を作成し、
    新しい列として追加します。グループ列が指定された場合は、
    グループ内でのラグ・リード変数を作成します。
    """

    def __init__(
        self,
        table_name: str,
        source_column: str,
        new_column_name: str,
        periods: int,
        group_columns: Optional[List[str]] = None,
    ):
        self.tables_store = TablesStore()
        self.table_name = table_name
        self.source_column = source_column
        self.new_column_name = new_column_name
        self.periods = periods
        self.group_columns = group_columns or []
        self.param_names = {
            "table_name": "tableName",
            "source_column_name": "sourceColumn",
            "new_column_name": "newColumnName",
            "periods": "periods",
            "group_columns": "groupColumns",
        }

    def validate(self):
        try:
            table_name_list = self.tables_store.get_table_name_list()
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names["table_name"],
            )
            column_name_list = self.tables_store.get_column_name_list(
                self.table_name
            )
            validate_existed_column_name(
                self.source_column,
                column_name_list,
                self.param_names["source_column_name"],
            )
            validate_new_column_name(
                self.new_column_name,
                column_name_list,
                self.param_names["new_column_name"],
            )

            # グループ列の存在確認
            if self.group_columns or len(self.group_columns) > 0:
                validate_existed_columns(
                    self.group_columns,
                    column_name_list,
                    self.param_names["group_columns"],
                )

            # periodsが整数であることを確認
            if not isinstance(self.periods, int):
                raise ValidationError(_("periods must be an integer"))

            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

            # shift操作を実行
            # Note: polars.shift(1) gives previous value (lag),
            # shift(-1) gives next value (lead)
            # But we want periods=-1 to mean lag, periods=1 to mean lead
            # So we need to negate the periods value
            shift_periods = -self.periods

            if self.group_columns:
                # グループ指定がある場合
                df_with_lag_lead = df.with_columns(
                    pl.col(self.source_column)
                    .shift(shift_periods)
                    .over(self.group_columns)
                    .alias(self.new_column_name)
                )
            else:
                # グループ指定がない場合
                df_with_lag_lead = df.with_columns(
                    pl.col(self.source_column)
                    .shift(shift_periods)
                    .alias(self.new_column_name)
                )

            # 新しい列をデータフレームに追加
            self.tables_store.update_table(self.table_name, df_with_lag_lead)

            # 結果を返す
            result = {
                "tableName": self.table_name,
                "columnName": self.new_column_name,
            }
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "adding lag/lead column processing"
            )
            raise ApiError(message) from e


def add_lag_lead_column(
    table_name: str,
    source_column: str,
    new_column_name: str,
    periods: int,
    group_columns: Optional[List[str]] = None,
) -> Dict:
    api = AddLagLeadColumn(
        table_name, source_column, new_column_name, periods, group_columns
    )
    validation_error = api.validate()
    if validation_error:
        raise ValueError(validation_error.message)
    return api.execute()
