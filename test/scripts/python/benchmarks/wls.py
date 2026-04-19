import pandas as pd
import statsmodels.api as sm

from benchmarks.helpers import build_linear_diagnostics, params_to_dict


# WLS の重みは既知分散の逆数を使い、GLS の対角特別ケースとして基準化する。
def bench_wls(df: pd.DataFrame) -> dict:
    y = df["y"].to_numpy(dtype=float)
    X = sm.add_constant(df[["x1", "x2", "x3"]].to_numpy(dtype=float))
    weights = df["weights"].to_numpy(dtype=float)
    var_names = ["const", "x1", "x2", "x3"]

    result = sm.WLS(
        y,
        X,
        weights=weights,  # type: ignore[arg-type]
    ).fit()
    return {
        "dep_var": "y",
        "expl_vars": ["x1", "x2", "x3"],
        "n_obs": len(y),
        "nonrobust": params_to_dict(result, var_names),
        "diagnostics": {
            **build_linear_diagnostics(result),
            "weights_definition": "inverse variance (1 / sigma2)",
            "nan_policy": "no NaN in synthetic_wls; no row dropped",
        },
    }
