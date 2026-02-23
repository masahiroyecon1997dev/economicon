"""インポート/エクスポート関連のスキーマ定義"""

from typing import Annotated

from pydantic import Field

from .common import BaseRequest, BaseResult
from .types import (
    CsvEncoding,
    DirectoryPath,
    ExcelSheetName,
    FileName,
    FilePath,
    NewTableName,
    Separator,
    TableName,
)

# ---------------------------------------------------------------------------
# リクエストボディ
# ---------------------------------------------------------------------------


class ImportFileRequestBody(BaseRequest):
    """ファイルパス指定インポートリクエスト（CSV / Excel / Parquet 共通）

    拡張子に応じて適切なインポーターが自動選択されます。

    - .csv / .tsv  → CSV インポーター（separator / encoding が有効）
    - .xlsx / .xls → Excel インポーター（sheet_name が有効）
    - .parquet     → Parquet インポーター
    """

    file_path: Annotated[
        FilePath,
        Field(
            title="File Path",
            description=(
                "インポートするファイルの絶対パス。"
                "対応拡張子: .csv, .tsv, .xlsx, .xls, .parquet"
                "（相対パスはサポートされていません）。"
            ),
        ),
    ]
    table_name: Annotated[
        NewTableName,
        Field(
            title="Table Name",
            description=(
                "インポート後のテーブル名。"
                "ワークスペース内で既存のテーブル名と重複しない名前を"
                "指定してください。"
            ),
        ),
    ]
    # --- CSV 専用オプション ---
    separator: Annotated[
        Separator,
        Field(
            title="Separator",
            description=(
                "CSV 区切り文字（CSV / TSV のみ有効）。"
                "カンマかタブ、もしくは 1〜10 文字の任意の文字列から"
                "選択してください。"
            ),
        ),
    ] = ","
    encoding: Annotated[
        CsvEncoding,
        Field(
            title="Encoding",
            description=(
                "CSV ファイルのエンコーディング（CSV / TSV のみ有効）。"
                "utf8 / latin1 / ascii / gbk / windows-1252 / shift_jis "
                "から選択してください。"
            ),
        ),
    ] = "utf8"
    # --- Excel 専用オプション ---
    sheet_name: Annotated[
        ExcelSheetName | None,
        Field(
            title="Sheet Name",
            description=(
                "インポートする Excel シート名（Excel のみ有効）。"
                "省略または null の場合は先頭シートを読み込みます。"
                "シート名は大文字・小文字を区別します。"
            ),
        ),
    ] = None


class ExportCsvByPathRequestBody(BaseRequest):
    """CSVファイルパス指定エクスポートリクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            title="Table Name",
            description="エクスポートするテーブル名。ワークスペース内に存在するテーブル名を指定してください。",
        ),
    ]
    directory_path: Annotated[
        DirectoryPath,
        Field(
            title="Directory Path",
            description="出力するCSVファイルのディレクトリの絶対パス（相対パスはサポートされていません）。",
        ),
    ]
    file_name: Annotated[
        FileName,
        Field(
            title="File Name",
            description="出力するCSVファイルのファイル名（拡張子を含む）。同名ファイルが存在する場合は上書きされます。",
        ),
    ]
    separator: Annotated[
        Separator,
        Field(
            title="Separator",
            description="CSV区切り文字。カンマかタブ、もしくは1から10文字の任意の文字列から選択してください。",
        ),
    ]


class ExportExcelByPathRequestBody(BaseRequest):
    """Excelファイルパス指定エクスポートリクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            title="Table Name",
            description="エクスポートするテーブル名。ワークスペース内に存在するテーブル名を指定してください。",
        ),
    ]
    directory_path: Annotated[
        DirectoryPath,
        Field(
            title="Directory Path",
            description="出力するExcelファイルのディレクトリの絶対パス（相対パスはサポートされていません）。",
        ),
    ]
    file_name: Annotated[
        FileName,
        Field(
            title="File Name",
            description="出力するExcelファイルのファイル名（拡張子を含む）。同名ファイルが存在する場合は上書きされます。",
        ),
    ]


class ExportParquetByPathRequestBody(BaseRequest):
    """Parquetファイルパス指定エクスポートリクエスト"""

    table_name: Annotated[
        TableName,
        Field(
            title="Table Name",
            description="エクスポートするテーブル名。ワークスペース内に存在するテーブル名を指定してください。",
        ),
    ]
    directory_path: Annotated[
        DirectoryPath,
        Field(
            title="Directory Path",
            description="出力するParquetファイルのディレクトリの絶対パス（相対パスはサポートされていません）。",
        ),
    ]
    file_name: Annotated[
        FileName,
        Field(
            title="File Name",
            description="出力するParquetファイルのファイル名（拡張子を含む）。同名ファイルが存在する場合は上書きされます。",
        ),
    ]


# ---------------------------------------------------------------------------
# レスポンス（Result）
# ---------------------------------------------------------------------------


class ImportTableResult(BaseResult):
    """インポート共通レスポンス基底"""

    table_name: str = Field(
        title="Table Name",
        description="インポートによって作成されたテーブル名",
    )


class ImportFileResult(ImportTableResult):
    """ファイルパス指定インポートレスポンス"""


class ExportFileResult(BaseResult):
    """エクスポート共通レスポンス基底"""

    file_path: str = Field(
        title="File Path",
        description="出力したファイルのフルパス",
    )


class ExportCsvByPathResult(ExportFileResult):
    """CSV エクスポートレスポンス"""


class ExportExcelByPathResult(ExportFileResult):
    """Excel エクスポートレスポンス"""


class ExportParquetByPathResult(ExportFileResult):
    """Parquet エクスポートレスポンス"""
