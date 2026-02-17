import polars as pl

from ...i18n.translation import gettext as _
from ...models import AddLagLeadColumnRequestBody
from ...utils import ProcessingError, ValidationError
from ...utils.validators import validate_existence, validate_non_existence
from ..data.tables_store import TablesStore


class AddLagLeadColumn:
    """
    テーブルにラグ変数・リード変数列を追加するためのAPIクラス

    指定されたテーブルの指定された列に対してラグ・リード変数を作成し、
    新しい列として追加します。グループ列が指定された場合は、
    グループ内でのラグ・リード変数を作成します。
    """

    def __init__(
        self,
        body: AddLagLeadColumnRequestBody,
    ):
        self.tables_store = TablesStore()
        self.table_name = body.table_name
        self.source_column = body.source_column
        self.new_column_name = body.new_column_name
        self.periods = body.periods
        self.group_columns = body.group_columns or []
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
            # 対象のテーブルが存在することを検証
            validate_existence(
                value=self.table_name,
                valid_list=table_name_list,
                target=self.param_names["table_name"],
            )
            column_name_list = self.tables_store.get_column_name_list(
                self.table_name
            )
            # 対象の列が存在することを検証
            validate_existence(
                value=self.source_column,
                valid_list=column_name_list,
                target=self.param_names["source_column_name"],
            )
            # 追加する列名が既存の列名と重複しないことを検証
            validate_non_existence(
                value=self.new_column_name,
                existing_list=column_name_list,
                target=self.param_names["new_column_name"],
            )

            # グループ列の存在確認
            if self.group_columns or len(self.group_columns) > 0:
                validate_existence(
                    value=self.group_columns,
                    valid_list=column_name_list,
                    target=self.param_names["group_columns"],
                )

            return None
        except ValidationError as e:
            return e

    def execute(self):
        try:
            table_info = self.tables_store.get_table(self.table_name)
            df = table_info.table

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
            raise ProcessingError(
                error_code="AddLagLeadColumnProcessError",
                message=message,
                detail=str(e),
            ) from e
