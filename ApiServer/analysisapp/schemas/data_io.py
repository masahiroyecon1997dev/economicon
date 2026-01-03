"""インポート関連のスキーマ定義"""
from pydantic import BaseModel, Field
from typing import Optional
from .common import TableRequest


class ImportCsvByPathRequest(BaseModel):
    """CSVファイルパス指定インポートリクエスト"""
    filePath: str = Field(..., description="インポートするCSVファイルのパス")
    tableName: str = Field(..., description="作成するテーブル名")
    separator: str = Field(default=",", description="区切り文字")


class ImportExcelByPathRequest(BaseModel):
    """Excelファイルパス指定インポートリクエスト"""
    filePath: str = Field(..., description="インポートするExcelファイルのパス")
    tableName: str = Field(..., description="作成するテーブル名")
    sheetName: Optional[str] = Field(default=None, description="シート名")


class ImportParquetByPathRequest(BaseModel):
    """Parquetファイルパス指定インポートリクエスト"""
    filePath: str = Field(..., description="インポートするParquetファイルのパス")
    tableName: str = Field(..., description="作成するテーブル名")


class ExportCsvByPathRequest(TableRequest):
    """CSVファイルパス指定エクスポートリクエスト"""
    directoryPath: str = Field(..., description="出力するディレクトリパス")
    fileName: str = Field(..., description="出力するCSVファイル名")
    separator: str = Field(default=",", description="区切り文字")


class ExportExcelByPathRequest(TableRequest):
    """Excelファイルパス指定エクスポートリクエスト"""
    directoryPath: str = Field(..., description="出力するディレクトリパス")
    fileName: str = Field(..., description="出力するExcelファイル名")


class ExportParquetByPathRequest(TableRequest):
    """Parquetファイルパス指定エクスポートリクエスト"""
    directoryPath: str = Field(..., description="出力するディレクトリパス")
    fileName: str = Field(..., description="出力するParquetファイル名")
