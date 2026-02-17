from ...i18n.translation import gettext as _
from ...models import CreateJoinTableRequestBody
from ...utils import ProcessingError, ValidationError
from ...utils.validators import validate_existence, validate_non_existence
from ..data.tables_store import TablesStore


class CreateJoinTable:
    """
    結合テーブル作成APIのPythonロジック

    二つのテーブルを指定されたキーで結合し、新しいテーブルを作成します。
    内部結合、左結合、右結合、完全外部結合に対応しています。
    """

    def __init__(
        self,
        body: CreateJoinTableRequestBody,
    ):
        self.tables_store = TablesStore()
        # 結合後のテーブル名
        self.join_table_name = body.join_table_name
        # 左テーブル名
        self.left_table_name = body.left_table_name
        # 右テーブル名
        self.right_table_name = body.right_table_name
        # 左テーブルのキー列名リスト
        self.left_key_column_names = body.left_key_column_names
        # 右テーブルのキー列名リスト
        self.right_key_column_names = body.right_key_column_names
        # 結合タイプ（inner, left, right, outer）
        self.join_type = body.join_type
        # パラメータ名のマッピング
        self.param_names = {
            "table_name": "joinTableName",
            "left_table_name": "leftTableName",
            "right_table_name": "rightTableName",
            "left_key_column_names": "leftKeyColumnNames",
            "right_key_column_names": "rightKeyColumnNames",
            "join_type": "joinType",
        }

    def validate(self):
        try:
            table_name_list = self.tables_store.get_table_name_list()
            # 新しいテーブル名の重複チェック
            validate_non_existence(
                value=self.join_table_name,
                existing_list=table_name_list,
                target=self.param_names["table_name"],
            )
            # 左テーブルの存在チェック
            validate_existence(
                value=self.left_table_name,
                valid_list=table_name_list,
                target=self.param_names["left_table_name"],
            )
            # 右テーブルの存在チェック
            validate_existence(
                value=self.right_table_name,
                valid_list=table_name_list,
                target=self.param_names["right_table_name"],
            )
            # 左テーブルのキー列の存在チェック
            left_table_column_name_list = TablesStore().get_column_name_list(
                self.left_table_name
            )
            for left_key_column_name in self.left_key_column_names:
                validate_existence(
                    value=left_key_column_name,
                    valid_list=left_table_column_name_list,
                    target=self.param_names["left_key_column_names"],
                )
            # 右テーブルのキー列の存在チェック
            right_table_column_name_list = TablesStore().get_column_name_list(
                self.right_table_name
            )
            for right_key_column_name in self.right_key_column_names:
                validate_existence(
                    value=right_key_column_name,
                    valid_list=right_table_column_name_list,
                    target=self.param_names["right_key_column_names"],
                )
            return None
        except ValidationError as e:
            return e

    def execute(self):
        # テーブル結合処理
        try:
            # 左テーブルのデータフレームを取得
            left_df = self.tables_store.get_table(self.left_table_name).table
            # 右テーブルのデータフレームを取得
            right_df = self.tables_store.get_table(self.right_table_name).table
            # 結合タイプに応じて結合処理を実行
            match self.join_type:
                case "left":
                    # 左結合
                    df = left_df.join(
                        right_df,
                        left_on=self.left_key_column_names,
                        right_on=self.right_key_column_names,
                        how="left",
                    )
                case "right":
                    # 右結合
                    df = left_df.join(
                        right_df,
                        left_on=self.left_key_column_names,
                        right_on=self.right_key_column_names,
                        how="right",
                    )
                case "outer":
                    # 完全外部結合
                    df = left_df.join(
                        right_df,
                        left_on=self.left_key_column_names,
                        right_on=self.right_key_column_names,
                        how="full",
                        coalesce=True,
                        maintain_order="left",
                    )
                case _:
                    # 内部結合（デフォルト）
                    df = left_df.join(
                        right_df,
                        left_on=self.left_key_column_names,
                        right_on=self.right_key_column_names,
                        how="inner",
                    )
            # 新しいテーブル情報を保存
            created_table_name = self.tables_store.store_table(
                self.join_table_name, df
            )
            # 結果を返す
            result = {"tableName": created_table_name}
            return result
        except Exception as e:
            message = _(
                "An unexpected error occurred during "
                "join table creation processing"
            )
            raise ProcessingError(
                error_code="JoinTableCreationError",
                message=message,
                detail=str(e),
            ) from e
