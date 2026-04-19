import numpy as np
import pandas as pd
import statsmodels.api as sm

from benchmarks.helpers import build_linear_diagnostics, params_to_dict


# API 実装と揃えるため、OLS 残差二乗を 1e-8 でクリップして 1-step FGLS を作る。
def bench_fgls_heteroskedastic(df: pd.DataFrame) -> dict:
    y = df["y"].to_numpy(dtype=float)
    X = sm.add_constant(df[["x1", "x2", "x3"]].to_numpy(dtype=float))
    var_names = ["const", "x1", "x2", "x3"]

    ols_result = sm.OLS(y, X).fit()
    sigma2_hat = np.clip(
        np.asarray(ols_result.resid, dtype=np.float64) ** 2, 1e-8, None
    )
    weights = 1.0 / sigma2_hat
    fgls_result = sm.WLS(
        y,
        X,
        weights=weights,  # type: ignore[arg-type]
    ).fit()

    return {
        "dep_var": "y",
        "expl_vars": ["x1", "x2", "x3"],
        "n_obs": len(y),
        "nonrobust": params_to_dict(fgls_result, var_names),
        "diagnostics": {
            **build_linear_diagnostics(fgls_result),
            "fgls_method": "heteroskedastic",
            "variance_estimator": "sigma2_hat = clip(ols_resid^2, 1e-8, None)",
            "nan_policy": "no NaN in synthetic_fgls_hetero; no row dropped",
        },
    }
