import pandas as pd
import statsmodels.api as sm

from benchmarks.helpers import build_linear_diagnostics, params_to_dict


# GLS は既知の sigma ファイルをそのまま使い、Aitken 推定量を固定する。
def bench_gls(df: pd.DataFrame, sigma_df: pd.DataFrame) -> dict:
    y = df["y"].to_numpy(dtype=float)
    X = sm.add_constant(df[["x1", "x2"]].to_numpy(dtype=float))
    sigma = sigma_df.to_numpy(dtype=float)
    var_names = ["const", "x1", "x2"]

    result = sm.GLS(y, X, sigma=sigma).fit()
    return {
        "dep_var": "y",
        "expl_vars": ["x1", "x2"],
        "n_obs": len(y),
        "nonrobust": params_to_dict(result, var_names),
        "diagnostics": {
            **build_linear_diagnostics(result),
            "sigma_shape": list(sigma.shape),
            "sigma_structure": "Toeplitz AR(1)-like covariance",
            "nan_policy": "GLS requires aligned complete cases; no NaN in synthetic_gls_data",
        },
    }
