"""
テーブルデータをApache Arrow形式で取得するサービス
"""

import base64
import io
from typing import ClassVar

import pyarrow as pa

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.models import FetchDataToArrowRequestBody
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import (
    validate_existence,
    validate_row_count_limit,
)


class FetchDataToArrow:
    """
    テーブルのデータをApache Arrow IPC形式で取得するAPIクラス

    指定されたテーブルの指定された開始行から指定されたチャンクサイズのデータを
    Apache Arrow IPC形式で取得します。
    仮想スクロール用に500行単位でのチャンク取得を想定しています。
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "table_name": "tableName",
        "start_row": "startRow",
        "chunk_size": "chunkSize",
    }

    def __init__(
        self,
        body: FetchDataToArrowRequestBody,
        tables_store: TablesStore,
    ):
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
        self.tables_store = tables_store
        self.table_name = body.table_name
        self.start_row = body.start_row
        self.chunk_size = body.chunk_size

    def validate(self):
        """
        パラメータのバリデーション

        Returns
        -------
        ValidationError or None
            バリデーションエラーが発生した場合はエラーオブジェクト、
            問題なければNone
        """
        table_name_list = self.tables_store.get_table_name_list()
        # テーブル名の存在チェック
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.PARAM_NAMES["table_name"],
        )
        row_count = self.tables_store.get_table(self.table_name).row_count - 1
        # 開始行番号の妥当性チェック
        validate_row_count_limit(
            current_row_count=row_count,
            requested_count=self.start_row,
            target=self.PARAM_NAMES["start_row"],
        )

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
        ProcessingError
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

            total_rows = table.row_count
            end_row = min(start_row + chunk_size, total_rows)
            return {
                "tableName": self.table_name,
                "arrowData": base64.b64encode(sink.getvalue()).decode("utf-8"),
                "totalRows": total_rows,
                "startRow": start_row,
                "endRow": end_row,
            }

        except Exception as e:
            message = _(
                f"An unexpected error during fetching Arrow data "
                f"from table '{self.table_name}': {str(e)}"
            )
            raise ProcessingError(
                error_code=ErrorCode.FETCH_DATA_TO_ARROW_ERROR,
                message=message,
                detail=str(e),
            ) from e
