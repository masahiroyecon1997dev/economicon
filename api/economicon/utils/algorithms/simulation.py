import numpy as np

from economicon.schemas import DistributionConfig, DistributionType


def generate_simulation_data(
    distribution: DistributionConfig, row_count: int
) -> np.ndarray:
    """指定された分布に従ってシミュレーションデータを生成"""

    rng = np.random.default_rng()

    # 各分布の生成ロジックをマッピング
    generators = {
        DistributionType.UNIFORM: lambda d: rng.uniform(
            d.low, d.high, row_count
        ),
        DistributionType.EXPONENTIAL: lambda d: rng.exponential(
            d.scale, row_count
        ),
        DistributionType.NORMAL: lambda d: rng.normal(
            d.loc, d.scale, row_count
        ),
        DistributionType.GAMMA: lambda d: rng.gamma(
            d.shape, d.scale, row_count
        ),
        DistributionType.BETA: lambda d: rng.beta(d.a, d.b, row_count),
        DistributionType.WEIBULL: lambda d: (
            rng.weibull(d.a, row_count) * d.scale
        ),
        DistributionType.LOGNORMAL: lambda d: rng.lognormal(
            d.mean, d.sigma, row_count
        ),
        DistributionType.BINOMIAL: lambda d: rng.binomial(d.n, d.p, row_count),
        DistributionType.BERNOULLI: lambda d: rng.binomial(1, d.p, row_count),
        DistributionType.POISSON: lambda d: rng.poisson(d.lam, row_count),
        DistributionType.GEOMETRIC: lambda d: rng.geometric(d.p, row_count),
        DistributionType.HYPERGEOMETRIC: lambda d: rng.hypergeometric(
            d.success_count,
            d.population_size - d.success_count,
            d.sample_size,
            row_count,
        ),
        DistributionType.NEGATIVE_BINOMIAL: lambda d: rng.negative_binomial(
            d.n, d.p, row_count
        ),
        DistributionType.FIXED: lambda d: np.full(row_count, d.value),
    }

    generator = generators.get(distribution.type)
    if not generator:
        raise ValueError(f"Unsupported distribution type: {distribution.type}")

    return generator(distribution)
