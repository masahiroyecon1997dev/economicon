import numpy as np
import pandas as pd

from data_generators.helpers import N_IV


# z1, z2 を強めの操作変数として設計し、first-stage を十分強くする。
def generate_iv_data(rng: np.random.Generator) -> pd.DataFrame:
    z1 = rng.normal(0.0, 1.0, N_IV)
    z2 = rng.normal(0.0, 1.0, N_IV)
    x_exog = rng.normal(0.0, 3.0, N_IV)
    v = rng.normal(0.0, 0.5, N_IV)
    x_endog = 0.7 * z1 + 0.4 * z2 + v
    u = 0.8 * v + rng.normal(0.0, 1.0, N_IV)
    y = 2.0 + 1.5 * x_exog + 3.0 * x_endog + u

    return pd.DataFrame(
        {
            "y": y,
            "x_exog": x_exog,
            "x_endog": x_endog,
            "z1": z1,
            "z2": z2,
        }
    )
