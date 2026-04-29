import pandas as pd

from benchmarks.helpers import f


# rdrobust の conventional / bias-corrected / robust をそのまま保存する。
def bench_rdd(df: pd.DataFrame) -> dict:
    from rdrobust import rdrobust

    y = df["y"].values
    x = df["running_var"].values
    # vce='hc1' は API の RDDPayload デフォルトと一致させる
    result = rdrobust(y, x, c=0.0, vce="hc1")

    return {
        "dep_var": "y",
        "running_var": "running_var",
        "cutoff": 0.0,
        "n_total": len(y),
        "n_left": int(result.N_h[0]),
        "n_right": int(result.N_h[1]),
        "bandwidth": {
            "bw_left": f(result.bws.loc["h", "left"]),
            "bw_right": f(result.bws.loc["h", "right"]),
            "bw_bias_left": f(result.bws.loc["b", "left"]),
            "bw_bias_right": f(result.bws.loc["b", "right"]),
        },
        "conventional": {
            "coef": f(result.coef.iloc[0, 0]),
            "std_err": f(result.se.iloc[0, 0]),
            "t_stat": f(result.t.iloc[0, 0]),
            "p_value": f(result.pv.iloc[0, 0]),
            "ci_lower": f(result.ci.iloc[0, 0]),
            "ci_upper": f(result.ci.iloc[0, 1]),
        },
        "bias_corrected": {
            "coef": f(result.coef.iloc[1, 0]),
            "std_err": f(result.se.iloc[1, 0]),
            "t_stat": f(result.t.iloc[1, 0]),
            "p_value": f(result.pv.iloc[1, 0]),
            "ci_lower": f(result.ci.iloc[1, 0]),
            "ci_upper": f(result.ci.iloc[1, 1]),
        },
        "robust": {
            "coef": f(result.coef.iloc[2, 0]),
            "std_err": f(result.se.iloc[2, 0]),
            "t_stat": f(result.t.iloc[2, 0]),
            "p_value": f(result.pv.iloc[2, 0]),
            "ci_lower": f(result.ci.iloc[2, 0]),
            "ci_upper": f(result.ci.iloc[2, 1]),
        },
    }
