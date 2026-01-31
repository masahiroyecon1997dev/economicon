"""
テーブルデータをApache Arrow形式で取得するサービス
"""

import base64

import pyarrow as pa

from ..i18n.translation import gettext as _
from ..utils.validator.common_validators import (
    ValidationError,
    validate_integer_positive,
    validate_required,
)
from ..utils.validator.tables_store_validator import (
    validate_existed_table_name,
    validate_row_index,
)
from .abstract_api import AbstractApi, ApiError
from .data.tables_store import TablesStore


class FetchDataToArrow(AbstractApi):
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
            num_rows = self.tables_store.get_table(self.table_name).num_rows
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
            total_rows = table.num_rows

            # 実際の終了行を計算（テーブルの行数を超えない範囲）
            end_row = min(start_row + chunk_size - 1, total_rows)

            # 指定された行範囲のデータを取得
            arrow_table = table.table[start_row - 1 : end_row]

            # Apache Arrow IPC形式にシリアライズ
            sink = pa.BufferOutputStream()
            writer = pa.ipc.new_stream(sink, arrow_table.schema)
            writer.write_table(arrow_table)
            writer.close()

            # バイナリデータを取得してBase64エンコード
            arrow_bytes = sink.getvalue().to_pybytes()
            arrow_base64 = base64.b64encode(arrow_bytes).decode("utf-8")

            result = {
                "tableName": self.table_name,
                "arrowData": arrow_base64,
                "totalRows": total_rows,
                "startRow": start_row,
                "endRow": end_row,
            }

            return result
        except Exception as e:
            message = _(
                f"An unexpected error during fetching Arrow data "
                f"from table '{self.table_name}': {str(e)}"
            )
            raise ApiError(message) from e


def fetch_data_to_arrow(
    table_name: str, start_row: int, chunk_size: int = 500
):
    """
    テーブルのデータをApache Arrow IPC形式で取得する関数

    Parameters
    ----------
    table_name : str
        テーブル名
    start_row : int
        取得開始行（1から始まる）
    chunk_size : int, optional
        チャンクサイズ（デフォルト500行）

    Returns
    -------
    dict
        Apache Arrow IPC形式のデータとメタ情報
        （総行数、開始行、終了行）

    Raises
    ------
    ValueError
        バリデーションエラーが発生した場合
    ApiError
        データ取得中にエラーが発生した場合
    """
    api = FetchDataToArrow(table_name, start_row, chunk_size)
    validation_error = api.validate()
    if validation_error:
        raise ValueError(validation_error.message)
    return api.execute()
