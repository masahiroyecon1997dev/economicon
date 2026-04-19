import pandas as pd
import statsmodels.api as sm
from linearmodels.panel import RandomEffects

from benchmarks.helpers import f, lm_params_to_dict


# RE は const を明示追加して API 実装と同じ設計行列に揃える。
def bench_re(df: pd.DataFrame) -> dict:
    df_indexed = df.set_index(["entity_id", "time_id"])
    X = sm.add_constant(df_indexed[["x1", "x2"]])
    var_names = ["const", "x1", "x2"]

    result = RandomEffects(df_indexed["y"], X).fit(cov_type="unadjusted")
    return {
        "n_obs": int(result.nobs),
        "r_squared_within": f(result.rsquared),
        "r_squared_between": f(result.rsquared_between),
        "r_squared_overall": f(result.rsquared_overall),
        "theta": f(result.theta.iloc[0, 0]),
        "nonrobust": lm_params_to_dict(result, var_names),
    }
