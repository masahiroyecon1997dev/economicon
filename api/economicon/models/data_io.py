"""インポート/エクスポート関連のスキーマ定義"""

from typing import Annotated

from pydantic import Field

from economicon.models.common import BaseRequest, BaseResult
from economicon.models.types import (
    CsvEncoding,
    DirectoryPath,
    ExcelSheetName,
    ExportFormat,
    FileName,
    FilePath,
    NewTableName,
    Separator,
    TableName,
)

# ---------------------------------------------------------------------------
# ファイルインポート
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


class ImportFileResult(BaseResult):
    """ファイルパス指定インポートレスポンス"""

    table_name: str = Field(
        title="Table Name",
        description="インポートによって作成されたテーブル名",
    )


# ---------------------------------------------------------------------------
# ファイルエクスポート
# ---------------------------------------------------------------------------


class ExportFileRequestBody(BaseRequest):
    """ファイルパス指定エクスポートリクエスト（CSV / Excel / Parquet 共通）

    ``format`` に応じて適切なエクスポーターが自動選択され、
    ファイル拡張子も自動で付与されます。

    - ``csv``     →
        CSV エクスポーター（separator / encoding / include_header が有効）
    - ``excel``   → Excel エクスポーター（sheet_name が有効）
    - ``parquet`` → Parquet エクスポーター
    """

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
            description="出力ファイルのディレクトリの絶対パス（相対パスはサポートされていません）。",
        ),
    ]
    file_name: Annotated[
        FileName,
        Field(
            title="File Name",
            description=(
                "出力ファイルのベース名（拡張子なし）。"
                "同名ファイルが存在する場合は上書きされます。"
            ),
        ),
    ]
    format: Annotated[
        ExportFormat,
        Field(
            title="Format",
            description=(
                "出力するファイル形式。"
                "csv / excel / parquet から選択してください。"
                "選択した形式に応じた拡張子が自動付与されます。"
            ),
        ),
    ]
    # --- CSV 専用オプション ---
    separator: Annotated[
        Separator,
        Field(
            title="Separator",
            description=(
                "CSV 区切り文字（CSV のみ有効）。カンマかタブ、"
                "もしくは 1〜10 文字の任意の文字列から選択してください。"
            ),
        ),
    ] = ","
    encoding: Annotated[
        CsvEncoding,
        Field(
            title="Encoding",
            description=(
                "CSV ファイルの出力エンコーディング（CSV のみ有効）。"
                "utf8 / latin1 / ascii / gbk / windows-1252 / shift_jis "
                "から選択してください。"
            ),
        ),
    ] = "utf8"
    include_header: Annotated[
        bool,
        Field(
            title="Include Header",
            description=(
                "ヘッダ行を含めるか否か（CSV のみ有効）。"
                "デフォルトは True（ヘッダあり）。"
            ),
        ),
    ] = True
    # --- Excel 専用オプション ---
    sheet_name: Annotated[
        ExcelSheetName | None,
        Field(
            title="Sheet Name",
            description=(
                "出力する Excel シート名（Excel のみ有効）。"
                "省略または null の場合は 'Sheet1' を使用します。"
            ),
        ),
    ] = None


class ExportFileResult(BaseResult):
    """エクスポート共通レスポンス"""

    file_path: str = Field(
        title="File Path",
        description="出力したファイルのフルパス（拡張子付き）",
    )
