"""
E2E テスト用 IV（操作変数法）データ生成スクリプト。

操作変数法（IV / 2SLS・GMM）の E2E テストで使用するサンプルデータを生成する。

## 出力

    sample/iv_e2e_data.csv

## 列定義

| 列名    | 型      | 説明                                              |
|---------|---------|---------------------------------------------------|
| y       | Float64 | 被説明変数                                         |
| x_exog  | Float64 | 外生的説明変数                                     |
| x_endog | Float64 | 内生変数（z1, z2 で識別）                           |
| z1      | Float64 | 操作変数 1（x_endog と相関、y への直接効果なし）    |
| z2      | Float64 | 操作変数 2（過剰識別のため 2 本用意）               |

## データ生成過程（DGP）

    eta    ~ N(0, 1)              内生性の源泉（共有ショック）
    x_exog ~ N(0, 1)              外生変数
    z1     ~ N(0, 1)              操作変数 1
    z2     ~ N(0, 1)              操作変数 2
    eps_x  ~ N(0, 0.3²)
    x_endog = 0.6*z1 + 0.5*z2 + 0.8*eta + eps_x

    eps_y  ~ N(0, 0.5²)
    eps    = 0.6*eta + eps_y      x_endog との内生性

    y = 2 + 3*x_exog + 2*x_endog + eps

    真の係数: const=2, x_exog=3, x_endog=2
    第一段階 F 統計量はデータ規模（N=300）と操作変数の強さから十分高い値になる

識別条件:
    操作変数(z1, z2) 2 本 ≥ 内生変数(x_endog) 1 本 → 過剰識別

## 実行方法

    cd test/scripts
    python generate_e2e_iv_data.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ── スクリプト単体実行時に data_generators を import できるようにする ──
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

SEED = 42
N_OBS = 300
REPO_ROOT = SCRIPTS_DIR.parents[1]
SAMPLE_DIR = REPO_ROOT / "sample"


def generate_iv_e2e_data(rng: np.random.Generator) -> pd.DataFrame:
    """
    IV 回帰 E2E データを生成する。

    Returns:
        DataFrame: y, x_exog, x_endog, z1, z2 列を持つ N_OBS 行のデータ
    """
    # 操作変数（外生的）
    z1 = rng.normal(0.0, 1.0, N_OBS)
    z2 = rng.normal(0.0, 1.0, N_OBS)

    # 外生的説明変数
    x_exog = rng.normal(0.0, 1.0, N_OBS)

    # 内生性の源泉（共有ショック）
    eta = rng.normal(0.0, 1.0, N_OBS)

    # 内生変数（z1, z2 と相関 + eta による内生性）
    eps_x = rng.normal(0.0, 0.3, N_OBS)
    x_endog = 0.6 * z1 + 0.5 * z2 + 0.8 * eta + eps_x

    # 誤差項（eta による内生性）
    eps_y = rng.normal(0.0, 0.5, N_OBS)
    eps = 0.6 * eta + eps_y

    # 被説明変数（真の係数: const=2, x_exog=3, x_endog=2）
    y = 2.0 + 3.0 * x_exog + 2.0 * x_endog + eps

    return pd.DataFrame(
        {
            "y": y,
            "x_exog": x_exog,
            "x_endog": x_endog,
            "z1": z1,
            "z2": z2,
        }
    )


def main() -> None:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(SEED)

    print("Generating E2E IV regression data...")
    df = generate_iv_e2e_data(rng)

    output_path = SAMPLE_DIR / "iv_e2e_data.csv"
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"  saved: {output_path}  (n={len(df)}, cols={list(df.columns)})")
    print(f"  x_endog mean={df['x_endog'].mean():.3f}, std={df['x_endog'].std():.3f}")
    print(f"  z1-x_endog corr={df['z1'].corr(df['x_endog']):.3f}")
    print(f"  z2-x_endog corr={df['z2'].corr(df['x_endog']):.3f}")
    print("\nDone.")


if __name__ == "__main__":
    main()
