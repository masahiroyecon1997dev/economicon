"""
テーブルデータをApache Arrow形式で取得するサービス
"""

import io

import pyarrow as pa

from ...exceptions import ApiError
from ...i18n.translation import gettext as _
from ...utils.validators.common import (
    ValidationError,
    validate_integer_positive,
    validate_required,
)
from ...utils.validators.tables_store import (
    validate_existed_table_name,
    validate_row_index,
)
from ..data.tables_store import TablesStore


class FetchDataToArrow:
    """
    テーブルのデータをApache Arrow IPC形式で取得するAPIクラス

    指定されたテーブルの指定された開始行から指定されたチャンクサイズのデータを
    Apache Arrow IPC形式で取得します。
    仮想スクロール用に500行単位でのチャンク取得を想定しています。
    """

    def __init__(self, table_name: str, start_row: int, chunk_size: int = 500):
        """
        初期化

        Parameters
        ----------
        table_name : str
            テーブル名
        start_row : int
            取得開始行（1から始まる）
        chunk_size : int, optional
            チャンクサイズ（デフォルト500行）
        """
        self.tables_store = TablesStore()
        self.table_name = table_name
        self.start_row = start_row
        self.chunk_size = chunk_size
        self.param_names = {
            "table_name": "tableName",
            "start_row": "startRow",
            "chunk_size": "chunkSize",
        }

    def validate(self):
        """
        パラメータのバリデーション

        Returns
        -------
        ValidationError or None
            バリデーションエラーが発生した場合はエラーオブジェクト、
            問題なければNone
        """
        try:
            # 必須パラメータのチェック
            validate_required(self.table_name, self.param_names["table_name"])
            validate_required(self.start_row, self.param_names["start_row"])
            validate_required(self.chunk_size, self.param_names["chunk_size"])

            table_name_list = self.tables_store.get_table_name_list()
            # テーブル名の存在チェック
            validate_existed_table_name(
                self.table_name,
                table_name_list,
                self.param_names["table_name"],
            )
            num_rows = (
                self.tables_store.get_table(self.table_name).num_rows - 1
            )
            # 開始行番号の妥当性チェック
            validate_row_index(
                self.start_row, num_rows, self.param_names["start_row"]
            )
            # チャンクサイズが正の整数であることをチェック
            validate_integer_positive(
                self.chunk_size, self.param_names["chunk_size"]
            )

            return None
        except ValidationError as e:
            return e

    def execute(self):
        """
        テーブルデータをApache Arrow IPC形式で取得

        Returns
        -------
        dict
            テーブル名、Arrow IPC形式のバイナリデータ（Base64エンコード）、
            総行数、開始行、終了行を含む辞書

        Raises
        ------
        ApiError
            データ取得中に予期しないエラーが発生した場合
        """
        try:
            # テーブルのデータを取得
            table = self.tables_store.get_table(self.table_name)
            start_row = int(self.start_row)
            chunk_size = int(self.chunk_size)
            arrow_table = table.table.slice(start_row, chunk_size)

            # Polars DataFrameをPyArrow Tableに変換
            pyarrow_table = arrow_table.to_arrow()

            # Apache Arrow IPC形式にシリアライズ
            sink = io.BytesIO()
            with pa.ipc.new_file(sink, pyarrow_table.schema) as writer:
                writer.write_table(pyarrow_table)

            return sink.getvalue()

        except Exception as e:
            message = _(
                f"An unexpected error during fetching Arrow data "
                f"from table '{self.table_name}': {str(e)}"
            )
            raise ApiError(message) from e
