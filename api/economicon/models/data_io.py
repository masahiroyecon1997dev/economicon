"""インポート関連のスキーマ定義"""

from typing import Annotated

from pydantic import Field

from .common import BaseRequest
from .types import (
    DirectoryPath,
    ExcelSheetName,
    FileName,
    FilePath,
    NewTableName,
    Separator,
    TableName,
)


class ImportCsvByPathRequestBody(BaseRequest):
    """CSVファイルパス指定インポートリクエスト"""

    file_path: Annotated[
        FilePath,
        Field(
            title="File Path",
            description="インポートするCSVファイルの絶対パス（相対パスはサポートされていません）。",
        ),
    ]
    table_name: Annotated[
        NewTableName,
        Field(
            title="Table Name",
            description="インポート先のテーブル名",
        ),
    ]
    separator: Annotated[
        Separator,
        Field(
            title="Separator",
            description="CSV区切り文字。カンマかタブ、もしくは1から10文字の任意の文字列から選択してください。",
        ),
    ] = ","


class ImportExcelByPathRequestBody(BaseRequest):
    """Excelファイルパス指定インポートリクエスト"""

    file_path: Annotated[
        FilePath,
        Field(
            title="File Path",
            description="インポートするExcelファイルの絶対パス（相対パスはサポートされていません）。",
        ),
    ]
    table_name: Annotated[
        NewTableName,
        Field(
            title="Table Name",
            description="インポート後のテーブル名。ワークスペース内で既存のテーブル名と重複しない名前を指定してください。",
        ),
    ]
    sheet_name: Annotated[
        ExcelSheetName,
        Field(
            title="Sheet Name",
            description="インポートするExcelシートの名前。指定したシートがExcelファイル内に存在しない場合、インポートは失敗します。シート名は大文字と小文字を区別します。",
        ),
    ]


class ImportParquetByPathRequestBody(BaseRequest):
    """Parquetファイルパス指定インポートリクエスト"""

    file_path: Annotated[
        FilePath,
        Field(
            title="File Path",
            description="インポートするParquetファイルの絶対パス（相対パスはサポートされていません）。",
        ),
    ]
    table_name: Annotated[
        NewTableName,
        Field(
            title="Table Name",
            description="インポート後のテーブル名。ワークスペース内で既存のテーブル名と重複しない名前を指定してください。",
        ),
    ]


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
