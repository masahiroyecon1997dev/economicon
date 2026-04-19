from typing import cast

import pandas as pd
import statsmodels.api as sm
from linearmodels.iv import IV2SLS
from linearmodels.iv.results import FirstStageResults, IVResults

from benchmarks.helpers import f, lm_params_to_dict


# robust は linearmodels の cov_type='robust' を使い、HC1 相当の比較基準にする。
def bench_iv(df: pd.DataFrame) -> dict:
    y = df["y"]
    exog = sm.add_constant(df[["x_exog"]])
    endog = df[["x_endog"]]
    instruments = df[["z1", "z2"]]
    var_names = ["const", "x_exog", "x_endog"]

    result = IV2SLS(y, exog, endog, instruments).fit(cov_type="unadjusted")
    robust = IV2SLS(y, exog, endog, instruments).fit(cov_type="robust")
    result = cast(IVResults, result)
    result_first_stage = cast(FirstStageResults, result.first_stage)
    first_stage = result_first_stage.diagnostics

    return {
        "dep_var": "y",
        "exog_vars": ["x_exog"],
        "endog_vars": ["x_endog"],
        "instruments": ["z1", "z2"],
        "n_obs": int(result.nobs),
        "r_squared": f(result.rsquared),
        "nonrobust": lm_params_to_dict(result, var_names),
        "hc1": lm_params_to_dict(robust, var_names),
        "first_stage": {
            "partial_r_squared": f(first_stage.loc["x_endog", "partial.rsquared"]),
            "f_statistic": f(first_stage.loc["x_endog", "f.stat"]),
            "f_p_value": f(first_stage.loc["x_endog", "f.pval"]),
        },
    }
