"""インポート関連のスキーマ定義"""

from typing import Annotated

from pydantic import BaseModel, Field

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
        FilePath, Field(description="インポートするCSVファイルのパス")
    ]
    table_name: NewTableName
    separator: Annotated[Separator, Field(description="区切り文字")] = ","


class ImportExcelByPathRequestBody(BaseRequest):
    """Excelファイルパス指定インポートリクエスト"""

    file_path: Annotated[
        FilePath, Field(description="インポートするExcelファイルのパス")
    ]
    table_name: NewTableName
    sheet_name: ExcelSheetName


class ImportParquetByPathRequestBody(BaseRequest):
    """Parquetファイルパス指定インポートリクエスト"""

    file_path: Annotated[
        FilePath, Field(description="インポートするParquetファイルのパス")
    ]
    table_name: NewTableName


class ExportCsvByPathRequestBody(BaseRequest):
    """CSVファイルパス指定エクスポートリクエスト"""

    table_name: TableName
    directory_path: Annotated[
        DirectoryPath,
        Field(description="出力するCSVファイルのディレクトリパス"),
    ]
    file_name: Annotated[
        FileName, Field(description="出力するCSVファイルのファイル名")
    ]
    separator: Separator


class ExportExcelByPathRequestBody(BaseModel):
    """Excelファイルパス指定エクスポートリクエスト"""

    table_name: TableName
    directory_path: Annotated[
        DirectoryPath,
        Field(description="出力するExcelファイルのディレクトリパス"),
    ]
    file_name: Annotated[
        FileName, Field(description="出力するExcelファイルのファイル名")
    ]


class ExportParquetByPathRequestBody(BaseModel):
    """Parquetファイルパス指定エクスポートリクエスト"""

    table_name: TableName
    directory_path: Annotated[
        DirectoryPath,
        Field(description="出力するParquetファイルのディレクトリパス"),
    ]
    file_name: Annotated[
        FileName, Field(description="出力するParquetファイルのファイル名")
    ]
