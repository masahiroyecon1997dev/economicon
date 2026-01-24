
from typing import Dict, List

from .django_compat import gettext as _

from .data.tables_store import TablesStore
from ..utils.validator.common_validators import ValidationError
from ..utils.validator.tables_store_validator import (
    validate_existed_column_name, validate_existed_table_name,
    validate_join_type, validate_new_table_name)
from .abstract_api import AbstractApi, ApiError


class CreateJoinTable(AbstractApi):
    """
    結合テーブル作成APIのPythonロジック

    二つのテーブルを指定されたキーで結合し、新しいテーブルを作成します。
    内部結合、左結合、右結合、完全外部結合に対応しています。
    """
    def __init__(
        self,
        join_table_name: str,
        left_table_name: str,
        right_table_name: str,
        left_key_column_names: List[str],
        right_key_column_names: List[str],
        join_type: str,
    ):
        self.tables_store = TablesStore()
        # 結合後のテーブル名
        self.join_table_name = join_table_name
        # 左テーブル名
        self.left_table_name = left_table_name
        # 右テーブル名
        self.right_table_name = right_table_name
        # 左テーブルのキー列名リスト
        self.left_key_column_names = left_key_column_names
        # 右テーブルのキー列名リスト
        self.right_key_column_names = right_key_column_names
        # 結合タイプ（inner, left, right, outer）
        self.join_type = join_type
        # パラメータ名のマッピング
        self.param_names = {
            'table_name': 'joinTableName',
            'left_table_name': 'leftTableName',
            'right_table_name': 'rightTableName',
            'left_key_column_names': 'leftKeyColumnNames',
            'right_key_column_names': 'rightKeyColumnNames',
            'join_type': 'joinType',
        }

    def validate(self):
        # 入力値のバリデーション
        try:
            table_name_list = self.tables_store.get_table_name_list()
            # 新しいテーブル名の重複チェック
            validate_new_table_name(
                self.join_table_name,
                table_name_list,
                self.param_names['table_name']
            )
            # 左テーブルの存在チェック
            validate_existed_table_name(
                self.left_table_name,
                table_name_list,
                self.param_names['left_table_name']
            )
            # 右テーブルの存在チェック
            validate_existed_table_name(
                self.right_table_name,
                table_name_list,
                self.param_names['right_table_name']
            )
            # 左テーブルのキー列の存在チェック
            left_table_column_name_list = TablesStore().get_column_name_list(
                self.left_table_name
            )
            for left_key_column_name in self.left_key_column_names:
                validate_existed_column_name(
                    left_key_column_name,
                    left_table_column_name_list,
                    self.param_names['left_key_column_names']
                )
            # 右テーブルのキー列の存在チェック
            right_table_column_name_list = \
                TablesStore().get_column_name_list(
                    self.right_table_name
                )
            for right_key_column_name in self.right_key_column_names:
                validate_existed_column_name(
                    right_key_column_name,
                    right_table_column_name_list,
                    self.param_names['right_key_column_names']
                )
            # 結合タイプの妥当性チェック
            validate_join_type(
                self.join_type,
                self.param_names['join_type']
            )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # テーブル結合処理
        try:
            # 左テーブルのデータフレームを取得
            left_df = self.tables_store.get_table(
                self.left_table_name).table
            # 右テーブルのデータフレームを取得
            right_df = self.tables_store.get_table(
                self.right_table_name).table
            # 結合タイプに応じて結合処理を実行
            match self.join_type:
                case 'inner':
                    # 内部結合
                    df = left_df.join(
                        right_df,
                        left_on=self.left_key_column_names,
                        right_on=self.right_key_column_names,
                        how='inner',
                    )
                case 'left':
                    # 左結合
                    df = left_df.join(
                        right_df,
                        left_on=self.left_key_column_names,
                        right_on=self.right_key_column_names,
                        how='left',
                    )
                case 'right':
                    # 右結合
                    df = left_df.join(
                        right_df,
                        left_on=self.left_key_column_names,
                        right_on=self.right_key_column_names,
                        how='right',
                    )
                case 'outer':
                    # 完全外部結合
                    df = left_df.join(
                        right_df,
                        left_on=self.left_key_column_names,
                        right_on=self.right_key_column_names,
                        how='full',
                        coalesce=True,
                        maintain_order='left',
                    )
                case _:
                    raise ApiError("Invalid join type specified.")
            # 新しいテーブル情報を保存
            created_table_name = self.tables_store.store_table(
                self.join_table_name, df
            )
            # 結果を返す
            result = {'tableName': created_table_name}
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "join table creation processing"
            )
            raise ApiError(message) from e


def create_join_table(
    join_table_name: str,
    left_table_name: str,
    right_table_name: str,
    left_key_column_names: List[str],
    right_key_column_names: List[str],
    join_type: str,
) -> Dict:
    api = CreateJoinTable(
        join_table_name, left_table_name, right_table_name,
        left_key_column_names, right_key_column_names, join_type
    )
    validation_error = api.validate()
    if validation_error:
        raise validation_error
    result = api.execute()
    return result
