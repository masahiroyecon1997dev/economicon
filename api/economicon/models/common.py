"""共通のスキーマ定義"""

from typing import Literal, TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
from pydantic.alias_generators import to_camel

from economicon.i18n.translation import gettext as _
from economicon.models.enums import DistributionType, TransformMethodType

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


class UniformParams(BaseRequest):
    """一様分布のパラメータ"""

    type: Literal[DistributionType.UNIFORM] = Field(description="分布の種類")
    low: float = Field(description="分布の下限")
    high: float = Field(description="分布の上限")

    @model_validator(mode="after")
    def validate_high(self) -> UniformParams:
        if self.low >= self.high:
            raise ValueError(
                _("For uniform distribution, 'low' must be less than 'high'")
            )
        return self


class ExponentialParams(BaseRequest):
    """指数分布のパラメータ"""

    type: Literal[DistributionType.EXPONENTIAL] = Field(
        description="分布の種類"
    )
    scale: float = Field(gt=0, description="尺度パラメータ")


class NormalParams(BaseRequest):
    """正規分布のパラメータ"""

    type: Literal[DistributionType.NORMAL] = Field(description="分布の種類")
    loc: float = Field(description="平均")
    scale: float = Field(gt=0, description="標準偏差")


class GammaParams(BaseRequest):
    """ガンマ分布のパラメータ"""

    type: Literal[DistributionType.GAMMA] = Field(description="分布の種類")
    shape: float = Field(gt=0, description="形状パラメータ")
    scale: float = Field(gt=0, description="尺度パラメータ")


class BetaParams(BaseRequest):
    """ベータ分布のパラメータ"""

    type: Literal[DistributionType.BETA] = Field(description="分布の種類")
    a: float = Field(gt=0, description="形状パラメータa")
    b: float = Field(gt=0, description="形状パラメータb")


class WeibullParams(BaseRequest):
    """ワイブル分布のパラメータ"""

    type: Literal[DistributionType.WEIBULL] = Field(description="分布の種類")
    a: float = Field(gt=0, description="形状パラメータ")
    scale: float = Field(gt=0, description="尺度パラメータ")


class LognormalParams(BaseRequest):
    """対数正規分布のパラメータ"""

    type: Literal[DistributionType.LOGNORMAL] = Field(description="分布の種類")
    mean: float = Field(description="平均")
    sigma: float = Field(gt=0, description="標準偏差")


class BinomialParams(BaseRequest):
    """二項分布のパラメータ"""

    type: Literal[DistributionType.BINOMIAL] = Field(description="分布の種類")
    n: int = Field(gt=0, description="試行回数")
    p: float = Field(gt=0, le=1, description="成功確率")


class BernoulliParams(BaseRequest):
    """ベルヌーイ分布のパラメータ"""

    type: Literal[DistributionType.BERNOULLI] = Field(description="分布の種類")
    p: float = Field(gt=0, le=1, description="成功確率")


class PoissonParams(BaseRequest):
    """ポアソン分布のパラメータ"""

    type: Literal[DistributionType.POISSON] = Field(description="分布の種類")
    lam: float = Field(gt=0, description="発生率")


class GeometricParams(BaseRequest):
    """幾何分布のパラメータ"""

    type: Literal[DistributionType.GEOMETRIC] = Field(description="分布の種類")
    p: float = Field(gt=0, le=1, description="成功確率")


class HypergeometricParams(BaseRequest):
    """超幾何分布のパラメータ"""

    type: Literal[DistributionType.HYPERGEOMETRIC] = Field(
        description="分布の種類"
    )
    population_size: int = Field(gt=0, description="母集団サイズ")
    success_count: int = Field(gt=0, description="成功要素数")
    sample_size: int = Field(gt=0, description="標本サイズ")

    @model_validator(mode="after")
    def validate_high(self) -> HypergeometricParams:
        if self.success_count > self.population_size:
            raise ValueError(
                _(
                    "For hypergeometric distribution, 'success_count' must "
                    "not exceed 'population_size'"
                )
            )
        if self.sample_size > self.population_size:
            raise ValueError(
                _(
                    "For hypergeometric distribution, 'sample_size' must "
                    "not exceed 'population_size'"
                )
            )
        return self


class FixedParams(BaseRequest):
    """固定値のパラメータ"""

    type: Literal[DistributionType.FIXED] = Field(description="分布の種類")
    value: int | float = Field(description="固定値")


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
    def validate_log_base(cls, v: float) -> float:
        # log_base == 1 のケースを個別にチェック
        if v == 1:
            raise ValueError(_("Log base cannot be 1."))
        return v


class PowerParams(BaseRequest):
    """べき乗変換のパラメータ"""

    method: Literal[TransformMethodType.POWER] = Field(description="変換方法")
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
    def validate_root_index(cls, v: float) -> float:
        # root_index == 0 のケースを個別にチェック
        if v == 0:
            raise ValueError(_("Root index cannot be 0."))
        return v


class BinaryChoiceRegularization(BaseRequest):
    type: Literal["l1", "l2"] = "l1"
    alpha: float = Field(default=1.0, ge=0.0)
