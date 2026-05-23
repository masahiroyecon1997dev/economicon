import numpy as np
import pandas as pd
import statsmodels.api as sm

from benchmarks.helpers import f, params_to_dict


# logit は MLE の収束差があり得るため、厳密比較は許容差を持たせる。
def bench_logit(df: pd.DataFrame) -> dict:
    y = df["y_binary"].to_numpy(dtype=float)
    X = sm.add_constant(df[["x1", "x2", "x3"]].to_numpy(dtype=float))
    var_names = ["const", "x1", "x2", "x3"]

    result = sm.Logit(y, X).fit(disp=0, method="newton")
    return {
        "dep_var": "y_binary",
        "n_obs": int(result.nobs),
        "n_positive": int(np.sum(y)),
        **params_to_dict(result, var_names),
        "pseudo_r_squared": f(result.prsquared),
        "log_likelihood": f(result.llf),
        "log_likelihood_null": f(result.llnull),
        "aic": f(result.aic),
        "bic": f(result.bic),
        "lr_test": {
            "statistic": f(result.llr),
            "df": int(result.df_model),
            "p_value": f(result.llr_pvalue),
        },
    }
