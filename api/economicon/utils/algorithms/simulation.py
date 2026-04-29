import numpy as np

from economicon.schemas import DistributionConfig, DistributionType


def generate_simulation_data(
    distribution: DistributionConfig,
    row_count: int,
    seed: int | np.random.SeedSequence | None = None,
) -> np.ndarray:
    """指定された分布に従ってシミュレーションデータを生成"""

    rng = np.random.default_rng(seed)

    # 各分布の生成ロジックをマッピング
    generators = {
        DistributionType.UNIFORM: lambda d: rng.uniform(
            d.low, d.high, row_count
        ),
        DistributionType.EXPONENTIAL: lambda d: rng.exponential(
            d.scale_parameter, row_count
        ),
        DistributionType.NORMAL: lambda d: rng.normal(
            d.mean, d.standard_deviation, row_count
        ),
        DistributionType.GAMMA: lambda d: rng.gamma(
            d.shape_parameter, d.scale_parameter, row_count
        ),
        DistributionType.BETA: lambda d: rng.beta(d.alpha, d.beta, row_count),
        DistributionType.WEIBULL: lambda d: (
            rng.weibull(d.shape_parameter, row_count) * d.scale_parameter
        ),
        DistributionType.LOGNORMAL: lambda d: rng.lognormal(
            d.log_mean, d.log_standard_deviation, row_count
        ),
        DistributionType.BINOMIAL: lambda d: rng.binomial(
            d.trial_count, d.success_probability, row_count
        ),
        DistributionType.BERNOULLI: lambda d: rng.binomial(
            1, d.success_probability, row_count
        ),
        DistributionType.POISSON: lambda d: rng.poisson(d.rate, row_count),
        DistributionType.GEOMETRIC: lambda d: rng.geometric(
            d.success_probability, row_count
        ),
        DistributionType.HYPERGEOMETRIC: lambda d: rng.hypergeometric(
            d.success_count,
            d.population_size - d.success_count,
            d.sample_size,
            row_count,
        ),
        DistributionType.NEGATIVE_BINOMIAL: lambda d: rng.negative_binomial(
            d.target_success_count, d.success_probability, row_count
        ),
        DistributionType.FIXED: lambda d: np.full(row_count, d.value),
        DistributionType.SEQUENCE: lambda d: np.arange(
            d.start,
            d.start + row_count * d.step,
            d.step,
            dtype=np.int64,
        ),
    }

    generator = generators.get(distribution.type)
    if not generator:
        raise ValueError(f"Unsupported distribution type: {distribution.type}")

    return generator(distribution)
