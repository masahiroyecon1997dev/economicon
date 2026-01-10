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
