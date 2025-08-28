from typing import Dict, List
from django.utils.translation import gettext as _
from ..utilities.validator.common_validators import ValidationError
from ..utilities.validator.validator import InputValidator
from ..utilities.validator.validation_config import (
    INPUT_VALIDATOR_CONFIG,
)
from ..data.tables_manager import TablesManager
from .common_api_class import AbstractApi, ApiError
import polars as pl


class CreateUnionTable(AbstractApi):
    """
    ユニオンテーブル作成APIのPythonロジック

    複数のテーブルを指定された列でユニオン（結合）し、新しいテーブルを作成します。
    すべてのテーブルに共通する列名を指定して、それらの行を結合します。
    """
    def __init__(
        self,
        union_table_name: str,
        table_names: List[str],
        column_names: List[str],
    ):
        self.tables_manager = TablesManager()
        # ユニオン後のテーブル名
        self.union_table_name = union_table_name
        # ユニオンするテーブル名リスト
        self.table_names = table_names
        # ユニオンする列名リスト
        self.column_names = column_names
        # パラメータ名のマッピング
        self.param_names = {
            'table_name': 'unionTableName',
            'table_names': 'tableNames',
            'column_names': 'columnNames',
        }

    def validate(self):
        # 入力値のバリデーション
        try:
            validator = InputValidator(
                param_names=self.param_names, **INPUT_VALIDATOR_CONFIG
            )
            table_name_list = self.tables_manager.get_table_name_list()
            
            # 新しいテーブル名の重複チェック
            validator.validate_new_table_name(
                self.union_table_name, table_name_list
            )
            
            # テーブル名リストが最低2つ以上あることをチェック
            if len(self.table_names) < 2:
                raise ValidationError("tableNames must contain at least 2 table names.")
            
            # すべてのテーブルの存在チェック
            for table_name in self.table_names:
                validator.param_names['table_name'] = 'tableNames'
                validator.validate_existed_table_name(
                    table_name, table_name_list
                )
            
            # 列名リストが空でないことをチェック
            if not self.column_names:
                raise ValidationError("columnNames cannot be empty.")
            
            # すべてのテーブルで指定された列が存在することをチェック
            for table_name in self.table_names:
                table_column_name_list = self.tables_manager.get_column_name_list(
                    table_name
                )
                for column_name in self.column_names:
                    validator.param_names['column_names'] = 'columnNames'
                    validator.validate_existed_column_name(
                        column_name, table_column_name_list
                    )
            
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # テーブルユニオン処理
        try:
            # 各テーブルから指定された列のみを選択してデータフレームのリストを作成
            dataframes = []
            for table_name in self.table_names:
                df = self.tables_manager.get_table(table_name).table
                # 指定された列のみを選択
                selected_df = df.select(self.column_names)
                dataframes.append(selected_df)
            
            # すべてのデータフレームをユニオン（縦方向に結合）
            union_df = pl.concat(dataframes, how="vertical")
            
            # 新しいテーブル情報を保存
            created_table_name = self.tables_manager.store_table(
                self.union_table_name, union_df
            )
            
            # 結果を返す
            result = {'tableName': created_table_name}
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "union table creation processing"
            )
            raise ApiError(message) from e


def create_union_table(
    union_table_name: str,
    table_names: List[str],
    column_names: List[str],
) -> Dict:
    api = CreateUnionTable(
        union_table_name, table_names, column_names
    )
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result