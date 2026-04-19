"""Python gold benchmark 生成の入口スクリプト。"""

from __future__ import annotations

import pandas as pd
from benchmarks.fe import bench_fe
from benchmarks.fgls_ar1 import bench_fgls_ar1
from benchmarks.fgls_heteroskedastic import bench_fgls_heteroskedastic
from benchmarks.gls import bench_gls
from benchmarks.heckman import bench_heckman
from benchmarks.helpers import DATA_DIR, build_meta, write_benchmark
from benchmarks.iv import bench_iv
from benchmarks.lasso import bench_lasso
from benchmarks.logit import bench_logit
from benchmarks.ols import bench_ols
from benchmarks.probit import bench_probit
from benchmarks.rdd import bench_rdd
from benchmarks.re import bench_re
from benchmarks.ridge import bench_ridge
from benchmarks.tobit import bench_tobit
from benchmarks.wls import bench_wls


def main() -> None:
    print("Loading synthetic data...")
    df_ols = pd.read_parquet(DATA_DIR / "synthetic_ols.parquet")
    df_panel = pd.read_parquet(DATA_DIR / "synthetic_panel.parquet")
    df_iv = pd.read_parquet(DATA_DIR / "synthetic_iv.parquet")
    df_wls = pd.read_parquet(DATA_DIR / "synthetic_wls.parquet")
    df_gls = pd.read_parquet(DATA_DIR / "synthetic_gls_data.parquet")
    df_gls_sigma = pd.read_parquet(DATA_DIR / "synthetic_gls_sigma.parquet")
    df_fgls_hetero = pd.read_parquet(DATA_DIR / "synthetic_fgls_hetero.parquet")
    df_fgls_ar1 = pd.read_parquet(DATA_DIR / "synthetic_fgls_ar1.parquet")
    df_tobit = pd.read_parquet(DATA_DIR / "synthetic_tobit.parquet")
    df_heckman = pd.read_parquet(DATA_DIR / "synthetic_heckman.parquet")
    df_rdd = pd.read_parquet(DATA_DIR / "synthetic_rdd.parquet")

    print("Running models...")

    print("  [1/15] OLS...")
    ols = bench_ols(df_ols)
    write_benchmark(
        "ols",
        ols,
        build_meta(
            "ols",
            "synthetic_ols.parquet",
            ["statsmodels"],
            ["ols_coef", "ols_se_hc1"],
        ),
    )

    print("  [2/15] Logit...")
    logit = bench_logit(df_ols)
    write_benchmark(
        "logit",
        logit,
        build_meta(
            "logit",
            "synthetic_ols.parquet",
            ["statsmodels"],
            ["logit_probit_coef"],
        ),
    )

    print("  [3/15] Probit...")
    probit = bench_probit(df_ols)
    write_benchmark(
        "probit",
        probit,
        build_meta(
            "probit",
            "synthetic_ols.parquet",
            ["statsmodels"],
            ["logit_probit_coef"],
        ),
    )

    print("  [4/15] Lasso...")
    lasso = bench_lasso(df_ols, alpha=0.1)
    write_benchmark(
        "lasso",
        lasso,
        build_meta(
            "lasso",
            "synthetic_ols.parquet",
            ["scikit-learn"],
            ["lasso_ridge_coef_scaled"],
            standardization="StandardScaler(ddof=0)",
        ),
    )

    print("  [5/15] Ridge...")
    ridge = bench_ridge(df_ols, alpha=0.5)
    write_benchmark(
        "ridge",
        ridge,
        build_meta(
            "ridge",
            "synthetic_ols.parquet",
            ["scikit-learn"],
            ["lasso_ridge_coef_scaled"],
            standardization="StandardScaler(ddof=0)",
        ),
    )

    print("  [6/15] Fixed Effects (FE)...")
    fe = bench_fe(df_panel)
    write_benchmark(
        "fe",
        fe,
        build_meta(
            "fe",
            "synthetic_panel.parquet",
            ["linearmodels"],
            ["fe_re_coef"],
        ),
    )

    print("  [7/15] Random Effects (RE)...")
    re = bench_re(df_panel)
    write_benchmark(
        "re",
        re,
        build_meta(
            "re",
            "synthetic_panel.parquet",
            ["linearmodels", "statsmodels"],
            ["fe_re_coef"],
        ),
    )

    print("  [8/15] IV (2SLS)...")
    iv = bench_iv(df_iv)
    write_benchmark(
        "iv",
        iv,
        build_meta(
            "iv",
            "synthetic_iv.parquet",
            ["linearmodels", "statsmodels"],
            ["iv_coef"],
        ),
    )

    print("  [9/15] WLS...")
    wls = bench_wls(df_wls)
    write_benchmark(
        "wls",
        wls,
        build_meta(
            "wls",
            "synthetic_wls.parquet",
            ["statsmodels"],
            ["wls_coef"],
            weights_column="weights",
            weights_definition="inverse variance (1 / sigma2)",
            missing_value_handling="no missing values in synthetic_wls",
        ),
    )

    print("  [10/15] GLS...")
    gls = bench_gls(df_gls, df_gls_sigma)
    write_benchmark(
        "gls",
        gls,
        build_meta(
            "gls",
            "synthetic_gls_data.parquet",
            ["statsmodels"],
            ["gls_coef"],
            sigma_file="synthetic_gls_sigma.parquet",
            missing_value_handling="complete-case only; no missing values in synthetic_gls_data",
        ),
    )

    print("  [11/15] FGLS heteroskedastic...")
    fgls_heteroskedastic = bench_fgls_heteroskedastic(df_fgls_hetero)
    write_benchmark(
        "fgls_heteroskedastic",
        fgls_heteroskedastic,
        build_meta(
            "fgls_heteroskedastic",
            "synthetic_fgls_hetero.parquet",
            ["statsmodels"],
            ["fgls_heteroskedastic_coef"],
            fgls_method="heteroskedastic",
            missing_value_handling="no missing values in synthetic_fgls_hetero",
        ),
    )

    print("  [12/15] FGLS AR(1)...")
    fgls_ar1 = bench_fgls_ar1(df_fgls_ar1, max_iter=10)
    write_benchmark(
        "fgls_ar1",
        fgls_ar1,
        build_meta(
            "fgls_ar1",
            "synthetic_fgls_ar1.parquet",
            ["statsmodels"],
            ["fgls_ar1_coef"],
            fgls_method="ar1",
            max_iter=10,
            missing_value_handling="no missing values in synthetic_fgls_ar1",
        ),
    )

    print("  [13/15] Tobit...")
    tobit = bench_tobit(df_tobit)
    write_benchmark(
        "tobit",
        tobit,
        build_meta(
            "tobit",
            "synthetic_tobit.parquet",
            ["statsmodels", "py4etrics"],
            ["tobit_coef"],
        ),
    )

    print("  [14/15] Heckman 2-step...")
    heckman = bench_heckman(df_heckman)
    write_benchmark(
        "heckman",
        heckman,
        build_meta(
            "heckman",
            "synthetic_heckman.parquet",
            ["statsmodels", "scipy"],
            ["heckman_coef"],
            missing_value_handling="wage is NaN for unselected observations by design",
        ),
    )

    print("  [15/15] RDD (rdrobust)...")
    rdd = bench_rdd(df_rdd)
    write_benchmark(
        "rdd",
        rdd,
        build_meta(
            "rdd",
            "synthetic_rdd.parquet",
            ["rdrobust"],
            ["rdd_coef"],
        ),
    )

    print("\nDone.")


if __name__ == "__main__":
    main()
