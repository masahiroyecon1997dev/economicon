"""インポート関連のスキーマ定義"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ImportCsvByPathRequest(BaseModel):
    """CSVファイルパス指定インポートリクエスト"""
    file_path: str = Field(
        ...,
        alias="filePath",
        description="インポートするCSVファイルのパス",
        min_length=1,
        max_length=1024
    )
    table_name: str = Field(
        ...,
        alias="tableName",
        description="作成するテーブル名",
        min_length=1,
        max_length=255
    )
    separator: str = Field(
        default=",",
        description="区切り文字",
        min_length=1,
        max_length=10
    )

    model_config = ConfigDict(populate_by_name=True)


class ImportExcelByPathRequest(BaseModel):
    """Excelファイルパス指定インポートリクエスト"""
    file_path: str = Field(
        ...,
        alias="filePath",
        description="インポートするExcelファイルのパス",
        min_length=1,
        max_length=1024
    )
    table_name: str = Field(
        ...,
        alias="tableName",
        description="作成するテーブル名",
        min_length=1,
        max_length=255
    )
    sheet_name: Optional[str] = Field(
        default=None,
        alias="sheetName",
        description="シート名",
        max_length=255
    )

    model_config = ConfigDict(populate_by_name=True)


class ImportParquetByPathRequest(BaseModel):
    """Parquetファイルパス指定インポートリクエスト"""
    file_path: str = Field(
        ...,
        alias="filePath",
        description="インポートするParquetファイルのパス",
        min_length=1,
        max_length=1024
    )
    table_name: str = Field(
        ...,
        alias="tableName",
        description="作成するテーブル名",
        min_length=1,
        max_length=255
    )

    model_config = ConfigDict(populate_by_name=True)


class ExportCsvByPathRequest(BaseModel):
    """CSVファイルパス指定エクスポートリクエスト"""
    table_name: str = Field(
        ...,
        alias="tableName",
        description="テーブル名",
        min_length=1,
        max_length=255
    )
    directory_path: str = Field(
        ...,
        alias="directoryPath",
        description="出力するディレクトリパス",
        min_length=1,
        max_length=1024
    )
    file_name: str = Field(
        ...,
        alias="fileName",
        description="出力するCSVファイル名",
        min_length=1,
        max_length=255
    )
    separator: str = Field(
        default=",",
        description="区切り文字",
        min_length=1,
        max_length=10
    )

    model_config = ConfigDict(populate_by_name=True)


class ExportExcelByPathRequest(BaseModel):
    """Excelファイルパス指定エクスポートリクエスト"""
    table_name: str = Field(
        ...,
        alias="tableName",
        description="テーブル名",
        min_length=1,
        max_length=255
    )
    directory_path: str = Field(
        ...,
        alias="directoryPath",
        description="出力するディレクトリパス",
        min_length=1,
        max_length=1024
    )
    file_name: str = Field(
        ...,
        alias="fileName",
        description="出力するExcelファイル名",
        min_length=1,
        max_length=255
    )

    model_config = ConfigDict(populate_by_name=True)


class ExportParquetByPathRequest(BaseModel):
    """Parquetファイルパス指定エクスポートリクエスト"""
    table_name: str = Field(
        ...,
        alias="tableName",
        description="テーブル名",
        min_length=1,
        max_length=255
    )
    directory_path: str = Field(
        ...,
        alias="directoryPath",
        description="出力するディレクトリパス",
        min_length=1,
        max_length=1024
    )
    file_name: str = Field(
        ...,
        alias="fileName",
        description="出力するParquetファイル名",
        min_length=1,
        max_length=255
    )

    model_config = ConfigDict(populate_by_name=True)
