"""共通の基盤スキーマ定義"""

from typing import TypeVar

from fastapi import status as _http_status
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class BaseResponse(BaseModel):
    """基本レスポンスモデル"""

    code: str = Field(..., description="レスポンスコード (OK/NG)")


class SuccessResponse[T](BaseResponse):
    """成功レスポンスモデル"""

    code: str = Field(default="OK", description="レスポンスコード")
    result: T = Field(..., description="処理結果")


class ErrorResponse(BaseResponse):
    """エラーレスポンスモデル"""

    code: str = Field(..., description="エラーコード")
    message: str = Field(..., description="エラーメッセージ")
    details: list[str] | None = Field(
        None, description="バリデーションエラーの詳細リスト"
    )


class BaseRequest(BaseModel):
    """基本リクエストモデル"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        strict=True,
    )


class BaseResult(BaseModel):
    """基本レスポンスモデル"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        strict=True,
    )


# OpenAPI エラーレスポンス定義（全ルーターで共用）
COMMON_ERROR_RESPONSES: dict = {
    _http_status.HTTP_400_BAD_REQUEST: {
        "model": ErrorResponse,
        "description": "バリデーション/データ整合性エラー",
    },
    _http_status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "model": ErrorResponse,
        "description": "リクエストボディの形式エラー",
    },
    _http_status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": ErrorResponse,
        "description": "サーバー内部エラー",
    },
}
