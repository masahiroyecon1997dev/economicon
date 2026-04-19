"""
statsmodels / linearmodels ベンチマーク計算スクリプト
======================================================
generate_synthetic_data.py が生成したデータを読み込み、各推定結果を
test/benchmarks/synthetic_gold.json に書き出す。

使い方:
    cd test/scripts
    python python/generate_benchmarks.py

出力:
    test/benchmarks/synthetic_gold.json

対応モデル:
    OLS (nonrobust / HC1 / HAC), Logit, Probit,
    FE (固定効果), RE (変量効果),
    IV (2SLS), Tobit, Heckman, RDD
"""

from __future__ import annotations

import importlib.metadata
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from linearmodels.iv import IV2SLS
from linearmodels.panel import PanelOLS, RandomEffects
from scipy.stats import norm
from sklearn.linear_model import Lasso, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# パス設定
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent.parent
_DATA_DIR = _REPO_ROOT / "test" / "data" / "parquet"
_BENCH_DIR = _REPO_ROOT / "test" / "benchmarks"


def _out(name: str) -> Path:
    """推定方法ごとの出力ファイルパスを返す。"""
    return _BENCH_DIR / f"synthetic_{name}_gold.json"


# ---------------------------------------------------------------------------
# JSON シリアライズ補助
# ---------------------------------------------------------------------------


class _NumpyEncoder(json.JSONEncoder):
    """numpy スカラー・配列を Python ネイティブ型に変換する。"""

    def default(self, o: object) -> object:
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        return super().default(o)


def _f(x) -> float:
    """numpy スカラーを float に変換（可読性用）。"""
    return float(x)


def _params_to_dict(result, var_names: list[str]) -> dict:
    """
    statsmodels の推定結果から {変数名: 値} 形式の係数・SE・t値・p値・CI を返す。

    Returns:
        dict with keys: coefficients, std_errors, t_values, p_values, conf_int
    """
    params = result.params
    bse = result.bse
    tvalues = result.tvalues
    pvalues = result.pvalues
    ci = result.conf_int()  # DataFrame or ndarray (lower, upper)

    coef_d = {v: _f(params[i]) for i, v in enumerate(var_names)}
    se_d = {v: _f(bse[i]) for i, v in enumerate(var_names)}
    t_d = {v: _f(tvalues[i]) for i, v in enumerate(var_names)}
    p_d = {v: _f(pvalues[i]) for i, v in enumerate(var_names)}

    if hasattr(ci, "values"):
        ci_arr = ci.values  # DataFrame → ndarray
    else:
        ci_arr = ci

    ci_d = {
        v: {"lower": _f(ci_arr[i, 0]), "upper": _f(ci_arr[i, 1])}
        for i, v in enumerate(var_names)
    }

    return {
        "coefficients": coef_d,
        "std_errors": se_d,
        "t_values": t_d,
        "p_values": p_d,
        "conf_int": ci_d,
    }


def _lm_params_to_dict(result, var_names: list[str]) -> dict:
    """
    linearmodels の推定結果から係数・SE・t値・p値・CI を返す。
    linearmodels は params / std_errors / tstats / pvalues / conf_int() を持つ。
    """
    params = result.params
    se = result.std_errors
    t = result.tstats
    p = result.pvalues
    ci = result.conf_int()  # DataFrame

    coef_d = {v: _f(params[v]) for v in var_names}
    se_d = {v: _f(se[v]) for v in var_names}
    t_d = {v: _f(t[v]) for v in var_names}
    p_d = {v: _f(p[v]) for v in var_names}
    ci_d = {
        v: {"lower": _f(ci.loc[v, "lower"]), "upper": _f(ci.loc[v, "upper"])}
        for v in var_names
    }

    return {
        "coefficients": coef_d,
        "std_errors": se_d,
        "t_values": t_d,
        "p_values": p_d,
        "conf_int": ci_d,
    }


# ---------------------------------------------------------------------------
# 1. OLS (nonrobust / HC1 / HAC)
# ---------------------------------------------------------------------------


def _bench_ols(df: pd.DataFrame) -> dict:
    """
    OLS ベンチマーク。
    DGP: y_cont = 3.0 + 2.5*x1 - 1.8*x2 + 0.9*x3 + ε
    """
    y = df["y_cont"].values
    X = sm.add_constant(df[["x1", "x2", "x3"]].values)
    var_names = ["const", "x1", "x2", "x3"]
    n = len(y)

    # -- nonrobust --
    res_ols = sm.OLS(y, X).fit()
    base = _params_to_dict(res_ols, var_names)
    f_stat = res_ols.fvalue
    f_df1 = int(res_ols.df_model)
    f_df2 = int(res_ols.df_resid)

    # -- HC1 (heteroskedasticity-robust) --
    res_hc1 = sm.OLS(y, X).fit(cov_type="HC1")
    hc1 = _params_to_dict(res_hc1, var_names)

    # -- HAC (Newey-West, maxlags=1) --
    res_hac = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 1})
    hac = _params_to_dict(res_hac, var_names)

    return {
        "dep_var": "y_cont",
        "expl_vars": ["x1", "x2", "x3"],
        "n_obs": n,
        "r_squared": _f(res_ols.rsquared),
        "adj_r_squared": _f(res_ols.rsquared_adj),
        "f_test": {
            "statistic": _f(f_stat),
            "df1": f_df1,
            "df2": f_df2,
            "p_value": _f(res_ols.f_pvalue),
        },
        "nonrobust": base,
        "hc1": hc1,
        "hac_maxlags1": hac,
    }


# ---------------------------------------------------------------------------
# 2. Logit
# ---------------------------------------------------------------------------


def _bench_logit(df: pd.DataFrame) -> dict:
    """
    Logit ベンチマーク。
    DGP: y_binary ~ logistic((-0.5 + 1.2*x1 - 0.8*x2 + 0.5*x3) * 0.15)
    """
    y: np.ndarray = df["y_binary"].to_numpy(dtype=float)
    X = sm.add_constant(df[["x1", "x2", "x3"]].to_numpy(dtype=float))
    var_names = ["const", "x1", "x2", "x3"]

    res = sm.Logit(y, X).fit(disp=0, method="newton")
    base = _params_to_dict(res, var_names)

    return {
        "dep_var": "y_binary",
        "n_obs": int(res.nobs),
        "n_positive": int(np.sum(y)),
        **base,
        "pseudo_r_squared": _f(res.prsquared),
        "log_likelihood": _f(res.llf),
        "log_likelihood_null": _f(res.llnull),
        "aic": _f(res.aic),
        "bic": _f(res.bic),
        "lr_test": {
            "statistic": _f(res.llr),
            "df": int(res.df_model),
            "p_value": _f(res.llr_pvalue),
        },
    }


# ---------------------------------------------------------------------------
# 3. Probit
# ---------------------------------------------------------------------------


def _bench_probit(df: pd.DataFrame) -> dict:
    """
    Probit ベンチマーク。
    DGP: y_binary ~ Phi((-0.5 + 1.2*x1 - 0.8*x2 + 0.5*x3) * 0.15)
    """
    y: np.ndarray = df["y_binary"].to_numpy(dtype=float)
    X = sm.add_constant(df[["x1", "x2", "x3"]].to_numpy(dtype=float))
    var_names = ["const", "x1", "x2", "x3"]

    res = sm.Probit(y, X).fit(disp=0, method="newton")
    base = _params_to_dict(res, var_names)

    return {
        "dep_var": "y_binary",
        "n_obs": int(res.nobs),
        "n_positive": int(np.sum(y)),
        **base,
        "pseudo_r_squared": _f(res.prsquared),
        "log_likelihood": _f(res.llf),
        "log_likelihood_null": _f(res.llnull),
        "aic": _f(res.aic),
        "bic": _f(res.bic),
        "lr_test": {
            "statistic": _f(res.llr),
            "df": int(res.df_model),
            "p_value": _f(res.llr_pvalue),
        },
    }


# ---------------------------------------------------------------------------
# 4. Lasso (sklearn, alpha=0.1)
# ---------------------------------------------------------------------------


def _bench_lasso(df: pd.DataFrame, alpha: float = 0.1) -> dict:
    """
    Lasso ベンチマーク（StandardScaler → Lasso）。
    SE なし（ペナルティ付きのため）。
    """
    y = df["y_cont"].values
    X_raw = df[["x1", "x2", "x3"]].values
    var_names = ["x1", "x2", "x3"]

    pipe = Pipeline(
        [
            ("scaler", StandardScaler(with_std=True)),
            ("lasso", Lasso(alpha=alpha, max_iter=10000)),
        ]
    )
    pipe.fit(X_raw, y)

    lasso_model = pipe.named_steps["lasso"]
    scaler = pipe.named_steps["scaler"]

    coef_scaled = {v: _f(c) for v, c in zip(var_names, lasso_model.coef_)}

    # 元スケール係数に逆変換
    scale = scaler.scale_
    mean = scaler.mean_
    coef_orig = {v: _f(c / s) for v, c, s in zip(var_names, lasso_model.coef_, scale)}
    intercept_orig = _f(
        lasso_model.intercept_ - np.sum(lasso_model.coef_ * mean / scale)
    )

    return {
        "dep_var": "y_cont",
        "alpha": alpha,
        "n_obs": len(y),
        "coef_scaled": coef_scaled,
        "coef_orig": {"const": intercept_orig, **coef_orig},
        "note": (
            "coef_scaled は StandardScaler(ddof=0) → Lasso(alpha) の coef_。"
            " coef_orig は元スケールに逆変換した係数。"
        ),
    }


# ---------------------------------------------------------------------------
# 5. Ridge (sklearn, alpha=0.5)
# ---------------------------------------------------------------------------


def _bench_ridge(df: pd.DataFrame, alpha: float = 0.5) -> dict:
    """
    Ridge ベンチマーク（StandardScaler → Ridge）。
    SE なし（ペナルティ付きのため）。
    """
    y = df["y_cont"].values
    X_raw = df[["x1", "x2", "x3"]].values
    var_names = ["x1", "x2", "x3"]

    pipe = Pipeline(
        [("scaler", StandardScaler(with_std=True)), ("ridge", Ridge(alpha=alpha))]
    )
    pipe.fit(X_raw, y)

    ridge_model = pipe.named_steps["ridge"]
    scaler = pipe.named_steps["scaler"]

    coef_scaled = {v: _f(c) for v, c in zip(var_names, ridge_model.coef_)}

    scale = scaler.scale_
    mean = scaler.mean_
    coef_orig = {v: _f(c / s) for v, c, s in zip(var_names, ridge_model.coef_, scale)}
    intercept_orig = _f(
        ridge_model.intercept_ - np.sum(ridge_model.coef_ * mean / scale)
    )

    return {
        "dep_var": "y_cont",
        "alpha": alpha,
        "n_obs": len(y),
        "coef_scaled": coef_scaled,
        "coef_orig": {"const": intercept_orig, **coef_orig},
        "note": (
            "coef_scaled は StandardScaler(ddof=0) → Ridge(alpha) の coef_。"
            " coef_orig は元スケールに逆変換した係数。"
        ),
    }


# ---------------------------------------------------------------------------
# 6. 固定効果 (FE)
# ---------------------------------------------------------------------------


def _bench_fe(df: pd.DataFrame) -> dict:
    """
    固定効果モデルベンチマーク (linearmodels PanelOLS)。
    DGP: y = 1.0 + 3.0*x1 - 2.0*x2 + alpha_i + ε
    """
    df_indexed = df.set_index(["entity_id", "time_id"])
    var_names = ["x1", "x2"]

    # nonrobust (unadjusted)
    res = PanelOLS(df_indexed["y"], df_indexed[["x1", "x2"]], entity_effects=True).fit(
        cov_type="unadjusted"
    )
    base = _lm_params_to_dict(res, var_names)

    # clustered SE (entity)
    res_cl = PanelOLS(
        df_indexed["y"], df_indexed[["x1", "x2"]], entity_effects=True
    ).fit(
        cov_type="clustered",
        cluster_entity=True,
    )
    cl = _lm_params_to_dict(res_cl, var_names)

    return {
        "n_obs": int(res.nobs),
        "n_entities": int(df["entity_id"].nunique()),
        "n_periods": int(df["time_id"].nunique()),
        "r_squared_within": _f(res.rsquared),
        "r_squared_between": _f(res.rsquared_between),
        "r_squared_overall": _f(res.rsquared_overall),
        "f_test": {
            "statistic": _f(res.f_statistic.stat),
            "p_value": _f(res.f_statistic.pval),
        },
        "nonrobust": base,
        "clustered_entity": cl,
    }


# ---------------------------------------------------------------------------
# 7. 変量効果 (RE)
# ---------------------------------------------------------------------------


def _bench_re(df: pd.DataFrame) -> dict:
    """
    変量効果モデルベンチマーク (linearmodels RandomEffects)。
    """
    df_indexed = df.set_index(["entity_id", "time_id"])
    X = sm.add_constant(df_indexed[["x1", "x2"]])
    var_names = ["const", "x1", "x2"]

    res = RandomEffects(df_indexed["y"], X).fit(cov_type="unadjusted")
    base = _lm_params_to_dict(res, var_names)

    return {
        "n_obs": int(res.nobs),
        "r_squared_within": _f(res.rsquared),
        "r_squared_between": _f(res.rsquared_between),
        "r_squared_overall": _f(res.rsquared_overall),
        "theta": _f(res.theta.iloc[0, 0]),
        "nonrobust": base,
    }


# ---------------------------------------------------------------------------
# 8. IV (2SLS)
# ---------------------------------------------------------------------------


def _bench_iv(df: pd.DataFrame) -> dict:
    """
    IV (2SLS) ベンチマーク (linearmodels IV2SLS)。
    DGP: y = 2.0 + 1.5*x_exog + 3.0*x_endog + u
    Instruments: z1, z2  for x_endog
    """
    y = df["y"]
    X_exog = sm.add_constant(df[["x_exog"]])
    X_endog = df[["x_endog"]]
    Z = df[["z1", "z2"]]
    var_names = ["const", "x_exog", "x_endog"]

    # nonrobust (unadjusted)
    res = IV2SLS(y, X_exog, X_endog, Z).fit(cov_type="unadjusted")
    base = _lm_params_to_dict(res, var_names)

    # HC1
    res_hc1 = IV2SLS(y, X_exog, X_endog, Z).fit(cov_type="robust")
    hc1 = _lm_params_to_dict(res_hc1, var_names)

    # First-stage statistics (F for weak instruments)
    first_stage = res.first_stage  # type: ignore[attr-defined]
    fs_res = first_stage.diagnostics

    return {
        "dep_var": "y",
        "exog_vars": ["x_exog"],
        "endog_vars": ["x_endog"],
        "instruments": ["z1", "z2"],
        "n_obs": int(res.nobs),
        "r_squared": _f(res.rsquared),
        "nonrobust": base,
        "hc1": hc1,
        "first_stage": {
            "partial_r_squared": _f(fs_res.loc["x_endog", "partial.rsquared"]),
            "f_statistic": _f(fs_res.loc["x_endog", "f.stat"]),
            "f_p_value": _f(fs_res.loc["x_endog", "f.pval"]),
        },
    }


# ---------------------------------------------------------------------------
# 9. Tobit (py4etrics)
# ---------------------------------------------------------------------------


def _bench_tobit(df: pd.DataFrame) -> dict:
    """
    Tobit ベンチマーク（左側打ち切り at 0）(py4etrics)。
    DGP: y_latent = 2.0 + 2.0*x1 + 1.5*x2 + ε, y = max(0, y_latent)
    """
    from py4etrics.tobit import Tobit  # noqa: PLC0415

    y: np.ndarray = df["y"].to_numpy(dtype=float)
    X = sm.add_constant(df[["x1", "x2"]].to_numpy(dtype=float))
    var_names = ["const", "x1", "x2"]

    censoring_ratio = _f(float((y == 0.0).mean()))
    n = len(y)

    cens = np.zeros(n)
    cens[y <= 0.0] = -1  # 左側打ち切りを -1 でマーク

    res = Tobit(y, X, cens=cens, left=0.0).fit(disp=False)
    params = res.params  # [beta..., log_sigma]
    bse = res.bse

    # py4etrics は params[-1] が log_sigma
    n_coef = len(var_names)
    coef_d = {v: _f(params[i]) for i, v in enumerate(var_names)}
    se_d = {v: _f(bse[i]) for i, v in enumerate(var_names)}
    t_d = {v: _f(params[i] / bse[i]) for i, v in enumerate(var_names)}
    sigma = _f(np.exp(params[n_coef]))

    # CI: 正規近似
    z_crit = 1.959963985  # qnorm(0.975)
    ci_d = {
        v: {
            "lower": _f(params[i] - z_crit * bse[i]),
            "upper": _f(params[i] + z_crit * bse[i]),
        }
        for i, v in enumerate(var_names)
    }

    return {
        "dep_var": "y",
        "left_censoring_limit": 0.0,
        "n_obs": n,
        "censoring_ratio": censoring_ratio,
        "sigma": sigma,
        "log_likelihood": _f(res.llf),
        "aic": _f(res.aic),
        "bic": _f(res.bic),
        "coefficients": coef_d,
        "std_errors": se_d,
        "t_values": t_d,
        "conf_int": ci_d,
    }


# ---------------------------------------------------------------------------
# 10. Heckman 2段階推定
# ---------------------------------------------------------------------------


def _bench_heckman(df: pd.DataFrame) -> dict:
    """
    Heckman 2段階推定ベンチマーク（statsmodels 手動実装）。

    Step 1: Probit  employed ~ const + educ + exp + kids  (全サンプル)
    Step 2: OLS     wage ~ const + educ + exp + IMR        (employed=1 のみ)

    DGP 真のパラメータ:
      観測方程式: const=1.5, educ=0.8, exp=0.4
      選択方程式: const=-5.0, educ=0.4, exp=0.3, kids=-0.7
    """
    # ---- Step 1: Probit (全サンプル) ----
    df_all = df.dropna(subset=["educ", "exp", "kids", "employed"])
    X_sel = sm.add_constant(df_all[["educ", "exp", "kids"]].values)
    y_sel = df_all["employed"].values
    sel_var_names = ["const", "educ", "exp", "kids"]

    res_probit = sm.Probit(y_sel, X_sel).fit(disp=0, method="newton")
    probit_params = _params_to_dict(res_probit, sel_var_names)

    # IMR: φ(xb) / Φ(xb)  (選択 = 1 のサンプル向け)
    xb_all = res_probit.fittedvalues  # linear predictor (全サンプル)
    phi_all = norm.pdf(xb_all)
    Phi_all = norm.cdf(xb_all)
    imr_all = phi_all / np.where(Phi_all > 1e-16, Phi_all, 1e-16)
    df_all = df_all.copy()
    df_all["_imr"] = imr_all

    # ---- Step 2: OLS (employed=1 のみ) ----
    df_sel = df_all[df_all["employed"] == 1.0].dropna(subset=["wage"])
    X_out = sm.add_constant(df_sel[["educ", "exp", "_imr"]].values)
    y_out = df_sel["wage"].values
    out_var_names = ["const", "educ", "exp", "imr"]

    res_ols2 = sm.OLS(y_out, X_out).fit()
    ols2_params = _params_to_dict(res_ols2, out_var_names)

    imr_coef = _f(res_ols2.params[3])
    imr_se = _f(res_ols2.bse[3])
    imr_t = _f(res_ols2.tvalues[3])
    imr_p = _f(res_ols2.pvalues[3])

    return {
        "n_total": len(df_all),
        "n_selected": int((df_all["employed"] == 1.0).sum()),
        "selection_ratio": _f((df_all["employed"] == 1.0).mean()),
        "step1_probit": {
            "dep_var": "employed",
            "sel_vars": ["educ", "exp", "kids"],
            "n_obs": int(res_probit.nobs),
            **probit_params,
            "pseudo_r_squared": _f(res_probit.prsquared),
            "log_likelihood": _f(res_probit.llf),
        },
        "step2_ols": {
            "dep_var": "wage",
            "outcome_vars": ["educ", "exp"],
            "n_obs": int(res_ols2.nobs),
            **ols2_params,
            "r_squared": _f(res_ols2.rsquared),
            "adj_r_squared": _f(res_ols2.rsquared_adj),
        },
        "imr": {
            "coefficient": imr_coef,
            "std_error": imr_se,
            "t_value": imr_t,
            "p_value": imr_p,
        },
    }


# ---------------------------------------------------------------------------
# 11. RDD (rdrobust)
# ---------------------------------------------------------------------------


def _bench_rdd(df: pd.DataFrame) -> dict:
    """
    RDD ベンチマーク (rdrobust)。
    DGP: y = 2.0 + 1.5*running_var + 5.0*treat + ε  (treat = 1[x>=0])
    cutoff = 0.0, 真の処置効果 = 5.0
    """
    from rdrobust import rdrobust  # noqa: PLC0415

    y = df["y"].values
    x = df["running_var"].values
    cutoff = 0.0

    res = rdrobust(y, x, c=cutoff)

    # coef[0]: conventional, coef[1]: bias-corrected, coef[2]: robust
    coef_conv = _f(res.coef.iloc[0, 0])
    coef_bc = _f(res.coef.iloc[1, 0])
    coef_rob = _f(res.coef.iloc[2, 0])

    se_conv = _f(res.se.iloc[0, 0])
    se_bc = _f(res.se.iloc[1, 0])
    se_rob = _f(res.se.iloc[2, 0])

    t_conv = _f(res.t.iloc[0, 0])
    t_bc = _f(res.t.iloc[1, 0])
    t_rob = _f(res.t.iloc[2, 0])

    pv_conv = _f(res.pv.iloc[0, 0])
    pv_bc = _f(res.pv.iloc[1, 0])
    pv_rob = _f(res.pv.iloc[2, 0])

    ci_conv = [_f(res.ci.iloc[0, 0]), _f(res.ci.iloc[0, 1])]
    ci_bc = [_f(res.ci.iloc[1, 0]), _f(res.ci.iloc[1, 1])]
    ci_rob = [_f(res.ci.iloc[2, 0]), _f(res.ci.iloc[2, 1])]

    # 帯域幅 (DataFrame: index = [h, b], cols = [left, right])
    bw_left = _f(res.bws.loc["h", "left"])
    bw_right = _f(res.bws.loc["h", "right"])
    bw_bias_left = _f(res.bws.loc["b", "left"])
    bw_bias_right = _f(res.bws.loc["b", "right"])

    n_left = int(res.N_h[0])
    n_right = int(res.N_h[1])

    return {
        "dep_var": "y",
        "running_var": "running_var",
        "cutoff": cutoff,
        "n_total": len(y),
        "n_left": n_left,
        "n_right": n_right,
        "bandwidth": {
            "bw_left": bw_left,
            "bw_right": bw_right,
            "bw_bias_left": bw_bias_left,
            "bw_bias_right": bw_bias_right,
        },
        "conventional": {
            "coef": coef_conv,
            "std_err": se_conv,
            "t_stat": t_conv,
            "p_value": pv_conv,
            "ci_lower": ci_conv[0],
            "ci_upper": ci_conv[1],
        },
        "bias_corrected": {
            "coef": coef_bc,
            "std_err": se_bc,
            "t_stat": t_bc,
            "p_value": pv_bc,
            "ci_lower": ci_bc[0],
            "ci_upper": ci_bc[1],
        },
        "robust": {
            "coef": coef_rob,
            "std_err": se_rob,
            "t_stat": t_rob,
            "p_value": pv_rob,
            "ci_lower": ci_rob[0],
            "ci_upper": ci_rob[1],
        },
    }


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------


def _get_version(package: str) -> str:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def _write(name: str, data: dict, meta: dict) -> None:
    """推定結果を {name} 専用の JSON ファイルへ書き出す。"""
    out = _out(name)
    payload = {"meta": {**meta, "model": name}, "estimates": data}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, cls=_NumpyEncoder)
    print(f"    -> {out.name}")


def main() -> None:
    _BENCH_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading synthetic data...")
    df_ols = pd.read_parquet(_DATA_DIR / "synthetic_ols.parquet")
    df_panel = pd.read_parquet(_DATA_DIR / "synthetic_panel.parquet")
    df_iv = pd.read_parquet(_DATA_DIR / "synthetic_iv.parquet")
    df_tobit = pd.read_parquet(_DATA_DIR / "synthetic_tobit.parquet")
    df_heckman = pd.read_parquet(_DATA_DIR / "synthetic_heckman.parquet")
    df_rdd = pd.read_parquet(_DATA_DIR / "synthetic_rdd.parquet")

    # 共通メタデータ（各ファイルに埋め込む）
    meta: dict = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "statsmodels_version": _get_version("statsmodels"),
        "linearmodels_version": _get_version("linearmodels"),
        "py4etrics_version": _get_version("py4etrics"),
        "scikit_learn_version": _get_version("scikit-learn"),
        "rdrobust_version": _get_version("rdrobust"),
        "seed": 2024,
        "tolerance_guide": {
            "ols_coef": "atol=1e-12 (nonrobust)",
            "ols_se_hc1": "atol=1e-12",
            "logit_probit_coef": "atol=1e-8 (MLE 収束差)",
            "fe_re_coef": "atol=1e-12",
            "iv_coef": "atol=1e-12",
            "tobit_coef": "atol=1e-6 (py4etrics MLE)",
            "heckman_coef": "atol=1e-8 (2段階 OLS/Probit)",
            "rdd_coef": "atol=1e-4 (rdrobust ローカル多項式)",
            "lasso_ridge_coef_scaled": "atol=1e-8 (sklearn Pipeline)",
        },
    }

    print("Running models...")

    print("  [1/11] OLS...")
    ols = _bench_ols(df_ols)
    _write("ols", ols, {**meta, "data_file": "synthetic_ols.parquet"})

    print("  [2/11] Logit...")
    logit = _bench_logit(df_ols)
    _write("logit", logit, {**meta, "data_file": "synthetic_ols.parquet"})

    print("  [3/11] Probit...")
    probit = _bench_probit(df_ols)
    _write("probit", probit, {**meta, "data_file": "synthetic_ols.parquet"})

    print("  [4/11] Lasso (alpha=0.1)...")
    lasso = _bench_lasso(df_ols, alpha=0.1)
    _write("lasso", lasso, {**meta, "data_file": "synthetic_ols.parquet"})

    print("  [5/11] Ridge (alpha=0.5)...")
    ridge = _bench_ridge(df_ols, alpha=0.5)
    _write("ridge", ridge, {**meta, "data_file": "synthetic_ols.parquet"})

    print("  [6/11] Fixed Effects (FE)...")
    fe = _bench_fe(df_panel)
    _write("fe", fe, {**meta, "data_file": "synthetic_panel.parquet"})

    print("  [7/11] Random Effects (RE)...")
    re = _bench_re(df_panel)
    _write("re", re, {**meta, "data_file": "synthetic_panel.parquet"})

    print("  [8/11] IV (2SLS)...")
    iv = _bench_iv(df_iv)
    _write("iv", iv, {**meta, "data_file": "synthetic_iv.parquet"})

    print("  [9/11] Tobit...")
    tobit = _bench_tobit(df_tobit)
    _write("tobit", tobit, {**meta, "data_file": "synthetic_tobit.parquet"})

    print("  [10/11] Heckman 2-step...")
    heckman = _bench_heckman(df_heckman)
    _write("heckman", heckman, {**meta, "data_file": "synthetic_heckman.parquet"})

    print("  [11/11] RDD (rdrobust)...")
    rdd = _bench_rdd(df_rdd)
    _write("rdd", rdd, {**meta, "data_file": "synthetic_rdd.parquet"})

    print("\nDone.")
    print()

    # --- サマリー表示 ---
    print("=== Benchmark Summary ===")
    ols_coef = ols["nonrobust"]["coefficients"]
    print("OLS  (true: const=3.0, x1=2.5, x2=-1.8, x3=0.9)")
    print(
        f"  const={ols_coef['const']:.4f}, x1={ols_coef['x1']:.4f}, "
        f"x2={ols_coef['x2']:.4f}, x3={ols_coef['x3']:.4f}"
    )

    fe_coef = fe["nonrobust"]["coefficients"]
    print("FE   (true: x1=3.0, x2=-2.0)")
    print(f"  x1={fe_coef['x1']:.4f}, x2={fe_coef['x2']:.4f}")

    iv_coef = iv["nonrobust"]["coefficients"]
    print("IV   (true: const=2.0, x_exog=1.5, x_endog=3.0)")
    print(
        f"  const={iv_coef['const']:.4f}, x_exog={iv_coef['x_exog']:.4f}, "
        f"x_endog={iv_coef['x_endog']:.4f}"
    )

    rdd_conv = rdd["conventional"]
    print("RDD  (true effect=5.0)")
    print(
        f"  conventional={rdd_conv['coef']:.4f}, "
        f"bias_corrected={rdd['bias_corrected']['coef']:.4f}"
    )


if __name__ == "__main__":
    main()
