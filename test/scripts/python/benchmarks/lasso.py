import numpy as np
import pandas as pd
from sklearn.linear_model import Lasso
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from benchmarks.helpers import f


# sklearn は母標準偏差(ddof=0)で標準化するので、その前提を metadata 側でも共有する。
def bench_lasso(df: pd.DataFrame, alpha: float = 0.1) -> dict:
    y = df["y_cont"].values
    X_raw = df[["x1", "x2", "x3"]].values
    var_names = ["x1", "x2", "x3"]

    pipe = Pipeline(
        [
            ("scaler", StandardScaler(with_std=True)),
            ("lasso", Lasso(alpha=alpha, max_iter=10000)),
        ]
    )
    pipe.fit(X_raw, y)

    model = pipe.named_steps["lasso"]
    scaler = pipe.named_steps["scaler"]
    coef_scaled = {var: f(coef) for var, coef in zip(var_names, model.coef_)}

    scale = scaler.scale_
    mean = scaler.mean_
    coef_orig = {
        var: f(coef / std) for var, coef, std in zip(var_names, model.coef_, scale)
    }
    intercept_orig = f(model.intercept_ - np.sum(model.coef_ * mean / scale))

    return {
        "dep_var": "y_cont",
        "alpha": alpha,
        "n_obs": len(y),
        "coef_scaled": coef_scaled,
        "coef_orig": {"const": intercept_orig, **coef_orig},
        "note": (
            "coef_scaled は StandardScaler(ddof=0) 後の Lasso 係数。"
            " coef_orig は元スケールへ逆変換した係数。"
        ),
    }
