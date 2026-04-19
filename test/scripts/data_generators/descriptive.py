import numpy as np
import pandas as pd

from data_generators.helpers import N_DESC


# 歪度や正負の相関を同時に検証できるように分布を混在させている。
def generate_descriptive_data(rng: np.random.Generator) -> pd.DataFrame:
    A = rng.normal(100.0, 20.0, N_DESC)
    B = rng.gamma(2.0, 15.0, N_DESC)
    D = rng.normal(0.0, 10.0, N_DESC)
    C = 0.7 * A + 0.5 * D + rng.normal(0.0, 5.0, N_DESC)
    E = -0.6 * A + rng.normal(0.0, 15.0, N_DESC)
    category_raw = rng.choice(["Low", "Mid", "High"], size=N_DESC)

    return pd.DataFrame(
        {
            "A": A,
            "B": B,
            "C": C,
            "D": D,
            "E": E,
            "category": category_raw,
        }
    )
