import numpy as np
import pandas as pd

from data_generators.helpers import N_OLS


# DGP (線形):
#   y_cont = 3.0 + 2.5*x1 - 1.8*x2 + 0.9*x3 + ε, ε ~ N(0, 3^2)
# DGP (binary):
#   y_binary ~ Bernoulli(logistic((-0.5 + 1.2*x1 - 0.8*x2 + 0.5*x3) * 0.15))
def generate_ols_data(rng: np.random.Generator) -> pd.DataFrame:
    x1 = rng.normal(0.0, 5.0, N_OLS)
    x2 = rng.normal(10.0, 8.0, N_OLS)
    x3 = rng.normal(-5.0, 4.0, N_OLS)
    eps = rng.normal(0.0, 3.0, N_OLS)

    y_cont = 3.0 + 2.5 * x1 - 1.8 * x2 + 0.9 * x3 + eps
    lc = (-0.5 + 1.2 * x1 - 0.8 * x2 + 0.5 * x3) * 0.15
    prob = 1.0 / (1.0 + np.exp(-lc))
    y_binary = rng.binomial(1, prob, N_OLS).astype(float)

    return pd.DataFrame(
        {
            "y_cont": y_cont,
            "y_binary": y_binary,
            "x1": x1,
            "x2": x2,
            "x3": x3,
        }
    )
