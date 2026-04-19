"""
合成テストデータ生成スクリプト
==============================
分析API（OLS / Logit / Probit / Lasso / Ridge / FE / RE / IV / Tobit / Heckman / RDD）
の数値ベンチマーク用テストデータを生成し、test/data/{csv,parquet}/ に保存する。

使い方:
    cd test/scripts
    python generate_synthetic_data.py

設計方針:
- 全データセットは SEED=2024 の np.random.default_rng で完全再現可能
- 分散を大きめに設定し、係数の t 値が十分大きくなるようにする
- 真のパラメータ（DGP）をコメントで明記し、ベンチマーク JSON の作成に使えるようにする
- OLS/FE/RE/IV は statsmodels / linearmodels で検証済みの精度 (atol=1e-12) を想定
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# パス設定
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
_DATA_DIR = _REPO_ROOT / "test" / "data"
_CSV_DIR = _DATA_DIR / "csv"
_PARQUET_DIR = _DATA_DIR / "parquet"

# ---------------------------------------------------------------------------
# グローバル定数
# ---------------------------------------------------------------------------

SEED = 2024

# 各データセットのサンプルサイズ
N_OLS = 300          # OLS / Logit / Probit / Lasso / Ridge
N_ENTITIES = 10      # パネルデータ: エンティティ数
N_PERIODS = 10       # パネルデータ: 期間数
N_PANEL = N_ENTITIES * N_PERIODS  # FE / RE
N_IV = 400           # IV (2SLS)
N_TOBIT = 300        # Tobit
N_HECKMAN = 600      # Heckman
N_RDD = 1000         # RDD
N_DESC = 500         # 記述統計 / 相関行列


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------


def _ensure_dirs() -> None:
    _CSV_DIR.mkdir(parents=True, exist_ok=True)
    _PARQUET_DIR.mkdir(parents=True, exist_ok=True)


def save_dataset(df: pd.DataFrame, name: str) -> None:
    """CSV と Parquet の両形式で保存する。"""
    csv_path = _CSV_DIR / f"{name}.csv"
    parquet_path = _PARQUET_DIR / f"{name}.parquet"

    df.to_csv(csv_path, index=False, encoding="utf-8")
    df.to_parquet(parquet_path, index=False, engine="pyarrow")

    print(f"  saved: {name}  (n={len(df)}, cols={list(df.columns)})")


# ---------------------------------------------------------------------------
# 1. OLS / Logit / Probit / Lasso / Ridge 用データ
# ---------------------------------------------------------------------------
# DGP (線形):
#   x1 ~ N(0, 5²),  x2 ~ N(10, 8²),  x3 ~ N(-5, 4²)
#   y_cont = 3.0 + 2.5*x1 - 1.8*x2 + 0.9*x3 + ε,  ε ~ N(0, 3²)
#
# DGP (binary):
#   lc = -0.5 + 1.2*x1 - 0.8*x2 + 0.5*x3
#   prob = logistic(lc * 0.15)   ← スケールを抑えて確率を0.5付近に集める
#   y_binary ~ Bernoulli(prob)
#
# 真のパラメータ（OLS）:
#   const=3.0, x1=2.5, x2=-1.8, x3=0.9
# ---------------------------------------------------------------------------


def generate_ols_data(rng: np.random.Generator) -> pd.DataFrame:
    """OLS / Logit / Probit / Lasso / Ridge 共用合成データ。"""
    x1 = rng.normal(0.0, 5.0, N_OLS)
    x2 = rng.normal(10.0, 8.0, N_OLS)
    x3 = rng.normal(-5.0, 4.0, N_OLS)
    eps = rng.normal(0.0, 3.0, N_OLS)

    y_cont = 3.0 + 2.5 * x1 - 1.8 * x2 + 0.9 * x3 + eps

    # バイナリ目的変数: ロジスティック DGP
    lc = (-0.5 + 1.2 * x1 - 0.8 * x2 + 0.5 * x3) * 0.15
    prob = 1.0 / (1.0 + np.exp(-lc))
    y_binary = rng.binomial(1, prob, N_OLS).astype(float)

    return pd.DataFrame(
        {
            "y_cont": y_cont,
            "y_binary": y_binary,
            "x1": x1,
            "x2": x2,
            "x3": x3,
        }
    )


# ---------------------------------------------------------------------------
# 2. パネルデータ (FE / RE) 用データ
# ---------------------------------------------------------------------------
# DGP:
#   entity_effect_i ~ N(0, 5²)          ← 大きな個体効果でFE/RE差が顕著に出る
#   x1_it ~ N(0, 4²),  x2_it ~ N(0, 3²)
#   ε_it ~ N(0, 1.5²)
#   y_it = 1.0 + 3.0*x1_it - 2.0*x2_it + alpha_i + ε_it
#
# 真のパラメータ（FE）:
#   x1=3.0, x2=-2.0  (const は固定効果に吸収)
# ---------------------------------------------------------------------------


def generate_panel_data(rng: np.random.Generator) -> pd.DataFrame:
    """固定効果・変量効果モデル用合成パネルデータ。"""
    entity_ids = np.repeat(np.arange(1, N_ENTITIES + 1), N_PERIODS)
    time_ids = np.tile(np.arange(1, N_PERIODS + 1), N_ENTITIES)

    entity_effects = rng.normal(0.0, 5.0, N_ENTITIES)
    alpha = np.repeat(entity_effects, N_PERIODS)

    x1 = rng.normal(0.0, 4.0, N_PANEL)
    x2 = rng.normal(0.0, 3.0, N_PANEL)
    eps = rng.normal(0.0, 1.5, N_PANEL)

    y = 1.0 + 3.0 * x1 - 2.0 * x2 + alpha + eps

    return pd.DataFrame(
        {
            "entity_id": entity_ids.astype(float),
            "time_id": time_ids.astype(float),
            "y": y,
            "x1": x1,
            "x2": x2,
        }
    )


# ---------------------------------------------------------------------------
# 3. IV (2SLS) 用データ
# ---------------------------------------------------------------------------
# DGP:
#   z1 ~ N(0, 1²),  z2 ~ N(0, 1²)           ← 操作変数（外生）
#   x_exog ~ N(0, 3²)                        ← 外生説明変数
#   v ~ N(0, 0.5²)                           ← 内生性の源
#   x_endog = 0.7*z1 + 0.4*z2 + v           ← First stage: F統計 >> 10
#   u = 0.8*v + N(0, 1²)                     ← y の誤差（v と相関）
#   y = 2.0 + 1.5*x_exog + 3.0*x_endog + u
#
# 真のパラメータ（IV）:
#   const=2.0, x_exog=1.5, x_endog=3.0
# First stage partial F: z1,z2 の係数が大きいため F >> 100 を期待
# ---------------------------------------------------------------------------


def generate_iv_data(rng: np.random.Generator) -> pd.DataFrame:
    """操作変数法 (IV2SLS) 用合成データ。"""
    z1 = rng.normal(0.0, 1.0, N_IV)
    z2 = rng.normal(0.0, 1.0, N_IV)
    x_exog = rng.normal(0.0, 3.0, N_IV)
    v = rng.normal(0.0, 0.5, N_IV)
    x_endog = 0.7 * z1 + 0.4 * z2 + v
    u = 0.8 * v + rng.normal(0.0, 1.0, N_IV)
    y = 2.0 + 1.5 * x_exog + 3.0 * x_endog + u

    return pd.DataFrame(
        {
            "y": y,
            "x_exog": x_exog,
            "x_endog": x_endog,
            "z1": z1,
            "z2": z2,
        }
    )


# ---------------------------------------------------------------------------
# 4. Tobit 用データ
# ---------------------------------------------------------------------------
# DGP (左側打ち切り、下限=0):
#   x1 ~ N(0, 2²),  x2 ~ N(0, 2²)
#   y_latent = 2.0 + 2.0*x1 + 1.5*x2 + ε,  ε ~ N(0, 2²)
#   y_censored = max(0, y_latent)
#
# 打ち切り比率: 約 35%
#   Var[y_latent] = (2*2)^2 + (1.5*2)^2 + 2^2 = 16+9+4 = 29, σ≈5.39
#   P(y_latent<0) = Φ(-2/5.39) ≈ 0.356
# 真のパラメータ（Tobit MLE）:
#   const=2.0, x1=2.0, x2=1.5, sigma≈2.0
# ---------------------------------------------------------------------------


def generate_tobit_data(rng: np.random.Generator) -> pd.DataFrame:
    """Tobit モデル（左側打ち切り）用合成データ。"""
    x1 = rng.normal(0.0, 2.0, N_TOBIT)
    x2 = rng.normal(0.0, 2.0, N_TOBIT)
    eps = rng.normal(0.0, 2.0, N_TOBIT)
    y_latent = 2.0 + 2.0 * x1 + 1.5 * x2 + eps
    y_censored = np.maximum(0.0, y_latent)

    censoring_ratio = (y_censored == 0.0).mean()
    print(f"    [tobit] censoring ratio = {censoring_ratio:.3f}")

    return pd.DataFrame(
        {
            "y": y_censored,
            "x1": x1,
            "x2": x2,
        }
    )


# ---------------------------------------------------------------------------
# 5. Heckman 選択モデル用データ
# ---------------------------------------------------------------------------
# DGP:
#   観測方程式 (wage):
#     wage_latent = 1.5 + 0.8*educ + 0.4*exp + ε_w,  ε_w ~ N(0, 2²)
#     wage = wage_latent (employed のみ観測)
#
#   選択方程式 (employed):
#     xb_sel = -5.0 + 0.4*educ + 0.3*exp - 0.7*kids
#     prob = logistic(xb_sel)
#     employed ~ Bernoulli(prob)
#
#   E[xb_sel] = -5.0 + 0.4*12 + 0.3*5 - 0.7*1.5 = -5.0+4.8+1.5-1.05 = 0.25
#   → P(employed) = logistic(0.25) ≈ 0.56
#
#   排除制約: kids は選択方程式にのみ登場（観測方程式から除外）
#   employed 比率: 約 55–60%
#
# 変数:
#   educ  ~ N(12, 2²)          (教育年数)
#   exp   ~ N(5, 3²)           (経験年数)
#   kids  ~ Poisson(1.5)       (子供数: 選択方程式の外生変数)
# ---------------------------------------------------------------------------


def generate_heckman_data(rng: np.random.Generator) -> pd.DataFrame:
    """Heckman 選択モデル用合成データ。"""
    educ = rng.normal(12.0, 2.0, N_HECKMAN)
    exp = rng.normal(5.0, 3.0, N_HECKMAN)
    kids = rng.poisson(1.5, N_HECKMAN).astype(float)

    xb_sel = -5.0 + 0.4 * educ + 0.3 * exp - 0.7 * kids
    prob_sel = 1.0 / (1.0 + np.exp(-xb_sel))
    employed = (rng.uniform(size=N_HECKMAN) < prob_sel).astype(float)

    eps_w = rng.normal(0.0, 2.0, N_HECKMAN)
    wage_latent = 1.5 + 0.8 * educ + 0.4 * exp + eps_w
    # 未就業者の wage は NaN（観測されない）
    wage = np.where(employed == 1.0, wage_latent, np.nan)

    employed_ratio = employed.mean()
    print(f"    [heckman] employed ratio = {employed_ratio:.3f}")

    return pd.DataFrame(
        {
            "wage": wage,
            "employed": employed,
            "educ": educ,
            "exp": exp,
            "kids": kids,
        }
    )


# ---------------------------------------------------------------------------
# 6. RDD 用データ
# ---------------------------------------------------------------------------
# DGP (シャープ RDD):
#   running_var ~ Uniform(-2, 2)
#   treat = 1[running_var >= 0]
#   y = 2.0 + 1.5*running_var + 5.0*treat + ε,  ε ~ N(0, 1.5²)
#
# カットオフ: 0.0
# 真の処置効果: 5.0  ← 肉眼でも明瞭な不連続点
# ---------------------------------------------------------------------------


def generate_rdd_data(rng: np.random.Generator) -> pd.DataFrame:
    """シャープ RDD 用合成データ。"""
    running_var = rng.uniform(-2.0, 2.0, N_RDD)
    treat = (running_var >= 0.0).astype(float)
    eps = rng.normal(0.0, 1.5, N_RDD)
    y = 2.0 + 1.5 * running_var + 5.0 * treat + eps

    return pd.DataFrame(
        {
            "y": y,
            "running_var": running_var,
        }
    )


# ---------------------------------------------------------------------------
# 7. 記述統計 / 相関行列 用データ
# ---------------------------------------------------------------------------
# DGP:
#   A ~ N(100, 20²)           (大きな平均・分散)
#   B ~ Gamma(shape=2, scale=15)  (右歪み分布)
#   D ~ N(0, 10²)
#   C = 0.7*A + 0.5*D + N(0, 5²)  (A と正の相関)
#   E = -0.6*A + N(0, 15²)        (A と負の相関)
#   category ~ {Low, Mid, High}
# ---------------------------------------------------------------------------


def generate_descriptive_data(rng: np.random.Generator) -> pd.DataFrame:
    """記述統計・相関行列検証用合成データ。"""
    A = rng.normal(100.0, 20.0, N_DESC)
    B = rng.gamma(2.0, 15.0, N_DESC)
    D = rng.normal(0.0, 10.0, N_DESC)
    C = 0.7 * A + 0.5 * D + rng.normal(0.0, 5.0, N_DESC)
    E = -0.6 * A + rng.normal(0.0, 15.0, N_DESC)

    # カテゴリ変数 (約 1/3 ずつ)
    category_raw = rng.choice(["Low", "Mid", "High"], size=N_DESC)

    return pd.DataFrame(
        {
            "A": A,
            "B": B,
            "C": C,
            "D": D,
            "E": E,
            "category": category_raw,
        }
    )


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------


def main() -> None:
    _ensure_dirs()

    rng = np.random.default_rng(SEED)

    print("Generating synthetic test datasets...")
    print()

    print("[1/7] OLS / Logit / Probit / Lasso / Ridge data")
    save_dataset(generate_ols_data(rng), "synthetic_ols")

    print("[2/7] Panel (FE / RE) data")
    save_dataset(generate_panel_data(rng), "synthetic_panel")

    print("[3/7] IV (2SLS) data")
    save_dataset(generate_iv_data(rng), "synthetic_iv")

    print("[4/7] Tobit data")
    save_dataset(generate_tobit_data(rng), "synthetic_tobit")

    print("[5/7] Heckman selection data")
    save_dataset(generate_heckman_data(rng), "synthetic_heckman")

    print("[6/7] RDD data")
    save_dataset(generate_rdd_data(rng), "synthetic_rdd")

    print("[7/7] Descriptive statistics / Correlation data")
    save_dataset(generate_descriptive_data(rng), "synthetic_descriptive")

    print()
    print(f"All done. Output: {_DATA_DIR}")


if __name__ == "__main__":
    main()
