"""共通のスキーマ定義"""

from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, Field

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


NAME_PATTERN = r"^[^\x00-\x1f\x7f]+$"

TableName = Annotated[
    str,
    Field(
        min_length=1,
        max_length=128,
        pattern=NAME_PATTERN,
        examples=["geographic_data", "市区町村人口データ"],
    ),
]
