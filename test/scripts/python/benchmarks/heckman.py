import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import norm

from benchmarks.helpers import f, params_to_dict


# Step1 Probit と Step2 OLS を分けて保存し、IMR の有意性も直接比較できるようにする。
def bench_heckman(df: pd.DataFrame) -> dict:
    df_all = df.dropna(subset=["educ", "exp", "kids", "employed"])
    X_sel = sm.add_constant(df_all[["educ", "exp", "kids"]].values)
    y_sel = df_all["employed"].values
    sel_var_names = ["const", "educ", "exp", "kids"]

    probit_result = sm.Probit(y_sel, X_sel).fit(disp=0, method="newton")
    xb_all = probit_result.fittedvalues
    phi_all = norm.pdf(xb_all)
    Phi_all = norm.cdf(xb_all)
    df_all = df_all.copy()
    df_all["_imr"] = phi_all / np.where(Phi_all > 1e-16, Phi_all, 1e-16)

    df_selected = df_all[df_all["employed"] == 1.0].dropna(subset=["wage"])
    X_out = sm.add_constant(df_selected[["educ", "exp", "_imr"]].values)
    y_out = df_selected["wage"].values
    out_var_names = ["const", "educ", "exp", "imr"]
    ols_result = sm.OLS(y_out, X_out).fit()

    return {
        "n_total": len(df_all),
        "n_selected": int((df_all["employed"] == 1.0).sum()),
        "selection_ratio": f((df_all["employed"] == 1.0).mean()),
        "step1_probit": {
            "dep_var": "employed",
            "sel_vars": ["educ", "exp", "kids"],
            "n_obs": int(probit_result.nobs),
            **params_to_dict(probit_result, sel_var_names),
            "pseudo_r_squared": f(probit_result.prsquared),
            "log_likelihood": f(probit_result.llf),
        },
        "step2_ols": {
            "dep_var": "wage",
            "outcome_vars": ["educ", "exp"],
            "n_obs": int(ols_result.nobs),
            **params_to_dict(ols_result, out_var_names),
            "r_squared": f(ols_result.rsquared),
            "adj_r_squared": f(ols_result.rsquared_adj),
        },
        "imr": {
            "coefficient": f(ols_result.params[3]),
            "std_error": f(ols_result.bse[3]),
            "t_value": f(ols_result.tvalues[3]),
            "p_value": f(ols_result.pvalues[3]),
        },
    }
