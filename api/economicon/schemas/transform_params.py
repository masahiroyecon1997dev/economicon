"""変換パラメータ関連のスキーマ定義"""

from typing import Literal

from pydantic import Field, field_validator

from economicon.i18n.translation import gettext as _
from economicon.schemas.common import BaseRequest
from economicon.schemas.enums import TransformMethodType


class LogParams(BaseRequest):
    """対数変換のパラメータ"""

    method: Literal[TransformMethodType.LOG] = Field(description="変換方法")
    log_base: float | None = Field(
        None,
        gt=0,
        description="対数の底 (省略時は自然対数)",
    )

    @field_validator("log_base")
    @classmethod
    def validate_log_base(cls, value: float) -> float:
        if value == 1:
            raise ValueError(_("Log base cannot be 1."))
        return value


class PowerParams(BaseRequest):
    """べき乗変換のパラメータ"""

    method: Literal[TransformMethodType.POWER] = Field(
        description="変換方法"
    )
    exponent: float = Field(
        default=2.0,
        description="べき乗の指数 (省略時は2乗)",
    )


class RootParams(BaseRequest):
    """平方根変換のパラメータ"""

    method: Literal[TransformMethodType.ROOT] = Field(description="変換方法")
    root_index: float = Field(
        default=2.0,
        gt=0,
        description="ルートの指数 (省略時は平方根)",
    )

    @field_validator("root_index")
    @classmethod
    def validate_root_index(cls, value: float) -> float:
        if value == 0:
            raise ValueError(_("Root index cannot be 0."))
        return value
