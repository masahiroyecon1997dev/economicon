import numpy as np
import pandas as pd
import statsmodels.api as sm

from benchmarks.helpers import f


# py4etrics は末尾パラメータに log_sigma を持つため、係数と sigma を分けて保存する。
def bench_tobit(df: pd.DataFrame) -> dict:
    from py4etrics.tobit import Tobit

    y = df["y"].to_numpy(dtype=float)
    X = sm.add_constant(df[["x1", "x2"]].to_numpy(dtype=float))
    var_names = ["const", "x1", "x2"]
    cens = np.zeros(len(y))
    cens[y <= 0.0] = -1

    result = Tobit(y, X, cens=cens, left=0.0).fit(disp=False)
    z_crit = 1.959963985
    n_coef = len(var_names)

    return {
        "dep_var": "y",
        "left_censoring_limit": 0.0,
        "n_obs": len(y),
        "censoring_ratio": f((y == 0.0).mean()),
        "sigma": f(np.exp(result.params[n_coef])),
        "log_likelihood": f(result.llf),
        "aic": f(result.aic),
        "bic": f(result.bic),
        "coefficients": {
            var: f(result.params[index]) for index, var in enumerate(var_names)
        },
        "std_errors": {
            var: f(result.bse[index]) for index, var in enumerate(var_names)
        },
        "t_values": {
            var: f(result.params[index] / result.bse[index])
            for index, var in enumerate(var_names)
        },
        "conf_int": {
            var: {
                "lower": f(result.params[index] - z_crit * result.bse[index]),
                "upper": f(result.params[index] + z_crit * result.bse[index]),
            }
            for index, var in enumerate(var_names)
        },
    }
