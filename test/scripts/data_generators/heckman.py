import numpy as np
import pandas as pd

from data_generators.helpers import N_HECKMAN


# 排除制約を持つ kids を選択方程式のみに入れている。
def generate_heckman_data(rng: np.random.Generator) -> pd.DataFrame:
    educ = rng.normal(12.0, 2.0, N_HECKMAN)
    exp = rng.normal(5.0, 3.0, N_HECKMAN)
    kids = rng.poisson(1.5, N_HECKMAN).astype(float)

    xb_sel = -5.0 + 0.4 * educ + 0.3 * exp - 0.7 * kids
    prob_sel = 1.0 / (1.0 + np.exp(-xb_sel))
    employed = (rng.uniform(size=N_HECKMAN) < prob_sel).astype(float)

    eps_w = rng.normal(0.0, 2.0, N_HECKMAN)
    wage_latent = 1.5 + 0.8 * educ + 0.4 * exp + eps_w
    wage = np.where(employed == 1.0, wage_latent, np.nan)

    employed_ratio = employed.mean()
    print(f"    [heckman] employed ratio = {employed_ratio:.3f}")

    return pd.DataFrame(
        {
            "wage": wage,
            "employed": employed,
            "educ": educ,
            "exp": exp,
            "kids": kids,
        }
    )
