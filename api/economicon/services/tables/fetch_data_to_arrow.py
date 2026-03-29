"""
テーブルデータをApache Arrow形式で取得するサービス
"""

import io
from typing import ClassVar

import pyarrow as pa

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas import FetchDataToArrowRequestBody
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import (
    validate_existence,
    validate_row_count_limit,
)


class FetchDataToArrow:
    """
    テーブルのデータをApache Arrow IPC形式（生バイト）で取得するAPIクラス

    レスポンスはJSON包装なし。Arrow IPC ファイル形式の生バイナリを直接返す。
    メタデータ（totalRows / startRow / endRow / tableName）は
    Arrowスキーマのカスタムメタデータとして埋め込む。
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
        self.tables_store = tables_store
        self.table_name = body.table_name
        self.start_row = body.start_row
        self.chunk_size = body.chunk_size

    def validate(self):
        """パラメータのバリデーション"""
        table_name_list = self.tables_store.get_table_name_list()
        validate_existence(
            value=self.table_name,
            valid_list=table_name_list,
            target=self.PARAM_NAMES["table_name"],
        )
        row_count = self.tables_store.get_table(self.table_name).row_count - 1
        validate_row_count_limit(
            current_row_count=row_count,
            requested_count=self.start_row,
            target=self.PARAM_NAMES["start_row"],
        )

    def execute(self) -> bytes:
        """
        テーブルデータをApache Arrow IPC生バイトで返す。

        Returns
        -------
        bytes
            Arrow IPC ファイル形式の生バイナリ。
            スキーマメタデータに totalRows / startRow / endRow /
            tableName を含む。

        Raises
        ------
        ProcessingError
            データ取得中に予期しないエラーが発生した場合
        """
        try:
            table = self.tables_store.get_table(self.table_name)
            start_row = int(self.start_row)
            chunk_size = int(self.chunk_size)
            arrow_slice = table.table.slice(start_row, chunk_size)

            pyarrow_table = arrow_slice.to_arrow()

            total_rows = table.row_count
            end_row = min(start_row + chunk_size, total_rows)

            # メタデータをスキーマに埋め込む（JSON包装の代替）
            meta = {
                b"totalRows": str(total_rows).encode(),
                b"startRow": str(start_row).encode(),
                b"endRow": str(end_row).encode(),
                b"tableName": self.table_name.encode(),
            }
            pyarrow_table = pyarrow_table.replace_schema_metadata(meta)

            sink = io.BytesIO()
            with pa.ipc.new_file(sink, pyarrow_table.schema) as writer:
                writer.write_table(pyarrow_table)

            return sink.getvalue()

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
