import numpy as np
import pandas as pd

from data_generators.helpers import N_FGLS_HETERO


# 不均一分散テストのため、誤差分散が説明変数の関数として変化するように設計する。
def generate_fgls_hetero_data(rng: np.random.Generator) -> pd.DataFrame:
    x1 = rng.normal(0.0, 3.5, N_FGLS_HETERO)
    x2 = rng.normal(1.5, 2.0, N_FGLS_HETERO)
    x3 = rng.normal(-1.0, 1.5, N_FGLS_HETERO)

    sigma = 0.7 + 0.08 * np.abs(x1) + 0.12 * (x3 + 1.0) ** 2
    sigma2 = sigma**2
    eps = rng.normal(0.0, sigma, N_FGLS_HETERO)
    y = 2.5 + 1.9 * x1 - 1.4 * x2 + 0.8 * x3 + eps

    return pd.DataFrame(
        {
            "y": y,
            "x1": x1,
            "x2": x2,
            "x3": x3,
            "sigma2_true": sigma2,
        }
    )
