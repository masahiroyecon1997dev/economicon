"""
E2E テスト用 Tobit サンプルデータ生成スクリプト。

## 出力

    sample/tobit_e2e_data.csv

## 列定義

| 列名   | 説明                                                          |
|--------|---------------------------------------------------------------|
| x1     | 説明変数 1（N(0, 1)）                                         |
| x2     | 説明変数 2（N(0, 1)）                                         |
| y_left | 左側打ち切り被説明変数（left=0, right=None）                  |
| y_both | 両側打ち切り被説明変数（left=0, right=4.0）                   |

## E2E テストでの使い方

    # Step 4 - 左打ち切りのみ
    dependent = "y_left"
    left_censoring = True, left_limit = 0.0
    right_censoring = False

    # Step 5 - 両側打ち切り
    dependent = "y_both"
    left_censoring = True,  left_limit = 0.0
    right_censoring = True, right_limit = 4.0   # RIGHT_CENSORING_LIMIT と一致

## 実行方法

    cd test/scripts
    python generate_e2e_sample_data.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

# ── スクリプト単体実行時に data_generators を import できるようにする ──
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from data_generators.e2e_tobit import generate_e2e_tobit_data  # noqa: E402

SEED = 42
REPO_ROOT = SCRIPTS_DIR.parents[1]
SAMPLE_DIR = REPO_ROOT / "sample"


def main() -> None:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(SEED)

    print("Generating E2E Tobit sample data...")
    df = generate_e2e_tobit_data(rng)

    output_path = SAMPLE_DIR / "tobit_e2e_data.csv"
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"  saved: {output_path}  (n={len(df)}, cols={list(df.columns)})")
    print("\nDone.")


if __name__ == "__main__":
    main()
