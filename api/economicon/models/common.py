"""共通のスキーマ定義"""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class BaseResponse(BaseModel):
    """基本レスポンスモデル"""

    code: str = Field(..., description="レスポンスコード (OK/NG)")


class SuccessResponse(BaseResponse, Generic[T]):
    """成功レスポンスモデル"""

    code: str = Field(default="OK", description="レスポンスコード")
    result: T = Field(..., description="処理結果")


class ErrorResponse(BaseResponse):
    """エラーレスポンスモデル"""

    code: str = Field(default="NG", description="レスポンスコード")
    message: str = Field(..., description="エラーメッセージ")


class BaseRequest(BaseModel):
    """基本リクエストモデル"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class BaseResult(BaseModel):
    """基本レスポンスモデル"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
