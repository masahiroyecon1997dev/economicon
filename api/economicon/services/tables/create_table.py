from pathlib import Path

import polars as pl

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.models import CreateTableRequestBody
from economicon.services.data.tables_store import TablesStore
from economicon.utils import ProcessingError
from economicon.utils.validators import (
    validate_file_format,
    validate_file_path,
    validate_non_existence,
)

# CSV エンコーディングマップ（Polars コーデック対応）
_ENCODING_MAP: dict[str, str] = {
    "utf8": "utf8",
    "latin1": "latin1",
    "ascii": "ascii",
    "gbk": "gbk",
    "windows-1252": "windows-1252",
    "shift_jis": "cp932",
}

# ファイルパスが指定された場合に許容する拡張子
_ALLOWED_EXTENSIONS = ["csv", "xlsx", "xls", "parquet"]


class CreateTable:
    """
    テーブル作成APIのPythonロジック

    ファイルパスが省略された場合は各カラムが空（None）の値で初期化されます。
    ファイルパスが指定された場合はファイルからデータを読み込み、
    カラム名はリクエストで指定された名前を使用します。
    行数は table_number_of_rows で調整でき、省略時はファイルの行数をそのまま
    使用します。
    """

    def __init__(
        self,
        body: CreateTableRequestBody,
        tables_store: TablesStore,
    ):
        self.tables_store = tables_store
        self.table_name = body.table_name
        self.row_count = body.row_count
        self.column_names = body.column_names
        self.file_path = body.file_path
        self.csv_has_header = body.csv_has_header
        self.csv_separator = body.csv_separator
        self.csv_encoding = body.csv_encoding
        self.excel_sheet_name = body.excel_sheet_name
        self.param_names = {
            "table_name": "tableName",
            "row_count": "rowCount",
            "column_names": "columnNames",
            "file_path": "filePath",
        }

    def validate(self):
        table_name_list = self.tables_store.get_table_name_list()
        # テーブル名の重複チェック
        validate_non_existence(
            value=self.table_name,
            existing_list=table_name_list,
            target=self.param_names["table_name"],
        )
        if self.file_path is not None:
            # ファイルあり: パスの存在と拡張子を検証
            validate_file_path(
                path_str=self.file_path,
                target=self.param_names["file_path"],
            )
            validate_file_format(
                path_str=self.file_path,
                target=self.param_names["file_path"],
                allowed_extensions=_ALLOWED_EXTENSIONS,
            )

    def execute(self):
        # テーブルの作成処理
        try:
            if self.file_path is not None:
                df = self._read_file(self.file_path)
            else:
                # 空（None）テーブルを作成（row_countはNoneではないはず）
                if self.row_count is None:
                    self.row_count = 1  # デフォルトは1行
                none_col = [None] * self.row_count
                data = {col: none_col for col in self.column_names}
                df = pl.DataFrame(data)

            created_table_name = self.tables_store.store_table(
                self.table_name, df
            )
            result = {"tableName": created_table_name}
            return result
        except ProcessingError as e:
            raise e
        except Exception as e:
            message = _(
                "An unexpected error occurred during table creation processing"
            )
            raise ProcessingError(
                error_code=ErrorCode.CREATE_TABLE_ERROR,
                message=message,
                detail=str(e),
            ) from e

    # ------------------------------------------------------------------
    # プライベートメソッド
    # ------------------------------------------------------------------

    def _read_file(self, path: str) -> pl.DataFrame:
        """ファイルを読み込み、column_names でカラム名を置換して返す"""
        ext = Path(path).suffix.lower().lstrip(".")

        if ext == "csv":
            df_raw = self._read_csv(path)
        elif ext in ("xlsx", "xls"):
            df_raw = self._read_excel(path)
        elif ext == "parquet":
            df_raw = self._read_parquet(path)
        else:
            message = _("Unsupported file type: {}").format(ext)
            raise ProcessingError(
                error_code=ErrorCode.UNSUPPORTED_FILE_TYPE,
                message=message,
            )

        # カラム数チェック
        if df_raw.width != len(self.column_names):
            message = _(
                "Column count mismatch: file has {file_cols} columns, "
                "but {requested_cols} column names were specified."
            ).format(
                file_cols=df_raw.width,
                requested_cols=len(self.column_names),
            )
            raise ProcessingError(
                error_code=ErrorCode.COLUMN_COUNT_MISMATCH,
                message=message,
            )

        # カラム名を置換してから行数調整
        rename_map = {
            old: str(new)
            for old, new in zip(df_raw.columns, self.column_names, strict=True)
        }
        df_renamed = df_raw.rename(rename_map)
        return self._adjust_rows(df_renamed)

    def _read_csv(self, path: str) -> pl.DataFrame:
        """CSVファイルを読み込む"""
        encoding = _ENCODING_MAP.get(self.csv_encoding, self.csv_encoding)
        return pl.read_csv(
            path,
            separator=self.csv_separator,
            encoding=encoding,
            has_header=self.csv_has_header,
        )

    def _read_excel(self, path: str) -> pl.DataFrame:
        """Excelファイルを読み込む"""
        sheet = self.excel_sheet_name or None
        if sheet:
            return pl.read_excel(path, sheet_name=sheet)
        return pl.read_excel(path)

    def _read_parquet(self, path: str) -> pl.DataFrame:
        """Parquetファイルを読み込む"""
        return pl.read_parquet(path)

    def _adjust_rows(self, df: pl.DataFrame) -> pl.DataFrame:
        """row_count に応じて行数を調整する。
        None の場合はそのまま返す。"""
        if self.row_count is None:
            return df
        current = df.height
        target = self.row_count
        if current > target:
            # 超過分を切り捨て
            return df.head(target)
        if current < target:
            # 不足分を None で埋める
            padding = pl.DataFrame(
                {col: [None] * (target - current) for col in df.columns}
            )
            return pl.concat([df, padding])
        return df
