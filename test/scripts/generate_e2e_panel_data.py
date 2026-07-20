"""
E2E テスト用パネルデータ生成スクリプト。

固定効果法（FE）・変量効果法（RE）の E2E テストで使用するサンプルデータを生成する。

## 出力

    sample/panel_e2e_data.csv

## 列定義

| 列名      | 型      | 説明                             |
|-----------|---------|----------------------------------|
| entity_id | Float64 | 個体 ID（1.0〜10.0）             |
| time_id   | Float64 | 時点（1.0〜15.0）                |
| x1        | Float64 | 説明変数 1（N(0, 4²)）           |
| x2        | Float64 | 説明変数 2（N(0, 3²)）           |
| y         | Float64 | 被説明変数（DGP 参照）           |

## データ生成過程（DGP）

    y_{it} = 1 + 3*x1_{it} - 2*x2_{it} + alpha_i + epsilon_{it}

    alpha_i ~ N(0, 5²)   個体固定効果（大きめで FE/RE の識別を明確に）
    epsilon  ~ N(0, 1.5²)  誤差項

## 実行方法

    cd test/scripts
    python generate_e2e_panel_data.py
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
N_ENTITIES = 10
N_PERIODS = 15
N_OBS = N_ENTITIES * N_PERIODS  # 150 行
REPO_ROOT = SCRIPTS_DIR.parents[1]
SAMPLE_DIR = REPO_ROOT / "sample"


def generate_panel_e2e_data(rng: np.random.Generator) -> pd.DataFrame:
    """
    パネル E2E データを生成する。

    Returns:
        DataFrame: entity_id, time_id, x1, x2, y 列を持つ 150 行のデータ
    """
    entity_ids = np.repeat(np.arange(1, N_ENTITIES + 1), N_PERIODS)
    time_ids = np.tile(np.arange(1, N_PERIODS + 1), N_ENTITIES)

    # 大きめの個体効果で FE/RE の効果が明確に出るようにする
    entity_effects = rng.normal(0.0, 5.0, N_ENTITIES)
    alpha = np.repeat(entity_effects, N_PERIODS)

    x1 = rng.normal(0.0, 4.0, N_OBS)
    x2 = rng.normal(0.0, 3.0, N_OBS)
    eps = rng.normal(0.0, 1.5, N_OBS)
    y = 1.0 + 3.0 * x1 - 2.0 * x2 + alpha + eps

    return pd.DataFrame(
        {
            "entity_id": entity_ids.astype(float),
            "time_id": time_ids.astype(float),
            "x1": x1,
            "x2": x2,
            "y": y,
        }
    )


def main() -> None:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(SEED)

    print("Generating E2E panel data (FE/RE)...")
    df = generate_panel_e2e_data(rng)

    output_path = SAMPLE_DIR / "panel_e2e_data.csv"
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"  saved: {output_path}  (n={len(df)}, cols={list(df.columns)})")
    print("\nDone.")


if __name__ == "__main__":
    main()
