"""分布パラメータ関連のスキーマ定義"""

from typing import Literal

from pydantic import Field, model_validator

from economicon.i18n.translation import gettext as _
from economicon.schemas.common import BaseRequest
from economicon.schemas.enums import DistributionType


class UniformParams(BaseRequest):
    """一様分布のパラメータ"""

    type: Literal[DistributionType.UNIFORM] = Field(
        description="分布の種類"
    )
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

    type: Literal[DistributionType.WEIBULL] = Field(
        description="分布の種類"
    )
    a: float = Field(gt=0, description="形状パラメータ")
    scale: float = Field(gt=0, description="尺度パラメータ")


class LognormalParams(BaseRequest):
    """対数正規分布のパラメータ"""

    type: Literal[DistributionType.LOGNORMAL] = Field(
        description="分布の種類"
    )
    mean: float = Field(description="平均")
    sigma: float = Field(gt=0, description="標準偏差")


class BinomialParams(BaseRequest):
    """二項分布のパラメータ"""

    type: Literal[DistributionType.BINOMIAL] = Field(
        description="分布の種類"
    )
    n: int = Field(gt=0, description="試行回数")
    p: float = Field(gt=0, le=1, description="成功確率")


class BernoulliParams(BaseRequest):
    """ベルヌーイ分布のパラメータ"""

    type: Literal[DistributionType.BERNOULLI] = Field(
        description="分布の種類"
    )
    p: float = Field(gt=0, le=1, description="成功確率")


class PoissonParams(BaseRequest):
    """ポアソン分布のパラメータ"""

    type: Literal[DistributionType.POISSON] = Field(description="分布の種類")
    lam: float = Field(gt=0, description="発生率")


class GeometricParams(BaseRequest):
    """幾何分布のパラメータ"""

    type: Literal[DistributionType.GEOMETRIC] = Field(
        description="分布の種類"
    )
    p: float = Field(gt=0, le=1, description="成功確率")


class NegativeBinomialParams(BaseRequest):
    """負の二項分布のパラメータ"""

    type: Literal[DistributionType.NEGATIVE_BINOMIAL] = Field(
        description="分布の種類"
    )
    n: int = Field(gt=0, description="成功回数")
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


class SequenceParams(BaseRequest):
    """連番のパラメータ"""

    type: Literal[DistributionType.SEQUENCE] = Field(
        description="分布の種類"
    )
    start: int = Field(default=1, description="開始値")
    step: int = Field(default=1, description="増分（負値で降順連番）")
