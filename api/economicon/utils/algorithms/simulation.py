import numpy as np

from ...models import DistributionType, DistributionConfig


def generate_simulation_data(distribution: DistributionConfig, num_rows: int):
    """指定された分布に従ってシミュレーションデータを生成"""

    # NumPyのランダムジェネレータを使用
    rng = np.random.default_rng()

    if distribution.type == DistributionType.UNIFORM:
        return rng.uniform(distribution.low, distribution.high, num_rows)

    elif distribution.type == DistributionType.EXPONENTIAL:
        return rng.exponential(distribution.scale, num_rows)

    elif distribution.type == DistributionType.NORMAL:
        return rng.normal(distribution.loc, distribution.scale, num_rows)

    elif distribution.type == DistributionType.GAMMA:
        return rng.gamma(
            distribution.shape,
            distribution.scale,
            num_rows,
        )

    elif distribution.type == DistributionType.BETA:
        return rng.beta(distribution.a, distribution.b, num_rows)

    elif distribution.type == DistributionType.WEIBULL:
        return rng.weibull(distribution.a, num_rows) * distribution.scale

    elif distribution.type == DistributionType.LOGNORMAL:
        return rng.lognormal(distribution.mean, distribution.sigma, num_rows)

    elif distribution.type == DistributionType.BINOMIAL:
        return rng.binomial(distribution.n, distribution.p, num_rows)

    elif distribution.type == DistributionType.BERNOULLI:
        return rng.binomial(1, distribution.p, num_rows)

    elif distribution.type == DistributionType.POISSON:
        return rng.poisson(distribution.lam, num_rows)

    elif distribution.type == DistributionType.GEOMETRIC:
        return rng.geometric(distribution.p, num_rows)

    elif distribution.type == DistributionType.HYPERGEOMETRIC:
        return rng.hypergeometric(
            distribution.K,
            distribution.N - distribution.K,
            distribution.n,
            num_rows,
        )

    else:
        raise ValueError(f"Unsupported distribution type: {distribution.type}")
