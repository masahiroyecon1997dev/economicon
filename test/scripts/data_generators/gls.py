import numpy as np
import pandas as pd

from data_generators.helpers import N_GLS


# 既知の Toeplitz 型共分散行列を別ファイルに保存し、GLS の基準を固定する。
def build_gls_sigma() -> np.ndarray:
    rho = 0.65
    sigma_scale = 1.8
    indices = np.arange(N_GLS)
    distance = np.abs(indices[:, None] - indices[None, :])
    return (sigma_scale**2) * (rho**distance)


def generate_gls_datasets(
    rng: np.random.Generator,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    x1 = rng.normal(0.0, 2.5, N_GLS)
    x2 = rng.normal(0.0, 1.5, N_GLS)

    sigma = build_gls_sigma()
    chol_sigma = np.linalg.cholesky(sigma)
    eps = chol_sigma @ rng.normal(size=N_GLS)
    y = 1.0 + 2.0 * x1 - 1.2 * x2 + eps

    df_data = pd.DataFrame({"y": y, "x1": x1, "x2": x2})
    df_sigma = pd.DataFrame(
        sigma,
        columns=[f"sigma_{i + 1}" for i in range(N_GLS)],
    )
    return df_data, df_sigma
