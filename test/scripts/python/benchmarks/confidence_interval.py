import numpy as np
import pandas as pd
import scipy.stats as spstats
from statsmodels.stats.proportion import proportion_confint

from benchmarks.helpers import f


def bench_confidence_interval(df: pd.DataFrame) -> dict:
    normal = df["normal_col"].to_numpy(dtype=float)
    binary = df["binary_col"].to_numpy(dtype=float)

    mean_level = 0.95
    mean_interval = spstats.t.interval(
        mean_level,
        df=len(normal) - 1,
        loc=float(np.mean(normal)),
        scale=float(spstats.sem(normal)),
    )

    median_level = 0.90
    median_stat = float(np.median(normal))
    median_rng = np.random.default_rng(42)
    median_boot = []
    for _index in range(10000):
        bootstrap_sample = median_rng.choice(normal, size=len(normal), replace=True)
        median_boot.append(np.median(bootstrap_sample))
    median_alpha = 1 - median_level
    median_lower = float(np.percentile(median_boot, (median_alpha / 2) * 100))
    median_upper = float(np.percentile(median_boot, (1 - median_alpha / 2) * 100))

    prop_level = 0.95
    prop_successes = int(np.sum(binary))
    prop_interval = proportion_confint(
        prop_successes,
        len(binary),
        alpha=1 - prop_level,
        method="wilson",
    )

    variance_level = 0.95
    sample_var = float(np.var(normal, ddof=1))
    alpha = 1 - variance_level
    chi2_lo = spstats.chi2.ppf(alpha / 2, df=len(normal) - 1)
    chi2_hi = spstats.chi2.ppf(1 - alpha / 2, df=len(normal) - 1)
    var_lower = (len(normal) - 1) * sample_var / chi2_hi
    var_upper = (len(normal) - 1) * sample_var / chi2_lo
    std_lower = float(np.sqrt(var_lower))
    std_upper = float(np.sqrt(var_upper))

    cases = [
        {
            "case_id": "ci_mean_95",
            "table_name": "synthetic_statistics_ci",
            "column_name": "normal_col",
            "statistic_type": "mean",
            "confidence_level": mean_level,
            "n_obs": len(normal),
            "statistic": {"type": "mean", "value": f(np.mean(normal))},
            "confidence_interval": {
                "lower": f(mean_interval[0]),
                "upper": f(mean_interval[1]),
            },
            "method": "t_interval",
            "notes": "scipy.stats.t.interval with sample sem",
        },
        {
            "case_id": "ci_median_90",
            "table_name": "synthetic_statistics_ci",
            "column_name": "normal_col",
            "statistic_type": "median",
            "confidence_level": median_level,
            "n_obs": len(normal),
            "statistic": {"type": "median", "value": median_stat},
            "confidence_interval": {
                "lower": f(median_lower),
                "upper": f(median_upper),
            },
            "method": "bootstrap_percentile",
            "notes": "manual percentile bootstrap, seed=42, n_resamples=10000",
        },
        {
            "case_id": "ci_proportion_95",
            "table_name": "synthetic_statistics_ci",
            "column_name": "binary_col",
            "statistic_type": "proportion",
            "confidence_level": prop_level,
            "n_obs": len(binary),
            "statistic": {
                "type": "proportion",
                "value": f(np.mean(binary)),
            },
            "confidence_interval": {
                "lower": f(prop_interval[0]),
                "upper": f(prop_interval[1]),
            },
            "method": "wilson_score",
            "notes": "statsmodels.stats.proportion.proportion_confint(method='wilson')",
        },
        {
            "case_id": "ci_variance_95",
            "table_name": "synthetic_statistics_ci",
            "column_name": "normal_col",
            "statistic_type": "variance",
            "confidence_level": variance_level,
            "n_obs": len(normal),
            "statistic": {"type": "variance", "value": sample_var},
            "confidence_interval": {
                "lower": f(var_lower),
                "upper": f(var_upper),
            },
            "method": "chi_square_variance",
            "notes": "sample variance with ddof=1",
        },
        {
            "case_id": "ci_std_95",
            "table_name": "synthetic_statistics_ci",
            "column_name": "normal_col",
            "statistic_type": "standard_deviation",
            "confidence_level": variance_level,
            "n_obs": len(normal),
            "statistic": {
                "type": "standard_deviation",
                "value": f(np.sqrt(sample_var)),
            },
            "confidence_interval": {
                "lower": f(std_lower),
                "upper": f(std_upper),
            },
            "method": "chi_square_std",
            "notes": "square root of variance confidence interval",
        },
    ]

    return {"cases": cases}
