"""合成テストデータ生成の入口スクリプト。"""

from __future__ import annotations

import numpy as np
from data_generators.descriptive import generate_descriptive_data
from data_generators.fgls_ar1 import generate_fgls_ar1_data
from data_generators.fgls_heteroskedastic import (
    generate_fgls_hetero_data,
)
from data_generators.gls import generate_gls_datasets
from data_generators.heckman import generate_heckman_data
from data_generators.helpers import DATA_DIR, SEED, ensure_dirs, save_dataset
from data_generators.iv import generate_iv_data
from data_generators.ols import generate_ols_data
from data_generators.panel import generate_panel_data
from data_generators.rdd import generate_rdd_data
from data_generators.statistics import (
    generate_statistics_ci_data,
    generate_statistics_ci_invalid_data,
    generate_statistics_constant_data,
    generate_statistics_core_data,
    generate_statistics_nulls_data,
    generate_statistics_test_groups_data,
)
from data_generators.tobit import generate_tobit_data
from data_generators.wls import generate_wls_data


def main() -> None:
    ensure_dirs()
    rng = np.random.default_rng(SEED)

    # 既存データセットは従来どおり 1 本の RNG を元の順序で消費し、
    # 追加した weighted 系データだけ独立 seed に切り出して
    # 既存 benchmark の数値を不必要に変えないようにする。
    rng_wls = np.random.default_rng(SEED + 101)
    rng_gls = np.random.default_rng(SEED + 102)
    rng_fgls_hetero = np.random.default_rng(SEED + 103)
    rng_fgls_ar1 = np.random.default_rng(SEED + 104)
    stats_ci_seed = 42
    stats_test_groups_seed = 42

    print("Generating synthetic test datasets...")
    print()

    print("[1/18] OLS / Logit / Probit / Lasso / Ridge data")
    save_dataset(generate_ols_data(rng), "synthetic_ols")

    print("[2/18] Panel (FE / RE) data")
    save_dataset(generate_panel_data(rng), "synthetic_panel")

    print("[3/18] IV (2SLS) data")
    save_dataset(generate_iv_data(rng), "synthetic_iv")

    print("[4/18] WLS data")
    save_dataset(generate_wls_data(rng_wls), "synthetic_wls")

    print("[5/18] GLS data and sigma matrix")
    gls_data, gls_sigma = generate_gls_datasets(rng_gls)
    save_dataset(gls_data, "synthetic_gls_data")
    save_dataset(gls_sigma, "synthetic_gls_sigma")

    print("[6/18] FGLS heteroskedastic data")
    save_dataset(
        generate_fgls_hetero_data(rng_fgls_hetero),
        "synthetic_fgls_hetero",
    )

    print("[7/18] FGLS AR(1) data")
    save_dataset(generate_fgls_ar1_data(rng_fgls_ar1), "synthetic_fgls_ar1")

    print("[8/18] Tobit data")
    save_dataset(generate_tobit_data(rng), "synthetic_tobit")

    print("[9/18] Heckman selection data")
    save_dataset(generate_heckman_data(rng), "synthetic_heckman")

    print("[10/18] RDD data")
    save_dataset(generate_rdd_data(rng), "synthetic_rdd")

    print("[11/18] Descriptive statistics / Correlation data")
    save_dataset(generate_descriptive_data(rng), "synthetic_descriptive")

    print("[12/18] Statistics core data")
    save_dataset(generate_statistics_core_data(), "synthetic_statistics_core")

    print("[13/18] Statistics null/sparse data")
    save_dataset(generate_statistics_nulls_data(), "synthetic_statistics_nulls")

    print("[14/18] Statistics constant-column data")
    save_dataset(
        generate_statistics_constant_data(),
        "synthetic_statistics_constant",
    )

    print("[15/18] Statistics confidence-interval data")
    save_dataset(
        generate_statistics_ci_data(seed=stats_ci_seed),
        "synthetic_statistics_ci",
    )

    print("[16/18] Statistics confidence-interval invalid data")
    save_dataset(
        generate_statistics_ci_invalid_data(),
        "synthetic_statistics_ci_invalid",
    )

    print("[17/18] Statistics test-group data")
    save_dataset(
        generate_statistics_test_groups_data(seed=stats_test_groups_seed),
        "synthetic_statistics_test_groups",
    )

    print("[18/18] Synthetic statistics add-ons complete")
    print()
    print(f"All done. Output: {DATA_DIR}")


if __name__ == "__main__":
    main()
