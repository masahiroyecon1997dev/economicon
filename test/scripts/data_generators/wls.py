import numpy as np
import pandas as pd

from data_generators.helpers import N_WLS


# 重みは既知分散の逆数 1/sigma2_i として保存する。
def generate_wls_data(rng: np.random.Generator) -> pd.DataFrame:
    x1 = rng.normal(0.0, 3.0, N_WLS)
    x2 = rng.normal(4.0, 2.5, N_WLS)
    x3 = rng.normal(-2.0, 1.8, N_WLS)

    obs_index = np.arange(1, N_WLS + 1, dtype=float)
    sigma2 = 0.4 + 0.015 * obs_index
    weights = 1.0 / sigma2
    eps = rng.normal(0.0, np.sqrt(sigma2), N_WLS)
    y = 4.0 + 1.8 * x1 - 1.1 * x2 + 0.6 * x3 + eps

    return pd.DataFrame(
        {
            "y": y,
            "x1": x1,
            "x2": x2,
            "x3": x3,
            "sigma2": sigma2,
            "weights": weights,
        }
    )
