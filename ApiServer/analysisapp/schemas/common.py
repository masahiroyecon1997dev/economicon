"""共通のスキーマ定義"""
from typing import Any

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """基本レスポンスモデル"""
    code: str = Field(..., description="レスポンスコード (OK/NG)")


class SuccessResponse(BaseResponse):
    """成功レスポンスモデル"""
    code: str = Field(default="OK", description="レスポンスコード")
    result: Any = Field(..., description="処理結果")


class ErrorResponse(BaseResponse):
    """エラーレスポンスモデル"""
    code: str = Field(default="NG", description="レスポンスコード")
    message: str = Field(..., description="エラーメッセージ")


class TableRequest(BaseModel):
    """テーブル名を含むリクエストの基底クラス"""
    tableName: str = Field(..., description="テーブル名")


class ColumnRequest(TableRequest):
    """テーブル名とカラム名を含むリクエストの基底クラス"""
    tableName: str = Field(..., description="テーブル名")
    columnName: str = Field(..., description="カラム名")
    columnName: str = Field(..., description="カラム名")
