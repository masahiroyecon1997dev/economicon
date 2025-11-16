from typing import Any, Dict

import numpy as np


def generate_simulation_data(
    distribution_type: str,
    distribution_params: Dict[str, Any], num_rows: int
):
    """指定された分布に従ってシミュレーションデータを生成"""

    # NumPyのランダムジェネレータを使用
    rng = np.random.default_rng()

    if distribution_type == 'uniform':
        return rng.uniform(
            distribution_params['low'],
            distribution_params['high'],
            num_rows
        )

    elif distribution_type == 'exponential':
        return rng.exponential(distribution_params['scale'], num_rows)

    elif distribution_type == 'normal':
        return rng.normal(
            distribution_params['loc'],
            distribution_params['scale'],
            num_rows
        )

    elif distribution_type == 'gamma':
        return rng.gamma(
            distribution_params['shape'],
            distribution_params['scale'],
            num_rows
        )

    elif distribution_type == 'beta':
        return rng.beta(
            distribution_params['a'],
            distribution_params['b'],
            num_rows
        )

    elif distribution_type == 'weibull':
        return rng.weibull(distribution_params['a'], num_rows)

    elif distribution_type == 'lognormal':
        return rng.lognormal(
            distribution_params['mean'],
            distribution_params['sigma'],
            num_rows
        )

    elif distribution_type == 'binomial':
        return rng.binomial(
            distribution_params['n'],
            distribution_params['p'],
            num_rows
        )

    elif distribution_type == 'bernoulli':
        return rng.binomial(1, distribution_params['p'], num_rows)

    elif distribution_type == 'poisson':
        return rng.poisson(distribution_params['lam'], num_rows)

    elif distribution_type == 'geometric':
        return rng.geometric(distribution_params['p'], num_rows)

    elif distribution_type == 'hypergeometric':
        return rng.hypergeometric(
            distribution_params['K'],
            distribution_params['N'] - distribution_params['K'],
            distribution_params['n'],
            num_rows
        )

    else:
        raise ValueError(
            f"Unsupported distribution type: {distribution_type}"
        )
