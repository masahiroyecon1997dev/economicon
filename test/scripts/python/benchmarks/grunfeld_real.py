from __future__ import annotations

import importlib.metadata
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import statsmodels.api as sm
from linearmodels.iv import IV2SLS
from linearmodels.panel import PanelOLS, RandomEffects
from sklearn.linear_model import Lasso, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from benchmarks.helpers import f


def _params_to_dict(result: Any, var_names: list[str]) -> dict[str, object]:
    params_obj = result.params
    bse_obj = getattr(result, "bse", None)
    if bse_obj is None:
        bse_obj = result.std_errors
    tvalues_obj = getattr(result, "tvalues", None)
    if tvalues_obj is None:
        tvalues_obj = result.tstats
    pvalues_obj = result.pvalues

    params = params_obj.to_numpy() if hasattr(params_obj, "to_numpy") else params_obj
    bse = bse_obj.to_numpy() if hasattr(bse_obj, "to_numpy") else bse_obj
    tvalues = (
        tvalues_obj.to_numpy() if hasattr(tvalues_obj, "to_numpy") else tvalues_obj
    )
    pvalues = (
        pvalues_obj.to_numpy() if hasattr(pvalues_obj, "to_numpy") else pvalues_obj
    )
    conf_int = result.conf_int()
    conf_int_array = conf_int.to_numpy() if hasattr(conf_int, "to_numpy") else conf_int

    return {
        "coefficients": {var: f(params[index]) for index, var in enumerate(var_names)},
        "std_errors": {var: f(bse[index]) for index, var in enumerate(var_names)},
        "t_values": {var: f(tvalues[index]) for index, var in enumerate(var_names)},
        "p_values": {var: f(pvalues[index]) for index, var in enumerate(var_names)},
        "conf_int": {
            var: {
                "lower": f(conf_int_array[index][0]),
                "upper": f(conf_int_array[index][1]),
            }
            for index, var in enumerate(var_names)
        },
    }


def bench_grunfeld_real(df: pd.DataFrame) -> dict[str, object]:
    """Generate Python reference benchmarks from persisted parquet data.

    The same parquet file is used by pytest so benchmark drift only occurs when
    the committed fixture changes.
    """
    df = df.copy().astype(float)

    y = df["inv"]
    x = df[["value", "capital"]]
    x_const = sm.add_constant(x)

    ols = sm.OLS(y, x_const).fit()

    panel_df = df.set_index(["firm", "year"])
    fe = PanelOLS(
        panel_df["inv"],
        panel_df[["value", "capital"]],
        entity_effects=True,
    ).fit(cov_type="unadjusted")
    re = RandomEffects(
        panel_df["inv"],
        panel_df[["value", "capital"]],
    ).fit(cov_type="unadjusted")

    inv_median = float(df["inv"].median())
    df["inv_high"] = (df["inv"] > inv_median).astype(float)
    logit = sm.Logit(df["inv_high"], x_const).fit(disp=False)
    probit = sm.Probit(df["inv_high"], x_const).fit(disp=False)

    df_iv = (
        df.sort_values(["firm", "year"])
        .assign(
            value_lag=lambda current: current.groupby("firm")["value"].shift(1),
            capital_lag=lambda current: current.groupby("firm")["capital"].shift(1),
        )
        .dropna(subset=["value_lag", "capital_lag"])
        .reset_index(drop=True)
    )

    iv = IV2SLS(
        df_iv["inv"],
        sm.add_constant(df_iv[["value"]]),
        df_iv[["capital"]],
        df_iv[["value_lag", "capital_lag"]],
    ).fit(cov_type="unadjusted")

    x_arr = df[["value", "capital"]].to_numpy()
    y_arr = df["inv"].to_numpy()
    lasso_pipeline = make_pipeline(StandardScaler(), Lasso(alpha=0.1))
    lasso_pipeline.fit(x_arr, y_arr)
    ridge_pipeline = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    ridge_pipeline.fit(x_arr, y_arr)

    return {
        "metadata": {
            "model": "grunfeld_real",
            "dataset": "plm_grunfeld.parquet",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "libraries": {
                "statsmodels": importlib.metadata.version("statsmodels"),
                "linearmodels": importlib.metadata.version("linearmodels"),
                "scikit_learn": importlib.metadata.version("scikit-learn"),
            },
            "n_obs": int(len(df)),
            "n_obs_iv": int(len(df_iv)),
            "n_firms": int(df["firm"].nunique()),
            "n_years": int(df["year"].nunique()),
            "nan_policy": "Drop rows created by lag construction for IV only; otherwise no NaN rows are removed.",
            "dummy_policy": "inv_high is derived as 1(inv > median(inv)); no category dummy expansion is used.",
        },
        "estimates": {
            "meta": {
                "inv_median": inv_median,
                "n_inv_high": int(df["inv_high"].sum()),
            },
            "ols": {
                **_params_to_dict(ols, ["const", "value", "capital"]),
                "r_squared": f(ols.rsquared),
                "adj_r_squared": f(ols.rsquared_adj),
                "f_test": {
                    "statistic": f(ols.fvalue),
                    "p_value": f(ols.f_pvalue),
                },
            },
            "fe": {
                **_params_to_dict(fe, ["value", "capital"]),
                "r_squared_within": f(fe.rsquared_within),
            },
            "re": {
                **_params_to_dict(re, ["value", "capital"]),
                "r_squared_within": f(re.rsquared_within),
            },
            "logit": {
                **_params_to_dict(logit, ["const", "value", "capital"]),
                "pseudo_r_squared": f(logit.prsquared),
                "log_likelihood": f(logit.llf),
                "log_likelihood_null": f(logit.llnull),
                "aic": f(logit.aic),
                "bic": f(logit.bic),
            },
            "probit": {
                **_params_to_dict(probit, ["const", "value", "capital"]),
                "pseudo_r_squared": f(probit.prsquared),
                "log_likelihood": f(probit.llf),
                "log_likelihood_null": f(probit.llnull),
                "aic": f(probit.aic),
                "bic": f(probit.bic),
            },
            "iv": {
                "coefficients": {key: f(value) for key, value in iv.params.items()},
                "std_errors": {key: f(value) for key, value in iv.std_errors.items()},
                "t_values": {key: f(value) for key, value in iv.tstats.items()},
                "p_values": {key: f(value) for key, value in iv.pvalues.items()},
                "r_squared": f(iv.rsquared),
            },
            "lasso": {
                "alpha": 0.1,
                "coef_scaled": {
                    "value": f(lasso_pipeline.named_steps["lasso"].coef_[0]),
                    "capital": f(lasso_pipeline.named_steps["lasso"].coef_[1]),
                },
            },
            "ridge": {
                "alpha": 1.0,
                "coef_scaled": {
                    "value": f(ridge_pipeline.named_steps["ridge"].coef_[0]),
                    "capital": f(ridge_pipeline.named_steps["ridge"].coef_[1]),
                },
            },
        },
    }
