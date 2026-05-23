"""分布プレビューサービス（scipy.stats を使用）"""

import math
from typing import Any, ClassVar

import numpy as np
from scipy import stats

from economicon.core.enums import ErrorCode
from economicon.i18n.translation import gettext as _
from economicon.schemas.distribution_preview import (
    DistributionPreviewRequestBody,
    DistributionPreviewResult,
)
from economicon.schemas.enums import DistributionType
from economicon.schemas.types import DistributionConfig
from economicon.utils.exceptions import ProcessingError, ValidationError

# 離散分布のタイプ集合
_DISCRETE_TYPES: frozenset[DistributionType] = frozenset(
    {
        DistributionType.BINOMIAL,
        DistributionType.BERNOULLI,
        DistributionType.POISSON,
        DistributionType.GEOMETRIC,
        DistributionType.HYPERGEOMETRIC,
        DistributionType.NEGATIVE_BINOMIAL,
    }
)

# プレビュー非対応のタイプ集合
_UNSUPPORTED_TYPES: frozenset[DistributionType] = frozenset(
    {
        DistributionType.FIXED,
        DistributionType.SEQUENCE,
    }
)


def _build_frozen_continuous(
    distribution: DistributionConfig,
) -> Any:  # noqa: ANN401
    """連続分布パラメータから scipy.stats 凍結分布を返す"""
    d = distribution
    match d.type:
        case DistributionType.UNIFORM:
            frozen = stats.uniform(
                loc=d.low,  # type: ignore[union-attr]
                scale=d.high - d.low,  # type: ignore[union-attr]
            )
        case DistributionType.EXPONENTIAL:
            frozen = stats.expon(
                scale=d.scale_parameter  # type: ignore[union-attr]
            )
        case DistributionType.NORMAL:
            frozen = stats.norm(
                loc=d.mean,  # type: ignore[union-attr]
                scale=d.standard_deviation,  # type: ignore[union-attr]
            )
        case DistributionType.GAMMA:
            frozen = stats.gamma(
                a=d.shape_parameter,  # type: ignore[union-attr]
                scale=d.scale_parameter,  # type: ignore[union-attr]
            )
        case DistributionType.BETA:
            frozen = stats.beta(
                a=d.alpha,  # type: ignore[union-attr]
                b=d.beta,  # type: ignore[union-attr]
            )
        case DistributionType.WEIBULL:
            frozen = stats.weibull_min(
                c=d.shape_parameter,  # type: ignore[union-attr]
                scale=d.scale_parameter,  # type: ignore[union-attr]
            )
        case DistributionType.LOGNORMAL:
            frozen = stats.lognorm(
                s=d.log_standard_deviation,  # type: ignore[union-attr]
                scale=math.exp(
                    d.log_mean  # type: ignore[union-attr]
                ),
            )
        case DistributionType.CHI_SQUARE:
            frozen = stats.chi2(
                df=d.degrees_of_freedom  # type: ignore[union-attr]
            )
        case DistributionType.F_DISTRIBUTION:
            frozen = stats.f(
                dfn=d.numerator_df,  # type: ignore[union-attr]
                dfd=d.denominator_df,  # type: ignore[union-attr]
            )
        case _:
            raise ValueError(f"Unsupported continuous distribution: {d.type}")
    return frozen


def _build_frozen_discrete(
    distribution: DistributionConfig,
) -> Any:  # noqa: ANN401
    """離散分布パラメータから scipy.stats 凍結分布を返す"""
    d = distribution
    match d.type:
        case DistributionType.BINOMIAL:
            return stats.binom(
                n=d.trial_count,  # type: ignore[union-attr]
                p=d.success_probability,  # type: ignore[union-attr]
            )
        case DistributionType.BERNOULLI:
            return stats.bernoulli(
                p=d.success_probability  # type: ignore[union-attr]
            )
        case DistributionType.POISSON:
            return stats.poisson(
                mu=d.rate  # type: ignore[union-attr]
            )
        case DistributionType.GEOMETRIC:
            return stats.geom(
                p=d.success_probability  # type: ignore[union-attr]
            )
        case DistributionType.HYPERGEOMETRIC:
            return stats.hypergeom(
                M=d.population_size,  # type: ignore[union-attr]
                n=d.success_count,  # type: ignore[union-attr]
                N=d.sample_size,  # type: ignore[union-attr]
            )
        case DistributionType.NEGATIVE_BINOMIAL:
            return stats.nbinom(
                n=d.target_success_count,  # type: ignore[union-attr]
                p=d.success_probability,  # type: ignore[union-attr]
            )
        case _:
            raise ValueError(f"Unsupported discrete distribution: {d.type}")


def _build_frozen(distribution: DistributionConfig) -> Any:  # noqa: ANN401
    """distribution パラメータから scipy.stats 凍結分布を返す"""
    if distribution.type in _DISCRETE_TYPES:
        return _build_frozen_discrete(distribution)
    return _build_frozen_continuous(distribution)


def _compute_x_array(
    d_type: DistributionType,
    frozen: Any,  # noqa: ANN401
    distribution: DistributionConfig,
    x_count: int,
) -> np.ndarray:
    """X 軸の値配列を計算する"""
    if d_type == DistributionType.BERNOULLI:
        return np.array([0.0, 1.0])

    if d_type in _DISCRETE_TYPES:
        x_min = int(max(0, frozen.ppf(0.005)))
        x_max = int(frozen.ppf(0.995))
        if d_type == DistributionType.GEOMETRIC:
            x_min = max(1, x_min)
        x_arr: np.ndarray = np.arange(x_min, x_max + 1, dtype=float)
        if len(x_arr) > x_count:
            x_arr = x_arr[:x_count]
        return x_arr

    # 連続分布
    match d_type:
        case DistributionType.UNIFORM:
            x_min_f = float(
                distribution.low  # type: ignore[union-attr]
            )
            x_max_f = float(
                distribution.high  # type: ignore[union-attr]
            )
        case DistributionType.EXPONENTIAL | DistributionType.WEIBULL:
            x_min_f = 0.0
            x_max_f = float(frozen.ppf(0.995))
        case DistributionType.CHI_SQUARE | DistributionType.F_DISTRIBUTION:
            x_min_f = max(float(frozen.ppf(0.005)), 1e-4)
            x_max_f = float(frozen.ppf(0.995))
        case _:
            x_min_f = float(frozen.ppf(0.005))
            x_max_f = float(frozen.ppf(0.995))

    return np.linspace(x_min_f, x_max_f, x_count)


def _result_dict(
    is_discrete: bool,
    x_arr: np.ndarray,
    frozen: Any,  # noqa: ANN401
) -> dict:
    """scipy 凍結分布から結果辞書を構築する（camelCase キー）"""
    x_list: list[float] = x_arr.tolist()
    if is_discrete:
        y_density: list[float] = frozen.pmf(x_arr).tolist()
    else:
        y_density = frozen.pdf(x_arr).tolist()
    y_cumulative: list[float] = frozen.cdf(x_arr).tolist()
    # OpenAPI response_model のエイリアス名と一致させる
    result = DistributionPreviewResult(
        is_discrete=is_discrete,
        x=x_list,
        y_density=y_density,
        y_cumulative=y_cumulative,
    )
    return result.model_dump(by_alias=True)


class DistributionPreview:
    """分布プレビューサービス"""

    PARAM_NAMES: ClassVar[dict[str, str]] = {}

    def __init__(self, body: DistributionPreviewRequestBody) -> None:
        self.distribution = body.distribution
        self.x_count = body.x_count

    def validate(self) -> None:
        """プレビュー非対応の分布タイプを早期排除する"""
        if self.distribution.type in _UNSUPPORTED_TYPES:
            raise ValidationError(
                error_code=(ErrorCode.DISTRIBUTION_PREVIEW_UNSUPPORTED_TYPE),
                message=_(
                    "Distribution type '{}' is not supported for preview"
                ).format(self.distribution.type),
            )

    def execute(self) -> dict:
        """scipy.stats を使用して分布プレビューデータを計算する"""
        try:
            frozen = _build_frozen(self.distribution)
            is_discrete = self.distribution.type in _DISCRETE_TYPES
            x_arr = _compute_x_array(
                self.distribution.type,
                frozen,
                self.distribution,
                self.x_count,
            )
            return _result_dict(is_discrete, x_arr, frozen)
        except ValidationError, ProcessingError:
            raise
        except Exception as e:
            raise ProcessingError(
                error_code=ErrorCode.DISTRIBUTION_PREVIEW_COMPUTE_ERROR,
                message=_("Failed to compute distribution preview"),
                detail=str(e),
            ) from e
