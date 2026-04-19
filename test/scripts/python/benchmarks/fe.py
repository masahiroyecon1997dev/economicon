import pandas as pd
from linearmodels.panel import PanelOLS

from benchmarks.helpers import f, lm_params_to_dict


# entity cluster SE も同時保存し、API の cluster オプションと照合できるようにする。
def bench_fe(df: pd.DataFrame) -> dict:
    df_indexed = df.set_index(["entity_id", "time_id"])
    var_names = ["x1", "x2"]

    result = PanelOLS(
        df_indexed["y"],
        df_indexed[["x1", "x2"]],
        entity_effects=True,
    ).fit(cov_type="unadjusted")
    clustered = PanelOLS(
        df_indexed["y"],
        df_indexed[["x1", "x2"]],
        entity_effects=True,
    ).fit(cov_type="clustered", cluster_entity=True)

    return {
        "n_obs": int(result.nobs),
        "n_entities": int(df["entity_id"].nunique()),
        "n_periods": int(df["time_id"].nunique()),
        "r_squared_within": f(result.rsquared),
        "r_squared_between": f(result.rsquared_between),
        "r_squared_overall": f(result.rsquared_overall),
        "f_test": {
            "statistic": f(result.f_statistic.stat),
            "p_value": f(result.f_statistic.pval),
        },
        "nonrobust": lm_params_to_dict(result, var_names),
        "clustered_entity": lm_params_to_dict(clustered, var_names),
    }
