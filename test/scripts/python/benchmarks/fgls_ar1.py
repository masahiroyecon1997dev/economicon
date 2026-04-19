import pandas as pd
import statsmodels.api as sm

from benchmarks.helpers import build_linear_diagnostics, f, params_to_dict


# statsmodels GLSAR の iterative_fit を使い、API 実装と同じ max_iter で固定する。
def bench_fgls_ar1(df: pd.DataFrame, max_iter: int = 10) -> dict:
    y = df["y"].to_numpy(dtype=float)
    X = sm.add_constant(df[["x1", "x2", "x3"]].to_numpy(dtype=float))
    var_names = ["const", "x1", "x2", "x3"]

    model = sm.GLSAR(y, X, rho=1)
    result = model.iterative_fit(maxiter=max_iter)
    rho_value = model.rho[0] if hasattr(model.rho, "__len__") else model.rho

    return {
        "dep_var": "y",
        "expl_vars": ["x1", "x2", "x3"],
        "n_obs": int(result.nobs),
        "nonrobust": params_to_dict(result, var_names),
        "diagnostics": {
            **build_linear_diagnostics(result),
            "fgls_method": "ar1",
            "max_iter": max_iter,
            "estimated_rho": f(rho_value),
            "nan_policy": "no NaN in synthetic_fgls_ar1; no row dropped",
        },
    }
