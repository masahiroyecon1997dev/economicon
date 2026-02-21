import numpy as np

from ...models import DistributionConfig, DistributionType


def generate_simulation_data(
    distribution: DistributionConfig, row_count: int
) -> np.ndarray:
    """指定された分布に従ってシミュレーションデータを生成"""

    # NumPyのランダムジェネレータを使用
    rng = np.random.default_rng()

    match distribution.type:
        case DistributionType.UNIFORM:
            return rng.uniform(distribution.low, distribution.high, row_count)
        case DistributionType.EXPONENTIAL:
            return rng.exponential(distribution.scale, row_count)
        case DistributionType.NORMAL:
            return rng.normal(distribution.loc, distribution.scale, row_count)
        case DistributionType.GAMMA:
            return rng.gamma(
                distribution.shape,
                distribution.scale,
                row_count,
            )
        case DistributionType.BETA:
            return rng.beta(distribution.a, distribution.b, row_count)
        case DistributionType.WEIBULL:
            return rng.weibull(distribution.a, row_count) * distribution.scale
        case DistributionType.LOGNORMAL:
            return rng.lognormal(
                distribution.mean, distribution.sigma, row_count
            )
        case DistributionType.BINOMIAL:
            return rng.binomial(distribution.n, distribution.p, row_count)
        case DistributionType.BERNOULLI:
            return rng.binomial(1, distribution.p, row_count)
        case DistributionType.POISSON:
            return rng.poisson(distribution.lam, row_count)
        case DistributionType.GEOMETRIC:
            return rng.geometric(distribution.p, row_count)
        case DistributionType.HYPERGEOMETRIC:
            return rng.hypergeometric(
                distribution.K,
                distribution.N - distribution.K,
                distribution.n,
                row_count,
            )
        case DistributionType.FIXED:
            return np.full(row_count, distribution.value)
