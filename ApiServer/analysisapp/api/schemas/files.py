"""ファイル操作・取得関連のスキーマ定義"""
from pydantic import BaseModel, Field
from typing import Optional
from .common import TableRequest


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


class GetFilesRequest(BaseModel):
    """ファイル一覧取得リクエスト（GETクエリパラメータ用）"""
    directoryPath: str = Field(..., description="対象ディレクトリパス")


class FetchDataToJsonRequest(BaseModel):
    """データJSON取得リクエスト（GETクエリパラメータ用）"""
    tableName: str = Field(..., description="対象テーブル名")
    startRow: int = Field(..., description="開始行番号")
    fetchRows: int = Field(..., description="取得行数")


class GetColumnListRequest(BaseModel):
    """カラムリスト取得リクエスト（GETクエリパラメータ用）"""
    tableName: str = Field(..., description="対象テーブル名")
    isNumberOnly: str = Field(default="false", description="数値カラムのみ取得")
