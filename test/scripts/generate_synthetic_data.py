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

    print("Generating synthetic test datasets...")
    print()

    print("[1/12] OLS / Logit / Probit / Lasso / Ridge data")
    save_dataset(generate_ols_data(rng), "synthetic_ols")

    print("[2/12] Panel (FE / RE) data")
    save_dataset(generate_panel_data(rng), "synthetic_panel")

    print("[3/12] IV (2SLS) data")
    save_dataset(generate_iv_data(rng), "synthetic_iv")

    print("[4/12] WLS data")
    save_dataset(generate_wls_data(rng_wls), "synthetic_wls")

    print("[5/12] GLS data and sigma matrix")
    gls_data, gls_sigma = generate_gls_datasets(rng_gls)
    save_dataset(gls_data, "synthetic_gls_data")
    save_dataset(gls_sigma, "synthetic_gls_sigma")

    print("[6/12] FGLS heteroskedastic data")
    save_dataset(
        generate_fgls_hetero_data(rng_fgls_hetero),
        "synthetic_fgls_hetero",
    )

    print("[7/12] FGLS AR(1) data")
    save_dataset(generate_fgls_ar1_data(rng_fgls_ar1), "synthetic_fgls_ar1")

    print("[8/12] Tobit data")
    save_dataset(generate_tobit_data(rng), "synthetic_tobit")

    print("[9/12] Heckman selection data")
    save_dataset(generate_heckman_data(rng), "synthetic_heckman")

    print("[10/12] RDD data")
    save_dataset(generate_rdd_data(rng), "synthetic_rdd")

    print("[11/12] Descriptive statistics / Correlation data")
    save_dataset(generate_descriptive_data(rng), "synthetic_descriptive")

    print("[12/12] Synthetic regression add-ons complete")
    print()
    print(f"All done. Output: {DATA_DIR}")


if __name__ == "__main__":
    main()
