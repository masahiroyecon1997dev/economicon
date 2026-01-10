"""インポート関連のスキーマ定義"""
from typing import Optional

from pydantic import BaseModel, Field


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


class ExportCsvByPathRequest(BaseModel):
    """CSVファイルパス指定エクスポートリクエスト"""
    tableName: str = Field(..., description="テーブル名")
    directoryPath: str = Field(..., description="出力するディレクトリパス")
    fileName: str = Field(..., description="出力するCSVファイル名")
    separator: str = Field(default=",", description="区切り文字")


class ExportExcelByPathRequest(BaseModel):
    """Excelファイルパス指定エクスポートリクエスト"""
    tableName: str = Field(..., description="テーブル名")
    directoryPath: str = Field(..., description="出力するディレクトリパス")
    fileName: str = Field(..., description="出力するExcelファイル名")


class ExportParquetByPathRequest(BaseModel):
    """Parquetファイルパス指定エクスポートリクエスト"""
    tableName: str = Field(..., description="テーブル名")
    directoryPath: str = Field(..., description="出力するディレクトリパス")
    fileName: str = Field(..., description="出力するParquetファイル名")
