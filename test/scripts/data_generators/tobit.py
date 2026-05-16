import numpy as np
import pandas as pd

from data_generators.helpers import N_TOBIT


# 左側打ち切り比率が十分に出るように切片と誤差分散を調整している。
def generate_tobit_data(rng: np.random.Generator) -> pd.DataFrame:
    x1 = rng.normal(0.0, 2.0, N_TOBIT)
    x2 = rng.normal(0.0, 2.0, N_TOBIT)
    eps = rng.normal(0.0, 2.0, N_TOBIT)
    y_latent = 2.0 + 2.0 * x1 + 1.5 * x2 + eps
    y_censored = np.maximum(0.0, y_latent)

    censoring_ratio = (y_censored == 0.0).mean()
    print(f"    [tobit] censoring ratio = {censoring_ratio:.3f}")

    return pd.DataFrame({"y": y_censored, "x1": x1, "x2": x2})
