"""共通のスキーマ定義"""

from typing import Generic, Literal, TypeVar, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)
from pydantic.alias_generators import to_camel

from ..i18n.translation import gettext as _
from .types import DistributionType

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
        strict=True,
    )


class BaseResult(BaseModel):
    """基本レスポンスモデル"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class UniformParams(BaseModel):
    """一様分布のパラメータ"""

    type: Literal[DistributionType.UNIFORM] = Field(description="分布の種類")
    low: float = Field(description="分布の下限")
    high: float = Field(description="分布の上限")

    @model_validator(mode="after")
    def validate_high(self) -> "UniformParams":
        if self.low >= self.high:
            raise ValueError(
                _("For uniform distribution, 'low' must be less than 'high'")
            )
        return self


class ExponentialParams(BaseModel):
    """指数分布のパラメータ"""

    type: Literal[DistributionType.EXPONENTIAL] = Field(
        description="分布の種類"
    )
    scale: float = Field(gt=0, description="尺度パラメータ")


class NormalParams(BaseModel):
    """正規分布のパラメータ"""

    type: Literal[DistributionType.NORMAL] = Field(description="分布の種類")
    loc: float = Field(description="平均")
    scale: float = Field(gt=0, description="標準偏差")


class GammaParams(BaseModel):
    """ガンマ分布のパラメータ"""

    type: Literal[DistributionType.GAMMA] = Field(description="分布の種類")
    shape: float = Field(gt=0, description="形状パラメータ")
    scale: float = Field(gt=0, description="尺度パラメータ")


class BetaParams(BaseModel):
    """ベータ分布のパラメータ"""

    type: Literal[DistributionType.BETA] = Field(description="分布の種類")
    a: float = Field(gt=0, description="形状パラメータa")
    b: float = Field(gt=0, description="形状パラメータb")


class WeibullParams(BaseModel):
    """ワイブル分布のパラメータ"""

    type: Literal[DistributionType.WEIBULL] = Field(description="分布の種類")
    a: float = Field(gt=0, description="形状パラメータ")
    scale: float = Field(gt=0, description="尺度パラメータ")


class LognormalParams(BaseModel):
    """対数正規分布のパラメータ"""

    type: Literal[DistributionType.LOGNORMAL] = Field(description="分布の種類")
    mean: float = Field(description="平均")
    sigma: float = Field(gt=0, description="標準偏差")


class BinomialParams(BaseModel):
    """二項分布のパラメータ"""

    type: Literal[DistributionType.BINOMIAL] = Field(description="分布の種類")
    n: int = Field(gt=0, description="試行回数")
    p: float = Field(gt=0, le=1, description="成功確率")


class BernoulliParams(BaseModel):
    """ベルヌーイ分布のパラメータ"""

    type: Literal[DistributionType.BERNOULLI] = Field(description="分布の種類")
    p: float = Field(gt=0, le=1, description="成功確率")


class PoissonParams(BaseModel):
    """ポアソン分布のパラメータ"""

    type: Literal[DistributionType.POISSON] = Field(description="分布の種類")
    lam: float = Field(gt=0, description="発生率")


class GeometricParams(BaseModel):
    """幾何分布のパラメータ"""

    type: Literal[DistributionType.GEOMETRIC] = Field(description="分布の種類")
    p: float = Field(gt=0, le=1, description="成功確率")


class HypergeometricParams(BaseModel):
    """超幾何分布のパラメータ"""

    type: Literal[DistributionType.HYPERGEOMETRIC] = Field(
        description="分布の種類"
    )
    N: int = Field(gt=0, description="母集団サイズ")
    K: int = Field(gt=0, description="成功要素数")
    n: int = Field(gt=0, description="標本サイズ")

    @model_validator(mode="after")
    def validate_high(self) -> "HypergeometricParams":
        if self.K > self.N:
            raise ValueError(
                _("For hypergeometric distribution, 'K' must not exceed 'N'")
            )
        if self.n > self.N:
            raise ValueError(
                _("For hypergeometric distribution, 'n' must not exceed 'N'")
            )
        return self


DistributionParams = Union[
    UniformParams,
    ExponentialParams,
    NormalParams,
    GammaParams,
    BetaParams,
    WeibullParams,
    LognormalParams,
    BinomialParams,
    BernoulliParams,
    PoissonParams,
    GeometricParams,
    HypergeometricParams,
]
