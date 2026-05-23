import numpy as np
import pandas as pd

from data_generators.helpers import N_FGLS_AR1


# 行順を時系列順とみなし、GLSAR の AR(1) 反復推定を安定に検証する。
def generate_fgls_ar1_data(rng: np.random.Generator) -> pd.DataFrame:
    x1 = rng.normal(0.0, 2.0, N_FGLS_AR1)
    x2 = rng.normal(0.0, 1.2, N_FGLS_AR1)
    x3 = rng.normal(1.0, 1.5, N_FGLS_AR1)

    rho = 0.7
    eta = rng.normal(0.0, 1.0, N_FGLS_AR1)
    u = np.zeros(N_FGLS_AR1)
    u[0] = eta[0] / np.sqrt(1.0 - rho**2)
    for index in range(1, N_FGLS_AR1):
        u[index] = rho * u[index - 1] + eta[index]

    y = 0.5 + 1.4 * x1 - 0.9 * x2 + 0.6 * x3 + u

    return pd.DataFrame(
        {
            "time_id": np.arange(1, N_FGLS_AR1 + 1, dtype=float),
            "y": y,
            "x1": x1,
            "x2": x2,
            "x3": x3,
            "ar1_error": u,
        }
    )
