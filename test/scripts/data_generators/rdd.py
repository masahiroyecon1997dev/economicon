import numpy as np
import pandas as pd

from data_generators.helpers import N_RDD


# 処置効果が視覚的にも十分識別できるようにジャンプ幅を大きめにしている。
def generate_rdd_data(rng: np.random.Generator) -> pd.DataFrame:
    running_var = rng.uniform(-2.0, 2.0, N_RDD)
    treat = (running_var >= 0.0).astype(float)
    eps = rng.normal(0.0, 1.5, N_RDD)
    y = 2.0 + 1.5 * running_var + 5.0 * treat + eps

    return pd.DataFrame({"y": y, "running_var": running_var})
