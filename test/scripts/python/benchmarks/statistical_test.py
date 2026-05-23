from typing import Any

import numpy as np
import pandas as pd
import scipy.stats as spstats
from statsmodels.stats.weightstats import ztest as sm_ztest

from benchmarks.helpers import f


def _group(df: pd.DataFrame, table_name: str) -> np.ndarray:
    return df.loc[df["table_name"] == table_name, "value"].to_numpy(dtype=float)


def _sample_summary(values: np.ndarray) -> dict:
    return {
        "n": int(len(values)),
        "mean": f(np.mean(values)),
        "variance": f(np.var(values, ddof=1)),
    }


def _cohen_d_1samp(x: np.ndarray, mu: float) -> float:
    return float(abs(np.mean(x) - mu) / np.std(x, ddof=1))


def _cohen_d_2samp(x: np.ndarray, y: np.ndarray, equal_var: bool) -> float:
    n1, n2 = len(x), len(y)
    s1 = float(np.std(x, ddof=1))
    s2 = float(np.std(y, ddof=1))
    if equal_var:
        pooled = np.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2))
    else:
        pooled = np.sqrt((s1**2 + s2**2) / 2)
    return float(abs(np.mean(x) - np.mean(y)) / pooled)


def _cohen_d_paired(x: np.ndarray, y: np.ndarray) -> float:
    diff = x - y
    return float(abs(np.mean(diff)) / np.std(diff, ddof=1))


def bench_statistical_test(df: pd.DataFrame) -> dict:
    group_a = _group(df, "StatTestTableA")
    group_b = _group(df, "StatTestTableB")
    group_c = _group(df, "StatTestTableC")

    t1: Any = spstats.ttest_1samp(group_a, popmean=50.0)
    t1_ci = spstats.ttest_1samp(
        group_a,
        popmean=50.0,
        alternative="two-sided",
    ).confidence_interval(confidence_level=0.95)

    t2: Any = spstats.ttest_ind(group_a, group_b, equal_var=True)
    t2_ci = t2.confidence_interval(confidence_level=0.95)

    tw: Any = spstats.ttest_ind(group_a, group_b, equal_var=False)
    tw_ci = tw.confidence_interval(confidence_level=0.95)

    tp: Any = spstats.ttest_rel(group_a, group_b, alternative="two-sided")
    tp_ci = tp.confidence_interval(confidence_level=0.95)

    z1_stat, z1_p = sm_ztest(group_a, value=50, alternative="two-sided")
    z1_center = float(np.mean(group_a))
    z1_se = float(np.std(group_a, ddof=1) / np.sqrt(len(group_a)))
    z_crit = float(spstats.norm.ppf(0.975))

    z2_stat, z2_p = sm_ztest(group_a, group_b, value=0, alternative="two-sided")
    z2_center = float(np.mean(group_a) - np.mean(group_b))
    z2_se = float(
        np.sqrt(
            np.var(group_a, ddof=1) / len(group_a)
            + np.var(group_b, ddof=1) / len(group_b)
        )
    )

    var_a = float(np.var(group_a, ddof=1))
    var_b = float(np.var(group_b, ddof=1))
    f_stat = var_a / var_b
    f_p = 2.0 * min(
        float(spstats.f.cdf(f_stat, len(group_a) - 1, len(group_b) - 1)),
        float(spstats.f.sf(f_stat, len(group_a) - 1, len(group_b) - 1)),
    )

    anova: Any = spstats.f_oneway(group_a, group_b, group_c)
    all_data = np.concatenate([group_a, group_b, group_c])
    grand_mean = float(np.mean(all_data))
    ss_between = float(
        sum(
            len(group) * (float(np.mean(group)) - grand_mean) ** 2
            for group in [group_a, group_b, group_c]
        )
    )
    ss_total = float(np.sum((all_data - grand_mean) ** 2))
    eta_sq = ss_between / ss_total

    cases = [
        {
            "case_id": "ttest_1sample_mu50",
            "test_type": "t-test",
            "sample_tables": [{"table_name": "StatTestTableA", "column_name": "value"}],
            "options": {"alternative": "two-sided", "mu": 50.0},
            "statistic": f(t1.statistic),
            "p_value": f(t1.pvalue),
            "df": f(len(group_a) - 1),
            "df2": None,
            "confidence_interval": {"lower": f(t1_ci.low), "upper": f(t1_ci.high)},
            "effect_size": f(_cohen_d_1samp(group_a, 50.0)),
            "sample_summary": {"StatTestTableA": _sample_summary(group_a)},
        },
        {
            "case_id": "ttest_2sample_equal_var",
            "test_type": "t-test",
            "sample_tables": [
                {"table_name": "StatTestTableA", "column_name": "value"},
                {"table_name": "StatTestTableB", "column_name": "value"},
            ],
            "options": {"equal_var": True},
            "statistic": f(t2.statistic),
            "p_value": f(t2.pvalue),
            "df": f(len(group_a) + len(group_b) - 2),
            "df2": None,
            "confidence_interval": {"lower": f(t2_ci.low), "upper": f(t2_ci.high)},
            "effect_size": f(_cohen_d_2samp(group_a, group_b, True)),
            "sample_summary": {
                "StatTestTableA": _sample_summary(group_a),
                "StatTestTableB": _sample_summary(group_b),
            },
        },
        {
            "case_id": "ttest_welch",
            "test_type": "t-test",
            "sample_tables": [
                {"table_name": "StatTestTableA", "column_name": "value"},
                {"table_name": "StatTestTableB", "column_name": "value"},
            ],
            "options": {"equalVar": False},
            "statistic": f(tw.statistic),
            "p_value": f(tw.pvalue),
            "df": f(tw.df),
            "df2": None,
            "confidence_interval": {"lower": f(tw_ci.low), "upper": f(tw_ci.high)},
            "effect_size": f(_cohen_d_2samp(group_a, group_b, False)),
            "sample_summary": {
                "StatTestTableA": _sample_summary(group_a),
                "StatTestTableB": _sample_summary(group_b),
            },
        },
        {
            "case_id": "ttest_paired",
            "test_type": "t-test",
            "sample_tables": [
                {"table_name": "StatTestTableA", "column_name": "value"},
                {"table_name": "StatTestTableB", "column_name": "value"},
            ],
            "options": {"paired": True},
            "statistic": f(tp.statistic),
            "p_value": f(tp.pvalue),
            "df": f(len(group_a) - 1),
            "df2": None,
            "confidence_interval": {"lower": f(tp_ci.low), "upper": f(tp_ci.high)},
            "effect_size": f(_cohen_d_paired(group_a, group_b)),
            "sample_summary": {
                "StatTestTableA": _sample_summary(group_a),
                "StatTestTableB": _sample_summary(group_b),
            },
        },
        {
            "case_id": "ztest_1sample_mu50",
            "test_type": "z-test",
            "sample_tables": [{"table_name": "StatTestTableA", "column_name": "value"}],
            "options": {"mu": 50.0},
            "statistic": f(z1_stat),
            "p_value": f(z1_p),
            "df": None,
            "df2": None,
            "confidence_interval": {
                "lower": f(z1_center - z_crit * z1_se),
                "upper": f(z1_center + z_crit * z1_se),
            },
            "effect_size": None,
            "sample_summary": {"StatTestTableA": _sample_summary(group_a)},
        },
        {
            "case_id": "ztest_2sample",
            "test_type": "z-test",
            "sample_tables": [
                {"table_name": "StatTestTableA", "column_name": "value"},
                {"table_name": "StatTestTableB", "column_name": "value"},
            ],
            "options": {"alternative": "two-sided"},
            "statistic": f(z2_stat),
            "p_value": f(z2_p),
            "df": None,
            "df2": None,
            "confidence_interval": {
                "lower": f(z2_center - z_crit * z2_se),
                "upper": f(z2_center + z_crit * z2_se),
            },
            "effect_size": None,
            "sample_summary": {
                "StatTestTableA": _sample_summary(group_a),
                "StatTestTableB": _sample_summary(group_b),
            },
        },
        {
            "case_id": "ftest_variance_ratio",
            "test_type": "f-test",
            "sample_tables": [
                {"table_name": "StatTestTableA", "column_name": "value"},
                {"table_name": "StatTestTableB", "column_name": "value"},
            ],
            "options": {},
            "statistic": f(f_stat),
            "p_value": f(f_p),
            "df": f(len(group_a) - 1),
            "df2": f(len(group_b) - 1),
            "confidence_interval": None,
            "effect_size": None,
            "sample_summary": {
                "StatTestTableA": _sample_summary(group_a),
                "StatTestTableB": _sample_summary(group_b),
            },
        },
        {
            "case_id": "anova_3groups",
            "test_type": "f-test",
            "sample_tables": [
                {"table_name": "StatTestTableA", "column_name": "value"},
                {"table_name": "StatTestTableB", "column_name": "value"},
                {"table_name": "StatTestTableC", "column_name": "value"},
            ],
            "options": {},
            "statistic": f(anova.statistic),
            "p_value": f(anova.pvalue),
            "df": 2.0,
            "df2": f(len(group_a) + len(group_b) + len(group_c) - 3),
            "confidence_interval": None,
            "effect_size": f(eta_sq),
            "sample_summary": {
                "StatTestTableA": _sample_summary(group_a),
                "StatTestTableB": _sample_summary(group_b),
                "StatTestTableC": _sample_summary(group_c),
            },
        },
    ]

    return {"cases": cases}
