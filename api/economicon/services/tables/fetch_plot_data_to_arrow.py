"""
プロット用列指定データを Apache Arrow 形式で取得するサービス
"""

import io
from typing import ClassVar

import pyarrow as pa

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas import FetchPlotDataRequestBody
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import validate_existence


class FetchPlotDataToArrow:
    """
    指定列のみを Apache Arrow IPC 形式（生バイト）で取得するAPIクラス

    グラフ描画に必要な列だけを選択して返すことで、メモリ使用量と
    転送量を削減する。レスポンスは JSON 包装なしの Arrow IPC 生バイナリ。
    メタデータ（tableName / columnNames / totalRows）は
    Arrow スキーマのカスタムメタデータとして埋め込む。
    """

    PARAM_NAMES: ClassVar[dict[str, str]] = {
        "table_name": "tableName",
        "column_names": "columnNames",
    }

    def __init__(
        self,
        body: FetchPlotDataRequestBody,
        tables_store: TablesStore,
    ):
        self.tables_store = tables_store
        self.table_name = body.table_name
        # 重複を除去しつつ順序を保持する
        seen: set[str] = set()
        self.column_names: list[str] = [
            c
            for c in body.column_names
            if c not in seen and not seen.add(c)  # type: ignore[func-returns-value]
        ]

    def validate(self) -> None:
        """パラメータのバリデーション"""
        validate_existence(
            value=self.table_name,
            valid_list=self.tables_store.get_table_name_list(),
            target=self.PARAM_NAMES["table_name"],
        )
        validate_existence(
            value=self.column_names,
            valid_list=self.tables_store.get_column_name_list(
                self.table_name
            ),
            target=self.PARAM_NAMES["column_names"],
        )

    def execute(self) -> bytes:
        """
        指定列のデータを Apache Arrow IPC 生バイトで返す。

        Returns
        -------
        bytes
            Arrow IPC ファイル形式の生バイナリ。
            スキーマメタデータに tableName / columnNames / totalRows を含む。

        Raises
        ------
        ProcessingError
            データ取得中に予期しないエラーが発生した場合
        """
        try:
            table = self.tables_store.get_table(self.table_name)
            df = table.table.select(self.column_names)
            pyarrow_table = df.to_arrow()

            total_rows = len(df)

            meta = {
                b"tableName": self.table_name.encode(),
                b"columnNames": ",".join(self.column_names).encode(),
                b"totalRows": str(total_rows).encode(),
            }
            pyarrow_table = pyarrow_table.replace_schema_metadata(meta)

            sink = io.BytesIO()
            with pa.ipc.new_file(sink, pyarrow_table.schema) as writer:
                writer.write_table(pyarrow_table)

            return sink.getvalue()

        except Exception as e:
            message = _(
                f"An unexpected error during fetching plot data "
                f"from table '{self.table_name}': {str(e)}"
            )
            raise ProcessingError(
                error_code=ErrorCode.FETCH_PLOT_DATA_ERROR,
                message=message,
                detail=str(e),
            ) from e
