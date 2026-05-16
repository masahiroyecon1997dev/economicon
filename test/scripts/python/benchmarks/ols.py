import pandas as pd
import statsmodels.api as sm

from benchmarks.helpers import f, params_to_dict


# OLS は HC1/HAC を同時に保存し、回帰結果の基準ケースを持つ。
def bench_ols(df: pd.DataFrame) -> dict:
    y = df["y_cont"].values
    X = sm.add_constant(df[["x1", "x2", "x3"]].values)
    var_names = ["const", "x1", "x2", "x3"]

    res_ols = sm.OLS(y, X).fit()
    res_hc1 = sm.OLS(y, X).fit(cov_type="HC1")
    res_hac = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 1})

    return {
        "dep_var": "y_cont",
        "expl_vars": ["x1", "x2", "x3"],
        "n_obs": len(y),
        "r_squared": f(res_ols.rsquared),
        "adj_r_squared": f(res_ols.rsquared_adj),
        "f_test": {
            "statistic": f(res_ols.fvalue),
            "df1": int(res_ols.df_model),
            "df2": int(res_ols.df_resid),
            "p_value": f(res_ols.f_pvalue),
        },
        "nonrobust": params_to_dict(res_ols, var_names),
        "hc1": params_to_dict(res_hc1, var_names),
        "hac_maxlags1": params_to_dict(res_hac, var_names),
    }
